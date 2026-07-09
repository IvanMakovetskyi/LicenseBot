"""Low-level DB access for message templates and client message flows.

Runtime message resolution and the admin management panel both go through this
module. Nothing here imports the legacy ``messages/`` seed files – those are only
used by the seeder in ``database.seed``.
"""

from __future__ import annotations

from typing import Optional, Sequence

from database.db import execute, fetch, fetchrow

DEFAULT_STATE_CODE = "default"
DEFAULT_LANGUAGE = "ru"


def _fallback_sql(prefix: str, pState: str, pLang: str, pDState: str, pDLang: str) -> tuple[str, str]:
    """Build the 4-level fallback WHERE and ORDER-BY snippets.

    Placeholder numbers are passed in so each query can use its own parameter
    layout while keeping the fallback priority identical:
      1. state + language  2. default + language  3. state + ru  4. default + ru
    """
    sc = f"{prefix}state_code"
    lg = f"{prefix}language"
    match = (
        f"({sc} = {pState} AND {lg} = {pLang})"
        f" OR ({sc} = {pDState} AND {lg} = {pLang})"
        f" OR ({sc} = {pState} AND {lg} = {pDLang})"
        f" OR ({sc} = {pDState} AND {lg} = {pDLang})"
    )
    order = (
        "CASE"
        f" WHEN {sc} = {pState} AND {lg} = {pLang} THEN 0"
        f" WHEN {sc} = {pDState} AND {lg} = {pLang} THEN 1"
        f" WHEN {sc} = {pState} AND {lg} = {pDLang} THEN 2"
        " ELSE 3 END"
    )
    return match, order


# --------------------------------------------------------------------------- #
# Runtime resolution
# --------------------------------------------------------------------------- #
async def resolveTemplate(
    messageKey: str,
    stateCode: Optional[str] = None,
    language: str = DEFAULT_LANGUAGE,
    includeInactive: bool = False,
):
    """Resolve a single template using the 4-level fallback.

    1. message_key + state + language (exact)
    2. message_key + default + language
    3. message_key + state + ru
    4. message_key + default + ru

    Returns the matched row or ``None`` when nothing usable exists.
    """
    effectiveState = stateCode or DEFAULT_STATE_CODE
    activeClause = "" if includeInactive else "AND is_active = TRUE"
    match, order = _fallback_sql("", "$2", "$3", "$4", "$5")

    return await fetchrow(
        f"""
        SELECT
            message_key,
            state_code,
            language,
            label,
            text,
            placeholders,
            message_category,
            display_order,
            is_active
        FROM message_templates
        WHERE message_key = $1
          {activeClause}
          AND ({match})
        ORDER BY {order}
        LIMIT 1
        """,
        messageKey,
        effectiveState,
        language,
        DEFAULT_STATE_CODE,
        DEFAULT_LANGUAGE,
    )


async def getUsableFlowMessages(
    stateCode: str,
    language: str = DEFAULT_LANGUAGE,
):
    """Return active flow rows for a state that have a usable active template.

    A key is only returned when the fallback resolves to at least one active
    template, so the normal send UI never shows a dead entry.
    """
    match, order = _fallback_sql("mt.", "$1", "$2", "$3", "$4")

    return await fetch(
        f"""
        SELECT
            flow.message_key,
            flow.display_order,
            flow.message_category,
            t.label AS label
        FROM client_message_flows AS flow
        JOIN LATERAL (
            SELECT mt.label
            FROM message_templates AS mt
            WHERE mt.message_key = flow.message_key
              AND mt.is_active = TRUE
              AND ({match})
            ORDER BY {order}
            LIMIT 1
        ) AS t ON TRUE
        WHERE flow.us_state = $1
          AND flow.is_active = TRUE
        ORDER BY flow.display_order ASC, flow.message_key ASC
        """,
        stateCode,
        language,
        DEFAULT_STATE_CODE,
        DEFAULT_LANGUAGE,
    )


# --------------------------------------------------------------------------- #
# Template management (admin / audit)
# --------------------------------------------------------------------------- #
async def listTemplates(includeInactive: bool = True):
    activeClause = "" if includeInactive else "WHERE is_active = TRUE"
    return await fetch(
        f"""
        SELECT
            message_key,
            state_code,
            language,
            label,
            text,
            placeholders,
            message_category,
            display_order,
            is_active
        FROM message_templates
        {activeClause}
        ORDER BY message_key ASC, state_code ASC, language ASC
        """
    )


async def listMessageKeys() -> list[str]:
    rows = await fetch(
        "SELECT DISTINCT message_key FROM message_templates ORDER BY message_key ASC"
    )
    return [row["message_key"] for row in rows]


