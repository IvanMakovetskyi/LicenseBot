from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Optional

import asyncpg

from config import settings

_pool: Optional[asyncpg.Pool] = None
_pool_lock = asyncio.Lock()
logger = logging.getLogger(__name__)

_QUERY_RETRIES = 3
_RETRY_DELAY_SECONDS = 0.25
_ACQUIRE_TIMEOUT_SECONDS = 8
_DEFAULT_LANGUAGE = "ru"
_DEFAULT_STATE_CODE = "default"
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


def _as_language_map(value: Any) -> dict[str, str]:
    if isinstance(value, dict):
        return {
            str(lang): str(text)
            for lang, text in value.items()
            if text is not None
        }

    normalized = "" if value is None else str(value)
    return {
        "ru": normalized,
        "en": normalized,
    }


def _build_template_rows() -> tuple[list[tuple[str, str, str, str, str, str]], list[tuple[str, str, int, str]]]:
    # Local files remain only as seed source; runtime reads from DB.
    from messages.messageMap import ADDITIONAL_MESSAGES, STATE_MESSAGE_MAP
    from messages.user import MESSAGES

    rows: list[tuple[str, str, str, str, str]] = []

    for message_key, message_data in MESSAGES.items():
        label_by_language = _as_language_map(message_data.get("label", ""))

        if "states" in message_data:
            state_map = message_data["states"]
            for state_code, state_data in state_map.items():
                text_by_language = _as_language_map(state_data.get("text", ""))
                placeholders = state_data.get(
                    "placeholders",
                    message_data.get("placeholders", []),
                )
                placeholders_json = json.dumps(placeholders, ensure_ascii=False)

                normalized_state = (
                    _DEFAULT_STATE_CODE
                    if state_code == _DEFAULT_STATE_CODE
                    else str(state_code)
                )

                for language, text in text_by_language.items():
                    label = (
                        label_by_language.get(language)
                        or label_by_language.get(_DEFAULT_LANGUAGE)
                        or ""
                    )
                    rows.append(
                        (
                            message_key,
                            normalized_state,
                            language,
                            label,
                            text,
                            placeholders_json,
                        )
                    )
        else:
            text_by_language = _as_language_map(message_data.get("text", ""))
            placeholders = message_data.get("placeholders", [])
            placeholders_json = json.dumps(placeholders, ensure_ascii=False)

            for language, text in text_by_language.items():
                label = (
                    label_by_language.get(language)
                    or label_by_language.get(_DEFAULT_LANGUAGE)
                    or ""
                )
                rows.append(
                    (
                        message_key,
                        _DEFAULT_STATE_CODE,
                        language,
                        label,
                        text,
                        placeholders_json,
                    )
                )

    flow_rows: list[tuple[str, str, int, str]] = []
    for state_code, message_keys in STATE_MESSAGE_MAP.items():
        seen: set[str] = set()
        ordered_keys = list(message_keys) + list(ADDITIONAL_MESSAGES)

        for order, message_key in enumerate(ordered_keys, start=1):
            if message_key in seen:
                continue
            seen.add(message_key)

            category = "additional" if message_key in ADDITIONAL_MESSAGES else "workflow"
            flow_rows.append((state_code, message_key, order, category))

    return rows, flow_rows


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


async def _seed_message_templates(conn: asyncpg.Connection) -> None:
    template_rows, flow_rows = _build_template_rows()

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
