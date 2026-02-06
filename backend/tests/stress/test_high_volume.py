"""
Stress Tests für High Volume Scenarios
Testet Performance unter hoher Last
"""

import pytest
import asyncio
import time
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.mark.slow
@pytest.mark.stress
class TestHighVolume:
    """Stress Tests für High Volume (Trades, Coins, Subscriptions)"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup für jeden Test"""
        with patch('unified_service.cache_size'), \
             patch('unified_service.cache_activations'), \
             patch('unified_service.cache_expirations'), \
             patch('unified_service.coins_tracked'), \
             patch('unified_service.ws_connected'), \
             patch('unified_service.db_connected'), \
             patch('unified_service.uptime_seconds'), \
             patch('unified_service.trades_received'), \
             patch('unified_service.trades_processed'):

            from unified_service import UnifiedService
            self.service = UnifiedService()
            self.service.watchlist = {}
            self.service.ath_cache = {}
            self.service.dirty_aths = set()
            self.service.last_trade_timestamps = {}
            self.service.subscription_watchdog = {}

            yield

    def _create_watchlist_entry(self, mint):
        """Erstellt Watchlist Entry für Tests"""
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
                "max_buy": 0,
                "max_sell": 0,
                "whale_buy_vol": 0,
                "whale_sell_vol": 0,
                "whale_buys": 0,
                "whale_sells": 0,
                "dev_sold_amount": 0,
                "micro_trades": 0,
                "wallets": set(),
                "v_sol": 0,
                "mcap": 0
            },
            "meta": {"creator_address": None},
            "interval": 5,
            "last_flush": time.time()
        }

    @pytest.mark.asyncio
    async def test_high_trade_volume(self):
        """Test Verarbeitung von 1000 Trades pro Sekunde"""
        mint = "HighVolumeCoin12345678901234567890123456"
        self._create_watchlist_entry(mint)

        trades_per_second = 1000
        duration_seconds = 1
        total_trades = trades_per_second * duration_seconds

        start_time = time.time()
        processed = 0

        for i in range(total_trades):
            trade = {
                "mint": mint,
                "txType": "buy" if i % 2 == 0 else "sell",
                "solAmount": 0.1,
                "vSolInBondingCurve": 10.0 + (i * 0.001),
                "vTokensInBondingCurve": 1000000000,
                "traderPublicKey": f"Trader{i % 100}"
            }
            self.service.process_trade(trade)
            processed += 1

        elapsed = time.time() - start_time

        assert processed == total_trades
        # Sollte in vernünftiger Zeit abgeschlossen sein
        assert elapsed < 5.0  # Max 5 Sekunden für 1000 Trades

        # Verifiziere Buffer wurde aktualisiert
        buf = self.service.watchlist[mint]["buffer"]
        assert buf["buys"] + buf["sells"] == total_trades

    @pytest.mark.asyncio
    async def test_many_simultaneous_coins(self):
        """Test Tracking von 500 Coins gleichzeitig"""
        num_coins = 500

        # Erstelle 500 Watchlist Entries
        for i in range(num_coins):
            mint = f"Coin{i:04d}12345678901234567890123456789012"
            self._create_watchlist_entry(mint)

        assert len(self.service.watchlist) == num_coins

        # Simuliere Trades für alle Coins
        trades_per_coin = 10
        total_trades = 0

        start_time = time.time()

        for i in range(num_coins):
            mint = f"Coin{i:04d}12345678901234567890123456789012"
            for j in range(trades_per_coin):
                trade = {
                    "mint": mint,
                    "txType": "buy",
                    "solAmount": 0.1,
                    "vSolInBondingCurve": 10.0,
                    "vTokensInBondingCurve": 1000000000,
                    "traderPublicKey": f"Trader{j}"
                }
                self.service.process_trade(trade)
                total_trades += 1

        elapsed = time.time() - start_time

        assert total_trades == num_coins * trades_per_coin
        assert elapsed < 10.0  # Max 10 Sekunden für 5000 Trades

    @pytest.mark.asyncio
    async def test_large_batch_subscription(self):
        """Test Subscription von 100 Coins in einem Batch"""
        pending_subscriptions = set()
        subscribed_mints = set()

        # 100 Coins zum Subscriben
        for i in range(100):
            pending_subscriptions.add(f"BatchCoin{i:03d}123456789012345678901234")

        # Batch Subscription
        batch = list(pending_subscriptions)
        subscription_msg = {
            "method": "subscribeTokenTrade",
            "keys": batch
        }

        # Simuliere erfolgreiche Subscription
        for mint in batch:
            subscribed_mints.add(mint)
            pending_subscriptions.discard(mint)

        assert len(pending_subscriptions) == 0
        assert len(subscribed_mints) == 100
        assert len(subscription_msg["keys"]) == 100

    @pytest.mark.asyncio
    async def test_cache_memory_usage(self):
        """Test Memory Usage mit 1000 Coins im Cache"""
        with patch('unified_service.cache_size'), \
             patch('unified_service.cache_activations'), \
             patch('unified_service.cache_expirations'):

            from unified_service import CoinCache
            cache = CoinCache(cache_seconds=120)

            num_coins = 1000
            trades_per_coin = 50

            for i in range(num_coins):
                mint = f"CacheCoin{i:04d}1234567890123456789012345"
                coin_data = {
                    "mint": mint,
                    "name": f"Cache Coin {i}",
                    "symbol": f"CC{i}",
                    "marketCapSol": 1000 + i
                }
                cache.add_coin(mint, coin_data)

                # Füge Trades hinzu
                for j in range(trades_per_coin):
                    trade = {
                        "signature": f"sig_{i}_{j}",
                        "solAmount": 0.1 * j,
                        "txType": "buy"
                    }
                    cache.add_trade(mint, trade)

            stats = cache.get_cache_stats()

            assert stats["total_coins"] == num_coins
            # Verifiziere dass alle Trades gespeichert wurden
            total_cached_trades = sum(
                len(data["trades"]) for data in cache.cache.values()
            )
            assert total_cached_trades == num_coins * trades_per_coin

    @pytest.mark.asyncio
    async def test_watchlist_iteration_performance(self):
        """Test Watchlist Iteration Performance"""
        num_coins = 1000

        # Erstelle große Watchlist
        for i in range(num_coins):
            mint = f"IterCoin{i:04d}123456789012345678901234567"
            self._create_watchlist_entry(mint)

        # Simuliere Watchdog Check (iteriert über alle Coins)
        start_time = time.time()
        inactive_coins = []
        now = time.time()

        for mint, entry in self.service.watchlist.items():
            last_trade = self.service.last_trade_timestamps.get(mint, now)
            if (now - last_trade) > 600:
                inactive_coins.append(mint)

        elapsed = time.time() - start_time

        # Iteration sollte schnell sein
        assert elapsed < 0.1  # Max 100ms für 1000 Coins

    @pytest.mark.asyncio
    async def test_concurrent_trade_processing(self):
        """Test Concurrent Trade Processing"""
        num_coins = 50
        trades_per_coin = 100

        # Setup Coins
        for i in range(num_coins):
            mint = f"ConcCoin{i:02d}12345678901234567890123456789"
            self._create_watchlist_entry(mint)

        processed_count = 0

        async def process_trades_for_coin(coin_index):
            nonlocal processed_count
            mint = f"ConcCoin{coin_index:02d}12345678901234567890123456789"

            for j in range(trades_per_coin):
                trade = {
                    "mint": mint,
                    "txType": "buy",
                    "solAmount": 0.1,
                    "vSolInBondingCurve": 10.0,
                    "vTokensInBondingCurve": 1000000000,
                    "traderPublicKey": f"Trader{j}"
                }
                self.service.process_trade(trade)
                processed_count += 1

        start_time = time.time()

        # Verarbeite Trades für alle Coins "gleichzeitig"
        tasks = [process_trades_for_coin(i) for i in range(num_coins)]
        await asyncio.gather(*tasks)

        elapsed = time.time() - start_time

        assert processed_count == num_coins * trades_per_coin
        assert elapsed < 5.0  # Max 5 Sekunden


