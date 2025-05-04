from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine 
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SYNC_DB_URL = os.getenv("SYNC_DB_URL")
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

sync_engine = create_engine(SYNC_DB_URL)
SyncSessionLocal = sessionmaker(sync_engine)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session