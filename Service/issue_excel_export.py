import datetime
import openpyxl
from PIL import Image

import issue_combiner
import Models
import secret
from openpyxl import Workbook
from dadata import Dadata


def excel_export_main():
    combine_reports()
    print("combined")
    # select_issues_by_date()
    # print("sorted")
    load_addresses()
    print("Addresses loaded")
    img_relative_path()
    print("Img paths fixed")
    export_to_xlsx()
    print("Report saved")


def export_to_xlsx(filename=f'../data/export{str(datetime.datetime.now().date())}.xlsx'):
    """
    Создаёт отчёт из подготовленного yaml файла
    :param filename: Путь для сохранения отчёта
    """
    wb = Workbook()
    ws = wb.active
    Create_headlines(ws)
    #change column size for image
    ws.column_dimensions['G'].width = 450
    issues = issue_combiner.load_from_yaml("../data/export_w_addr.yaml")
    row_position = 2
    iss: Models.Issue
    for iss in issues:
        ws[f'A{str(row_position)}'] = str(row_position - 1)
        ws[f'B{str(row_position)}'] = str(iss.send_time.date())
        ws[f'C{str(row_position)}'] = iss.type
        ws[f'D{str(row_position)}'] = iss.address
        ws[f'E{str(row_position)}'] = iss.description
        ws[f'F{str(row_position)}'] = iss.geo

        img = openpyxl.drawing.image.Image('../' + iss.image)
        img.anchor = f'G{str(row_position)}'
        img.width = img.width / 3
        img.height = img.height / 3
        ws.add_image(img)
        ws.row_dimensions[row_position].height = 240

        row_position += 1
    wb.save(filename=filename)


def Create_headlines(ws):
    ws['A1'] = "№"
    ws['B1'] = "Дата"
    ws['C1'] = "Тип обращения"
    ws['D1'] = "Адрес"
    ws['E1'] = "Описание"
    ws['F1'] = "Геопозиция"
    ws['G1'] = "Фото"

def combine_reports():
    """
    Объединяет отчёты в один файл
    """
    issues = []
    # TODO: ignore combined_export.yaml
    folder_path = "../data/"
    issues = issue_combiner.open_and_load_to_array(folder_path)
    issue_combiner.save_to_yml(issues, "../data/combined_export.yaml")


def select_issues_by_date(date: str, issues):
    """
    :param date: дата в формате год-месяц-день
    :param issues: список issues
    :return: выбранные issues по дате
    """
    date_time_obj = datetime.datetime.strptime(date, '%Y-%m-%d')
    sorted_issues = []
    iss: Models.Issue
    for iss in issues:
        if date_time_obj.date() == iss.send_time.date():
            sorted_issues.append(iss)

    return sorted_issues

def img_relative_path():
    """
    Делает путь к изображениям относительным
    """
    issues = issue_combiner.load_from_yaml("../data/export_w_addr.yaml")
    iss: Models.Issue
    for iss in issues:
        iss.image = iss.image.replace('/home/danil0111/bkg_bot/', '')
    issue_combiner.save_to_yml(issues, "../data/export_w_addr.yaml")


def load_addresses():
    """
    Загружает адреса по гео-координатам
    :return:
    """
    issues = issue_combiner.load_from_yaml("../data/combined_export.yaml")
    iss: Models.Issue
    for iss in issues:
        try:
            if (iss.geo != None):

                geo = iss.geo.split(',')
                iss.address = reverse_geocode(geo[0], geo[1])[0]['unrestricted_value']
        except Exception as exc:
            print(f"No address in {iss.geo} {exc}")

    issue_combiner.save_to_yml(issues, "../data/export_w_addr.yaml")

def reverse_geocode(lat, lon):
    """
    Преобразует координаты в адрес
    :rtype: str address
    """
    with Dadata(secret.dadata_token, secret.dadata_secret) as dadata:
        return dadata.geolocate(name='address', lat=lat, lon=lon)


if __name__ == '__main__':
    excel_export_main()
