import hashlib
import os
import sqlite3
from datetime import date
from pathlib import Path
import pandas as pd
from financial_data_query.constants import DATE_FORMAT


class DiskCache:
    def __init__(self, cache_dir: str | None = None):
        if cache_dir is None:
            cache_dir = str(Path.home() / ".cache" / "financial_data_query")
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._cleanup_old_files()
        today_str = date.today().strftime(DATE_FORMAT)
        self._db_path = self._cache_dir / f"{today_str}.db"
        self._conn = sqlite3.connect(str(self._db_path))

    def _table_name(
        self, source: str, symbol: str, frequency: str | None
    ) -> str:
        # Use SHA256 hash of the symbol to preserve uniqueness for non-ASCII chars
        symbol_hash = hashlib.sha256(symbol.encode("utf-8")).hexdigest()[:12]
        freq_part = frequency if frequency else "none"
        return f"{source}_{symbol_hash}_{freq_part}"

    def _schema_hash(self, source: str, symbol: str, frequency: str | None) -> str:
        """Get schema version hash for a table, or empty string if not found."""
        try:
            table = self._table_name(source, symbol, frequency)
            cursor = self._conn.cursor()
            row = cursor.execute(
                'SELECT schema_hash FROM "__metadata__" WHERE table_name = ?',
                (table,),
            ).fetchone()
            return row[0] if row else ""
        except (sqlite3.OperationalError, sqlite3.ProgrammingError):
            return ""

    def _set_schema_hash(self, source: str, symbol: str, frequency: str | None, schema_hash: str) -> None:
        """Store schema version hash for a table."""
        try:
            table = self._table_name(source, symbol, frequency)
            cursor = self._conn.cursor()
            # Ensure metadata table exists
            cursor.execute(
                'CREATE TABLE IF NOT EXISTS "__metadata__" (table_name TEXT PRIMARY KEY, schema_hash TEXT)'
            )
            cursor.execute(
                'INSERT OR REPLACE INTO "__metadata__" (table_name, schema_hash) VALUES (?, ?)',
                (table, schema_hash),
            )
            self._conn.commit()
        except (sqlite3.OperationalError, sqlite3.ProgrammingError):
            pass

    def _compute_schema_hash(self, source: str, symbol: str, frequency: str | None, df: pd.DataFrame) -> str:
        """Compute a hash of the DataFrame column schema for cache invalidation."""
        cols = tuple(df.columns)
        raw = f"{source}|{symbol}|{frequency}|{cols}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def get(
        self,
        source: str,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        frequency: str | None = None,
        expected_schema_hash: str | None = None,
        expected_columns: list[str] | None = None,
    ) -> pd.DataFrame | None:
        """Get data from disk cache.

        If expected_schema_hash is provided and doesn't match the stored schema,
        return None to force a re-fetch (schema mismatch means data structure changed).

        If expected_columns is provided, return None if cached data doesn't have
        all expected columns (schema changed, cache is stale).
        """
        try:
            table = self._table_name(source, symbol, frequency)
            # Check schema hash if provided
            if expected_schema_hash:
                stored_hash = self._schema_hash(source, symbol, frequency)
                if stored_hash and stored_hash != expected_schema_hash:
                    return None
            query = f'SELECT * FROM "{table}"'
            conditions = []
            params: list[str] = []

            if start:
                conditions.append("date >= ?")
                params.append(start)
            if end:
                conditions.append("date <= ?")
                params.append(end)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY date"

            df = pd.read_sql_query(query, self._conn, parse_dates=["date"], params=params)
            if df.empty:
                return None
            df.set_index("date", inplace=True)
            # Check columns if expected columns are provided
            if expected_columns:
                if not all(c in df.columns for c in expected_columns):
                    return None
            return df
        except (pd.io.sql.DatabaseError, sqlite3.OperationalError):
            return None

    def set(
        self,
        source: str,
        symbol: str,
        df: pd.DataFrame,
        frequency: str | None = None,
    ) -> None:
        try:
            table = self._table_name(source, symbol, frequency)
            reset = df.reset_index()
            reset.rename(columns={reset.columns[0]: "date"}, inplace=True)

            cursor = self._conn.cursor()
            existing_tables = [
                r[0]
                for r in cursor.execute(
                    'SELECT name FROM sqlite_master WHERE type="table"'
                ).fetchall()
            ]

            # If table exists, check if schema changed (columns differ)
            if table in existing_tables:
                existing_cols = [
                    r[1] for r in cursor.execute(f'PRAGMA table_info("{table}")').fetchall()
                ]
                new_cols = list(reset.columns)
                if existing_cols != new_cols:
                    # Schema changed — drop old table and recreate with new schema
                    cursor.execute(f'DROP TABLE IF EXISTS "{table}"')
                    existing_tables.remove(table)

            if table not in existing_tables:
                col_defs = []
                for c in reset.columns:
                    if c == "date":
                        col_defs.append('"date" TEXT PRIMARY KEY')
                    else:
                        col_defs.append(f'"{c}" TEXT')
                cursor.execute(
                    f'CREATE TABLE "{table}" ({", ".join(col_defs)})'
                )

            def _to_sql_value(v):
                    if isinstance(v, pd.Timestamp):
                        return v.strftime(DATE_FORMAT)
                    return v

            placeholders = ", ".join(["?"] * len(reset.columns))
            col_names = ", ".join(f'"{c}"' for c in reset.columns)
            rows = [tuple(_to_sql_value(v) for v in row) for _, row in reset.iterrows()]
            cursor.executemany(
                f'INSERT OR REPLACE INTO "{table}" ({col_names}) VALUES ({placeholders})',
                rows,
            )

            self._conn.commit()
        except Exception:
            pass

    def _cleanup_old_files(self) -> None:
        today_str = date.today().strftime(DATE_FORMAT)
        try:
            for f in self._cache_dir.glob("*.db"):
                if f.stem != today_str:
                    os.unlink(f)
        except OSError:
            pass

    def close(self) -> None:
        if self._conn:
            self._conn.close()
