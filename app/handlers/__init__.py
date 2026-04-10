from .admin import router as adminRouter
from .createClient import router as createClientRouter
from .send import router as sendRouter

allRouters = [
    adminRouter,
    createClientRouter,
    sendRouter,
]
