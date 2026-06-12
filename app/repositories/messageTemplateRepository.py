import json

from database.db import fetch, fetchrow


DEFAULT_STATE_CODE = "default"
DEFAULT_LANGUAGE = "ru"


async def getAvailableMessagesForState(
    stateCode: str,
    language: str = DEFAULT_LANGUAGE,
):
    return await fetch(
        """
        SELECT
            flow.message_key,
            COALESCE(state_tpl.label, default_tpl.label) AS label
        FROM client_message_flows AS flow
        LEFT JOIN message_templates AS state_tpl
            ON state_tpl.message_key = flow.message_key
            AND state_tpl.state_code = $1
            AND state_tpl.language = $2
        LEFT JOIN message_templates AS default_tpl
            ON default_tpl.message_key = flow.message_key
            AND default_tpl.state_code = $3
            AND default_tpl.language = $2
        WHERE flow.us_state = $1
        ORDER BY flow.display_order ASC, flow.message_key ASC
        """,
        stateCode,
        language,
        DEFAULT_STATE_CODE,
    )


async def resolveMessageTemplate(
    messageKey: str,
    stateCode: str | None = None,
    language: str = DEFAULT_LANGUAGE,
):
    effectiveState = stateCode or DEFAULT_STATE_CODE

    row = await fetchrow(
        """
        SELECT message_key, label, text, placeholders
        FROM message_templates
        WHERE message_key = $1
          AND language = $2
          AND state_code IN ($3, $4)
        ORDER BY
            CASE WHEN state_code = $3 THEN 0 ELSE 1 END
        LIMIT 1
        """,
        messageKey,
        language,
        effectiveState,
        DEFAULT_STATE_CODE,
    )

    if not row:
        raise ValueError(
            f"Message template '{messageKey}' not found for state '{effectiveState}' and language '{language}'."
        )

    placeholdersRaw = row["placeholders"] or "[]"
    placeholders = json.loads(placeholdersRaw)

    return {
        "key": row["message_key"],
        "label": row["label"],
        "text": row["text"],
        "placeholders": placeholders,
    }
