from Utils.utils import check_cooldown, fetch_cmd_data


def reply_with_source_code(self, message):
    cmd = fetch_cmd_data(self, message)

    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown):
        return

    text = 'Source code: https://github.com/BluePigman/BluePagmanBot'
    self.send_privmsg(cmd.channel, text)