# Wichtige SQL-Queries

Sammlung der wichtigsten Datenbank-Queries mit Erklärungen.

---

## Stream-Management

### Aktive Streams abrufen

```sql
-- Alle aktiven Streams mit Phase-Details
SELECT
    cs.token_address,
    cs.current_phase_id,
    cs.started_at,
    cs.ath_price_sol,
    rcp.name as phase_name,
    rcp.interval_seconds,
    EXTRACT(EPOCH FROM (NOW() - cs.started_at)) / 60 as age_minutes
FROM coin_streams cs
JOIN ref_coin_phases rcp ON cs.current_phase_id = rcp.id
WHERE cs.is_active = true
ORDER BY cs.started_at DESC;
```

**Verwendung in Service:**
```python
# unified_service.py - get_active_streams()
async def get_active_streams(self):
    rows = await self.pool.fetch("""
        SELECT
            cs.token_address,
            cs.current_phase_id as phase_id,
            cs.started_at as created_at,
            dc.trader_public_key as creator_address,
            dc.name, dc.symbol
        FROM coin_streams cs
        LEFT JOIN discovered_coins dc ON cs.token_address = dc.token_address
        WHERE cs.is_active = true
    """)
    return {row["token_address"]: dict(row) for row in rows}
```

### Streams nach Phase zählen

```sql
SELECT
    current_phase_id,
    COUNT(*) as count
FROM coin_streams
GROUP BY current_phase_id
ORDER BY current_phase_id;
```

**Beispiel-Output:**
```
 current_phase_id | count
------------------+-------
                1 |    45
                2 |   120
                3 |    64
               99 |   890
              100 |   404
```

### Stream aktivieren

```sql
-- Neuen Stream anlegen
INSERT INTO coin_streams (token_address, current_phase_id, is_active)
VALUES ('So111...', 1, true)
ON CONFLICT (token_address) DO NOTHING;
```

### Stream beenden

```sql
-- Timeout (Phase 99)
UPDATE coin_streams
SET is_active = false, current_phase_id = 99
WHERE token_address = 'So111...';

-- Graduation (Phase 100)
UPDATE coin_streams
SET is_active = false, current_phase_id = 100, is_graduated = true
WHERE token_address = 'So111...';
```

---

## Phase-Management

### Phase wechseln

```sql
UPDATE coin_streams
SET current_phase_id = 2
WHERE token_address = 'So111...'
  AND current_phase_id = 1;
```

### Streams bei Phase-Löschung migrieren

```sql
-- Streams zu nächster Phase verschieben
UPDATE coin_streams
SET current_phase_id = (
    SELECT id FROM ref_coin_phases
    WHERE id > 2 AND id < 99
    ORDER BY id ASC
    LIMIT 1
)
WHERE current_phase_id = 2 AND is_active = true;
```

### Phase-Konfiguration laden

```sql
SELECT id, name, interval_seconds, min_age_minutes, max_age_minutes
FROM ref_coin_phases
ORDER BY id ASC;
```

---

## Metriken-Queries

### Metriken für einen Coin

```sql
SELECT
    timestamp,
    price_open, price_high, price_low, price_close,
    volume_sol, volume_buy_sol, volume_sell_sol,
    num_buys, num_sells,
    unique_wallets,
    whale_buys, whale_sells,
    dev_sold_sol
FROM coin_metrics
WHERE mint = 'So111...'
ORDER BY timestamp DESC
LIMIT 100;
```

### Letzte X Minuten Performance

```sql
-- Preisänderung in den letzten 5 Minuten
WITH latest AS (
    SELECT price_close as current_price
    FROM coin_metrics
    WHERE mint = 'So111...'
    ORDER BY timestamp DESC
    LIMIT 1
),
old AS (
    SELECT price_close as old_price
    FROM coin_metrics
    WHERE mint = 'So111...'
      AND timestamp < NOW() - INTERVAL '5 minutes'
    ORDER BY timestamp DESC
    LIMIT 1
)
SELECT
    latest.current_price,
    old.old_price,
    ((latest.current_price - old.old_price) / old.old_price * 100) as change_pct
FROM latest, old;
```

### Aggregierte Tages-Statistiken

```sql
SELECT
    mint,
    DATE(timestamp) as day,
    COUNT(*) as metric_count,
    SUM(volume_sol) as total_volume,
    SUM(num_buys) as total_buys,
    SUM(num_sells) as total_sells,
    MAX(price_high) as day_high,
    MIN(price_low) as day_low
FROM coin_metrics
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY mint, DATE(timestamp)
ORDER BY day DESC, total_volume DESC;
```

### Batch-Insert Metriken

```sql
-- Verwendet in check_lifecycle_and_flush()
INSERT INTO coin_metrics (
    mint, timestamp,
    price_open, price_high, price_low, price_close,
    volume_sol, volume_buy_sol, volume_sell_sol,
    num_buys, num_sells, unique_wallets,
    whale_buys, whale_sells,
    whale_buy_volume, whale_sell_volume,
    dev_sold_sol, micro_trades, market_cap_sol
) VALUES
    ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19),
    ($1, $2, ...),
    ...;
```

