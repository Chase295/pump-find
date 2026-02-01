/**
 * MSW Request Handlers
 * Definiert Mock-Responses für alle API Endpoints
 */

import { http, HttpResponse } from 'msw';

// Sample Data
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
  db_refresh_interval: 10,
  batch_size: 10,
  batch_timeout: 30,
  bad_names_pattern: 'test|bot|rug|scam',
  spam_burst_window: 30,
  sol_reserves_full: 85.0,
  whale_threshold_sol: 1.0,
  age_calculation_offset_min: 60,
  trade_buffer_seconds: 180,
  ath_flush_interval: 5,
};

export const mockMetricsResponse = `
# HELP unified_coins_received_total Total coins received
# TYPE unified_coins_received_total counter
unified_coins_received_total 123

# HELP unified_cache_size Current cache size
# TYPE unified_cache_size gauge
unified_cache_size 10

# HELP unified_coins_tracked Currently tracked coins
# TYPE unified_coins_tracked gauge
unified_coins_tracked 50

# HELP unified_trades_received_total Total trades received
# TYPE unified_trades_received_total counter
unified_trades_received_total 1000

# HELP unified_ws_reconnects_total Total WebSocket reconnects
# TYPE unified_ws_reconnects_total counter
unified_ws_reconnects_total 2

# HELP unified_ws_connected WebSocket connection status
# TYPE unified_ws_connected gauge
unified_ws_connected 1

# HELP unified_db_connected Database connection status
# TYPE unified_db_connected gauge
unified_db_connected 1

# HELP unified_n8n_available n8n availability status
# TYPE unified_n8n_available gauge
unified_n8n_available 1

# HELP unified_uptime_seconds Service uptime
# TYPE unified_uptime_seconds gauge
unified_uptime_seconds 3600

# HELP unified_coins_filtered_total Total filtered coins
# TYPE unified_coins_filtered_total counter
unified_coins_filtered_total{reason="bad_name"} 45
unified_coins_filtered_total{reason="spam_burst"} 12
`.trim();

export const mockStreamStatsResponse = {
  active_streams: 50,
  total_streams: 200,
  streams_by_phase: {
    '1': 20,
    '2': 20,
    '3': 10,
  },
};

export const mockPhasesResponse = [
  { id: 1, name: 'Baby Zone', interval_seconds: 5 },
  { id: 2, name: 'Survival Zone', interval_seconds: 30 },
  { id: 3, name: 'Mature Zone', interval_seconds: 60 },
];

// Handlers
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
    const body = await request.json() as Record<string, unknown>;
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
      headers: {
        'Content-Type': 'text/plain',
      },
    });
  }),

  // Database Endpoints
  http.get('*/api/database/streams/stats', () => {
    return HttpResponse.json(mockStreamStatsResponse);
  }),

  http.get('*/api/database/phases', () => {
    return HttpResponse.json(mockPhasesResponse);
  }),

  // Analytics Endpoint
  http.get('*/api/analytics/:mint', ({ params }) => {
    const { mint } = params;
    return HttpResponse.json({
      mint,
      current_price: 0.00001234,
      last_updated: new Date().toISOString(),
      is_active: true,
      performance: {
        '1m': {
          price_change: 5.5,
          volume: 10.0,
          trades: 50,
          trend: '🚀 PUMP',
          data_found: true,
          data_age_seconds: 30,
        },
        '5m': {
          price_change: -2.3,
          volume: 45.0,
          trades: 200,
          trend: '📉 DUMP',
          data_found: true,
          data_age_seconds: 150,
        },
      },
    });
  }),

  // Test n8n Endpoint
  http.post('*/test/n8n', () => {
    return HttpResponse.json({
      available: true,
      status_code: 200,
      response_time_ms: 45,
    });
  }),
];

// Error Handlers für Tests
export const errorHandlers = {
  healthError: http.get('*/api/health', () => {
    return HttpResponse.json(
      { error: 'Service unavailable' },
      { status: 503 }
    );
  }),

  configError: http.get('*/api/config', () => {
    return HttpResponse.json(
      { error: 'Failed to load config' },
      { status: 500 }
    );
  }),

  networkError: http.get('*/api/health', () => {
    return HttpResponse.error();
  }),
};

// Degraded State Handler
export const degradedHealthHandler = http.get('*/api/health', () => {
  return HttpResponse.json({
    ...mockHealthResponse,
    status: 'degraded',
    ws_connected: false,
    last_error: 'WebSocket connection lost',
  });
});
