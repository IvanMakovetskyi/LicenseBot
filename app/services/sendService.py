from repositories.messageTemplateRepository import (
    getAvailableMessagesForState,
    resolveMessageTemplate,
)

DEFAULT_LANGUAGE = "ru"


async def resolveMessage(
    messageKey: str,
    stateCode: str | None = None,
    language: str = DEFAULT_LANGUAGE,
) -> dict:
    return await resolveMessageTemplate(
        messageKey=messageKey,
        stateCode=stateCode,
        language=language,
    )


async def getAvailableMessages(
    stateCode: str,
    language: str = DEFAULT_LANGUAGE,
    lastMessageKey: str | None = None,
) -> list[dict]:
    rows = await getAvailableMessagesForState(stateCode, language)

    return [
        {
            "key": row["message_key"],
            "label": row["label"],
            "is_last": row["message_key"] == lastMessageKey if lastMessageKey else False,
        }
        for row in rows
    ]
