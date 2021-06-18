import os

import yaml

import Models
from Models import Issue

issues = []
def combiner_main():
    folder_path = "../data/"
    issues = open_and_load_to_array(folder_path)
    save_to_yml(issues, "../data/combined_export.yaml")
    print_issues_with_address()


def open_and_load_to_array(folder_path):
    arr = []
    for file in os.listdir(folder_path):
        if file.endswith(".yaml"):
            arr.append(load_from_yaml(folder_path+file))
    return arr

def load_from_yaml(filepath):
    with open(filepath, "r", encoding="utf-8") as ff:
        return yaml.load(ff, Loader=yaml.UnsafeLoader)

def print_issues_with_address():
    iss: Models.Issue
    for iss in issues:
        if iss.address is not None:
            print(iss)

def save_to_yml(serializable_obj, file_path):
    with open(file_path, 'w', encoding="utf-8") as ff:
        yaml.dump(serializable_obj, ff, default_flow_style=False, allow_unicode=True)
    return file_path


if __name__ == '__main__':
    combiner_main()