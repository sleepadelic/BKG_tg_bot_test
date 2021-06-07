import datetime
import yaml
import Models
import secret
import telebot
import settings
from Models import User as User

bot = telebot.AsyncTeleBot(secret.Token)
Users = []


def bot_main():
    bot.polling(none_stop=True, interval=0)


@bot.message_handler(content_types=['text', 'photo', 'location'])
def main_handler(message: telebot.types.Message):
    # user auth
    # TODO add login to log

    user = None
    u: User
    user: User
    time_now = datetime.datetime.now()
    for u in Users:
        if u.id == message.from_user.id:
            user = u
            user.last_action_time = time_now
        else:
            if settings.isSessionCheckEnabled:
                session_time_check(time_now, u)

    if user is None:
        user = create_user(message.from_user.id)

    if user.state == 'init':
        bot.send_message(user.id, "Бот для загрузки информации на портал bkg.sibadi.org, приветствует тебя!").wait()
        bot.send_message(user.id, "Отправь мне 'начать' или 'отправить', чтобы загрузить фото-обращение")
        user.state = 'state_ask_type'
        return

    if user.state == 'state_ask_type':
        user.issue = Models.Issue()
        user.issue.send_time = datetime.datetime.now()

        bot.send_message(user.id, "Какой тип обращения?")
        user.state = 'state_ask_photo'
        return
    if user.state == 'state_ask_photo':
        if message.text != '':
            user.issue.type = message.text
            user.state = 'state_ask_geo_or_address'
            bot.send_message(user.id, 'Отправьте фото')
            return
        else:
            user.state = 'state_ask_type'
            main_handler(message)
    if user.state == 'state_ask_geo_or_address':
        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
            file_info = bot.get_file(file_id).wait()
            downloaded_file = bot.download_file(file_info.file_path)
            filepath = settings.output_files_directory + user.issue.type + "_" + str(
                user.issue.send_time.timestamp()) + "_" + str(
                user.id) + ".jpg"
            user.issue.image = filepath
            with open(filepath, 'wb') as new_file:
                new_file.write(downloaded_file.wait())
            user.state = 'state_ask_description'
            bot.send_message(user.id, 'Отправьте адрес или геопозицию (желательно)')
            return
        else:
            user.state = 'state_ask_photo'
            main_handler(message)
    if user.state == 'state_ask_description':
        if message.text != '' or message.content_type == 'location':
            if message.content_type == 'location':
                user.issue.geo = str(message.location.latitude) + ',' + str(message.location.longitude)
            else:
                user.issue.address = message.text
            bot.send_message(user.id, 'Отправьте описание')
            user.state = 'state_create_issue'
            return
        else:
            user.state = 'state_ask_geo_or_address'
            main_handler(message)
    if user.state == 'state_create_issue':
        # TODO add to log
        user.issue.description = message.text
        bot.send_message(user.id, 'Обращение успешно сохранено')
        issue = user.issue
        filepath: str = settings.output_files_directory + user.issue.type + "_" + str(
            user.issue.send_time.timestamp()) + "_" + str(
            user.id) + ".yaml"
        save_issue_to_yaml(filepath, issue)
        user.state = 'init'


def save_issue_to_yaml(filepath, issue):
    filepath = filepath.replace(' ', '')
    with open(filepath, 'w', encoding="utf-8") as f:
        yaml.dump(issue, f, default_flow_style=False, allow_unicode=True)


def session_time_check(time_now, user):
    if time_now - user.last_action_time >= datetime.timedelta(minutes=20):
        if user.state != 'init':
            bot.send_message(user.id, "Время сессии истекло, до скорого!")
        Users.remove(user)
    if time_now - user.last_action_time >= datetime.timedelta(minutes=15):
        if user.state != 'init':
            bot.send_message(user.id, "Время сессии истекает, осталось 5 минут!")


def create_user(user_id):
    user = User()
    user.id = user_id
    Users.append(user)
    user.last_action_time = datetime.datetime.now()
    return user


if __name__ == '__main__':
    bot_main()
