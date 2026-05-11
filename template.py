# create_structure.py
from pathlib import Path

# Create in current directory
BASE_DIR = Path(".")

FILES = {
    "app/__init__.py": "",
    "app/main.py": "# App factory + lifespan (DB/Redis init/teardown)\n",

    "app/core/__init__.py": "",
    "app/core/config.py": "# All env vars via pydantic-settings\n",
    "app/core/database.py": "# Tortoise ORM init + TORTOISE_ORM_CONFIG\n",
    "app/core/redis.py": "# Singleton async Redis client\n",
    "app/core/logging.py": "# Structured logging setup\n",

    "app/models/__init__.py": "",
    "app/models/db.py": "# Session + Message ORM models\n",
    "app/models/schemas.py": "# Pydantic request/response schemas\n",

    "app/routers/__init__.py": "",
    "app/routers/chat.py": "# All endpoints (chat, sessions list/detail/delete)\n",

    "app/services/__init__.py": "",
    "app/services/agent.py": "# GPT-4o tool loop (async, with tiktoken counting)\n",
    "app/services/executor.py": "# AWS CLI subprocess runner + blocklist\n",
    "app/services/session.py": "# DB read/write + Redis cache invalidation\n",
    "app/services/rate_limiter.py": "# Per-IP sliding window via Redis sorted set\n",

    "docker-compose.yml": "# postgres + redis + app with healthchecks\n",
    "Dockerfile": "# Python 3.12 + AWS CLI v2 install\n",
    "pyproject.toml": "# aerich migration config\n",
    "requirements.txt": "",
}

def create_project_structure():
    for relative_path, content in FILES.items():
        file_path = BASE_DIR / relative_path

        # Create directories
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Create file
        if not file_path.exists():
            file_path.write_text(content, encoding="utf-8")
            print(f"Created: {file_path}")
        else:
            print(f"Skipped: {file_path}")

if __name__ == "__main__":
    create_project_structure()
    print("\nProject structure created in current directory.")