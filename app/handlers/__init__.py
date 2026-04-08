from .start import router as startRouter
from .status import router as statusRouter
from .echo import router as echoRouter

allRouters = [
    startRouter,
    statusRouter,
    echoRouter,
]
