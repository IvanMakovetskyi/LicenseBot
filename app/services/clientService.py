from repositories.caseRepository import (
    getAllCases,
    getCase,
    getCaseById,
    updateCaseStatus,
    createCase
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

    @staticmethod
    async def createClient(chatId: int, fullName: str, usState: str, status: str):
        createCase(chatId, fullName, usState, status)


clientService = ClientService()
