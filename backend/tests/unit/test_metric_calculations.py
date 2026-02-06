"""
Unit Tests für Metric Calculations
Testet die calculate_advanced_metrics() Methode
"""

import pytest
from unittest.mock import patch, MagicMock


class TestMetricCalculations:
    """Tests für calculate_advanced_metrics() (unified_service.py:1953-1980)"""

    @pytest.fixture(autouse=True)
    def setup_service(self):
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
            yield

    def _create_buffer(self, **overrides):
        """Erstellt einen Test-Buffer mit Standardwerten"""
        default = {
            "open": 0.00001,
            "close": 0.000012,
            "high": 0.000015,
            "low": 0.000008,
            "vol": 10.0,
            "vol_buy": 6.0,
            "vol_sell": 4.0,
            "buys": 100,
            "sells": 50,
            "max_buy": 2.0,
            "max_sell": 1.5,
            "whale_buy_vol": 5.0,
            "whale_sell_vol": 3.0,
            "whale_buys": 3,
            "whale_sells": 2,
            "dev_sold_amount": 0,
            "micro_trades": 5,
            "wallets": {"w1", "w2", "w3", "w4", "w5"},  # 5 unique wallets
            "v_sol": 10.0,
            "mcap": 10000.0
        }
        default.update(overrides)
        return default

    def test_net_volume_calculation(self):
        """Verify net_volume_sol = vol_buy - vol_sell"""
        buf = self._create_buffer(vol_buy=10.0, vol_sell=4.0)

        result = self.service.calculate_advanced_metrics(buf)

        assert result["net_volume_sol"] == 6.0

    def test_net_volume_negative(self):
        """Verify negative net volume wenn mehr Sells"""
        buf = self._create_buffer(vol_buy=3.0, vol_sell=8.0)

        result = self.service.calculate_advanced_metrics(buf)

        assert result["net_volume_sol"] == -5.0

    def test_net_volume_zero(self):
        """Verify zero net volume wenn gleich viel Buy/Sell"""
        buf = self._create_buffer(vol_buy=5.0, vol_sell=5.0)

        result = self.service.calculate_advanced_metrics(buf)

        assert result["net_volume_sol"] == 0.0

    def test_volatility_calculation(self):
        """Verify volatility_pct = ((high - low) / open) * 100"""
        buf = self._create_buffer(
            open=0.00010,
            high=0.00015,  # +50%
            low=0.00005   # -50%
        )

        result = self.service.calculate_advanced_metrics(buf)

        # (0.00015 - 0.00005) / 0.00010 * 100 = 100%
        assert abs(result["volatility_pct"] - 100.0) < 0.0001

    def test_volatility_low_volatility(self):
        """Verify niedrige Volatilität"""
        buf = self._create_buffer(
            open=0.00010,
            high=0.00011,  # +10%
            low=0.00009    # -10%
        )

        result = self.service.calculate_advanced_metrics(buf)

        # (0.00011 - 0.00009) / 0.00010 * 100 = 20%
        assert result["volatility_pct"] == 20.0

    def test_volatility_zero_open_price(self):
        """Verify volatility ist 0 wenn open price 0 ist"""
        buf = self._create_buffer(open=0, high=0.0001, low=0.00005)

        result = self.service.calculate_advanced_metrics(buf)

        assert result["volatility_pct"] == 0.0

    def test_volatility_none_open_price(self):
        """Verify volatility ist 0 wenn open None ist"""
        buf = self._create_buffer(open=None, high=0.0001, low=0.00005)

        result = self.service.calculate_advanced_metrics(buf)

        assert result["volatility_pct"] == 0.0

    def test_avg_trade_size_calculation(self):
        """Verify avg_trade_size_sol = vol / total_trades"""
        buf = self._create_buffer(vol=15.0, buys=10, sells=5)

        result = self.service.calculate_advanced_metrics(buf)

        # 15.0 / (10 + 5) = 1.0
        assert result["avg_trade_size_sol"] == 1.0

    def test_avg_trade_size_zero_trades(self):
        """Verify avg_trade_size ist 0 wenn keine Trades"""
        buf = self._create_buffer(vol=0, buys=0, sells=0)

        result = self.service.calculate_advanced_metrics(buf)

        assert result["avg_trade_size_sol"] == 0.0

    def test_buy_pressure_ratio(self):
        """Verify buy_pressure_ratio = vol_buy / total_volume"""
        buf = self._create_buffer(vol_buy=8.0, vol_sell=2.0)

        result = self.service.calculate_advanced_metrics(buf)

        # 8.0 / (8.0 + 2.0) = 0.8
        assert result["buy_pressure_ratio"] == 0.8

    def test_buy_pressure_ratio_all_buys(self):
        """Verify 100% buy pressure"""
        buf = self._create_buffer(vol_buy=10.0, vol_sell=0.0)

        result = self.service.calculate_advanced_metrics(buf)

        assert result["buy_pressure_ratio"] == 1.0

    def test_buy_pressure_ratio_all_sells(self):
        """Verify 0% buy pressure bei nur Sells"""
        buf = self._create_buffer(vol_buy=0.0, vol_sell=10.0)

        result = self.service.calculate_advanced_metrics(buf)

        assert result["buy_pressure_ratio"] == 0.0

    def test_buy_pressure_ratio_zero_volume(self):
        """Verify buy_pressure_ratio ist 0 bei null Volume"""
        buf = self._create_buffer(vol_buy=0.0, vol_sell=0.0)

        result = self.service.calculate_advanced_metrics(buf)

        assert result["buy_pressure_ratio"] == 0.0

    def test_unique_signer_ratio(self):
        """Verify unique_signer_ratio = unique_wallets / total_trades"""
        buf = self._create_buffer(
            wallets={"w1", "w2", "w3", "w4", "w5"},  # 5 wallets
            buys=8,
            sells=2  # 10 total trades
        )

        result = self.service.calculate_advanced_metrics(buf)

        # 5 / 10 = 0.5
        assert result["unique_signer_ratio"] == 0.5

    def test_unique_signer_ratio_all_unique(self):
        """Verify 100% unique wenn jeder Trade von anderer Wallet"""
        buf = self._create_buffer(
            wallets={"w1", "w2", "w3", "w4", "w5"},  # 5 wallets
            buys=3,
            sells=2  # 5 total trades
        )

        result = self.service.calculate_advanced_metrics(buf)

        # 5 / 5 = 1.0
        assert result["unique_signer_ratio"] == 1.0

    def test_unique_signer_ratio_one_wallet(self):
        """Verify niedrige Ratio wenn nur eine Wallet"""
        buf = self._create_buffer(
            wallets={"single_wallet"},  # 1 wallet
            buys=50,
            sells=50  # 100 total trades
        )

        result = self.service.calculate_advanced_metrics(buf)

        # 1 / 100 = 0.01
        assert result["unique_signer_ratio"] == 0.01

    def test_unique_signer_ratio_zero_trades(self):
        """Verify unique_signer_ratio ist 0 bei null Trades"""
        buf = self._create_buffer(wallets=set(), buys=0, sells=0)

        result = self.service.calculate_advanced_metrics(buf)

        assert result["unique_signer_ratio"] == 0.0

    def test_whale_metrics_passthrough(self):
        """Verify Whale Metriken werden korrekt durchgereicht"""
        buf = self._create_buffer(
            whale_buy_vol=25.0,
            whale_sell_vol=15.0,
            whale_buys=10,
            whale_sells=5
        )

        result = self.service.calculate_advanced_metrics(buf)

        assert result["whale_buy_volume_sol"] == 25.0
        assert result["whale_sell_volume_sol"] == 15.0
        assert result["num_whale_buys"] == 10
        assert result["num_whale_sells"] == 5

    def test_all_metrics_returned(self):
        """Verify alle erwarteten Metriken werden zurückgegeben"""
        buf = self._create_buffer()

        result = self.service.calculate_advanced_metrics(buf)

        expected_keys = [
            "net_volume_sol",
            "volatility_pct",
            "avg_trade_size_sol",
            "whale_buy_volume_sol",
            "whale_sell_volume_sol",
            "num_whale_buys",
            "num_whale_sells",
            "buy_pressure_ratio",
            "unique_signer_ratio"
        ]

        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

    def test_metrics_with_extreme_values(self):
        """Verify Handling extremer Werte"""
        buf = self._create_buffer(
            open=0.0000000001,
            high=0.001,
            low=0.0000000001,
            vol=1000000.0,
            vol_buy=999999.0,
            vol_sell=1.0,
            buys=1000000,
            sells=1,
            wallets=set(f"w{i}" for i in range(10000))
        )

        result = self.service.calculate_advanced_metrics(buf)

        # Sollte keine Fehler werfen
        assert result["volatility_pct"] > 0
        assert result["buy_pressure_ratio"] > 0.99
        assert result["avg_trade_size_sol"] > 0

    def test_metrics_with_floating_point_precision(self):
        """Verify Floating Point Precision wird richtig gehandhabt"""
        buf = self._create_buffer(
            vol_buy=0.1 + 0.1 + 0.1,  # Floating point Probleme
            vol_sell=0.3
        )

        result = self.service.calculate_advanced_metrics(buf)

        # Net volume sollte ~0 sein (nicht exakt wegen Float)
        assert abs(result["net_volume_sol"]) < 0.0000001

    def test_empty_buffer(self):
        """Verify Handling eines leeren Buffers"""
        buf = {
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
            "wallets": set(),
            "v_sol": 0,
            "mcap": 0
        }

        result = self.service.calculate_advanced_metrics(buf)

        assert result["net_volume_sol"] == 0
        assert result["volatility_pct"] == 0
        assert result["avg_trade_size_sol"] == 0
        assert result["buy_pressure_ratio"] == 0
        assert result["unique_signer_ratio"] == 0
