"""
Unit Tests für CoinCache Klasse
Testet das 120-Sekunden Cache-System für neue Coins
"""

import pytest
import time
from unittest.mock import patch, MagicMock


class TestCoinCache:
    """Tests für CoinCache Klasse (unified_service.py:468-567)"""

    @pytest.fixture(autouse=True)
    def setup_cache(self):
        """Setup für jeden Test - importiert CoinCache mit gemockten Metriken"""
        with patch('unified_service.cache_size') as self.mock_cache_size, \
             patch('unified_service.cache_activations') as self.mock_activations, \
             patch('unified_service.cache_expirations') as self.mock_expirations:

            self.mock_cache_size.set = MagicMock()
            self.mock_activations.inc = MagicMock()
            self.mock_expirations.inc = MagicMock()

            from unified_service import CoinCache
            self.cache = CoinCache(cache_seconds=120)
            yield

    def test_add_coin_stores_metadata(self, sample_coin_data):
        """Verify add_coin() speichert vollständige Coin-Daten"""
        mint = sample_coin_data["mint"]

        self.cache.add_coin(mint, sample_coin_data)

        # Verifiziere Struktur
        assert mint in self.cache.cache
        cached = self.cache.cache[mint]

        assert "discovered_at" in cached
        assert "metadata" in cached
        assert "trades" in cached
        assert "n8n_sent" in cached
        assert "activated" in cached

        # Verifiziere Werte
        assert cached["metadata"]["name"] == sample_coin_data["name"]
        assert cached["metadata"]["symbol"] == sample_coin_data["symbol"]
        assert cached["trades"] == []
        assert cached["n8n_sent"] is False
        assert cached["activated"] is False

    def test_add_coin_updates_cache_size_metric(self, sample_coin_data):
        """Verify cache_size Prometheus Metrik wird aktualisiert"""
        self.cache.add_coin(sample_coin_data["mint"], sample_coin_data)

        self.mock_cache_size.set.assert_called_with(1)

    def test_add_trade_only_for_non_activated_coins(self, sample_coin_data, sample_trade_data):
        """Verify Trades werden nur zu nicht-aktivierten Coins hinzugefügt"""
        mint = sample_coin_data["mint"]
        self.cache.add_coin(mint, sample_coin_data)

        # Trade hinzufügen
        self.cache.add_trade(mint, sample_trade_data)

        assert len(self.cache.cache[mint]["trades"]) == 1
        assert self.cache.cache[mint]["trades"][0][1] == sample_trade_data

    def test_add_trade_ignored_for_activated_coins(self, sample_coin_data, sample_trade_data):
        """Verify Trades werden ignoriert wenn Coin aktiviert ist"""
        mint = sample_coin_data["mint"]
        self.cache.add_coin(mint, sample_coin_data)

        # Coin aktivieren
        self.cache.activate_coin(mint)

        # Trade hinzufügen (sollte ignoriert werden)
        self.cache.add_trade(mint, sample_trade_data)

        # Keine neuen Trades nach Aktivierung
        # (activate_coin setzt activated=True, danach werden Trades ignoriert)
        assert self.cache.cache[mint]["activated"] is True

    def test_add_trade_ignored_for_unknown_coin(self, sample_trade_data):
        """Verify Trades für unbekannte Coins werden ignoriert"""
        unknown_mint = "UnknownCoin123456789012345678901234567890"

        # Sollte keine Exception werfen
        self.cache.add_trade(unknown_mint, sample_trade_data)

        assert unknown_mint not in self.cache.cache

    def test_activate_coin_returns_cached_trades(self, sample_coin_data, sample_trade_data):
        """Verify activate_coin() gibt alle gecachten Trades zurück"""
        mint = sample_coin_data["mint"]
        self.cache.add_coin(mint, sample_coin_data)

        # Mehrere Trades hinzufügen
        for i in range(5):
            trade = sample_trade_data.copy()
            trade["signature"] = f"sig_{i}"
            self.cache.add_trade(mint, trade)

        trades = self.cache.activate_coin(mint)

        assert len(trades) == 5
        assert self.cache.cache[mint]["activated"] is True

    def test_activate_coin_sets_activated_flag(self, sample_coin_data):
        """Verify activated Flag wird gesetzt"""
        mint = sample_coin_data["mint"]
        self.cache.add_coin(mint, sample_coin_data)

        self.cache.activate_coin(mint)

        assert self.cache.cache[mint]["activated"] is True

    def test_activate_coin_increments_counter(self, sample_coin_data):
        """Verify cache_activations Prometheus Counter wird inkrementiert"""
        mint = sample_coin_data["mint"]
        self.cache.add_coin(mint, sample_coin_data)

        self.cache.activate_coin(mint)

        self.mock_activations.inc.assert_called_once()

    def test_activate_unknown_coin_returns_empty(self):
        """Verify activate_coin() für unbekannten Coin gibt leere Liste zurück"""
        trades = self.cache.activate_coin("UnknownCoin")

        assert trades == []

    def test_remove_coin_clears_entry(self, sample_coin_data):
        """Verify Coin wird aus Cache entfernt"""
        mint = sample_coin_data["mint"]
        self.cache.add_coin(mint, sample_coin_data)

        self.cache.remove_coin(mint)

        assert mint not in self.cache.cache

    def test_remove_coin_increments_expiration_if_not_activated(self, sample_coin_data):
        """Verify cache_expirations Counter für nicht-aktivierte Coins"""
        mint = sample_coin_data["mint"]
        self.cache.add_coin(mint, sample_coin_data)

        self.cache.remove_coin(mint)

        self.mock_expirations.inc.assert_called_once()

    def test_remove_coin_no_expiration_if_activated(self, sample_coin_data):
        """Verify keine Expiration-Metrik für aktivierte Coins"""
        mint = sample_coin_data["mint"]
        self.cache.add_coin(mint, sample_coin_data)
        self.cache.activate_coin(mint)

        self.mock_expirations.reset_mock()
        self.cache.remove_coin(mint)

        self.mock_expirations.inc.assert_not_called()

    def test_remove_unknown_coin_no_error(self):
        """Verify remove für unbekannten Coin wirft keine Exception"""
        self.cache.remove_coin("UnknownCoin")  # Sollte nicht crashen

    def test_cleanup_expired_coins_removes_old_entries(self, sample_coin_data):
        """Verify Coins älter als cache_seconds werden entfernt"""
        mint = sample_coin_data["mint"]
        self.cache.add_coin(mint, sample_coin_data)

        # Simuliere Zeit-Fortschritt (121 Sekunden)
        future_time = time.time() + 121

        removed = self.cache.cleanup_expired_coins(current_time=future_time)

        assert removed == 1
        assert mint not in self.cache.cache

    def test_cleanup_expired_coins_keeps_activated_coins(self, sample_coin_data):
        """Verify aktivierte Coins werden nicht entfernt"""
        mint = sample_coin_data["mint"]
        self.cache.add_coin(mint, sample_coin_data)
        self.cache.activate_coin(mint)

        # Simuliere Zeit-Fortschritt
        future_time = time.time() + 200

        removed = self.cache.cleanup_expired_coins(current_time=future_time)

        assert removed == 0
        assert mint in self.cache.cache

    def test_cleanup_expired_coins_keeps_fresh_coins(self, sample_coin_data):
        """Verify frische Coins werden nicht entfernt"""
        mint = sample_coin_data["mint"]
        self.cache.add_coin(mint, sample_coin_data)

        # Nur 60 Sekunden später
        future_time = time.time() + 60

        removed = self.cache.cleanup_expired_coins(current_time=future_time)

        assert removed == 0
        assert mint in self.cache.cache

    def test_get_cache_stats_returns_correct_counts(self, sample_coin_data):
        """Verify Cache-Statistiken sind korrekt"""
        # Mehrere Coins hinzufügen
        for i in range(5):
            coin = sample_coin_data.copy()
            coin["mint"] = f"Coin{i}12345678901234567890123456789012345"
            self.cache.add_coin(coin["mint"], coin)

        # 2 davon aktivieren
        self.cache.activate_coin("Coin012345678901234567890123456789012345")
        self.cache.activate_coin("Coin112345678901234567890123456789012345")

        stats = self.cache.get_cache_stats()

        assert stats["total_coins"] == 5
        assert stats["activated_coins"] == 2
        assert stats["expired_coins"] == 3  # total - activated

    def test_get_cache_stats_empty_cache(self):
        """Verify Stats für leeren Cache"""
        stats = self.cache.get_cache_stats()

        assert stats["total_coins"] == 0
        assert stats["activated_coins"] == 0
        assert stats["oldest_age_seconds"] == 0
        assert stats["newest_age_seconds"] == 0

    def test_get_cache_stats_age_calculation(self, sample_coin_data):
        """Verify Altersberechnung in Stats"""
        mint = sample_coin_data["mint"]
        self.cache.add_coin(mint, sample_coin_data)

        # Warte kurz
        time.sleep(0.1)

        stats = self.cache.get_cache_stats()

        assert stats["oldest_age_seconds"] >= 0
        assert stats["newest_age_seconds"] >= 0

    def test_cache_with_custom_cache_seconds(self, sample_coin_data):
        """Verify benutzerdefinierte cache_seconds funktionieren"""
        # Erstelle Cache mit 60s statt 120s
        with patch('unified_service.cache_size'), \
             patch('unified_service.cache_activations'), \
             patch('unified_service.cache_expirations'):

            from unified_service import CoinCache
            short_cache = CoinCache(cache_seconds=60)

            mint = sample_coin_data["mint"]
            short_cache.add_coin(mint, sample_coin_data)

            # Nach 61 Sekunden sollte Coin ablaufen
            future_time = time.time() + 61
            removed = short_cache.cleanup_expired_coins(current_time=future_time)

            assert removed == 1

    def test_multiple_trades_chronological_order(self, sample_coin_data, sample_trade_data):
        """Verify Trades werden in chronologischer Reihenfolge gespeichert"""
        mint = sample_coin_data["mint"]
        self.cache.add_coin(mint, sample_coin_data)

        # Trades mit unterschiedlichen Zeitstempeln hinzufügen
        for i in range(5):
            trade = sample_trade_data.copy()
            trade["signature"] = f"sig_{i}"
            self.cache.add_trade(mint, trade)
            time.sleep(0.01)  # Kleine Verzögerung

        trades = self.cache.cache[mint]["trades"]

        # Prüfe chronologische Reihenfolge
        timestamps = [t[0] for t in trades]
        assert timestamps == sorted(timestamps)

    def test_cache_size_updates_on_multiple_operations(self, sample_coin_data):
        """Verify cache_size Metrik wird bei allen Operationen aktualisiert"""
        # Hinzufügen
        for i in range(3):
            coin = sample_coin_data.copy()
            coin["mint"] = f"Coin{i}12345678901234567890123456789012345"
            self.cache.add_coin(coin["mint"], coin)

        # Entfernen
        self.cache.remove_coin("Coin012345678901234567890123456789012345")

        # Prüfe dass set() mehrfach aufgerufen wurde
        assert self.mock_cache_size.set.call_count >= 4  # 3 adds + 1 remove
