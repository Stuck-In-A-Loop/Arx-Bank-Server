from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator, Generator
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from .face_data_handling import load_init_face_data
import pickle

# from sqlmodel.ext.asyncio.session import create_async_engine, AsyncSession

from arx_bank_server.setup import logger, settings

engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)


# def run_sync_tables():
#     SQLModel.metadata.create_all(engine)


async def run_migrations():
    async with AsyncSession(engine) as session:
        with open("migrations.sql", "r") as f:
            migrations = f.read().replace("\n", "").split(";")
        for migration in migrations:
            if migration:
                await session.exec(text(migration))
        await session.commit()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as session:
        yield session


@asynccontextmanager
async def get_async_session_opener() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as session:
        yield session


class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)


class UserModel(UserBase):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    age: int | None = Field(default=None)
    phone: str | None = Field(default=None)
    face_id: str | None = Field(default=None, unique=True)
    trained: bool = Field(default=False)


class UserLogin(UserBase):
    password: str = Field(nullable=False)


class UserCreate(UserBase):
    name: str = Field(index=True)
    age: int | None = Field(default=None, index=True)
    phone: str | None = Field(default=None)
    face_id: str | None = Field(default=None, unique=True)
    password: str = Field(nullable=False)


class User(UserModel, table=True):
    password: str = Field(nullable=False)
    face_data: bytes | None = Field(default=None)

    __table_args__ = {"extend_existing": True}


async def create_init_user():
    data = load_init_face_data()
    users = [
        {
            "name": "Cristian Iordachescu",
            "age": 23,
            "email": "ci239@student.ugal.ro",
            "phone": "0723456789",
            "face_id": "cristianiordachescu",
            "password": "password",
            "trained": True,
            "face_data": pickle.dumps(data["cristianiordachescu"]),
        },
        {
            "name": "Alexandru Creanga",
            "age": 22,
            "email": "ac662@student.ugal.ro",
            "phone": "0723456789",
            "face_id": "alexandrucreanga",
            "password": "password",
            "trained": True,
            "face_data": pickle.dumps(data["alexandrucreanga"]),
        },
        {
            "name": "Vlad Gorobtov",
            "age": 22,
            "email": "vg182@student.ugal.ro",
            "phone": "0723456789",
            "face_id": "vladgorobtov",
            "password": "password",
            "trained": True,
            "face_data": pickle.dumps(data["vladgorobtov"]),
        },
        {
            "name": "Alexandru Sandru",
            "age": 25,
            "email": "as496@student.ugal.ro",
            "phone": "0723456789",
            "face_id": "alexandrusandru",
            "password": "password",
            "trained": True,
            "face_data": pickle.dumps(data["alexandrusandru"]),
        },
    ]
    async with AsyncSession(engine) as session:
        for user in users:
            # check if user already exists
            user_exists = (
                await session.exec(select(User).where(User.email == user["email"]))
            ).first()
            if user_exists:
                continue
            logger.debug(f"Creating user: {user['email']}")
            session.add(User(**user))
        await session.commit()
