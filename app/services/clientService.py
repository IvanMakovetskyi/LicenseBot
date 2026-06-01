from repositories.clientRepository import (
    createClient,
    deleteClient,
    getAllClients,
    getClientByChatId,
    getClientById,
    updateClientLastSentMessage,
    updateClientStatus,
)


class ClientService:
    @staticmethod
    async def getAllClients():
        return await getAllClients()

    @staticmethod
    async def getClientById(clientId: int):
        return await getClientById(clientId)

    @staticmethod
    async def getClientByChatId(chatId: int):
        return await getClientByChatId(chatId)

    @staticmethod
    async def updateStatus(clientId: int, status: str):
        await updateClientStatus(clientId, status)

    @staticmethod
    async def createClient(chatId: int, fullName: str, usState: str, language: str = "ru", status: str = "new"):
        await createClient(chatId, fullName, usState, language, status)

    @staticmethod
    async def deleteClient(clientId: int):
        await deleteClient(clientId)

    @staticmethod
    async def updateLastSentMessage(clientId: int, messageKey: str, messageLabel: str):
        await updateClientLastSentMessage(clientId, messageKey, messageLabel)


clientService = ClientService()
