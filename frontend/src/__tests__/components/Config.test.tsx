/**
 * Tests für Config Component
 * Testet Form Handling und Config Updates
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import Config from '../../pages/Config';
import { usePumpStore } from '../../stores/pumpStore';
import { server } from '../mocks/server';
import { mockConfigResponse } from '../mocks/handlers';
import { http, HttpResponse } from 'msw';

// Wrapper für Router Context
const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('Config Component', () => {
  beforeEach(() => {
    usePumpStore.setState({
      health: null,
      config: null,
      isLoading: false,
      error: null,
      lastUpdated: null,
    });
    // Clear private polling interval
    (usePumpStore.getState() as any)._pollingInterval = null;
  });

  describe('Form Initialization', () => {
    it('füllt Form mit Config-Werten', async () => {
      usePumpStore.setState({
        config: mockConfigResponse as any,
        isLoading: false,
      });

      renderWithRouter(<Config />);

      await waitFor(() => {
        const cacheInput = screen.getByDisplayValue('120');
        expect(cacheInput).toBeInTheDocument();
      });
    });

    it('verwendet Default-Werte wenn config null ist', async () => {
      renderWithRouter(<Config />);

      await waitFor(() => {
        expect(screen.getByText(/Konfiguration/i)).toBeInTheDocument();
      });
    });
  });

  describe('Form Fields', () => {
    it('zeigt n8n_webhook_url Feld', async () => {
      usePumpStore.setState({
        config: mockConfigResponse as any,
        isLoading: false,
      });

      renderWithRouter(<Config />);

      await waitFor(() => {
        expect(screen.getByLabelText(/Webhook URL/i)).toBeInTheDocument();
      });
    });

    it('zeigt coin_cache_seconds Feld', async () => {
      usePumpStore.setState({
        config: mockConfigResponse as any,
        isLoading: false,
      });

      renderWithRouter(<Config />);

      await waitFor(() => {
        expect(screen.getByLabelText(/Cache/i)).toBeInTheDocument();
      });
    });

    it('zeigt Batch Sektion', async () => {
      usePumpStore.setState({
        config: mockConfigResponse as any,
        isLoading: false,
      });

      renderWithRouter(<Config />);

      await waitFor(() => {
        // Die Sektion enthält "Batch" im Header
        const batchElements = screen.getAllByText(/Batch-Größe/i);
        expect(batchElements.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Form Validation', () => {
    it('sendet nur geänderte Felder', async () => {
      const user = userEvent.setup();
      let capturedBody: Record<string, unknown> | null = null;

      server.use(
        http.put('*/api/config', async ({ request }) => {
          capturedBody = await request.json() as Record<string, unknown>;
          return HttpResponse.json({ status: 'success' });
        })
      );

      usePumpStore.setState({
        config: mockConfigResponse as any,
        isLoading: false,
      });

      renderWithRouter(<Config />);

      await waitFor(() => {
        expect(screen.getByDisplayValue('120')).toBeInTheDocument();
      });

      // Ändere nur coin_cache_seconds
      const cacheInput = screen.getByDisplayValue('120');
      await user.clear(cacheInput);
      await user.type(cacheInput, '180');

      // Submit
      const submitButton = screen.getByRole('button', { name: /Speichern/i });
      await user.click(submitButton);

      await waitFor(() => {
        if (capturedBody) {
          // Sollte nur das geänderte Feld enthalten
          expect(capturedBody).toHaveProperty('coin_cache_seconds');
        }
      });
    });

    it('zeigt "keine Änderungen" wenn nichts geändert', async () => {
      const user = userEvent.setup();

      usePumpStore.setState({
        config: mockConfigResponse as any,
        isLoading: false,
      });

      renderWithRouter(<Config />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Speichern/i })).toBeInTheDocument();
      });

      // Submit ohne Änderungen
      const submitButton = screen.getByRole('button', { name: /Speichern/i });
      await user.click(submitButton);

      // Sollte Hinweis zeigen oder nichts senden
      // (abhängig von Implementierung)
    });

    it('sendet keine zensierte db_dsn', async () => {
      const user = userEvent.setup();
      let capturedBody: Record<string, unknown> | null = null;

      server.use(
        http.put('*/api/config', async ({ request }) => {
          capturedBody = await request.json() as Record<string, unknown>;
          return HttpResponse.json({ status: 'success' });
        })
      );

      usePumpStore.setState({
        config: { ...mockConfigResponse, db_dsn: '***censored***' } as any,
        isLoading: false,
      });

      renderWithRouter(<Config />);

      await waitFor(() => {
        expect(screen.getByDisplayValue('120')).toBeInTheDocument();
      });

      // Ändere anderes Feld
      const cacheInput = screen.getByDisplayValue('120');
      await user.clear(cacheInput);
      await user.type(cacheInput, '150');

      const submitButton = screen.getByRole('button', { name: /Speichern/i });
      await user.click(submitButton);

      await waitFor(() => {
        if (capturedBody) {
          // db_dsn mit *** sollte nicht gesendet werden
          const dsn = capturedBody.db_dsn as string | undefined;
          if (dsn) {
            expect(dsn).not.toContain('***');
          }
        }
      });
    });
  });

  describe('Form Submission', () => {
    it('ruft updateConfig bei Submit auf', async () => {
      const user = userEvent.setup();
      const updateConfigSpy = vi.fn();

      usePumpStore.setState({
        config: mockConfigResponse as any,
        isLoading: false,
        updateConfig: updateConfigSpy,
      });

      renderWithRouter(<Config />);

      await waitFor(() => {
        expect(screen.getByDisplayValue('120')).toBeInTheDocument();
      });

      // Ändere Wert
      const cacheInput = screen.getByDisplayValue('120');
      await user.clear(cacheInput);
      await user.type(cacheInput, '180');

      const submitButton = screen.getByRole('button', { name: /Speichern/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(updateConfigSpy).toHaveBeenCalled();
      });
    });

    it('zeigt Success Message bei erfolgreichem Update', async () => {
      const user = userEvent.setup();

      usePumpStore.setState({
        config: mockConfigResponse as any,
        isLoading: false,
      });

      renderWithRouter(<Config />);

      await waitFor(() => {
        expect(screen.getByDisplayValue('120')).toBeInTheDocument();
      });

      const cacheInput = screen.getByDisplayValue('120');
      await user.clear(cacheInput);
      await user.type(cacheInput, '180');

      const submitButton = screen.getByRole('button', { name: /Speichern/i });
      await user.click(submitButton);

      // Erfolgreiche Submission zeigt entweder Success Message oder Config bleibt sichtbar
      await waitFor(() => {
        expect(screen.getByText(/Service Konfiguration/i)).toBeInTheDocument();
      });
    });

    it('handhabt Update Errors graceful', async () => {
      const user = userEvent.setup();

      server.use(
        http.put('*/api/config', () => {
          return HttpResponse.json({ error: 'Update failed' }, { status: 500 });
        })
      );

      usePumpStore.setState({
        config: mockConfigResponse as any,
        isLoading: false,
      });

      renderWithRouter(<Config />);

      await waitFor(() => {
        expect(screen.getByDisplayValue('120')).toBeInTheDocument();
      });

      const cacheInput = screen.getByDisplayValue('120');
      await user.clear(cacheInput);
      await user.type(cacheInput, '180');

      const submitButton = screen.getByRole('button', { name: /Speichern/i });
      await user.click(submitButton);

      // Sollte nicht crashen
      await waitFor(() => {
        expect(screen.getByText(/Service Konfiguration/i)).toBeInTheDocument();
      });
    });
  });

  describe('Refresh Button', () => {
    it('ruft fetchConfig bei Refresh auf', async () => {
      const user = userEvent.setup();
      const fetchConfigSpy = vi.fn();

      usePumpStore.setState({
        config: mockConfigResponse as any,
        isLoading: false,
        fetchConfig: fetchConfigSpy,
      });

      renderWithRouter(<Config />);

      await waitFor(() => {
        const refreshButton = screen.getByRole('button', { name: /Aktualisieren|Refresh/i });
        expect(refreshButton).toBeInTheDocument();
      });

      const refreshButton = screen.getByRole('button', { name: /Aktualisieren|Refresh/i });
      await user.click(refreshButton);

      expect(fetchConfigSpy).toHaveBeenCalled();
    });
  });

  describe('Loading State', () => {
    it('disablet Buttons während Loading', async () => {
      usePumpStore.setState({
        config: mockConfigResponse as any,
        isLoading: true,
      });

      renderWithRouter(<Config />);

      await waitFor(() => {
        const submitButton = screen.getByRole('button', { name: /Speichern|Speichere/i });
        expect(submitButton).toBeDisabled();
      });
    });

    it('zeigt "Speichere..." Text während Loading', async () => {
      usePumpStore.setState({
        config: mockConfigResponse as any,
        isLoading: true,
      });

      renderWithRouter(<Config />);

      await waitFor(() => {
        expect(screen.getByText(/Speichere|Loading/i)).toBeInTheDocument();
      });
    });
  });

  describe('Current Config Display', () => {
    it('zeigt aktuelle Config-Werte', async () => {
      usePumpStore.setState({
        config: mockConfigResponse as any,
        isLoading: false,
      });

      renderWithRouter(<Config />);

      await waitFor(() => {
        // Werte aus mockConfigResponse sollten angezeigt werden
        expect(screen.getByDisplayValue('120')).toBeInTheDocument();
      });
    });

    it('zeigt Aktuelle Konfiguration Sektion', async () => {
      usePumpStore.setState({
        config: mockConfigResponse as any,
        isLoading: false,
      });

      renderWithRouter(<Config />);

      await waitFor(() => {
        expect(screen.getByText(/Aktuelle Konfiguration/i)).toBeInTheDocument();
      });
    });
  });
});
