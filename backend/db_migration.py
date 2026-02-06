"""
Database migration utilities for Pump Find
"""

import asyncpg
import os

async def check_and_create_schema(pool: asyncpg.Pool):
    """
    Erstellt die notwendigen Tabellen und Views für Pump Find
    """
    try:
        # Lade Schema-Dateien
        schema_dir = "/app/sql"

        # Erstelle discovered_coins Tabelle
        schema_path = os.path.join(schema_dir, "schema.sql")
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                schema_sql = f.read()

            async with pool.acquire() as conn:
                await conn.execute(schema_sql)
                print("✅ discovered_coins Schema erstellt")

        # Erstelle Views
        views_path = os.path.join(schema_dir, "views.sql")
        if os.path.exists(views_path):
            with open(views_path, 'r') as f:
                views_sql = f.read()

            async with pool.acquire() as conn:
                await conn.execute(views_sql)
                print("✅ Views erstellt")

        # Erstelle coin_streams Tabelle (aus pump-metric)
        complete_schema_path = os.path.join(schema_dir, "complete_schema.sql")
        if os.path.exists(complete_schema_path):
            with open(complete_schema_path, 'r') as f:
                complete_sql = f.read()

            async with pool.acquire() as conn:
                # Splitte an Semikolons und führe jeden Befehl aus
                statements = [stmt.strip() for stmt in complete_sql.split(';') if stmt.strip()]
                for stmt in statements:
                    if stmt:
                        try:
                            await conn.execute(stmt)
                        except asyncpg.exceptions.DuplicateTableError:
                            pass  # Tabelle existiert bereits
                        except asyncpg.exceptions.DuplicateObjectError:
                            pass  # Objekt existiert bereits

                print("✅ Vollständiges Schema erstellt")

        print("✅ Datenbank-Schema ist bereit")

    except Exception as e:
        print(f"❌ Fehler beim Erstellen des Schemas: {e}")
        raise


