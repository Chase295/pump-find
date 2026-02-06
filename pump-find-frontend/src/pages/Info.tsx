import React from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  useTheme,
  useMediaQuery,
  Chip,
  Divider,
  Grid,
} from '@mui/material';
import {
  Info as InfoIcon,
  Timeline as TimelineIcon,
  Analytics as AnalyticsIcon,
  Speed as SpeedIcon,
  CheckCircle as CheckCircleIcon,
  ExpandMore as ExpandMoreIcon,
  Storage as StorageIcon,
  Settings as SettingsIcon,
  Schedule as ScheduleIcon,
  SmartToy as SmartToyIcon,
} from '@mui/icons-material';
import { usePumpStore } from '../stores/pumpStore';

// Responsive Code Block Component
const CodeBlock: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <Box sx={{
    bgcolor: 'rgba(0,0,0,0.3)',
    p: { xs: 1.5, sm: 2 },
    borderRadius: 1,
    mb: 2,
    overflowX: 'auto',
    '&::-webkit-scrollbar': { height: 6 },
    '&::-webkit-scrollbar-thumb': { bgcolor: 'rgba(255,255,255,0.2)', borderRadius: 3 },
  }}>
    <Typography
      component="pre"
      variant="body2"
      sx={{
        fontFamily: 'monospace',
        fontSize: { xs: '0.7rem', sm: '0.8rem' },
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
        m: 0,
      }}
    >
      {children}
    </Typography>
  </Box>
);

// Config Item Component for mobile-friendly config display
const ConfigItem: React.FC<{
  name: string;
  value: string;
  range?: string;
  desc: string;
  color?: string;
}> = ({ name, value, range, desc, color = '#4caf50' }) => (
  <Box sx={{
    mb: 2,
    p: { xs: 1.5, sm: 2 },
    bgcolor: 'rgba(0,0,0,0.2)',
    borderRadius: 1,
    borderLeft: `3px solid ${color}`,
  }}>
    <Typography variant="body2" sx={{ fontWeight: 'bold', color, mb: 0.5, fontSize: { xs: '0.8rem', sm: '0.875rem' } }}>
      {name}
    </Typography>
    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 0.5 }}>
      <Chip label={`Default: ${value}`} size="small" sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' } }} />
      {range && <Chip label={`Range: ${range}`} size="small" variant="outlined" sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' } }} />}
    </Box>
    <Typography variant="body2" sx={{ color: 'text.secondary', fontSize: { xs: '0.75rem', sm: '0.8rem' } }}>
      {desc}
    </Typography>
  </Box>
);

// Phase Item Component
const PhaseItem: React.FC<{
  name: string;
  interval: string;
  range: string;
  desc: string;
  color: string;
}> = ({ name, interval, range, desc, color }) => (
  <Box sx={{
    p: { xs: 1.5, sm: 2 },
    bgcolor: 'rgba(0,0,0,0.2)',
    borderRadius: 1,
    borderLeft: `3px solid ${color}`,
    mb: 1,
  }}>
    <Typography variant="body2" sx={{ fontWeight: 'bold', color, fontSize: { xs: '0.85rem', sm: '0.9rem' } }}>
      {name}
    </Typography>
    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
      <Chip label={interval} size="small" sx={{ fontSize: { xs: '0.65rem', sm: '0.7rem' } }} />
      <Chip label={range} size="small" variant="outlined" sx={{ fontSize: { xs: '0.65rem', sm: '0.7rem' } }} />
    </Box>
    <Typography variant="body2" sx={{ color: 'text.secondary', mt: 0.5, fontSize: { xs: '0.7rem', sm: '0.75rem' } }}>
      {desc}
    </Typography>
  </Box>
);

// API Endpoint Component
const ApiEndpoint: React.FC<{
  method: string;
  path: string;
  desc: string;
  details?: string;
  color?: string;
}> = ({ method, path, desc, details, color = '#00d4ff' }) => (
  <Box sx={{
    mb: 2,
    p: { xs: 1.5, sm: 2 },
    bgcolor: 'rgba(0,0,0,0.2)',
    borderRadius: 1,
  }}>
    <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 1, mb: 1 }}>
      <Chip
        label={method}
        size="small"
        sx={{
          bgcolor: method === 'GET' ? '#4caf50' : method === 'PUT' ? '#ff9800' : method === 'POST' ? '#2196f3' : '#f44336',
          color: 'white',
          fontWeight: 'bold',
          fontSize: { xs: '0.65rem', sm: '0.7rem' },
        }}
      />
      <Typography
        variant="body2"
        sx={{
          fontFamily: 'monospace',
          color,
          fontWeight: 'bold',
          fontSize: { xs: '0.75rem', sm: '0.85rem' },
          wordBreak: 'break-all',
        }}
      >
        {path}
      </Typography>
    </Box>
    <Typography variant="body2" sx={{ mb: details ? 1 : 0, fontSize: { xs: '0.75rem', sm: '0.8rem' } }}>
      {desc}
    </Typography>
    {details && (
      <Typography variant="body2" sx={{ color: 'text.secondary', fontSize: { xs: '0.7rem', sm: '0.75rem' } }}>
        {details}
      </Typography>
    )}
  </Box>
);

