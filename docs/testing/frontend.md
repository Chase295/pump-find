# Frontend Tests (vitest)

Dokumentation der 101 Frontend-Tests.

---

## Übersicht

```
pump-ui/src/__tests__/
├── setup.ts              # Test-Setup
├── mocks/
│   ├── handlers.ts       # MSW Request Handlers
│   └── server.ts         # MSW Server Setup
├── services/
│   └── api.test.ts       # API Client Tests
├── stores/
│   └── pumpStore.test.ts # Zustand Store Tests
└── components/
    ├── Dashboard.test.tsx
    ├── Config.test.tsx
    └── Metrics.test.tsx
```

---

## Test-Ausführung

```bash
cd pump-ui

# Alle Tests
npm test

# Watch Mode
npm test -- --watch

# Einzelne Datei
npm test -- Dashboard.test.tsx

# Mit Coverage
npm test -- --coverage

# UI Mode (Browser)
npm test -- --ui
```

---

## vitest.config.ts

```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/__tests__/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      exclude: ['node_modules/', 'src/__tests__/'],
    },
  },
});
```

---

## MSW (Mock Service Worker)

### server.ts

```typescript
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);
```

### handlers.ts

**Mock-Daten:**

```typescript
export const mockHealthResponse = {
  status: 'healthy',
  ws_connected: true,
  db_connected: true,
  uptime_seconds: 3600,
  last_message_ago: 5,
  reconnect_count: 0,
  last_error: null,
  cache_stats: {
    total_coins: 10,
    activated_coins: 5,
    expired_coins: 5,
    oldest_age_seconds: 100,
    newest_age_seconds: 10,
  },
  tracking_stats: {
    active_coins: 50,
    total_trades: 1000,
    total_metrics_saved: 500,
  },
  discovery_stats: {
    total_coins_discovered: 200,
    n8n_available: true,
    n8n_buffer_size: 3,
  },
};

export const mockConfigResponse = {
  n8n_webhook_url: 'http://localhost:5678/webhook/test',
  n8n_webhook_method: 'POST',
  db_dsn: 'postgresql://user:***@host:5432/db',
  coin_cache_seconds: 120,
  batch_size: 10,
  ...
};

export const mockMetricsResponse = `
# HELP unified_coins_received_total Total coins received
# TYPE unified_coins_received_total counter
unified_coins_received_total 123

# HELP unified_cache_size Current cache size
# TYPE unified_cache_size gauge
unified_cache_size 10
`.trim();
```

**Request Handlers:**

```typescript
export const handlers = [
  // Health Endpoint
  http.get('*/api/health', () => {
    return HttpResponse.json(mockHealthResponse);
  }),

  // Config Endpoints
  http.get('*/api/config', () => {
    return HttpResponse.json(mockConfigResponse);
  }),

  http.put('*/api/config', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({
      status: 'success',
      message: 'Configuration updated',
      updated_fields: Object.keys(body),
      new_config: { ...mockConfigResponse, ...body },
    });
  }),

  // Metrics Endpoint
  http.get('*/api/metrics', () => {
    return new HttpResponse(mockMetricsResponse, {
      headers: { 'Content-Type': 'text/plain' },
    });
  }),

  // Stream Stats
  http.get('*/api/database/streams/stats', () => {
    return HttpResponse.json(mockStreamStatsResponse);
  }),
];
```

**Error Handlers:**

```typescript
export const errorHandlers = {
  healthError: http.get('*/api/health', () => {
    return HttpResponse.json(
      { error: 'Service unavailable' },
      { status: 503 }
    );
  }),

  networkError: http.get('*/api/health', () => {
    return HttpResponse.error();
  }),
};

export const degradedHealthHandler = http.get('*/api/health', () => {
  return HttpResponse.json({
    ...mockHealthResponse,
    status: 'degraded',
    ws_connected: false,
    last_error: 'WebSocket connection lost',
  });
});
```

---

## setup.ts

