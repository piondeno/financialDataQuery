import hashlib
import os
import re
import sqlite3
from datetime import date
from pathlib import Path
import pandas as pd


class DiskCache:
    def __init__(self, cache_dir: str = "/home/piondeno/.cache/financial_data_query"):
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._cleanup_old_files()
        today_str = date.today().strftime("%Y-%m-%d")
        self._db_path = self._cache_dir / f"{today_str}.db"
        self._conn = sqlite3.connect(str(self._db_path))

    def _table_name(
        self, source: str, symbol: str, frequency: str | None
    ) -> str:
        # Use SHA256 hash of the symbol to preserve uniqueness for non-ASCII chars
        symbol_hash = hashlib.sha256(symbol.encode("utf-8")).hexdigest()[:12]
        freq_part = frequency if frequency else "none"
        return f"{source}_{symbol_hash}_{freq_part}"

    def get(
        self,
        source: str,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        frequency: str | None = None,
    ) -> pd.DataFrame | None:
        try:
            table = self._table_name(source, symbol, frequency)
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
                        return v.strftime("%Y-%m-%d")
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
        today_str = date.today().strftime("%Y-%m-%d")
        try:
            for f in self._cache_dir.glob("*.db"):
                if f.stem != today_str:
                    os.unlink(f)
        except OSError:
            pass

    def close(self) -> None:
        if self._conn:
            self._conn.close()
