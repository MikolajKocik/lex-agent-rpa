from dotenv import load_dotenv
from src.infrastructure.keyvault.client import POSTGRES_PASSWORD
import asyncpg
from contextlib import asynccontextmanager
import os
import logging

load_dotenv()
logger = logging.getLogger("databases")


@asynccontextmanager
async def get_postgres_connection(readonly: bool = False):
    """Establishes an asyncpg connection to PostgreSQL with transaction management."""
    user = os.getenv("DB_USER", "lex_user")
    conn = await asyncpg.connect(
        user=user,
        password=POSTGRES_PASSWORD,
        database=os.getenv("DB_NAME", "lex_agent_db"),
        host=os.getenv("DB_HOST", "localhost"),
    )
    try:
        if readonly:
            async with conn.transaction(readonly=True, isolation="repeatable_read"):
                yield conn
        else:
            async with conn.transaction():
                yield conn
    except Exception as e:
        logger.exception("Database error: %s", e)
        raise
    finally:
        await conn.close()
