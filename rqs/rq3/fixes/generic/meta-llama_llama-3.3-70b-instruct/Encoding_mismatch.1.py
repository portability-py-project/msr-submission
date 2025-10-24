```python
import pytest
import csv
import os
from bs4 import BeautifulSoup
from importlib import import_module

CONFIG = {"scraper_dir": "recipe_urls", "test_dir": "tests/test_data"}


def get_scraper_modules():
    modules = []
    for module_file in os.listdir(CONFIG["scraper_dir"]):
        if module_file.endswith(".py") and not module_file.startswith("_"):
            module_name = module_file[:-3]
            try:
                module = import_module(f'.{module_name}', package=CONFIG["scraper_dir"])
                modules.append((module_name, module))
            except ImportError:
                continue
    return modules


def get_test_files():
    for dirpath, dirnames, filenames in os.walk(CONFIG["test_dir"]):
        base_url_file = next((f for f in filenames if f.endswith("_base_url.csv")), None)
        html_file = next((f for f in filenames if f.endswith(".testhtml")), None)
        exp_output_file = next((f for f in filenames if f.endswith("_exp_output.csv")), None)
        if base_url_file and html_file and exp_output_file:
            yield (os.path.join(dirpath, base_url_file), os.path.join(dirpath, html_file), os.path.join(dirpath, exp_output_file))


def load_html(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return BeautifulSoup(file.read(), "html.parser")
    except Exception as e:
        print(f"Error loading HTML file {file_path}: {e}")
        raise


def format_class_name(module_name):
    parts = module_name.split("_")
    class_name = "".join(part.capitalize() for part in parts) + "Scraper"
    return class_name


def find_class(module, base_nam