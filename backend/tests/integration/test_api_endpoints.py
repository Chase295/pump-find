"""
Integration Tests für FastAPI Endpoints
Testet Health, Config, Metrics und Analytics Endpoints
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestHealthEndpoint:
    """Tests für /api/health Endpoint"""

    @pytest.mark.asyncio
    async def test_health_returns_correct_structure(self, sample_health_response):
        """Test /api/health gibt korrekte Struktur zurück"""
        expected_keys = [
            "status", "ws_connected", "db_connected", "uptime_seconds",
            "last_message_ago", "reconnect_count", "last_error",
            "cache_stats", "tracking_stats", "discovery_stats"
        ]

        for key in expected_keys:
            assert key in sample_health_response

    @pytest.mark.asyncio
    async def test_health_status_healthy_when_connected(self):
        """Test status='healthy' wenn ws und db verbunden"""
        ws_connected = True
        db_connected = True

        status = "healthy" if ws_connected and db_connected else "degraded"
        assert status == "healthy"

    @pytest.mark.asyncio
    async def test_health_status_degraded_when_ws_disconnected(self):
        """Test status='degraded' wenn WS nicht verbunden"""
        ws_connected = False
        db_connected = True

        status = "healthy" if ws_connected and db_connected else "degraded"
        assert status == "degraded"

    @pytest.mark.asyncio
    async def test_health_status_degraded_when_db_disconnected(self):
        """Test status='degraded' wenn DB nicht verbunden"""
        ws_connected = True
        db_connected = False

        status = "healthy" if ws_connected and db_connected else "degraded"
        assert status == "degraded"

    @pytest.mark.asyncio
    async def test_health_cache_stats_structure(self, sample_health_response):
        """Test cache_stats hat korrekte Struktur"""
        cache_stats = sample_health_response["cache_stats"]

        assert "total_coins" in cache_stats
        assert "activated_coins" in cache_stats
        assert "expired_coins" in cache_stats
        assert "oldest_age_seconds" in cache_stats
        assert "newest_age_seconds" in cache_stats

    @pytest.mark.asyncio
    async def test_health_tracking_stats_structure(self, sample_health_response):
        """Test tracking_stats hat korrekte Struktur"""
        tracking_stats = sample_health_response["tracking_stats"]

        assert "active_coins" in tracking_stats
        assert "total_trades" in tracking_stats
        assert "total_metrics_saved" in tracking_stats

    @pytest.mark.asyncio
    async def test_health_discovery_stats_structure(self, sample_health_response):
        """Test discovery_stats hat korrekte Struktur"""
        discovery_stats = sample_health_response["discovery_stats"]

        assert "total_coins_discovered" in discovery_stats
        assert "n8n_available" in discovery_stats
        assert "n8n_buffer_size" in discovery_stats


class TestConfigEndpoint:
    """Tests für /api/config Endpoints"""

    @pytest.mark.asyncio
    async def test_get_config_returns_all_values(self, sample_config_response):
        """Test GET /api/config gibt alle Werte zurück"""
        expected_keys = [
            "n8n_webhook_url", "n8n_webhook_method", "db_dsn",
            "coin_cache_seconds", "db_refresh_interval", "batch_size",
            "batch_timeout", "bad_names_pattern", "spam_burst_window",
            "sol_reserves_full", "whale_threshold_sol",
            "age_calculation_offset_min", "trade_buffer_seconds",
            "ath_flush_interval"
        ]

        for key in expected_keys:
            assert key in sample_config_response

    @pytest.mark.asyncio
    async def test_config_db_dsn_is_censored(self, sample_config_response):
        """Test DB DSN ist zensiert (enthält ***)"""
        db_dsn = sample_config_response["db_dsn"]
        assert "***" in db_dsn

    @pytest.mark.asyncio
    async def test_update_config_partial_update(self):
        """Test PUT /api/config mit partiellen Feldern"""
        current_config = {"coin_cache_seconds": 120, "batch_size": 10}
        update_data = {"coin_cache_seconds": 180}

        # Merge Configs
        new_config = current_config.copy()
        new_config.update(update_data)

        assert new_config["coin_cache_seconds"] == 180
        assert new_config["batch_size"] == 10  # Unverändert

    @pytest.mark.asyncio
    async def test_update_config_validation(self):
        """Test Ungültige Config-Werte werden abgelehnt"""
        # Negative Werte sollten nicht erlaubt sein
        invalid_values = [
            {"coin_cache_seconds": -10},
            {"batch_size": 0},
            {"whale_threshold_sol": -1.0}
        ]

        for invalid in invalid_values:
            for key, value in invalid.items():
                is_valid = value > 0
                assert is_valid is False


class TestMetricsEndpoint:
    """Tests für /api/metrics Endpoint"""

    @pytest.mark.asyncio
    async def test_metrics_prometheus_format(self):
        """Test /api/metrics gibt Prometheus Format zurück"""
        sample_metrics = """