```typescript
import '@testing-library/jest-dom';
import { server } from './mocks/server';
import { beforeAll, afterEach, afterAll } from 'vitest';

// MSW Server starten
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));

// Handler nach jedem Test zurücksetzen
afterEach(() => server.resetHandlers());

// Server nach allen Tests beenden
afterAll(() => server.close());
```

---

## Component Tests

### Dashboard.test.tsx

**Testet:** Dashboard-Seite mit Live-Status

```typescript
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from '../../pages/Dashboard';

describe('Dashboard', () => {
  const renderDashboard = () => {
    return render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );
  };

  it('renders service status', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText(/healthy/i)).toBeInTheDocument();
    });
  });

  it('shows uptime', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText(/uptime/i)).toBeInTheDocument();
    });
  });

  it('displays cache stats', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText(/total_coins/i)).toBeInTheDocument();
    });
  });

  it('shows WebSocket status chip', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText(/connected/i)).toBeInTheDocument();
    });
  });

  it('handles degraded status', async () => {
    server.use(degradedHealthHandler);
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText(/degraded/i)).toBeInTheDocument();
    });
  });
});
```

**Test-Kategorien:**
- Rendering (5 Tests)
- Status-Anzeige (4 Tests)
- Error Handling (3 Tests)
- Polling (3 Tests)

### Config.test.tsx

**Testet:** Konfigurations-Seite

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Config from '../../pages/Config';

describe('Config', () => {
  it('loads current config', async () => {
    render(<Config />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('120')).toBeInTheDocument();
    });
  });

  it('updates config on save', async () => {
    render(<Config />);

    await waitFor(() => {
      const input = screen.getByLabelText(/batch_size/i);
      fireEvent.change(input, { target: { value: '15' } });
    });

    const saveButton = screen.getByRole('button', { name: /save/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText(/success/i)).toBeInTheDocument();
    });
  });

  it('shows error on failed save', async () => {
    server.use(errorHandlers.configError);
    render(<Config />);

    // ... Test Implementation
  });
});
```

**Test-Kategorien:**
- Config Loading (3 Tests)
- Form Interaction (5 Tests)
- Save/Update (4 Tests)
- Validation (3 Tests)

### Metrics.test.tsx

**Testet:** Metriken-Seite mit Charts

```typescript
import { render, screen, waitFor } from '@testing-library/react';
import Metrics from '../../pages/Metrics';

describe('Metrics', () => {
  it('fetches and displays metrics', async () => {
    render(<Metrics />);

    await waitFor(() => {
      expect(screen.getByText(/unified_coins_received/i)).toBeInTheDocument();
    });
  });

  it('parses Prometheus format', async () => {
    render(<Metrics />);

    await waitFor(() => {
      // Parsed value aus mockMetricsResponse
      expect(screen.getByText('123')).toBeInTheDocument();
    });
  });

  it('renders charts', async () => {
    render(<Metrics />);

    await waitFor(() => {
      expect(screen.getByTestId('metrics-chart')).toBeInTheDocument();
    });
  });
});
```

---

## Store Tests

### pumpStore.test.ts

**Testet:** Zustand State Management

```typescript
import { usePumpStore } from '../../stores/pumpStore';
import { act } from '@testing-library/react';

describe('pumpStore', () => {
  beforeEach(() => {
    // Store zurücksetzen
    usePumpStore.setState({
      health: null,
      config: null,
      isLoading: false,
      error: null,
    });
  });

  it('fetchHealth updates state', async () => {
    await act(async () => {
      await usePumpStore.getState().fetchHealth();
    });

    const state = usePumpStore.getState();
    expect(state.health).not.toBeNull();
    expect(state.health?.status).toBe('healthy');
  });

  it('fetchConfig updates state', async () => {
    await act(async () => {
      await usePumpStore.getState().fetchConfig();
    });

    const state = usePumpStore.getState();
    expect(state.config).not.toBeNull();
    expect(state.config?.batch_size).toBe(10);
  });

  it('handles API errors', async () => {
    server.use(errorHandlers.healthError);

    await act(async () => {
      await usePumpStore.getState().fetchHealth();
    });

    const state = usePumpStore.getState();
    expect(state.error).not.toBeNull();
  });

  it('startPolling creates interval', () => {
    act(() => {
      usePumpStore.getState().startPolling();
    });

    // Polling sollte aktiv sein
    expect(window.__pumpPollingId).toBeDefined();

    act(() => {
      usePumpStore.getState().stopPolling();
    });
  });
});
```

**Test-Kategorien:**
- fetchHealth (5 Tests)
- fetchConfig (4 Tests)
- updateConfig (3 Tests)
- Polling (4 Tests)
- Error Handling (4 Tests)

---

## API Tests

### api.test.ts

**Testet:** Axios HTTP Client

```typescript
import { pumpApi } from '../../services/api';

