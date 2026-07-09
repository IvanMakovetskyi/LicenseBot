from .admin import router as adminRouter
from .createClient import router as createClientRouter
from .deleteClient import router as deleteClientRouter
from .messageAdmin import router as messageAdminRouter
from .send import router as sendRouter

allRouters = [
    adminRouter,
    createClientRouter,
    deleteClientRouter,
    messageAdminRouter,
    sendRouter,
]
