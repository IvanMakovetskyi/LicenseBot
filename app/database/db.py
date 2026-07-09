from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

import asyncpg

from config import settings
from database.seed import build_seed_rows

_pool: Optional[asyncpg.Pool] = None
_pool_lock = asyncio.Lock()
logger = logging.getLogger(__name__)

_QUERY_RETRIES = 3
_RETRY_DELAY_SECONDS = 0.25
_ACQUIRE_TIMEOUT_SECONDS = 8
_TRANSIENT_DB_ERRORS = (
    asyncpg.PostgresConnectionError,
    asyncpg.InterfaceError,
    TimeoutError,
    OSError,
)


async def get_pool() -> asyncpg.Pool:
    global _pool

    if _pool is None:
        async with _pool_lock:
            if _pool is None:
                _pool = await asyncpg.create_pool(
                    dsn=settings.DATABASE_URL,
                    min_size=1,
                    max_size=10,
                    timeout=10,
                    command_timeout=15,
                    max_inactive_connection_lifetime=120,
                    server_settings={
                        "application_name": "licensebot",
                    },
                )

    return _pool


async def close_pool() -> None:
    global _pool

    if _pool is not None:
        await _pool.close()
        _pool = None


async def _migrate_cases_to_clients(conn: asyncpg.Connection) -> None:
    await conn.execute(
        """
        DO $$
        BEGIN
            IF to_regclass('public.clients') IS NULL
               AND to_regclass('public.cases') IS NOT NULL THEN
                ALTER TABLE cases RENAME TO clients;
            END IF;
        END $$;
        """
    )


async def _ensure_clients_table(conn: asyncpg.Connection) -> None:
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS clients (
            id BIGSERIAL PRIMARY KEY,
            chat_id BIGINT UNIQUE,
            full_name TEXT,
            us_state TEXT,
            status TEXT DEFAULT 'new',
            language TEXT DEFAULT 'ru',
            last_sent_message_key TEXT,
            last_sent_message_label TEXT,
            last_sent_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
        """
    )

    await conn.execute(
        """
        ALTER TABLE clients
        ADD COLUMN IF NOT EXISTS language TEXT DEFAULT 'ru'
        """
    )
    await conn.execute(
        """
        ALTER TABLE clients
        ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'new'
        """
    )
    await conn.execute(
        """
        ALTER TABLE clients
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()
        """
    )
    await conn.execute(
        """
        ALTER TABLE clients
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW()
        """
    )
    await conn.execute(
        """
        ALTER TABLE clients
        ADD COLUMN IF NOT EXISTS last_sent_message_key TEXT
        """
    )
    await conn.execute(
        """
        ALTER TABLE clients
        ADD COLUMN IF NOT EXISTS last_sent_message_label TEXT
        """
    )
    await conn.execute(
        """
        ALTER TABLE clients
        ADD COLUMN IF NOT EXISTS last_sent_at TIMESTAMP
        """
    )
    await conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_clients_chat_id_unique
        ON clients (chat_id)
        """
    )

    # If both tables exist (manual drift), keep data by merging without overwriting existing clients.
    await conn.execute(
        """
        DO $$
        BEGIN
            IF to_regclass('public.cases') IS NOT NULL
               AND to_regclass('public.clients') IS NOT NULL THEN
                INSERT INTO clients (chat_id, full_name, us_state, status, language)
                SELECT chat_id, full_name, us_state, status, language
                FROM cases
                ON CONFLICT (chat_id) DO NOTHING;
            END IF;
        END $$;
        """
    )


async def _ensure_message_tables(conn: asyncpg.Connection) -> None:
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS message_templates (
            id BIGSERIAL PRIMARY KEY,
            message_key TEXT NOT NULL,
            state_code TEXT NOT NULL DEFAULT 'default',
            language TEXT NOT NULL DEFAULT 'ru',
            label TEXT NOT NULL,
            text TEXT NOT NULL,
            placeholders TEXT NOT NULL DEFAULT '[]',
            message_category TEXT NOT NULL DEFAULT 'workflow',
            display_order INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE (message_key, state_code, language)
        )
        """
    )

    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS client_message_flows (
            id BIGSERIAL PRIMARY KEY,
            us_state TEXT NOT NULL,
            message_key TEXT NOT NULL,
            display_order INTEGER NOT NULL DEFAULT 0,
            message_category TEXT NOT NULL DEFAULT 'workflow',
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE (us_state, message_key)
        )
        """
    )

    # is_active lets admins deactivate a template/flow without deleting it.
    # Runtime queries only use active rows; the admin/audit views see all.
    await conn.execute(
        """
        ALTER TABLE message_templates
        ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE
        """
    )
    await conn.execute(
        """
        ALTER TABLE client_message_flows
        ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE
        """
    )


async def _seed_message_templates(conn: asyncpg.Connection) -> None:
    template_rows, flow_rows = build_seed_rows()

    await conn.executemany(
        """
        INSERT INTO message_templates (
            message_key,
            state_code,
            language,
            label,
            text,
            placeholders
        )
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (message_key, state_code, language) DO NOTHING
        """,
        template_rows,
    )

    await conn.executemany(
        """
        INSERT INTO client_message_flows (
            us_state,
            message_key,
            display_order,
            message_category
        )
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (us_state, message_key) DO NOTHING
        """,
        flow_rows,
    )


async def init_db() -> None:
    pool = await get_pool()

    async with pool.acquire(timeout=_ACQUIRE_TIMEOUT_SECONDS) as conn:
        async with conn.transaction():
            await _migrate_cases_to_clients(conn)
            await _ensure_clients_table(conn)
            await _ensure_message_tables(conn)
            await _seed_message_templates(conn)


async def _run_with_retry(coro: Any):
    delay = _RETRY_DELAY_SECONDS

    for attempt in range(1, _QUERY_RETRIES + 1):
        try:
            return await coro()
        except _TRANSIENT_DB_ERRORS:
            if attempt >= _QUERY_RETRIES:
                raise
            logger.warning(
                "Transient DB error on attempt %s/%s, retrying in %.2fs",
                attempt,
                _QUERY_RETRIES,
                delay,
            )
            await asyncio.sleep(delay)
            delay *= 2


async def fetchrow(query: str, *args: Any):
    async def _op():
        pool = await get_pool()
        async with pool.acquire(timeout=_ACQUIRE_TIMEOUT_SECONDS) as conn:
            return await conn.fetchrow(query, *args)

    return await _run_with_retry(_op)


async def fetch(query: str, *args: Any):
    async def _op():
        pool = await get_pool()
        async with pool.acquire(timeout=_ACQUIRE_TIMEOUT_SECONDS) as conn:
            return await conn.fetch(query, *args)

    return await _run_with_retry(_op)


async def execute(query: str, *args: Any):
    async def _op():
        pool = await get_pool()
        async with pool.acquire(timeout=_ACQUIRE_TIMEOUT_SECONDS) as conn:
            return await conn.execute(query, *args)

    return await _run_with_retry(_op)
