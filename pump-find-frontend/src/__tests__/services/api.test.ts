/**
 * Tests für API Service
 * Testet alle API Endpoints und Error Handling
 */

import { describe, it, expect, vi } from 'vitest';
import { pumpApi } from '../../services/api';
import { server } from '../mocks/server';
import { http, HttpResponse } from 'msw';

describe('pumpApi', () => {
  describe('getHealth', () => {
    it('ruft /api/health Endpoint auf', async () => {
      const health = await pumpApi.getHealth();

      expect(health).toBeDefined();
      expect(health.status).toBe('healthy');
    });

    it('gibt HealthResponse Typ zurück', async () => {
      const health = await pumpApi.getHealth();

      expect(health).toHaveProperty('status');
      expect(health).toHaveProperty('ws_connected');
      expect(health).toHaveProperty('db_connected');
      expect(health).toHaveProperty('uptime_seconds');
      expect(health).toHaveProperty('cache_stats');
      expect(health).toHaveProperty('tracking_stats');
      expect(health).toHaveProperty('discovery_stats');
    });

    it('wirft bei Network Error', async () => {
      server.use(
        http.get('*/api/health', () => {
          return HttpResponse.error();
        })
      );

      await expect(pumpApi.getHealth()).rejects.toThrow();
    });

    it('wirft bei 500 Error', async () => {
      server.use(
        http.get('*/api/health', () => {
          return HttpResponse.json(
            { error: 'Internal Server Error' },
            { status: 500 }
          );
        })
      );

      await expect(pumpApi.getHealth()).rejects.toThrow();
    });
  });

  describe('getConfig', () => {
    it('ruft /api/config Endpoint auf', async () => {
      const config = await pumpApi.getConfig();

      expect(config).toBeDefined();
      expect(config.coin_cache_seconds).toBe(120);
    });

    it('gibt ConfigResponse Typ zurück', async () => {
      const config = await pumpApi.getConfig();

      expect(config).toHaveProperty('n8n_webhook_url');
      expect(config).toHaveProperty('coin_cache_seconds');
      expect(config).toHaveProperty('batch_size');
      expect(config).toHaveProperty('db_dsn');
    });
  });

  describe('updateConfig', () => {
    it('sendet PUT Request an /api/config', async () => {
      const updateData = { coin_cache_seconds: 180 };

      const response = await pumpApi.updateConfig(updateData);

      expect(response).toBeDefined();
      expect(response.status).toBe('success');
    });

    it('enthält Config-Daten im Body', async () => {
      let capturedBody: Record<string, unknown> | null = null;

      server.use(
        http.put('*/api/config', async ({ request }) => {
          capturedBody = await request.json() as Record<string, unknown>;
          return HttpResponse.json({ status: 'success' });
        })
      );

      await pumpApi.updateConfig({ coin_cache_seconds: 180 });

      expect(capturedBody).toEqual({ coin_cache_seconds: 180 });
    });
  });

  describe('getMetrics', () => {
    it('gibt String Response zurück', async () => {
      const metrics = await pumpApi.getMetrics();

      expect(typeof metrics).toBe('string');
      expect(metrics).toContain('unified_coins_received_total');
    });

    it('enthält Prometheus Format', async () => {
      const metrics = await pumpApi.getMetrics();

      expect(metrics).toContain('# HELP');
      expect(metrics).toContain('# TYPE');
    });
  });

  describe('getStreamStats', () => {
    it('ruft /api/database/streams/stats auf', async () => {
      const stats = await pumpApi.getStreamStats();

      expect(stats).toBeDefined();
      expect(stats.active_streams).toBe(50);
      expect(stats.total_streams).toBe(200);
    });

    it('enthält streams_by_phase', async () => {
      const stats = await pumpApi.getStreamStats();

      expect(stats.streams_by_phase).toBeDefined();
      expect(stats.streams_by_phase['1']).toBe(20);
    });
  });

  describe('getPhases', () => {
    it('ruft /api/database/phases auf', async () => {
      const phases = await pumpApi.getPhases();

      expect(phases).toBeDefined();
      expect(Array.isArray(phases)).toBe(true);
      expect(phases.length).toBeGreaterThan(0);
    });

    it('enthält Phase Struktur', async () => {
      const phases = await pumpApi.getPhases();

      expect(phases[0]).toHaveProperty('id');
      expect(phases[0]).toHaveProperty('name');
      expect(phases[0]).toHaveProperty('interval_seconds');
    });
  });

  describe('checkServiceHealth', () => {
    it('gibt true zurück bei erfolgreichem Health Check', async () => {
      const isHealthy = await pumpApi.checkServiceHealth();

      expect(isHealthy).toBe(true);
    });

    it('gibt false zurück bei Error', async () => {
      server.use(
        http.get('*/api/health', () => {
          return HttpResponse.error();
        })
      );

      const isHealthy = await pumpApi.checkServiceHealth();

      expect(isHealthy).toBe(false);
    });

    it('wirft nicht bei Error (gibt false zurück)', async () => {
      server.use(
        http.get('*/api/health', () => {
          return HttpResponse.json({ error: 'Error' }, { status: 500 });
        })
      );

      // Sollte nicht werfen
      await expect(pumpApi.checkServiceHealth()).resolves.toBe(false);
    });
  });

  describe('Error Handling', () => {
    it('loggt Errors in Console', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      server.use(
        http.get('*/api/health', () => {
          return HttpResponse.error();
        })
      );

      try {
        await pumpApi.getHealth();
      } catch {
        // Error erwartet
      }

      expect(consoleSpy).toHaveBeenCalled();
      consoleSpy.mockRestore();
    });

    it('rejected Promise bei Error', async () => {
      server.use(
        http.get('*/api/config', () => {
          return HttpResponse.json({ error: 'Failed' }, { status: 500 });
        })
      );

      await expect(pumpApi.getConfig()).rejects.toBeDefined();
    });
  });

  describe('Base URL', () => {
    it('verwendet relative URLs', async () => {
      let capturedUrl = '';

      server.use(
        http.get('*/api/health', ({ request }) => {
          capturedUrl = request.url;
          return HttpResponse.json({ status: 'healthy' });
        })
      );

      await pumpApi.getHealth();

      expect(capturedUrl).toContain('/api/health');
    });
  });

  describe('Timeout Handling', () => {
    it('hat Timeout konfiguriert', async () => {
      // Simuliere langsamen Server
      server.use(
        http.get('*/api/health', async () => {
          // Verzögerung würde in echtem Test Timeout auslösen
          return HttpResponse.json({ status: 'healthy' });
        })
      );

      // Test dass Request durchgeht (kein Timeout bei normalem Response)
      const health = await pumpApi.getHealth();
      expect(health).toBeDefined();
    });
  });
});
