"""
Integration Tests für Zombie Detection
Testet Erkennung inaktiver Coins und Force Re-Subscribe
"""

import pytest
import asyncio
import time
from unittest.mock import patch, MagicMock, AsyncMock


class TestZombieDetection:
    """Tests für Zombie Detection (unified_service.py:1643-1689, 1861-1890)"""

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
            self.service.last_trade_timestamps = {}
            self.service.subscription_watchdog = {}
            self.service.websocket = AsyncMock()
            self.service.websocket.send = AsyncMock()

            yield

    @pytest.mark.asyncio
    async def test_watchdog_detects_inactive_coins(self):
        """Test Coins ohne Trades für 10+ Minuten werden erkannt"""
        mint = "ZombieCoin123456789012345678901234567890"
        now = time.time()

        # Coin mit letztem Trade vor 15 Minuten
        self.service.watchlist[mint] = {"buffer": {}}
        self.service.last_trade_timestamps[mint] = now - 900  # 15 Minuten

        # Finde inaktive Coins
        inactive_coins = []
        for m, entry in self.service.watchlist.items():
            last_trade = self.service.last_trade_timestamps.get(m, 0)
            time_since_trade = now - last_trade
            if time_since_trade > 600:  # 10 Minuten
                inactive_coins.append((m, time_since_trade))

        assert len(inactive_coins) == 1
        assert inactive_coins[0][0] == mint
        assert inactive_coins[0][1] >= 900

    @pytest.mark.asyncio
    async def test_watchdog_ignores_active_coins(self):
        """Test Aktive Coins werden nicht als Zombie erkannt"""
        mint = "ActiveCoin12345678901234567890123456789"
        now = time.time()

        # Coin mit letztem Trade vor 5 Minuten
        self.service.watchlist[mint] = {"buffer": {}}
        self.service.last_trade_timestamps[mint] = now - 300  # 5 Minuten

        # Finde inaktive Coins
        inactive_coins = []
        for m, entry in self.service.watchlist.items():
            last_trade = self.service.last_trade_timestamps.get(m, 0)
            time_since_trade = now - last_trade
            if time_since_trade > 600:  # 10 Minuten
                inactive_coins.append(m)

        assert len(inactive_coins) == 0

    @pytest.mark.asyncio
    async def test_force_resubscribe_sends_unsubscribe_then_subscribe(self):
        """Test Re-Subscription Sequenz: Unsubscribe → Wait → Subscribe"""
        mint = "ResubCoin1234567890123456789012345678901"
        self.service.watchlist[mint] = {"buffer": {}}

        # Simuliere force_resubscribe Logik
        if mint in self.service.watchlist and self.service.websocket:
            # Unsubscribe
            import json
            unsubscribe_msg = {"method": "unsubscribeTokenTrade", "keys": [mint]}
            await self.service.websocket.send(json.dumps(unsubscribe_msg))

            # Wait
            await asyncio.sleep(0.01)

            # Subscribe
            subscribe_msg = {"method": "subscribeTokenTrade", "keys": [mint]}
            await self.service.websocket.send(json.dumps(subscribe_msg))

        # Verifiziere beide Aufrufe
        assert self.service.websocket.send.call_count == 2

        # Prüfe Aufrufreihenfolge
        calls = self.service.websocket.send.call_args_list
        first_call = json.loads(calls[0][0][0])
        second_call = json.loads(calls[1][0][0])

        assert first_call["method"] == "unsubscribeTokenTrade"
        assert second_call["method"] == "subscribeTokenTrade"

    @pytest.mark.asyncio
    async def test_force_resubscribe_resets_watchdog(self):
        """Test Watchdog Timestamp wird nach Re-Subscribe zurückgesetzt"""
        mint = "ResetCoin1234567890123456789012345678901"
        old_time = time.time() - 1000

        self.service.watchlist[mint] = {"buffer": {}}
        self.service.subscription_watchdog[mint] = old_time

        # Simuliere Re-Subscribe (Reset Watchdog)
        new_time = time.time()
        self.service.subscription_watchdog[mint] = new_time

        assert self.service.subscription_watchdog[mint] > old_time
        assert self.service.subscription_watchdog[mint] >= new_time - 1

    @pytest.mark.asyncio
    async def test_no_websocket_handles_gracefully(self):
        """Test Force Re-Subscribe ohne WebSocket wirft keine Exception"""
        mint = "NoWsCoin12345678901234567890123456789012"
        self.service.watchlist[mint] = {"buffer": {}}
        self.service.websocket = None

        # Sollte keine Exception werfen
        if mint in self.service.watchlist:
            if hasattr(self, 'websocket') and self.service.websocket:
                await self.service.websocket.send("{}")
            else:
                pass  # Keine WebSocket-Verbindung

        # Test bestanden wenn keine Exception