describe('pumpApi', () => {
  it('getHealth returns HealthResponse', async () => {
    const health = await pumpApi.getHealth();

    expect(health.status).toBe('healthy');
    expect(health.ws_connected).toBe(true);
    expect(health.cache_stats).toBeDefined();
  });

  it('getConfig returns ConfigResponse', async () => {
    const config = await pumpApi.getConfig();

    expect(config.batch_size).toBe(10);
    expect(config.coin_cache_seconds).toBe(120);
  });

  it('updateConfig sends PUT request', async () => {
    const response = await pumpApi.updateConfig({ batch_size: 15 });

    expect(response.status).toBe('success');
    expect(response.updated_fields).toContain('batch_size');
  });

  it('getMetrics returns string', async () => {
    const metrics = await pumpApi.getMetrics();

    expect(typeof metrics).toBe('string');
    expect(metrics).toContain('unified_coins_received_total');
  });

  it('handles network errors', async () => {
    server.use(errorHandlers.networkError);

    await expect(pumpApi.getHealth()).rejects.toThrow();
  });
});
```

**Test-Kategorien:**
- getHealth (3 Tests)
- getConfig (3 Tests)
- updateConfig (4 Tests)
- getMetrics (2 Tests)
- getStreamStats (2 Tests)
- getPhases (2 Tests)
- Error Handling (4 Tests)

---

## Test-Patterns

### Async Rendering

```typescript
// Warte auf asynchrone Daten
await waitFor(() => {
  expect(screen.getByText(/expected text/i)).toBeInTheDocument();
});
```

### User Events

```typescript
import userEvent from '@testing-library/user-event';

it('handles form submission', async () => {
  const user = userEvent.setup();
  render(<Form />);

  await user.type(screen.getByLabelText('Name'), 'Test');
  await user.click(screen.getByRole('button', { name: /submit/i }));

  await waitFor(() => {
    expect(screen.getByText(/success/i)).toBeInTheDocument();
  });
});
```

### MSW Handler Override

```typescript
it('handles error state', async () => {
  // Temporär anderen Handler verwenden
  server.use(
    http.get('*/api/health', () => {
      return HttpResponse.json({ error: 'Failed' }, { status: 500 });
    })
  );

  render(<Component />);

  await waitFor(() => {
    expect(screen.getByText(/error/i)).toBeInTheDocument();
  });
});
```

### Store State Reset

```typescript
beforeEach(() => {
  usePumpStore.setState({
    health: null,
    config: null,
    isLoading: false,
    error: null,
  });
});
```

---

## Best Practices

1. **MSW für API Mocking:** Nicht axios direkt mocken
2. **waitFor für Async:** Immer auf asynchrone Updates warten
3. **User Events:** `userEvent` statt `fireEvent` für realistischere Tests
4. **Accessibility Queries:** `getByRole`, `getByLabelText` bevorzugen
5. **Isolation:** Store-State vor jedem Test zurücksetzen

---

## Coverage

```bash
# Coverage Report generieren
npm test -- --coverage

# HTML Report öffnen
open coverage/index.html
```

**Ziel-Coverage:**
- Statements: > 80%
- Branches: > 75%
- Functions: > 80%
- Lines: > 80%

---

## Weiterführende Dokumentation

- [Backend Tests](backend.md) - pytest Tests
- [Frontend-Architektur](../architecture/frontend.md) - Zu testende Komponenten
- [API-Endpunkte](../api/endpoints.md) - MSW Handlers
