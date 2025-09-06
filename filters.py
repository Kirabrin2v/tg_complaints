from telegram.ext.filters import MessageFilter
import constants as const


class ActiveDialogue(MessageFilter):
    def filter(self, message):
        tg_id = message.from_user.id
        if tg_id in const.app.bot_data["dialogue_users"]:
            return True
        elif tg_id in const.app.bot_data["moderator_dialogue_id"]:
            return True

        return False


active_dialogue_filter = ActiveDialogue()