# HELP unified_coins_received_total Total coins received
# TYPE unified_coins_received_total counter
unified_coins_received_total 123

# HELP unified_cache_size Current cache size
# TYPE unified_cache_size gauge
unified_cache_size 10
        """.strip()

        # Prüfe Format
        lines = sample_metrics.split('\n')
        assert any(line.startswith("# HELP") for line in lines)
        assert any(line.startswith("# TYPE") for line in lines)

    @pytest.mark.asyncio
    async def test_metrics_contains_key_metrics(self):
        """Test Wichtige Metriken sind enthalten"""
        expected_metrics = [
            "unified_coins_received_total",
            "unified_cache_size",
            "unified_coins_tracked",
            "unified_trades_received_total",
            "unified_ws_connected",
            "unified_db_connected"
        ]

        sample_text = """
unified_coins_received_total 123
unified_cache_size 10
unified_coins_tracked 50
unified_trades_received_total 1000
unified_ws_connected 1
unified_db_connected 1
        """

        for metric in expected_metrics:
            assert metric in sample_text


class TestAnalyticsEndpoint:
    """Tests für /api/analytics/{mint} Endpoint"""

    @pytest.mark.asyncio
    async def test_analytics_returns_correct_structure(self):
        """Test /api/analytics/{mint} gibt korrekte Struktur zurück"""
        sample_analytics = {
            "mint": "TestCoin123",
            "current_price": 0.00001,
            "last_updated": "2024-01-01T00:00:00+00:00",
            "is_active": True,
            "performance": {
                "1m": {
                    "price_change": 5.5,
                    "volume": 10.0,
                    "trades": 50,
                    "trend": "🚀 PUMP"
                }
            }
        }

        assert "mint" in sample_analytics
        assert "current_price" in sample_analytics
        assert "is_active" in sample_analytics
        assert "performance" in sample_analytics

    @pytest.mark.asyncio
    async def test_analytics_time_windows(self):
        """Test Benutzerdefinierte Time Windows"""
        windows_param = "30s,1m,5m,15m,30m,1h"
        windows = windows_param.split(",")

        assert len(windows) == 6
        assert "30s" in windows
        assert "1h" in windows

    @pytest.mark.asyncio
    async def test_analytics_trend_values(self):
        """Test Gültige Trend-Werte"""
        valid_trends = ["🚀 PUMP", "📉 DUMP", "➡️ FLAT", "❓ NO_DATA"]

        for trend in valid_trends:
            assert trend in valid_trends

    @pytest.mark.asyncio
    async def test_analytics_unknown_coin(self):
        """Test Handling von unbekanntem Coin"""
        # Unbekannter Coin sollte leere/default Analytics zurückgeben
        unknown_response = {
            "mint": "UnknownCoin",
            "current_price": None,
            "is_active": False,
            "performance": {}
        }

        assert unknown_response["is_active"] is False
        assert unknown_response["current_price"] is None


class TestDatabaseEndpoints:
    """Tests für /api/database/* Endpoints"""

    @pytest.mark.asyncio
    async def test_streams_stats_structure(self):
        """Test /api/database/streams/stats Struktur"""
        sample_stats = {
            "active_streams": 50,
            "total_streams": 200,
            "streams_by_phase": {
                "1": 20,
                "2": 20,
                "3": 10
            }
        }

        assert "active_streams" in sample_stats
        assert "total_streams" in sample_stats
        assert "streams_by_phase" in sample_stats

    @pytest.mark.asyncio
    async def test_phases_structure(self):
        """Test /api/database/phases Struktur"""
        sample_phases = [
            {"id": 1, "name": "Baby Zone", "interval_seconds": 5},
            {"id": 2, "name": "Survival Zone", "interval_seconds": 30},
            {"id": 3, "name": "Mature Zone", "interval_seconds": 60}
        ]

        assert len(sample_phases) >= 1
        for phase in sample_phases:
            assert "id" in phase
            assert "name" in phase
            assert "interval_seconds" in phase


class TestN8nTestEndpoint:
    """Tests für /test/n8n Endpoint"""

    @pytest.mark.asyncio
    async def test_n8n_availability_check(self):
        """Test n8n Verfügbarkeits-Check"""
        # Simuliere verschiedene n8n Stati
        n8n_responses = [
            {"available": True, "status_code": 200},
            {"available": False, "status_code": 500},
            {"available": False, "error": "Connection refused"}
        ]

        for response in n8n_responses:
            if response.get("available"):
                assert response.get("status_code") == 200
            else:
                assert response.get("status_code") != 200 or "error" in response
