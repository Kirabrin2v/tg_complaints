from models import Request as RequestBase


async def notify_new_request(request_id: int, request_type: str, Request: RequestBase):
    moderator_ids = await var.get_moderator_ids()

    request = await Request.get_request(request_id=request_id)
    user = request.user

    href = f'<a href="tg://user?id={user.tg_id}">@{user.username}</a>'

    buttons = [
        [
            InlineKeyboardButton(
                "Подробнее", callback_data=f"{request_type}_{complaint_id}"
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    context_message = {
        "nick": request.nick,
        "href": href,
        "request_type": request.request_type,
    }

    text = replace_pattern_html(
        notify_new_request_message, context=context_message, bimap=const.button_names
    )

    for tg_id in moderator_ids:
        moderator = await Moderator.get_moderator(tg_id=tg_id)
        if request.request_type in moderator.request_types:
            await const.bot.send_photo(
                chat_id=tg_id,
                caption=text,
                parse_mode="HTML",
                reply_markup=reply_markup,
                photo=const.greet_image_path,
            )
            print("Отправлено:", tg_id)
