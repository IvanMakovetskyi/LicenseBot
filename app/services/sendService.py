from messages.user import MESSAGES
from messages.messageMap import STATE_MESSAGE_MAP, ADDITIONAL_MESSAGES

DEFAULT_LANGUAGE = "ru"


def getLocalized(value, language: str = DEFAULT_LANGUAGE):
    if isinstance(value, dict):
        return value.get(language) or value.get(DEFAULT_LANGUAGE)

    return value


def resolveMessage(
    messageKey: str,
    stateCode: str | None = None,
    language: str = DEFAULT_LANGUAGE,
) -> dict:
    messageData = MESSAGES[messageKey]

    label = getLocalized(messageData["label"], language)

    if "states" in messageData:
        statesData = messageData["states"]
        stateData = statesData.get(stateCode) or statesData.get("default")

        if not stateData:
            raise ValueError(
                f"Message '{messageKey}' has no template for state '{stateCode}' and no default template."
            )

        return {
            "label": label,
            "text": getLocalized(stateData["text"], language),
            "placeholders": stateData.get(
                "placeholders",
                messageData.get("placeholders", []),
            ),
        }

    return {
        "label": label,
        "text": getLocalized(messageData["text"], language),
        "placeholders": messageData.get("placeholders", []),
    }


def getAvailableMessages(stateCode: str) -> list[str]:
    return STATE_MESSAGE_MAP[stateCode] + ADDITIONAL_MESSAGES


def getMessageLabel(messageKey: str) -> str:
    return getLocalized(MESSAGES[messageKey]["label"], DEFAULT_LANGUAGE)
