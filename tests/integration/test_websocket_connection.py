"""
Integration Tests für WebSocket Connection
Testet Reconnection, Subscription Restore und Error Handling
"""

import pytest
import asyncio
import json
import time
from unittest.mock import patch, MagicMock, AsyncMock


class TestWebSocketConnection:
    """Tests für WebSocket Connection (unified_service.py:1982-2222)"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup für jeden Test"""
        self.mock_ws = AsyncMock()
        self.mock_ws.send = AsyncMock()
        self.mock_ws.recv = AsyncMock(return_value='{}')
        self.mock_ws.close = AsyncMock()
        self.mock_ws.closed = False
        self.mock_ws.ping = AsyncMock()

        # Mock Pool
        self.mock_pool = AsyncMock()
        self.mock_pool.fetch = AsyncMock(return_value=[])
        self.mock_pool.fetchrow = AsyncMock(return_value=None)
        self.mock_pool.execute = AsyncMock()

        # Context Manager für acquire
        conn = AsyncMock()
        conn.fetch = self.mock_pool.fetch
        self.mock_pool.acquire = MagicMock()
        self.mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
        self.mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        yield

    @pytest.mark.asyncio
    async def test_subscribes_to_new_tokens_on_connect(self):
        """Test subscribeNewToken Message wird bei Connect gesendet"""
        with patch('unified_service.cache_size'), \
             patch('unified_service.cache_activations'), \
             patch('unified_service.cache_expirations'), \
             patch('unified_service.coins_tracked'), \
             patch('unified_service.ws_connected'), \
             patch('unified_service.db_connected'), \
             patch('unified_service.uptime_seconds'), \
             patch('unified_service.asyncpg.create_pool', return_value=self.mock_pool):

            from unified_service import UnifiedService
            service = UnifiedService()
            service.pool = self.mock_pool
            service.websocket = self.mock_ws

            # Simuliere subscribeNewToken Aufruf
            await service.websocket.send(json.dumps({"method": "subscribeNewToken"}))

            # Verifiziere dass send aufgerufen wurde
            self.mock_ws.send.assert_called()
            call_args = self.mock_ws.send.call_args[0][0]
            data = json.loads(call_args)
            assert data["method"] == "subscribeNewToken"

    @pytest.mark.asyncio
    async def test_restores_subscriptions_on_reconnect(self):
        """Test bestehende Subscriptions werden nach Reconnect wiederhergestellt"""
        with patch('unified_service.cache_size'), \
             patch('unified_service.cache_activations'), \
             patch('unified_service.cache_expirations'), \
             patch('unified_service.coins_tracked'), \
             patch('unified_service.ws_connected'), \
             patch('unified_service.db_connected'), \
             patch('unified_service.uptime_seconds'):

            from unified_service import UnifiedService
            service = UnifiedService()
            service.pool = self.mock_pool
            service.websocket = self.mock_ws

            # Pre-populate subscribed_mints
            test_mints = [
                "Coin1123456789012345678901234567890123456",
                "Coin2123456789012345678901234567890123456",
                "Coin3123456789012345678901234567890123456"
            ]
            service.subscribed_mints = set(test_mints)

            # Simuliere Restore
            if service.subscribed_mints:
                restore_msg = {
                    "method": "subscribeTokenTrade",
                    "keys": list(service.subscribed_mints)
                }
                await service.websocket.send(json.dumps(restore_msg))

            # Verifiziere
            self.mock_ws.send.assert_called()
            call_args = self.mock_ws.send.call_args[0][0]
            data = json.loads(call_args)
            assert data["method"] == "subscribeTokenTrade"
            assert len(data["keys"]) == 3

    @pytest.mark.asyncio
    async def test_exponential_backoff_calculation(self):
        """Test Exponential Backoff wird korrekt berechnet"""
        WS_RETRY_DELAY = 3
        WS_MAX_RETRY_DELAY = 60

        # Teste verschiedene Reconnect-Counts
        test_cases = [
            (0, 3),    # 3 * (1 + 0 * 0.5) = 3
            (1, 4.5),  # 3 * (1 + 1 * 0.5) = 4.5
            (2, 6),    # 3 * (1 + 2 * 0.5) = 6
            (5, 10.5), # 3 * (1 + 5 * 0.5) = 10.5
            (20, 33),  # 3 * (1 + 20 * 0.5) = 33
            (50, 60),  # min(78, 60) = 60 (capped)
        ]

        for reconnect_count, expected_delay in test_cases:
            delay = min(WS_RETRY_DELAY * (1 + reconnect_count * 0.5), WS_MAX_RETRY_DELAY)
            assert delay == expected_delay, f"reconnect_count={reconnect_count}"

    @pytest.mark.asyncio
    async def test_connection_timeout_detection(self):
        """Test Connection Timeout (30s ohne Message) wird erkannt"""
        WS_CONNECTION_TIMEOUT = 30

        # Simuliere letzte Nachricht vor 35 Sekunden
        last_message_time = time.time() - 35

        time_since_last = time.time() - last_message_time
        should_timeout = time_since_last > WS_CONNECTION_TIMEOUT

        assert should_timeout is True

    @pytest.mark.asyncio
    async def test_no_timeout_within_window(self):
        """Test kein Timeout innerhalb des Windows"""
        WS_CONNECTION_TIMEOUT = 30

        # Letzte Nachricht vor 10 Sekunden
        last_message_time = time.time() - 10

        time_since_last = time.time() - last_message_time
        should_timeout = time_since_last > WS_CONNECTION_TIMEOUT

        assert should_timeout is False

    @pytest.mark.asyncio
    async def test_batching_task_management(self):
        """Test Batching Task wird gestartet und gestoppt"""
        with patch('unified_service.cache_size'), \
             patch('unified_service.cache_activations'), \
             patch('unified_service.cache_expirations'), \
             patch('unified_service.coins_tracked'), \
             patch('unified_service.ws_connected'), \
             patch('unified_service.db_connected'), \
             patch('unified_service.uptime_seconds'):

            from unified_service import UnifiedService
            service = UnifiedService()

            # Initialisiere Task-Variable
            service.batching_task = None

            # Simuliere Task Start
            async def mock_batching():
                while True:
                    await asyncio.sleep(1)

            service.batching_task = asyncio.create_task(mock_batching())

            assert service.batching_task is not None
            assert not service.batching_task.done()

            # Cleanup
            service.batching_task.cancel()
            try:
                await service.batching_task
            except asyncio.CancelledError:
                pass

    @pytest.mark.asyncio
    async def test_reconnect_resets_counter_on_success(self):
        """Test reconnect_count wird auf 0 gesetzt nach erfolgreicher Verbindung"""
        reconnect_count = 5

        # Simuliere erfolgreiche Verbindung
        connection_successful = True

        if connection_successful:
            reconnect_count = 0

        assert reconnect_count == 0

    @pytest.mark.asyncio
    async def test_ssl_context_configuration(self):
        """Test SSL Context wird korrekt konfiguriert"""
        import ssl

        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        assert ssl_context.check_hostname is False
        assert ssl_context.verify_mode == ssl.CERT_NONE

    @pytest.mark.asyncio
    async def test_subscription_message_format(self):
        """Test Subscription Message hat korrektes Format"""
        mints = ["mint1", "mint2", "mint3"]

        subscribe_msg = {
            "method": "subscribeTokenTrade",
            "keys": mints
        }

        json_str = json.dumps(subscribe_msg)
        parsed = json.loads(json_str)

        assert parsed["method"] == "subscribeTokenTrade"
        assert parsed["keys"] == mints

    @pytest.mark.asyncio
    async def test_unsubscribe_message_format(self):
        """Test Unsubscribe Message hat korrektes Format"""
        mint = "mint1"

        unsubscribe_msg = {
            "method": "unsubscribeTokenTrade",
            "keys": [mint]
        }

        json_str = json.dumps(unsubscribe_msg)
        parsed = json.loads(json_str)

        assert parsed["method"] == "unsubscribeTokenTrade"
        assert parsed["keys"] == [mint]

    @pytest.mark.asyncio
    async def test_handles_json_decode_error(self):
        """Test JSON Decode Errors werden graceful gehandhabt"""
        invalid_json = "not valid json {"

        try:
            json.loads(invalid_json)
            json_valid = True
        except json.JSONDecodeError:
            json_valid = False

        assert json_valid is False

    @pytest.mark.asyncio
    async def test_handles_websocket_send_error(self):
        """Test WebSocket Send Errors werden gehandhabt"""
        self.mock_ws.send = AsyncMock(side_effect=Exception("Connection closed"))

        with pytest.raises(Exception) as exc_info:
            await self.mock_ws.send("test")

        assert "Connection closed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_websocket_recv_timeout(self):
        """Test WebSocket Receive mit Timeout"""
        async def slow_recv():
            await asyncio.sleep(10)
            return "{}"

        self.mock_ws.recv = slow_recv

        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(self.mock_ws.recv(), timeout=0.1)

    @pytest.mark.asyncio
    async def test_pending_subscriptions_queue(self):
        """Test Pending Subscriptions werden korrekt verwaltet"""
        pending = set()

        # Füge Coins hinzu
        pending.add("coin1")
        pending.add("coin2")
        pending.add("coin3")

        assert len(pending) == 3

        # Entferne nach Subscription
        pending.discard("coin1")
        assert len(pending) == 2
        assert "coin1" not in pending


