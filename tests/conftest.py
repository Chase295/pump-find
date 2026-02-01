"""
Pytest Fixtures für Pump Finder Tests
Enthält alle gemeinsamen Fixtures für Unit, Integration und Stress Tests
"""

import pytest
import asyncio
import time
import json
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

# === SAMPLE DATA FIXTURES ===

@pytest.fixture
def sample_coin_data() -> Dict[str, Any]:
    """Sample Coin-Daten für Discovery Tests"""
    return {
        "mint": "TestCoin123456789012345678901234567890123",
        "name": "Good Coin",
        "symbol": "GOOD",
        "marketCapSol": 1000.0,
        "vTokensInBondingCurve": 1000000000,
        "vSolInBondingCurve": 10.0,
        "bondingCurveKey": "BondingCurveKey123456789012345678901234567890",
        "traderPublicKey": "CreatorKey123456789012345678901234567890123",
        "signature": "TxSignature123456789012345678901234567890123",
        "pool": None,
        "uri": "https://example.com/metadata.json",
        "image_uri": "https://example.com/image.png"
    }


@pytest.fixture
def sample_bad_name_coin() -> Dict[str, Any]:
    """Coin mit Bad Name für Filter Tests"""
    return {
        "mint": "BadCoin12345678901234567890123456789012345",
        "name": "Test Scam Bot",  # Enthält "test", "scam", "bot"
        "symbol": "SCAM",
        "marketCapSol": 500.0,
        "vTokensInBondingCurve": 500000000,
        "vSolInBondingCurve": 5.0,
        "bondingCurveKey": "BondingCurveKeyBad12345678901234567890123",
        "traderPublicKey": "CreatorKeyBad12345678901234567890123456789",
        "signature": "TxSignatureBad1234567890123456789012345678"
    }


@pytest.fixture
def sample_trade_data() -> Dict[str, Any]:
    """Sample Trade-Daten für Processing Tests"""
    return {
        "mint": "TestCoin123456789012345678901234567890123",
        "txType": "buy",
        "solAmount": 1.5,
        "tokenAmount": 150000,
        "vSolInBondingCurve": 15.0,
        "vTokensInBondingCurve": 900000000,
        "traderPublicKey": "TraderKey123456789012345678901234567890123",
        "signature": "TradeSig12345678901234567890123456789012345",
        "timestamp": int(time.time() * 1000)  # Millisekunden
    }


@pytest.fixture
def sample_sell_trade() -> Dict[str, Any]:
    """Sample Sell-Trade"""
    return {
        "mint": "TestCoin123456789012345678901234567890123",
        "txType": "sell",
        "solAmount": 0.8,
        "tokenAmount": 80000,
        "vSolInBondingCurve": 14.2,
        "vTokensInBondingCurve": 920000000,
        "traderPublicKey": "SellerKey12345678901234567890123456789012",
        "signature": "SellSig1234567890123456789012345678901234",
        "timestamp": int(time.time() * 1000)
    }


@pytest.fixture
def sample_whale_trade() -> Dict[str, Any]:
    """Whale Trade (>= 1.0 SOL)"""
    return {
        "mint": "TestCoin123456789012345678901234567890123",
        "txType": "buy",
        "solAmount": 5.0,  # Whale threshold überschritten
        "tokenAmount": 500000,
        "vSolInBondingCurve": 20.0,
        "vTokensInBondingCurve": 800000000,
        "traderPublicKey": "WhaleKey1234567890123456789012345678901234",
        "signature": "WhaleSig123456789012345678901234567890123",
        "timestamp": int(time.time() * 1000)
    }


@pytest.fixture
def sample_micro_trade() -> Dict[str, Any]:
    """Micro Trade (< 0.01 SOL)"""
    return {
        "mint": "TestCoin123456789012345678901234567890123",
        "txType": "buy",
        "solAmount": 0.005,  # Unter micro threshold
        "tokenAmount": 500,
        "vSolInBondingCurve": 10.005,
        "vTokensInBondingCurve": 999999500,
        "traderPublicKey": "MicroKey1234567890123456789012345678901234",
        "signature": "MicroSig123456789012345678901234567890123",
        "timestamp": int(time.time() * 1000)
    }


@pytest.fixture
def sample_stream_data() -> Dict[str, Any]:
    """Sample Stream-Daten aus DB"""
    return {
        "token_address": "TestCoin123456789012345678901234567890123",
        "phase_id": 1,
        "interval_seconds": 5,
        "is_active": True,
        "created_at": "2024-01-01T00:00:00+00:00",
        "started_at": "2024-01-01T00:01:00+00:00",
        "token_created_at": "2024-01-01T00:00:00+00:00",
        "creator_address": "CreatorKey123456789012345678901234567890123",
        "ath_price_sol": 0.00001
    }


