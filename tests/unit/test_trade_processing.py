"""
Unit Tests für Trade Processing
Testet die process_trade() Methode und zugehörige Logik
"""

import pytest
import time
from unittest.mock import patch, MagicMock


class TestTradeProcessing:
    """Tests für process_trade() (unified_service.py:1582-1641)"""

    @pytest.fixture(autouse=True)
    def setup_service(self):
        """Setup für jeden Test mit gemocktem UnifiedService"""
        # Mock alle Prometheus Metriken und Konfigurationswerte
        with patch('unified_service.cache_size'), \
             patch('unified_service.cache_activations'), \
             patch('unified_service.cache_expirations'), \
             patch('unified_service.coins_tracked'), \
             patch('unified_service.ws_connected'), \
             patch('unified_service.db_connected'), \
             patch('unified_service.uptime_seconds'), \
             patch('unified_service.trades_received'), \
             patch('unified_service.trades_processed'), \
             patch('unified_service.WHALE_THRESHOLD_SOL', 1.0):

            from unified_service import UnifiedService

            self.service = UnifiedService()

            # Initialisiere benötigte Datenstrukturen
            self.service.watchlist = {}
            self.service.ath_cache = {}
            self.service.dirty_aths = set()
            self.service.last_trade_timestamps = {}
            self.service.subscription_watchdog = {}

            yield

    def _create_watchlist_entry(self, mint, creator_address=None):
        """Hilfsfunktion um Watchlist-Eintrag zu erstellen"""
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
            "meta": {
                "creator_address": creator_address
            },
            "interval": 5,
            "last_flush": time.time()
        }

    def test_process_trade_updates_buffer_for_buy(self, sample_trade_data):
        """Verify Buy Trade aktualisiert vol_buy, buys, max_buy"""
        mint = sample_trade_data["mint"]
        self._create_watchlist_entry(mint)

        self.service.process_trade(sample_trade_data)

        buf = self.service.watchlist[mint]["buffer"]
        assert buf["buys"] == 1
        assert buf["vol_buy"] == sample_trade_data["solAmount"]
        assert buf["max_buy"] == sample_trade_data["solAmount"]

    def test_process_trade_updates_buffer_for_sell(self, sample_sell_trade):
        """Verify Sell Trade aktualisiert vol_sell, sells, max_sell"""
        mint = sample_sell_trade["mint"]
        self._create_watchlist_entry(mint)

        self.service.process_trade(sample_sell_trade)

        buf = self.service.watchlist[mint]["buffer"]
        assert buf["sells"] == 1
        assert buf["vol_sell"] == sample_sell_trade["solAmount"]
        assert buf["max_sell"] == sample_sell_trade["solAmount"]

    def test_process_trade_whale_detection_buy(self, sample_whale_trade):
        """Verify Whale Buy (>= 1.0 SOL) wird erkannt"""
        mint = sample_whale_trade["mint"]
        self._create_watchlist_entry(mint)

        self.service.process_trade(sample_whale_trade)

        buf = self.service.watchlist[mint]["buffer"]
        assert buf["whale_buys"] == 1
        assert buf["whale_buy_vol"] == sample_whale_trade["solAmount"]

    def test_process_trade_whale_detection_sell(self):
        """Verify Whale Sell (>= 1.0 SOL) wird erkannt"""
        mint = "TestCoin123456789012345678901234567890123"
        self._create_watchlist_entry(mint)

        whale_sell = {
            "mint": mint,
            "txType": "sell",
            "solAmount": 2.5,
            "vSolInBondingCurve": 10.0,
            "vTokensInBondingCurve": 1000000000,
            "traderPublicKey": "WhaleTrader123"
        }

        self.service.process_trade(whale_sell)

        buf = self.service.watchlist[mint]["buffer"]
        assert buf["whale_sells"] == 1
        assert buf["whale_sell_vol"] == 2.5

    def test_process_trade_non_whale_not_counted(self, sample_trade_data):
        """Verify normaler Trade (< 1.0 SOL) wird nicht als Whale gezählt"""
        mint = sample_trade_data["mint"]
        sample_trade_data["solAmount"] = 0.5  # Unter Whale Threshold
        self._create_watchlist_entry(mint)

        self.service.process_trade(sample_trade_data)

        buf = self.service.watchlist[mint]["buffer"]
        assert buf["whale_buys"] == 0
        assert buf["whale_buy_vol"] == 0

    def test_process_trade_dev_sold_tracking(self, sample_sell_trade):
        """Verify Dev Sell wird getrackt wenn Trader = Creator"""
        mint = sample_sell_trade["mint"]
        creator = sample_sell_trade["traderPublicKey"]
        self._create_watchlist_entry(mint, creator_address=creator)

        self.service.process_trade(sample_sell_trade)

        buf = self.service.watchlist[mint]["buffer"]
        assert buf["dev_sold_amount"] == sample_sell_trade["solAmount"]

    def test_process_trade_dev_sold_not_tracked_for_others(self, sample_sell_trade):
        """Verify Dev Sell wird nicht getrackt für andere Trader"""
        mint = sample_sell_trade["mint"]
        self._create_watchlist_entry(mint, creator_address="DifferentCreator123")

        self.service.process_trade(sample_sell_trade)

        buf = self.service.watchlist[mint]["buffer"]
        assert buf["dev_sold_amount"] == 0

    def test_process_trade_micro_trades(self, sample_micro_trade):
        """Verify Micro Trades (< 0.01 SOL) werden gezählt"""
        mint = sample_micro_trade["mint"]
        self._create_watchlist_entry(mint)

        self.service.process_trade(sample_micro_trade)

        buf = self.service.watchlist[mint]["buffer"]
        assert buf["micro_trades"] == 1

    def test_process_trade_normal_trade_not_micro(self, sample_trade_data):
        """Verify normaler Trade (>= 0.01 SOL) ist kein Micro Trade"""
        mint = sample_trade_data["mint"]
        sample_trade_data["solAmount"] = 0.1  # Über Micro Threshold
        self._create_watchlist_entry(mint)

        self.service.process_trade(sample_trade_data)

        buf = self.service.watchlist[mint]["buffer"]
        assert buf["micro_trades"] == 0

    def test_process_trade_ohlc_calculation(self, sample_trade_data):
        """Verify OHLC (Open/High/Low/Close) wird korrekt berechnet"""
        mint = sample_trade_data["mint"]
        self._create_watchlist_entry(mint)

        # Berechne erwarteten Preis
        expected_price = float(sample_trade_data["vSolInBondingCurve"]) / float(sample_trade_data["vTokensInBondingCurve"])

        self.service.process_trade(sample_trade_data)

        buf = self.service.watchlist[mint]["buffer"]
        assert buf["open"] == expected_price
        assert buf["close"] == expected_price
        assert buf["high"] == expected_price
        assert buf["low"] == expected_price

    def test_process_trade_ohlc_multiple_trades(self):
        """Verify OHLC über mehrere Trades"""
        mint = "TestCoin123456789012345678901234567890123"
        self._create_watchlist_entry(mint)

        # Trade 1: Preis = 0.00001
        trade1 = {
            "mint": mint,
            "txType": "buy",
            "solAmount": 1.0,
            "vSolInBondingCurve": 10.0,
            "vTokensInBondingCurve": 1000000,  # Preis = 0.00001
            "traderPublicKey": "Trader1"
        }

        # Trade 2: Preis = 0.00002 (höher)
        trade2 = {
            "mint": mint,
            "txType": "buy",
            "solAmount": 1.0,
            "vSolInBondingCurve": 20.0,
            "vTokensInBondingCurve": 1000000,  # Preis = 0.00002
            "traderPublicKey": "Trader2"
        }

        # Trade 3: Preis = 0.000005 (niedriger)
        trade3 = {
            "mint": mint,
            "txType": "buy",
            "solAmount": 1.0,
            "vSolInBondingCurve": 5.0,
            "vTokensInBondingCurve": 1000000,  # Preis = 0.000005
            "traderPublicKey": "Trader3"
        }

        self.service.process_trade(trade1)
        self.service.process_trade(trade2)
        self.service.process_trade(trade3)

        buf = self.service.watchlist[mint]["buffer"]
        assert buf["open"] == 0.00001  # Erster Trade
        assert buf["close"] == 0.000005  # Letzter Trade
        assert buf["high"] == 0.00002  # Höchster
        assert buf["low"] == 0.000005  # Niedrigster

    def test_process_trade_wallet_tracking(self, sample_trade_data):
        """Verify Unique Wallets werden getrackt"""
        mint = sample_trade_data["mint"]
        self._create_watchlist_entry(mint)

        self.service.process_trade(sample_trade_data)

        buf = self.service.watchlist[mint]["buffer"]
        assert sample_trade_data["traderPublicKey"] in buf["wallets"]
        assert len(buf["wallets"]) == 1

    def test_process_trade_multiple_wallets(self):
        """Verify mehrere unique Wallets werden gezählt"""
        mint = "TestCoin123456789012345678901234567890123"
        self._create_watchlist_entry(mint)

        for i in range(5):
            trade = {
                "mint": mint,
                "txType": "buy",
                "solAmount": 0.1,
                "vSolInBondingCurve": 10.0,
                "vTokensInBondingCurve": 1000000000,
                "traderPublicKey": f"Trader{i}"
            }
            self.service.process_trade(trade)

        buf = self.service.watchlist[mint]["buffer"]
        assert len(buf["wallets"]) == 5

    def test_process_trade_same_wallet_counted_once(self):
        """Verify gleiche Wallet wird nur einmal gezählt"""
        mint = "TestCoin123456789012345678901234567890123"
        self._create_watchlist_entry(mint)

        for _ in range(3):
            trade = {
                "mint": mint,
                "txType": "buy",
                "solAmount": 0.1,
                "vSolInBondingCurve": 10.0,
                "vTokensInBondingCurve": 1000000000,
                "traderPublicKey": "SameTrader"
            }
            self.service.process_trade(trade)

        buf = self.service.watchlist[mint]["buffer"]
        assert len(buf["wallets"]) == 1

    def test_process_trade_ath_tracking(self, sample_trade_data):
        """Verify ATH Cache wird aktualisiert"""
        mint = sample_trade_data["mint"]
        self._create_watchlist_entry(mint)
        self.service.ath_cache[mint] = 0.0

        self.service.process_trade(sample_trade_data)

        # ATH sollte gesetzt sein
        expected_price = float(sample_trade_data["vSolInBondingCurve"]) / float(sample_trade_data["vTokensInBondingCurve"])
        assert self.service.ath_cache[mint] == expected_price
        assert mint in self.service.dirty_aths

    def test_process_trade_ath_not_updated_if_lower(self):
        """Verify ATH wird nicht aktualisiert wenn Preis niedriger"""
        mint = "TestCoin123456789012345678901234567890123"
        self._create_watchlist_entry(mint)
        self.service.ath_cache[mint] = 1.0  # Hoher ATH

        trade = {
            "mint": mint,
            "txType": "buy",
            "solAmount": 0.1,
            "vSolInBondingCurve": 0.00001,  # Niedriger Preis
            "vTokensInBondingCurve": 1000000000,
            "traderPublicKey": "Trader1"
        }

        self.service.process_trade(trade)

        assert self.service.ath_cache[mint] == 1.0
        assert mint not in self.service.dirty_aths

    def test_process_trade_zombie_timestamp_update(self, sample_trade_data):
        """Verify Zombie Detection Timestamps werden aktualisiert"""
        mint = sample_trade_data["mint"]
        self._create_watchlist_entry(mint)

        before = time.time()
        self.service.process_trade(sample_trade_data)
        after = time.time()

        assert mint in self.service.last_trade_timestamps
        assert mint in self.service.subscription_watchdog
        assert before <= self.service.last_trade_timestamps[mint] <= after

    def test_process_trade_ignores_unknown_mint(self, sample_trade_data):
        """Verify Trade für unbekannten Mint wird ignoriert"""
        # Keine Watchlist Entry
        self.service.process_trade(sample_trade_data)

        # Keine Änderungen an Datenstrukturen
        assert sample_trade_data["mint"] not in self.service.watchlist

    def test_process_trade_handles_missing_fields(self):
        """Verify graceful Handling von fehlenden Feldern"""
        mint = "TestCoin123456789012345678901234567890123"
        self._create_watchlist_entry(mint)

        malformed_trade = {
            "mint": mint,
            # Fehlendes solAmount, vSolInBondingCurve, etc.
        }

        # Sollte nicht crashen
        self.service.process_trade(malformed_trade)

        # Buffer sollte unverändert sein
        buf = self.service.watchlist[mint]["buffer"]
        assert buf["buys"] == 0
        assert buf["sells"] == 0

    def test_process_trade_handles_invalid_numbers(self):
        """Verify Handling von ungültigen Zahlen"""
        mint = "TestCoin123456789012345678901234567890123"
        self._create_watchlist_entry(mint)

        invalid_trade = {
            "mint": mint,
            "txType": "buy",
            "solAmount": "not_a_number",
            "vSolInBondingCurve": 10.0,
            "vTokensInBondingCurve": 1000000000,
            "traderPublicKey": "Trader1"
        }

        # Sollte nicht crashen
        self.service.process_trade(invalid_trade)

        buf = self.service.watchlist[mint]["buffer"]
        assert buf["buys"] == 0

    def test_process_trade_volume_accumulation(self):
        """Verify Volume wird über mehrere Trades akkumuliert"""
        mint = "TestCoin123456789012345678901234567890123"
        self._create_watchlist_entry(mint)

        for i in range(5):
            trade = {
                "mint": mint,
                "txType": "buy",
                "solAmount": 1.0,
                "vSolInBondingCurve": 10.0,
                "vTokensInBondingCurve": 1000000000,
                "traderPublicKey": f"Trader{i}"
            }
            self.service.process_trade(trade)

        buf = self.service.watchlist[mint]["buffer"]
        assert buf["vol"] == 5.0
        assert buf["vol_buy"] == 5.0
        assert buf["buys"] == 5

    def test_process_trade_max_buy_tracking(self):
        """Verify max_buy trackt den größten Buy"""
        mint = "TestCoin123456789012345678901234567890123"
        self._create_watchlist_entry(mint)

        amounts = [0.5, 2.0, 1.0, 3.0, 0.1]
        for i, amount in enumerate(amounts):
            trade = {
                "mint": mint,
                "txType": "buy",
                "solAmount": amount,
                "vSolInBondingCurve": 10.0,
                "vTokensInBondingCurve": 1000000000,
                "traderPublicKey": f"Trader{i}"
            }
            self.service.process_trade(trade)

        buf = self.service.watchlist[mint]["buffer"]
        assert buf["max_buy"] == 3.0

    def test_process_trade_v_sol_and_mcap_update(self, sample_trade_data):
        """Verify v_sol und mcap werden aktualisiert"""
        mint = sample_trade_data["mint"]
        self._create_watchlist_entry(mint)

        self.service.process_trade(sample_trade_data)

        buf = self.service.watchlist[mint]["buffer"]
        assert buf["v_sol"] == float(sample_trade_data["vSolInBondingCurve"])
        # mcap = price * 1_000_000_000
        expected_price = float(sample_trade_data["vSolInBondingCurve"]) / float(sample_trade_data["vTokensInBondingCurve"])
        assert buf["mcap"] == expected_price * 1_000_000_000
