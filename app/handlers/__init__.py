from .start import router as startRouter
from .admin import router as adminRouter
from .send import router as sendRouter
from .status import router as statusRouter
from .document import router as documentRouter
from .echo import router as echoRouter

allRouters = [
    startRouter,
    adminRouter,
    sendRouter,
    statusRouter,
    documentRouter,
    echoRouter,
]