@pytest.fixture
def sample_health_response() -> Dict[str, Any]:
    """Sample Health Response"""
    return {
        "status": "healthy",
        "ws_connected": True,
        "db_connected": True,
        "uptime_seconds": 3600,
        "last_message_ago": 5,
        "reconnect_count": 0,
        "last_error": None,
        "cache_stats": {
            "total_coins": 10,
            "activated_coins": 5,
            "expired_coins": 5,
            "oldest_age_seconds": 100,
            "newest_age_seconds": 10
        },
        "tracking_stats": {
            "active_coins": 50,
            "total_trades": 1000,
            "total_metrics_saved": 500
        },
        "discovery_stats": {
            "total_coins_discovered": 200,
            "n8n_available": True,
            "n8n_buffer_size": 3
        }
    }


@pytest.fixture
def sample_config_response() -> Dict[str, Any]:
    """Sample Config Response"""
    return {
        "n8n_webhook_url": "http://localhost:5678/webhook/test",
        "n8n_webhook_method": "POST",
        "db_dsn": "postgresql://user:***@host:5432/db",
        "coin_cache_seconds": 120,
        "db_refresh_interval": 10,
        "batch_size": 10,
        "batch_timeout": 30,
        "bad_names_pattern": "test|bot|rug|scam",
        "spam_burst_window": 30,
        "sol_reserves_full": 85.0,
        "whale_threshold_sol": 1.0,
        "age_calculation_offset_min": 60,
        "trade_buffer_seconds": 180,
        "ath_flush_interval": 5
    }


# === MOCK FIXTURES ===

@pytest.fixture
def mock_db_pool():
    """Mock asyncpg Connection Pool"""
    pool = AsyncMock()

    # Konfiguriere fetch Methoden
    pool.fetch = AsyncMock(return_value=[])
    pool.fetchrow = AsyncMock(return_value=None)
    pool.fetchval = AsyncMock(return_value=None)
    pool.execute = AsyncMock(return_value="INSERT 0 1")

    # Konfiguriere Connection acquire
    conn = AsyncMock()
    conn.fetch = pool.fetch
    conn.fetchrow = pool.fetchrow
    conn.fetchval = pool.fetchval
    conn.execute = pool.execute

    # Context manager für acquire
    pool.acquire = MagicMock()
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

    # Close method
    pool.close = AsyncMock()

    return pool


@pytest.fixture
def mock_websocket():
    """Mock WebSocket Connection"""
    ws = AsyncMock()
    ws.send = AsyncMock()
    ws.recv = AsyncMock(return_value='{}')
    ws.close = AsyncMock()
    ws.closed = False
    ws.ping = AsyncMock()
    ws.pong = AsyncMock()

    return ws


@pytest.fixture
def mock_http_client():
    """Mock HTTP Client (httpx)"""
    client = AsyncMock()

    # Success Response
    response = MagicMock()
    response.status_code = 200
    response.json = MagicMock(return_value={"status": "ok"})
    response.text = "OK"

    client.post = AsyncMock(return_value=response)
    client.get = AsyncMock(return_value=response)

    return client


# === COIN CACHE FIXTURE ===

@pytest.fixture
def coin_cache():
    """Erstellt CoinCache Instanz für Tests"""
    # Import hier um zirkuläre Imports zu vermeiden
    import sys
    sys.path.insert(0, '/Users/moritzhaslbeck/.claude-worktrees/pump-find/gallant-franklin')

    # Mock die Prometheus Metriken
    with patch('unified_service.cache_size') as mock_cache_size, \
         patch('unified_service.cache_activations') as mock_activations, \
         patch('unified_service.cache_expirations') as mock_expirations:

        mock_cache_size.set = MagicMock()
        mock_activations.inc = MagicMock()
        mock_expirations.inc = MagicMock()

        from unified_service import CoinCache
        cache = CoinCache(cache_seconds=120)
        cache._mock_cache_size = mock_cache_size
        cache._mock_activations = mock_activations
        cache._mock_expirations = mock_expirations

        yield cache


@pytest.fixture
def coin_filter():
    """Erstellt CoinFilter Instanz für Tests"""
    import sys
    sys.path.insert(0, '/Users/moritzhaslbeck/.claude-worktrees/pump-find/gallant-franklin')

    with patch('unified_service.coins_filtered') as mock_filtered, \
         patch('unified_service.BAD_NAMES') as mock_bad_names:

        import re
        mock_bad_names.search = re.compile(r'(test|bot|rug|scam|cant|honey|faucet)', re.IGNORECASE).search
        mock_filtered.labels = MagicMock(return_value=MagicMock(inc=MagicMock()))

        from unified_service import CoinFilter
        filter_instance = CoinFilter(spam_burst_window=30)
        filter_instance._mock_filtered = mock_filtered

        yield filter_instance