---

## ATH-Tracking

### ATH aktualisieren

```sql
UPDATE coin_streams
SET ath_price_sol = $1, ath_timestamp = NOW()
WHERE token_address = $2
  AND (ath_price_sol IS NULL OR ath_price_sol < $1);
```

### Batch ATH-Update

```sql
-- Verwendet in flush_ath_updates()
UPDATE coin_streams
SET ath_price_sol = $1, ath_timestamp = NOW()
WHERE token_address = $2;
```

### Top ATH Coins

```sql
SELECT
    cs.token_address,
    dc.name,
    dc.symbol,
    cs.ath_price_sol,
    cs.ath_timestamp,
    cs.started_at
FROM coin_streams cs
JOIN discovered_coins dc ON cs.token_address = dc.token_address
WHERE cs.ath_price_sol IS NOT NULL
ORDER BY cs.ath_price_sol DESC
LIMIT 50;
```

---

## Zombie Detection

### Inaktive Streams finden

```sql
-- Streams ohne kürzliche Metriken
SELECT
    cs.token_address,
    cs.started_at,
    cs.current_phase_id,
    MAX(cm.timestamp) as last_metric
FROM coin_streams cs
LEFT JOIN coin_metrics cm ON cs.token_address = cm.mint
WHERE cs.is_active = true
GROUP BY cs.token_address, cs.started_at, cs.current_phase_id
HAVING MAX(cm.timestamp) < NOW() - INTERVAL '30 minutes'
   OR MAX(cm.timestamp) IS NULL
ORDER BY last_metric ASC NULLS FIRST;
```

### Zombie-Cleanup

```sql
-- Vorsicht: Nur nach manueller Prüfung ausführen!
UPDATE coin_streams
SET is_active = false, current_phase_id = 99
WHERE is_active = true
  AND started_at < NOW() - INTERVAL '4 hours'
  AND NOT EXISTS (
    SELECT 1 FROM coin_metrics cm
    WHERE cm.mint = token_address
    AND cm.timestamp > NOW() - INTERVAL '1 hour'
  );
```

---

## Coin Discovery

### Neuen Coin speichern

```sql
INSERT INTO discovered_coins (
    token_address, name, symbol, price_sol, market_cap_sol,
    pool_address, trader_public_key, social_count, has_socials,
    twitter_url, telegram_url, website_url, discovered_at
) VALUES (
    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW()
)
ON CONFLICT (token_address) DO NOTHING;
```

### Coins mit Socials

```sql
SELECT
    token_address, name, symbol,
    social_count,
    twitter_url, telegram_url, website_url, discord_url
FROM discovered_coins
WHERE social_count > 0
ORDER BY discovered_at DESC
LIMIT 100;
```

### Coins nach Creator

```sql
-- Alle Coins eines Creators
SELECT
    token_address, name, symbol,
    discovered_at, market_cap_sol
FROM discovered_coins
WHERE trader_public_key = 'Creator111...'
ORDER BY discovered_at DESC;
```

---

## Statistik-Queries

### Tägliche Discovery-Rate

```sql
SELECT
    DATE(discovered_at) as day,
    COUNT(*) as coins_discovered,
    SUM(CASE WHEN is_graduated THEN 1 ELSE 0 END) as graduated,
    SUM(CASE WHEN has_socials THEN 1 ELSE 0 END) as with_socials
FROM discovered_coins
WHERE discovered_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(discovered_at)
ORDER BY day DESC;
```

### Phase-Verteilung über Zeit

```sql
SELECT
    DATE(started_at) as day,
    current_phase_id,
    COUNT(*) as count
FROM coin_streams
WHERE started_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(started_at), current_phase_id
ORDER BY day DESC, current_phase_id;
```

### Whale-Aktivität

```sql
SELECT
    mint,
    SUM(whale_buys) as total_whale_buys,
    SUM(whale_sells) as total_whale_sells,
    SUM(whale_buy_volume) as total_whale_buy_vol,
    SUM(whale_sell_volume) as total_whale_sell_vol
FROM coin_metrics
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY mint
HAVING SUM(whale_buys) + SUM(whale_sells) > 10
ORDER BY total_whale_buy_vol DESC;
```

---

## Wartungs-Queries

### Tabellen-Größen

```sql
SELECT
    relname as table_name,
    pg_size_pretty(pg_total_relation_size(relid)) as total_size,
    n_live_tup as row_count
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(relid) DESC;
```

### Alte Daten löschen

```sql
-- Metriken älter als 30 Tage
DELETE FROM coin_metrics
WHERE timestamp < NOW() - INTERVAL '30 days';

-- VACUUM nach großen Löschungen
VACUUM ANALYZE coin_metrics;
```

### Index-Nutzung prüfen

```sql
SELECT
    schemaname,
    relname as table_name,
    indexrelname as index_name,
    idx_scan as scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
```

---

## Weiterführende Dokumentation

- [Schema-Übersicht](schema.md) - Tabellen-Strukturen
- [API-Endpunkte](../api/endpoints.md) - Zugriff via REST
- [Backend-Architektur](../architecture/backend.md) - DB-Operationen im Code
