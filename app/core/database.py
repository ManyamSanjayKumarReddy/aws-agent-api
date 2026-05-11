from tortoise import Tortoise
from app.core.config import get_settings

settings = get_settings()

TORTOISE_ORM_CONFIG = {
    "connections": {
        "default": settings.database_url,
    },
    "apps": {
        "models": {
            "models": ["app.models.db", "aerich.models"],
            "default_connection": "default",
        }
    },
}


async def init_db():
    await Tortoise.init(config=TORTOISE_ORM_CONFIG)
    await Tortoise.generate_schemas()


async def close_db():
    await Tortoise.close_connections()# Tortoise ORM init + TORTOISE_ORM_CONFIG
