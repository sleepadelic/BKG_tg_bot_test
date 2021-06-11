import os

import yaml

from Models import Issue

issues = []
def combiner_main():
    for file in os.listdir("../data/"):
        if file.endswith(".yaml"):
            with open("../data/"+file, "r", encoding="utf-8") as ff:
                obj = yaml.load(ff, Loader=yaml.UnsafeLoader)
                issues.append(obj)
    save_to_yml(issues, "../data/combined_export.yaml")
    print("saved")







def save_to_yml(serializable_obj, file_path):
    with open(file_path, 'w', encoding="utf-8") as ff:

        yaml.dump(serializable_obj, ff, default_flow_style=False, allow_unicode=True)
    return file_path


if __name__ == '__main__':
    combiner_main()