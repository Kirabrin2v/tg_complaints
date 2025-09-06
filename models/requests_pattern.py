from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    select,
    delete,
    update,
    Table,
)
from sqlalchemy.orm import joinedload
from .custom_types import JsonList
from db import Base, async_session
from utils.formatter import get_datetime
import json


class Request(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True)
    global_id = Column(Integer, nullable=False, unique=True)

    date_create = Column(DateTime)
    user_id = Column(Integer, ForeignKey("users.tg_id"), nullable=False)
    request_type = Column(String)
    moderator_id = Column(Integer, ForeignKey("moderators.tg_id"), nullable=True)
    context = Column(JsonList)
    is_active = Column(Boolean, default=True)

    @classmethod
    def __table_cls__(cls, name, metadata, *args, **kwargs):
        """Переопределяем порядок колонок при создании таблицы"""

        first_fields = ["id", "global_id", "date_create", "user_id", "request_type"]
        last_fields = ["moderator_id", "context", "is_active"]

        # Разделим все колонки по группам
        first = []
        middle = []
        last = []

        for col in args:
            if col.name in first_fields:
                first.append((first_fields.index(col.name), col))
            elif col.name in last_fields:
                last.append((last_fields.index(col.name), col))
            else:
                middle.append(col)

        # Упорядочим
        first_sorted = [col for _, col in sorted(first, key=lambda x: x[0])]
        last_sorted = [col for _, col in sorted(last, key=lambda x: x[0])]

        final_columns = first_sorted + middle + last_sorted

        return Table(name, metadata, *final_columns, **kwargs)

    def to_dict(self) -> dict:
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    @classmethod
    async def update_context(cls, request_id: int, context: list):
        async with async_session() as session:
            async with session.begin():
                await session.execute(
                    update(cls).where(cls.id == request_id).values(context=context)
                )

    @classmethod
    async def set_active_status(cls, request_id: int, is_active: bool):
        async with async_session() as session:
            async with session.begin():
                await session.execute(
                    update(cls).where(cls.id == request_id).values(is_active=is_active)
                )

    @classmethod
    async def delete_request(cls, request_id: int):
        async with async_session() as session:
            async with session.begin():
                await session.execute(delete(cls).where(cls.id == request_id))

    @classmethod
    async def get_active_requests(
        cls,
        user_id: int = None,
        request_type: str = None,
        limit: int = -1,
        start_index: int = -1,
    ) -> list:
        if start_index != -1:
            start_index -= 1
        async with async_session() as session:
            result = await session.execute(
                select(cls)
                .where(
                    (cls.is_active == True)
                    & (cls.moderator_id == None)
                    & (user_id == None or cls.user_id == user_id)
                    & (request_type == None or cls.request_type == request_type)
                )
                .order_by(cls.id)
                .limit(limit)
                .offset(start_index)
            )
            return result.scalars().all()

    @classmethod
    async def get_request(cls, request_id: int):
        async with async_session() as session:
            result = await session.execute(
                select(cls)
                .options(joinedload(cls.moderator), joinedload(cls.user))
                .where(cls.id == request_id)
            )
            result = result.scalar_one()

            return result

    @classmethod
    async def set_moderator(cls, request_id: int, moderator_id: int):
        async with async_session() as session:
            async with session.begin():
                await session.execute(
                    update(cls)
                    .where(cls.id == request_id)
                    .values(moderator_id=moderator_id)
                )

    def __repr__(self):
        return f"<Request {self.request_type} user_id={self.user_id} nick={self.nick!r} {self.is_active}>"
