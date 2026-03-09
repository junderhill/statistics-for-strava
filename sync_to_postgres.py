#!/usr/bin/env python3
"""
sync_to_postgres.py - Sync Statistics for Strava SQLite database to PostgreSQL.

This script:
  - Creates the PostgreSQL schema if it doesn't exist
  - Applies schema migrations incrementally (tracks applied versions)
  - Upserts all data from SQLite into PostgreSQL
  - Is safe to run repeatedly (idempotent)

Usage:
    python sync_to_postgres.py \\
        --sqlite storage/database/strava.db \\
        --postgres "postgresql://user:pass@host:5432/dbname"

Cron example (every hour):
    0 * * * * cd /app && python sync_to_postgres.py \\
        --sqlite storage/database/strava.db \\
        --postgres "postgresql://user:pass@host/strava" \\
        >> /var/log/strava-sync.log 2>&1

Requirements:
    pip install psycopg2-binary
"""

import argparse
import logging
import sqlite3
import sys
from datetime import datetime, timezone

try:
    import psycopg2
    import psycopg2.extras
    import psycopg2.extensions
except ImportError:
    print("psycopg2 is required: pip install psycopg2-binary", file=sys.stderr)
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Migration definitions: SQLite migrations translated to PostgreSQL DDL.
# Each entry maps a Doctrine migration version to a list of SQL statements.
# Add a new entry here whenever a new migration is added to the project.
# ---------------------------------------------------------------------------
MIGRATIONS = [
    (
        "Version20260130000000",
        [
            """
            CREATE TABLE IF NOT EXISTS "Activity" (
                "activityId"                    VARCHAR(255)     NOT NULL,
                "activityType"                  VARCHAR(255)     DEFAULT NULL,
                "data"                          TEXT             DEFAULT NULL,
                "streamsAreImported"            BOOLEAN          DEFAULT NULL,
                "markedForDeletion"             BOOLEAN          DEFAULT NULL,
                "startDateTime"                 TIMESTAMP        NOT NULL,
                "sportType"                     VARCHAR(255)     NOT NULL,
                "worldType"                     VARCHAR(255)     DEFAULT NULL,
                "name"                          VARCHAR(255)     NOT NULL,
                "description"                   VARCHAR(255)     DEFAULT NULL,
                "distance"                      INTEGER          NOT NULL,
                "elevation"                     INTEGER          NOT NULL,
                "calories"                      INTEGER          DEFAULT NULL,
                "averagePower"                  INTEGER          DEFAULT NULL,
                "maxPower"                      INTEGER          DEFAULT NULL,
                "averageSpeed"                  DOUBLE PRECISION NOT NULL,
                "maxSpeed"                      DOUBLE PRECISION NOT NULL,
                "averageHeartRate"              INTEGER          DEFAULT NULL,
                "maxHeartRate"                  INTEGER          DEFAULT NULL,
                "averageCadence"                INTEGER          DEFAULT NULL,
                "movingTimeInSeconds"           INTEGER          NOT NULL,
                "kudoCount"                     INTEGER          NOT NULL,
                "deviceName"                    VARCHAR(255)     DEFAULT NULL,
                "totalImageCount"               INTEGER          NOT NULL,
                "localImagePaths"               TEXT             DEFAULT NULL,
                "polyline"                      TEXT             DEFAULT NULL,
                "routeGeography"                TEXT             DEFAULT NULL,
                "weather"                       TEXT             DEFAULT NULL,
                "gearId"                        VARCHAR(255)     DEFAULT NULL,
                "isCommute"                     BOOLEAN          DEFAULT NULL,
                "workoutType"                   VARCHAR(255)     DEFAULT NULL,
                "startingCoordinateLatitude"    DOUBLE PRECISION DEFAULT NULL,
                "startingCoordinateLongitude"   DOUBLE PRECISION DEFAULT NULL,
                PRIMARY KEY ("activityId")
            )
            """,
            'CREATE INDEX IF NOT EXISTS "Activity_startDateTimeIndex" ON "Activity" ("startDateTime")',
            'CREATE INDEX IF NOT EXISTS "Activity_sportType" ON "Activity" ("sportType")',
            """
            CREATE TABLE IF NOT EXISTS "ActivityBestEffort" (
                "activityId"       VARCHAR(255) NOT NULL,
                "distanceInMeter"  INTEGER      NOT NULL,
                "sportType"        VARCHAR(255) NOT NULL,
                "timeInSeconds"    INTEGER      NOT NULL,
                PRIMARY KEY ("activityId", "distanceInMeter")
            )
            """,
            'CREATE INDEX IF NOT EXISTS "ActivityBestEffort_sportTypeIndex" ON "ActivityBestEffort" ("sportType")',
            """
            CREATE TABLE IF NOT EXISTS "ActivityLap" (
                "lapId"                 VARCHAR(255)     NOT NULL,
                "activityId"            VARCHAR(255)     NOT NULL,
                "lapNumber"             INTEGER          NOT NULL,
                "name"                  VARCHAR(255)     NOT NULL,
                "elapsedTimeInSeconds"  INTEGER          NOT NULL,
                "movingTimeInSeconds"   INTEGER          NOT NULL,
                "distance"              INTEGER          NOT NULL,
                "averageSpeed"          DOUBLE PRECISION NOT NULL,
                "minAverageSpeed"       DOUBLE PRECISION NOT NULL,
                "maxAverageSpeed"       DOUBLE PRECISION NOT NULL,
                "maxSpeed"              DOUBLE PRECISION NOT NULL,
                "elevationDifference"   INTEGER          NOT NULL,
                "averageHeartRate"      INTEGER          DEFAULT NULL,
                PRIMARY KEY ("lapId")
            )
            """,
            'CREATE INDEX IF NOT EXISTS "ActivitySplit_activityId" ON "ActivityLap" ("activityId")',
            """
            CREATE TABLE IF NOT EXISTS "ActivitySplit" (
                "activityId"            VARCHAR(255)     NOT NULL,
                "unitSystem"            VARCHAR(255)     NOT NULL,
                "splitNumber"           INTEGER          NOT NULL,
                "distance"              INTEGER          NOT NULL,
                "elapsedTimeInSeconds"  INTEGER          NOT NULL,
                "movingTimeInSeconds"   INTEGER          NOT NULL,
                "elevationDifference"   INTEGER          NOT NULL,
                "averageSpeed"          DOUBLE PRECISION NOT NULL,
                "minAverageSpeed"       DOUBLE PRECISION NOT NULL,
                "maxAverageSpeed"       INTEGER          NOT NULL,
                "paceZone"              INTEGER          NOT NULL,
                PRIMARY KEY ("activityId", "unitSystem", "splitNumber")
            )
            """,
            'CREATE INDEX IF NOT EXISTS "ActivitySplit_activityIdUnitSystemIndex" ON "ActivitySplit" ("activityId", "unitSystem")',
            """
            CREATE TABLE IF NOT EXISTS "ActivityStream" (
                "activityId"   VARCHAR(255) NOT NULL,
                "streamType"   VARCHAR(255) NOT NULL,
                "createdOn"    TIMESTAMP    NOT NULL,
                "data"         TEXT         NOT NULL,
                "computedFieldsState" TEXT  DEFAULT NULL,
                "normalizedPower"     INTEGER DEFAULT NULL,
                "valueDistribution"   TEXT   DEFAULT NULL,
                "bestAverages"        TEXT   DEFAULT NULL,
                PRIMARY KEY ("activityId", "streamType")
            )
            """,
            'CREATE INDEX IF NOT EXISTS "ActivityStream_activityIndex" ON "ActivityStream" ("activityId")',
            'CREATE INDEX IF NOT EXISTS "ActivityStream_streamTypeIndex" ON "ActivityStream" ("streamType")',
            """
            CREATE TABLE IF NOT EXISTS "Challenge" (
                "challengeId"   VARCHAR(255) NOT NULL,
                "createdOn"     TIMESTAMP    NOT NULL,
                "name"          VARCHAR(255) NOT NULL,
                "logoUrl"       VARCHAR(255) DEFAULT NULL,
                "localLogoUrl"  VARCHAR(255) DEFAULT NULL,
                "slug"          VARCHAR(255) NOT NULL,
                PRIMARY KEY ("challengeId")
            )
            """,
            'CREATE INDEX IF NOT EXISTS "Challenge_createdOnIndex" ON "Challenge" ("createdOn")',
            """
            CREATE TABLE IF NOT EXISTS "ChatMessage" (
                "messageId"   VARCHAR(255) NOT NULL,
                "message"     TEXT         NOT NULL,
                "messageRole" VARCHAR(255) NOT NULL,
                "on"          TIMESTAMP    NOT NULL,
                PRIMARY KEY ("messageId")
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "CombinedActivityStream" (
                "activityId"  VARCHAR(255) NOT NULL,
                "unitSystem"  VARCHAR(255) NOT NULL,
                "streamTypes" VARCHAR(255) NOT NULL,
                "data"        TEXT         NOT NULL,
                PRIMARY KEY ("activityId", "unitSystem")
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "Gear" (
                "gearId"           VARCHAR(255) NOT NULL,
                "createdOn"        TIMESTAMP    NOT NULL,
                "distanceInMeter"  INTEGER      NOT NULL,
                "name"             VARCHAR(255) NOT NULL,
                "isRetired"        BOOLEAN      NOT NULL,
                "type"             VARCHAR(255) NOT NULL DEFAULT 'imported',
                PRIMARY KEY ("gearId")
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "KeyValue" (
                "key"   VARCHAR(255) NOT NULL,
                "value" TEXT         NOT NULL,
                PRIMARY KEY ("key")
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "Segment" (
                "segmentId"                   VARCHAR(255)     NOT NULL,
                "name"                        VARCHAR(255)     DEFAULT NULL,
                "sportType"                   VARCHAR(255)     NOT NULL,
                "distance"                    INTEGER          NOT NULL,
                "maxGradient"                 DOUBLE PRECISION NOT NULL,
                "isFavourite"                 BOOLEAN          NOT NULL,
                "climbCategory"               INTEGER          DEFAULT NULL,
                "deviceName"                  VARCHAR(255)     DEFAULT NULL,
                "countryCode"                 VARCHAR(255)     DEFAULT NULL,
                "detailsHaveBeenImported"     BOOLEAN          DEFAULT NULL,
                "polyline"                    TEXT             DEFAULT NULL,
                "startingCoordinateLatitude"  DOUBLE PRECISION DEFAULT NULL,
                "startingCoordinateLongitude" DOUBLE PRECISION DEFAULT NULL,
                PRIMARY KEY ("segmentId")
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "SegmentEffort" (
                "segmentEffortId"      VARCHAR(255)     NOT NULL,
                "segmentId"            VARCHAR(255)     NOT NULL,
                "activityId"           VARCHAR(255)     NOT NULL,
                "startDateTime"        TIMESTAMP        NOT NULL,
                "name"                 VARCHAR(255)     NOT NULL,
                "elapsedTimeInSeconds" DOUBLE PRECISION NOT NULL,
                "distance"             INTEGER          NOT NULL,
                "averageWatts"         DOUBLE PRECISION DEFAULT NULL,
                "averageHeartRate"     INTEGER          DEFAULT NULL,
                "maxHeartRate"         INTEGER          DEFAULT NULL,
                PRIMARY KEY ("segmentEffortId")
            )
            """,
            'CREATE INDEX IF NOT EXISTS "SegmentEffort_segmentIndex" ON "SegmentEffort" ("segmentId")',
            'CREATE INDEX IF NOT EXISTS "SegmentEffort_activityIndex" ON "SegmentEffort" ("activityId")',
            """
            CREATE TABLE IF NOT EXISTS "WebhookEvent" (
                "objectId"   VARCHAR(255) NOT NULL,
                "objectType" VARCHAR(255) NOT NULL,
                "aspectType" VARCHAR(255) NOT NULL,
                "payload"    TEXT         NOT NULL,
                PRIMARY KEY ("objectId")
            )
            """,
        ],
    ),
    (
        "Version20260203112204",
        [
            'CREATE INDEX IF NOT EXISTS "Activity_gearId" ON "Activity" ("gearId")',
            'CREATE INDEX IF NOT EXISTS "Activity_markedForDeletion" ON "Activity" ("markedForDeletion")',
            'CREATE INDEX IF NOT EXISTS "Activity_streamsAreImported" ON "Activity" ("streamsAreImported")',
            'CREATE INDEX IF NOT EXISTS "ChatMessage_on" ON "ChatMessage" ("on")',
            'CREATE INDEX IF NOT EXISTS "Gear_type" ON "Gear" ("type")',
            'CREATE INDEX IF NOT EXISTS "Segment_detailsHaveBeenImported" ON "Segment" ("detailsHaveBeenImported")',
            'CREATE INDEX IF NOT EXISTS "SegmentEffort_segmentElapsedTime" ON "SegmentEffort" ("segmentId", "elapsedTimeInSeconds")',
            'CREATE INDEX IF NOT EXISTS "SegmentEffort_segmentStartDateTime" ON "SegmentEffort" ("segmentId", "startDateTime")',
        ],
    ),
    (
        "Version20260209083118",
        [
            # Restructure CombinedActivityStream: add maxYAxisValue, change data to BYTEA
            # We use DO $$ ... $$ to conditionally add the column so this is idempotent
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'CombinedActivityStream'
                    AND column_name = 'maxYAxisValue'
                ) THEN
                    ALTER TABLE "CombinedActivityStream" ADD COLUMN "maxYAxisValue" INTEGER NOT NULL DEFAULT 0;
                END IF;
            END$$
            """,
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'CombinedActivityStream'
                    AND column_name = 'data'
                    AND data_type = 'text'
                ) THEN
                    ALTER TABLE "CombinedActivityStream" ALTER COLUMN "data" TYPE BYTEA
                        USING "data"::bytea;
                END IF;
            END$$
            """,
        ],
    ),
    (
        "Version20260211033128",
        [
            # Data cleanup migration — no schema changes, data will be resynced naturally
        ],
    ),
    (
        "Version20260219090805",
        [
            """
            CREATE TABLE IF NOT EXISTS "ActivityStreamMetric" (
                "activityId"  VARCHAR(255) NOT NULL,
                "streamType"  VARCHAR(255) NOT NULL,
                "metricType"  VARCHAR(255) NOT NULL,
                "data"        BYTEA        NOT NULL,
                PRIMARY KEY ("activityId", "streamType", "metricType")
            )
            """,
            'CREATE INDEX IF NOT EXISTS "ActivityStreamMetric_activityIndex" ON "ActivityStreamMetric" ("activityId")',
            'CREATE INDEX IF NOT EXISTS "ActivityStreamMetric_streamTypeIndex" ON "ActivityStreamMetric" ("streamType")',
            'CREATE INDEX IF NOT EXISTS "ActivityStreamMetric_metricTypeIndex" ON "ActivityStreamMetric" ("metricType")',
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'ActivityStream' AND column_name = 'computedFieldsState'
                ) THEN
                    ALTER TABLE "ActivityStream" DROP COLUMN "computedFieldsState";
                END IF;
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'ActivityStream' AND column_name = 'normalizedPower'
                ) THEN
                    ALTER TABLE "ActivityStream" DROP COLUMN "normalizedPower";
                END IF;
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'ActivityStream' AND column_name = 'valueDistribution'
                ) THEN
                    ALTER TABLE "ActivityStream" DROP COLUMN "valueDistribution";
                END IF;
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'ActivityStream' AND column_name = 'bestAverages'
                ) THEN
                    ALTER TABLE "ActivityStream" DROP COLUMN "bestAverages";
                END IF;
            END$$
            """,
        ],
    ),
    (
        "Version20260220085447",
        [
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'ActivityStream' AND column_name = 'dataSize'
                ) THEN
                    ALTER TABLE "ActivityStream" ADD COLUMN "dataSize" INTEGER NOT NULL DEFAULT 0;
                END IF;
            END$$
            """,
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'ActivityStream'
                    AND column_name = 'data'
                    AND data_type = 'text'
                ) THEN
                    ALTER TABLE "ActivityStream" ALTER COLUMN "data" TYPE BYTEA
                        USING "data"::bytea;
                END IF;
            END$$
            """,
        ],
    ),
]

# ---------------------------------------------------------------------------
# Table sync configuration.
# binary_columns: columns that contain raw bytes in SQLite → BYTEA in PG
# primary_key: columns forming the primary key (used for ON CONFLICT clause)
# ---------------------------------------------------------------------------
TABLES = [
    {
        "name": "Activity",
        "primary_key": ["activityId"],
        "binary_columns": [],
    },
    {
        "name": "ActivityBestEffort",
        "primary_key": ["activityId", "distanceInMeter"],
        "binary_columns": [],
    },
    {
        "name": "ActivityLap",
        "primary_key": ["lapId"],
        "binary_columns": [],
    },
    {
        "name": "ActivitySplit",
        "primary_key": ["activityId", "unitSystem", "splitNumber"],
        "binary_columns": [],
    },
    {
        "name": "ActivityStream",
        "primary_key": ["activityId", "streamType"],
        "binary_columns": ["data"],
    },
    {
        "name": "ActivityStreamMetric",
        "primary_key": ["activityId", "streamType", "metricType"],
        "binary_columns": ["data"],
    },
    {
        "name": "Challenge",
        "primary_key": ["challengeId"],
        "binary_columns": [],
    },
    {
        "name": "ChatMessage",
        "primary_key": ["messageId"],
        "binary_columns": [],
    },
    {
        "name": "CombinedActivityStream",
        "primary_key": ["activityId", "unitSystem"],
        "binary_columns": ["data"],
    },
    {
        "name": "Gear",
        "primary_key": ["gearId"],
        "binary_columns": [],
    },
    {
        "name": "KeyValue",
        "primary_key": ["key"],
        "binary_columns": [],
    },
    {
        "name": "Segment",
        "primary_key": ["segmentId"],
        "binary_columns": [],
    },
    {
        "name": "SegmentEffort",
        "primary_key": ["segmentEffortId"],
        "binary_columns": [],
    },
    {
        "name": "WebhookEvent",
        "primary_key": ["objectId"],
        "binary_columns": [],
    },
]

SYNC_META_TABLE = "strava_sync_meta"
BATCH_SIZE = 500


# ---------------------------------------------------------------------------
# Schema / migration helpers
# ---------------------------------------------------------------------------

def create_meta_table(pg_cur: psycopg2.extensions.cursor) -> None:
    """Create the metadata table that tracks applied migrations and sync state."""
    pg_cur.execute(f"""
        CREATE TABLE IF NOT EXISTS "{SYNC_META_TABLE}" (
            "key"        VARCHAR(255) NOT NULL,
            "value"      TEXT         NOT NULL,
            "updated_at" TIMESTAMP    NOT NULL DEFAULT now(),
            PRIMARY KEY ("key")
        )
    """)


def get_applied_migrations(pg_cur: psycopg2.extensions.cursor) -> set[str]:
    pg_cur.execute(f'SELECT "value" FROM "{SYNC_META_TABLE}" WHERE "key" = \'applied_migrations\'')
    row = pg_cur.fetchone()
    if row is None:
        return set()
    return set(row[0].split(",")) if row[0] else set()


def save_applied_migrations(pg_cur: psycopg2.extensions.cursor, applied: set[str]) -> None:
    pg_cur.execute(f"""
        INSERT INTO "{SYNC_META_TABLE}" ("key", "value", "updated_at")
        VALUES ('applied_migrations', %s, now())
        ON CONFLICT ("key") DO UPDATE SET "value" = EXCLUDED."value", "updated_at" = now()
    """, (",".join(sorted(applied)),))


def apply_migrations(pg_conn, pg_cur: psycopg2.extensions.cursor) -> None:
    """Apply any unapplied migrations to the PostgreSQL schema."""
    create_meta_table(pg_cur)
    pg_conn.commit()

    applied = get_applied_migrations(pg_cur)

    for version, statements in MIGRATIONS:
        if version in applied:
            continue

        log.info("Applying migration %s", version)
        for sql in statements:
            sql = sql.strip()
            if sql:
                pg_cur.execute(sql)
        pg_conn.commit()

        applied.add(version)
        save_applied_migrations(pg_cur, applied)
        pg_conn.commit()
        log.info("Migration %s applied", version)


# ---------------------------------------------------------------------------
# Data sync helpers
# ---------------------------------------------------------------------------

def get_sqlite_columns(sqlite_cur: sqlite3.Cursor, table: str) -> list[str]:
    """Return the list of column names for a SQLite table."""
    sqlite_cur.execute(f'PRAGMA table_info("{table}")')
    return [row[1] for row in sqlite_cur.fetchall()]


def get_pg_columns(pg_cur: psycopg2.extensions.cursor, table: str) -> set[str]:
    """Return the set of column names for a PostgreSQL table."""
    pg_cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = %s
    """, (table,))
    return {row[0] for row in pg_cur.fetchall()}


