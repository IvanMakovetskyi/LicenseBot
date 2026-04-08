from aiogram import Dispatcher
from handlers import allRouters

def setupRouters(dp: Dispatcher):
    for router in allRouters:
        dp.include_router(router)
