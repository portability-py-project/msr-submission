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
            modules.append(
                (module_name, import_module(f'{CONFIG["scraper_dir"]}.{module_name}'))
            )
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
        with open(file_path, "r", encoding='utf-8') as file:
            return BeautifulSoup(file.read(), "html.parser")
    except Exception as e:
        print(f"Error loading HTML file {file_path}: {e}")
        raise


def format_class_name(module_name):
    parts = module_name.split("_")
    class_name = "".join(part.capitalize() for part in parts) + "Scraper"
    return class_name


def find_class(module, base_name):
    target_name = base_name.lower() + "scraper"
    for name in dir(module):
        if name.lower() == target_name:
            return getattr(module, name)
    raise AttributeError(
        f"Module '{module.__name__}' does not have a class matching '{base_name}Scraper'"
    )


@pytest.mark.parametrize(
    "scraper_module, base_url_file, html_file, exp_output_file",
    [
        (module, base_url, html, exp_output)
        for module in get_scraper_modules()
        for base_url, html, exp_output in get_test_files()
        if module[0] == os.path.basename(html)[:-9]
    ],
)
def test_scraper(mocker, scraper_module, base_url_file, html_file, exp_output_file):
    module_name, module = scraper_module
    scraper_class = find_class(module, module_name)

    with open(base_url_file, newline="", encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        row = next(reader, None)
        if row:
            base_url = row[0]

    with open(html_file, "r", encoding='utf-8') as file:
        html_content = file.read()

    scraper = scraper_class(base_url=base_url, html=html_content)

    if not hasattr(scraper, "soup"):
        scraper.soup = BeautifulSoup(html_content, "html.parser")

    scraped_links = scraper.scrape()

    expected_links = []
    with open(exp_output_file, newline="", encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            expected_links.extend(row)

    assert set(scraped_links) == set(expected_links), f"The scraped links do not match the expected links for {module_name}."