def build_upsert_sql(table: str, columns: list[str], primary_key: list[str]) -> str:
    """Build a PostgreSQL INSERT ... ON CONFLICT DO UPDATE statement."""
    quoted_cols = [f'"{c}"' for c in columns]
    placeholders = ", ".join(["%s"] * len(columns))
    conflict_cols = ", ".join(f'"{c}"' for c in primary_key)

    update_cols = [c for c in columns if c not in primary_key]
    if update_cols:
        update_clause = ", ".join(f'"{c}" = EXCLUDED."{c}"' for c in update_cols)
        on_conflict = f"ON CONFLICT ({conflict_cols}) DO UPDATE SET {update_clause}"
    else:
        on_conflict = f"ON CONFLICT ({conflict_cols}) DO NOTHING"

    return (
        f'INSERT INTO "{table}" ({", ".join(quoted_cols)}) '
        f"VALUES ({placeholders}) {on_conflict}"
    )


def coerce_row(row: sqlite3.Row, columns: list[str], binary_columns: list[str]) -> tuple:
    """Convert a SQLite row to values suitable for PostgreSQL insertion."""
    result = []
    for col, val in zip(columns, row):
        if val is None:
            result.append(None)
        elif col in binary_columns:
            # SQLite BLOB → PostgreSQL BYTEA
            result.append(psycopg2.Binary(val) if isinstance(val, (bytes, bytearray)) else psycopg2.Binary(val.encode() if isinstance(val, str) else bytes(val)))
        else:
            result.append(val)
    return tuple(result)


