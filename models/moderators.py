from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    Boolean,
    select,
    update,
    delete,
)
from sqlalchemy.orm import declarative_base, relationship, joinedload
from .custom_types import JsonList
from db import Base, async_session
import json


class Moderator(Base):
    __tablename__ = "moderators"

    tg_id = Column(Integer, ForeignKey("users.tg_id"), primary_key=True)
    nick = Column(String)
    request_types = Column(JsonList)
    on_receive_requests = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)

    complaints = relationship("Complaint", back_populates="moderator")
    blogger_requests = relationship("BloggerRequest", back_populates="moderator")
    buildings_requests = relationship("BuildingsRequest", back_populates="moderator")
    improvements_requests = relationship(
        "ImprovementsRequest", back_populates="moderator"
    )
    moderation_requests = relationship("ModerationRequest", back_populates="moderator")
    errors_requests = relationship("ErrorRequest", back_populates="moderator")

    user = relationship("User", back_populates="moderator", uselist=False)

    @classmethod
    async def add_moderator(cls, tg_id: int, nick: str, request_types: list):
        async with async_session() as session:
            async with session.begin():
                user = cls(tg_id=tg_id, nick=nick, request_types=request_types)
                session.add(user)

    @classmethod
    async def delete_moderator(cls, tg_id: int):
        async with async_session() as session:
            async with session.begin():
                await session.execute(delete(cls).where(cls.tg_id == tg_id))

    @classmethod
    async def get_moderators(cls):
        async with async_session() as session:
            result = await session.execute(select(cls))
            return result.scalars().all()

    @classmethod
    async def get_active_moderators(cls):
        async with async_session() as session:
            result = await session.execute(select(cls).where(cls.is_active == True))
            return result.scalars().all()

    @classmethod
    async def get_moderator(cls, tg_id: int):
        async with async_session() as session:
            result = await session.execute(
                select(cls)
                .options(joinedload(cls.user), joinedload(cls.complaints))
                .where(cls.tg_id == tg_id)
            )
            return result.unique().scalar_one_or_none()

    @classmethod
    async def update_moderator(
        cls,
        tg_id: int,
        request_types: list = None,
        nick: str = None,
        on_receive_requests: bool = None,
        is_active: bool = None,
    ):
        values_to_update = {}
        if request_types:
            values_to_update["request_types"] = request_types
        if on_receive_requests != None:
            values_to_update["on_receive_requests"] = on_receive_requests
        if is_active != None:
            values_to_update["is_active"] = is_active
        if nick != None:
            values_to_update["nick"] = nick

        async with async_session() as session:
            async with session.begin():
                await session.execute(
                    update(cls).where(cls.tg_id == tg_id).values(**values_to_update)
                )

    def __repr__(self):
        return f"<{self.tg_id}, {'Активен' if self.is_active else 'Неактивен'}>"

    # @classmethod
    # async def get_moderator_by_username(cls, username_substr: str):
    # 	 async with async_session() as session:
    # 		 result = await session.execute(
    # 			 select(cls).where(cls.username.like(f"%{username_substr}%"))
    # 		 )
    # 		 return result.scalars().all()
