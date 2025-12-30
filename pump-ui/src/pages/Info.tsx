import React from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
} from '@mui/material';
import {
  Info as InfoIcon,
  Timeline as TimelineIcon,
  Analytics as AnalyticsIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material';
import { usePumpStore } from '../stores/pumpStore';

const Info: React.FC = () => {
  const { health } = usePumpStore();

  // Live-Statistiken aus health-Daten berechnen
  const activeStreams = health?.tracking_stats?.active_coins || 0;
  const totalStreams = health?.discovery_stats?.total_coins_discovered || 0;
  const cacheSize = health?.cache_stats?.total_coins || 0;

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ textAlign: 'center', mb: 6 }}>
        <Typography variant="h3" gutterBottom sx={{ color: '#00d4ff', fontWeight: 'bold' }}>
          📖 Vollständige System-Dokumentation
        </Typography>
        <Typography variant="h6" sx={{ color: 'text.secondary', mb: 2 }}>
          Pump-Discover & Pump-Metric System - Detaillierte Funktionsweise
        </Typography>
        <Alert severity="info" sx={{ maxWidth: 800, mx: 'auto' }}>
          <Typography variant="body2">
            Dieses Dokument erklärt <strong>jede Datenbank-Eintragung</strong>, <strong>alle Berechnungen</strong>
            und <strong>den kompletten Datenfluss</strong> des Pump-Service Systems.
          </Typography>
        </Alert>
      </Box>

      {/* 1. System-Architektur */}
      <Card sx={{ mb: 4, bgcolor: 'rgba(0, 212, 255, 0.1)', border: '1px solid rgba(0, 212, 255, 0.3)' }}>
        <CardContent>
          <Box display="flex" alignItems="center" gap={2} mb={3}>
            <InfoIcon sx={{ color: '#00d4ff', fontSize: 30 }} />
            <Typography variant="h4" sx={{ color: '#00d4ff', fontWeight: 'bold' }}>
              🏗️ 1. System-Architektur Übersicht
            </Typography>
          </Box>

          <Typography variant="h6" gutterBottom sx={{ color: '#00d4ff' }}>
            Zwei unabhängige Services arbeiten zusammen:
          </Typography>

          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3, mt: 2 }}>
            <Card sx={{ bgcolor: 'rgba(76, 175, 80, 0.1)', border: '1px solid rgba(76, 175, 80, 0.3)' }}>
              <CardContent>
                <Typography variant="h6" sx={{ color: '#4caf50', mb: 2 }}>
                  🔍 Pump-Discover (Phase 0)
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Funktion:</strong> Neue Coins in Echtzeit entdecken
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Datenquelle:</strong> WebSocket zu PumpPortal
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Filter:</strong> Spam-Burst, Bad Names Regex
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Ausgabe:</strong> discovered_coins Tabelle
                </Typography>
              </CardContent>
            </Card>

            <Card sx={{ bgcolor: 'rgba(255, 152, 0, 0.1)', border: '1px solid rgba(255, 152, 0, 0.3)' }}>
              <CardContent>
                <Typography variant="h6" sx={{ color: '#ff9800', mb: 2 }}>
                  📊 Pump-Metric (Phase 1)
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Funktion:</strong> Live-Trade-Tracking aktiver Coins
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Datenquelle:</strong> WebSocket Trades + Buffer-System
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Berechnungen:</strong> Metriken, Dev-Tracking, Whale-Analysis
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Ausgabe:</strong> coin_metrics Tabelle
                </Typography>
              </CardContent>
            </Card>
          </Box>
        </CardContent>
      </Card>

      {/* 2. Phase 0: Coin Discovery */}
      <Card sx={{ mb: 4, bgcolor: 'rgba(76, 175, 80, 0.1)', border: '1px solid rgba(76, 175, 80, 0.3)' }}>
        <CardContent>
          <Box display="flex" alignItems="center" gap={2} mb={3}>
            <TimelineIcon sx={{ color: '#4caf50', fontSize: 30 }} />
            <Typography variant="h4" sx={{ color: '#4caf50', fontWeight: 'bold' }}>
              🔍 2. Phase 0: Coin Discovery (Pump-Discover)
            </Typography>
          </Box>

          <Typography variant="h6" gutterBottom sx={{ color: '#4caf50' }}>
            Wie neue Coins entdeckt und verarbeitet werden:
          </Typography>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, color: '#4caf50' }}>
            📡 Schritt 1: WebSocket-Verbindung zu PumpPortal
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            <strong>Datenquelle:</strong> wss://pumpportal.fun/api/data
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            <strong>Event-Typ:</strong> "create" (neue Token-Erstellung)
          </Typography>

          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
              Empfangene Daten pro Coin:<br/>
              • mint: Token-Adresse<br/>
              • name, symbol: Token-Name und Symbol<br/>
              • signature: Transaktions-Signatur<br/>
              • traderPublicKey: Creator-Wallet<br/>
              • bondingCurveKey: Bonding Curve Adresse<br/>
              • vSolInBondingCurve: Virtuelles SOL<br/>
              • vTokensInBondingCurve: Virtuelle Tokens<br/>
              • marketCapSol: Market Cap<br/>
              • uri: Metadata-URI
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, color: '#4caf50' }}>
            🛡️ Schritt 2: Spam-Filterung und Validierung
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Bevor ein Coin gespeichert wird, durchläuft er mehrere Filter:
          </Typography>

          <TableContainer component={Box} sx={{ bgcolor: 'rgba(0,0,0,0.2)', borderRadius: 1, mb: 3 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ color: '#4caf50', fontWeight: 'bold' }}>Filter-Typ</TableCell>
                  <TableCell sx={{ color: '#4caf50', fontWeight: 'bold' }}>Beschreibung</TableCell>
                  <TableCell sx={{ color: '#4caf50', fontWeight: 'bold' }}>Beispiel</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>Bad Names Regex</TableCell>
                  <TableCell>Sucht verbotene Wörter im Namen</TableCell>
                  <TableCell>test|bot|rug|scam|cant|honey|faucet</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Spam-Burst</TableCell>
                  <TableCell>Blockiert Massen-Erstellungen</TableCell>
                  <TableCell>Max 3 Coins pro Minute von gleicher Wallet</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, color: '#4caf50' }}>
            🔍 Schritt 3: API-Daten-Abruf
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Für jeden validierten Coin werden zusätzliche Daten abgerufen:
          </Typography>

          <TableContainer component={Box} sx={{ bgcolor: 'rgba(0,0,0,0.2)', borderRadius: 1, mb: 3 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ color: '#4caf50', fontWeight: 'bold' }}>API</TableCell>
                  <TableCell sx={{ color: '#4caf50', fontWeight: 'bold' }}>Zweck</TableCell>
                  <TableCell sx={{ color: '#4caf50', fontWeight: 'bold' }}>Beispieldaten</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>RugCheck API</TableCell>
                  <TableCell>Token-Details (Decimals, Supply)</TableCell>
                  <TableCell>decimals: 6, supply: 1.000.000.000.000</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>RugCheck API</TableCell>
                  <TableCell>Risiko-Score & Flags</TableCell>
                  <TableCell>score: 85, metadata_is_mutable: false</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, color: '#4caf50' }}>
            📄 Schritt 4: Metadata-Parsing
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Die URI aus dem WebSocket wird geparst (IPFS/Arweave):
          </Typography>

          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
              Extrahierte Daten:<br/>
              • description: Token-Beschreibung<br/>
              • image: Bild-URL<br/>
              • twitter: Twitter/X URL<br/>
              • telegram: Telegram URL<br/>
              • website: Website URL<br/>
              • discord: Discord URL<br/>
              • has_socials: Boolean (mind. 1 Social-Link)<br/>
              • social_count: Anzahl Social-Links (0-4)
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, color: '#4caf50' }}>
            💾 Schritt 5: Datenbank-Speicherung
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Alle Daten werden in der <code>discovered_coins</code> Tabelle gespeichert:
          </Typography>

          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
              INSERT INTO discovered_coins (<br/>
              &nbsp;&nbsp;mint, name, symbol, signature,<br/>
              &nbsp;&nbsp;trader_public_key, bonding_curve_key,<br/>
              &nbsp;&nbsp;v_sol_in_bonding_curve, v_tokens_in_bonding_curve,<br/>
              &nbsp;&nbsp;price_sol, market_cap_sol,<br/>
              &nbsp;&nbsp;token_decimals, token_supply,<br/>
              &nbsp;&nbsp;description, image_url, twitter_url,<br/>
              &nbsp;&nbsp;telegram_url, website_url,<br/>
              &nbsp;&nbsp;risk_score, has_socials, social_count<br/>
              ) VALUES (...);
            </Typography>
          </Box>

          <Alert severity="info" sx={{ mb: 2 }}>
            <Typography variant="body2">
              <strong>Wichtig:</strong> Diese Tabelle enthält den vollständigen Initial-Snapshot jedes Coins.
              Sie dient als Basis für das spätere Live-Tracking.
            </Typography>
          </Alert>
        </CardContent>
      </Card>

      {/* 3. Phase 1: Live-Tracking */}
      <Card sx={{ mb: 4, bgcolor: 'rgba(255, 152, 0, 0.1)', border: '1px solid rgba(255, 152, 0, 0.3)' }}>
        <CardContent>
          <Box display="flex" alignItems="center" gap={2} mb={3}>
            <AnalyticsIcon sx={{ color: '#ff9800', fontSize: 30 }} />
            <Typography variant="h4" sx={{ color: '#ff9800', fontWeight: 'bold' }}>
              📊 3. Phase 1: Live-Tracking (Pump-Metric)
            </Typography>
          </Box>

          <Typography variant="h6" gutterBottom sx={{ color: '#ff9800' }}>
            Wie Coins in Echtzeit getrackt werden:
          </Typography>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, color: '#ff9800' }}>
            🔄 Schritt 1: Datenbank-Abfrage (alle 10 Sekunden)
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Das System fragt alle aktiven Coins ab (WHERE is_active = TRUE):
          </Typography>

          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
              SELECT cs.token_address, cs.current_phase_id, dc.token_created_at<br/>
              FROM coin_streams cs<br/>
              JOIN discovered_coins dc ON cs.token_address = dc.token_address<br/>
              WHERE cs.is_active = TRUE
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, color: '#ff9800' }}>
            📡 Schritt 2: Trade-Empfang & Verarbeitung
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Bei jedem Trade werden folgende Berechnungen durchgeführt:
          </Typography>

          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
              Preis-Berechnung:<br/>
              price = vSolInBondingCurve / vTokensInBondingCurve<br/>
              <br/>
              Volumen-Akkumulation:<br/>
              volume_sol += solAmount<br/>
              buy_volume_sol += solAmount (wenn txType == "buy")<br/>
              sell_volume_sol += solAmount (wenn txType == "sell")<br/>
              <br/>
              Trade-Zählung:<br/>
              num_buys += 1<br/>
              num_sells += 1<br/>
              unique_wallets.add(traderPublicKey)
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, color: '#ff9800' }}>
            📈 Schritt 3: Phasen-Management
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Coins durchlaufen verschiedene Phasen basierend auf ihrem Alter:
          </Typography>

          <TableContainer component={Box} sx={{ bgcolor: 'rgba(0,0,0,0.2)', borderRadius: 1, mb: 3 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ color: '#ff9800', fontWeight: 'bold' }}>Phase</TableCell>
                  <TableCell sx={{ color: '#ff9800', fontWeight: 'bold' }}>Intervall</TableCell>
                  <TableCell sx={{ color: '#ff9800', fontWeight: 'bold' }}>Zeitbereich</TableCell>
                  <TableCell sx={{ color: '#ff9800', fontWeight: 'bold' }}>Beschreibung</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>Baby Zone</TableCell>
                  <TableCell>5 Sekunden</TableCell>
                  <TableCell>0-10 Minuten</TableCell>
                  <TableCell>Sehr junge Coins, häufige Updates</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Survival Zone</TableCell>
                  <TableCell>30 Sekunden</TableCell>
                  <TableCell>10-60 Minuten</TableCell>
                  <TableCell>Coins die überlebt haben</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Mature Zone</TableCell>
                  <TableCell>60 Sekunden</TableCell>
                  <TableCell>1-24 Stunden</TableCell>
                  <TableCell>Reife Coins, weniger Updates</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Finished</TableCell>
                  <TableCell>0 Sekunden</TableCell>
                  <TableCell>24h+</TableCell>
                  <TableCell>Tracking beendet (zu alt)</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, color: '#ff9800' }}>
            💾 Schritt 4: Metrik-Speicherung
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Metriken werden periodisch in coin_metrics gespeichert:
          </Typography>

          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
              INSERT INTO coin_metrics (mint, timestamp, phase_id_at_time,<br/>
              &nbsp;&nbsp;price_open, price_high, price_low, price_close,<br/>
              &nbsp;&nbsp;market_cap_close, bonding_curve_pct, virtual_sol_reserves,<br/>
              &nbsp;&nbsp;volume_sol, buy_volume_sol, sell_volume_sol,<br/>
              &nbsp;&nbsp;num_buys, num_sells, unique_wallets,<br/>
              &nbsp;&nbsp;dev_sold_amount, whale_buy_volume_sol, num_whale_buys<br/>
              ) VALUES (...);
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* 4. Live-Monitoring */}
      <Card sx={{ bgcolor: 'rgba(0, 212, 255, 0.1)', border: '1px solid rgba(0, 212, 255, 0.3)' }}>
        <CardContent>
          <Box display="flex" alignItems="center" gap={2} mb={3}>
            <SpeedIcon sx={{ color: '#00d4ff', fontSize: 30 }} />
            <Typography variant="h4" sx={{ color: '#00d4ff', fontWeight: 'bold' }}>
              📊 4. Live-Monitoring & Statistiken
            </Typography>
          </Box>

          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, gap: 2, mb: 3 }}>
            <Box>
              <Typography variant="h6" sx={{ color: '#00d4ff' }}>{activeStreams}</Typography>
              <Typography variant="body2" sx={{ color: 'text.secondary' }}>Aktive Coins</Typography>
            </Box>
            <Box>
              <Typography variant="h6" sx={{ color: '#00d4ff' }}>{totalStreams}</Typography>
              <Typography variant="body2" sx={{ color: 'text.secondary' }}>Entdeckte Coins</Typography>
            </Box>
            <Box>
              <Typography variant="h6" sx={{ color: '#00d4ff' }}>{cacheSize}</Typography>
              <Typography variant="body2" sx={{ color: 'text.secondary' }}>Cache-Größe</Typography>
            </Box>
            <Box>
              <Typography variant="h6" sx={{ color: '#00d4ff' }}>
                {health?.ws_connected ? '🟢' : '🔴'} {health?.ws_connected ? 'Verbunden' : 'Getrennt'}
              </Typography>
              <Typography variant="body2" sx={{ color: 'text.secondary' }}>WebSocket</Typography>
            </Box>
          </Box>

          <Typography variant="body2" sx={{ mb: 2 }}>
            <strong>Verfügbare API-Endpunkte:</strong>
          </Typography>
          <Box sx={{ fontFamily: 'monospace', fontSize: '0.8rem', bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 2 }}>
            GET /database/phases - Alle Phasen<br/>
            GET /database/streams/stats - Stream-Statistiken<br/>
            GET /database/streams?limit=50 - Einzelne Streams<br/>
            GET /database/metrics?limit=100 - Metriken
          </Box>

          <Typography variant="body2" sx={{ mb: 2 }}>
            <strong>Prometheus-Metriken:</strong>
          </Typography>
          <Box sx={{ fontFamily: 'monospace', fontSize: '0.8rem', bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1 }}>
            tracker_trades_received_total<br/>
            tracker_coins_tracked<br/>
            tracker_ws_connected<br/>
            tracker_db_connected<br/>
            tracker_ath_updates_total<br/>
            tracker_trade_buffer_size
          </Box>
        </CardContent>
      </Card>

      {/* 5. API-Funktionalität */}
      <Card sx={{ mb: 4, bgcolor: 'rgba(76, 175, 80, 0.1)', border: '1px solid rgba(76, 175, 80, 0.3)' }}>
        <CardContent>
          <Box display="flex" alignItems="center" gap={2} mb={3}>
            <AnalyticsIcon sx={{ color: '#4caf50', fontSize: 30 }} />
            <Typography variant="h4" sx={{ color: '#4caf50', fontWeight: 'bold' }}>
              🔗 5. API-Funktionalität - Vollständige Dokumentation
            </Typography>
          </Box>

          <Typography variant="body2" sx={{ mb: 3 }}>
            Die API bildet das Herzstück des Systems und ermöglicht den Zugriff auf alle gespeicherten Daten
            und Live-Statistiken. Alle Endpunkte sind über <code>/api/</code> erreichbar und liefern JSON-Daten zurück.
          </Typography>

          <Typography variant="h6" sx={{ mb: 2, color: '#4caf50' }}>
            📋 GET /api/health - System-Status & Live-Daten
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            <strong>Funktion:</strong> Liefert den aktuellen Systemstatus und Live-Statistiken.
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            <strong>Datenquelle:</strong> Sammelt Daten aus allen internen Systemkomponenten:
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
              ws_connected: WebSocket-Verbindung zu PumpPortal (true/false)<br/>
              db_connected: PostgreSQL-Datenbank-Verbindung (true/false)<br/>
              uptime_seconds: Service-Laufzeit in Sekunden<br/>
              reconnect_count: Anzahl WebSocket-Reconnects<br/>
              last_error: Letzter Fehler (null wenn keiner)<br/>
              cache_stats: Aktuelle Cache-Statistiken<br/>
              tracking_stats: Live-Tracking-Daten<br/>
              discovery_stats: Discovery-Statistiken
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, color: '#4caf50' }}>
            📊 GET /api/database/phases - Phasen-Konfiguration
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            <strong>Funktion:</strong> Zeigt alle konfigurierten Phasen mit ihren Grenzwerten und Regeln.
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            <strong>Datenquelle:</strong> <code>ref_coin_phases</code> Tabelle in PostgreSQL.
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
              Beispiel-Response:<br/>
              [<br/>
              &nbsp;&nbsp;{"{id: 1, name: 'Baby Zone', min_age: 0, max_age: 1800, ...}"}<br/>
              &nbsp;&nbsp;{"{id: 2, name: 'Survival Zone', min_age: 1800, max_age: 3600, ...}"}<br/>
              ]
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, color: '#4caf50' }}>
            📈 GET /api/database/streams/stats - Stream-Statistiken
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            <strong>Funktion:</strong> Aggregierte Statistiken über alle aktiven und beendeten Streams.
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            <strong>Berechnung:</strong>
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
              total_streams: COUNT(*) FROM coin_streams<br/>
              active_streams: COUNT(*) WHERE ended_at IS NULL<br/>
              ended_streams: COUNT(*) WHERE ended_at IS NOT NULL<br/>
              streams_by_phase: GROUP BY current_phase_id
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, color: '#4caf50' }}>
            🎯 GET /api/database/streams?limit=50 - Einzelne Streams
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            <strong>Funktion:</strong> Detaillierte Informationen über einzelne Coin-Streams.
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            <strong>Datenquelle:</strong> <code>coin_streams</code> Tabelle, sortiert nach created_at DESC.
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
              Pro Stream:<br/>
              - mint: Token-Adresse<br/>
              - name/symbol: Coin-Name<br/>
              - created_at/ended_at: Lebenszyklus<br/>
              - current_phase_id: Aktuelle Phase<br/>
              - bonding_curve_pct: Bonding-Curve Fortschritt<br/>
              - dev_sold_amount: Creator-Verkäufe
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, color: '#4caf50' }}>
            📉 GET /api/database/metrics?limit=100 - Historische Metriken
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            <strong>Funktion:</strong> Zeitreihen-Daten für Preis, Volumen und Marktanalyse.
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            <strong>Datenquelle:</strong> <code>coin_metrics</code> Tabelle mit OHLCV-Daten.
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
              Pro Metrik-Eintrag:<br/>
              - timestamp: Messzeitpunkt<br/>
              - price_open/high/low/close: OHLC-Preise<br/>
              - volume_sol: Handelsvolumen in SOL<br/>
              - market_cap_close: Marktkapitalisierung<br/>
              - bonding_curve_pct: Bonding-Curve Status<br/>
              - num_buys/num_sells: Transaktionszahlen
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, color: '#4caf50' }}>
            ⚙️ PUT /api/config - Konfiguration ändern
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            <strong>Funktion:</strong> Runtime-Konfiguration des Services ändern ohne Neustart.
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            <strong>Konfigurierbare Parameter:</strong>
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
              n8n_webhook_url: Webhook-URL für Coin-Benachrichtigungen<br/>
              db_dsn: PostgreSQL-Verbindungsstring<br/>
              coin_cache_seconds: Cache-Dauer für neue Coins (120s)<br/>
              db_refresh_interval: DB-Refresh-Intervall (10s)<br/>
              batch_size: Batch-Größe für n8n-Sends (10)<br/>
              bad_names_pattern: Regex für Coin-Filter<br/>
              spam_burst_window: Spam-Schutz-Fenster (30s)
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, color: '#ff9800' }}>
            🔄 API-Datenfluss
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            <strong>Health-Endpoint:</strong> Sammelt Live-Daten aus allen Services<br/>
            <strong>Database-Endpoints:</strong> Direkte SQL-Queries auf PostgreSQL<br/>
            <strong>Config-Endpoint:</strong> Speichert Änderungen in ./config/.env
          </Typography>
        </CardContent>
      </Card>

      {/* 6. Web UI Architektur - Vollständige Übersicht */}
      <Card sx={{ mb: 4, bgcolor: 'rgba(156, 39, 176, 0.1)', border: '1px solid rgba(156, 39, 176, 0.3)' }}>
        <CardContent>
          <Box display="flex" alignItems="center" gap={2} mb={3}>
            <TimelineIcon sx={{ color: '#9c27b0', fontSize: 30 }} />
            <Typography variant="h4" sx={{ color: '#9c27b0', fontWeight: 'bold' }}>
              🌐 6. Web UI Architektur - Vollständige Übersicht
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, color: '#9c27b0' }}>
            🏗️ Frontend-Technologie-Stack
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
              <strong>Framework:</strong> React 18 + TypeScript<br/>
              <strong>Build-Tool:</strong> Vite 5.4.21 (ESBuild)<br/>
              <strong>UI-Library:</strong> Material-UI (MUI) v7<br/>
              <strong>State-Management:</strong> Zustand v5.0.9<br/>
              <strong>HTTP-Client:</strong> Axios v1.13.2<br/>
              <strong>Charts:</strong> Recharts v3.6.0<br/>
              <strong>Styling:</strong> Emotion CSS-in-JS
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, color: '#9c27b0' }}>
            🔄 API-Kommunikation & Proxy-Konfiguration
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Die Web-UI kommuniziert ausschließlich über HTTP-API-Calls mit dem Backend:
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>API-Base-URL:</strong> http://localhost:8000<br/>
              <strong>Konfiguration:</strong> VITE_API_BASE_URL=http://localhost:8000<br/>
              <strong>Protokoll:</strong> HTTP/1.1 + JSON<br/>
              <strong>Timeout:</strong> 10 Sekunden pro Request<br/>
              <strong>CORS:</strong> Aktiviert für localhost:3000
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Docker Networking:</strong><br/>
              pump-ui (Port 3000) → pump-service (Port 8000)<br/>
              Beide Container im gleichen Docker-Netzwerk<br/>
              Direkte HTTP-Kommunikation ohne Reverse-Proxy
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, color: '#9c27b0' }}>
            📦 State-Management mit Zustand
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Alle UI-Zustände werden zentral in einem Zustand-Store verwaltet:
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Store-Struktur:</strong><br/>
              - health: System-Status & Live-Daten<br/>
              - config: Runtime-Konfiguration<br/>
              - loading/error: UI-Zustände<br/>
              - lastUpdated: Timestamp für Cache-Invalidierung
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Automatische Updates:</strong><br/>
              - Health-Daten: Alle 5 Sekunden<br/>
              - Stream-Stats: Alle 10 Sekunden<br/>
              - Config-Daten: Bei Änderungen + einmalig beim Laden
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, color: '#9c27b0' }}>
            🔧 API-Service Layer
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Alle API-Calls werden durch einen zentralen Service-Layer abstrahiert:
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>src/services/api.ts:</strong><br/>
              - pumpApi.getHealth() → GET /health<br/>
              - pumpApi.getConfig() → GET /config<br/>
              - pumpApi.updateConfig(data) → PUT /config<br/>
              - pumpApi.getMetrics() → GET /metrics<br/>
              - pumpApi.getStreamStats() → GET /database/streams/stats<br/>
              - pumpApi.getPhases() → GET /database/phases
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Error Handling:</strong><br/>
              - Axios Interceptors für globale Fehlerbehandlung<br/>
              - Retry-Logik für temporäre Netzwerkfehler<br/>
              - Fallback-Werte bei API-Ausfällen<br/>
              - Browser-Console Logging für Debugging
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, color: '#9c27b0' }}>
            🎨 UI-Komponenten Architektur
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Die UI ist in wiederverwendbare Komponenten strukturiert:
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Seiten-Komponenten:</strong><br/>
              - Dashboard: Hauptübersicht mit Live-Status<br/>
              - Metrics: Detaillierte Statistiken & Charts<br/>
              - Config: Runtime-Konfiguration<br/>
              - Info: Diese Dokumentations-Seite
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Shared Components:</strong><br/>
              - Material-UI Komponenten (Cards, Tables, Charts)<br/>
              - Custom Hooks für Daten-Fetching<br/>
              - Responsive Layout mit Grid-System<br/>
              - Dark Theme mit blauem Akzent
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, color: '#9c27b0' }}>
            ⚡ Performance-Optimierungen
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Build-Optimierungen:</strong><br/>
              - Vite ESBuild: Schneller als Webpack<br/>
              - Code-Splitting: Automatische Chunk-Aufteilung<br/>
              - Tree-Shaking: Unbenutzter Code wird entfernt<br/>
              - Minification: JavaScript & CSS komprimiert
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Runtime-Optimierungen:</strong><br/>
              - React.useMemo für teure Berechnungen<br/>
              - React.useCallback für Event-Handler<br/>
              - Lazy Loading für große Komponenten<br/>
              - Intelligent Caching von API-Responses
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* 7. Vollständige API-Dokumentation */}
      <Card sx={{ mb: 4, bgcolor: 'rgba(0, 212, 255, 0.1)', border: '1px solid rgba(0, 212, 255, 0.3)' }}>
        <CardContent>
          <Box display="flex" alignItems="center" gap={2} mb={3}>
            <AnalyticsIcon sx={{ color: '#00d4ff', fontSize: 30 }} />
            <Typography variant="h4" sx={{ color: '#00d4ff', fontWeight: 'bold' }}>
              📚 7. Vollständige API-Dokumentation
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, color: '#00d4ff' }}>
            🌐 Basis-Informationen
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Base-URL:</strong> http://localhost:8000<br/>
              <strong>Protokoll:</strong> HTTP/1.1 + RESTful API<br/>
              <strong>Content-Type:</strong> application/json<br/>
              <strong>Authentication:</strong> Keine erforderlich<br/>
              <strong>CORS:</strong> Aktiviert für localhost:3000<br/>
              <strong>Rate-Limiting:</strong> Keines implementiert
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, color: '#00d4ff' }}>
            📋 GET /health - System-Status & Live-Daten
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Funktion:</strong> Vollständiger System-Status<br/>
              <strong>Cache:</strong> Kein Caching (Live-Daten)<br/>
              <strong>Timeout:</strong> 5 Sekunden<br/>
              <strong>UI-Verwendung:</strong> Dashboard + Metrics alle 5s
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Response-Schema:</strong><br/>
              {"{"}<br/>
              &nbsp;&nbsp;"status": "healthy|degraded|unhealthy",<br/>
              &nbsp;&nbsp;"ws_connected": boolean,<br/>
              &nbsp;&nbsp;"db_connected": boolean,<br/>
              &nbsp;&nbsp;"uptime_seconds": number,<br/>
              &nbsp;&nbsp;"last_message_ago": number|null,<br/>
              &nbsp;&nbsp;"reconnect_count": number,<br/>
              &nbsp;&nbsp;"last_error": string|null,<br/>
              &nbsp;&nbsp;"cache_stats": {"{"}<br/>
              &nbsp;&nbsp;&nbsp;&nbsp;"total_coins": number,<br/>
              &nbsp;&nbsp;&nbsp;&nbsp;"activated_coins": number,<br/>
              &nbsp;&nbsp;&nbsp;&nbsp;"expired_coins": number,<br/>
              &nbsp;&nbsp;&nbsp;&nbsp;"oldest_age_seconds": number,<br/>
              &nbsp;&nbsp;&nbsp;&nbsp;"newest_age_seconds": number<br/>
              &nbsp;&nbsp;{"}"}<br/>
              &nbsp;&nbsp;"tracking_stats": {"{"}<br/>
              &nbsp;&nbsp;&nbsp;&nbsp;"active_coins": number,<br/>
              &nbsp;&nbsp;&nbsp;&nbsp;"total_trades": number,<br/>
              &nbsp;&nbsp;&nbsp;&nbsp;"total_metrics_saved": number<br/>
              &nbsp;&nbsp;{"}"}<br/>
              &nbsp;&nbsp;"discovery_stats": {"{"}<br/>
              &nbsp;&nbsp;&nbsp;&nbsp;"total_coins_discovered": number,<br/>
              &nbsp;&nbsp;&nbsp;&nbsp;"n8n_available": boolean,<br/>
              &nbsp;&nbsp;&nbsp;&nbsp;"n8n_buffer_size": number<br/>
              &nbsp;&nbsp;{"}"}<br/>
              {"}"}
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, color: '#00d4ff' }}>
            ⚙️ GET /config - Aktuelle Konfiguration lesen
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Funktion:</strong> Runtime-Konfiguration auslesen<br/>
              <strong>Datenquelle:</strong> ./config/.env Datei<br/>
              <strong>UI-Verwendung:</strong> Config-Seite beim Laden
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Response-Beispiel:</strong><br/>
              {"{"}<br/>
              &nbsp;&nbsp;"n8n_webhook_url": "https://n8n.example.com/webhook",<br/>
              &nbsp;&nbsp;"db_dsn": "postgresql://user:***@host:5432/db",<br/>
              &nbsp;&nbsp;"coin_cache_seconds": 120,<br/>
              &nbsp;&nbsp;"db_refresh_interval": 10,<br/>
              &nbsp;&nbsp;"batch_size": 5,<br/>
              &nbsp;&nbsp;"batch_timeout": 28,<br/>
              &nbsp;&nbsp;"bad_names_pattern": "test|bot|rug|scam",<br/>
              &nbsp;&nbsp;"spam_burst_window": 30<br/>
              {"}"}
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, color: '#00d4ff' }}>
            🔧 PUT /config - Konfiguration aktualisieren
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Funktion:</strong> Runtime-Konfiguration ändern<br/>
              <strong>Validierung:</strong> Typ- und Wertebereichs-Prüfung<br/>
              <strong>Persistierung:</strong> In ./config/.env speichern<br/>
              <strong>UI-Verwendung:</strong> Config-Seite "Speichern" Button
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Request-Body (nur geänderte Felder):</strong><br/>
              {"{"}<br/>
              &nbsp;&nbsp;"db_refresh_interval": 15,<br/>
              &nbsp;&nbsp;"batch_size": 10<br/>
              {"}"}
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Response:</strong><br/>
              {"{"}<br/>
              &nbsp;&nbsp;"status": "success",<br/>
              &nbsp;&nbsp;"message": "Konfiguration aktualisiert: db_refresh_interval, batch_size",<br/>
              &nbsp;&nbsp;"updated_fields": ["db_refresh_interval", "batch_size"],<br/>
              &nbsp;&nbsp;"new_config": {"{...}"}<br/>
              {"}"}
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, color: '#00d4ff' }}>
            📊 GET /metrics - Prometheus-Metriken
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Funktion:</strong> Prometheus-kompatible Metriken<br/>
              <strong>Format:</strong> Plain Text (text/plain)<br/>
              <strong>UI-Verwendung:</strong> Metrics-Seite alle 30s
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Beispiel-Output:</strong><br/>
              # HELP tracker_coins_received_total Coins received from WebSocket<br/>
              # TYPE tracker_coins_received_total counter<br/>
              tracker_coins_received_total 1337<br/>
              <br/>
              # HELP tracker_cache_size_current Current cache size<br/>
              # TYPE tracker_cache_size_current gauge<br/>
              tracker_cache_size_current 25
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, color: '#00d4ff' }}>
            🗄️ GET /database/streams/stats - Stream-Statistiken
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Funktion:</strong> Aggregierte Stream-Statistiken<br/>
              <strong>Datenbank:</strong> PostgreSQL coin_streams Tabelle<br/>
              <strong>UI-Verwendung:</strong> Metrics-Seite alle 10s
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Response-Schema:</strong><br/>
              {"{"}<br/>
              &nbsp;&nbsp;"total_streams": 1602,<br/>
              &nbsp;&nbsp;"active_streams": 577,<br/>
              &nbsp;&nbsp;"ended_streams": 1025,<br/>
              &nbsp;&nbsp;"streams_by_phase": {"{"}"1":79,"2":488,"3":10,"99":1014,"100":11{"}"}<br/>
              {"}"}
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, color: '#00d4ff' }}>
            📊 GET /database/phases - Phasen-Konfiguration
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Funktion:</strong> Phasen-Definitionen auslesen<br/>
              <strong>Datenbank:</strong> PostgreSQL ref_coin_phases Tabelle<br/>
              <strong>UI-Verwendung:</strong> Metrics-Seite beim Laden
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Response-Schema:</strong><br/>
              {"{"}<br/>
              &nbsp;&nbsp;"phases": [<br/>
              &nbsp;&nbsp;&nbsp;&nbsp;{"{"}"id":1,"name":"Baby Zone","interval_seconds":5,"min_age_minutes":0,"max_age_minutes":10{"}"}<br/>
              &nbsp;&nbsp;],<br/>
              &nbsp;&nbsp;"count": 5<br/>
              {"}"}
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, color: '#00d4ff' }}>
            📈 GET /database/streams - Einzelne Streams
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Funktion:</strong> Detaillierte Stream-Informationen<br/>
              <strong>Parameter:</strong> limit=50 (Standard)<br/>
              <strong>Sortierung:</strong> created_at DESC<br/>
              <strong>UI-Verwendung:</strong> Nicht verwendet (zukünftig)
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Response-Schema:</strong><br/>
              [{"{"}<br/>
              &nbsp;&nbsp;"mint": "TokenAddress",<br/>
              &nbsp;&nbsp;"name": "Coin Name",<br/>
              &nbsp;&nbsp;"created_at": "2025-12-30T17:00:00Z",<br/>
              &nbsp;&nbsp;"ended_at": null,<br/>
              &nbsp;&nbsp;"current_phase_id": 2,<br/>
              &nbsp;&nbsp;"bonding_curve_pct": 0.15,<br/>
              &nbsp;&nbsp;"dev_sold_amount": 0.5<br/>
              {"}"}]
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, color: '#00d4ff' }}>
            📉 GET /database/metrics - Historische Metriken
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Funktion:</strong> Zeitreihen-Daten für Analyse<br/>
              <strong>Parameter:</strong> limit=100 (Standard)<br/>
              <strong>Datenbank:</strong> coin_metrics Tabelle<br/>
              <strong>UI-Verwendung:</strong> Nicht implementiert (zukünftig)
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Response-Schema:</strong><br/>
              [{"{"}<br/>
              &nbsp;&nbsp;"timestamp": "2025-12-30T17:00:00Z",<br/>
              &nbsp;&nbsp;"price_open": 0.0000123,<br/>
              &nbsp;&nbsp;"price_high": 0.0000156,<br/>
              &nbsp;&nbsp;"price_low": 0.0000111,<br/>
              &nbsp;&nbsp;"price_close": 0.0000134,<br/>
              &nbsp;&nbsp;"volume_sol": 25.67,<br/>
              &nbsp;&nbsp;"market_cap_close": 12345.67,<br/>
              &nbsp;&nbsp;"num_buys": 15,<br/>
              &nbsp;&nbsp;"num_sells": 8<br/>
              {"}"}]
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* 8. Konfigurationsparameter - Vollständige Übersicht */}
      <Card sx={{ mb: 4, bgcolor: 'rgba(76, 175, 80, 0.1)', border: '1px solid rgba(76, 175, 80, 0.3)' }}>
        <CardContent>
          <Box display="flex" alignItems="center" gap={2} mb={3}>
            <InfoIcon sx={{ color: '#4caf50', fontSize: 30 }} />
            <Typography variant="h4" sx={{ color: '#4caf50', fontWeight: 'bold' }}>
              ⚙️ 8. Konfigurationsparameter - Vollständige Übersicht
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, color: '#4caf50' }}>
            🗂️ Konfigurationsdatei: ./config/.env
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
              # Beispiel-Konfiguration<br/>
              DB_DSN=postgresql://user:password@host:5432/database<br/>
              WS_URI=wss://pumpportal.fun/api/data<br/>
              N8N_WEBHOOK_URL=https://n8n.example.com/webhook/pump-discover<br/>
              COIN_CACHE_SECONDS=120<br/>
              DB_REFRESH_INTERVAL=10<br/>
              BATCH_SIZE=10<br/>
              BATCH_TIMEOUT=30<br/>
              BAD_NAMES_PATTERN=test|bot|rug|scam|cant|honey|faucet<br/>
              SPAM_BURST_WINDOW=30
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, color: '#4caf50' }}>
            🗄️ Datenbank-Konfiguration
          </Typography>
          <TableContainer component={Box} sx={{ bgcolor: 'rgba(0,0,0,0.2)', borderRadius: 1, mb: 3 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ color: '#4caf50', fontWeight: 'bold' }}>Parameter</TableCell>
                  <TableCell sx={{ color: '#4caf50', fontWeight: 'bold' }}>Standard</TableCell>
                  <TableCell sx={{ color: '#4caf50', fontWeight: 'bold' }}>Bereich</TableCell>
                  <TableCell sx={{ color: '#4caf50', fontWeight: 'bold' }}>Beschreibung</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>DB_DSN</TableCell>
                  <TableCell>postgresql://...</TableCell>
                  <TableCell>String</TableCell>
                  <TableCell>PostgreSQL-Verbindungsstring (Passwort wird maskiert)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>DB_REFRESH_INTERVAL</TableCell>
                  <TableCell>10</TableCell>
                  <TableCell>5-300</TableCell>
                  <TableCell>Intervall für DB-Abfragen aktiver Streams (Sekunden)</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>

          <Typography variant="h6" sx={{ mb: 2, color: '#4caf50' }}>
            🌐 WebSocket & API-Konfiguration
          </Typography>
          <TableContainer component={Box} sx={{ bgcolor: 'rgba(0,0,0,0.2)', borderRadius: 1, mb: 3 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ color: '#4caf50', fontWeight: 'bold' }}>Parameter</TableCell>
                  <TableCell sx={{ color: '#4caf50', fontWeight: 'bold' }}>Standard</TableCell>
                  <TableCell sx={{ color: '#4caf50', fontWeight: 'bold' }}>Beschreibung</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>WS_URI</TableCell>
                  <TableCell>wss://pumpportal.fun/api/data</TableCell>
                  <TableCell>WebSocket-Endpunkt für Coin-Discovery</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>WS_RETRY_DELAY</TableCell>
                  <TableCell>3</TableCell>
                  <TableCell>Verzögerung zwischen Reconnect-Versuchen (Sekunden)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>WS_MAX_RETRY_DELAY</TableCell>
                  <TableCell>60</TableCell>
                  <TableCell>Maximale Reconnect-Verzögerung (Sekunden)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>WS_PING_INTERVAL</TableCell>
                  <TableCell>20</TableCell>
                  <TableCell>Intervall für Keep-Alive Pings (Sekunden)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>WS_PING_TIMEOUT</TableCell>
                  <TableCell>10</TableCell>
                  <TableCell>Timeout für Ping-Responses (Sekunden)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>WS_CONNECTION_TIMEOUT</TableCell>
                  <TableCell>30</TableCell>
                  <TableCell>Timeout für Verbindungsaufbau (Sekunden)</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>

          <Typography variant="h6" sx={{ mb: 2, color: '#4caf50' }}>
            🔍 Discovery & Filter-Konfiguration
          </Typography>
          <TableContainer component={Box} sx={{ bgcolor: 'rgba(0,0,0,0.2)', borderRadius: 1, mb: 3 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ color: '#4caf50', fontWeight: 'bold' }}>Parameter</TableCell>
                  <TableCell sx={{ color: '#4caf50', fontWeight: 'bold' }}>Standard</TableCell>
                  <TableCell sx={{ color: '#4caf50', fontWeight: 'bold' }}>Bereich</TableCell>
                  <TableCell sx={{ color: '#4caf50', fontWeight: 'bold' }}>Beschreibung</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>COIN_CACHE_SECONDS</TableCell>
                  <TableCell>120</TableCell>
                  <TableCell>10-3600</TableCell>
                  <TableCell>Cache-Dauer für neue Coins vor Tracking-Start</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>BAD_NAMES_PATTERN</TableCell>
                  <TableCell>test|bot|rug|scam|cant|honey|faucet</TableCell>
                  <TableCell>Regex</TableCell>
                  <TableCell>Regex-Muster für Coin-Filterung nach Namen</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>SPAM_BURST_WINDOW</TableCell>
                  <TableCell>30</TableCell>
                  <TableCell>1-300</TableCell>
                  <TableCell>Zeitfenster für Spam-Burst-Erkennung (Sekunden)</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>

          <Typography variant="h6" sx={{ mb: 2, color: '#4caf50' }}>
            📤 n8n Integration & Batching
          </Typography>
          <TableContainer component={Box} sx={{ bgcolor: 'rgba(0,0,0,0.2)', borderRadius: 1, mb: 3 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ color: '#4caf50', fontWeight: 'bold' }}>Parameter</TableCell>
                  <TableCell sx={{ color: '#4caf50', fontWeight: 'bold' }}>Standard</TableCell>
                  <TableCell sx={{ color: '#4caf50', fontWeight: 'bold' }}>Bereich</TableCell>
                  <TableCell sx={{ color: '#4caf50', fontWeight: 'bold' }}>Beschreibung</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>N8N_WEBHOOK_URL</TableCell>
                  <TableCell>https://n8n.example.com/webhook</TableCell>
                  <TableCell>URL</TableCell>
                  <TableCell>Vollständige n8n Webhook-URL für Coin-Benachrichtigungen</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>N8N_WEBHOOK_METHOD</TableCell>
                  <TableCell>POST</TableCell>
                  <TableCell>GET/POST</TableCell>
                  <TableCell>HTTP-Methode für n8n Webhook-Calls</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>BATCH_SIZE</TableCell>
                  <TableCell>10</TableCell>
                  <TableCell>1-100</TableCell>
                  <TableCell>Anzahl Coins pro n8n Batch-Send</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>BATCH_TIMEOUT</TableCell>
                  <TableCell>30</TableCell>
                  <TableCell>5-300</TableCell>
                  <TableCell>Maximale Wartezeit für Batch-Füllung (Sekunden)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>N8N_RETRY_DELAY</TableCell>
                  <TableCell>5</TableCell>
                  <TableCell>1-60</TableCell>
                  <TableCell>Verzögerung zwischen n8n Retry-Versuchen (Sekunden)</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>

          <Typography variant="h6" sx={{ mb: 2, color: '#4caf50' }}>
            📊 Monitoring & Health-Checks
          </Typography>
          <TableContainer component={Box} sx={{ bgcolor: 'rgba(0,0,0,0.2)', borderRadius: 1, mb: 3 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ color: '#4caf50', fontWeight: 'bold' }}>Parameter</TableCell>
                  <TableCell sx={{ color: '#4caf50', fontWeight: 'bold' }}>Standard</TableCell>
                  <TableCell sx={{ color: '#4caf50', fontWeight: 'bold' }}>Beschreibung</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>HEALTH_PORT</TableCell>
                  <TableCell>8000</TableCell>
                  <TableCell>Port für Health-Checks und API</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>SOL_RESERVES_FULL</TableCell>
                  <TableCell>85.0</TableCell>
                  <TableCell>Schwellwert für "Bonding Curve Full" (%)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>AGE_CALCULATION_OFFSET_MIN</TableCell>
                  <TableCell>60</TableCell>
                  <TableCell>Zeit-Offset für Altersberechnungen (Minuten)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>TRADE_BUFFER_SECONDS</TableCell>
                  <TableCell>180</TableCell>
                  <TableCell>Puffer für Trade-Aggregation (Sekunden)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>WHALE_THRESHOLD_SOL</TableCell>
                  <TableCell>1.0</TableCell>
                  <TableCell>Schwellwert für Whale-Trades (SOL)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>ATH_FLUSH_INTERVAL</TableCell>
                  <TableCell>5</TableCell>
                  <TableCell>Intervall für All-Time-High Updates (Sekunden)</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* 9. Docker & Deployment */}
      <Card sx={{ mb: 4, bgcolor: 'rgba(244, 67, 54, 0.1)', border: '1px solid rgba(244, 67, 54, 0.3)' }}>
        <CardContent>
          <Box display="flex" alignItems="center" gap={2} mb={3}>
            <SpeedIcon sx={{ color: '#f44336', fontSize: 30 }} />
            <Typography variant="h4" sx={{ color: '#f44336', fontWeight: 'bold' }}>
              🐳 9. Docker & Deployment - Vollständige Übersicht
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, color: '#f44336' }}>
            🏗️ Container-Architektur
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Backend (pump-service):</strong><br/>
              - Image: python:3.11-slim<br/>
              - Port: 8000 (intern + extern exposed)<br/>
              - Volume: ./config:/app/config:rw<br/>
              - Health-Check: curl -f http://localhost:8000/health<br/>
              - Restart: unless-stopped
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Frontend (pump-ui):</strong><br/>
              - Build: node:22-alpine → nginx:alpine<br/>
              - Port: 3000 (nginx serving static files)<br/>
              - Environment: VITE_API_BASE_URL=http://localhost:8000<br/>
              - Health-Check: curl -f http://localhost/health<br/>
              - Restart: unless-stopped
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Docker Network:</strong><br/>
              - Name: pump-find_pump-network<br/>
              - Driver: bridge<br/>
              - Beide Container kommunizieren direkt über HTTP
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, color: '#f44336' }}>
            🚀 Deployment-Befehle
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Erstmaliges Setup:</strong><br/>
              docker-compose -f docker-compose.ui.yml up -d
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Logs ansehen:</strong><br/>
              docker-compose -f docker-compose.ui.yml logs -f
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Container neu bauen:</strong><br/>
              docker-compose -f docker-compose.ui.yml build --no-cache
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Container stoppen:</strong><br/>
              docker-compose -f docker-compose.ui.yml down
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, color: '#f44336' }}>
            🔧 Troubleshooting
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>API nicht erreichbar:</strong><br/>
              - Container läuft? docker ps<br/>
              - Port exposed? docker-compose port pump-service 8000<br/>
              - API antwortet? curl http://localhost:8000/health
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>UI zeigt "Network Error":</strong><br/>
              - API-Base-URL: VITE_API_BASE_URL=http://localhost:8000<br/>
              - CORS-Problem? Backend muss localhost:3000 erlauben<br/>
              - Container neu gestartet? docker-compose restart
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>DB-Verbindung fehlschlägt:</strong><br/>
              - DSN korrekt? ./config/.env prüfen<br/>
              - PostgreSQL läuft? telnet host 5432<br/>
              - Credentials? Passwort zensiert in UI, aber in .env klartext
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, color: '#f44336' }}>
            📊 Ressourcen-Monitoring
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Container-Ressourcen:</strong><br/>
              docker stats pump-service pump-ui
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Logs überwachen:</strong><br/>
              docker-compose logs -f --tail=100
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Health-Checks:</strong><br/>
              docker ps --filter "health=unhealthy"
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* 10. Metrics-Seite - Detaillierte Erklärung */}
      <Card sx={{ mb: 4, bgcolor: 'rgba(255, 152, 0, 0.1)', border: '1px solid rgba(255, 152, 0, 0.3)' }}>
        <CardContent>
          <Box display="flex" alignItems="center" gap={2} mb={3}>
            <TimelineIcon sx={{ color: '#ff9800', fontSize: 30 }} />
            <Typography variant="h4" sx={{ color: '#ff9800', fontWeight: 'bold' }}>
              📊 10. Metrics-Seite - Vollständige Funktionsweise
            </Typography>
          </Box>

          <Typography variant="body2" sx={{ mb: 3 }}>
            Die Metrics-Seite zeigt Live-Statistiken und Systemstatus in Echtzeit an.
            Alle Daten werden automatisch aktualisiert und kommen aus verschiedenen Quellen.
          </Typography>

          <Typography variant="h6" sx={{ mb: 2, color: '#ff9800' }}>
            🔌 Service-Status Karten (Obere Reihe)
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>WebSocket:</strong><br/>
              ✅ Connected = ws_connected: true<br/>
              ❌ Disconnected = ws_connected: false<br/>
              <em>Datenquelle: GET /api/health</em>
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Datenbank:</strong><br/>
              ✅ Connected = db_connected: true<br/>
              ❌ Disconnected = db_connected: false<br/>
              <em>Datenquelle: GET /api/health</em>
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>n8n Service:</strong><br/>
              ✅ Available = discovery_stats.n8n_available: true<br/>
              ❌ Unavailable = discovery_stats.n8n_available: false<br/>
              <em>Datenquelle: health.discovery_stats.n8n_available</em>
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Reconnects:</strong><br/>
              Zahl = reconnect_count<br/>
              <em>Datenquelle: GET /api/health</em>
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, color: '#ff9800' }}>
            ⏱️ System-Metriken (Mittlere Reihe)
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Uptime:</strong><br/>
              Formatiert = React.useMemo(() =&gt; formatUptime(health?.uptime_seconds))<br/>
              Rohwert = uptime_seconds aus GET /api/health<br/>
              <em>Berechnung: Sekunden → Tage/Stunden/Minuten</em>
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Cache-Größe:</strong><br/>
              Zahl = cache_stats.total_coins<br/>
              <em>Datenquelle: GET /api/health → cache_stats.total_coins</em>
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Aktive Coins:</strong><br/>
              Zahl = tracking_stats.active_coins<br/>
              <em>Datenquelle: GET /api/health → tracking_stats.active_coins</em>
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Gesamt Trades:</strong><br/>
              Zahl = tracking_stats.total_trades<br/>
              <em>Datenquelle: GET /api/health → tracking_stats.total_trades</em>
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, color: '#ff9800' }}>
            📈 Stream-Statistiken (Untere Reihe)
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Diese Daten kommen aus separaten API-Calls an die Database-Endpunkte:
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Gesamt Streams:</strong><br/>
              fetchStreamsStats() → GET /api/database/streams/stats<br/>
              → total_streams<br/>
              <em>Berechnung: COUNT(*) FROM coin_streams</em>
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Aktive Streams:</strong><br/>
              fetchStreamsStats() → active_streams<br/>
              <em>Berechnung: COUNT(*) WHERE ended_at IS NULL</em>
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Beendete Streams:</strong><br/>
              fetchStreamsStats() → ended_streams<br/>
              <em>Berechnung: COUNT(*) WHERE ended_at IS NOT NULL</em>
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, color: '#ff9800' }}>
            🎯 Phasen-Verteilung (Gitter unten)
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Das Phasen-Gitter zeigt die Verteilung aller Streams nach Phasen:
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Datenquelle:</strong><br/>
              fetchStreamsStats() → streams_by_phase<br/>
              <em>SQL: GROUP BY current_phase_id</em>
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', mb: 2 }}>
              <strong>Phasen-Mapping:</strong><br/>
              Phase 1 = Baby Zone (0-30min)<br/>
              Phase 2 = Survival Zone (30min-1h)<br/>
              Phase 3 = Mature Zone (1h-2h)<br/>
              Phase 99 = Finished<br/>
              Phase 100 = Graduated
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, color: '#ff9800' }}>
            🔄 Automatische Aktualisierung
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Die Metrics-Seite aktualisiert sich automatisch:
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
              <strong>useEffect Hook:</strong><br/>
              - fetchHealth() alle 5 Sekunden<br/>
              - fetchStreamsStats() alle 10 Sekunden<br/>
              - fetchConfig() einmal beim Laden<br/>
              <em>Alle Daten werden in Zustand-Store gespeichert</em>
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, color: '#ff9800' }}>
            🚨 Fehlerbehandlung
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Bei API-Fehlern werden Fallback-Werte angezeigt:
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
              WebSocket: "Connecting..."<br/>
              Datenbank: "Connecting..."<br/>
              Uptime: "N/A"<br/>
              Zahlen: "0" oder "--"<br/>
              <em>API-Fehler werden in Browser-Console geloggt</em>
            </Typography>
          </Box>
        </CardContent>
      </Card>

      <Box sx={{ mt: 4, textAlign: 'center' }}>
        <Typography variant="body2" sx={{ color: 'text.secondary' }}>
          🔄 System läuft seit {health?.uptime_seconds ? Math.floor(health.uptime_seconds / 3600) : '?'} Stunden ohne Unterbrechung
          | Aktive Coins: {activeStreams} | Cache-Größe: {cacheSize}
        </Typography>
      </Box>
    </Container>
  );
};

export default Info;
