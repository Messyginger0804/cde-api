import os
from dotenv import load_dotenv


load_dotenv()


# API token for simple bearer auth
API_TOKEN = os.getenv("API_TOKEN", "devtoken")


def _build_postgres_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        if not url.startswith("postgresql"):
            raise ValueError("DATABASE_URL must be a PostgreSQL URL (postgresql+psycopg2://...)")
        return url

    host = os.getenv("PGHOST") or "127.0.0.1"
    port = os.getenv("PGPORT") or "5432"
    user = os.getenv("PGUSER")
    password = os.getenv("PGPASSWORD")
    database = os.getenv("PGDATABASE")

    if user and password and database:
        # Basic sanity for port
        try:
            int(port)
        except ValueError:
            raise ValueError("PGPORT must be an integer")
        return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"

    raise ValueError(
        "PostgreSQL configuration required. Set DATABASE_URL or PGUSER, PGPASSWORD, PGDATABASE (optional PGHOST/PGPORT)."
    )


DATABASE_URL = _build_postgres_url()
