# 🚀 UNIFIED PUMP SERVICE
# Vereint pump-discover und pump-metric in einem Service
# Nur 1 WebSocket-Verbindung zu pumpportal.fun
# FastAPI-Version mit automatischer API-Dokumentation

import asyncio
import websockets
import json
import time
import asyncpg
import os
import re
from datetime import datetime, timezone
from dateutil import parser
from zoneinfo import ZoneInfo
from collections import Counter
from contextlib import asynccontextmanager

# FastAPI & Pydantic
from fastapi import FastAPI, BackgroundTasks, HTTPException, Response
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

# Prometheus & Server
from prometheus_client import Counter as PromCounter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Zusätzliche Metriken
n8n_available = Gauge("unified_n8n_available", "n8n Service Verfügbarkeit (1=verfügbar, 0=nicht verfügbar)")
n8n_available.set(0)  # Standardmäßig als nicht verfügbar setzen
import uvicorn

# Datenbank
from db_migration import check_and_create_schema

# === KONFIGURATION ===
# Kombiniert aus pump-discover und pump-metric

# Datenbank (aus pump-metric)
DB_DSN = os.getenv("DB_DSN", "postgresql://postgres:9HVxi6hN6j7xpmqUx84o@100.118.155.75:5432/crypto")
DB_REFRESH_INTERVAL = int(os.getenv("DB_REFRESH_INTERVAL", "10"))
DB_RETRY_DELAY = int(os.getenv("DB_RETRY_DELAY", "5"))

# WebSocket (gemeinsam) - DEAKTIVIERT wegen API-Änderung
WS_URI = os.getenv("WS_URI", "wss://pumpportal.fun/api/data")  # Temporär deaktiviert
WS_RETRY_DELAY = int(os.getenv("WS_RETRY_DELAY", "3"))
WS_MAX_RETRY_DELAY = int(os.getenv("WS_MAX_RETRY_DELAY", "60"))
WS_PING_INTERVAL = int(os.getenv("WS_PING_INTERVAL", "20"))
WS_PING_TIMEOUT = int(os.getenv("WS_PING_TIMEOUT", "5"))   # Schnellere Ping-Erkennung
WS_CONNECTION_TIMEOUT = int(os.getenv("WS_CONNECTION_TIMEOUT", "30"))  # 30s statt 300s - schneller erkennen
HEALTH_PORT = int(os.getenv("HEALTH_PORT", "8000"))

# Discovery (aus pump-discover)
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "").strip()
N8N_WEBHOOK_METHOD = os.getenv("N8N_WEBHOOK_METHOD", "POST").upper()
N8N_RETRY_DELAY = int(os.getenv("N8N_RETRY_DELAY", "5"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))
BATCH_TIMEOUT = int(os.getenv("BATCH_TIMEOUT", "30"))
BAD_NAMES_PATTERN = os.getenv("BAD_NAMES_PATTERN", "test|bot|rug|scam|cant|honey|faucet")
SPAM_BURST_WINDOW = int(os.getenv("SPAM_BURST_WINDOW", "30"))  # Sekunden für Spam-Burst-Erkennung

# Cache-System (NEU - 120 Sekunden)
COIN_CACHE_SECONDS = int(os.getenv("COIN_CACHE_SECONDS", "120"))  # 120s Cache für neue Coins

# Metric-System (aus pump-metric)
SOL_RESERVES_FULL = float(os.getenv("SOL_RESERVES_FULL", "85.0"))
AGE_CALCULATION_OFFSET_MIN = int(os.getenv("AGE_CALCULATION_OFFSET_MIN", "60"))
TRADE_BUFFER_SECONDS = int(os.getenv("TRADE_BUFFER_SECONDS", "180"))  # Für aktive Coins
WHALE_THRESHOLD_SOL = float(os.getenv("WHALE_THRESHOLD_SOL", "1.0"))
ATH_FLUSH_INTERVAL = int(os.getenv("ATH_FLUSH_INTERVAL", "5"))