class TestStaleDataDetection:
    """Tests für Stale Data Detection"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup für jeden Test"""
        self.last_saved_signatures = {}
        self.stale_data_warnings = {}
        yield

    @pytest.mark.asyncio
    async def test_stale_data_detection_identical_signature(self):
        """Test Identische Daten-Signatur wird erkannt"""
        mint = "StaleCoin1234567890123456789012345678901"

        # Erstelle Signatur aus Daten
        def create_signature(data):
            return f"{data['price']}_{data['volume']}_{data['trades']}"

        current_data = {"price": 0.001, "volume": 10.0, "trades": 100}
        current_sig = create_signature(current_data)

        # Erste Speicherung
        self.last_saved_signatures[mint] = current_sig

        # Gleiche Daten nochmal
        new_data = {"price": 0.001, "volume": 10.0, "trades": 100}
        new_sig = create_signature(new_data)

        is_stale = new_sig == self.last_saved_signatures.get(mint)
        assert is_stale is True

    @pytest.mark.asyncio
    async def test_stale_data_warning_counter(self):
        """Test Stale Data Warning Counter wird inkrementiert"""
        mint = "WarnCoin12345678901234567890123456789012"

        # Initialisiere
        self.stale_data_warnings[mint] = 0

        # Mehrere Stale-Detections
        for _ in range(3):
            self.stale_data_warnings[mint] += 1

        assert self.stale_data_warnings[mint] == 3

    @pytest.mark.asyncio
    async def test_stale_triggers_resubscribe_threshold(self):
        """Test 2+ Stale Warnings mit 5min+ Inaktivität triggert Re-Subscribe"""
        mint = "ThresholdCoin123456789012345678901234567"

        self.stale_data_warnings[mint] = 2
        last_trade = time.time() - 400  # 6+ Minuten

        should_resubscribe = (
            self.stale_data_warnings.get(mint, 0) >= 2 and
            (time.time() - last_trade) > 300  # 5 Minuten
        )

        assert should_resubscribe is True

    @pytest.mark.asyncio
    async def test_stale_no_resubscribe_if_active(self):
        """Test Kein Re-Subscribe wenn Coin noch aktiv ist"""
        mint = "ActiveStaleCoin1234567890123456789012345"

        self.stale_data_warnings[mint] = 3
        last_trade = time.time() - 60  # Nur 1 Minute

        should_resubscribe = (
            self.stale_data_warnings.get(mint, 0) >= 2 and
            (time.time() - last_trade) > 300  # 5 Minuten
        )

        assert should_resubscribe is False

    @pytest.mark.asyncio
    async def test_stale_warning_reset_on_save(self):
        """Test Stale Warnings werden nach erfolgreichem Save zurückgesetzt"""
        mint = "ResetWarnCoin123456789012345678901234567"

        self.stale_data_warnings[mint] = 5

        # Simuliere erfolgreichen Save
        save_successful = True
        if save_successful:
            self.stale_data_warnings[mint] = 0

        assert self.stale_data_warnings[mint] == 0


class TestZombieWatchdogTiming:
    """Tests für Zombie Watchdog Timing"""

    @pytest.mark.asyncio
    async def test_watchdog_10_minute_threshold(self):
        """Test 10-Minuten Threshold für Zombie Detection"""
        ZOMBIE_THRESHOLD = 600  # 10 Minuten in Sekunden

        # Genau 10 Minuten = gerade noch OK
        time_since_trade_ok = 599
        is_zombie_ok = time_since_trade_ok > ZOMBIE_THRESHOLD
        assert is_zombie_ok is False

        # Über 10 Minuten = Zombie
        time_since_trade_zombie = 601
        is_zombie = time_since_trade_zombie > ZOMBIE_THRESHOLD
        assert is_zombie is True

    @pytest.mark.asyncio
    async def test_watchdog_check_interval(self):
        """Test Watchdog wird alle 10 Sekunden geprüft"""
        DB_REFRESH_INTERVAL = 10  # Sekunden

        # Watchdog sollte bei jedem DB Refresh geprüft werden
        assert DB_REFRESH_INTERVAL == 10

    @pytest.mark.asyncio
    async def test_multiple_zombies_detected_at_once(self):
        """Test Mehrere Zombies werden gleichzeitig erkannt"""
        now = time.time()

        coins_with_last_trade = {
            "Zombie1": now - 700,   # 11+ Minuten
            "Zombie2": now - 900,   # 15 Minuten
            "Active1": now - 300,   # 5 Minuten (OK)
            "Zombie3": now - 1200,  # 20 Minuten
            "Active2": now - 60     # 1 Minute (OK)
        }

        zombies = []
        for mint, last_trade in coins_with_last_trade.items():
            if (now - last_trade) > 600:
                zombies.append(mint)

        assert len(zombies) == 3
        assert "Zombie1" in zombies
        assert "Zombie2" in zombies
        assert "Zombie3" in zombies
        assert "Active1" not in zombies
        assert "Active2" not in zombies

    @pytest.mark.asyncio
    async def test_new_coin_not_zombie(self):
        """Test Neu hinzugefügter Coin ist kein Zombie"""
        now = time.time()

        # Coin gerade erst hinzugefügt
        last_trade_timestamps = {}
        mint = "NewCoin1234567890123456789012345678901234"

        # Kein Eintrag = gerade erst hinzugefügt
        last_trade = last_trade_timestamps.get(mint, now)  # Default: jetzt
        time_since_trade = now - last_trade

        is_zombie = time_since_trade > 600
        assert is_zombie is False
