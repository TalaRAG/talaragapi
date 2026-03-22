import importlib


def _load_object(path):
    module_name, object_name = path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, object_name)


def create_app(config_object="config.Config"):
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    from app.db import db
    from app.environment import load_environment
    from app.storage import init_storage

    load_environment()
    settings = _load_object(config_object)

    app = FastAPI(title=settings.APP_NAME)
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    db.configure(settings.SQLALCHEMY_DATABASE_URI)
    init_storage(settings)

    from app.routes import register_routes

    register_routes(app)
    return app