async def getTemplateExact(
    messageKey: str,
    stateCode: str,
    language: str,
):
    """Fetch the exact template row (no fallback), including inactive ones."""
    return await fetchrow(
        """
        SELECT
            message_key,
            state_code,
            language,
            label,
            text,
            placeholders,
            message_category,
            display_order,
            is_active
        FROM message_templates
        WHERE message_key = $1
          AND state_code = $2
          AND language = $3
        """,
        messageKey,
        stateCode,
        language,
    )


async def upsertTemplate(
    messageKey: str,
    stateCode: str,
    language: str,
    label: str,
    text: str,
    placeholders: str,
    messageCategory: str = "workflow",
    displayOrder: int = 0,
    isActive: bool = True,
) -> None:
    await execute(
        """
        INSERT INTO message_templates (
            message_key,
            state_code,
            language,
            label,
            text,
            placeholders,
            message_category,
            display_order,
            is_active,
            updated_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
        ON CONFLICT (message_key, state_code, language) DO UPDATE
        SET label = EXCLUDED.label,
            text = EXCLUDED.text,
            placeholders = EXCLUDED.placeholders,
            message_category = EXCLUDED.message_category,
            display_order = EXCLUDED.display_order,
            is_active = EXCLUDED.is_active,
            updated_at = NOW()
        """,
        messageKey,
        stateCode,
        language,
        label,
        text,
        placeholders,
        messageCategory,
        displayOrder,
        isActive,
    )


async def setTemplateActive(
    messageKey: str,
    stateCode: str,
    language: str,
    isActive: bool,
) -> str:
    return await execute(
        """
        UPDATE message_templates
        SET is_active = $4, updated_at = NOW()
        WHERE message_key = $1
          AND state_code = $2
          AND language = $3
        """,
        messageKey,
        stateCode,
        language,
        isActive,
    )


# --------------------------------------------------------------------------- #
# Flow management (admin / audit)
# --------------------------------------------------------------------------- #
async def listFlowStates() -> list[str]:
    rows = await fetch(
        "SELECT DISTINCT us_state FROM client_message_flows ORDER BY us_state ASC"
    )
    return [row["us_state"] for row in rows]


async def listFlows(usState: str, includeInactive: bool = True):
    activeClause = "" if includeInactive else "AND is_active = TRUE"
    return await fetch(
        f"""
        SELECT
            us_state,
            message_key,
            display_order,
            message_category,
            is_active
        FROM client_message_flows
        WHERE us_state = $1
          {activeClause}
        ORDER BY display_order ASC, message_key ASC
        """,
        usState,
    )


async def listAllFlows():
    return await fetch(
        """
        SELECT
            us_state,
            message_key,
            display_order,
            message_category,
            is_active
        FROM client_message_flows
        ORDER BY us_state ASC, display_order ASC, message_key ASC
        """
    )


async def addFlow(
    usState: str,
    messageKey: str,
    displayOrder: int,
    messageCategory: str = "workflow",
) -> None:
    # ON CONFLICT keeps the flow free of duplicate (state, key) rows.
    await execute(
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
        usState,
        messageKey,
        displayOrder,
        messageCategory,
    )


async def removeFlow(usState: str, messageKey: str) -> None:
    await execute(
        "DELETE FROM client_message_flows WHERE us_state = $1 AND message_key = $2",
        usState,
        messageKey,
    )


async def updateFlowOrder(usState: str, messageKey: str, displayOrder: int) -> None:
    await execute(
        """
        UPDATE client_message_flows
        SET display_order = $3
        WHERE us_state = $1 AND message_key = $2
        """,
        usState,
        messageKey,
        displayOrder,
    )


async def updateFlowCategory(usState: str, messageKey: str, messageCategory: str) -> None:
    await execute(
        """
        UPDATE client_message_flows
        SET message_category = $3
        WHERE us_state = $1 AND message_key = $2
        """,
        usState,
        messageKey,
        messageCategory,
    )


async def nextFlowOrder(usState: str) -> int:
    row = await fetchrow(
        "SELECT COALESCE(MAX(display_order), 0) AS max_order FROM client_message_flows WHERE us_state = $1",
        usState,
    )
    return int(row["max_order"]) + 1 if row else 1


def orderTemplatesByFallback(
    templates: Sequence[dict],
    stateCode: str,
    language: str,
) -> list[dict]:
    """In-memory mirror of the SQL fallback ordering (used by the audit)."""

    def rank(tpl: dict) -> int:
        if tpl["state_code"] == stateCode and tpl["language"] == language:
            return 0
        if tpl["state_code"] == DEFAULT_STATE_CODE and tpl["language"] == language:
            return 1
        if tpl["state_code"] == stateCode and tpl["language"] == DEFAULT_LANGUAGE:
            return 2
        if tpl["state_code"] == DEFAULT_STATE_CODE and tpl["language"] == DEFAULT_LANGUAGE:
            return 3
        return 99

    return sorted(templates, key=rank)
