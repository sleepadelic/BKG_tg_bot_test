import datetime
import logging
import telebot
import yaml
import Models
import secret
import settings
import os
from ListTypesInputConstraint import IssueTypes
from ListTypesInputConstraint import ServiceTypes
from ListTypesInputConstraint import ReportTypes
from ListTypesInputConstraint import DANGERTypes
from ListTypesInputConstraint import YesNoTypes
from Models import User as User

bot = telebot.AsyncTeleBot(secret.Token)
Users = []

logger = None

# Клавиатура главного меню
MenuKeyboard = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
MenuKeyboard.add('Отправить обращение', 'О проекте')

# Клавиатура выбора типа обращения
IssueTypesKeyboard = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
IssueTypesKeyboard.add(IssueTypes[0], IssueTypes[1])
IssueTypesKeyboard.add(IssueTypes[2], IssueTypes[3])
IssueTypesKeyboard.add(IssueTypes[4], IssueTypes[5])
IssueTypesKeyboard.add(IssueTypes[6], IssueTypes[7])
IssueTypesKeyboard.add(IssueTypes[8])
IssueTypesKeyboard.add(IssueTypes[9], IssueTypes[10])
hideBoard = telebot.types.ReplyKeyboardRemove()

# Клавиатура сервисного меню
ServiceTypesKeyboard = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
ServiceTypesKeyboard.add(ServiceTypes[0], ServiceTypes[1])
ServiceTypesKeyboard.add(ServiceTypes[2], ServiceTypes[3])
ServiceTypesKeyboard.add(ServiceTypes[4], ServiceTypes[5])
ServiceTypesKeyboard.add(ServiceTypes[6])
hideServiceBoard = telebot.types.ReplyKeyboardRemove()

# Клавиатура отчета по условиям
ReportTypesKeyboard = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
ReportTypesKeyboard.add(ReportTypes[0], ReportTypes[1])
ReportTypesKeyboard.add(ReportTypes[2], ReportTypes[3])
ReportTypesKeyboard.add(ReportTypes[4])
hideReportBoard = telebot.types.ReplyKeyboardRemove()

# Клавиатура опасной зоны
DANGERTypesKeyboard = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
DANGERTypesKeyboard.add(DANGERTypes[0], DANGERTypes[1])
DANGERTypesKeyboard.add(DANGERTypes[2], DANGERTypes[3])
DANGERTypesKeyboard.add(DANGERTypes[4], DANGERTypes[5])
DANGERTypesKeyboard.add(DANGERTypes[6], DANGERTypes[7])
hideDANGERBoard = telebot.types.ReplyKeyboardRemove()

# Клавиатура ответа
YesNoTypesKeyboard = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
YesNoTypesKeyboard.add(YesNoTypes[0], YesNoTypes[1])
hideYesNoBoard = telebot.types.ReplyKeyboardRemove()

def logger_init():
    log = logging.getLogger("BKG_BOT")
    log.setLevel(logging.INFO)
    fh = logging.FileHandler(f"{settings.log_file_directory}{str(datetime.date.today())}.log")  # Путь файла лога
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

# Начало сервисного меню
    if message.text == "/service":
        bot.send_message(user.id, "Вы открыли сервисное меню. Выберите пункт из меню.",
                         reply_markup=ServiceTypesKeyboard)
        user.state = 'ServiceMenu'

# Компоненты сервисного меню
    if user.state == 'ServiceMenu':
        if message.text == 'Активные пользователи':
            bot.send_message(user.id, "Список активных пользователей был отправлен.", reply_markup=ServiceTypesKeyboard)
            return
        if message.text == 'Кол-во обращений за день':
            bot.send_message(user.id, "Кол-во обращений за день было отправлено", reply_markup=ServiceTypesKeyboard)
            return
        if message.text == 'Сообщение об остановке бота':
            bot.send_message(user.id, "Сообщение об остановке бота отправлено.", reply_markup=ServiceTypesKeyboard)
            return
        if message.text == 'Выгрузка отчета за сегодня':
            bot.send_message(user.id, "Отчет был отправлен.", reply_markup=ServiceTypesKeyboard)
            return
        if message.text == 'Выгрузка отчета с условиями':
            bot.send_message(user.id, "Выберите тип отчета.", reply_markup=ReportTypesKeyboard)
            user.state = "conditions_report"

        if message.text == 'Опасная зона':
            bot.send_message(user.id, "Вы открыли опасную зону :)", reply_markup=DANGERTypesKeyboard)
            user.state = 'danger'

        if message.text == 'В начало':
            bot.send_message(user.id,
                             "Бот для загрузки информации на портал bkg.sibadi.org, приветствует тебя!\n"
                             "Если Вам нужна помощь, по работе бота, введите команду /help",
                             reply_markup=MenuKeyboard).wait()
            user.state = "auth_require"
            return