def table_exists_in_pg(pg_cur: psycopg2.extensions.cursor, table: str) -> bool:
    pg_cur.execute(
        "SELECT 1 FROM information_schema.tables WHERE table_name = %s",
        (table,),
    )
    return pg_cur.fetchone() is not None


def table_exists_in_sqlite(sqlite_cur: sqlite3.Cursor, table: str) -> bool:
    sqlite_cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    )
    return sqlite_cur.fetchone() is not None


def sync_table(
    sqlite_conn: sqlite3.Connection,
    pg_conn,
    table_config: dict,
) -> int:
    """Upsert all rows from SQLite table into PostgreSQL. Returns row count."""
    table = table_config["name"]
    primary_key = table_config["primary_key"]
    binary_columns = table_config["binary_columns"]

    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()

    if not table_exists_in_sqlite(sqlite_cur, table):
        log.debug("Table %s not in SQLite, skipping", table)
        return 0

    if not table_exists_in_pg(pg_cur, table):
        log.warning("Table %s not in PostgreSQL, skipping (run migrations first)", table)
        return 0

    # Use only columns that exist in both SQLite and PostgreSQL
    sqlite_columns = get_sqlite_columns(sqlite_cur, table)
    pg_columns = get_pg_columns(pg_cur, table)
    columns = [c for c in sqlite_columns if c in pg_columns]

    if not columns:
        log.warning("No matching columns for table %s, skipping", table)
        return 0

    upsert_sql = build_upsert_sql(table, columns, primary_key)
    quoted_cols = ", ".join(f'"{c}"' for c in columns)

    sqlite_cur.execute(f'SELECT {quoted_cols} FROM "{table}"')

    total = 0
    batch = []
    for row in sqlite_cur:
        batch.append(coerce_row(row, columns, binary_columns))
        if len(batch) >= BATCH_SIZE:
            psycopg2.extras.execute_batch(pg_cur, upsert_sql, batch, page_size=BATCH_SIZE)
            pg_conn.commit()
            total += len(batch)
            batch = []

    if batch:
        psycopg2.extras.execute_batch(pg_cur, upsert_sql, batch, page_size=BATCH_SIZE)
        pg_conn.commit()
        total += len(batch)

    return total


