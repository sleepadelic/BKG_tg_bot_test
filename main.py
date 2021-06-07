import datetime
import requests
import yaml
import Models
import secret
import telebot
from Models import User as User

bot = telebot.AsyncTeleBot(secret.Token)
Users = []


def botmain():
    bot.polling(none_stop=True, interval=0)


@bot.message_handler(content_types=['text', 'photo', 'location'])
def main_handler(message: telebot.types.Message):
    # users flush
    us: User
    for us in Users:
        # if us.last_action_time
        pass
    # user auth
    # TODO add login to log

    user = None
    user: User
    for u in Users:
        if u.id == message.from_user.id:
            user = u

    if user is None:
        user = User()
        user.id = message.from_user.id
        Users.append(user)

    user.last_action_time = datetime.datetime.now()
    if user.state == 'init':
        bot.send_message(user.id, "Welcome message")
        user.issue = Models.Issue()
        user.issue.send_time = datetime.datetime.now()
        user.state = 'state_ask_type'
        # return
    if user.state == 'state_ask_type':
        bot.send_message(user.id, "Напишите тип обращения")
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
            fileID = message.photo[-1].file_id
            file_info = bot.get_file(fileID).wait()
            downloaded_file = bot.download_file(file_info.file_path)
            outfilepath ="data/" + user.issue.type + "_" + str(user.issue.send_time.timestamp()) + "_" + str(user.id) + ".jpg"
            user.issue.image = outfilepath
            with open(outfilepath, 'wb') as new_file:
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
        filepath = user.issue.type + "_" + str(user.issue.send_time.timestamp()) + "_" + str(user.id)
        filepath = filepath.replace(' ', '')
        with open(f'data/{filepath}.yaml', 'w', encoding="utf-8") as f:
            yaml.dump(user.issue, f, default_flow_style=False, allow_unicode=True)
        user.state = 'init'

if __name__ == '__main__':
    botmain()

