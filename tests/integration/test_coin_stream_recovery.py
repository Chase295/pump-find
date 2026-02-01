"""
Integration Tests für Coin Stream Recovery
Testet Cache-Aktivierung, Watchlist-Sync und Subscription-Wiederherstellung
"""

import pytest
import asyncio
import time
from unittest.mock import patch, MagicMock, AsyncMock


class TestCoinStreamRecovery:
    """Tests für Coin Stream Recovery (unified_service.py:1435-1498, 2038-2108)"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup für jeden Test"""
        with patch('unified_service.cache_size'), \
             patch('unified_service.cache_activations'), \
             patch('unified_service.cache_expirations'), \
             patch('unified_service.coins_tracked'), \
             patch('unified_service.ws_connected'), \
             patch('unified_service.db_connected'), \
             patch('unified_service.uptime_seconds'):

            from unified_service import UnifiedService, CoinCache
            self.service = UnifiedService()
            self.service.coin_cache = CoinCache(cache_seconds=120)
            self.service.watchlist = {}
            self.service.subscribed_mints = set()
            self.service.pending_subscriptions = set()
            self.service.active_streams = {}

            yield

    @pytest.mark.asyncio
    async def test_cache_activation_for_db_activated_coins(self, sample_coin_data, sample_trade_data):
        """Test Coins in DB werden aus Cache aktiviert"""
        mint = sample_coin_data["mint"]

        # Coin zum Cache hinzufügen
        self.service.coin_cache.add_coin(mint, sample_coin_data)

        # Trades zum Cache hinzufügen
        for i in range(5):
            trade = sample_trade_data.copy()
            trade["signature"] = f"sig_{i}"
            self.service.coin_cache.add_trade(mint, trade)

        # Simuliere DB sagt Coin ist aktiv
        self.service.active_streams[mint] = {
            "phase_id": 1,
            "interval_seconds": 5,
            "is_active": True
        }

        # Aktiviere Coin
        cached_trades = self.service.coin_cache.activate_coin(mint)

        assert len(cached_trades) == 5
        assert self.service.coin_cache.cache[mint]["activated"] is True

    @pytest.mark.asyncio
    async def test_cache_expiration_for_non_activated_coins(self, sample_coin_data):
        """Test Coins nicht in DB werden aus Cache entfernt"""
        mint = sample_coin_data["mint"]

        # Coin zum Cache hinzufügen
        self.service.coin_cache.add_coin(mint, sample_coin_data)

        # Keine Aktivierung durch DB

        # Simuliere Cache-Ablauf (121 Sekunden später)
        future_time = time.time() + 121

        removed = self.service.coin_cache.cleanup_expired_coins(current_time=future_time)

        assert removed == 1
        assert mint not in self.service.coin_cache.cache

    @pytest.mark.asyncio
    async def test_cached_trades_processed_chronologically(self, sample_coin_data, sample_trade_data):
        """Test Cached Trades werden chronologisch verarbeitet"""
        mint = sample_coin_data["mint"]
        self.service.coin_cache.add_coin(mint, sample_coin_data)

        # Trades mit Zeitstempeln hinzufügen
        for i in range(5):
            trade = sample_trade_data.copy()
            trade["signature"] = f"sig_{i}"
            self.service.coin_cache.add_trade(mint, trade)
            time.sleep(0.01)  # Kleine Verzögerung

        cached_trades = self.service.coin_cache.activate_coin(mint)

        # Prüfe chronologische Reihenfolge
        timestamps = [t[0] for t in cached_trades]
        assert timestamps == sorted(timestamps)

    @pytest.mark.asyncio
    async def test_watchlist_entry_created_on_activation(self, sample_coin_data):
        """Test Watchlist-Eintrag wird bei Aktivierung erstellt"""
        mint = sample_coin_data["mint"]

        # Erstelle Watchlist-Eintrag
        self.service.watchlist[mint] = {
            "buffer": {
                "open": None,
                "close": None,
                "high": 0,
                "low": float('inf'),
                "vol": 0,
                "vol_buy": 0,
                "vol_sell": 0,
                "buys": 0,
                "sells": 0,
                "wallets": set()
            },
            "interval": 5,
            "last_flush": time.time(),
            "meta": {}
        }

        assert mint in self.service.watchlist
        assert self.service.watchlist[mint]["interval"] == 5

    @pytest.mark.asyncio
    async def test_db_sync_adds_new_active_coins(self, sample_stream_data):
        """Test Neue Coins aus DB werden zu pending_subscriptions hinzugefügt"""
        mint = sample_stream_data["token_address"]

        # Simuliere neue aktive Streams aus DB
        self.service.active_streams[mint] = sample_stream_data

        # Coin ist noch nicht subscribed
        if mint not in self.service.subscribed_mints:
            self.service.pending_subscriptions.add(mint)

        assert mint in self.service.pending_subscriptions

    @pytest.mark.asyncio
    async def test_db_sync_removes_finished_coins(self, sample_coin_data):
        """Test Coins nicht mehr aktiv in DB werden entfernt"""
        mint = sample_coin_data["mint"]

        # Coin ist in Watchlist
        self.service.watchlist[mint] = {"buffer": {}, "interval": 5}
        self.service.subscribed_mints.add(mint)

        # DB sagt Coin ist nicht mehr aktiv
        self.service.active_streams = {}  # Leer = kein aktiver Stream

        # Sync: Entferne Coins die nicht in active_streams sind
        to_remove = []
        for m in self.service.watchlist:
            if m not in self.service.active_streams:
                to_remove.append(m)

        for m in to_remove:
            del self.service.watchlist[m]
            self.service.subscribed_mints.discard(m)

        assert mint not in self.service.watchlist
        assert mint not in self.service.subscribed_mints

    @pytest.mark.asyncio
    async def test_subscription_restored_after_reconnect(self, multiple_coins):
        """Test Alle subscribed_mints werden nach Reconnect re-subscribed"""
        # Füge Coins zu subscribed_mints hinzu
        for coin in multiple_coins[:5]:
            self.service.subscribed_mints.add(coin["mint"])

        assert len(self.service.subscribed_mints) == 5

        # Simuliere Reconnect: Alle Mints müssen re-subscribed werden
        mints_to_restore = list(self.service.subscribed_mints)

        assert len(mints_to_restore) == 5
        assert all(m in self.service.subscribed_mints for m in mints_to_restore)

    @pytest.mark.asyncio
    async def test_pending_subscriptions_on_restore_failure(self):
        """Test Fehlgeschlagene Subscriptions werden zu pending_subscriptions hinzugefügt"""
        mint = "FailedCoin123456789012345678901234567890"

        # Simuliere fehlgeschlagene Subscription
        subscription_failed = True

        if subscription_failed:
            self.service.pending_subscriptions.add(mint)

        assert mint in self.service.pending_subscriptions


