import telebot

from ListTypesInputConstraint import DANGERTypes, ReportTypes, ServiceTypes, IssueTypes


def get_danger_zone_keyboard():
    DANGERTypesKeyboard = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    DANGERTypesKeyboard.add(DANGERTypes[0], DANGERTypes[1])
    DANGERTypesKeyboard.add(DANGERTypes[2], DANGERTypes[3])
    DANGERTypesKeyboard.add(DANGERTypes[4], DANGERTypes[5])
    DANGERTypesKeyboard.add(DANGERTypes[6], DANGERTypes[7])
    return DANGERTypesKeyboard


def get_report_types_keyboard():
    ReportTypesKeyboard = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    ReportTypesKeyboard.add(ReportTypes[0], ReportTypes[1])
    ReportTypesKeyboard.add(ReportTypes[2], ReportTypes[3])
    ReportTypesKeyboard.add(ReportTypes[4])
    return ReportTypesKeyboard


def get_service_menu_keyboard():
    ServiceTypesKeyboard = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    ServiceTypesKeyboard.add(ServiceTypes[0], ServiceTypes[1])
    ServiceTypesKeyboard.add(ServiceTypes[2], ServiceTypes[3])
    ServiceTypesKeyboard.add(ServiceTypes[4], ServiceTypes[5])
    ServiceTypesKeyboard.add(ServiceTypes[6])
    return ServiceTypesKeyboard


def get_issue_types_keyboard():
    IssueTypesKeyboard = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    IssueTypesKeyboard.add(IssueTypes[0], IssueTypes[1])
    IssueTypesKeyboard.add(IssueTypes[2], IssueTypes[3])
    IssueTypesKeyboard.add(IssueTypes[4], IssueTypes[5])
    IssueTypesKeyboard.add(IssueTypes[6], IssueTypes[7])
    IssueTypesKeyboard.add(IssueTypes[8])
    IssueTypesKeyboard.add(IssueTypes[9], IssueTypes[10])
    return IssueTypesKeyboard


def get_main_menu_keyboard():
    MenuKeyboard = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    MenuKeyboard.add('Отправить обращение', 'О проекте')
    return MenuKeyboard
