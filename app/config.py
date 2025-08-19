import os
from dotenv import load_dotenv


load_dotenv()


# API token for simple bearer auth
API_TOKEN = os.getenv("API_TOKEN", "devtoken")

# Default to in-memory SQLite for local/testing (no filesystem writes)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")

