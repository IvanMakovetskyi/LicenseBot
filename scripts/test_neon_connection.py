import asyncio
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
APP_DIR = ROOT_DIR / "app"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from database.db import close_pool, get_pool, init_db  # noqa: E402


async def run_check() -> None:
    await init_db()
    pool = await get_pool()

    test_chat_id = 900000000000

    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO clients (chat_id, full_name, us_state, language, status)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (chat_id) DO UPDATE
            SET full_name = EXCLUDED.full_name,
                us_state = EXCLUDED.us_state,
                language = EXCLUDED.language,
                status = EXCLUDED.status
            """,
            test_chat_id,
            "Neon Connectivity Test",
            "CA",
            "en",
            "new",
        )

        created = await conn.fetchrow(
            "SELECT * FROM clients WHERE chat_id = $1",
            test_chat_id,
        )
        if not created:
            raise RuntimeError("Insert/read check failed")

        await conn.execute(
            "UPDATE clients SET status = $1 WHERE chat_id = $2",
            "in_progress",
            test_chat_id,
        )
        updated_status = await conn.fetchval(
            "SELECT status FROM clients WHERE chat_id = $1",
            test_chat_id,
        )
        if updated_status != "in_progress":
            raise RuntimeError("Update check failed")

        await conn.execute(
            "DELETE FROM clients WHERE chat_id = $1",
            test_chat_id,
        )
        deleted = await conn.fetchrow(
            "SELECT * FROM clients WHERE chat_id = $1",
            test_chat_id,
        )
        if deleted is not None:
            raise RuntimeError("Delete check failed")

    print("Neon check passed: connection + init + CRUD are working.")


async def _main() -> None:
    try:
        await run_check()
    finally:
        await close_pool()


if __name__ == "__main__":
    asyncio.run(_main())