# === UNIFIED SERVICE FIXTURE ===

@pytest.fixture
def unified_service_mocked(mock_db_pool, mock_websocket):
    """Erstellt UnifiedService mit gemockten Dependencies"""
    import sys
    sys.path.insert(0, '/Users/moritzhaslbeck/.claude-worktrees/pump-find/gallant-franklin')

    with patch('unified_service.asyncpg.create_pool', return_value=mock_db_pool), \
         patch('unified_service.websockets.connect', return_value=mock_websocket), \
         patch('unified_service.cache_size'), \
         patch('unified_service.cache_activations'), \
         patch('unified_service.cache_expirations'), \
         patch('unified_service.coins_tracked'), \
         patch('unified_service.ws_connected'), \
         patch('unified_service.db_connected'), \
         patch('unified_service.uptime_seconds'):

        from unified_service import UnifiedService
        service = UnifiedService()
        service.pool = mock_db_pool
        service._mock_ws = mock_websocket

        yield service


# === HELPER FIXTURES ===

@pytest.fixture
def time_freeze():
    """Fixture zum Einfrieren der Zeit"""
    frozen_time = time.time()

    class TimeFreezer:
        def __init__(self):
            self.current_time = frozen_time

        def advance(self, seconds: float):
            self.current_time += seconds
            return self.current_time

        def get_time(self):
            return self.current_time

    return TimeFreezer()


@pytest.fixture
def multiple_coins(sample_coin_data) -> List[Dict[str, Any]]:
    """Generiert mehrere Test-Coins"""
    coins = []
    for i in range(10):
        coin = sample_coin_data.copy()
        coin["mint"] = f"Coin{i:04d}1234567890123456789012345678901234567"
        coin["name"] = f"Test Coin {i}"
        coin["symbol"] = f"TC{i}"
        coins.append(coin)
    return coins


@pytest.fixture
def multiple_trades(sample_trade_data) -> List[Dict[str, Any]]:
    """Generiert mehrere Test-Trades"""
    trades = []
    base_time = int(time.time() * 1000)
    for i in range(20):
        trade = sample_trade_data.copy()
        trade["signature"] = f"Trade{i:04d}123456789012345678901234567890123"
        trade["solAmount"] = 0.1 * (i + 1)
        trade["timestamp"] = base_time + (i * 1000)  # 1 Sekunde Abstand
        trade["txType"] = "buy" if i % 2 == 0 else "sell"
        trades.append(trade)
    return trades


# === ASYNC HELPERS ===

@pytest.fixture
def event_loop():
    """Erstellt neuen Event Loop für jeden Test"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# === PROMETHEUS MOCK FIXTURE ===

@pytest.fixture
def mock_prometheus_metrics():
    """Mock alle Prometheus Metriken"""
    with patch('unified_service.coins_received') as coins_received, \
         patch('unified_service.coins_filtered') as coins_filtered, \
         patch('unified_service.coins_sent_n8n') as coins_sent_n8n, \
         patch('unified_service.trades_received') as trades_received, \
         patch('unified_service.trades_processed') as trades_processed, \
         patch('unified_service.metrics_saved') as metrics_saved, \
         patch('unified_service.cache_size') as cache_size, \
         patch('unified_service.cache_activations') as cache_activations, \
         patch('unified_service.cache_expirations') as cache_expirations, \
         patch('unified_service.coins_tracked') as coins_tracked, \
         patch('unified_service.ws_connected') as ws_connected, \
         patch('unified_service.db_connected') as db_connected:

        # Konfiguriere alle Mocks
        for mock in [coins_received, coins_sent_n8n, trades_received,
                     trades_processed, metrics_saved, cache_activations,
                     cache_expirations]:
            mock.inc = MagicMock()

        for mock in [cache_size, coins_tracked, ws_connected, db_connected]:
            mock.set = MagicMock()

        coins_filtered.labels = MagicMock(return_value=MagicMock(inc=MagicMock()))

        yield {
            'coins_received': coins_received,
            'coins_filtered': coins_filtered,
            'coins_sent_n8n': coins_sent_n8n,
            'trades_received': trades_received,
            'trades_processed': trades_processed,
            'metrics_saved': metrics_saved,
            'cache_size': cache_size,
            'cache_activations': cache_activations,
            'cache_expirations': cache_expirations,
            'coins_tracked': coins_tracked,
            'ws_connected': ws_connected,
            'db_connected': db_connected
        }
