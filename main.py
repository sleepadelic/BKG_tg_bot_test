import datetime
import logging
import telebot
import yaml
import Models
import secret
import settings
from Models import User as User

bot = telebot.AsyncTeleBot(secret.Token)
Users = []

logger = None

#Клавиатура главного меню
MenuKeyboard = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
MenuKeyboard.add('Отправить обращение', 'О проекте')

#Клавиатура выбора типа обращения
IssueTypesKeyboard = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
IssueTypesKeyboard.add('Тратуары', 'Пешеходные переходы', 'Освещение', 'Автомобильные  дороги', 'Ливневая канализация')
IssueTypesKeyboard.add('Заброшеные объекты', 'Детские площадки', 'Свалки', 'Проведение капитального ремонта')
IssueTypesKeyboard.add('Доступная среда', 'Другое')
hideBoard = telebot.types.ReplyKeyboardRemove()


def logger_init():
    log = logging.getLogger("BKG_BOT")
    log.setLevel(logging.INFO)
    fh = logging.FileHandler(f"{settings.log_file_directory}{str(datetime.date.today())}.log") #Путь файла лога
    formatter = logging.Formatter('%(asctime)s- %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    log.addHandler(fh)
    return log


logger = logger_init()


def bot_main():
    while True:
        try:
            logger.info('bot started')
            bot.polling(none_stop=True, interval=0)
        except Exception as e:
            logger.exception("Main exception")
        finally:
            Users.clear()


@bot.message_handler(content_types=['text', 'photo', 'location'])
def main_handler(message: telebot.types.Message):
    logger.debug(f"Handled message from {message.from_user.id}")

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

    if message.text == "/start" or message.text == "назад" or message.text == "сброс" or message.text == 'меню':
        user.state = 'init'

    if message.text == 'О проекте':
        bot.send_message(user.id,
                         'BKG.sibadi.org -  Сибирский автомобильно-дорожный университет – СибАДИ реализует проект'
                         '  "Безопасный и комфортный город" при поддержке ректора Жигадло Александра Петровича'
                         ' с целью улучшения качества жизни в Советском округе г. Омска. '
                         'Мы хотим, чтобы каждый омич мог  принять участие в жизни своего города, выявить проблемы, '
                         'которые влияют на безопасность и  качество жизни, '
                         'чтобы можно было оперативно'
                         ' их решать через взаимодействие с администрацией города Омска').wait()
        return

    if user.state == 'init':
        bot.send_message(user.id, "Бот для загрузки информации на портал bkg.sibadi.org, приветствует тебя!",
                         reply_markup=MenuKeyboard).wait()
        if settings.isAuthRequire:
            user.state = 'auth_require'
        else:
            user.state = 'state_ask_type'
        return
    if user.state == "auth_require":
        bot.send_message(user.id, "Бот находится в стадии тестирования отправьте пароль: ").wait()
        user.state = "auth"
        return

    if user.state == 'auth':
        if str.lower(message.text) == secret.AuthPassword:
            bot.send_message(user.id, "ok").wait()
            user.state = 'state_ask_type'
            main_handler(message)
            logger.info(f"Success login id: {user.id}")
            return
        else:
            bot.send_message(user.id, "Пароль неверный").wait()
            user.state = "auth_require"
            logger.info(f"Unsuccess login id: {user.id}")
            main_handler(message)
            return

    if user.state == 'state_ask_type':
        user.issue = Models.Issue()
        bot.send_message(user.id, "Какой тип обращения?", reply_markup=IssueTypesKeyboard)
        user.state = 'state_ask_photo'
        return

    if user.state == 'state_ask_photo':
        if message.text != '':
            user.issue.type = message.text
            bot.send_message(user.id, 'Отправьте фото')
            user.state = 'state_ask_geo_or_address'
            return
        else:
            user.state = 'state_ask_type'
            main_handler(message)

    if user.state == 'state_ask_geo_or_address':
        if message.content_type == 'photo':
            #Формирование пути файла -картинки
            filepath = settings.output_files_directory + user.issue.type + "_" + str(
                user.issue.send_time.timestamp()) + "_" + str(
                user.id) + ".jpg"
            filepath = filepath.replace(' ', '')
            user.issue.image = filepath
            #Сохраняем картинку на диск
            save_image(message.photo[-1].file_id, filepath)
            bot.send_message(user.id, 'Отправьте геопозицию (желательно) или адрес')
            user.state = 'state_ask_description'
            return
        else:
            user.state = 'state_ask_photo'
            main_handler(message)

    if user.state == 'state_ask_description':
        if message.text != '' or message.content_type == 'location':
            if message.content_type == 'location':
                # Преобразование в удобный формат для работы с картами
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
        user.issue.description = message.text
        filepath: str = settings.output_files_directory + user.issue.type + "_" + str(
            user.issue.send_time.timestamp()) + "_" + str(
            user.id) + ".yaml"
        save_issue_to_yaml(filepath, user.issue)
        bot.send_message(user.id, 'Обращение успешно сохранено').wait()
        bot.send_message(user.id, 'Спасибо, за то, что отправили обращение')
        bot.send_message(user.id, 'Вместе мы сможем сделать город комфортнее и безопаснее')
        logger.info(f"New issue saved to {filepath} by user: {user.id}")
        user.state = 'init'
        main_handler(message)
        user.reset_issue()

# Сохранения изображения на диск
def save_image(file_id, image_filepath):
    file_info = bot.get_file(file_id).wait()
    downloaded_file = bot.download_file(file_info.file_path)
    with open(image_filepath, 'wb') as new_file:
        new_file.write(downloaded_file.wait())


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
