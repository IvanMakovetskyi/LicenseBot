from database.db import execute, fetch, fetchrow


async def getClientByChatId(chatId: int):
    return await fetchrow(
        "SELECT * FROM clients WHERE chat_id = $1",
        chatId,
    )


async def getClientById(clientId: int):
    return await fetchrow(
        "SELECT * FROM clients WHERE id = $1",
        clientId,
    )


async def getAllClients():
    return await fetch(
        "SELECT * FROM clients ORDER BY id DESC"
    )


async def createClient(
    chatId: int,
    fullName: str,
    usState: str,
    language: str = "ru",
    status: str = "new",
):
    await execute(
        """
        INSERT INTO clients (chat_id, full_name, us_state, language, status)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (chat_id) DO NOTHING
        """,
        chatId,
        fullName,
        usState,
        language,
        status,
    )


async def deleteClient(clientId: int):
    await execute(
        "DELETE FROM clients WHERE id = $1",
        clientId,
    )


async def updateClientStatus(clientId: int, status: str):
    await execute(
        """
        UPDATE clients
        SET status = $1, updated_at = NOW()
        WHERE id = $2
        """,
        status,
        clientId,
    )


async def updateClientLastSentMessage(
    clientId: int,
    messageKey: str,
    messageLabel: str,
):
    await execute(
        """
        UPDATE clients
        SET
            last_sent_message_key = $1,
            last_sent_message_label = $2,
            last_sent_at = NOW(),
            updated_at = NOW()
        WHERE id = $3
        """,
        messageKey,
        messageLabel,
        clientId,
    )