# === GLOBALE VARIABLEN ===
# Lade Config aus Datei (falls vorhanden)
def load_config_from_file():
    """Lädt Konfiguration aus .env Datei (geteiltes Volume)"""
    global DB_DSN, WS_URI, DB_REFRESH_INTERVAL, SOL_RESERVES_FULL, AGE_CALCULATION_OFFSET_MIN
    global TRADE_BUFFER_SECONDS, WHALE_THRESHOLD_SOL, ATH_FLUSH_INTERVAL, DB_RETRY_DELAY, WS_RETRY_DELAY
    global WS_MAX_RETRY_DELAY, WS_PING_INTERVAL, WS_PING_TIMEOUT, WS_CONNECTION_TIMEOUT
    global N8N_WEBHOOK_URL, N8N_WEBHOOK_METHOD, BATCH_SIZE, BATCH_TIMEOUT, BAD_NAMES_PATTERN, COIN_CACHE_SECONDS, SPAM_BURST_WINDOW

    config_file = "/app/config/.env"
    if os.path.exists(config_file):
        try:
            print(f"📄 Lade Konfiguration aus {config_file}...", flush=True)
            with open(config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")

                        if value:
                            if key == "DB_DSN": DB_DSN = value
                            elif key == "WS_URI": WS_URI = value
                            elif key == "DB_REFRESH_INTERVAL" and value.isdigit(): DB_REFRESH_INTERVAL = int(value)
                            elif key == "SOL_RESERVES_FULL": SOL_RESERVES_FULL = float(value)
                            elif key == "AGE_CALCULATION_OFFSET_MIN" and value.isdigit(): AGE_CALCULATION_OFFSET_MIN = int(value)
                            elif key == "TRADE_BUFFER_SECONDS" and value.isdigit(): TRADE_BUFFER_SECONDS = int(value)
                            elif key == "WHALE_THRESHOLD_SOL": WHALE_THRESHOLD_SOL = float(value)
                            elif key == "ATH_FLUSH_INTERVAL" and value.isdigit(): ATH_FLUSH_INTERVAL = int(value)
                            elif key == "DB_RETRY_DELAY" and value.isdigit(): DB_RETRY_DELAY = int(value)
                            elif key == "WS_RETRY_DELAY" and value.isdigit(): WS_RETRY_DELAY = int(value)
                            elif key == "WS_MAX_RETRY_DELAY" and value.isdigit(): WS_MAX_RETRY_DELAY = int(value)
                            elif key == "WS_PING_INTERVAL" and value.isdigit(): WS_PING_INTERVAL = int(value)
                            elif key == "WS_PING_TIMEOUT" and value.isdigit(): WS_PING_TIMEOUT = int(value)
                            elif key == "WS_CONNECTION_TIMEOUT" and value.isdigit(): WS_CONNECTION_TIMEOUT = int(value)
                            elif key == "N8N_WEBHOOK_URL": N8N_WEBHOOK_URL = value
                            elif key == "N8N_WEBHOOK_METHOD": N8N_WEBHOOK_METHOD = value.upper()
                            elif key == "BATCH_SIZE" and value.isdigit(): BATCH_SIZE = int(value)
                            elif key == "BATCH_TIMEOUT" and value.isdigit(): BATCH_TIMEOUT = int(value)
                            elif key == "BAD_NAMES_PATTERN": BAD_NAMES_PATTERN = value
                            elif key == "COIN_CACHE_SECONDS" and value.isdigit(): COIN_CACHE_SECONDS = int(value)
                            elif key == "SPAM_BURST_WINDOW" and value.isdigit(): SPAM_BURST_WINDOW = int(value)
            print(f"✅ Konfiguration aus {config_file} geladen", flush=True)
        except Exception as e:
            print(f"⚠️ Fehler beim Laden der Config-Datei {config_file}: {e}", flush=True)
    else:
        print(f"ℹ️ Config-Datei {config_file} nicht gefunden, verwende Environment Variables", flush=True)

# Lade Config beim Start
load_config_from_file()

# Regex für Bad Names (aus pump-discover)
BAD_NAMES = re.compile(rf'({BAD_NAMES_PATTERN})', re.IGNORECASE)

# Zeitzonen
GERMAN_TZ = ZoneInfo("Europe/Berlin")

# === PROMETHEUS METRIKEN ===
# Kombiniert aus beiden Systemen
    # Discovery-Metriken (aus pump-discover)
coins_received = PromCounter("unified_coins_received_total", "Anzahl empfangener Coins")
coins_filtered = PromCounter("unified_coins_filtered_total", "Anzahl gefilterter Coins", ["reason"])
coins_sent_n8n = PromCounter("unified_coins_sent_n8n_total", "Anzahl an n8n gesendeter Coins")
n8n_batches_sent = PromCounter("unified_n8n_batches_sent_total", "Anzahl gesendeter n8n Batches")
n8n_buffer_size = Gauge("unified_n8n_buffer_size", "Anzahl Coins im n8n-Discovery-Buffer")
n8n_errors = PromCounter("unified_n8n_errors_total", "n8n Fehler", ["type"])
buffer_size = Gauge("unified_buffer_size", "Aktuelle Buffer-Größe")

# Cache-Metriken (NEU)
cache_size = Gauge("unified_cache_size", "Anzahl Coins im 120s Cache")
cache_activations = PromCounter("unified_cache_activations_total", "Cache-Aktivierungen")
cache_expirations = PromCounter("unified_cache_expirations_total", "Cache-Abläufe")

# Metric-Metriken (aus pump-metric)
trades_received = PromCounter("unified_trades_received_total", "Anzahl empfangener Trades")
trades_processed = PromCounter("unified_trades_processed_total", "Anzahl verarbeiteter Trades")
metrics_saved = PromCounter("unified_metrics_saved_total", "Anzahl gespeicherter Metriken")
coins_tracked = Gauge("unified_coins_tracked", "Anzahl aktuell getrackter Coins")
coins_graduated = PromCounter("unified_coins_graduated_total", "Anzahl graduierter Coins")
coins_finished = PromCounter("unified_coins_finished_total", "Anzahl beendeter Coins")
phase_switches = PromCounter("unified_phase_switches_total", "Anzahl Phasen-Wechsel")
db_errors = PromCounter("unified_db_errors_total", "DB Fehler", ["type"])
ws_reconnects = PromCounter("unified_ws_reconnects_total", "WebSocket Reconnects")
ws_connected = Gauge("unified_ws_connected", "WebSocket Status (1=connected)")
db_connected = Gauge("unified_db_connected", "DB Status (1=connected)")
uptime_seconds = Gauge("unified_uptime_seconds", "Uptime in Sekunden")
last_trade_timestamp = Gauge("unified_last_trade_timestamp", "Timestamp des letzten Trades")
connection_duration = Gauge("unified_connection_duration_seconds", "Dauer der aktuellen Verbindung")
db_query_duration = Histogram("unified_db_query_duration_seconds", "Dauer von DB-Queries")
flush_duration = Histogram("unified_flush_duration_seconds", "Dauer von Metric-Flushes")

# Batching-Metriken (aus pump-metric)
pending_subscriptions = Gauge("unified_pending_subscriptions", "Anzahl wartender Subscription-Requests")
batches_sent_total = PromCounter("unified_batches_sent_total", "Anzahl gesendeter Subscription-Batches")
subscriptions_batched_total = PromCounter("unified_subscriptions_batched_total", "Anzahl über Batch abonnierter Coins")
batch_size_histogram = Histogram("unified_batch_size", "Größe der Subscription-Batches", buckets=[1, 2, 5, 10, 25, 50])

# ATH-Metriken (aus pump-metric)
ath_updates_total = PromCounter("unified_ath_updates_total", "Anzahl ATH-Updates in DB")
ath_cache_size = Gauge("unified_ath_cache_size", "Anzahl Coins im ATH-Cache")

# === STATUS TRACKING ===
unified_status = {
    "db_connected": False,
    "ws_connected": False,
    "n8n_available": False,  # Standardmäßig als False setzen
    "last_error": None,
    "start_time": time.time(),
    "connection_start": None,
    "last_message_time": None,
    "reconnect_count": 0,
    "total_coins_discovered": 0,
    "total_trades": 0,
    "total_metrics_saved": 0
}


# Globale Service-Instanz
_unified_instance = None

# Globales Flag für DB-Reconnect
_force_db_reconnect = False

# === FASTAPI MODELLE ===
class CacheStats(BaseModel):
    total_coins: int
    activated_coins: int
    expired_coins: int
    oldest_age_seconds: int
    newest_age_seconds: int

class TrackingStats(BaseModel):
    active_coins: int
    total_trades: int
    total_metrics_saved: int

class DiscoveryStats(BaseModel):
    total_coins_discovered: int
    n8n_available: bool
    n8n_buffer_size: int

class HealthResponse(BaseModel):
    status: str
    ws_connected: bool
    db_connected: bool
    uptime_seconds: int
    last_message_ago: Optional[int]
    reconnect_count: int
    last_error: Optional[str]
    cache_stats: CacheStats
    tracking_stats: TrackingStats
    discovery_stats: DiscoveryStats

class ConfigReloadResponse(BaseModel):
    status: str
    message: str
    config: Dict[str, Any]

class ConfigUpdateRequest(BaseModel):
    n8n_webhook_url: Optional[str] = None
    n8n_webhook_method: Optional[str] = None
    db_dsn: Optional[str] = None
    coin_cache_seconds: Optional[int] = None
    db_refresh_interval: Optional[int] = None
    batch_size: Optional[int] = None
    batch_timeout: Optional[int] = None
    bad_names_pattern: Optional[str] = None
    spam_burst_window: Optional[int] = None

class ConfigUpdateResponse(BaseModel):
    status: str
    message: str
    updated_fields: List[str]
    new_config: Dict[str, Any]

# === FASTAPI LIFESPAN ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI Lifespan Manager für Startup/Shutdown"""
    # Startup
    print("🚀 Starting Unified Pump Service...")
    global _unified_instance
    service = UnifiedService()
    _unified_instance = service

    # Starte Service in Background-Task
    background_task = asyncio.create_task(service.run())

    yield

    # Shutdown
    print("👋 Shutting down Unified Pump Service...")
    background_task.cancel()
    try:
        await background_task
    except asyncio.CancelledError:
        pass

# === FASTAPI APP ===
app = FastAPI(
    title="Unified Pump Service",
    description="Vereinter Pump-Discover und Pump-Metric Service mit automatischer API-Dokumentation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS wird manuell über Response-Header behandelt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

# CORS für externen Zugriff
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Alle Origins für Testzwecke erlauben
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# === CACHE-SYSTEM ===
class CoinCache:
    """
    120-Sekunden Cache für neue Coins
    Sammelt neue Coins bis sie aktiviert werden oder ablaufen
    """

    def __init__(self, cache_seconds=120):
        self.cache_seconds = cache_seconds
        self.cache = {}  # {mint: coin_data}
        self.last_cleanup = time.time()

    def add_coin(self, mint, coin_data):
        """Fügt neuen Coin zum Cache hinzu"""
        now = time.time()
        self.cache[mint] = {
            "discovered_at": now,
            "metadata": coin_data.copy(),  # Vollständige Coin-Daten
            "trades": [],  # [(timestamp, trade_data), ...]
            "n8n_sent": False,  # Wurde an n8n gesendet?
            "activated": False,  # Wurde für Tracking aktiviert?
            "subscription_active": True  # Trade-Subscription aktiv?
        }

        # Cache-Größe aktualisieren
        cache_size.set(len(self.cache))

        print(f"🆕 Coin {mint[:8]}... in {self.cache_seconds}s Cache gelegt", flush=True)

    def add_trade(self, mint, trade_data):
        """Fügt Trade zu Cache hinzu (falls Coin noch nicht aktiv)"""
        if mint in self.cache and not self.cache[mint]["activated"]:
            now = time.time()
            self.cache[mint]["trades"].append((now, trade_data))

    def activate_coin(self, mint, stream_data=None):
        """Aktiviert Coin für Tracking"""
        if mint in self.cache:
            self.cache[mint]["activated"] = True
            trades = self.cache[mint]["trades"].copy()

            # Cache-Größe aktualisieren
            cache_size.set(len(self.cache))

            cache_activations.inc()
            print(f"✅ Coin {mint[:8]}... aktiviert - {len(trades)} Cache-Trades verfügbar", flush=True)

            return trades
        return []

    def remove_coin(self, mint):
        """Entfernt Coin aus Cache (bei Ablauf oder Fehler)"""
        if mint in self.cache:
            was_activated = self.cache[mint]["activated"]
            del self.cache[mint]

            # Cache-Größe aktualisieren
            cache_size.set(len(self.cache))

            if not was_activated:
                cache_expirations.inc()
                print(f"⏰ Coin {mint[:8]}... Cache abgelaufen - entfernt", flush=True)

    def cleanup_expired_coins(self, current_time=None):
        """Entfernt abgelaufene Coins aus dem Cache"""
        if current_time is None:
            current_time = time.time()

        expired_mints = []
        for mint, data in self.cache.items():
            age = current_time - data["discovered_at"]
            if age > self.cache_seconds and not data["activated"]:
                expired_mints.append(mint)

        for mint in expired_mints:
            self.remove_coin(mint)

        # Cleanup-Zeitpunkt aktualisieren
        self.last_cleanup = current_time

        return len(expired_mints)

    def get_cache_stats(self):
        """Gibt Cache-Statistiken zurück"""
        total_coins = len(self.cache)
        activated_coins = sum(1 for data in self.cache.values() if data["activated"])
        expired_coins = total_coins - activated_coins

        if self.cache:
            oldest_age = min(time.time() - data["discovered_at"] for data in self.cache.values())
            newest_age = max(time.time() - data["discovered_at"] for data in self.cache.values())
        else:
            oldest_age = newest_age = 0

        return {
            "total_coins": total_coins,
            "activated_coins": activated_coins,
            "expired_coins": expired_coins,
            "oldest_age_seconds": int(oldest_age),
            "newest_age_seconds": int(newest_age)
        }

# === FILTER-SYSTEM (aus pump-discover) ===
class CoinFilter:
    """Filtert Coins basierend auf Bad Names und Spam-Burst"""

    def __init__(self, spam_burst_window=30):
        self.recent_coins = []  # [(timestamp, name, symbol), ...] für Spam-Burst-Erkennung
        self.spam_burst_window = spam_burst_window  # Sekunden für Spam-Burst-Erkennung

    def should_filter_coin(self, coin_data):
        """Prüft ob Coin gefiltert werden soll"""
        name = coin_data.get("name", "").strip()
        symbol = coin_data.get("symbol", "").strip()

        # 1. Bad Names Filter
        if BAD_NAMES.search(name):
            coins_filtered.labels(reason="bad_name").inc()
            return True, "bad_name"

        # 2. Spam-Burst Filter (gleicher Name/Symbol in kurzer Zeit)
        now = time.time()
        recent_identical = [
            ts for ts, n, s in self.recent_coins
            if (n == name or s == symbol) and (now - ts) < self.spam_burst_window
        ]

        if recent_identical:
            coins_filtered.labels(reason="spam_burst").inc()
            return True, "spam_burst"

        # Coin ist okay - zu Recent-Liste hinzufügen
        self.recent_coins.append((now, name, symbol))

        # Recent-Liste aufräumen (älter als 2x Window)
        cutoff = now - (self.spam_burst_window * 2)
        self.recent_coins = [(ts, n, s) for ts, n, s in self.recent_coins if ts > cutoff]

        return False, None

# === FASTAPI ROUTEN ===

@app.options("/health")
async def health_options():
    """CORS Preflight für Health Endpoint"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "http://localhost:5173",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.get("/health")
async def health_check(response: Response):
    """Health-Check Endpoint mit detaillierten Infos"""
    try:
        global _unified_instance

        # === ECHTE VERBINDUNGSTESTS ===

        # 1. DB-Verbindung testen (echte Query)
        db_status = False
        try:
            if _unified_instance and hasattr(_unified_instance, 'pool') and _unified_instance.pool:
                async with _unified_instance.pool.acquire() as conn:
                    await conn.fetchval('SELECT 1')
                    db_status = True
        except Exception as e:
            print(f"❌ DB Health-Check fehlgeschlagen: {e}", flush=True)
            db_status = False

        # 2. WebSocket-Verbindung testen (nur für Health-Check)
        ws_status = False
        last_msg = unified_status.get("last_message_time")

        if last_msg:
            # WebSocket gilt als verbunden, wenn letzte Nachricht < 5min alt ist
            # (Realistisch für Token-Erstellungen - kommen nicht jede Sekunde)
            time_since_last_msg = time.time() - last_msg
            ws_status = time_since_last_msg < 300  # 5 Minuten Timeout
            if not ws_status:
                print(f"⚠️ WebSocket als offline markiert - letzte Nachricht vor {time_since_last_msg:.0f}s", flush=True)
        else:
            # Keine Nachrichten empfangen - als offline markieren
            ws_status = False
            print("⚠️ WebSocket als offline markiert - keine Nachrichten empfangen", flush=True)

        # 3. n8n-Status-Management
        n8n_status = unified_status.get("n8n_available", False)
        last_n8n_success = unified_status.get("last_n8n_success", 0)
        current_time = time.time()

        # Wenn DB oder WS offline sind, markiere n8n auch als offline
        if not db_status or not ws_status:
            if n8n_status:
                print("⚠️ n8n als offline markiert - DB/WS haben Probleme", flush=True)
                unified_status["n8n_available"] = False
                n8n_available.set(0)
                n8n_status = False

        # Timeout-Mechanismus: Wenn seit letztem erfolgreichen Senden > 1 Stunde vergangen
        # markiere n8n als offline (könnte zwischenzeitlich ausgefallen sein)
        elif n8n_status and last_n8n_success > 0 and (current_time - last_n8n_success) > 3600:
            print(f"⚠️ n8n als offline markiert - letzter Erfolg vor {(current_time - last_n8n_success)/3600:.1f}h", flush=True)
            unified_status["n8n_available"] = False
            n8n_available.set(0)
            n8n_status = False

        # n8n-Status wird durch tatsächliche Sendeversuche aktualisiert (in send_batch_to_n8n)

        uptime = time.time() - unified_status.get("start_time", time.time())

        # Cache-Statistiken
        cache_stats = CacheStats(
            total_coins=0,
            activated_coins=0,
            expired_coins=0,
            oldest_age_seconds=0,
            newest_age_seconds=0
        )
        if _unified_instance and hasattr(_unified_instance, 'coin_cache'):
            cache_data = _unified_instance.coin_cache.get_cache_stats()
            cache_stats = CacheStats(**cache_data)

        # Tracking-Statistiken
        tracking_stats = TrackingStats(
            active_coins=0,
            total_trades=unified_status.get("total_trades", 0),
            total_metrics_saved=unified_status.get("total_metrics_saved", 0)
        )
        if _unified_instance and hasattr(_unified_instance, 'watchlist'):
            tracking_stats.active_coins = len(_unified_instance.watchlist)

        # Discovery-Statistiken
        n8n_buffer_size = 0
        if _unified_instance and hasattr(_unified_instance, 'discovery_buffer'):
            n8n_buffer_size = len(_unified_instance.discovery_buffer)

        discovery_stats = DiscoveryStats(
            total_coins_discovered=unified_status.get("total_coins_discovered", 0),
            n8n_available=unified_status.get("n8n_available", False),
            n8n_buffer_size=n8n_buffer_size
        )

        health_data = HealthResponse(
            status="healthy" if (db_status and ws_status) else "degraded",
            ws_connected=ws_status,
            db_connected=db_status,
            uptime_seconds=int(uptime),
            last_message_ago=int(time.time() - last_msg) if last_msg else None,
            reconnect_count=unified_status.get("reconnect_count", 0),
            last_error=unified_status.get("last_error"),
            cache_stats=cache_stats,
            tracking_stats=tracking_stats,
            discovery_stats=discovery_stats
        )

        # CORS-Header für UI-Zugriff
        return JSONResponse(
            content=health_data.dict(),
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.options("/metrics")
async def metrics_options():
    """CORS Preflight für Metrics Endpoint"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "http://localhost:5173",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.get("/metrics", response_class=PlainTextResponse)
async def metrics_handler(response: Response):
    """Prometheus Metrics Endpoint"""
    uptime_seconds.set(time.time() - unified_status["start_time"])
    if unified_status["connection_start"]:
        connection_duration.set(time.time() - unified_status["connection_start"])

    # n8n_available Gauge aktualisieren
    n8n_available.set(1 if unified_status.get("n8n_available", False) else 0)

    # CORS-Header für UI-Zugriff
    metrics_data = generate_latest()
    return PlainTextResponse(
        content=metrics_data,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.post("/reload-config", response_model=ConfigReloadResponse)
async def reload_config():
    """Lädt die Konfiguration und Phasen neu"""
    try:
        load_config_from_file()
        # Phasen-Konfiguration auch neu laden
        if _unified_instance:
            await _unified_instance.load_phases_config()
        print("🔄 Konfiguration und Phasen neu geladen!", flush=True)

        response = ConfigReloadResponse(
            status="success",
            message="Konfiguration wurde neu geladen",
            config={
                "COIN_CACHE_SECONDS": COIN_CACHE_SECONDS,
                "DB_REFRESH_INTERVAL": DB_REFRESH_INTERVAL,
                "BATCH_SIZE": BATCH_SIZE
            }
        )
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Config reload failed: {str(e)}")

def update_global_config(updates: Dict[str, Any]):
    """Aktualisiert die globalen Konfigurationsvariablen"""
    global N8N_WEBHOOK_URL, N8N_WEBHOOK_METHOD, DB_DSN, COIN_CACHE_SECONDS
    global DB_REFRESH_INTERVAL, BATCH_SIZE, BATCH_TIMEOUT, BAD_NAMES_PATTERN, SPAM_BURST_WINDOW

    # Aktualisiere globale Variablen
    if "N8N_WEBHOOK_URL" in updates:
        N8N_WEBHOOK_URL = updates["N8N_WEBHOOK_URL"]
    if "N8N_WEBHOOK_METHOD" in updates:
        N8N_WEBHOOK_METHOD = updates["N8N_WEBHOOK_METHOD"]
    if "DB_DSN" in updates:
        DB_DSN = updates["DB_DSN"]
    if "COIN_CACHE_SECONDS" in updates:
        COIN_CACHE_SECONDS = int(updates["COIN_CACHE_SECONDS"])
    if "DB_REFRESH_INTERVAL" in updates:
        DB_REFRESH_INTERVAL = int(updates["DB_REFRESH_INTERVAL"])
    if "BATCH_SIZE" in updates:
        BATCH_SIZE = int(updates["BATCH_SIZE"])
    if "BATCH_TIMEOUT" in updates:
        BATCH_TIMEOUT = int(updates["BATCH_TIMEOUT"])
    if "BATCH_TIMEOUT" in updates:
        BATCH_TIMEOUT = int(updates["BATCH_TIMEOUT"])
    if "BAD_NAMES_PATTERN" in updates:
        global BAD_NAMES_PATTERN, BAD_NAMES
        BAD_NAMES_PATTERN = updates["BAD_NAMES_PATTERN"]
        BAD_NAMES = re.compile(rf'({BAD_NAMES_PATTERN})', re.IGNORECASE)
    if "SPAM_BURST_WINDOW" in updates:
        global SPAM_BURST_WINDOW
        SPAM_BURST_WINDOW = int(updates["SPAM_BURST_WINDOW"])
        # Filter-Konfiguration wird bei Bedarf automatisch aktualisiert

def save_config_to_env(updates: Dict[str, Any]) -> bool:
    """Speichert Konfigurationsänderungen in die .env Datei"""
    config_file = "/app/config/.env" if os.path.exists("/app/config/.env") else "./config/.env"

    # Lade bestehende Konfiguration
    current_config = {}
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        current_config[key.strip()] = value.strip()
        except Exception as e:
            print(f"⚠️ Fehler beim Lesen der Config-Datei: {e}")
            return False

    # Aktualisiere mit neuen Werten
    current_config.update(updates)

    # Schreibe zurück in Datei
    try:
        with open(config_file, 'w') as f:
            f.write("# Unified Pump Service Configuration\n")
            f.write("# Diese Datei wird vom Service zur Laufzeit geladen\n\n")

            for key, value in sorted(current_config.items()):
                if value is not None:
                    f.write(f"{key}={value}\n")

        print(f"💾 Konfiguration in {config_file} gespeichert: {updates}")
        return True
    except Exception as e:
        print(f"❌ Fehler beim Speichern der Config-Datei: {e}")
        return False

@app.put("/config", response_model=ConfigUpdateResponse)
async def update_config(config_update: ConfigUpdateRequest, response: Response):
    """Aktualisiert die Konfiguration zur Laufzeit und speichert sie persistent"""
    try:
        # Debug: Log received data
        print(f"🔧 START Config Update", flush=True)
        print(f"🔧 Config Update Request: {config_update}", flush=True)

        # Sammle Änderungen
        updates = {}
        updated_fields = []

        # Validierung und Mapping der Felder
        if config_update.n8n_webhook_url is not None:
            updates["N8N_WEBHOOK_URL"] = config_update.n8n_webhook_url
            updated_fields.append("n8n_webhook_url")

        if config_update.n8n_webhook_method is not None:
            method = config_update.n8n_webhook_method.upper()
            if method in ["GET", "POST"]:
                updates["N8N_WEBHOOK_METHOD"] = method
                updated_fields.append("n8n_webhook_method")
            else:
                raise HTTPException(status_code=400, detail="n8n_webhook_method must be 'GET' or 'POST'")

        print(f"DEBUG: db_dsn is not None check: {config_update.db_dsn is not None}, value: {repr(config_update.db_dsn)}", flush=True)
        if config_update.db_dsn is not None:
            # Verhindere Speicherung zensierter Passwörter
            print(f"DEBUG: db_dsn received: {config_update.db_dsn}", flush=True)
            if "***" in config_update.db_dsn:
                print("🚨 BLOCKIERE: Zensiertes Passwort erkannt!", flush=True)
                raise HTTPException(status_code=400, detail="Cannot save censored password. Please enter the full database connection string.")
            updates["DB_DSN"] = config_update.db_dsn
            updated_fields.append("db_dsn")

        if config_update.coin_cache_seconds is not None:
            if config_update.coin_cache_seconds < 10 or config_update.coin_cache_seconds > 3600:
                raise HTTPException(status_code=400, detail="coin_cache_seconds must be between 10 and 3600")
            updates["COIN_CACHE_SECONDS"] = str(config_update.coin_cache_seconds)
            updated_fields.append("coin_cache_seconds")

        if config_update.db_refresh_interval is not None:
            if config_update.db_refresh_interval < 5 or config_update.db_refresh_interval > 300:
                raise HTTPException(status_code=400, detail="db_refresh_interval must be between 5 and 300")
            updates["DB_REFRESH_INTERVAL"] = str(config_update.db_refresh_interval)
            updated_fields.append("db_refresh_interval")

        if config_update.batch_size is not None:
            if config_update.batch_size < 1 or config_update.batch_size > 100:
                raise HTTPException(status_code=400, detail="batch_size must be between 1 and 100")
            updates["BATCH_SIZE"] = str(config_update.batch_size)
            updated_fields.append("batch_size")

        if config_update.batch_timeout is not None:
            if config_update.batch_timeout < 10 or config_update.batch_timeout > 300:
                raise HTTPException(status_code=400, detail="batch_timeout must be between 10 and 300 seconds")
            updates["BATCH_TIMEOUT"] = str(config_update.batch_timeout)
            updated_fields.append("batch_timeout")

        if config_update.bad_names_pattern is not None:
            # Grundlegende Validierung - sollte ein Regex-Pattern sein
            if not config_update.bad_names_pattern.strip():
                raise HTTPException(status_code=400, detail="bad_names_pattern cannot be empty")
            updates["BAD_NAMES_PATTERN"] = config_update.bad_names_pattern
            updated_fields.append("bad_names_pattern")

        if config_update.spam_burst_window is not None:
            if config_update.spam_burst_window < 5 or config_update.spam_burst_window > 300:
                raise HTTPException(status_code=400, detail="spam_burst_window must be between 5 and 300 seconds")
            updates["SPAM_BURST_WINDOW"] = str(config_update.spam_burst_window)
            updated_fields.append("spam_burst_window")

        if not updates:
            raise HTTPException(status_code=400, detail="No valid configuration fields provided")

        # Speichere in .env Datei (optional für lokale Entwicklung)
        try:
            save_config_to_env(updates)
        except Exception as e:
            print(f"⚠️ Config-Datei konnte nicht gespeichert werden: {e} - Setze nur Runtime-Konfiguration", flush=True)

        # Aktualisiere globale Variablen
        update_global_config(updates)

        # Spezielle Behandlung für DB-DSN Änderung
        global _force_db_reconnect
        if "DB_DSN" in updates:
            print("🔄 DB-DSN geändert - forciere DB-Reconnect beim nächsten Check...")
            _force_db_reconnect = True

        # Erstelle Response
        config_response = ConfigUpdateResponse(
            status="success",
            message=f"Konfiguration aktualisiert: {', '.join(updated_fields)}",
            updated_fields=updated_fields,
            new_config={
                "n8n_webhook_url": config_update.n8n_webhook_url,
                "n8n_webhook_method": config_update.n8n_webhook_method,
                "db_dsn": config_update.db_dsn,
                "coin_cache_seconds": config_update.coin_cache_seconds,
                "db_refresh_interval": config_update.db_refresh_interval,
                "batch_size": config_update.batch_size
            }
        )

        # CORS-Header für UI-Zugriff
        print(f"✅ Konfiguration aktualisiert über API: {updated_fields}")
        return JSONResponse(
            content=config_response.dict(),
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Config update failed: {str(e)}")

@app.options("/config")
async def config_options():
    """CORS Preflight für Config Endpoint"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "http://localhost:5173",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.get("/config", response_model=Dict[str, Any])
async def get_current_config(response: Response):
    """Zeigt die aktuelle Konfiguration an"""
    try:
        global BATCH_TIMEOUT  # Sicherstellen, dass die Variable verfügbar ist
        config = {
            "n8n_webhook_url": N8N_WEBHOOK_URL,
            "n8n_webhook_method": N8N_WEBHOOK_METHOD,
            "db_dsn": DB_DSN.replace(DB_DSN.split('@')[0].split(':')[-1], "***") if '@' in DB_DSN else "***",  # Passwort verstecken
            "coin_cache_seconds": COIN_CACHE_SECONDS,
            "db_refresh_interval": DB_REFRESH_INTERVAL,
            "batch_size": BATCH_SIZE,
            "batch_timeout": BATCH_TIMEOUT,
            "bad_names_pattern": "test|bot|rug|scam|cant|honey|faucet",  # Standardwerte
            "spam_burst_window": 30,  # Standardwerte
            "sol_reserves_full": SOL_RESERVES_FULL,
            "whale_threshold_sol": WHALE_THRESHOLD_SOL,
            "age_calculation_offset_min": AGE_CALCULATION_OFFSET_MIN,
            "trade_buffer_seconds": TRADE_BUFFER_SECONDS,
            "ath_flush_interval": ATH_FLUSH_INTERVAL
        }

        # CORS-Header für UI-Zugriff
        return JSONResponse(
            content=config,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")


@app.get("/database/phases")
async def get_phases():
    """Gibt alle Phasen aus der ref_coin_phases Tabelle zurück"""
    try:
        if not _unified_instance or not _unified_instance.pool:
            raise HTTPException(status_code=503, detail="Database not connected")

        rows = await _unified_instance.pool.fetch("SELECT * FROM ref_coin_phases ORDER BY id ASC")
        phases = [dict(row) for row in rows]

        return {
            "phases": phases,
            "count": len(phases)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get phases: {str(e)}")


@app.get("/database/streams")
async def get_streams(limit: int = 50):
    """Gibt Streams aus der coin_streams Tabelle zurück"""
    try:
        if not _unified_instance or not _unified_instance.pool:
            raise HTTPException(status_code=503, detail="Database not connected")

        rows = await _unified_instance.pool.fetch("""
            SELECT * FROM coin_streams
            ORDER BY id DESC
            LIMIT $1
        """, limit)

        streams = [dict(row) for row in rows]

        return {
            "streams": streams,
            "count": len(streams),
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get streams: {str(e)}")


@app.get("/database/streams/stats")
async def get_streams_stats():
    """Gibt Statistiken über Streams und Phasen zurück"""
    try:
        if not _unified_instance or not _unified_instance.pool:
            raise HTTPException(status_code=503, detail="Database not connected")

        # Anzahl Streams pro Phase
        phase_counts = await _unified_instance.pool.fetch("""
            SELECT current_phase_id, COUNT(*) as count
            FROM coin_streams
            GROUP BY current_phase_id
            ORDER BY current_phase_id ASC
        """)

        # Gesamtanzahl Streams
        total_count = await _unified_instance.pool.fetchval("SELECT COUNT(*) FROM coin_streams")

        # Aktive Streams (nicht beendet)
        active_count = await _unified_instance.pool.fetchval("""
            SELECT COUNT(*) FROM coin_streams
            WHERE is_active = TRUE
        """)

        stats = {
            "total_streams": total_count,
            "active_streams": active_count,
            "ended_streams": total_count - active_count,
            "streams_by_phase": {row["current_phase_id"]: row["count"] for row in phase_counts}
        }

        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stream stats: {str(e)}")


@app.get("/database/metrics")
async def get_recent_metrics(limit: int = 100, mint: Optional[str] = None):
    """Gibt die letzten Metriken aus der coin_metrics Tabelle zurück

    Query-Parameter:
    - limit: Anzahl der zurückzugebenden Einträge (Standard: 100)
    - mint: Optional - Filter nach spezifischem Token-Mint (z.B. für historische Daten eines Coins)
    """
    try:
        if not _unified_instance or not _unified_instance.pool:
            raise HTTPException(status_code=503, detail="Database not connected")

        # Baue die Query dynamisch auf
        query = "SELECT * FROM coin_metrics"
        params = []

        # Füge WHERE-Klausel hinzu, wenn mint angegeben ist
        if mint and mint.strip():
            query += " WHERE mint = $1"
            params.append(mint.strip())

        # Sortierung und Limit
        if params:
            query += " ORDER BY timestamp DESC LIMIT $2"
            params.append(limit)
        else:
            query += " ORDER BY timestamp DESC LIMIT $1"
            params.append(limit)

        rows = await _unified_instance.pool.fetch(query, *params)

        metrics = [dict(row) for row in rows]

        return {
            "metrics": metrics,
            "count": len(metrics),
            "limit": limit,
            "mint_filter": mint  # Zeige angewendeten Filter in Response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

# Analytics-Routen vorübergehend deaktiviert

# === HELPER FUNCTIONS FOR ANALYTICS ===

def parse_time_windows(windows_str: str) -> dict:
    """Parse Zeitfenster-String in Dictionary mit Sekunden-Werten"""
    windows = {}
    for window in windows_str.split(','):
        window = window.strip()
        if not window:
            continue

        # Parse Suffix
        if window.endswith('s'):
            seconds = int(window[:-1])
        elif window.endswith('m'):
            seconds = int(window[:-1]) * 60
        elif window.endswith('h'):
            seconds = int(window[:-1]) * 3600
        else:
            # Fallback: Minuten
            seconds = int(window) * 60

        windows[window] = {'seconds': seconds}

    return windows

async def check_coin_active_status(mint: str) -> bool:
    """Prüfe ob Coin in aktiven Streams ist"""
    try:
        if not _unified_instance or not _unified_instance.pool:
            return False

        row = await _unified_instance.pool.fetchrow(
            "SELECT is_active FROM coin_streams WHERE token_address = $1",
            mint
        )
        return row['is_active'] if row else False
    except Exception as e:
        print(f"[Analytics] Error checking active status for {mint}: {e}", flush=True)
        return False

async def get_current_coin_data(mint: str) -> dict:
    """Hole neueste Daten für einen Coin"""
    if not _unified_instance or not _unified_instance.pool:
        return None

    try:
        row = await _unified_instance.pool.fetchrow(
            "SELECT * FROM coin_metrics WHERE mint = $1 ORDER BY timestamp DESC LIMIT 1",
            mint
        )
        return dict(row) if row else None
    except Exception as e:
        print(f"[Analytics] Error getting current data for {mint}: {e}", flush=True)
        return None

async def get_historical_data(mint: str, max_seconds: int) -> list:
    """Hole historische Daten für Zeitfenster-Analyse"""
    if not _unified_instance or not _unified_instance.pool:
        return []

    try:
        # Hole alle verfügbaren Daten für diesen Coin (letzte 24h minimum)
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=max(max_seconds, 86400))

        rows = await _unified_instance.pool.fetch(
            "SELECT * FROM coin_metrics WHERE mint = $1 AND timestamp >= $2 ORDER BY timestamp ASC",
            mint, cutoff_time
        )

        historical_data = [dict(row) for row in rows]
        print(f"[Analytics] Loaded {len(historical_data)} historical data points for {mint}", flush=True)

        return historical_data
    except Exception as e:
        print(f"[Analytics] Error getting historical data for {mint}: {e}", flush=True)
        return []

def calculate_window_analytics(current_data: dict, historical_data: list, target_time: datetime) -> dict:
    """Berechne Analytics für ein spezifisches Zeitfenster"""
    if not historical_data:
        return {
            "price_change_pct": None,
            "old_price": None,
            "trend": "❓ NO_DATA",
            "data_found": False,
            "data_age_seconds": None
        }

    # Finde den nächsten Datenpunkt zum Zielzeitpunkt
    best_match = None
    best_diff = float('inf')

    for data_point in historical_data:
        diff = abs((data_point['timestamp'] - target_time).total_seconds())
        if diff < best_diff:
            best_diff = diff
            best_match = data_point

    if not best_match:
        return {
            "price_change_pct": None,
            "old_price": None,
            "trend": "❓ NO_DATA",
            "data_found": False,
            "data_age_seconds": None
        }

    # Berechnungen
    current_price = current_data['price_close']
    old_price = best_match['price_close']

    if old_price and old_price > 0:
        price_change_pct = ((current_price - old_price) / old_price) * 100
    else:
        price_change_pct = None

    # Trend basierend auf Preisänderung
    if price_change_pct is None:
        trend = "❓ NO_DATA"
    elif price_change_pct > 5:
        trend = "🚀 PUMP"
    elif price_change_pct < -5:
        trend = "📉 DUMP"
    else:
        trend = "➡️ FLAT"

    return {
        "price_change_pct": round(price_change_pct, 2) if price_change_pct is not None else None,
        "old_price": old_price,
        "trend": trend,
        "data_found": True,
        "data_age_seconds": int(best_diff)
    }

# === N8N INTEGRATION (FastAPI-Version mit httpx) ===
import httpx

async def test_n8n_availability():
    """Testet die Verfügbarkeit von n8n beim Start"""
    if not N8N_WEBHOOK_URL:
        unified_status["n8n_available"] = False
        n8n_available.set(0)
        print("ℹ️ n8n Webhook nicht konfiguriert", flush=True)
        return

    try:
        # Versuche eine einfache Test-Anfrage
        test_url = N8N_WEBHOOK_URL.replace('/webhook/', '/health')
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(test_url, timeout=5.0)
            if response.status_code in [200, 404]:  # 404 ist ok, bedeutet nur kein /health endpoint
                unified_status["n8n_available"] = True
                n8n_available.set(1)
                print("✅ n8n Service verfügbar", flush=True)
            else:
                unified_status["n8n_available"] = False
                n8n_available.set(0)
                print(f"⚠️ n8n Service Status: {response.status_code}", flush=True)
    except Exception as e:
        unified_status["n8n_available"] = False
        n8n_available.set(0)
        print(f"⚠️ n8n Service nicht erreichbar: {str(e)[:50]}", flush=True)

async def send_batch_to_n8n(batch):
    """Sendet Batch an n8n (FastAPI-Version mit httpx)"""
    if not N8N_WEBHOOK_URL:
        print("❌ FEHLER: N8N_WEBHOOK_URL ist nicht gesetzt!", flush=True)
        return False

    max_retries = 3
    retry_count = 0

    payload = {
        "source": "unified_pump_service",
        "count": len(batch),
        "timestamp": datetime.utcnow().isoformat(),
        "data": batch
    }

    while retry_count < max_retries:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                if N8N_WEBHOOK_METHOD == "GET":
                    import urllib.parse
                    json_data = json.dumps(payload)
                    encoded_data = urllib.parse.quote(json_data)
                    url_with_params = f"{N8N_WEBHOOK_URL}?data={encoded_data}"

                    resp = await client.get(url_with_params)
                else:
                    resp = await client.post(N8N_WEBHOOK_URL, json=payload)

                status = resp.status_code

            if status == 200:
                print(f"📦 Paket ({len(batch)} Coins) an n8n übergeben! ✅", flush=True)
                unified_status["n8n_available"] = True
                unified_status["last_n8n_success"] = time.time()  # Timestamp des Erfolgs
                n8n_available.set(1)
                n8n_batches_sent.inc()
                coins_sent_n8n.inc(len(batch))
                return True
            elif status == 404:
                print("❌ n8n Fehler 404: Bitte n8n Webhook überprüfen!", flush=True)
                unified_status["n8n_available"] = False
                n8n_available.set(0)
                n8n_errors.labels(type="404").inc()
                return False
            else:
                print(f"⚠️ n8n Status: {status} (Retry {retry_count + 1}/{max_retries})", flush=True)
                unified_status["n8n_available"] = False
                n8n_available.set(0)
                n8n_errors.labels(type=f"status_{status}").inc()
                retry_count += 1

        except httpx.TimeoutException:
            print(f"⚠️ n8n Timeout (Retry {retry_count + 1}/{max_retries})", flush=True)
            unified_status["n8n_available"] = False
            n8n_available.set(0)
            n8n_errors.labels(type="timeout").inc()
            retry_count += 1
        except httpx.RequestError as e:
            print(f"⚠️ n8n Connection Error: {e} (Retry {retry_count + 1}/{max_retries})", flush=True)
            unified_status["n8n_available"] = False
            n8n_available.set(0)
            n8n_errors.labels(type="connection").inc()
            retry_count += 1
        except Exception as e:
            print(f"⚠️ n8n Unerwarteter Fehler: {e}", flush=True)
            unified_status["n8n_available"] = False
            n8n_available.set(0)
            n8n_errors.labels(type="unknown").inc()
            return False

        if retry_count < max_retries:
            await asyncio.sleep(N8N_RETRY_DELAY * retry_count)

        unified_status["n8n_available"] = False
        n8n_available.set(0)
    print("❌ n8n nicht erreichbar nach allen Versuchen", flush=True)
    return False

# === UNIFIED SERVICE KLASSE ===
class UnifiedService:
    """
    Vereinter Service für Pump-Discovery und Metric-Tracking
    Verwendet nur 1 WebSocket-Verbindung
    """

    def __init__(self):
        # Datenbank
        self.pool = None
        self.phases_config = {}
        self.sorted_phase_ids = []

        # Cache-System (NEU)
        self.coin_cache = CoinCache(COIN_CACHE_SECONDS)
        self.coin_filter = CoinFilter(SPAM_BURST_WINDOW)

        # Watchlist für aktive Coins (aus pump-metric)
        self.watchlist = {}  # {mint: entry}
        self.subscribed_mints = set()

        # Trade-Buffer für aktive Coins (aus pump-metric)
        self.trade_buffer = {}  # {mint: [(timestamp, trade_data), ...]}
        self.last_buffer_cleanup = time.time()

        # ATH-Tracking (aus pump-metric)
        self.ath_cache = {}  # {mint: ath_price}
        self.dirty_aths = set()
        self.last_ath_flush = time.time()

        # Zombie-Coin Detection & Watchdog
        self.last_trade_timestamps = {}  # {mint: timestamp}
        self.subscription_watchdog = {}  # {mint: last_heartbeat}
        self.stale_data_warnings = {}  # {mint: warning_count}
        self.last_saved_signatures = {}  # {mint: last_saved_data_signature}

        # WebSocket Batching (aus pump-metric)
        self.pending_subscriptions = set()
        self.batching_task = None
        self.last_batch_flush = time.time()

        # Discovery-Buffer (aus pump-discover)
        self.discovery_buffer = []
        self.last_discovery_flush = time.time()

    # === DATENBANK METHODEN ===
    async def init_db_connection(self):
        """Datenbank-Verbindung aufbauen (aus pump-metric)"""
        while True:
            try:
                if self.pool:
                    await self.pool.close()

                self.pool = await asyncpg.create_pool(DB_DSN, min_size=1, max_size=10)
                await check_and_create_schema(self.pool)

                # Phasen-Konfiguration laden
                rows = await self.pool.fetch("SELECT * FROM ref_coin_phases ORDER BY id ASC")
                self.phases_config = {}
                for row in rows:
                    self.phases_config[row["id"]] = {
                        "interval": row["interval_seconds"],
                        "max_age": row["max_age_minutes"],
                        "name": row["name"]
                    }
                self.sorted_phase_ids = sorted(self.phases_config.keys())

                print(f"✅ DB verbunden. Geladene Phasen: {self.sorted_phase_ids}", flush=True)
                unified_status["db_connected"] = True
                unified_status["last_error"] = None
                db_connected.set(1)
                return

            except Exception as e:
                unified_status["db_connected"] = False
                unified_status["last_error"] = f"db_error: {str(e)[:100]}"
                db_connected.set(0)
                db_errors.labels(type="connection").inc()
                print(f"❌ DB Verbindungsfehler: {e}", flush=True)
                print(f"⏳ Retry in {DB_RETRY_DELAY}s...", flush=True)
                await asyncio.sleep(DB_RETRY_DELAY)

    async def force_db_reconnect(self):
        """Erzwingt eine DB-Neuverbindung mit neuen Credentials"""
        print("🔄 Erzwinge DB-Reconnect mit neuen Credentials...")
        try:
            if self.pool:
                await self.pool.close()
                self.pool = None

            # Neue Verbindung mit aktueller DSN aufbauen
            self.pool = await asyncpg.create_pool(DB_DSN, min_size=1, max_size=10)
            await check_and_create_schema(self.pool)

            # Phasen neu laden
            rows = await self.pool.fetch("SELECT * FROM ref_coin_phases ORDER BY id ASC")
            self.phases_config = {}
            for row in rows:
                self.phases_config[row["id"]] = {
                    "interval": row["interval_seconds"],
                    "max_age": row["max_age_minutes"],
                    "name": row["name"]
                }
            self.sorted_phase_ids = sorted(self.phases_config.keys())

            unified_status["db_connected"] = True
            unified_status["last_error"] = None
            db_connected.set(1)
            print("✅ DB-Reconnect erfolgreich mit neuen Credentials!")

        except Exception as e:
            unified_status["db_connected"] = False
            unified_status["last_error"] = f"db_reconnect_failed: {str(e)[:100]}"
            db_connected.set(0)
            db_errors.labels(type="reconnect").inc()
            print(f"❌ DB-Reconnect fehlgeschlagen: {e}")
            raise

    async def get_active_streams(self):
        """Lädt aktive Coin-Streams (aus pump-metric)"""
        try:
            with db_query_duration.time():
                # Repair fehlende Streams
                try:
                    await self.pool.execute("SELECT repair_missing_streams()")
                except:
                    pass  # Funktion existiert vielleicht noch nicht

                # Aktive Streams laden
                sql = """
                    SELECT cs.token_address, cs.current_phase_id, dc.token_created_at,
                           cs.started_at, dc.trader_public_key, cs.ath_price_sol
                    FROM coin_streams cs
                    JOIN discovered_coins dc ON cs.token_address = dc.token_address
                    WHERE cs.is_active = TRUE
                """
                rows = await self.pool.fetch(sql)
                results = {}

                for row in rows:
                    mint = row["token_address"]
                    created_at = row["token_created_at"]
                    started_at = row["started_at"]

                    if not created_at: created_at = datetime.now(timezone.utc)
                    if created_at.tzinfo is None: created_at = created_at.replace(tzinfo=timezone.utc)
                    if started_at and started_at.tzinfo is None: started_at = started_at.replace(tzinfo=timezone.utc)

                    # ATH aus DB laden
                    db_ath = row.get("ath_price_sol")
                    if db_ath is None: db_ath = 0.0
                    else: db_ath = float(db_ath)

                    if mint not in self.ath_cache:
                        self.ath_cache[mint] = db_ath
                    elif self.ath_cache[mint] < db_ath:
                        self.ath_cache[mint] = db_ath

                    results[mint] = {
                        "phase_id": row["current_phase_id"],
                        "created_at": created_at,
                        "started_at": started_at or created_at,
                        "creator_address": row.get("trader_public_key")
                    }

                ath_cache_size.set(len(self.ath_cache))
                return results

        except Exception as e:
            print(f"⚠️ DB Query Error: {e}", flush=True)
            unified_status["db_connected"] = False
            db_connected.set(0)
            db_errors.labels(type="query").inc()
            raise

    # === CACHE-MANAGEMENT ===
    async def check_cache_activation(self):
        """Prüft Cache auf zu aktivierende Coins"""
        current_time = time.time()
        active_streams = await self.get_active_streams()
        active_mints = set(active_streams.keys())

        activated_count = 0
        expired_count = 0

        for mint in list(self.coin_cache.cache.keys()):
            cache_data = self.coin_cache.cache[mint]
            age = current_time - cache_data["discovered_at"]

            if age >= COIN_CACHE_SECONDS:
                if mint in active_mints:
                    # Coin wurde aktiviert - Cache-Trades verarbeiten
                    trades = self.coin_cache.activate_coin(mint, active_streams[mint])
                    await self.process_cached_trades(mint, trades, active_streams[mint])
                    activated_count += 1
                else:
                    # Cache abgelaufen - entfernen
                    self.coin_cache.remove_coin(mint)
                    expired_count += 1

        # Cache-Cleanup
        cleaned = self.coin_cache.cleanup_expired_coins(current_time)

        if activated_count > 0 or expired_count > 0 or cleaned > 0:
            print(f"🔄 Cache-Management: {activated_count} aktiviert, {expired_count + cleaned} entfernt", flush=True)

        return activated_count, expired_count + cleaned

    async def process_cached_trades(self, mint, cached_trades, stream_data):
        """Verarbeitet Cache-Trades für neu aktivierte Coins"""
        if not cached_trades:
            return

        # Watchlist-Eintrag erstellen
        p_id = stream_data["phase_id"]
        if p_id not in self.phases_config:
            p_id = self.sorted_phase_ids[0] if self.sorted_phase_ids else 1

        interval = self.phases_config[p_id]["interval"]
        self.watchlist[mint] = {
            "meta": stream_data,
            "buffer": self.get_empty_buffer(),
            "next_flush": time.time() + interval,
            "interval": interval
        }
        self.subscribed_mints.add(mint)

        # Cache-Trades verarbeiten (chronologisch)
        cached_trades.sort(key=lambda x: x[0])  # Nach Timestamp sortieren
        processed_count = 0

        for trade_ts, trade_data in cached_trades:
            if mint in self.watchlist:
                self.process_trade(trade_data)
                processed_count += 1
                trades_processed.inc()

        print(f"🔄 {processed_count} Cache-Trades für {mint[:8]}... verarbeitet", flush=True)

    # === DISCOVERY-METHODEN ===
    async def process_new_coin(self, coin_data):
        """Verarbeitet neuen Coin (Discovery-Logik)"""
        mint = coin_data.get("mint")
        if not mint:
            return

        # 1. Filter anwenden
        should_filter, reason = self.coin_filter.should_filter_coin(coin_data)
        if should_filter:
            print(f"🚫 Coin {coin_data.get('symbol', '???')} gefiltert: {reason}", flush=True)
            return

        # 2. Berechnungen (aus pump-discover)
        v_tokens = coin_data.get("vTokensInBondingCurve", 0)
        market_cap = coin_data.get("marketCapSol", 0)

        if v_tokens and v_tokens > 0:
            price_sol = market_cap / v_tokens
        else:
            price_sol = 0

        social_count = 0
        if coin_data.get("twitter_url") or coin_data.get("twitter"): social_count += 1
        if coin_data.get("telegram_url") or coin_data.get("telegram"): social_count += 1
        if coin_data.get("website_url") or coin_data.get("website"): social_count += 1
        if coin_data.get("discord_url") or coin_data.get("discord"): social_count += 1

        coin_data["price_sol"] = price_sol
        coin_data["pool_address"] = coin_data.get("bondingCurveKey", "")
        coin_data["social_count"] = social_count

        # 3. In Cache legen
        self.coin_cache.add_coin(mint, coin_data)

        # 4. Sofort für Trades abonnieren
        self.pending_subscriptions.add(mint)

        # 5. An Discovery-Buffer für n8n hinzufügen
        self.discovery_buffer.append(coin_data)
        n8n_buffer_size.set(len(self.discovery_buffer))

        unified_status["total_coins_discovered"] += 1
        coins_received.inc()

        print(f"➕ Neuer Coin: {coin_data.get('symbol', '???')} (Cache: {len(self.coin_cache.cache)})", flush=True)

    async def flush_discovery_buffer(self):
        """Sendet Discovery-Buffer an n8n"""
        if not self.discovery_buffer:
            return

        is_full = len(self.discovery_buffer) >= BATCH_SIZE
        is_timeout = (time.time() - self.last_discovery_flush) > BATCH_TIMEOUT

        if is_full or is_timeout:
            print(f"🚚 Sende {len(self.discovery_buffer)} Coins an n8n...", flush=True)
            success = await send_batch_to_n8n(self.discovery_buffer)

            if success:
                # Markiere Coins als an n8n gesendet
                for coin in self.discovery_buffer:
                    mint = coin.get("mint")
                    if mint in self.coin_cache.cache:
                        self.coin_cache.cache[mint]["n8n_sent"] = True

                self.discovery_buffer = []
                n8n_buffer_size.set(0)
                buffer_size.set(0)
            self.last_discovery_flush = time.time()

    # === METRIC-METHODEN (aus pump-metric) ===
    def get_empty_buffer(self):
        """Leerer Buffer für neue Coins"""
        return {
            "open": None, "high": -1, "low": float("inf"), "close": 0,
            "vol": 0, "vol_buy": 0, "vol_sell": 0, "buys": 0, "sells": 0,
            "micro_trades": 0, "max_buy": 0, "max_sell": 0,
            "wallets": set(), "v_sol": 0, "mcap": 0,
            "whale_buy_vol": 0, "whale_sell_vol": 0, "whale_buys": 0, "whale_sells": 0,
            "dev_sold_amount": 0
        }

    def process_trade(self, data):
        """Verarbeitet einzelnen Trade (aus pump-metric)"""
        mint = data["mint"]
        if mint not in self.watchlist:
            return

        entry = self.watchlist[mint]
        buf = entry["buffer"]
        now_ts = time.time()

        try:
            sol = float(data["solAmount"])
            price = float(data["vSolInBondingCurve"]) / float(data["vTokensInBondingCurve"])
            is_buy = data["txType"] == "buy"
            trader_key = data.get("traderPublicKey", "")
        except:
            return

        # === ZOMBIE DETECTION: Trade-Timestamp tracken ===
        self.last_trade_timestamps[mint] = now_ts
        self.subscription_watchdog[mint] = now_ts

        print(f"[Trade] {mint[:8]}... @ {price:.2e} SOL - {'BUY' if is_buy else 'SELL'} {sol:.6f} SOL", flush=True)

        # ATH-Tracking
        known_ath = self.ath_cache.get(mint, 0.0)
        if price > known_ath:
            self.ath_cache[mint] = price
            self.dirty_aths.add(mint)

        # Trade-Daten sammeln
        if buf["open"] is None: buf["open"] = price
        buf["close"] = price
        buf["high"] = max(buf["high"], price)
        buf["low"] = min(buf["low"], price)
        buf["vol"] += sol

        if is_buy:
            buf["buys"] += 1
            buf["vol_buy"] += sol
            buf["max_buy"] = max(buf["max_buy"], sol)
            if sol >= WHALE_THRESHOLD_SOL:
                buf["whale_buy_vol"] += sol
                buf["whale_buys"] += 1
        else:
            buf["sells"] += 1
            buf["vol_sell"] += sol
            buf["max_sell"] = max(buf["max_sell"], sol)
            if sol >= WHALE_THRESHOLD_SOL:
                buf["whale_sell_vol"] += sol
                buf["whale_sells"] += 1
            # Dev-Tracking
            creator_address = entry["meta"].get("creator_address")
            if creator_address and trader_key and trader_key == creator_address:
                buf["dev_sold_amount"] += sol

        if sol < 0.01: buf["micro_trades"] += 1
        buf["wallets"].add(trader_key)
        buf["v_sol"] = float(data["vSolInBondingCurve"])
        buf["mcap"] = price * 1_000_000_000

    async def check_subscription_watchdog(self, now_ts):
        """Watchdog: Prüfe alle aktiven Coins auf zu lange Inaktivität"""
        inactive_coins = []

        for mint, entry in self.watchlist.items():
            last_trade = self.last_trade_timestamps.get(mint, 0)
            time_since_trade = now_ts - last_trade

            # 10 Minuten ohne Trades = kritisch
            if time_since_trade > 600:  # 10 Minuten
                inactive_coins.append((mint, time_since_trade))

        if inactive_coins:
            print(f"[Watchdog] 🚨 {len(inactive_coins)} Coins ohne Trades seit >10 Min!", flush=True)
            for mint, inactive_time in inactive_coins:
                print(f"[Watchdog]   {mint[:8]}... - {inactive_time:.0f}s ohne Trades", flush=True)
                await self.force_resubscribe(mint)

    async def force_resubscribe(self, mint):
        """Force re-subscribe für einen Coin um WebSocket-Verbindung zu erneuern"""
        if mint not in self.watchlist:
            return

        try:
            # Sende unsubscribe + subscribe über bestehende WebSocket-Verbindung
            if hasattr(self, 'websocket') and self.websocket:
                print(f"[WebSocket] Force Re-Subscribe für {mint[:8]}...", flush=True)

                # Unsubscribe
                unsubscribe_msg = {"method": "unsubscribeTokenTrade", "keys": [mint]}
                await self.websocket.send(json.dumps(unsubscribe_msg))
                await asyncio.sleep(0.1)  # Kurze Pause

                # Subscribe
                subscribe_msg = {"method": "subscribeTokenTrade", "keys": [mint]}
                await self.websocket.send(json.dumps(subscribe_msg))

                # Reset watchdog
                self.subscription_watchdog[mint] = time.time()

                print(f"[WebSocket] ✓ Re-Subscription gesendet für {mint[:8]}...", flush=True)
            else:
                print(f"[WebSocket] ❌ Keine aktive WebSocket-Verbindung für Re-Subscribe {mint[:8]}...", flush=True)

        except Exception as e:
            print(f"[WebSocket] ❌ Fehler bei Re-Subscribe für {mint[:8]}...: {e}", flush=True)

    async def flush_ath_updates(self):
        """Schreibt ATH-Updates in DB (aus pump-metric)"""
        if not self.dirty_aths:
            return

        if not self.pool or not unified_status["db_connected"]:
            return

        updates = []
        for mint in self.dirty_aths:
            new_ath = self.ath_cache.get(mint, 0.0)
            if new_ath > 0:
                updates.append((new_ath, mint))

        if not updates:
            self.dirty_aths.clear()
            return

        try:
            query = """
                UPDATE coin_streams
                SET ath_price_sol = $1, ath_timestamp = NOW()
                WHERE token_address = $2
            """
            async with self.pool.acquire() as conn:
                await conn.executemany(query, updates)

            updated_count = len(updates)
            self.dirty_aths.clear()
            self.last_ath_flush = time.time()
            ath_updates_total.inc(updated_count)

            if updated_count > 10:
                print(f"💾 ATH-Update: {updated_count} Coins in DB gespeichert", flush=True)

        except Exception as e:
            print(f"❌ ATH-Update Fehler: {e}", flush=True)
            db_errors.labels(type="ath_update").inc()

    async def run_subscription_batching_task(self, ws):
        """Batching-Task für WebSocket-Subscriptions (aus pump-metric)"""
        batch_interval = 2.0
        max_batch_size = 50

        while True:
            try:
                await asyncio.sleep(batch_interval)

                if not self.pending_subscriptions:
                    continue

                batch_mints = []
                for mint in list(self.pending_subscriptions):
                    batch_mints.append(mint)
                    if len(batch_mints) >= max_batch_size:
                        break

                for mint in batch_mints:
                    self.pending_subscriptions.remove(mint)

                if batch_mints:
                    try:
                        await ws.send(json.dumps({"method": "subscribeTokenTrade", "keys": batch_mints}))
                        print(f"📡 Batch-Subscription: {len(batch_mints)} Coins abonniert", flush=True)

                        for mint in batch_mints:
                            self.subscribed_mints.add(mint)

                        batches_sent_total.inc()
                        subscriptions_batched_total.inc(len(batch_mints))
                        batch_size_histogram.observe(len(batch_mints))

                    except Exception as e:
                        print(f"❌ Batch-Subscription Fehler: {e}", flush=True)
                        for mint in batch_mints:
                            self.pending_subscriptions.add(mint)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️ Batch-Task Fehler: {e}", flush=True)
                await asyncio.sleep(1.0)

    # === LIFECYCLE-MANAGEMENT ===
    async def switch_phase(self, mint, old_phase, new_phase):
        """Phase wechseln (aus pump-metric)"""
        try:
            print(f"🆙 Phase {old_phase} -> {new_phase} für {mint[:8]}...", flush=True)
            async with self.pool.acquire() as conn:
                await conn.execute("UPDATE coin_streams SET current_phase_id = $1 WHERE token_address = $2", new_phase, mint)
            phase_switches.inc()
        except Exception as e:
            print(f"⚠️ Phase Switch Error: {e}", flush=True)
            db_errors.labels(type="update").inc()

    async def stop_tracking(self, mint, is_graduation=False):
        """Tracking beenden (aus pump-metric)"""
        try:
            if is_graduation:
                print(f"🎉 GRADUATION: {mint[:8]}... geht zu Raydium!", flush=True)
                final_phase = 100
                graduated_flag = True
                coins_graduated.inc()
            else:
                print(f"🏁 FINISHED: {mint[:8]}... Lifecycle beendet", flush=True)
                final_phase = 99
                graduated_flag = False
                coins_finished.inc()

            async with self.pool.acquire() as conn:
                await conn.execute("""
                    UPDATE coin_streams
                    SET is_active = FALSE, current_phase_id = $2, is_graduated = $3
                    WHERE token_address = $1
                """, mint, final_phase, graduated_flag)
        except Exception as e:
            print(f"⚠️ Stop Tracking Error: {e}", flush=True)
            db_errors.labels(type="update").inc()
        finally:
            if mint in self.watchlist: del self.watchlist[mint]
            if mint in self.subscribed_mints: self.subscribed_mints.remove(mint)
            if mint in self.dirty_aths: self.dirty_aths.remove(mint)
            coins_tracked.set(len(self.watchlist))

    async def check_lifecycle_and_flush(self, now_ts):
        """Lifecycle-Prüfung und Metric-Flush (aus pump-metric)"""
        batch_data = []
        phases_in_batch = []
        now_utc = datetime.now(timezone.utc)
        now_berlin = datetime.now(GERMAN_TZ)

        for mint, entry in list(self.watchlist.items()):
            buf = entry["buffer"]
            current_bonding_pct = (buf["v_sol"] / SOL_RESERVES_FULL) * 100

            # Graduation-Check
            if current_bonding_pct >= 99.5:
                await self.stop_tracking(mint, is_graduation=True)
                continue

            # Phase-Upgrade-Check
            created_at = entry["meta"]["created_at"]
            current_pid = entry["meta"]["phase_id"]
            diff = now_utc - created_at
            age_minutes = (diff.total_seconds() / 60) - AGE_CALCULATION_OFFSET_MIN
            if age_minutes < 0: age_minutes = 0

            phase_cfg = self.phases_config.get(current_pid)
            if phase_cfg and age_minutes > phase_cfg["max_age"]:
                next_pid = None
                for pid in self.sorted_phase_ids:
                    if pid > current_pid:
                        next_pid = pid
                        break

                if next_pid is None or next_pid >= 99:
                    await self.stop_tracking(mint, is_graduation=False)
                    continue
                else:
                    print(f"[Phase] {mint[:8]}... - Wechsel von Phase {current_pid} zu {next_pid}", flush=True)
                    await self.switch_phase(mint, current_pid, next_pid)
                    entry["meta"]["phase_id"] = next_pid
                    new_interval = self.phases_config[next_pid]["interval"]
                    entry["interval"] = new_interval
                    entry["next_flush"] = now_ts + new_interval

                    # === PHASE TRANSITION FIX: Sicherstellen dass Subscription erhalten bleibt ===
                    print(f"[WebSocket] {mint[:8]}... - Phase-Wechsel: Subscription-Check", flush=True)
                    # Force re-subscribe nach Phase-Wechsel um sicherzustellen
                    await self.force_resubscribe(mint)

            # === ZOMBIE DETECTION: Metric-Flush mit Stale Data Check ===
            if now_ts >= entry["next_flush"]:
                # Watchdog-Check: Wann kam der letzte Trade?
                last_trade = self.last_trade_timestamps.get(mint, 0)
                time_since_last_trade = now_ts - last_trade
                is_stale = time_since_last_trade > 300  # 5 Minuten ohne Trades = verdächtig

                # Stale Data Detection: Speichere nur wenn sich Daten geändert haben
                should_save = False
                if buf["vol"] > 0:
                    # Prüfe ob sich die Daten seit dem letzten Speichern geändert haben
                    last_saved_signature = self.last_saved_signatures.get(mint)
                    current_signature = f"{buf['close']:.10f}_{buf['vol']:.6f}_{buf['buys'] + buf['sells']}"

                    if last_saved_signature != current_signature:
                        should_save = True
                        self.last_saved_signatures[mint] = current_signature
                    else:
                        # Daten sind identisch zum letzten Mal - ZOMBIE ALERT!
                        warning_count = self.stale_data_warnings.get(mint, 0) + 1
                        self.stale_data_warnings[mint] = warning_count

                        if warning_count <= 3:  # Logge nur die ersten 3 Male
                            print(f"⚠️  [Zombie Alert] {mint[:8]}... - Identische Daten seit {warning_count} Speicherungen!", flush=True)

                        # Watchdog: Re-subscribe wenn zu lange keine Trades
                        if is_stale and warning_count >= 2:
                            print(f"🚨 [Watchdog] {mint[:8]}... - Keine Trades seit {time_since_last_trade:.0f}s - Trigger Re-Subscription!", flush=True)
                            await self.force_resubscribe(mint)

                if should_save:
                    is_koth = buf["mcap"] > 30000

                    # Erweiterte Metriken berechnen
                    advanced_metrics = self.calculate_advanced_metrics(buf)

                    batch_data.append((
                        mint, now_berlin, entry["meta"]["phase_id"],
                        buf["open"], buf["high"], buf["low"], buf["close"], buf["mcap"],
                        current_bonding_pct, buf["v_sol"], is_koth,
                        buf["vol"], buf["vol_buy"], buf["vol_sell"],
                        buf["buys"], buf["sells"], len(buf["wallets"]), buf["micro_trades"],
                        buf["dev_sold_amount"], buf["max_buy"], buf["max_sell"],
                        advanced_metrics["net_volume_sol"], advanced_metrics["volatility_pct"],
                        advanced_metrics["avg_trade_size_sol"], advanced_metrics["whale_buy_volume_sol"],
                        advanced_metrics["whale_sell_volume_sol"], advanced_metrics["num_whale_buys"],
                        advanced_metrics["num_whale_sells"], advanced_metrics["buy_pressure_ratio"],
                        advanced_metrics["unique_signer_ratio"]
                    ))
                    phases_in_batch.append(entry["meta"]["phase_id"])

                    print(f"[Metrics] {mint[:8]}... - Speichere {buf['buys'] + buf['sells']} Trades, Vol: {buf['vol']:.1f} SOL", flush=True)

                    # Reset warning counter bei erfolgreichem Save
                    if mint in self.stale_data_warnings:
                        del self.stale_data_warnings[mint]

                # Buffer immer zurücksetzen (auch bei no-save)
                entry["buffer"] = self.get_empty_buffer()
                entry["next_flush"] = now_ts + entry["interval"]

        # Batch in DB speichern
        if batch_data and unified_status["db_connected"]:
            sql = """
                INSERT INTO coin_metrics (
                    mint, timestamp, phase_id_at_time, price_open, price_high, price_low, price_close,
                    market_cap_close, bonding_curve_pct, virtual_sol_reserves, is_koth, volume_sol,
                    buy_volume_sol, sell_volume_sol, num_buys, num_sells, unique_wallets, num_micro_trades,
                    dev_sold_amount, max_single_buy_sol, max_single_sell_sol, net_volume_sol,
                    volatility_pct, avg_trade_size_sol, whale_buy_volume_sol, whale_sell_volume_sol,
                    num_whale_buys, num_whale_sells, buy_pressure_ratio, unique_signer_ratio
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $30)
            """
            try:
                with flush_duration.time():
                    async with self.pool.acquire() as conn:
                        await conn.executemany(sql, batch_data)

                metrics_saved.inc(len(batch_data))
                unified_status["total_metrics_saved"] += len(batch_data)

                # Logging wie in pump-metric
                counts = Counter(phases_in_batch)
                details = ", ".join([f"Phase {k}: {v}" for k,v in sorted(counts.items())])
                print(f"💾 Saved metrics for {len(batch_data)} coins ({details})", flush=True)

            except Exception as e:
                print(f"⚠️ SQL Error: {e}", flush=True)
                unified_status["db_connected"] = False
                db_connected.set(0)
                db_errors.labels(type="insert").inc()

    def calculate_advanced_metrics(self, buf):
        """Erweiterte Metriken berechnen (aus pump-metric)"""
        net_volume = buf["vol_buy"] - buf["vol_sell"]

        if buf["open"] and buf["open"] > 0:
            volatility = ((buf["high"] - buf["low"]) / buf["open"]) * 100
        else:
            volatility = 0.0

        total_trades = buf["buys"] + buf["sells"]
        avg_trade_size = buf["vol"] / total_trades if total_trades > 0 else 0.0

        total_volume = buf["vol_buy"] + buf["vol_sell"]
        buy_pressure_ratio = buf["vol_buy"] / total_volume if total_volume > 0 else 0.0

        unique_signer_ratio = len(buf["wallets"]) / total_trades if total_trades > 0 else 0.0

        return {
            "net_volume_sol": net_volume,
            "volatility_pct": volatility,
            "avg_trade_size_sol": avg_trade_size,
            "whale_buy_volume_sol": buf["whale_buy_vol"],
            "whale_sell_volume_sol": buf["whale_sell_vol"],
            "num_whale_buys": buf["whale_buys"],
            "num_whale_sells": buf["whale_sells"],
            "buy_pressure_ratio": buy_pressure_ratio,
            "unique_signer_ratio": unique_signer_ratio
        }

    # === HAUPT-RUN-METHODE ===
    async def run(self):
        """Hauptmethode des vereinten Services (FastAPI-Version)"""
        await self.init_db_connection()

        reconnect_count = 0

        while True:
            try:
                print(f"🔌 Verbinde zu WebSocket (Vereinter Service)... (Versuch #{reconnect_count + 1})", flush=True)

                # SSL-Kontext erstellen, der Zertifikatsfehler ignoriert
                import ssl
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

                async with websockets.connect(
                    WS_URI,
                    ping_interval=WS_PING_INTERVAL,
                    ping_timeout=WS_PING_TIMEOUT,
                    close_timeout=10,
                    max_size=2**23,
                    compression=None,
                    ssl=ssl_context  # Benutzerdefinierter SSL-Kontext
                ) as ws:

                    # WebSocket-Referenz für Re-Subscribe setzen
                    self.websocket = ws

                    unified_status["ws_connected"] = True
                    unified_status["connection_start"] = time.time()
                    unified_status["last_error"] = None
                    ws_connected.set(1)
                    reconnect_count = 0
                    unified_status["reconnect_count"] = reconnect_count

                    print("✅ WebSocket verbunden! Vereinter Service läuft...", flush=True)

                    # subscribeNewToken für Discovery
                    await ws.send(json.dumps({"method": "subscribeNewToken"}))
                    print("📡 subscribeNewToken aktiv - warte auf neue Coins...", flush=True)

                    # BEREITS AKTUELLE SUBSCRIPTIONS WIEDERHERSTELLEN
                    if self.subscribed_mints:
                        print(f"🔄 Stelle {len(self.subscribed_mints)} bestehende Subscriptions wieder her...", flush=True)
                        try:
                            await ws.send(json.dumps({"method": "subscribeTokenTrade", "keys": list(self.subscribed_mints)}))
                            print(f"✅ {len(self.subscribed_mints)} aktive Coin-Subscriptions wiederhergestellt", flush=True)
                            # Metrik aktualisieren
                            subscriptions_batched_total.inc(len(self.subscribed_mints))
                        except Exception as e:
                            print(f"⚠️ Fehler beim Wiederherstellen der Subscriptions: {e}", flush=True)
                            # Bei Fehler alle Subscriptions als pending markieren
                            self.pending_subscriptions.update(self.subscribed_mints)

                    # AKTIVE STREAMS AUS DB LADEN FÜR WATCHLIST-SYNC
                    try:
                        print("🔍 Lade aktuelle aktive Streams aus DB für Synchronisation...", flush=True)
                        db_streams = await self.get_active_streams()
                        current_set = set(db_streams.keys())

                        # Neue aktive Coins hinzufügen (die noch nicht subscribed sind)
                        to_add = current_set - self.subscribed_mints
                        if to_add:
                            print(f"➕ Füge {len(to_add)} neue aktive Coins zur Subscription hinzu...", flush=True)
                            for mint in to_add:
                                self.pending_subscriptions.add(mint)

                        print(f"📊 DB-Sync: {len(current_set)} aktive Streams, {len(self.subscribed_mints)} subscribed, {len(self.pending_subscriptions)} pending", flush=True)

                    except Exception as e:
                        print(f"⚠️ Fehler beim Laden aktiver Streams: {e}", flush=True)

                    # Batching-Task starten
                    self.batching_task = asyncio.create_task(self.run_subscription_batching_task(ws))

                    last_refresh = 0
                    last_message_time = time.time()

                    while True:
                        now_ts = time.time()

                        # Cache-Management (alle 10 Sekunden)
                        if now_ts - last_refresh > DB_REFRESH_INTERVAL:
                            try:
                                # Prüfe ob DB-Reconnect erzwungen werden soll
                                global _force_db_reconnect
                                if _force_db_reconnect:
                                    print("🔄 Führe erzwungenen DB-Reconnect durch...")
                                    await self.force_db_reconnect()
                                    _force_db_reconnect = False

                                activated, expired = await self.check_cache_activation()

                                # Aktive Streams neu laden für Watchlist-Management
                                db_streams = await self.get_active_streams()
                                current_set = set(db_streams.keys())
                                to_remove = self.subscribed_mints - current_set

                                # Entferne beendete Coins
                                for mint in to_remove:
                                    if mint in self.watchlist:
                                        del self.watchlist[mint]
                                    self.subscribed_mints.remove(mint)

                                # Neue aktive Coins hinzufügen
                                to_add = current_set - self.subscribed_mints
                                for mint in to_add:
                                    if mint in db_streams:
                                        p_id = db_streams[mint]["phase_id"]
                                        if p_id not in self.phases_config:
                                            p_id = self.sorted_phase_ids[0] if self.sorted_phase_ids else 1

                                        interval = self.phases_config[p_id]["interval"]
                                        self.watchlist[mint] = {
                                            "meta": db_streams[mint],
                                            "buffer": self.get_empty_buffer(),
                                            "next_flush": now_ts + interval,
                                            "interval": interval
                                        }
                                        self.subscribed_mints.add(mint)

                                unified_status["db_connected"] = True
                                db_connected.set(1)
                                coins_tracked.set(len(self.watchlist))
                                last_refresh = now_ts

                            except Exception as e:
                                print(f"⚠️ DB Sync Error: {e}", flush=True)
                                unified_status["db_connected"] = False
                                db_connected.set(0)

                        # WebSocket-Nachricht empfangen
                        try:
                            msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                            last_message_time = time.time()
                            unified_status["last_message_time"] = last_message_time

                            data = json.loads(msg)

                            if data.get("txType") == "create" and "mint" in data:
                                # NEUER COIN - Discovery-Logik
                                await self.process_new_coin(data)

                            elif "txType" in data and data["txType"] in ["buy", "sell"]:
                                # TRADE - Metric-Logik
                                mint = data.get("mint")
                                if mint:
                                    trades_received.inc()

                                    if mint in self.watchlist:
                                        # Coin ist aktiv - sofort verarbeiten
                                        self.process_trade(data)
                                        trades_processed.inc()
                                        unified_status["total_trades"] += 1
                                        last_trade_timestamp.set(time.time())
                                    elif mint in self.coin_cache.cache:
                                        # Coin ist im Cache - Trade sammeln
                                        self.coin_cache.add_trade(mint, data)

                        except asyncio.TimeoutError:
                            # Prüfe nur alle 30 Sekunden auf Timeout (nicht bei jedem recv timeout)
                            if now_ts - last_message_time > WS_CONNECTION_TIMEOUT and now_ts % 30 < 1:
                                print(f"⚠️ Keine Nachrichten seit {WS_CONNECTION_TIMEOUT}s - Reconnect", flush=True)
                                raise websockets.exceptions.ConnectionClosed(1006, "Timeout")

                        except websockets.exceptions.ConnectionClosed as e:
                            print(f"🔌 WebSocket Verbindung geschlossen: {e}", flush=True)
                            unified_status["ws_connected"] = False
                            unified_status["last_error"] = f"ws_closed: {str(e)[:100]}"
                            ws_connected.set(0)
                            # Batching-Task ordnungsgemäß beenden
                            if self.batching_task and not self.batching_task.done():
                                print("🛑 Beende Batching-Task...", flush=True)
                                self.batching_task.cancel()
                                try:
                                    await self.batching_task
                                except asyncio.CancelledError:
                                    pass
                            break

                        except json.JSONDecodeError as e:
                            print(f"⚠️ JSON Fehler: {e}", flush=True)
                            continue

                        except Exception as e:
                            print(f"⚠️ WS Receive Error: {e}", flush=True)
                            unified_status["last_error"] = f"ws_error: {str(e)[:100]}"
                            break

                        # Buffer-Cleanup
                        if now_ts - self.last_buffer_cleanup > 10:
                            removed = self.cleanup_old_trades_from_buffer(now_ts)
                            if removed > 0:
                                print(f"🧹 Buffer-Cleanup: {removed} alte Trades entfernt", flush=True)
                            self.last_buffer_cleanup = now_ts

                        # Discovery-Buffer flushen (regelmäßig)
                        await self.flush_discovery_buffer()

                        # Lifecycle-Checks und Metric-Flush
                        await self.check_lifecycle_and_flush(now_ts)

                        # === ZOMBIE WATCHDOG: Regelmäßige Subscription-Checks ===
                        if int(now_ts) % 60 == 0:  # Alle 60 Sekunden
                            await self.check_subscription_watchdog(now_ts)

                        # ATH-Updates
                        if now_ts - self.last_ath_flush > ATH_FLUSH_INTERVAL:
                            await self.flush_ath_updates()

                        # Batching-Metriken
                        pending_subscriptions.set(len(self.pending_subscriptions))

            except websockets.exceptions.WebSocketException as e:
                unified_status["ws_connected"] = False
                unified_status["last_error"] = f"ws_exception: {str(e)[:100]}"
                ws_connected.set(0)
                ws_reconnects.inc()
                # WebSocket-Referenz zurücksetzen
                self.websocket = None
                print(f"❌ WebSocket Exception: {e}", flush=True)
                reconnect_count += 1
                unified_status["reconnect_count"] = reconnect_count

            except Exception as e:
                unified_status["ws_connected"] = False
                unified_status["last_error"] = f"unexpected: {str(e)[:100]}"
                ws_connected.set(0)
                ws_reconnects.inc()
                # WebSocket-Referenz zurücksetzen
                self.websocket = None
                print(f"❌ Unerwarteter Fehler: {e}", flush=True)
                reconnect_count += 1
                unified_status["reconnect_count"] = reconnect_count

            # Reconnect-Delay
            delay = min(WS_RETRY_DELAY * (1 + reconnect_count * 0.5), WS_MAX_RETRY_DELAY)
            print(f"⏳ Reconnect in {delay:.1f}s...", flush=True)
            await asyncio.sleep(delay)

            # DB-Reconnect falls nötig
            if not unified_status["db_connected"]:
                print("🔄 DB auch getrennt, versuche Reconnect...", flush=True)
                await self.init_db_connection()

    def cleanup_old_trades_from_buffer(self, now_ts):
        """Buffer-Cleanup für aktive Coins (aus pump-metric)"""
        cutoff_time = now_ts - TRADE_BUFFER_SECONDS
        total_removed = 0

        for mint in list(self.trade_buffer.keys()):
            original_len = len(self.trade_buffer[mint])
            self.trade_buffer[mint] = [
                (ts, data) for ts, data in self.trade_buffer[mint]
                if ts > cutoff_time
            ]
            removed = original_len - len(self.trade_buffer[mint])
            total_removed += removed

            if not self.trade_buffer[mint]:
                del self.trade_buffer[mint]

        buffer_size.set(sum(len(trades) for trades in self.trade_buffer.values()))
        return total_removed

# === FASTAPI STARTUP ===
if __name__ == "__main__":
    # Konfiguration laden
    load_config_from_file()

    # n8n beim Start testen
    print("🔍 Teste n8n Verfügbarkeit...", flush=True)
    asyncio.run(test_n8n_availability())

    print("=" * 60)
    print("🚀 UNIFIED PUMP SERVICE - Discovery + Metrics (FastAPI)")
    print("=" * 60)
    print("🔧 Konfiguration:")
    print(f"  - DB_DSN: {DB_DSN[:50]}..." if DB_DSN else "  - DB_DSN: NICHT GESETZT")
    print(f"  - WS_URI: {WS_URI}")
    print(f"  - N8N_WEBHOOK_URL: {N8N_WEBHOOK_URL if N8N_WEBHOOK_URL else 'NICHT GESETZT'}")
    print(f"  - COIN_CACHE_SECONDS: {COIN_CACHE_SECONDS}s (120s Cache)")
    print(f"  - DB_REFRESH_INTERVAL: {DB_REFRESH_INTERVAL}s")
    print(f"  - BATCH_SIZE: {BATCH_SIZE}")
    print(f"  - SOL_RESERVES_FULL: {SOL_RESERVES_FULL}")
    print(f"  - WHALE_THRESHOLD_SOL: {WHALE_THRESHOLD_SOL}")
    print("=" * 60)
    print("📖 API-Dokumentation verfügbar unter: http://localhost:8000/docs")
    print("🔍 Alternative Docs unter: http://localhost:8000/redoc")
    print("=" * 60)

    # Starte WebSocket-Service
    print("🚀 Starte Unified Pump Service (WebSocket)...", flush=True)

    # Erstelle Service-Instanz
    service = UnifiedService()

    # Starte WebSocket-Service in der Haupt-Event-Loop
    print("🔌 Starte WebSocket-Service...", flush=True)
    asyncio.run(service.run())
