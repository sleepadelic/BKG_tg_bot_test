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

    #users flush
    #user auth

    user = None
    user: User
    for u in Users:
        if u.id == message.from_user.id:
            user = u
    if user is None:
        user = User()
        user.id = message.from_user.id
        Users.append(user)

    if user.state == 'init':
        bot.send_message(user.id, "Welcome message")
        user.issue = Models.Issue()
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
            #save image
            user.state = 'state_ask_description'
            bot.send_message(user.id, 'Отправьте адрес или геолокацию (желательно)')
            return
        else:
            user.state = 'state_ask_photo'
            main_handler(message)
    if user.state == 'state_ask_description':
        if message.text != '':
            user.state = 'state_create_issue'
        else:
            pass
        return




# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    botmain()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
