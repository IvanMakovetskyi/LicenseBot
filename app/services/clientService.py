from repositories.caseRepository import (
    getAllCases,
    getCase,
    getCaseById,
    updateCaseStatus
)

class ClientService:
    @staticmethod
    async def getAllClients():
        return getAllCases()

    @staticmethod
    async def getClientById(clientId: int):
        return getCaseById(clientId)

    @staticmethod
    async def getClientByChatId(chatId: int):
        return getCase(chatId)

    @staticmethod
    async def updateStatus(clientId: int, status: str):
        updateCaseStatus(clientId, status)


clientService = ClientService()
