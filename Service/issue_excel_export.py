import datetime
import os
import openpyxl
import zipfile
from Service import Yaml_processing
import Models
from openpyxl import Workbook
from dadata import Dadata

config = Yaml_processing.load_from_yaml("setting.yaml")

def export_to_xlsx(issues, filename, route):
    """
    Создаёт отчёт из подготовленного yaml файла
    :param filename: Путь для сохранения отчёта
    :param route: ../ возврат в предыдущую папку
    """
    wb = Workbook()
    ws = wb.active
    Create_headlines(ws)
    # change column size for image
    ws.column_dimensions['G'].width = 450
    row_position = 2
    iss: Models.Issue
    for iss in issues:
        ws[f'A{str(row_position)}'] = str(row_position - 1)
        ws[f'B{str(row_position)}'] = str(iss.send_time.date())
        ws[f'C{str(row_position)}'] = iss.type
        ws[f'D{str(row_position)}'] = iss.address
        ws[f'E{str(row_position)}'] = iss.description
        ws[f'F{str(row_position)}'] = iss.geo

        img = openpyxl.drawing.image.Image(route + iss.image)
        img.anchor = f'G{str(row_position)}'
        img.width = img.width / 3
        img.height = img.height / 3
        ws.add_image(img)
        ws.row_dimensions[row_position].height = 240

        row_position += 1
    wb.save(filename=filename)


def Create_headlines(ws):
    """
    Создание заголовков в таблице
    :param ws: openpyxl Worksheet
    :return:
    """
    ws['A1'] = "№"
    ws['B1'] = "Дата"
    ws['C1'] = "Тип обращения"
    ws['D1'] = "Адрес"
    ws['E1'] = "Описание"
    ws['F1'] = "Геопозиция"
    ws['G1'] = "Фото"


def combine_reports(folder_path="../data/"):
    """
    Объединяет отчёты в один файл
    """
    return Yaml_processing.upload_yamls_to_list(folder_path)


def select_issues_by_date(date, issues):
    """
    :param date: дата в формате год-месяц-день
    :param issues: список issues
    :return: выбранные issues по дате
    """
    selected_issues = []
    iss: Models.Issue
    for iss in issues:
        if date == iss.send_time.date():
            selected_issues.append(iss)

    return selected_issues


def select_issues_by_period(date_one, date_two, issues):
    """
    Выбор issue за период из списка
    :param date_one: начальная дата в формате год-месяц-день
    :param date_two: конечная дата в формате год-месяц-день
    :param issues: список Models.Issue
    :return: список issues за период
    """
    selected_issues = []
    while date_one <= date_two:
        iss: Models.Issue
        for iss in issues:
            if date_one == iss.send_time.date():
                selected_issues.append(iss)
        date_one = date_one + datetime.timedelta(days=1)

    return selected_issues


def select_issues_by_type(type: str, issues):
    """
    Выбор issue по типу
    :param type: выбор с клавиатуры, строка
    :param issues: список issues
    :return: список issues по типу
    """
    selected_issues = []
    iss: Models.Issue
    for iss in issues:
        if type == iss.type:
            selected_issues.append(iss)

    return selected_issues


def select_issues_by_type_and_date(date, type: str, issues):
    """
    Выбор issue по типу и дате
    :param date: дата в формате год-месяц-день
    :param type: выбор с клавиатуры, строка
    :param issues: список issues
    :return: список issues по дате и типу
    """
    selected_issues = select_issues_by_date(date, issues)
    selected_issues = select_issues_by_type(type, selected_issues)
    return selected_issues


def save_to_yaml_file(issues, filename):
    Yaml_processing.save_to_yml(issues, filename)


def save_to_zip_file(issues, filename):
    new_arch = zipfile.ZipFile(filename + '.zip', mode="w")
    iss: Models.Issue
    for iss in issues:
        new_arch.write(iss.image)
    new_arch.close()


def open_and_load_zip_backup(folder_path, filename):
    new_arch = zipfile.ZipFile(filename + '.zip', mode="w")
    for file in os.listdir(folder_path):
        if file.endswith(".yaml") or file.endswith(".jpg"):
            new_arch.write(folder_path + file)
    new_arch.close()


def img_relative_path(issues):
    """
    Делает путь к изображениям относительным
    """
    iss: Models.Issue
    for iss in issues:
        iss.image = iss.image.replace('/home/danil0111/bkg_bot/', '')
    return issues


def load_addresses(issues):
    """
    Загружает адреса по гео-координатам
    :return:
    """
    iss: Models.Issue
    for iss in issues:
        try:
            if (iss.geo != None):
                geo = iss.geo.split(',')
                iss.address = reverse_geocode(geo[0], geo[1])[0]['unrestricted_value']
        except Exception as exc:
            print(f"No address in {iss.geo} {exc}")
    return issues


def reverse_geocode(lat, lon):
    """
    Преобразует координаты в адрес
    :rtype: str address
    """
    with Dadata(config.dadata_token, config.dadata_secret) as dadata:
        return dadata.geolocate(name='address', lat=lat, lon=lon)
