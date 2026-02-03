import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
  TextField,
  Alert,
  Chip,
  Divider,
} from '@mui/material';
import { Refresh as RefreshIcon, Download as DownloadIcon } from '@mui/icons-material';
import { pumpApi } from '../services/api';

const Logs: React.FC = () => {
  const [logs, setLogs] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(30); // Sekunden

  const fetchLogs = async () => {
    try {
      setIsLoading(true);
      setError('');

      // Für echte Logs würden wir eine Logs-API brauchen
      // Hier simulieren wir es mit den Health-Daten
      const health = await pumpApi.getHealth();

      const logEntries = [
        `[${new Date().toISOString()}] Service Status: ${health.status}`,
        `[${new Date().toISOString()}] WebSocket: ${health.ws_connected ? 'Connected' : 'Disconnected'}`,
        `[${new Date().toISOString()}] Database: ${health.db_connected ? 'Connected' : 'Disconnected'}`,
        `[${new Date().toISOString()}] Cache: ${health.cache_stats.total_coins} Coins`,
        `[${new Date().toISOString()}] Discovery: ${health.discovery_stats.total_coins_discovered} Coins gefunden`,
        `[${new Date().toISOString()}] Tracking: ${health.tracking_stats.active_coins} aktive Coins`,
        `[${new Date().toISOString()}] Trades: ${health.tracking_stats.total_trades} Gesamt-Trades`,
        `[${new Date().toISOString()}] Uptime: ${Math.floor(health.uptime_seconds / 3600)}h ${Math.floor((health.uptime_seconds % 3600) / 60)}m`,
        health.last_error ? `[${new Date().toISOString()}] ERROR: ${health.last_error}` : `[${new Date().toISOString()}] No errors`,
      ];

      setLogs(prevLogs => [...logEntries, ...prevLogs.slice(0, 50)]); // Behalte letzte 50 Einträge
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch logs');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs(); // Initial load
  }, []);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(fetchLogs, refreshInterval * 1000);
    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval]);

  const handleDownloadLogs = () => {
    const logText = logs.join('\n');
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `pump-service-logs-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getLogLevelColor = (log: string) => {
    if (log.includes('ERROR')) return 'error';
    if (log.includes('WARN')) return 'warning';
    if (log.includes('Connected')) return 'success';
    if (log.includes('Disconnected')) return 'error';
    return 'default';
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box display="flex" flexDirection={{ xs: 'column', sm: 'row' }} justifyContent="space-between" alignItems={{ xs: 'flex-start', sm: 'center' }} gap={2} sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ fontSize: { xs: '1.5rem', md: '2.125rem' } }}>
          📋 Service Logs
        </Typography>

        <Box display="flex" gap={1} flexWrap="wrap" justifyContent={{ xs: 'flex-start', sm: 'flex-end' }}>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleDownloadLogs}
            disabled={logs.length === 0}
            size="small"
          >
            Download
          </Button>

          <Button
            variant={autoRefresh ? "contained" : "outlined"}
            startIcon={<RefreshIcon />}
            onClick={() => setAutoRefresh(!autoRefresh)}
            color={autoRefresh ? "primary" : "inherit"}
            size="small"
          >
            Auto {autoRefresh ? 'ON' : 'OFF'}
          </Button>

          <Button
            variant="contained"
            startIcon={<RefreshIcon />}
            onClick={fetchLogs}
            disabled={isLoading}
            size="small"
          >
            {isLoading ? 'Loading...' : 'Refresh'}
          </Button>
        </Box>
      </Box>

      {autoRefresh && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Auto-Refresh aktiviert: Aktualisierung alle {refreshInterval} Sekunden
          <TextField
            type="number"
            size="small"
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(parseInt(e.target.value) || 30)}
            inputProps={{ min: 5, max: 300 }}
            sx={{ ml: 2, width: 80 }}
          />
          Sekunden
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: { xs: 1.5, md: 2 }, height: { xs: '60vh', md: '70vh' }, overflow: 'auto' }}>
        <Typography variant="h6" gutterBottom>
          Service Activity Log
        </Typography>

        <Divider sx={{ mb: 2 }} />

        {logs.length === 0 ? (
          <Typography color="textSecondary" sx={{ textAlign: 'center', py: 4 }}>
            No logs available. Click "Refresh" to load service status.
          </Typography>
        ) : (
          <Box sx={{ fontFamily: 'monospace', fontSize: { xs: '0.75rem', md: '0.875rem' } }}>
            {logs.map((log, index) => (
              <Box key={index} sx={{ mb: 0.5, display: 'flex', alignItems: 'flex-start', flexDirection: { xs: 'column', sm: 'row' }, gap: { xs: 0.5, sm: 0 } }}>
                <Chip
                  label={log.split(']')[0].substring(1)}
                  size="small"
                  color={getLogLevelColor(log)}
                  sx={{
                    mr: { sm: 1 },
                    fontSize: { xs: '0.7rem', md: '0.75rem' },
                    minHeight: { xs: 24, md: 24 },
                    height: 'auto'
                  }}
                />
                <Typography variant="body2" sx={{ flex: 1, fontSize: { xs: '0.75rem', md: '0.875rem' }, wordBreak: 'break-word' }}>
                  {log.split(']')[1]?.substring(1) || log}
                </Typography>
              </Box>
            ))}
          </Box>
        )}
      </Paper>

      <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
        {logs.length} Log-Einträge • Letzte Aktualisierung: {new Date().toLocaleTimeString()}
      </Typography>
    </Container>
  );
};

export default Logs;


