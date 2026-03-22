import os

from dotenv import find_dotenv, load_dotenv


_loaded_env_name = None


def load_environment(force=False):
    global _loaded_env_name

    env_name = os.getenv("APP_ENV", "development")
    if _loaded_env_name == env_name and not force:
        return

    dotenv_filename = ".env.test" if env_name == "test" else ".env"
    dotenv_path = find_dotenv(dotenv_filename, usecwd=True)
    if dotenv_path:
        load_dotenv(dotenv_path, override=False)

    _loaded_env_name = env_name
