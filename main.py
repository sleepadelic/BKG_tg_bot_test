import datetime
import logging
import telebot
import os
import yaml
import pathlib
from pathlib import Path
import keyboards
import Models
import secret
import settings
from datetime import timedelta
from ListTypesInputConstraint import IssueTypes
from Models import User as User
from Service import issue_excel_export
from Service import issue_combiner

Users = []
config = issue_combiner.load_from_yaml("setting.yaml")
bot = telebot.AsyncTeleBot(config.Token)
logger = None


def logger_init():
    log = logging.getLogger("BKG_BOT")
    log.setLevel(logging.INFO)
    fh = logging.FileHandler(f"{config.log_file_directory}{str(datetime.date.today())}.log")  # Путь файла лога
    formatter = logging.Formatter('%(asctime)s- %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    log.addHandler(fh)
    return log


logger = logger_init()


def bot_main():
    if config.debug_mode != True:
        while True:
            try:
                logger.info('bot started')
                # issue_combiner.save_to_yml(config, "setting.yaml")
                bot.polling(none_stop=True, interval=0)
            except Exception as e:
                logger.exception("Main exception")
            finally:
                Users.clear()
    else:
        logger.info('Бот запущен в режиме отладки')
        bot.polling(none_stop=True, interval=0)


@bot.message_handler(content_types=['text', 'photo', 'location'])
def main_handler(message: telebot.types.Message):
    logger.debug(f"Handled message from {message.from_user.id}")

    user = None
    u: User
    user: User
    time_now = datetime.datetime.now()
    user = find_user_in_list(message, user)

    if user is None:
        user = create_user(message.from_user.id)

    if message.text == "/start" or message.text == "назад" or message.text == "сброс" or message.text == 'меню':
        user.state = 'init'

    # Начало сервисного меню
    if message.text == "/service":
        enter_to_service_menu(message, user)
        return

    # Компоненты сервисного меню
    if user.state == 'ServiceMenu':
        service_menu_processing(message, time_now, user)
        return

    # Компоненты опасной зоны
    if user.state == 'danger':
        danger_zone_processing(message, user)
        return
    # Компоненты меню по типу опасной зоны
    if user.state == 'links':
        bot.send_message(user.id, 'Получена ссылка на админ-панель сервера бота',
                         reply_markup=keyboards.get_danger_zone_keyboard())
        user.state = 'danger'
        return

    if user.state == 'discharge':
        bot.send_message(user.id, 'Логи выгружены', reply_markup=keyboards.get_danger_zone_keyboard())
        logger.info(f"User {user.id} success uploading logs into DANGER ZONE")
        user.state = 'danger'
        return

    if user.state == 'version':
        bot.send_message(user.id, 'Версия бота - ...', reply_markup=keyboards.get_danger_zone_keyboard())
        user.state = 'danger'
        return

    if user.state == 'delID':
        try:
            config.admins_ids.remove(message.text)
            config.admins_DANGER_ZONE_ids.remove(message.text)
            issue_combiner.save_to_yml(config, 'setting.yaml')
            bot.send_message(user.id, f'ID {message.text} удален', reply_markup=keyboards.get_danger_zone_keyboard())
            logger.info(f"User {user.id} delete ID {message.text}")
        except:
            bot.send_message(user.id, 'Нет такого ID', reply_markup=keyboards.get_danger_zone_keyboard())
        user.state = 'danger'
        return

    if user.state == 'addID':
        config.admins_ids.append(message.text)
        config.admins_DANGER_ZONE_ids.append(message.text)
        issue_combiner.save_to_yml(config, 'setting.yaml')
        bot.send_message(user.id, f'ID {message.text} добавлен', reply_markup=keyboards.get_danger_zone_keyboard())
        logger.info(f"User {user.id} append ID {message.text}")
        user.state = 'danger'
        return

    # Отгрузки перезагрузки
    if user.state == 'yes_restart':
        if message.text == 'Да':
            bot.send_message(user.id, 'Тут должен быть кот рестарта', reply_markup=keyboards.get_danger_zone_keyboard())
            logger.info(f"User {user.id} success restarting the bot into DANGER ZONE")
            user.state = 'danger'
            return
        if message.text == 'Нет':
            bot.send_message(user.id, 'Вы вернулись обратно. Выберите пункт',
                             reply_markup=keyboards.get_danger_zone_keyboard())
            user.state = 'danger'
            return

    if user.state == 'yes_updating_stop':
        if message.text == 'Да':
            bot.send_message(user.id, 'Тут должен быть кот обновы с остановкой',
                             reply_markup=keyboards.get_danger_zone_keyboard())
            logger.info(f"User {user.id} success updating the bot with stopping the service into DANGER ZONE")
            user.state = 'danger'
            return
        if message.text == 'Нет':
            bot.send_message(user.id, 'Вы вернулись обратно. Выберите пункт',
                             reply_markup=keyboards.get_danger_zone_keyboard())
            user.state = 'danger'
            return

    if user.state == 'yes_updating_restart':
        if message.text == 'Да':
            bot.send_message(user.id, 'Тут должен быть кот обновы с перезагрузкой',
                             reply_markup=keyboards.get_danger_zone_keyboard())
            logger.info(f"User {user.id} success updating the bot with a reboot into DANGER ZONE")
            user.state = 'danger'
            return
        if message.text == 'Нет':
            bot.send_message(user.id, 'Вы вернулись обратно. Выберите пункт',
                             reply_markup=keyboards.get_danger_zone_keyboard())
            user.state = 'danger'
            return

    # Компоненты меню выгрузки отчета с условиями
    if user.state == "conditions_report":
        condition_reports_menu(message, user)
        return

    if user.state == "type_by_date":
        create_and_send_report_by_date(message, time_now, user)
        return

    if user.state == "type_by_type":
        create_and_send_report_by_type(message, time_now, user)
        return

        # select_issues_by_type_and_date
    if user.state == "type_by_date_and_type":
        user.report_conditions.report_date = message.text
        bot.send_message(user.id, "Выберите тип:", reply_markup=keyboards.get_issue_types_keyboard()).wait()
        user.state = 'type_by_date_and_type:get_type'
        return

    if user.state == "type_by_date_and_type:get_type":
        if message.text in IssueTypes:
            user.report_conditions.report_type = message.text
            bot.send_message(user.id, "Формирование отчета может занять некоторое время (около трех минут)."
                                      "По завершению должно быть отправлено три файла.\n"
                                      "Пожалуйста, дождитесь сообщения о завершении операции.").wait()
            try:
                date_time_obj = datetime.datetime.strptime(user.report_conditions.report_date, '%Y-%m-%d').date()
                filepath = config.report_files_directory \
                           + user.report_conditions.report_date + user.report_conditions.report_type + str(
                    time_now.timestamp()) + "_" + str(user.id)
                combined_issues = issue_excel_export.combine_reports(f'{config.output_files_directory}')
                combined_issues = issue_excel_export.select_issues_by_type_and_date(date_time_obj,
                                                                                    user.report_conditions.report_type,
                                                                                    combined_issues)
                combined_issues = issue_excel_export.load_addresses(combined_issues)
                combined_issues = issue_excel_export.img_relative_path(combined_issues)
                issue_excel_export.saved_yaml_file(combined_issues, filepath + '.yaml')
                issue_excel_export.export_to_xlsx(combined_issues, filepath + '.xlsx', '')
                issue_excel_export.saved_zip_file(combined_issues, filepath)
                try:
                    bot.send_document(message.chat.id, open(filepath + '.xlsx', 'rb'), timeout=120).wait()
                    bot.send_document(message.chat.id, open(filepath + '.yaml', 'rb')).wait()
                    bot.send_document(message.chat.id, open(filepath + '.zip', 'rb'), timeout=60).wait()

                    bot.send_message(user.id,
                                     f"Отчет по типу {user.report_conditions.report_type} "
                                     f"за {user.report_conditions.report_date} был отправлен",
                                     reply_markup=keyboards.get_report_types_keyboard())

                    os.remove(Path(pathlib.Path.cwd(), filepath + '.xlsx'))
                    os.remove(Path(pathlib.Path.cwd(), filepath + '.yaml'))
                    os.remove(Path(pathlib.Path.cwd(), filepath + '.zip'))
                    logger.info(f"User {user.id} success sending a report by date and type into service panel")
                    user.state = "conditions_report"
                    return
                except OSError:
                    bot.send_message(user.id, "Что-то пошло не так, невозможно завершить действие "
                                              "на данный момент", reply_markup=keyboards.get_service_menu_keyboard())
                    logger.exception("Type_by_date_and_type report exception")
                    return
            except ValueError:
                bot.send_message(user.id, "Ошибка. Формат даты был указан неверно, попробуйте снова")
                user.state = "type_by_date_and_type"
                return
        else:
            bot.send_message(user.id, "Неправильно указан тип обращений").wait()
            bot.send_message(user.id, "Выберите тип отчета.", reply_markup=keyboards.get_report_types_keyboard())
        return

    if user.state == "type_by_period":
        user.report_conditions.report_date_one = message.text
        bot.send_message(user.id, 'Напишите конечную дату:').wait()
        user.state = 'type_by_period:get_date_two'
        return

    if user.state == 'type_by_period:get_date_two':
        user.report_conditions.report_date_two = message.text
        bot.send_message(user.id, "Формирование отчета может занять некоторое время (около трех минут)."
                                  "По завершению должно быть отправлено три файла.\n"
                                  "Пожалуйста, дождитесь сообщения о завершении операции.").wait()
        try:
            date_time_obj_one = datetime.datetime.strptime(user.report_conditions.report_date_one, '%Y-%m-%d').date()
            date_time_obj_two = datetime.datetime.strptime(user.report_conditions.report_date_two, '%Y-%m-%d').date()
            filepath = config.report_files_directory \
                       + user.report_conditions.report_date_one + "_" + user.report_conditions.report_date_two \
                       + str(time_now.timestamp()) + "_" + str(user.id)
            combined_issues = issue_excel_export.combine_reports(f'{config.output_files_directory}')
            combined_issues = issue_excel_export.select_issues_by_period(date_time_obj_one, date_time_obj_two,
                                                                         combined_issues)
            combined_issues = issue_excel_export.load_addresses(combined_issues)
            combined_issues = issue_excel_export.img_relative_path(combined_issues)
            issue_excel_export.saved_yaml_file(combined_issues, filepath + '.yaml')
            issue_excel_export.export_to_xlsx(combined_issues, filepath + '.xlsx', '')
            issue_excel_export.saved_zip_file(combined_issues, filepath)
            try:
                bot.send_document(message.chat.id, open(filepath + '.xlsx', 'rb'), timeout=120).wait()
                bot.send_document(message.chat.id, open(filepath + '.yaml', 'rb')).wait()
                bot.send_document(message.chat.id, open(filepath + '.zip', 'rb'), timeout=60).wait()

                bot.send_message(user.id,
                                 f"Отчет за период {user.report_conditions.report_date_one} — "
                                 f"{user.report_conditions.report_date_two} был отправлен",
                                 reply_markup=keyboards.get_report_types_keyboard())

                os.remove(Path(pathlib.Path.cwd(), filepath + '.xlsx'))
                os.remove(Path(pathlib.Path.cwd(), filepath + '.yaml'))
                os.remove(Path(pathlib.Path.cwd(), filepath + '.zip'))
                logger.info(
                    f"User {user.id} success sending a report by period {user.report_conditions.report_date_one} — "
                    f"{user.report_conditions.report_date_two} and type into service panel")
                user.state = "conditions_report"
                return
            except OSError:
                bot.send_message(user.id, "Что-то пошло не так, невозможно завершить действие "
                                          "на данный момент", reply_markup=keyboards.get_service_menu_keyboard())
                logger.exception("Type_by_period report exception")
                return
        except ValueError:
            bot.send_message(user.id, "Ошибка. Формат даты был указан неверно, попробуйте снова\n"
                                      "Напишите начальную дату (прим. 2021-06-26):").wait()
            user.state = "type_by_period"
            return

    if message.text == '/help' or message.text == "помощь":
        send_help_message(user)
        return

    if message.text == 'О проекте':
        send_about_message(user)
        return

    if user.state == 'init':
        status_init(user)
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
        bot.send_message(user.id, "Какой тип обращения?", reply_markup=keyboards.get_issue_types_keyboard())
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
            filepath = config.output_files_directory + user.issue.type + "_" + str(
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
        elif message.text != '' and message.content_type == 'text':
            user.issue.address = message.text
            bot.send_message(user.id, 'Напишите описание')
            user.state = 'state_create_issue'
            return
        else:
            bot.send_message(user.id, 'Отправьте геопозицию (желательно) или адрес')
            user.state = 'state_ask_description'
            return

    if user.state == 'state_create_issue':
        if message.content_type == 'text':
            user.issue.description = message.text
            filepath: str = config.output_files_directory + user.issue.type + "_" + str(
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


def condition_reports_menu(message, user):
    if message.text == 'Выгрузка отчета за сегодня':
        create_and_send_report_for_today(message, user)
        return
    if message.text == 'По дате':
        bot.send_message(user.id, 'Напишите дату (прим. 2021-06-26):').wait()
        user.state = "type_by_date"
    if message.text == 'По типу':
        bot.send_message(user.id, "Выберите тип:", reply_markup=keyboards.get_issue_types_keyboard()).wait()
        user.state = "type_by_type"
    if message.text == 'По дате и типу':
        bot.send_message(user.id, 'Напишите дату (прим. 2021-06-26):').wait()
        user.state = "type_by_date_and_type"
    if message.text == 'За период':
        bot.send_message(user.id, 'Напишите начальную дату (прим. 2021-06-26):').wait()
        user.state = "type_by_period"
    if message.text == 'В начало':
        bot.send_message(user.id,
                         "Бот для загрузки информации на портал bkg.sibadi.org, приветствует тебя!\n"
                         "Если Вам нужна помощь, по работе бота, введите команду /help",
                         reply_markup=keyboards.get_main_menu_keyboard()).wait()
        user.state = "auth_require"
    if message.text == 'Назад':
        bot.send_message(user.id, "Вы открыли сервисное меню. Выберите пункт из меню.",
                         reply_markup=keyboards.get_service_menu_keyboard())
        user.state = 'ServiceMenu'


def create_and_send_report_for_today(message, user):
    bot.send_message(user.id, "Формирование отчета может занять некоторое время (около трех минут)."
                              "По завершению должно быть отправлено три файла.\n"
                              "Пожалуйста, дождитесь сообщения о завершении операции.").wait()
    time_now = datetime.datetime.now()
    filepath = config.report_files_directory + str(time_now.date()) + str(
        time_now.timestamp()) + "_" + str(
        user.id)
    combined_issues = issue_excel_export.combine_reports(f'{config.output_files_directory}')
    combined_issues = issue_excel_export.select_issues_by_date(time_now.date(), combined_issues)
    combined_issues = issue_excel_export.load_addresses(combined_issues)
    combined_issues = issue_excel_export.img_relative_path(combined_issues)
    issue_excel_export.saved_yaml_file(combined_issues, filepath + '.yaml')
    issue_excel_export.export_to_xlsx(combined_issues, filepath + '.xlsx', '')
    issue_excel_export.saved_zip_file(combined_issues, filepath)
    try:
        bot.send_document(message.chat.id, open(filepath + '.xlsx', 'rb'), timeout=120).wait()
        bot.send_document(message.chat.id, open(filepath + '.yaml', 'rb')).wait()
        bot.send_document(message.chat.id, open(filepath + '.zip', 'rb'), timeout=60).wait()

        bot.send_message(user.id, "Отчет был отправлен.", reply_markup=keyboards.get_service_menu_keyboard())
        os.remove(Path(pathlib.Path.cwd(), filepath + '.xlsx'))
        os.remove(Path(pathlib.Path.cwd(), filepath + '.yaml'))
        os.remove(Path(pathlib.Path.cwd(), filepath + '.zip'))
        logger.info(f"Был выгружен отчет за {time_now.date()} пользователю: {user.id}")
    except OSError:
        bot.send_message(user.id, "Что-то пошло не так, невозможно завершить действие "
                                  "на данный момент", reply_markup=keyboards.get_service_menu_keyboard())
        logger.exception("Today report exception")
        return


def create_and_send_report_by_type(message, time_now, user):
    types = message.text
    if message.text in IssueTypes:
        bot.send_message(user.id, "Формирование отчета может занять некоторое время (около трех минут)."
                                  "По завершению должно быть отправлено три файла.\n"
                                  "Пожалуйста, дождитесь сообщения о завершении операции.").wait()
        filepath = config.report_files_directory + types + str(
            time_now.timestamp()) + "_" + str(user.id)
        combined_issues = issue_excel_export.combine_reports(f'{config.output_files_directory}')
        combined_issues = issue_excel_export.select_issues_by_type(types, combined_issues)
        combined_issues = issue_excel_export.load_addresses(combined_issues)
        combined_issues = issue_excel_export.img_relative_path(combined_issues)
        issue_excel_export.saved_yaml_file(combined_issues, filepath + '.yaml')
        issue_excel_export.export_to_xlsx(combined_issues, filepath + '.xlsx', '')
        issue_excel_export.saved_zip_file(combined_issues, filepath)
        try:
            bot.send_document(message.chat.id, open(filepath + '.xlsx', 'rb'), timeout=120).wait()
            bot.send_document(message.chat.id, open(filepath + '.yaml', 'rb')).wait()
            bot.send_document(message.chat.id, open(filepath + '.zip', 'rb'), timeout=60).wait()

            bot.send_message(user.id, f"Отчет по {types} был отправлен", reply_markup=keyboards.get_report_types_keyboard())

            os.remove(Path(pathlib.Path.cwd(), filepath + '.xlsx'))
            os.remove(Path(pathlib.Path.cwd(), filepath + '.yaml'))
            os.remove(Path(pathlib.Path.cwd(), filepath + '.zip'))
            logger.info(f"User {user.id} success sending a report by type {types} into service panel")
            user.state = "conditions_report"
        except OSError:
            bot.send_message(user.id, "Что-то пошло не так, невозможно завершить действие "
                                      "на данный момент", reply_markup=keyboards.get_service_menu_keyboard())
            logger.exception("Type_by_type report exception")
            return
    else:
        bot.send_message(user.id, "Неправильно указан тип обращений").wait()
        bot.send_message(user.id, "Выберите тип отчета.", reply_markup=keyboards.get_report_types_keyboard())
        user.state = "conditions_report"


def create_and_send_report_by_date(message, time_now, user):
    try:
        date_time_str = message.text
        bot.send_message(user.id, "Формирование отчета может занять некоторое время (около трех минут)."
                                  "По завершению должно быть отправлено три файла.\n"
                                  "Пожалуйста, дождитесь сообщения о завершении операции.").wait()
        date_time_obj = datetime.datetime.strptime(date_time_str, '%Y-%m-%d').date()
        filepath = config.report_files_directory + date_time_str + str(
            time_now.timestamp()) + "_" + str(user.id)
        combined_issues = issue_excel_export.combine_reports(f'{config.output_files_directory}')
        combined_issues = issue_excel_export.select_issues_by_date(date_time_obj, combined_issues)
        combined_issues = issue_excel_export.load_addresses(combined_issues)
        combined_issues = issue_excel_export.img_relative_path(combined_issues)
        issue_excel_export.saved_yaml_file(combined_issues, filepath + '.yaml')
        issue_excel_export.export_to_xlsx(combined_issues, filepath + '.xlsx', '')
        issue_excel_export.saved_zip_file(combined_issues, filepath)
        try:
            bot.send_document(message.chat.id, open(filepath + '.xlsx', 'rb'), timeout=120).wait()
            bot.send_document(message.chat.id, open(filepath + '.yaml', 'rb')).wait()
            bot.send_document(message.chat.id, open(filepath + '.zip', 'rb'), timeout=60).wait()
            bot.send_message(user.id, f"Отчет по дате {date_time_str} был отправлен",
                             reply_markup=keyboards.get_report_types_keyboard())
            os.remove(Path(pathlib.Path.cwd(), filepath + '.xlsx'))
            os.remove(Path(pathlib.Path.cwd(), filepath + '.yaml'))
            os.remove(Path(pathlib.Path.cwd(), filepath + '.zip'))
            logger.info(f"User {user.id} success sending a report by date {date_time_str} into service panel")
            user.state = "conditions_report"
        except OSError:
            bot.send_message(user.id, "Что-то пошло не так, невозможно завершить действие "
                                      "на данный момент", reply_markup=keyboards.get_service_menu_keyboard())
            logger.exception("Type_by_date report exception")
            return
    except ValueError:
        bot.send_message(user.id, "Ошибка. Формат даты указан неверно, попробуйте снова")
        return


def danger_zone_processing(message, user):
    if message.text == "Перезапуск бота":
        bot.send_message(user.id, 'Вы точно этого хотите? Да или Нет?')
        user.state = 'yes_restart'
        return
    if message.text == "Обновление бота с остановкой службы":
        bot.send_message(user.id, 'Вы точно этого хотите? Да или Нет?')
        user.state = 'yes_updating_stop'
        return
    if message.text == "Обновление бота с перезагрузкой":
        bot.send_message(user.id, 'Вы точно этого хотите? Да или Нет?')
        user.state = 'yes_updating_restart'
        return
    if message.text == "Ссылка на админ-панель":
        user.state = 'links'
        return
    if message.text == "Выгрузка логов":
        user.state = 'discharge'
        return
    if message.text == "Версия бота":
        user.state = 'version'
        return
    if message.text == "Добавить ID":
        bot.send_message(user.id, "Введите ID:")
        logger.info(f"User {user.id} adds a new ID")
        user.state = 'addID'
        return
    if message.text == "Удалить ID":
        bot.send_message(user.id, "Введите ID:")
        logger.info(f"User {user.id} delete ID")
        user.state = 'delID'
        return
    if message.text == "Назад":
        bot.send_message(user.id, "Вы открыли сервисное меню. Выберите пункт из меню.",
                         reply_markup=keyboards.get_service_menu_keyboard())
        user.state = 'ServiceMenu'
        return
    if message.text == "В начало":
        bot.send_message(user.id,
                         "Бот для загрузки информации на портал bkg.sibadi.org, приветствует тебя!\n"
                         "Если Вам нужна помощь, по работе бота, введите команду /help",
                         reply_markup=keyboards.get_main_menu_keyboard()).wait()
        user.state = "auth_require"
        return


def enter_to_danger_zone(message, user):
    u_info: telebot.types.User
    u_info = message.from_user
    if str(user.id) in config.admins_DANGER_ZONE_ids:
        u_info: telebot.types.User
        u_info = message.from_user
        bot.send_message(user.id, "Вы открыли опасную зону :)", reply_markup=keyboards.get_danger_zone_keyboard())
        user.state = 'danger'
        logger.info(f"User {u_info.username} success login into DANGER ZONE")
    else:
        bot.send_message(user.id, "У вас нет доступа для использования данной команды").wait()


def service_menu_processing(message, time_now, user):
    if message.text == 'Статистика':
        active_users(time_now, user)
        combined_issues = issue_excel_export.combine_reports(f'{config.output_files_directory}')
        today_issues = issue_excel_export.select_issues_by_date(time_now.date(), combined_issues)
        yesterday_issues = []
        yesterday_issues = issue_excel_export.select_issues_by_date((time_now.date() -
                                                                     timedelta(days=1)), combined_issues)
        bot.send_message(user.id, f"Сегодня было отправлено {len(today_issues)}, "
                                  f"вчера {len(yesterday_issues)} обращений",
                         reply_markup=keyboards.get_service_menu_keyboard())
    if message.text == 'Сообщение об остановке бота':
        for usr in Users:
            if usr.state != 'init' and (time_now - usr.last_action_time < datetime.timedelta(minutes=5)):
                bot.send_message(usr.id, "Через 5 минут бот будет остановлен, для обслуживания."
                                         "Необходимо завершить заполнение обращения, иначе данные будут потеряны "
                                         "и потребуется повторное заполнение",
                                 reply_markup=keyboards.get_service_menu_keyboard())
        bot.send_message(user.id, "Сообщения об остановк бота через 5 минут отправлены.",
                         reply_markup=keyboards.get_service_menu_keyboard())

    if message.text == 'Выгрузка отчета':
        bot.send_message(user.id, "Выберите тип отчета.", reply_markup=keyboards.get_report_types_keyboard())
        user.state = "conditions_report"

    if message.text == 'Опасная зона':
        enter_to_danger_zone(message, user)

    if message.text == 'Выгрузка сырых файлов':
        filepath = config.report_files_directory + "backup" + "_" + str(datetime.datetime.now().date()) + str(
            time_now.timestamp()) + "_" + str(
            user.id)
        try:
            issue_excel_export.open_and_load_zip_backup(f'{config.output_files_directory}', filepath)
            bot.send_message(user.id, "Выполнение запроса может занять некоторое время (не больше одной минуты). "
                                      "Пожалуйста, подождите.")
            bot.send_document(message.chat.id, open(filepath + '.zip', 'rb'), timeout=60).wait()
            bot.send_message(user.id, "Выгрузка была завершена", reply_markup=keyboards.get_service_menu_keyboard())
            os.remove(Path(pathlib.Path.cwd(), filepath + '.zip'))
            logger.info(
                f"Были выгружены все файлы из {config.output_files_directory} на момент {time_now.date()} "
                f"пользователю: {user.id}")
        except OSError:
            bot.send_message(user.id, "Что-то пошло не так, невозможно завершить действие "
                                      "на данный момент", reply_markup=keyboards.get_service_menu_keyboard())
            logger.exception("Backup report exception")
            return

    if message.text == 'В начало':
        bot.send_message(user.id,
                         "Бот для загрузки информации на портал bkg.sibadi.org, приветствует тебя!\n"
                         "Если Вам нужна помощь, по работе бота, введите команду /help",
                         reply_markup=keyboards.get_main_menu_keyboard()).wait()
        user.state = "auth_require"


def active_users(time_now, user):
    user_count = 0
    usr: User
    for usr in Users:
        if usr.state != 'init' and (time_now - usr.last_action_time < datetime.timedelta(minutes=5)):
            user_count += 1
    bot.send_message(user.id, f"Сейчас у бота {user_count} активных пользователей (включая вас).",
                     reply_markup=keyboards.get_service_menu_keyboard())


def enter_to_service_menu(message, user):
    u_info: telebot.types.User
    u_info = message.from_user
    if user.id in secret.admins_ids or u_info.username in secret.admins_ids:
        u_info: telebot.types.User
        u_info = message.from_user
        bot.send_message(user.id, "Вы открыли сервисное меню. Выберите пункт из меню.",
                         reply_markup=keyboards.get_service_menu_keyboard())
        user.state = 'ServiceMenu'
        logger.info(f"User {u_info.username} success login into service panel")
    else:
        bot.send_message(user.id, "У вас нет доступа для использования данной команды").wait()


def find_user_in_list(message, user):
    for u in Users:
        if u.id == message.from_user.id:
            user = u
            user.last_action_time = datetime.datetime.now()
        else:
            if config.isSessionCheckEnabled:
                session_time_check(datetime.datetime.now(), u)
    return user


def status_init(user):
    bot.send_message(user.id,
                     "Бот для загрузки информации на портал bkg.sibadi.org, приветствует тебя!\n"
                     "Если Вам нужна помощь, по работе бота, введите команду /help",
                     reply_markup=keyboards.get_main_menu_keyboard()).wait()
    if config.isAuthRequire:
        user.state = 'auth_require'
    else:
        user.state = 'state_ask_type'


def send_about_message(user):
    bot.send_message(user.id,
                     'BKG.sibadi.org - Сибирский автомобильно-дорожный университет – СибАДИ реализует проект '
                     '"Безопасный и комфортный город" при поддержке ректора Жигадло Александра Петровича '
                     'с целью улучшения качества жизни в Советском округе г. Омска. '
                     'Мы хотим, чтобы каждый омич мог принять участие в жизни своего города, выявить проблемы, '
                     'которые влияют на безопасность и качество жизни, '
                     'чтобы можно было оперативно '
                     'их решать через взаимодействие с администрацией города Омска',
                     reply_markup=keyboards.get_main_menu_keyboard()).wait()


def send_help_message(user):
    bot.send_message(user.id,
                     'Бот состоит из анкеты, которая включает такие пункты:\n'
                     '"Какой тип обращения?"\n'
                     '"Отправьте фото"\n'
                     '"Отправьте геопозицию (желательно) или адрес"\n'
                     '"Напишите описание"\n'
                     'После прохождения, обращение будет сохранено и отправлено на портал.\n').wait()


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
