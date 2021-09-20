import os
import yaml


def upload_yamls_to_list(folder_path):
    """
    Combine objects from yaml files to list
    :param folder_path: path to folder with yaml files to combine to list
    :return:
    """
    loaded_list = []
    for file in os.listdir(folder_path):
        if file.endswith(".yaml"):
            loaded_list.append(load_from_yaml(folder_path + file))
    return loaded_list


def load_from_yaml(filepath):
    """
    Load object from yaml file
    :param filepath: file path
    :return: loaded object
    """
    with open(filepath, "r", encoding="utf-8") as ff:
        return yaml.load(ff, Loader=yaml.UnsafeLoader)


def save_to_yml(object_to_save, file_path):
    """
    Save object to yaml file
    :param object_to_save: object to save
    :param file_path: saving file path
    :return: file path
    """
    with open(file_path, 'w', encoding="utf-8") as ff:
        yaml.dump(object_to_save, ff, default_flow_style=False, allow_unicode=True)
    return file_path
