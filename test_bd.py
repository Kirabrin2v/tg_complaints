import asyncio
from models import Complaint
from models import Moderator
from models import User
from utils.formatter import get_datetime


async def main():
    now = get_datetime()
    print(now)
    # complaints = await Complaint.get_active_complaints()
    # for complaint in complaints:
    #     print(complaint)
    # # Добавление пользователя
    # await User.create(telegram_id=12345, username="testuser")

    # # Получение пользователя
    # user = await User.get_by_telegram_id(12345)
    # print("Найден пользователь:", user.username if user else "Не найден")

    # # Поиск по части имени
    # results = await User.search_by_username("test")
    # for u in results:
    #     print("Подходящий пользователь:", u.username)


async def users():
    # await User.add_user(tg_id=12345678, username="Kirabriin")
    # await User.update_username(tg_id=12345678, new_username="Herobrin2v")
    user = await User.get_user_by_id(tg_id=1593918381)
    moderator = user.moderator
    print(moderator.to_dict())


async def complaints():
    await Complaint.add_complaint(
        date_event=get_datetime("17.11.2006 15:00"),
        user_id=1593918381,
        request_type="cheat_complaint_type",
        nickname="Kirabrin",
        location="КВ, Локация №9",
        description="Загриферили",
        photo_ids=[],
        video_ids=[
            "BAACAgIAAxkBAAIU7GhHGzplS7jkfRfcpveZhgYMFQIxAAK7dAACPv45Sl8JbeyOZ-EINgQ"
        ],
    )
    complaint = await Complaint.get_complaint(complaint_id=2)
    complaint.context = [1, 2, 3, 3]
    # print(dir(complaint))


async def moderators():
    # moderator = await Moderator.get_moderator(tg_id=1593918381)
    # print(moderator)
    # user = moderator.user
    # print(user.username)
    await Moderator.add_moderator(
        tg_id=1231233213, complaint_types=[1, 2, 3, 43, 4, "asdasdas"]
    )


if __name__ == "__main__":
    asyncio.run(users())