def update_last_sync(pg_conn) -> None:
    pg_cur = pg_conn.cursor()
    pg_cur.execute(f"""
        INSERT INTO "{SYNC_META_TABLE}" ("key", "value", "updated_at")
        VALUES ('last_sync', %s, now())
        ON CONFLICT ("key") DO UPDATE SET "value" = EXCLUDED."value", "updated_at" = now()
    """, (datetime.now(timezone.utc).isoformat(),))
    pg_conn.commit()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync Statistics for Strava SQLite database to PostgreSQL",
    )
    parser.add_argument(
        "--sqlite",
        required=True,
        metavar="PATH",
        help="Path to the SQLite database file (e.g. storage/database/strava.db)",
    )
    parser.add_argument(
        "--postgres",
        required=True,
        metavar="DSN",
        help='PostgreSQL connection string (e.g. "postgresql://user:pass@host:5432/dbname")',
    )
    parser.add_argument(
        "--tables",
        nargs="*",
        metavar="TABLE",
        help="Sync only these tables (default: all tables)",
    )
    parser.add_argument(
        "--skip-migrations",
        action="store_true",
        help="Skip applying schema migrations (useful if schema is managed externally)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Connect and validate but do not write any data",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.dry_run:
        log.info("DRY RUN — no data will be written")

    # Connect to SQLite
    log.info("Opening SQLite database: %s", args.sqlite)
    sqlite_conn = sqlite3.connect(args.sqlite)
    sqlite_conn.row_factory = sqlite3.Row

    # Connect to PostgreSQL
    log.info("Connecting to PostgreSQL")
    try:
        pg_conn = psycopg2.connect(args.postgres)
    except psycopg2.OperationalError as exc:
        log.error("Failed to connect to PostgreSQL: %s", exc)
        return 1

    pg_cur = pg_conn.cursor()

    if args.dry_run:
        log.info("Connections OK. Exiting (dry run).")
        return 0

    # Apply schema migrations
    if not args.skip_migrations:
        log.info("Checking and applying schema migrations...")
        apply_migrations(pg_conn, pg_cur)
    else:
        log.info("Skipping migrations (--skip-migrations)")

    # Determine which tables to sync
    tables_to_sync = TABLES
    if args.tables:
        requested = set(args.tables)
        tables_to_sync = [t for t in TABLES if t["name"] in requested]
        unknown = requested - {t["name"] for t in tables_to_sync}
        if unknown:
            log.warning("Unknown tables requested: %s", ", ".join(sorted(unknown)))

    # Sync data
    log.info("Starting data sync (%d tables)...", len(tables_to_sync))
    start = datetime.now()
    grand_total = 0

    for table_config in tables_to_sync:
        table_name = table_config["name"]
        try:
            count = sync_table(sqlite_conn, pg_conn, table_config)
            log.info("  %-30s %d rows synced", table_name, count)
            grand_total += count
        except Exception as exc:  # noqa: BLE001
            log.error("  %-30s ERROR: %s", table_name, exc)
            pg_conn.rollback()

    elapsed = (datetime.now() - start).total_seconds()
    log.info("Sync complete: %d total rows in %.1fs", grand_total, elapsed)

    update_last_sync(pg_conn)

    pg_conn.close()
    sqlite_conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