# Компоненты меню опасной зоны
    if user.state == 'danger':
        if message.text == "Перезапуск бота":
            bot.send_message(user.id, 'Вы точно этого хотите?!!2312!', reply_markup=YesNoTypesKeyboard)
            user.state = 'restart'

        if message.text == "Обновление бота с остановкой службы":
            bot.send_message(user.id, 'Вы точно этого хотите???????', reply_markup=YesNoTypesKeyboard)
            user.state = 'Updating_Stop'

        if message.text == "Обновление бота с перезагрузкой":
            bot.send_message(user.id, "Вы точно этого хотите??", reply_markup=YesNoTypesKeyboard)
            user.state = 'Updating_Restart'

        if message.text == "Ссылка на админ-панель":
            user.state = 'links'

        if message.text == "Выгрузка логов":
            user.state = 'discharge'

        if message.text == "Версия бота":
            user.state = 'version'

        if message.text == "Назад":
            bot.send_message(user.id, "Вы открыли сервисное меню. Выберите пункт из меню.",
                             reply_markup=ServiceTypesKeyboard)
            user.state = 'ServiceMenu'
            return
        if message.text == "В начало":
            bot.send_message(user.id,
                             "Бот для загрузки информации на портал bkg.sibadi.org, приветствует тебя!\n"
                             "Если Вам нужна помощь, по работе бота, введите команду /help",
                             reply_markup=MenuKeyboard).wait()
            user.state = "auth_require"
            return
# Компоненты по типа опасной зоны
    if user.state == 'restart':
        if message.text == 'Да':
            user.state = 'yes_restart'

        if message.text == 'Нет':
            bot.send_message(user.id, "Вы открыли опасную зону :)", reply_markup=DANGERTypesKeyboard)
            user.state = 'danger'
            return

    if user.state == 'Updating_Stop':
        if message.text == 'Да':
            user.state = 'yes_updating_stop'
        if message.text == 'Нет':
            bot.send_message(user.id, "Вы открыли опасную зону :)", reply_markup=DANGERTypesKeyboard)
            user.state = 'danger'

    if user.state == 'Updating_Restart':
        if message.text == 'Да':
            user.state = 'yes_updating_restart'
        if message.text == 'Нет':
            bot.send_message(user.id, "Вы открыли опасную зону :)", reply_markup=DANGERTypesKeyboard)
            user.state = 'danger'

    if user.state == 'links':
        bot.send_message(user.id, 'Получена ссылка на админ-панель сервера бота', reply_markup=DANGERTypesKeyboard)
        user.state = 'danger'

    if user.state == 'discharge':
        bot.send_message(user.id, 'Выгрузка логов была совершена', reply_markup=DANGERTypesKeyboard)
        user.state = 'danger'

    if user.state == 'version':
        bot.send_message(user.id, 'Версия бота - версия', reply_markup=DANGERTypesKeyboard)
        user.state = 'danger'

# Отгрузки перезагрузки
    if user.state == 'yes_restart':
        bot.send_message(user.id, 'Тут должен быть кот рестарта', reply_markup=DANGERTypesKeyboard)
        user.state = 'danger'
        return

    if user.state == 'yes_updating_stop':
        bot.send_message(user.id, 'Тут должен быть кот обновы с остановкой', reply_markup=DANGERTypesKeyboard)
        user.state = 'danger'
        return

    if user.state == 'yes_updating_restart':
        bot.send_message(user.id, 'Тут должен быть кот обновы с перезагрузкой', reply_markup=DANGERTypesKeyboard)
        user.state = 'danger'
        return

# Компоненты меню выгрузки отчета с условиями
    if user.state == "conditions_report":
        if message.text == 'По дате':
            user.state = "type_by_date"

        if message.text == 'По типу':
            user.state = "type_by_type"

        if message.text == 'По дате и типу':
            user.state = "type_by_date_and_type"

        if message.text == 'В начало':
            bot.send_message(user.id,
                             "Бот для загрузки информации на портал bkg.sibadi.org, приветствует тебя!\n"
                             "Если Вам нужна помощь, по работе бота, введите команду /help",
                             reply_markup=MenuKeyboard).wait()
            user.state = "auth_require"
            return
        if message.text == 'Назад':
            bot.send_message(user.id, "Вы открыли сервисное меню. Выберите пункт из меню.",
                             reply_markup=ServiceTypesKeyboard)
            user.state = 'ServiceMenu'
            return

    if user.state == "type_by_date":
        bot.send_message(user.id, "Сообщение об отправке отчета по дате.", reply_markup=ReportTypesKeyboard)
        user.state = "conditions_report"
    if user.state == "type_by_type":
        bot.send_message(user.id, "Сообщение об отправке отчета по типу.", reply_markup=ReportTypesKeyboard)
        user.state = "conditions_report"
    if user.state == "type_by_date_and_type":
        bot.send_message(user.id, "Сообщение об отправке отчета по дате и типу.", reply_markup=ReportTypesKeyboard)
        user.state = "conditions_report"

    if message.text == '/help' or message.text == "помощь":
        bot.send_message(user.id,
                         'Бот состоит из анкеты, которая включает такие пункты:\n'
                         '"Какой тип обращения?"\n'
                         '"Отправьте фото"\n'
                         '"Отправьте геопозицию (желательно) или адрес"\n'
                         '"Напишите описание"\n'
                         'После прохождения, обращение будет сохранено и отправлено на портал.\n').wait()
        return
