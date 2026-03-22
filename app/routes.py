from fastapi import FastAPI

from app.controllers.documents_controller import router as documents_router
from app.controllers.health_controller import router as health_router
from app.controllers.system_controller import router as system_router
from app.controllers.uploads_controller import router as uploads_router
from app.controllers.users_controller import router as users_router


def register_routes(app: FastAPI):
    app.include_router(health_router)
    app.include_router(system_router)
    app.include_router(users_router)
    app.include_router(documents_router)
    app.include_router(uploads_router)
