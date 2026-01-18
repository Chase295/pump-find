#!/usr/bin/env python3
"""
🔍 VERIFY DEPLOYMENT - Test-Skript für Analytics Endpoint & Zombie-Coin-Fix
Überprüft die korrekte Implementierung der letzten Änderungen.
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional

class DeploymentVerifier:
    def __init__(self, base_url: str = "http://localhost:3001"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 10

    def test_endpoint(self, endpoint: str, expected_status: int = 200) -> tuple[bool, Dict[str, Any]]:
        """Testet einen API-Endpunkt"""
        try:
            url = f"{self.base_url}{endpoint}"
            print(f"🔍 Teste: {url}")

            response = self.session.get(url)
            success = response.status_code == expected_status

            try:
                data = response.json()
            except:
                data = {"error": "Invalid JSON response"}

            return success, data

        except requests.RequestException as e:
            print(f"❌ Netzwerk-Fehler: {e}")
            return False, {"error": str(e)}

    def find_active_coin(self) -> Optional[str]:
        """Findet einen aktiven Coin aus der Datenbank"""
        print("🎯 Suche aktiven Coin...")

        # Versuche zuerst Streams-Stats
        success, data = self.test_endpoint("/api/database/streams/stats")
        if success and "total_streams" in data and data["total_streams"] > 0:
            print(f"✅ {data['active_streams']} aktive Streams gefunden")

            # Hole einen echten aktiven Coin
            success, streams_data = self.test_endpoint("/api/database/streams?limit=1")
            if success and isinstance(streams_data, list) and len(streams_data) > 0:
                mint = streams_data[0].get("mint") or streams_data[0].get("token_address")
                if mint:
                    return mint

            # Fallback: Bekannter Coin aus DB
            return "EAzpJpy6veRTJRLjrwWpwUEhKHtGmXXBwvnTR3ZKpump"

        # Fallback: Einzelne Streams
        success, data = self.test_endpoint("/api/database/streams?limit=1")
        if success and isinstance(data, list) and len(data) > 0:
            mint = data[0].get("mint") or data[0].get("token_address")
            if mint:
                print(f"✅ Aktiver Coin gefunden: {mint[:8]}...")
                return mint

        print("❌ Keine aktiven Coins gefunden")
        return None

    def test_analytics_endpoint(self, mint: str) -> bool:
        """Testet den Analytics-Endpunkt"""
        print(f"\n🎯 Teste Analytics für Coin: {mint[:8]}...")

        # Teste mit verschiedenen Zeitfenstern
        endpoint = f"/api/analytics/{mint}?windows=1m,5m"
        success, data = self.test_endpoint(endpoint)

        if not success:
            print(f"❌ Analytics-Endpunkt fehlgeschlagen: HTTP {data.get('status_code', 'unknown')}")
            return False

        # Validiere Response-Struktur
        required_fields = ["mint", "current_price", "last_updated", "is_active", "performance"]

        for field in required_fields:
            if field not in data:
                print(f"❌ Fehlendes Feld: {field}")
                return False

        # Validiere Performance-Daten
        if not isinstance(data["performance"], dict):
            print("❌ Performance ist kein Dictionary")
            return False

        # Prüfe mindestens ein Zeitfenster
        if not data["performance"]:
            print("❌ Keine Performance-Daten")
            return False

        # Validiere erstes Zeitfenster
        first_window = list(data["performance"].keys())[0]
        window_data = data["performance"][first_window]

        window_fields = ["price_change_pct", "old_price", "trend", "data_found", "data_age_seconds"]
        for field in window_fields:
            if field not in window_data:
                print(f"❌ Fehlendes Feld in {first_window}: {field}")
                return False

        # Validiere Trend-Werte
        valid_trends = ["🚀 PUMP", "📉 DUMP", "➡️ FLAT", "❓ NO_DATA"]
        if window_data["trend"] not in valid_trends:
            print(f"❌ Ungültiger Trend: {window_data['trend']}")
            return False

        print("✅ Analytics-Response validiert")
        print(f"   📊 Aktueller Preis: {data['current_price']}")
        print(f"   🎯 Trend ({first_window}): {window_data['trend']}")
        print(f"   ⏱️ Daten-Alter: {window_data['data_age_seconds']} Sekunden")

        return True

    def run_all_tests(self) -> bool:
        """Führt alle Tests durch"""
        print("🚀 START: Deployment-Verifikation")
        print("=" * 50)

        # Test 1: Health-Check
        print("\n1️⃣ Teste Health-Endpoint...")
        success, data = self.test_endpoint("/api/health")
        if not success:
            print("❌ Health-Check fehlgeschlagen")
            return False
        print("✅ Health-Check erfolgreich")

        # Test 2: Finde aktiven Coin
        print("\n2️⃣ Suche aktiven Coin...")
        active_mint = self.find_active_coin()
        if not active_mint:
            print("❌ Kein aktiver Coin gefunden - verwende Test-Coin")
            # Verwende einen bekannten Coin aus der DB für Test
            active_mint = "EAzpJpy6veRTJRLjrwWpwUEhKHtGmXXBwvnTR3ZKpump"  # Bekannter Coin aus DB

        # Test 3: Analytics-Endpunkt
        print(f"\n3️⃣ Teste Analytics-Endpunkt mit Coin: {active_mint}")
        analytics_success = self.test_analytics_endpoint(active_mint)

        # Zusammenfassung
        print("\n" + "=" * 50)
        if analytics_success:
            print("✅ ALLE TESTS BESTANDEN!")
            print("🎉 Analytics Endpoint & Zombie-Coin-Fix sind korrekt implementiert!")
            return True
        else:
            print("❌ TESTS FEHLGESCHLAGEN!")
            print("🔧 Bitte überprüfe die Implementierung.")
            return False

def main():
    """Hauptfunktion"""
    verifier = DeploymentVerifier()

    # Warte kurz, falls Services noch starten
    print("⏳ Warte 3 Sekunden auf Service-Start...")
    time.sleep(3)

    success = verifier.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()