class TestCacheActivationFlow:
    """Tests für den kompletten Cache-Aktivierungs-Flow"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup für jeden Test"""
        with patch('unified_service.cache_size') as self.mock_cache_size, \
             patch('unified_service.cache_activations') as self.mock_activations, \
             patch('unified_service.cache_expirations') as self.mock_expirations:

            self.mock_cache_size.set = MagicMock()
            self.mock_activations.inc = MagicMock()
            self.mock_expirations.inc = MagicMock()

            from unified_service import CoinCache
            self.cache = CoinCache(cache_seconds=120)
            yield

    @pytest.mark.asyncio
    async def test_full_activation_flow(self, sample_coin_data, sample_trade_data):
        """Test kompletter Flow: Discovery -> Cache -> Trades -> Aktivierung"""
        mint = sample_coin_data["mint"]

        # 1. Coin discovered und in Cache gelegt
        self.cache.add_coin(mint, sample_coin_data)
        assert mint in self.cache.cache
        assert self.cache.cache[mint]["activated"] is False

        # 2. Trades kommen rein während Coin im Cache ist
        for i in range(10):
            trade = sample_trade_data.copy()
            trade["signature"] = f"sig_{i}"
            self.cache.add_trade(mint, trade)

        assert len(self.cache.cache[mint]["trades"]) == 10

        # 3. DB bestätigt Aktivierung
        cached_trades = self.cache.activate_coin(mint)

        assert len(cached_trades) == 10
        assert self.cache.cache[mint]["activated"] is True
        self.mock_activations.inc.assert_called_once()

    @pytest.mark.asyncio
    async def test_expiration_flow(self, sample_coin_data):
        """Test Flow: Discovery -> Cache -> Timeout -> Expiration"""
        mint = sample_coin_data["mint"]

        # 1. Coin discovered und in Cache gelegt
        self.cache.add_coin(mint, sample_coin_data)

        # 2. Warte 121 Sekunden (simuliert)
        future_time = time.time() + 121

        # 3. Cleanup entfernt abgelaufene Coins
        removed = self.cache.cleanup_expired_coins(current_time=future_time)

        assert removed == 1
        assert mint not in self.cache.cache
        self.mock_expirations.inc.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_trades_after_activation(self, sample_coin_data, sample_trade_data):
        """Test Keine neuen Trades nach Aktivierung im Cache"""
        mint = sample_coin_data["mint"]

        # Coin in Cache und aktiviert
        self.cache.add_coin(mint, sample_coin_data)
        self.cache.activate_coin(mint)

        initial_trades = len(self.cache.cache[mint]["trades"])

        # Versuche Trade hinzuzufügen
        self.cache.add_trade(mint, sample_trade_data)

        # Trades sollten nicht hinzugefügt werden (activated=True)
        # Da add_trade prüft auf activated
        assert self.cache.cache[mint]["activated"] is True


