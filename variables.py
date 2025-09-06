import asyncio
from models import (
    Moderator,
    Complaint,
    ErrorRequest,
    BloggerRequest,
    BuildingsRequest,
    ImprovementsRequest,
    ModerationRequest,
)
from models import Request as RequestBase
import constants as const
from constants import admin_ids


async def get_moderator_ids():
    global moderator_ids
    if not moderator_ids:
        moderators = await Moderator.get_active_moderators()
        moderator_ids = [moderator.tg_id for moderator in moderators]
    return moderator_ids


async def reload_moderator_ids():
    global moderator_ids
    moderator_ids = []
    await get_moderator_ids()


def request_type_to_db(request_type: str) -> RequestBase:
    if request_type in const.complaint_types:
        return Complaint
    elif request_type in const.errors_types:
        return ErrorRequest
    elif request_type == "blogger_request_other_type":
        return BloggerRequest
    elif request_type == "buildings_request_other_type":
        return BuildingsRequest
    elif request_type == "improvements_request_other_type":
        return ImprovementsRequest
    elif request_type == "moderation_request_other_type":
        return ModerationRequest
    else:
        raise ValueError(f"Тип {request_type} не привязан к БД")


moderator_ids = []
