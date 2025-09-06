import configparser
import json
from utils.bimap import BiMap

bot = None
app = None

admin_ids = [1593918381]

count_requests_on_page = 10  # Количество заявок, отображаемых на одной странице

duplicate_messages = (
    False  # Отображение в диалоге с модератором отправителю его же сообщений
)

complaint_types = [
    "cheat_complaint_type",
    "grief_complaint_type",
    "chat_complaint_type",
    "false_punished_complaint_type",
    "other_complaint_type",
]

errors_types = ["error_errors_type", "bug_errors_type", "lags_errors_type"]

other_types = [
    "blogger_request_other_type",
    "buildings_request_other_type",
    "improvements_request_other_type",
    "moderation_request_other_type",
]

request_types = complaint_types + errors_types + other_types

games = ["classic_survival_game", "block_party_game"]

locations = games + ["site", "hub"]

button_names = BiMap(
    {
        # Стартовое сообщение
        "complaint": "Жалоба",
        "errors": "Ошибки/Баги/Лаги",
        "other": "Прочее",
        "show_user_active_requests": "Активные заявки",
        # Выбор типа жалобы
        "cheat_complaint_type": "Читерство",
        "grief_complaint_type": "Гриферство",
        "chat_complaint_type": "Нарушения в чате",
        "false_punished_complaint_type": "Ложное наказание",
        "other_complaint_type": "Другая жалоба",
        "main_menu": "Вернуться в меню",
        # Подтверждение жалобы
        "edit_complaint": "Изменить",
        "end_collection_complaint_data": "Отправить",
        # Администрирование
        "admin_mode": "Режим администратора",
        "add_new_moderator": "Добавить модератора",
        "edit_moderators": "Редактировать модераторов",
        "confirm_moderator_types": "Категории выбраны",
        "edit_request_types": "Категории заявок",
        "edit_is_active": "Доступ",
        "delete_moderator": "Снять с должности",
        "confirm_delete_moderator": "Подтвердить",
        "cancel_action": "Отмена",
        "block_moderator": "Заморозить",
        "unblock_moderator": "Разморозить",
        "back_to_main_menu": "Выйти из режима админа",
        # Модератор
        "show_request_types": "Список категорий",
        "show_request_list": "Список заявок",
        "show_request_groups": "Список групп",
        "main_menu_from_moderator": "Выйти из режима модерации",
        "moderator_mode": "Режим модерации",
        # Диалог
        "cancel": "Отменить",
        # Выбор типа "прочего"
        "moderation_request_other_type": "Заявка в модерацию",
        "blogger_request_other_type": "Заявка на блогера",
        "buildings_request_other_type": "Предложить постройки",
        "improvements_request_other_type": "Предложить улучшения",
        # Категория "Прочее"
        "edit_request": "Изменить",
        "end_collection_request_data": "Отправить",
        # Заявка в модерацию
        "is_have_experience": "Да, опыт был",
        "is_not_have_experience": "Без опыта",
        # Заявка на блогера
        "classic_survival_game": "Выживание",
        "block_party_game": "Дискотека",
        "confirm_blogger_games": "Режимы выбраны",
        # Предложить улучшение
        "skip_media": "Продолжить без медиа",
        # Изменения
        "edit_nick": "Ник",
        "edit_violator_nick": "Ник нарушителя",
        "edit_name_and_years": "Имя и возраст",
        "edit_count_subsribers": "Количество подписчиков",
        "edit_game": "Режим",
        "edit_games": "Режимы",
        "edit_media": "Фото/Видео",
        "edit_channel_hrefs": "Канал",
        "edit_video_hrefs": "Видео",
        "edit_date_location": "Дата/Место",
        "edit_description": "Описание",
        "edit_proofs": "Доказательства",
        "edit_is_have_experience": "Опыт",
        "edit_duties_description": "Сфера занятий",
        "edit_document_or_pos": "Корды/Карта",
        "edit_idea": "Предложение",
        "edit_location": "Место",
        "edit_date": "Дата",
        # Ошибки
        "site": "Сайт",
        "hub": "Хаб",
        "error_errors_type": "Ошибка",
        "bug_errors_type": "Баг",
        "lags_errors_type": "Лаги",
    }
)


# Фотографии
greet_image_path = "./images/greet_image.png"
