"""Seed source for message templates and flows.

The ``messages/`` package (``user.py`` / ``messageMap.py``) is used ONLY here to
build the initial rows. Runtime message resolution reads from the DB via
``repositories.messageRepository`` and never imports these files.
"""

from __future__ import annotations

import json
from typing import Any

_DEFAULT_LANGUAGE = "ru"
_DEFAULT_STATE_CODE = "default"


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


def build_seed_rows() -> tuple[
    list[tuple[str, str, str, str, str, str]],
    list[tuple[str, str, int, str]],
]:
    """Return ``(template_rows, flow_rows)`` built from the local seed files."""
    from messages.messageMap import ADDITIONAL_MESSAGES, STATE_MESSAGE_MAP
    from messages.user import MESSAGES

    template_rows: list[tuple[str, str, str, str, str, str]] = []

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
                    template_rows.append(
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
                template_rows.append(
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

    return template_rows, flow_rows
