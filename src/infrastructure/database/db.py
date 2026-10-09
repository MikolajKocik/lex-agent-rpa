from dotenv import load_dotenv
from src.infrastructure.keyvault.client import POSTGRES_PASSWORD
import asyncpg
from contextlib import asynccontextmanager
import os
import logging

load_dotenv()
logger = logging.getLogger("databases")

@asynccontextmanager
async def get_postgres_connection():
    conn = await asyncpg.connect(
        user="read_only_user",
        password=POSTGRES_PASSWORD,
        database=os.getenv("DB_NAME"),
        host=os.getenv("DB_HOST"),
    )
    try:
        async with conn.transaction(readonly=True, isolation="repeatable_read"):
            yield conn
    except Exception as e:
        logger.exception(f"Database error: {e}")
        raise
    finally:
        await conn.close()
