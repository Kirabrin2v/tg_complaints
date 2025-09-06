from sqlalchemy import Column, String, Integer, Boolean, select, update
from sqlalchemy.orm import relationship
from .custom_types import JsonList
from db import async_session
from utils.formatter import get_datetime
from datetime import datetime
from .requests_pattern import Request
from .global_counter import GlobalCounter


class ModerationRequest(Request):
    __tablename__ = "moderation_requests"

    nick = Column(String)
    request_type = Column(String)
    name = Column(String)
    years = Column(Integer)
    is_have_experience = Column(Boolean)
    duties_description = Column(String)

    moderator = relationship(
        "Moderator", back_populates="moderation_requests", uselist=False
    )
    user = relationship("User", back_populates="moderation_requests", uselist=False)

    @classmethod
    async def add_request(
        cls,
        user_id: int,
        nick: str,
        request_type: str,
        name: str,
        years: int,
        is_have_experience: bool,
        duties_description: str,
        moderator_id: int = None,
        context: list[str] = [],
        is_active: bool = True,
        date_create: datetime = None,
    ) -> int:
        if not date_create:
            date_create = get_datetime()

        if not context:
            context = []

        async with async_session() as session:
            async with session.begin():
                request = cls(
                    global_id=await GlobalCounter.get_id(),
                    date_create=date_create,
                    nick=nick,
                    user_id=user_id,
                    request_type=request_type,
                    name=name,
                    years=years,
                    is_have_experience=is_have_experience,
                    duties_description=duties_description,
                    moderator_id=moderator_id,
                    context=context,
                    is_active=is_active,
                )
                session.add(request)
                await session.flush()  # Получаем ID после INSERT
                return request.id