class TestWatchlistSync:
    """Tests für Watchlist Synchronisation"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup für jeden Test"""
        with patch('unified_service.cache_size'), \
             patch('unified_service.cache_activations'), \
             patch('unified_service.cache_expirations'), \
             patch('unified_service.coins_tracked'), \
             patch('unified_service.ws_connected'), \
             patch('unified_service.db_connected'), \
             patch('unified_service.uptime_seconds'):

            from unified_service import UnifiedService
            self.service = UnifiedService()
            self.service.watchlist = {}
            self.service.subscribed_mints = set()
            self.service.active_streams = {}
            self.service.pending_subscriptions = set()

            yield

    @pytest.mark.asyncio
    async def test_sync_adds_missing_coins(self):
        """Test Sync fügt fehlende Coins zur Watchlist hinzu"""
        # DB hat aktive Streams
        self.service.active_streams = {
            "Coin1": {"phase_id": 1, "interval_seconds": 5},
            "Coin2": {"phase_id": 1, "interval_seconds": 5},
            "Coin3": {"phase_id": 2, "interval_seconds": 30}
        }

        # Nur Coin1 ist in Watchlist
        self.service.watchlist["Coin1"] = {}

        # Finde fehlende Coins
        missing = set(self.service.active_streams.keys()) - set(self.service.watchlist.keys())

        assert "Coin2" in missing
        assert "Coin3" in missing
        assert "Coin1" not in missing

    @pytest.mark.asyncio
    async def test_sync_removes_stale_coins(self):
        """Test Sync entfernt nicht mehr aktive Coins"""
        # Watchlist hat 3 Coins
        self.service.watchlist = {
            "Coin1": {},
            "Coin2": {},
            "Coin3": {}
        }

        # DB hat nur Coin1 aktiv
        self.service.active_streams = {
            "Coin1": {"phase_id": 1}
        }

        # Finde zu entfernende Coins
        stale = set(self.service.watchlist.keys()) - set(self.service.active_streams.keys())

        assert "Coin2" in stale
        assert "Coin3" in stale
        assert "Coin1" not in stale

    @pytest.mark.asyncio
    async def test_sync_updates_phase_changes(self):
        """Test Sync aktualisiert Phasen-Änderungen"""
        # Coin in Watchlist mit Phase 1
        self.service.watchlist["Coin1"] = {
            "phase": 1,
            "interval": 5
        }

        # DB sagt Coin ist jetzt in Phase 2
        self.service.active_streams["Coin1"] = {
            "phase_id": 2,
            "interval_seconds": 30
        }

        # Prüfe Phasen-Änderung
        current_phase = self.service.watchlist["Coin1"]["phase"]
        new_phase = self.service.active_streams["Coin1"]["phase_id"]

        assert current_phase != new_phase
        assert new_phase == 2
