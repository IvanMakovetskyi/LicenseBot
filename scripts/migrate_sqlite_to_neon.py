import asyncio
import sqlite3
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
APP_DIR = ROOT_DIR / "app"
SQLITE_PATH = ROOT_DIR / "data" / "clients.db"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from database.db import close_pool, get_pool, init_db  # noqa: E402


async def migrate() -> None:
    if not SQLITE_PATH.exists():
        print(f"SQLite file not found, nothing to migrate: {SQLITE_PATH}")
        return

    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()
    cursor.execute(
        """
        SELECT id, chat_id, full_name, us_state, language, status
        FROM cases
        ORDER BY id ASC
        """
    )
    rows = cursor.fetchall()
    sqlite_conn.close()

    await init_db()
    pool = await get_pool()

    migrated = 0
    skipped = 0

    async with pool.acquire() as conn:
        async with conn.transaction():
            for row in rows:
                if row["chat_id"] is None:
                    skipped += 1
                    continue

                result = await conn.execute(
                    """
                    INSERT INTO clients (chat_id, full_name, us_state, language, status)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (chat_id) DO NOTHING
                    """,
                    int(row["chat_id"]),
                    row["full_name"] or "",
                    row["us_state"] or "",
                    row["language"] or "ru",
                    row["status"] or "new",
                )

                if result.endswith("1"):
                    migrated += 1
                else:
                    skipped += 1

    print(f"Total SQLite rows: {len(rows)}")
    print(f"Migrated to Neon: {migrated}")
    print(f"Skipped (duplicate chat_id): {skipped}")


async def _main() -> None:
    try:
        await migrate()
    finally:
        await close_pool()


if __name__ == "__main__":
    asyncio.run(_main())
