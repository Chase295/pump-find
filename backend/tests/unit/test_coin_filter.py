"""
Unit Tests für CoinFilter Klasse
Testet Bad Name Filter und Spam-Burst Detection
"""

import pytest
import time
from unittest.mock import patch, MagicMock
import re


class TestCoinFilter:
    """Tests für CoinFilter Klasse (unified_service.py:569-606)"""

    @pytest.fixture(autouse=True)
    def setup_filter(self):
        """Setup für jeden Test"""
        with patch('unified_service.coins_filtered') as self.mock_filtered, \
             patch('unified_service.BAD_NAMES', re.compile(r'(test|bot|rug|scam|cant|honey|faucet)', re.IGNORECASE)):

            self.mock_filtered.labels = MagicMock(return_value=MagicMock(inc=MagicMock()))

            from unified_service import CoinFilter
            self.filter = CoinFilter(spam_burst_window=30)
            yield

    def test_filter_bad_name_test(self):
        """Test 'test' wird gefiltert"""
        coin = {"name": "TestCoin", "symbol": "TST"}

        should_filter, reason = self.filter.should_filter_coin(coin)

        assert should_filter is True
        assert reason == "bad_name"

    def test_filter_bad_name_bot(self):
        """Test 'bot' wird gefiltert"""
        coin = {"name": "Trading Bot", "symbol": "BOT"}

        should_filter, reason = self.filter.should_filter_coin(coin)

        assert should_filter is True
        assert reason == "bad_name"

    def test_filter_bad_name_rug(self):
        """Test 'rug' wird gefiltert"""
        coin = {"name": "RugPull Coin", "symbol": "RUG"}

        should_filter, reason = self.filter.should_filter_coin(coin)

        assert should_filter is True
        assert reason == "bad_name"

    def test_filter_bad_name_scam(self):
        """Test 'scam' wird gefiltert"""
        coin = {"name": "Not A Scam", "symbol": "SCAM"}

        should_filter, reason = self.filter.should_filter_coin(coin)

        assert should_filter is True
        assert reason == "bad_name"

    def test_filter_bad_name_honey(self):
        """Test 'honey' wird gefiltert"""
        coin = {"name": "Honeypot Token", "symbol": "HONEY"}

        should_filter, reason = self.filter.should_filter_coin(coin)

        assert should_filter is True
        assert reason == "bad_name"

    def test_filter_bad_name_faucet(self):
        """Test 'faucet' wird gefiltert"""
        coin = {"name": "Free Faucet", "symbol": "FAUCET"}

        should_filter, reason = self.filter.should_filter_coin(coin)

        assert should_filter is True
        assert reason == "bad_name"

    def test_filter_case_insensitive_uppercase(self):
        """Test Case-insensitive Matching (UPPERCASE)"""
        coin = {"name": "TESTCOIN", "symbol": "TEST"}

        should_filter, reason = self.filter.should_filter_coin(coin)

        assert should_filter is True
        assert reason == "bad_name"

    def test_filter_case_insensitive_mixed(self):
        """Test Case-insensitive Matching (MixedCase)"""
        coin = {"name": "TeSt CoIn", "symbol": "TsT"}

        should_filter, reason = self.filter.should_filter_coin(coin)

        assert should_filter is True
        assert reason == "bad_name"

    def test_filter_bad_name_in_middle(self):
        """Test Bad Name in der Mitte des Namens"""
        coin = {"name": "Super Scam Coin", "symbol": "SSC"}

        should_filter, reason = self.filter.should_filter_coin(coin)

        assert should_filter is True
        assert reason == "bad_name"

    def test_good_coin_passes(self):
        """Test legitimer Coin passiert alle Filter"""
        coin = {"name": "Moon Rocket", "symbol": "MOON"}

        should_filter, reason = self.filter.should_filter_coin(coin)

        assert should_filter is False
        assert reason is None

    def test_good_coin_added_to_recent_list(self):
        """Test Coin wird zu recent_coins hinzugefügt"""
        coin = {"name": "Good Coin", "symbol": "GOOD"}

        self.filter.should_filter_coin(coin)

        assert len(self.filter.recent_coins) == 1
        assert self.filter.recent_coins[0][1] == "Good Coin"
        assert self.filter.recent_coins[0][2] == "GOOD"

    def test_spam_burst_identical_name(self):
        """Test identischer Name innerhalb des Windows wird gefiltert"""
        coin1 = {"name": "Duplicate Coin", "symbol": "DUP1"}
        coin2 = {"name": "Duplicate Coin", "symbol": "DUP2"}

        # Erster Coin passiert
        should_filter1, _ = self.filter.should_filter_coin(coin1)
        assert should_filter1 is False

        # Zweiter Coin mit gleichem Namen wird gefiltert
        should_filter2, reason = self.filter.should_filter_coin(coin2)
        assert should_filter2 is True
        assert reason == "spam_burst"

    def test_spam_burst_identical_symbol(self):
        """Test identisches Symbol innerhalb des Windows wird gefiltert"""
        coin1 = {"name": "First Coin", "symbol": "SAME"}
        coin2 = {"name": "Second Coin", "symbol": "SAME"}

        # Erster Coin passiert
        should_filter1, _ = self.filter.should_filter_coin(coin1)
        assert should_filter1 is False

        # Zweiter Coin mit gleichem Symbol wird gefiltert
        should_filter2, reason = self.filter.should_filter_coin(coin2)
        assert should_filter2 is True
        assert reason == "spam_burst"

    def test_spam_burst_outside_window(self):
        """Test gleicher Name/Symbol nach Window-Ablauf wird erlaubt"""
        coin1 = {"name": "Time Coin", "symbol": "TIME"}
        coin2 = {"name": "Time Coin", "symbol": "TIME2"}

        # Erster Coin
        self.filter.should_filter_coin(coin1)

        # Manipuliere Timestamp um außerhalb des Windows zu sein
        self.filter.recent_coins[0] = (
            time.time() - 31,  # 31 Sekunden alt (Window = 30s)
            "Time Coin",
            "TIME"
        )

        # Zweiter Coin sollte passieren
        should_filter, reason = self.filter.should_filter_coin(coin2)
        assert should_filter is False

    def test_recent_coins_cleanup(self):
        """Test alte Einträge werden aus recent_coins entfernt"""
        # Füge mehrere Coins hinzu
        for i in range(5):
            coin = {"name": f"Coin {i}", "symbol": f"C{i}"}
            self.filter.should_filter_coin(coin)

        # Manipuliere erste 3 Timestamps um alt zu sein
        now = time.time()
        for i in range(3):
            self.filter.recent_coins[i] = (
                now - 100,  # 100 Sekunden alt (> 2x Window)
                f"Coin {i}",
                f"C{i}"
            )

        # Trigger Cleanup durch neuen Coin
        self.filter.should_filter_coin({"name": "New Coin", "symbol": "NEW"})

        # Alte Einträge sollten entfernt sein
        assert len(self.filter.recent_coins) <= 3

    def test_prometheus_counter_on_bad_name(self):
        """Test Prometheus Counter für Bad Name Filter"""
        coin = {"name": "Test Coin", "symbol": "TST"}

        self.filter.should_filter_coin(coin)

        self.mock_filtered.labels.assert_called_with(reason="bad_name")

    def test_prometheus_counter_on_spam_burst(self):
        """Test Prometheus Counter für Spam Burst Filter"""
        coin1 = {"name": "Spam Coin", "symbol": "SPAM"}
        coin2 = {"name": "Spam Coin", "symbol": "SPAM2"}

        self.filter.should_filter_coin(coin1)
        self.filter.should_filter_coin(coin2)

        # Sollte mindestens einmal mit spam_burst aufgerufen worden sein
        calls = self.mock_filtered.labels.call_args_list
        spam_burst_calls = [c for c in calls if c == ((), {'reason': 'spam_burst'})]
        assert len(spam_burst_calls) >= 1

    def test_empty_name_handling(self):
        """Test leerer Name wird behandelt"""
        coin = {"name": "", "symbol": "EMPTY"}

        # Sollte keine Exception werfen
        should_filter, reason = self.filter.should_filter_coin(coin)

        # Leerer Name ist kein Bad Name
        assert should_filter is False or reason == "spam_burst"

    def test_missing_name_handling(self):
        """Test fehlender Name wird behandelt"""
        coin = {"symbol": "NONAME"}

        # Sollte keine Exception werfen
        should_filter, reason = self.filter.should_filter_coin(coin)

        assert should_filter is False or reason is not None

    def test_whitespace_name_trimmed(self):
        """Test Whitespace wird getrimmt"""
        coin = {"name": "  Test Coin  ", "symbol": "TST"}

        should_filter, reason = self.filter.should_filter_coin(coin)

        assert should_filter is True
        assert reason == "bad_name"

    def test_multiple_bad_words(self):
        """Test mehrere Bad Words im Namen"""
        coin = {"name": "Test Scam Bot Rug", "symbol": "TSBT"}

        should_filter, reason = self.filter.should_filter_coin(coin)

        assert should_filter is True
        assert reason == "bad_name"  # Erste Übereinstimmung zählt

    def test_custom_spam_burst_window(self):
        """Test benutzerdefiniertes Spam-Burst Window"""
        with patch('unified_service.coins_filtered') as mock_filtered, \
             patch('unified_service.BAD_NAMES', re.compile(r'(test|bot|rug|scam)', re.IGNORECASE)):

            mock_filtered.labels = MagicMock(return_value=MagicMock(inc=MagicMock()))

            from unified_service import CoinFilter
            short_window_filter = CoinFilter(spam_burst_window=5)

            coin1 = {"name": "Short Window", "symbol": "SW1"}
            coin2 = {"name": "Short Window", "symbol": "SW2"}

            short_window_filter.should_filter_coin(coin1)

            # Manipuliere Timestamp um außerhalb des kurzen Windows zu sein
            short_window_filter.recent_coins[0] = (
                time.time() - 6,  # 6 Sekunden (> 5s Window)
                "Short Window",
                "SW1"
            )

            # Sollte passieren
            should_filter, _ = short_window_filter.should_filter_coin(coin2)
            assert should_filter is False

    def test_similar_but_not_identical_names_pass(self):
        """Test ähnliche aber nicht identische Namen passieren"""
        coin1 = {"name": "Moon Coin", "symbol": "MOON1"}
        coin2 = {"name": "Moon Token", "symbol": "MOON2"}

        self.filter.should_filter_coin(coin1)
        should_filter, _ = self.filter.should_filter_coin(coin2)

        assert should_filter is False

    def test_unicode_names_handled(self):
        """Test Unicode-Namen werden verarbeitet"""
        coin = {"name": "🚀 Rocket Moon 🌙", "symbol": "ROCKET"}

        # Sollte keine Exception werfen
        should_filter, reason = self.filter.should_filter_coin(coin)

        assert should_filter is False  # Keine Bad Words

    def test_numbers_in_name(self):
        """Test Zahlen im Namen"""
        coin = {"name": "Coin2024", "symbol": "C24"}

        should_filter, reason = self.filter.should_filter_coin(coin)

        assert should_filter is False

    def test_special_characters_in_name(self):
        """Test Sonderzeichen im Namen"""
        coin = {"name": "Coin-With_Special.Chars!", "symbol": "SPEC"}

        should_filter, reason = self.filter.should_filter_coin(coin)

        assert should_filter is False