const Info: React.FC = () => {
  const { health } = usePumpStore();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  // Live-Statistiken aus health-Daten berechnen
  const activeStreams = health?.tracking_stats?.active_coins || 0;
  const totalStreams = health?.discovery_stats?.total_coins_discovered || 0;
  const cacheSize = health?.cache_stats?.total_coins || 0;

  return (
    <Container maxWidth="lg" sx={{ py: { xs: 2, sm: 4 }, px: { xs: 1, sm: 2, md: 3 } }}>
      {/* Header */}
      <Box sx={{ textAlign: 'center', mb: { xs: 3, sm: 6 } }}>
        <Typography
          variant={isMobile ? "h5" : "h4"}
          gutterBottom
          sx={{ color: '#00d4ff', fontWeight: 'bold' }}
        >
          System-Dokumentation
        </Typography>
        <Typography
          variant="body2"
          sx={{ color: 'text.secondary', mb: 2, fontSize: { xs: '0.8rem', sm: '0.9rem' } }}
        >
          Pump Find System
        </Typography>
        <Alert severity="info" sx={{ maxWidth: 800, mx: 'auto', '& .MuiAlert-message': { fontSize: { xs: '0.75rem', sm: '0.875rem' } } }}>
          Vollständige Dokumentation aller Datenbank-Einträge, Berechnungen und Datenflüsse.
        </Alert>
      </Box>

      {/* Live Stats Bar */}
      <Card sx={{ mb: 3, bgcolor: 'rgba(0, 212, 255, 0.1)', border: '1px solid rgba(0, 212, 255, 0.3)' }}>
        <CardContent sx={{ py: { xs: 1.5, sm: 2 }, '&:last-child': { pb: { xs: 1.5, sm: 2 } } }}>
          <Grid container spacing={{ xs: 1, sm: 2 }}>
            <Grid size={{ xs: 4 }}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant={isMobile ? "body1" : "h6"} sx={{ color: '#00d4ff', fontWeight: 'bold' }}>
                  {activeStreams}
                </Typography>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: { xs: '0.6rem', sm: '0.75rem' } }}>
                  Aktive Coins
                </Typography>
              </Box>
            </Grid>
            <Grid size={{ xs: 4 }}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant={isMobile ? "body1" : "h6"} sx={{ color: '#00d4ff', fontWeight: 'bold' }}>
                  {totalStreams}
                </Typography>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: { xs: '0.6rem', sm: '0.75rem' } }}>
                  Entdeckt
                </Typography>
              </Box>
            </Grid>
            <Grid size={{ xs: 4 }}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant={isMobile ? "body1" : "h6"} sx={{ color: health?.ws_connected ? '#4caf50' : '#f44336', fontWeight: 'bold' }}>
                  {health?.ws_connected ? 'Online' : 'Offline'}
                </Typography>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: { xs: '0.6rem', sm: '0.75rem' } }}>
                  WebSocket
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* 0. Architecture Overview */}
      <Accordion defaultExpanded sx={{ mb: 2, bgcolor: 'rgba(76, 175, 80, 0.1)', border: '1px solid rgba(76, 175, 80, 0.3)' }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CheckCircleIcon sx={{ color: '#4caf50', fontSize: { xs: 20, sm: 24 } }} />
            <Typography variant={isMobile ? "body1" : "h6"} sx={{ color: '#4caf50', fontWeight: 'bold' }}>
              Single-Port-Architektur
            </Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Alert severity="success" sx={{ mb: 2, '& .MuiAlert-message': { fontSize: { xs: '0.75rem', sm: '0.875rem' } } }}>
            Nur 1 Port (3001) exposed - UI + API
          </Alert>

          <CodeBlock>
{`EXTERNER ZUGRIFF (Coolify):
- Port: 3001
- UI: https://deine-domain.com
- API: https://deine-domain.com/api/*

INTERNE ARCHITEKTUR:
┌──────────────────┐    ┌──────────────────┐
│ pump-find-       │◄──►│ pump-find-       │
│ frontend         │    │ backend          │
│ Port 3001        │    │ Port 8000        │
│ Nginx Proxy      │    │ Nur intern       │
└──────────────────┘    └──────────────────┘
     │
     ▼
/api/* → pump-find-backend:8000
UI    → static files`}
          </CodeBlock>
        </AccordionDetails>
      </Accordion>

      {/* 1. System Architecture */}
      <Accordion sx={{ mb: 2, bgcolor: 'rgba(0, 212, 255, 0.1)', border: '1px solid rgba(0, 212, 255, 0.3)' }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <InfoIcon sx={{ color: '#00d4ff', fontSize: { xs: 20, sm: 24 } }} />
            <Typography variant={isMobile ? "body1" : "h6"} sx={{ color: '#00d4ff', fontWeight: 'bold' }}>
              1. System-Architektur
            </Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 6 }}>
              <Card sx={{ bgcolor: 'rgba(76, 175, 80, 0.1)', border: '1px solid rgba(76, 175, 80, 0.3)', height: '100%' }}>
                <CardContent sx={{ p: { xs: 1.5, sm: 2 } }}>
                  <Typography variant="body1" sx={{ color: '#4caf50', mb: 1, fontWeight: 'bold', fontSize: { xs: '0.9rem', sm: '1rem' } }}>
                    Discovery (Phase 0)
                  </Typography>
                  <Typography variant="body2" sx={{ fontSize: { xs: '0.75rem', sm: '0.8rem' } }}>
                    <strong>Funktion:</strong> Neue Coins entdecken<br/>
                    <strong>Quelle:</strong> WebSocket PumpPortal<br/>
                    <strong>Filter:</strong> Spam, Bad Names<br/>
                    <strong>Output:</strong> discovered_coins
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <Card sx={{ bgcolor: 'rgba(255, 152, 0, 0.1)', border: '1px solid rgba(255, 152, 0, 0.3)', height: '100%' }}>
                <CardContent sx={{ p: { xs: 1.5, sm: 2 } }}>
                  <Typography variant="body1" sx={{ color: '#ff9800', mb: 1, fontWeight: 'bold', fontSize: { xs: '0.9rem', sm: '1rem' } }}>
                    Metric Tracking (Phase 1+)
                  </Typography>
                  <Typography variant="body2" sx={{ fontSize: { xs: '0.75rem', sm: '0.8rem' } }}>
                    <strong>Funktion:</strong> Live-Trade-Tracking<br/>
                    <strong>Quelle:</strong> WebSocket + Buffer<br/>
                    <strong>Berechnungen:</strong> Metriken, Dev, Whale<br/>
                    <strong>Output:</strong> coin_metrics
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* 2. Phase 0: Discovery */}
      <Accordion sx={{ mb: 2, bgcolor: 'rgba(76, 175, 80, 0.1)', border: '1px solid rgba(76, 175, 80, 0.3)' }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <TimelineIcon sx={{ color: '#4caf50', fontSize: { xs: 20, sm: 24 } }} />
            <Typography variant={isMobile ? "body1" : "h6"} sx={{ color: '#4caf50', fontWeight: 'bold' }}>
              2. Phase 0: Coin Discovery
            </Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="body2" sx={{ mb: 2, fontWeight: 'bold', color: '#4caf50', fontSize: { xs: '0.8rem', sm: '0.9rem' } }}>
            WebSocket-Verbindung zu PumpPortal
          </Typography>
          <CodeBlock>
{`Empfangene Daten pro Coin:
- mint: Token-Adresse
- name, symbol: Token-Name
- traderPublicKey: Creator-Wallet
- vSolInBondingCurve: Virtuelles SOL
- marketCapSol: Market Cap
- uri: Metadata-URI`}
          </CodeBlock>

          <Typography variant="body2" sx={{ mb: 2, fontWeight: 'bold', color: '#4caf50', fontSize: { xs: '0.8rem', sm: '0.9rem' } }}>
            Spam-Filterung
          </Typography>
          <Box sx={{ mb: 2 }}>
            <ConfigItem
              name="Bad Names Regex"
              value="test|bot|rug|scam|cant|honey|faucet"
              desc="Filtert Coins mit verdächtigen Namen"
            />
            <ConfigItem
              name="Spam-Burst Filter"
              value="Max 3 Coins/Minute"
              desc="Blockiert Massen-Erstellungen von gleicher Wallet"
            />
          </Box>

          <Typography variant="body2" sx={{ mb: 2, fontWeight: 'bold', color: '#4caf50', fontSize: { xs: '0.8rem', sm: '0.9rem' } }}>
            API-Daten-Abruf
          </Typography>
          <CodeBlock>
{`RugCheck API:
- decimals, supply
- risk_score, metadata_is_mutable

Metadata (IPFS/Arweave):
- description, image
- twitter, telegram, website, discord
- has_socials, social_count`}
          </CodeBlock>
        </AccordionDetails>
      </Accordion>

      {/* 3. Phase Management - NEW */}
      <Accordion sx={{ mb: 2, bgcolor: 'rgba(156, 39, 176, 0.1)', border: '1px solid rgba(156, 39, 176, 0.3)' }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ScheduleIcon sx={{ color: '#9c27b0', fontSize: { xs: 20, sm: 24 } }} />
            <Typography variant={isMobile ? "body1" : "h6"} sx={{ color: '#9c27b0', fontWeight: 'bold' }}>
              3. Phasen-Management
            </Typography>
            <Chip label="NEU" size="small" color="secondary" sx={{ ml: 1, fontSize: { xs: '0.6rem', sm: '0.7rem' } }} />
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Alert severity="info" sx={{ mb: 2, '& .MuiAlert-message': { fontSize: { xs: '0.75rem', sm: '0.875rem' } } }}>
            Phasen sind jetzt vollständig verwaltbar - Erstellen, Bearbeiten und Löschen!
          </Alert>

          <Typography variant="body2" sx={{ mb: 2, fontWeight: 'bold', color: '#9c27b0', fontSize: { xs: '0.8rem', sm: '0.9rem' } }}>
            Standard-Phasen
          </Typography>

          <PhaseItem
            name="Baby Zone (Phase 1)"
            interval="5 Sekunden"
            range="0-10 Minuten"
            desc="Sehr junge Coins, häufige Metriken-Updates"
            color="#4caf50"
          />
          <PhaseItem
            name="Survival Zone (Phase 2)"
            interval="30 Sekunden"
            range="10-60 Minuten"
            desc="Coins die erste 10 Minuten überlebt haben"
            color="#ff9800"
          />
          <PhaseItem
            name="Mature Zone (Phase 3)"
            interval="60 Sekunden"
            range="1-24 Stunden"
            desc="Etablierte Coins, weniger häufige Updates"
            color="#2196f3"
          />

          <Divider sx={{ my: 2 }} />

          <Typography variant="body2" sx={{ mb: 2, fontWeight: 'bold', color: '#9c27b0', fontSize: { xs: '0.8rem', sm: '0.9rem' } }}>
            System-Phasen (nicht editierbar)
          </Typography>

          <PhaseItem
            name="Finished (Phase 99)"
            interval="Gestoppt"
            range="24h+"
            desc="Tracking beendet (zu alt)"
            color="#f44336"
          />
          <PhaseItem
            name="Graduated (Phase 100)"
            interval="Gestoppt"
            range="-"
            desc="Token hat Bonding Curve verlassen (Raydium)"
            color="#9c27b0"
          />

          <Divider sx={{ my: 2 }} />

          <Typography variant="body2" sx={{ mb: 2, fontWeight: 'bold', color: '#9c27b0', fontSize: { xs: '0.8rem', sm: '0.9rem' } }}>
            API Endpunkte
          </Typography>

          <ApiEndpoint
            method="GET"
            path="/api/database/phases"
            desc="Alle Phasen abrufen"
            color="#9c27b0"
          />
          <ApiEndpoint
            method="PUT"
            path="/api/database/phases/{id}"
            desc="Phase aktualisieren"
            details="Felder: name, interval_seconds, min_age_minutes, max_age_minutes"
            color="#9c27b0"
          />
          <ApiEndpoint
            method="POST"
            path="/api/database/phases"
            desc="Neue Phase erstellen"
            details="Automatische ID-Vergabe (1-98)"
            color="#9c27b0"
          />
          <ApiEndpoint
            method="DELETE"
            path="/api/database/phases/{id}"
            desc="Phase löschen"
            details="Streams werden zur nächsten Phase migriert"
            color="#9c27b0"
          />

          <Alert severity="warning" sx={{ mt: 2, '& .MuiAlert-message': { fontSize: { xs: '0.75rem', sm: '0.875rem' } } }}>
            Nach Phasen-Änderungen werden aktive Streams automatisch neu konfiguriert!
          </Alert>
        </AccordionDetails>
      </Accordion>

      {/* 4. Live Tracking */}
      <Accordion sx={{ mb: 2, bgcolor: 'rgba(255, 152, 0, 0.1)', border: '1px solid rgba(255, 152, 0, 0.3)' }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AnalyticsIcon sx={{ color: '#ff9800', fontSize: { xs: 20, sm: 24 } }} />
            <Typography variant={isMobile ? "body1" : "h6"} sx={{ color: '#ff9800', fontWeight: 'bold' }}>
              4. Live-Tracking
            </Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="body2" sx={{ mb: 2, fontWeight: 'bold', color: '#ff9800', fontSize: { xs: '0.8rem', sm: '0.9rem' } }}>
            Trade-Verarbeitung
          </Typography>
          <CodeBlock>
{`Preis-Berechnung:
price = vSolInBondingCurve / vTokensInBondingCurve

Volumen-Akkumulation:
volume_sol += solAmount
buy_volume_sol  (wenn txType == "buy")
sell_volume_sol (wenn txType == "sell")

Trade-Zählung:
num_buys, num_sells, unique_wallets`}
          </CodeBlock>

          <Typography variant="body2" sx={{ mb: 2, fontWeight: 'bold', color: '#ff9800', fontSize: { xs: '0.8rem', sm: '0.9rem' } }}>
            Metrik-Speicherung
          </Typography>
          <CodeBlock>
{`INSERT INTO coin_metrics (
  mint, timestamp, phase_id_at_time,
  price_open, price_high, price_low, price_close,
  market_cap_close, bonding_curve_pct,
  volume_sol, buy_volume_sol, sell_volume_sol,
  num_buys, num_sells, unique_wallets,
  dev_sold_amount, whale_buy_volume_sol
)`}
          </CodeBlock>
        </AccordionDetails>
      </Accordion>

      {/* 5. API Documentation */}
      <Accordion sx={{ mb: 2, bgcolor: 'rgba(0, 212, 255, 0.1)', border: '1px solid rgba(0, 212, 255, 0.3)' }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <StorageIcon sx={{ color: '#00d4ff', fontSize: { xs: 20, sm: 24 } }} />
            <Typography variant={isMobile ? "body1" : "h6"} sx={{ color: '#00d4ff', fontWeight: 'bold' }}>
              5. API-Dokumentation
            </Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="body2" sx={{ mb: 2, fontWeight: 'bold', color: '#00d4ff', fontSize: { xs: '0.8rem', sm: '0.9rem' } }}>
            System-Endpunkte
          </Typography>

          <ApiEndpoint
            method="GET"
            path="/api/health"
            desc="System-Status & Live-Daten"
            details="ws_connected, db_connected, uptime, cache_stats, tracking_stats"
          />
          <ApiEndpoint
            method="GET"
            path="/api/config"
            desc="Aktuelle Konfiguration"
          />
          <ApiEndpoint
            method="PUT"
            path="/api/config"
            desc="Konfiguration ändern"
            details="Runtime-Änderungen ohne Neustart"
          />
          <ApiEndpoint
            method="GET"
            path="/api/metrics"
            desc="Prometheus-Metriken"
            details="Format: text/plain"
          />

          <Divider sx={{ my: 2 }} />

          <Typography variant="body2" sx={{ mb: 2, fontWeight: 'bold', color: '#00d4ff', fontSize: { xs: '0.8rem', sm: '0.9rem' } }}>
            Datenbank-Endpunkte
          </Typography>

          <ApiEndpoint
            method="GET"
            path="/api/database/streams/stats"
            desc="Stream-Statistiken"
            details="total_streams, active_streams, streams_by_phase"
          />
          <ApiEndpoint
            method="GET"
            path="/api/database/streams?limit=50"
            desc="Einzelne Streams"
          />
          <ApiEndpoint
            method="GET"
            path="/api/database/metrics?limit=100&mint=..."
            desc="Historische Metriken (OHLCV)"
          />

          <Divider sx={{ my: 2 }} />

          <Typography variant="body2" sx={{ mb: 2, fontWeight: 'bold', color: '#00d4ff', fontSize: { xs: '0.8rem', sm: '0.9rem' } }}>
            Analytics-Endpunkt
          </Typography>

          <ApiEndpoint
            method="GET"
            path="/api/analytics/{TOKEN_ADDRESS}"
            desc="Coin Vitalwerte & Performance"
            details="Parameter: windows (z.B. 1m,5m,1h) - Preisänderungen, Trends (PUMP/DUMP/FLAT)"
          />

          <CodeBlock>
{`Beispiel-Response:
{
  "mint": "91WNez8D...",
  "current_price": 0.00001234,
  "performance": {
    "1m": {
      "price_change_pct": -2.5,
      "trend": "DUMP",
      "data_age_seconds": 45
    }
  }
}`}
          </CodeBlock>
        </AccordionDetails>
      </Accordion>

      {/* 6. Configuration */}
      <Accordion sx={{ mb: 2, bgcolor: 'rgba(76, 175, 80, 0.1)', border: '1px solid rgba(76, 175, 80, 0.3)' }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SettingsIcon sx={{ color: '#4caf50', fontSize: { xs: 20, sm: 24 } }} />
            <Typography variant={isMobile ? "body1" : "h6"} sx={{ color: '#4caf50', fontWeight: 'bold' }}>
              6. Konfiguration
            </Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="body2" sx={{ mb: 2, fontWeight: 'bold', color: '#4caf50', fontSize: { xs: '0.8rem', sm: '0.9rem' } }}>
            Datenbank
          </Typography>
          <ConfigItem
            name="DB_DSN"
            value="postgresql://..."
            desc="PostgreSQL-Verbindungsstring"
          />
          <ConfigItem
            name="DB_REFRESH_INTERVAL"
            value="10"
            range="5-300"
            desc="Intervall für DB-Abfragen (Sekunden)"
          />

          <Divider sx={{ my: 2 }} />

          <Typography variant="body2" sx={{ mb: 2, fontWeight: 'bold', color: '#4caf50', fontSize: { xs: '0.8rem', sm: '0.9rem' } }}>
            Discovery & Filter
          </Typography>
          <ConfigItem
            name="COIN_CACHE_SECONDS"
            value="120"
            range="10-3600"
            desc="Cache-Dauer für neue Coins"
          />
          <ConfigItem
            name="BAD_NAMES_PATTERN"
            value="test|bot|rug|scam"
            desc="Regex für Coin-Filterung"
          />
          <ConfigItem
            name="SPAM_BURST_WINDOW"
            value="30"
            range="1-300"
            desc="Zeitfenster für Spam-Erkennung (Sekunden)"
          />

          <Divider sx={{ my: 2 }} />

          <Typography variant="body2" sx={{ mb: 2, fontWeight: 'bold', color: '#4caf50', fontSize: { xs: '0.8rem', sm: '0.9rem' } }}>
            n8n Integration
          </Typography>
          <ConfigItem
            name="N8N_WEBHOOK_URL"
            value="https://..."
            desc="Webhook-URL für Coin-Benachrichtigungen"
          />
          <ConfigItem
            name="BATCH_SIZE"
            value="10"
            range="1-100"
            desc="Coins pro Batch"
          />
          <ConfigItem
            name="BATCH_TIMEOUT"
            value="30"
            range="5-300"
            desc="Max. Wartezeit für Batch (Sekunden)"
          />

          <Divider sx={{ my: 2 }} />

          <Typography variant="body2" sx={{ mb: 2, fontWeight: 'bold', color: '#4caf50', fontSize: { xs: '0.8rem', sm: '0.9rem' } }}>
            Tracking
          </Typography>
          <ConfigItem
            name="SOL_RESERVES_FULL"
            value="85.0"
            desc="Schwellwert für Bonding Curve Full (%)"
          />
          <ConfigItem
            name="WHALE_THRESHOLD_SOL"
            value="1.0"
            desc="Schwellwert für Whale-Trades (SOL)"
          />
          <ConfigItem
            name="TRADE_BUFFER_SECONDS"
            value="180"
            desc="Puffer für Trade-Aggregation (Sekunden)"
          />
        </AccordionDetails>
      </Accordion>

      {/* 7. Docker & Deployment */}
      <Accordion sx={{ mb: 2, bgcolor: 'rgba(244, 67, 54, 0.1)', border: '1px solid rgba(244, 67, 54, 0.3)' }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SpeedIcon sx={{ color: '#f44336', fontSize: { xs: 20, sm: 24 } }} />
            <Typography variant={isMobile ? "body1" : "h6"} sx={{ color: '#f44336', fontWeight: 'bold' }}>
              7. Docker & Deployment
            </Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="body2" sx={{ mb: 2, fontWeight: 'bold', color: '#f44336', fontSize: { xs: '0.8rem', sm: '0.9rem' } }}>
            Container-Architektur
          </Typography>
          <CodeBlock>
{`pump-find-backend (API Backend):
- Image: python:3.11-slim
- Port: 8000 (nur intern)
- Volume: ./config:/app/config

pump-find-frontend (UI + Reverse Proxy):
- Build: node:22-alpine → nginx:alpine
- Port: 3001 (extern)
- Nginx: /api/* → pump-find-backend:8000`}
          </CodeBlock>

          <Typography variant="body2" sx={{ mb: 2, fontWeight: 'bold', color: '#f44336', fontSize: { xs: '0.8rem', sm: '0.9rem' } }}>
            Befehle
          </Typography>
          <CodeBlock>
{`# Starten
docker-compose up -d

# Logs
docker-compose logs -f

# Neu bauen
docker-compose build --no-cache

# Stoppen
docker-compose down`}
          </CodeBlock>

          <Typography variant="body2" sx={{ mb: 2, fontWeight: 'bold', color: '#f44336', fontSize: { xs: '0.8rem', sm: '0.9rem' } }}>
            Troubleshooting
          </Typography>
          <CodeBlock>
{`# Container Status
docker ps

# API testen
curl http://localhost:3001/api/health

# Ressourcen
docker stats pump-find-backend pump-find-frontend

# Unhealthy Container
docker ps --filter "health=unhealthy"`}
          </CodeBlock>
        </AccordionDetails>
      </Accordion>

      {/* 8. Web UI */}
      <Accordion sx={{ mb: 2, bgcolor: 'rgba(156, 39, 176, 0.1)', border: '1px solid rgba(156, 39, 176, 0.3)' }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <TimelineIcon sx={{ color: '#9c27b0', fontSize: { xs: 20, sm: 24 } }} />
            <Typography variant={isMobile ? "body1" : "h6"} sx={{ color: '#9c27b0', fontWeight: 'bold' }}>
              8. Web UI Architektur
            </Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="body2" sx={{ mb: 2, fontWeight: 'bold', color: '#9c27b0', fontSize: { xs: '0.8rem', sm: '0.9rem' } }}>
            Technologie-Stack
          </Typography>
          <CodeBlock>
{`Framework: React 18 + TypeScript
Build-Tool: Vite 5.4
UI-Library: Material-UI v7
State: Zustand v5
HTTP: Axios v1.13
Charts: Recharts v3.6`}
          </CodeBlock>

          <Typography variant="body2" sx={{ mb: 2, fontWeight: 'bold', color: '#9c27b0', fontSize: { xs: '0.8rem', sm: '0.9rem' } }}>
            Seiten
          </Typography>
          <Grid container spacing={1}>
            {[
              { name: 'Dashboard', desc: 'Hauptübersicht mit Live-Status' },
              { name: 'Metrics', desc: 'Statistiken & Charts' },
              { name: 'Phasen', desc: 'Phase-Management (CRUD)' },
              { name: 'Config', desc: 'Runtime-Konfiguration' },
              { name: 'Info', desc: 'Diese Dokumentation' },
              { name: 'Logs', desc: 'System-Logs' },
            ].map((page) => (
              <Grid key={page.name} size={{ xs: 6, sm: 4 }}>
                <Box sx={{ p: 1, bgcolor: 'rgba(0,0,0,0.2)', borderRadius: 1, textAlign: 'center' }}>
                  <Typography variant="body2" sx={{ fontWeight: 'bold', color: '#9c27b0', fontSize: { xs: '0.75rem', sm: '0.85rem' } }}>
                    {page.name}
                  </Typography>
                  <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: { xs: '0.6rem', sm: '0.7rem' } }}>
                    {page.desc}
                  </Typography>
                </Box>
              </Grid>
            ))}
          </Grid>

          <Divider sx={{ my: 2 }} />

          <Typography variant="body2" sx={{ mb: 2, fontWeight: 'bold', color: '#9c27b0', fontSize: { xs: '0.8rem', sm: '0.9rem' } }}>
            Auto-Refresh
          </Typography>
          <CodeBlock>
{`Health-Daten: alle 5 Sekunden
Stream-Stats: alle 10 Sekunden
Config: einmalig beim Laden`}
          </CodeBlock>
        </AccordionDetails>
      </Accordion>

      {/* 9. MCP Server */}
      <Accordion sx={{ mb: 2, bgcolor: 'rgba(0, 188, 212, 0.1)', border: '1px solid rgba(0, 188, 212, 0.3)' }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SmartToyIcon sx={{ color: '#00bcd4', fontSize: { xs: 20, sm: 24 } }} />
            <Typography variant={isMobile ? "body1" : "h6"} sx={{ color: '#00bcd4', fontWeight: 'bold' }}>
              9. MCP Server (Model Context Protocol)
            </Typography>
            <Chip label="NEU" size="small" sx={{ ml: 1, fontSize: { xs: '0.6rem', sm: '0.7rem' }, bgcolor: '#00bcd4', color: 'white' }} />
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Alert severity="info" sx={{ mb: 2, '& .MuiAlert-message': { fontSize: { xs: '0.75rem', sm: '0.875rem' } } }}>
            AI-Assistenten (Claude Code, Claude Desktop, Cursor) können per MCP direkt mit dem Service interagieren.
          </Alert>

          <Typography variant="body2" sx={{ mb: 2, fontWeight: 'bold', color: '#00bcd4', fontSize: { xs: '0.8rem', sm: '0.9rem' } }}>
            Verbindung
          </Typography>
          <CodeBlock>
{`MCP Transport: SSE (Server-Sent Events)

Direkt (intern):  http://localhost:8000/mcp
Via Nginx (extern): http://localhost:3001/api/mcp

Messages-Endpoint: POST /mcp/messages/?session_id=...`}
          </CodeBlock>

          <Typography variant="body2" sx={{ mb: 2, fontWeight: 'bold', color: '#00bcd4', fontSize: { xs: '0.8rem', sm: '0.9rem' } }}>
            Verfügbare MCP-Tools ({14})
          </Typography>

          <Grid container spacing={1} sx={{ mb: 2 }}>
            {[
              { name: 'get_health', desc: 'Service-Status & Live-Daten', cat: 'System' },
              { name: 'get_metrics', desc: 'Prometheus-Metriken', cat: 'System' },
              { name: 'get_config', desc: 'Konfiguration lesen', cat: 'Config' },
              { name: 'update_config', desc: 'Konfiguration ändern', cat: 'Config' },
              { name: 'reload_config', desc: 'Config + Phasen neu laden', cat: 'Config' },
              { name: 'list_phases', desc: 'Alle Phasen auflisten', cat: 'Phasen' },
              { name: 'create_phase', desc: 'Neue Phase erstellen', cat: 'Phasen' },
              { name: 'update_phase', desc: 'Phase bearbeiten', cat: 'Phasen' },
              { name: 'delete_phase', desc: 'Phase löschen', cat: 'Phasen' },
              { name: 'get_streams', desc: 'Aktive Coin-Streams', cat: 'Daten' },
              { name: 'get_stream_stats', desc: 'Stream-Statistiken', cat: 'Daten' },
              { name: 'get_recent_metrics', desc: 'Letzte Metriken aus DB', cat: 'Daten' },
              { name: 'get_coin_detail', desc: 'Vollständige Coin-Daten', cat: 'Daten' },
              { name: 'get_coin_analytics', desc: 'Coin-Performance', cat: 'Daten' },
            ].map((tool) => (
              <Grid key={tool.name} size={{ xs: 12, sm: 6 }}>
                <Box sx={{
                  p: { xs: 1, sm: 1.5 },
                  bgcolor: 'rgba(0,0,0,0.2)',
                  borderRadius: 1,
                  borderLeft: `3px solid ${
                    tool.cat === 'System' ? '#4caf50' :
                    tool.cat === 'Config' ? '#ff9800' :
                    tool.cat === 'Phasen' ? '#9c27b0' : '#00bcd4'
                  }`,
                }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                    <Typography variant="body2" sx={{
                      fontFamily: 'monospace',
                      fontWeight: 'bold',
                      color: '#00bcd4',
                      fontSize: { xs: '0.7rem', sm: '0.8rem' },
                    }}>
                      {tool.name}
                    </Typography>
                    <Chip
                      label={tool.cat}
                      size="small"
                      sx={{
                        fontSize: { xs: '0.55rem', sm: '0.6rem' },
                        height: 18,
                        bgcolor: tool.cat === 'System' ? 'rgba(76,175,80,0.2)' :
                                 tool.cat === 'Config' ? 'rgba(255,152,0,0.2)' :
                                 tool.cat === 'Phasen' ? 'rgba(156,39,176,0.2)' : 'rgba(0,188,212,0.2)',
                      }}
                    />
                  </Box>
                  <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: { xs: '0.65rem', sm: '0.7rem' } }}>
                    {tool.desc}
                  </Typography>
                </Box>
              </Grid>
            ))}
          </Grid>

          <Divider sx={{ my: 2 }} />

          <Typography variant="body2" sx={{ mb: 2, fontWeight: 'bold', color: '#00bcd4', fontSize: { xs: '0.8rem', sm: '0.9rem' } }}>
            Client-Konfiguration
          </Typography>

          <Typography variant="body2" sx={{ mb: 1, color: 'text.secondary', fontSize: { xs: '0.75rem', sm: '0.8rem' } }}>
            Die Datei <code>.mcp.json</code> im Projekt-Root konfiguriert Claude Code automatisch:
          </Typography>

          <CodeBlock>
{`// .mcp.json
{
  "mcpServers": {
    "pump-finder": {
      "type": "sse",
      "url": "http://localhost:3001/api/mcp"
    }
  }
}`}
          </CodeBlock>

          <Typography variant="body2" sx={{ mb: 2, fontWeight: 'bold', color: '#00bcd4', fontSize: { xs: '0.8rem', sm: '0.9rem' } }}>
            Technologie
          </Typography>

          <CodeBlock>
{`Library:   fastapi-mcp >= 0.3.0
Transport: SSE (Server-Sent Events)
Protokoll: MCP 2025-11-25
Mount:     mcp.mount_sse(mount_path="/mcp")

Funktionsweise:
1. Client öffnet GET /mcp (SSE-Stream)
2. Server sendet session_id
3. Client sendet JSON-RPC via POST /mcp/messages/
4. Antworten kommen über den SSE-Stream`}
          </CodeBlock>

          <Alert severity="success" sx={{ '& .MuiAlert-message': { fontSize: { xs: '0.75rem', sm: '0.875rem' } } }}>
            Alle 14 REST-Endpoints werden automatisch als MCP-Tools exponiert — keine separate Tool-Definition nötig.
          </Alert>
        </AccordionDetails>
      </Accordion>

      {/* Footer */}
      <Box sx={{ mt: 4, textAlign: 'center', py: 2 }}>
        <Typography variant="body2" sx={{ color: 'text.secondary', fontSize: { xs: '0.7rem', sm: '0.8rem' } }}>
          System läuft seit {health?.uptime_seconds ? Math.floor(health.uptime_seconds / 3600) : '?'} Stunden
          {' | '}Aktive Coins: {activeStreams}
          {' | '}Cache: {cacheSize}
        </Typography>
      </Box>
    </Container>
  );
};

export default Info;
