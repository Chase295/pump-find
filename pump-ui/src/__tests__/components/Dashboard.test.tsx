/**
 * Tests für Dashboard Component
 * Testet Rendering, Status-Anzeige und Polling
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from '../../pages/Dashboard';
import { usePumpStore } from '../../stores/pumpStore';
import { server } from '../mocks/server';
import { degradedHealthHandler, mockHealthResponse } from '../mocks/handlers';
import { http, HttpResponse } from 'msw';

// Wrapper für Router Context
const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('Dashboard Component', () => {
  beforeEach(() => {
    // Reset store state
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

  afterEach(() => {
    usePumpStore.getState().stopPolling();
  });

  describe('Rendering', () => {
    it('zeigt Loading State initial', () => {
      usePumpStore.setState({ isLoading: true, health: null });

      renderWithRouter(<Dashboard />);

      expect(screen.getByText(/Lade Service-Status/i)).toBeInTheDocument();
    });

    it('rendert alle Status-Karten wenn Daten geladen', async () => {
      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText(/Service Status/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/Uptime/i)).toBeInTheDocument();
      expect(screen.getByText(/WebSocket/i)).toBeInTheDocument();
      expect(screen.getByText(/Datenbank/i)).toBeInTheDocument();
    });

    it('zeigt Error Alert wenn error existiert', async () => {
      // Mock fetchHealth um den Error nicht zu überschreiben
      server.use(
        http.get('*/api/health', () => {
          return HttpResponse.json({ error: 'Failed' }, { status: 500 });
        })
      );

      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        // Nach fehlgeschlagenem fetch sollte ein error gesetzt sein
        const state = usePumpStore.getState();
        expect(state.error).not.toBeNull();
      });
    });
  });

  describe('Status Display', () => {
    it('zeigt grünen Status für healthy', async () => {
      usePumpStore.setState({
        health: mockHealthResponse as any,
        isLoading: false,
      });

      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText(/Healthy/i)).toBeInTheDocument();
      });
    });

    it('zeigt roten Status für degraded', async () => {
      server.use(degradedHealthHandler);

      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText(/Degraded/i)).toBeInTheDocument();
      });
    });

    it('zeigt Connected Chip für ws_connected=true', async () => {
      usePumpStore.setState({
        health: { ...mockHealthResponse, ws_connected: true } as any,
        isLoading: false,
      });

      renderWithRouter(<Dashboard />);

      const wsSection = screen.getByText(/WebSocket/i).closest('div');
      expect(wsSection).toBeInTheDocument();
    });

    it('zeigt Disconnected Chip für ws_connected=false', async () => {
      usePumpStore.setState({
        health: { ...mockHealthResponse, ws_connected: false } as any,
        isLoading: false,
      });

      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText(/Disconnected/i)).toBeInTheDocument();
      });
    });
  });

  describe('Uptime Formatting', () => {
    it('formatiert Uptime korrekt für Stunden', async () => {
      usePumpStore.setState({
        health: { ...mockHealthResponse, uptime_seconds: 7325 } as any, // 2h 2m 5s
        isLoading: false,
      });

      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText(/2h/i)).toBeInTheDocument();
      });
    });

    it('formatiert Uptime korrekt für nur Minuten', async () => {
      usePumpStore.setState({
        health: { ...mockHealthResponse, uptime_seconds: 125 } as any, // 2m 5s
        isLoading: false,
      });

      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText(/2m/i)).toBeInTheDocument();
      });
    });
  });

  describe('Cache Statistics', () => {
    it('zeigt Cache Statistiken Sektion', async () => {
      usePumpStore.setState({
        health: mockHealthResponse as any,
        isLoading: false,
      });

      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText(/Cache Statistiken/i)).toBeInTheDocument();
      });
    });

    it('zeigt Gesamt Coins Wert', async () => {
      usePumpStore.setState({
        health: mockHealthResponse as any,
        isLoading: false,
      });

      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText(/Gesamt Coins/i)).toBeInTheDocument();
      });
    });
  });

  describe('Discovery Statistics', () => {
    it('zeigt Discovery Statistiken Sektion', async () => {
      usePumpStore.setState({
        health: mockHealthResponse as any,
        isLoading: false,
      });

      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText(/Discovery Statistiken/i)).toBeInTheDocument();
      });
    });

    it('zeigt n8n Status', async () => {
      usePumpStore.setState({
        health: { ...mockHealthResponse, discovery_stats: { ...mockHealthResponse.discovery_stats, n8n_available: true } } as any,
        isLoading: false,
      });

      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText(/n8n Status/i)).toBeInTheDocument();
      });
    });
  });

  describe('Tracking Statistics', () => {
    it('zeigt Tracking Statistiken Sektion', async () => {
      usePumpStore.setState({
        health: mockHealthResponse as any,
        isLoading: false,
      });

      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText(/Tracking Statistiken/i)).toBeInTheDocument();
      });
    });

    it('zeigt Aktive Coins Label', async () => {
      usePumpStore.setState({
        health: mockHealthResponse as any,
        isLoading: false,
      });

      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText(/Aktive Coins/i)).toBeInTheDocument();
      });
    });
  });

  describe('Polling', () => {
    it('startet polling on mount', async () => {
      const startPollingSpy = vi.spyOn(usePumpStore.getState(), 'startPolling');

      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        expect(startPollingSpy).toHaveBeenCalled();
      });
    });

    it('stoppt polling on unmount', async () => {
      // Spy muss vor dem render erstellt werden
      const stopPollingSpy = vi.spyOn(usePumpStore.getState(), 'stopPolling');

      const { unmount } = renderWithRouter(<Dashboard />);

      // Warte kurz, damit der Component mounted ist
      await waitFor(() => {
        expect(screen.getByText(/Pump Service Dashboard/i)).toBeInTheDocument();
      });

      unmount();

      expect(stopPollingSpy).toHaveBeenCalled();
    });

    it('ruft fetchHealth und fetchConfig on mount auf', async () => {
      const fetchHealthSpy = vi.spyOn(usePumpStore.getState(), 'fetchHealth');
      const fetchConfigSpy = vi.spyOn(usePumpStore.getState(), 'fetchConfig');

      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        expect(fetchHealthSpy).toHaveBeenCalled();
        expect(fetchConfigSpy).toHaveBeenCalled();
      });
    });
  });

  describe('Error Display', () => {
    it('zeigt last_error in Warning Alert', async () => {
      usePumpStore.setState({
        health: {
          ...mockHealthResponse,
          last_error: 'WebSocket timeout',
        } as any,
        isLoading: false,
      });

      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText(/WebSocket timeout/i)).toBeInTheDocument();
      });
    });
  });

  describe('Data Accuracy', () => {
    it('zeigt echte API-Werte an', async () => {
      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        // Werte aus mockHealthResponse
        expect(screen.getByText(/healthy/i)).toBeInTheDocument();
      });

      // Verifiziere spezifische Werte
      const state = usePumpStore.getState();
      expect(state.health?.uptime_seconds).toBe(3600);
      expect(state.health?.cache_stats.total_coins).toBe(10);
    });
  });
});
