from messages.user import MESSAGES
from messages.messageMap import STATE_MESSAGE_MAP, ADDITIONAL_MESSAGES

def resolveMessage(messageKey: str, stateCode: str | None = None) -> dict:
    messageData = MESSAGES[messageKey]

    if "states" in messageData:
        stateData = messageData["states"][stateCode]
        return {
            "label": messageData["label"],
            "text": stateData["text"],
            "placeholders": stateData.get("placeholders", messageData.get("placeholders", [])),
        }
    
    return {
        "label": messageData["label"],
        "text": messageData["text"],
        "placeholders": messageData.get("placeholders", []),
    }

def getAvailableMessages(stateCode: str) -> list[str]:
    return STATE_MESSAGE_MAP[stateCode] + ADDITIONAL_MESSAGES

def getMessageLabel(messageKey: str) -> str:
    return MESSAGES[messageKey]["label"]
