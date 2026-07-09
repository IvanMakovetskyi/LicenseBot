"""Business logic for messages.

This is the single entry point the runtime send flow and the admin panel use.
Runtime never touches the ``messages/`` seed files; only :func:`runAudit`
imports them (lazily) to compare the seed source against the DB.
"""

from __future__ import annotations

import json
from typing import Optional

from repositories import messageRepository as repo
from repositories.messageRepository import (
    DEFAULT_LANGUAGE,
    DEFAULT_STATE_CODE,
)

# Shown to the admin when a mapped message has no usable template at all.
MESSAGE_NOT_CONFIGURED = (
    "Сообщение не настроено для этого штата и не имеет default версии."
)

EDITABLE_STATES = ["default", "CA", "FL", "NY", "PA", "NC"]
CLIENT_STATES = ["CA", "FL", "NY", "PA", "NC"]
LANGUAGES = ["ru", "en"]
CATEGORIES = ["workflow", "additional"]


# --------------------------------------------------------------------------- #
# Placeholders helpers
# --------------------------------------------------------------------------- #
def loadPlaceholders(raw) -> list[str]:
    """Best-effort parse of a stored placeholders value (never raises)."""
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(item) for item in raw]
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return []
    if isinstance(data, list):
        return [str(item) for item in data]
    return []


def isValidPlaceholdersJson(raw) -> bool:
    if raw is None:
        return False
    if isinstance(raw, list):
        return all(isinstance(item, str) for item in raw)
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return False
    return isinstance(data, list) and all(isinstance(item, str) for item in data)


def parsePlaceholders(rawInput: str) -> list[str]:
    """Parse admin input into a list of placeholder names.

    Accepts either a JSON array (``["amount", "login"]``) or a comma separated
    list (``amount, login``). Raises ``ValueError`` on malformed input so the
    caller can reject the save.
    """
    text = (rawInput or "").strip()
    if not text or text in {"-", "[]"}:
        return []

    if text.startswith("["):
        data = json.loads(text)  # raises ValueError on bad JSON
        if not isinstance(data, list) or not all(isinstance(item, str) for item in data):
            raise ValueError("JSON must be a list of strings")
        return [item.strip() for item in data if item.strip()]

    return [part.strip() for part in text.split(",") if part.strip()]


def placeholdersToJson(placeholders: list[str]) -> str:
    return json.dumps(placeholders, ensure_ascii=False)


def placeholdersToInput(placeholders: list[str]) -> str:
    return ", ".join(placeholders)


def _rowToMessage(row) -> dict:
    return {
        "key": row["message_key"],
        "state_code": row["state_code"],
        "language": row["language"],
        "label": row["label"],
        "text": row["text"],
        "placeholders": loadPlaceholders(row["placeholders"]),
        "is_active": row["is_active"],
    }


# --------------------------------------------------------------------------- #
# Runtime resolution (used by the send flow)
# --------------------------------------------------------------------------- #
async def resolveMessage(
    messageKey: str,
    stateCode: Optional[str] = None,
    language: str = DEFAULT_LANGUAGE,
) -> Optional[dict]:
    """Resolve a message with the 4-level fallback.

    Returns ``None`` instead of raising when nothing usable exists, so the
    handler can show :data:`MESSAGE_NOT_CONFIGURED` rather than crashing.
    """
    row = await repo.resolveTemplate(messageKey, stateCode, language or DEFAULT_LANGUAGE)
    if not row:
        return None
    return _rowToMessage(row)


async def getAvailableMessages(
    stateCode: str,
    language: str = DEFAULT_LANGUAGE,
    lastMessageKey: Optional[str] = None,
) -> list[dict]:
    rows = await repo.getUsableFlowMessages(stateCode, language or DEFAULT_LANGUAGE)
    return [
        {
            "key": row["message_key"],
            "label": row["label"] or row["message_key"],
            "is_last": row["message_key"] == lastMessageKey if lastMessageKey else False,
        }
        for row in rows
    ]


# --------------------------------------------------------------------------- #
# Admin: template management
# --------------------------------------------------------------------------- #
async def listMessageKeys() -> list[str]:
    return await repo.listMessageKeys()


async def listTemplates() -> list:
    return await repo.listTemplates(includeInactive=True)


async def getTemplate(messageKey: str, stateCode: str, language: str) -> Optional[dict]:
    row = await repo.getTemplateExact(messageKey, stateCode, language)
    if not row:
        return None
    result = _rowToMessage(row)
    result["message_category"] = row["message_category"]
    result["display_order"] = row["display_order"]
    return result


async def saveTemplate(
    messageKey: str,
    stateCode: str,
    language: str,
    label: str,
    text: str,
    placeholders: list[str],
    messageCategory: str = "workflow",
    displayOrder: int = 0,
    isActive: bool = True,
) -> None:
    await repo.upsertTemplate(
        messageKey=messageKey,
        stateCode=stateCode,
        language=language,
        label=label,
        text=text,
        placeholders=placeholdersToJson(placeholders),
        messageCategory=messageCategory,
        displayOrder=displayOrder,
        isActive=isActive,
    )


async def setTemplateActive(
    messageKey: str,
    stateCode: str,
    language: str,
    isActive: bool,
) -> None:
    await repo.setTemplateActive(messageKey, stateCode, language, isActive)


# --------------------------------------------------------------------------- #
# Admin: flow management
# --------------------------------------------------------------------------- #
async def getFlows(usState: str):
    return await repo.listFlows(usState, includeInactive=True)


async def addFlowKey(usState: str, messageKey: str, messageCategory: str = "workflow") -> None:
    order = await repo.nextFlowOrder(usState)
    await repo.addFlow(usState, messageKey, order, messageCategory)