# Конец компонентов меню выгрузки отчета с условиями

    if message.text == 'О проекте':
        bot.send_message(user.id,
                         'BKG.sibadi.org - Сибирский автомобильно-дорожный университет – СибАДИ реализует проект '
                         '"Безопасный и комфортный город" при поддержке ректора Жигадло Александра Петровича '
                         'с целью улучшения качества жизни в Советском округе г. Омска. '
                         'Мы хотим, чтобы каждый омич мог принять участие в жизни своего города, выявить проблемы, '
                         'которые влияют на безопасность и качество жизни, '
                         'чтобы можно было оперативно '
                         'их решать через взаимодействие с администрацией города Омска').wait()
        return

    if user.state == 'init':
        bot.send_message(user.id,
                         "Бот для загрузки информации на портал bkg.sibadi.org, приветствует тебя!\n"
                         "Если Вам нужна помощь, по работе бота, введите команду /help",
                         reply_markup=MenuKeyboard).wait()
        if settings.isAuthRequire:
            user.state = 'auth_require'
        else:
            user.state = 'state_ask_type'
        return
    if user.state == "auth_require":
        bot.send_message(user.id, "Бот находится в стадии тестирования. Отправьте пароль: ").wait()
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
        if message.text in IssueTypes:
            user.issue.type = message.text
            bot.send_message(user.id, 'Отправьте фото')
            user.state = 'state_ask_geo_or_address'
            return
        else:
            user.state = 'state_ask_type'
            main_handler(message)

    if user.state == 'state_ask_geo_or_address':
        if message.content_type == 'photo':
            # Формирование пути файла -картинки
            filepath = settings.output_files_directory + user.issue.type + "_" + str(
                user.issue.send_time.timestamp()) + "_" + str(
                user.id) + ".jpg"
            filepath = filepath.replace(' ', '')
            user.issue.image = filepath
            # Сохраняем картинку на диск
            save_image(message.photo[-1].file_id, filepath)
            bot.send_message(user.id, 'Отправьте геопозицию (желательно) или адрес')
            user.state = 'state_ask_description'
            return
        else:
            bot.send_message(user.id, 'Отправьте фото')
            user.state = 'state_ask_geo_or_address'
            return

    if user.state == 'state_ask_description':
        if message.content_type == 'location':
            # Преобразование в удобный формат для работы с картами
            user.issue.geo = str(message.location.latitude) + ',' + str(message.location.longitude)
            bot.send_message(user.id, 'Напишите описание')
            user.state = 'state_create_issue'
            return
        elif message.text != '' and message.content_type != 'photo' and message.content_type != 'location':
            user.issue.address = message.text
            bot.send_message(user.id, 'Напишите описание')
            user.state = 'state_create_issue'
            return
        else:
            bot.send_message(user.id, 'Отправьте геопозицию (желательно) или адрес')
            user.state = 'state_ask_description'
            return

    if user.state == 'state_create_issue':
        if message.content_type != 'photo':
            user.issue.description = message.text
            filepath: str = settings.output_files_directory + user.issue.type + "_" + str(
                user.issue.send_time.timestamp()) + "_" + str(
                user.id) + ".yaml"
            save_issue_to_yaml(filepath, user.issue)
            bot.send_message(user.id, 'Обращение успешно сохранено').wait()
            bot.send_message(user.id, 'Спасибо за то, что отправили обращение')
            bot.send_message(user.id, 'Вместе мы сможем сделать город комфортнее и безопаснее')
            logger.info(f"New issue saved to {filepath} by user: {user.id}")
            user.state = 'init'
            main_handler(message)
            user.reset_issue()
        else:
            bot.send_message(user.id, 'Напишите описание')
            user.state = 'state_create_issue'
            return


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
