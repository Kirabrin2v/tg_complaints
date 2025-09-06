from functools import wraps
from utils.load_files import load_html
from utils.formatter import replace_pattern_html
import constants as const

exceeded_max_len_message = load_html("errors/exceeded_max_len.html")


def catch_long_message(max_len, text=exceeded_max_len_message):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            update = kwargs.get("update") or (args[0] if args else None)
            user_text = update.message.text or update.message.caption
            if user_text and len(user_text) > max_len:
                message_context = {"max_len": max_len, "now_len": len(user_text)}
                await update.effective_chat.send_photo(
                    caption=replace_pattern_html(text=text, context=message_context),
                    parse_mode="HTML",
                    photo=const.greet_image_path,
                )

            else:
                return await func(*args, **kwargs)

        return wrapper

    return decorator
