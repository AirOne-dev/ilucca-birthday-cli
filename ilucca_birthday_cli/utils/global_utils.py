import configparser
import os


def get_config():
    config_file_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), 
        "..", 
        "..", 
        "config.ini"
    )

    config = configparser.ConfigParser()
    config.read(config_file_path)
    return config