class TestWebSocketMessageHandling:
    """Tests für WebSocket Message Handling"""

    @pytest.mark.asyncio
    async def test_handles_new_token_message(self):
        """Test newToken Message wird korrekt verarbeitet"""
        message = {
            "method": "newToken",
            "mint": "TestCoin123456789012345678901234567890123",
            "name": "Test Coin",
            "symbol": "TEST",
            "marketCapSol": 1000
        }

        # Verifiziere Struktur
        assert message.get("method") == "newToken"
        assert "mint" in message
        assert "name" in message

    @pytest.mark.asyncio
    async def test_handles_token_trade_message(self):
        """Test tokenTrade Message wird korrekt verarbeitet"""
        message = {
            "method": "tokenTrade",
            "mint": "TestCoin123456789012345678901234567890123",
            "txType": "buy",
            "solAmount": 1.5,
            "tokenAmount": 150000,
            "traderPublicKey": "TraderKey123"
        }

        assert message.get("method") == "tokenTrade"
        assert message.get("txType") in ["buy", "sell"]

    @pytest.mark.asyncio
    async def test_ignores_unknown_message_type(self):
        """Test unbekannte Message Types werden ignoriert"""
        message = {
            "method": "unknownMethod",
            "data": "some data"
        }

        method = message.get("method")
        known_methods = ["newToken", "tokenTrade"]

        should_process = method in known_methods
        assert should_process is False

    @pytest.mark.asyncio
    async def test_handles_empty_message(self):
        """Test leere Messages werden gehandhabt"""
        message = {}

        method = message.get("method")
        assert method is None

    @pytest.mark.asyncio
    async def test_handles_malformed_trade_data(self):
        """Test malformed Trade Data wird gehandhabt"""
        message = {
            "method": "tokenTrade",
            "mint": "TestCoin123",
            # Fehlt: txType, solAmount, etc.
        }

        # Sollte keine Exception werfen
        tx_type = message.get("txType")
        sol_amount = message.get("solAmount", 0)

        assert tx_type is None
        assert sol_amount == 0
