from sqlalchemy import Column, String, Boolean, select, update
from sqlalchemy.orm import relationship
from .custom_types import JsonList
from db import async_session
from utils.formatter import get_datetime
from datetime import datetime
from .requests_pattern import Request
from .global_counter import GlobalCounter


class ImprovementsRequest(Request):
    __tablename__ = "improvements_requests"

    nick = Column(String)
    request_type = Column(String)
    idea = Column(String)
    document_id = Column(String)
    photo_ids = Column(JsonList)
    video_ids = Column(JsonList)

    moderator = relationship(
        "Moderator", back_populates="improvements_requests", uselist=False
    )
    user = relationship("User", back_populates="improvements_requests", uselist=False)

    @classmethod
    async def add_request(
        cls,
        user_id: int,
        nick: str,
        request_type: str,
        idea: str = None,
        document_id: str = None,
        photo_ids: list[str] = [],
        video_ids: list[str] = [],
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
                    idea=idea,
                    document_id=document_id,
                    photo_ids=photo_ids,
                    video_ids=video_ids,
                    moderator_id=moderator_id,
                    context=context,
                    is_active=is_active,
                )
                session.add(request)
                await session.flush()  # Получаем ID после INSERT
                return request.id
