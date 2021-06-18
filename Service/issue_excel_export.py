import datetime
import openpyxl
from PIL import Image

import issue_combiner
import Models
import secret
from openpyxl import Workbook
from dadata import Dadata


def excel_export_main():
    # load_addresses()
    # img_relative_path()

    wb = Workbook()
    ws = wb.active

    ws['A1'] = "№"
    ws['B1'] = "Дата"
    ws['C1'] = "Тип обращения"
    ws['D1'] = "Адрес"
    ws['E1'] = "Описание"
    ws['F1'] = "Геопозиция"
    ws['G1'] = "Фото"
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
        img.width = img.width/3
        img.height = img.height / 3
        ws.add_image(img)
        ws.row_dimensions[row_position].height = 240

        row_position += 1
    wb.save(filename=f'../data/export{str(datetime.datetime.now().date())}.xlsx')

    print("saved")


def img_relative_path():
    issues = issue_combiner.load_from_yaml("../data/export_w_addr.yaml")
    iss: Models.Issue
    for iss in issues:
        iss.image = iss.image.removeprefix('/home/danil0111/bkg_bot/')
    issue_combiner.save_to_yml(issues, "../data/export_w_addr.yaml")


def load_addresses():
    issues = issue_combiner.load_from_yaml("../data/combined_export.yaml")
    iss: Models.Issue
    for iss in issues:
        geo = iss.geo.split(',')
        iss.address = reverse_geocode(geo[0], geo[1])[0]['unrestricted_value']
    issue_combiner.save_to_yml(issues, "../data/export_w_addr.yaml")


def reverse_geocode(lat, lon):
    """
    :rtype: str address
    """
    with Dadata(secret.dadata_token, secret.dadata_secret) as dadata:
        return dadata.geolocate(name='address', lat=lat, lon=lon)


if __name__ == '__main__':
    excel_export_main()