async def removeFlowKey(usState: str, messageKey: str) -> None:
    await repo.removeFlow(usState, messageKey)


async def setFlowOrder(usState: str, messageKey: str, displayOrder: int) -> None:
    await repo.updateFlowOrder(usState, messageKey, displayOrder)


async def setFlowCategory(usState: str, messageKey: str, messageCategory: str) -> None:
    await repo.updateFlowCategory(usState, messageKey, messageCategory)


# --------------------------------------------------------------------------- #
# Audit
# --------------------------------------------------------------------------- #
def _resolveInMemory(templatesForKey, stateCode, language, activeOnly=True):
    candidates = [
        tpl for tpl in templatesForKey if (not activeOnly or tpl["is_active"])
    ]
    ordered = repo.orderTemplatesByFallback(candidates, stateCode, language)
    for tpl in ordered:
        matches = (
            (tpl["state_code"] == stateCode and tpl["language"] == language)
            or (tpl["state_code"] == DEFAULT_STATE_CODE and tpl["language"] == language)
            or (tpl["state_code"] == stateCode and tpl["language"] == DEFAULT_LANGUAGE)
            or (tpl["state_code"] == DEFAULT_STATE_CODE and tpl["language"] == DEFAULT_LANGUAGE)
        )
        if matches:
            return tpl
    return None


async def runAudit() -> dict:
    """Cross-check flows, templates and seed files. Returns a structured report."""
    templates = [dict(row) for row in await repo.listTemplates(includeInactive=True)]
    flows = [dict(row) for row in await repo.listAllFlows()]

    # Seed keys come straight from the local source files (audit-only import).
    try:
        from messages.user import MESSAGES  # noqa: WPS433 (lazy, audit only)

        seedKeys = set(MESSAGES.keys())
    except Exception:  # pragma: no cover - seed file optional at audit time
        seedKeys = set()

    templatesByKey: dict[str, list[dict]] = {}
    for tpl in templates:
        templatesByKey.setdefault(tpl["message_key"], []).append(tpl)

    dbKeys = set(templatesByKey.keys())
    flowKeys = {flow["message_key"] for flow in flows}
    activeFlows = [flow for flow in flows if flow["is_active"]]

    report: dict[str, list[str]] = {
        "flows_without_usable_template": [],
        "mapped_missing_state_and_default": [],
        "unreachable_templates": [],
        "seed_only_keys": [],
        "keys_missing_default_template": [],
        "invalid_placeholders": [],
        "inactive_referenced_by_flow": [],
    }

    # 1 & 5. Flow rows whose key does not resolve to a usable active template,
    #        and the structural "no state-specific and no default" case.
    for flow in activeFlows:
        state = flow["us_state"]
        key = flow["message_key"]
        forKey = templatesByKey.get(key, [])

        usable = _resolveInMemory(forKey, state, "ru", activeOnly=True) or _resolveInMemory(
            forKey, state, "en", activeOnly=True
        )
        if not usable:
            report["flows_without_usable_template"].append(f"{state} → {key}")

        hasState = any(tpl["state_code"] == state for tpl in forKey)
        hasDefault = any(tpl["state_code"] == DEFAULT_STATE_CODE for tpl in forKey)
        if not hasState and not hasDefault:
            report["mapped_missing_state_and_default"].append(f"{state} → {key}")

    # 2. Templates whose key is never referenced by any flow.
    for key in sorted(dbKeys - flowKeys):
        report["unreachable_templates"].append(key)

    # 3. Keys present only in the seed files, missing from the DB.
    for key in sorted(seedKeys - dbKeys):
        report["seed_only_keys"].append(key)

    # 4. Keys in DB that have no default-state template at all.
    for key in sorted(dbKeys):
        if not any(tpl["state_code"] == DEFAULT_STATE_CODE for tpl in templatesByKey[key]):
            report["keys_missing_default_template"].append(key)

    # 6. Templates with invalid placeholders JSON.
    for tpl in templates:
        if not isValidPlaceholdersJson(tpl["placeholders"]):
            report["invalid_placeholders"].append(
                f"{tpl['message_key']} [{tpl['state_code']}/{tpl['language']}]"
            )

    # 7. Inactive templates whose key is used by an active flow.
    activeFlowKeys = {flow["message_key"] for flow in activeFlows}
    for tpl in templates:
        if not tpl["is_active"] and tpl["message_key"] in activeFlowKeys:
            report["inactive_referenced_by_flow"].append(
                f"{tpl['message_key']} [{tpl['state_code']}/{tpl['language']}]"
            )

    return report


_AUDIT_TITLES = {
    "flows_without_usable_template": "❌ Flow без рабочего шаблона (штат → ключ)",
    "mapped_missing_state_and_default": "❌ Нет ни шаблона штата, ни default (штат → ключ)",
    "unreachable_templates": "⚠️ Шаблоны, не привязанные ни к одному flow",
    "seed_only_keys": "⚠️ Ключи только в seed-файлах, но не в БД",
    "keys_missing_default_template": "ℹ️ Ключи без default-шаблона",
    "invalid_placeholders": "❌ Некорректный JSON в placeholders",
    "inactive_referenced_by_flow": "⚠️ Выключенные шаблоны, используемые активным flow",
}


def formatAuditReport(report: dict) -> str:
    lines: list[str] = ["📋 Аудит сообщений", ""]
    hasIssues = False

    for key, title in _AUDIT_TITLES.items():
        items = report.get(key, [])
        if not items:
            continue
        hasIssues = True
        lines.append(f"{title} ({len(items)}):")
        lines.extend(f"  • {item}" for item in items)
        lines.append("")

    if not hasIssues:
        lines.append("✅ Проблем не обнаружено.")

    return "\n".join(lines).strip()