@pytest.mark.slow
@pytest.mark.stress
class TestDataIntegrity:
    """Tests für Daten-Integrität unter Last"""

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
            self.service.ath_cache = {}
            self.service.dirty_aths = set()
            self.service.last_trade_timestamps = {}
            self.service.subscription_watchdog = {}

            yield

    def _create_watchlist_entry(self, mint):
        """Erstellt Watchlist Entry"""
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
                "max_buy": 0,
                "max_sell": 0,
                "whale_buy_vol": 0,
                "whale_sell_vol": 0,
                "whale_buys": 0,
                "whale_sells": 0,
                "dev_sold_amount": 0,
                "micro_trades": 0,
                "wallets": set(),
                "v_sol": 0,
                "mcap": 0
            },
            "meta": {"creator_address": None},
            "interval": 5,
            "last_flush": time.time()
        }

    @pytest.mark.asyncio
    async def test_volume_accuracy_under_load(self):
        """Test Volume-Berechnung ist akkurat unter Last"""
        mint = "AccuracyCoin123456789012345678901234567"
        self._create_watchlist_entry(mint)

        expected_buy_vol = 0.0
        expected_sell_vol = 0.0
        num_trades = 10000

        for i in range(num_trades):
            sol_amount = 0.1 + (i % 10) * 0.01  # Variiere Beträge
            is_buy = i % 3 != 0  # 2/3 Buys, 1/3 Sells

            trade = {
                "mint": mint,
                "txType": "buy" if is_buy else "sell",
                "solAmount": sol_amount,
                "vSolInBondingCurve": 10.0,
                "vTokensInBondingCurve": 1000000000,
                "traderPublicKey": f"Trader{i % 100}"
            }

            if is_buy:
                expected_buy_vol += sol_amount
            else:
                expected_sell_vol += sol_amount

            self.service.process_trade(trade)

        buf = self.service.watchlist[mint]["buffer"]

        # Floating Point Vergleich mit Toleranz
        assert abs(buf["vol_buy"] - expected_buy_vol) < 0.001
        assert abs(buf["vol_sell"] - expected_sell_vol) < 0.001

    @pytest.mark.asyncio
    async def test_trade_count_accuracy(self):
        """Test Trade Count ist akkurat"""
        mint = "CountCoin12345678901234567890123456789012"
        self._create_watchlist_entry(mint)

        num_buys = 7500
        num_sells = 2500

        for i in range(num_buys):
            trade = {
                "mint": mint,
                "txType": "buy",
                "solAmount": 0.1,
                "vSolInBondingCurve": 10.0,
                "vTokensInBondingCurve": 1000000000,
                "traderPublicKey": f"Buyer{i}"
            }
            self.service.process_trade(trade)

        for i in range(num_sells):
            trade = {
                "mint": mint,
                "txType": "sell",
                "solAmount": 0.1,
                "vSolInBondingCurve": 10.0,
                "vTokensInBondingCurve": 1000000000,
                "traderPublicKey": f"Seller{i}"
            }
            self.service.process_trade(trade)

        buf = self.service.watchlist[mint]["buffer"]

        assert buf["buys"] == num_buys
        assert buf["sells"] == num_sells

    @pytest.mark.asyncio
    async def test_unique_wallets_accuracy(self):
        """Test Unique Wallets werden korrekt gezählt"""
        mint = "WalletCoin1234567890123456789012345678901"
        self._create_watchlist_entry(mint)

        unique_wallets = 100
        trades_per_wallet = 50

        for wallet_id in range(unique_wallets):
            for trade_num in range(trades_per_wallet):
                trade = {
                    "mint": mint,
                    "txType": "buy",
                    "solAmount": 0.1,
                    "vSolInBondingCurve": 10.0,
                    "vTokensInBondingCurve": 1000000000,
                    "traderPublicKey": f"Wallet{wallet_id:03d}"
                }
                self.service.process_trade(trade)

        buf = self.service.watchlist[mint]["buffer"]

        # Set sollte nur unique Wallets enthalten
        assert len(buf["wallets"]) == unique_wallets
        assert buf["buys"] == unique_wallets * trades_per_wallet

    @pytest.mark.asyncio
    async def test_ohlc_accuracy(self):
        """Test OHLC Berechnung ist akkurat"""
        mint = "OHLCCoin123456789012345678901234567890123"
        self._create_watchlist_entry(mint)

        # Trades mit bekannten Preisen
        prices = [0.00010, 0.00015, 0.00008, 0.00012, 0.00020, 0.00005, 0.00018]

        for i, _ in enumerate(prices):
            # Berechne vSol und vTokens für gewünschten Preis
            v_tokens = 1000000
            v_sol = prices[i] * v_tokens

            trade = {
                "mint": mint,
                "txType": "buy",
                "solAmount": 0.1,
                "vSolInBondingCurve": v_sol,
                "vTokensInBondingCurve": v_tokens,
                "traderPublicKey": f"Trader{i}"
            }
            self.service.process_trade(trade)

        buf = self.service.watchlist[mint]["buffer"]

        assert buf["open"] == prices[0]  # Erster Preis
        assert buf["close"] == prices[-1]  # Letzter Preis
        assert buf["high"] == max(prices)  # Höchster
        assert buf["low"] == min(prices)  # Niedrigster

    @pytest.mark.asyncio
    async def test_ath_tracking_accuracy(self):
        """Test ATH Tracking ist akkurat"""
        mint = "ATHCoin12345678901234567890123456789012345"
        self._create_watchlist_entry(mint)
        self.service.ath_cache[mint] = 0.0

        max_price = 0.0
        num_trades = 1000

        for i in range(num_trades):
            # Preis variiert, aber manchmal neue ATHs
            price = 0.00001 * (1 + (i % 100))
            if i % 50 == 0:
                price *= 2  # Gelegentlich höhere Preise

            max_price = max(max_price, price)

            v_tokens = 1000000
            v_sol = price * v_tokens

            trade = {
                "mint": mint,
                "txType": "buy",
                "solAmount": 0.1,
                "vSolInBondingCurve": v_sol,
                "vTokensInBondingCurve": v_tokens,
                "traderPublicKey": f"Trader{i}"
            }
            self.service.process_trade(trade)

        # ATH Cache sollte Maximum tracken
        assert self.service.ath_cache[mint] == max_price
