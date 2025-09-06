from datetime import datetime
import constants as const


def replace_pattern_html(
    text: str, context: dict[str, str | list[str]], bimap: "BiMap" = None
) -> str:
    for key, value in context.items():
        if isinstance(value, list):
            processed_values = [
                (
                    bimap.to_user(val)
                    if bimap and isinstance(val, str) and val in bimap
                    else val
                )
                for val in value
            ]
            value_str = ", ".join(processed_values)
        elif isinstance(value, bool):
            if value:
                value_str = "Да"
            else:
                value_str = "Нет"
        else:
            value_str = (
                bimap.to_user(value)
                if bimap and isinstance(value, str) and value in bimap
                else str(value)
            )

        text = text.replace(f"{{{key}}}", value_str)

    return text


def get_datetime(
    date: datetime = None, string_time: str = None, to_string: bool = False
):
    if string_time:
        try:
            date = datetime.strptime(string_time, "%d.%m.%Y %H:%M")
        except ValueError:
            date = None
    elif not date:
        date = datetime.now()

    if to_string:
        return datetime.strftime(date, "%Y.%m.%d %H:%M:%S")

    else:
        return date
