from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import requests
from pathlib import Path
from bs4 import BeautifulSoup
import time
from tqdm import tqdm

class BotDriver:
    def __init__(self, *options):
        self.browser = self.make_chrome_browser(*options)
        self.root_folder = Path(__file__).parent

        # Aponta para: .../meu_repositorio_dissertacao/data/external_data
        self.external_data_folder = (
            self.root_folder.parent.parent / 'data' / 'external_data'
        )
        self.external_data_folder.mkdir(parents=True, exist_ok=True)

    def make_chrome_browser(self, *options):
        chrome_options = webdriver.ChromeOptions()
        for opt in options:
            chrome_options.add_argument(opt)

        service = Service(ChromeDriverManager().install())
        browser = webdriver.Chrome(service=service, options=chrome_options)
        browser.maximize_window()  # opcional
        return browser

    def get_country_list(self):
        wait = WebDriverWait(self.browser, 30)
        country_select_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "select.zyxaudit-campo_pais"))
        )
        dropdown = Select(country_select_element)
        return [opt.text.strip() for opt in dropdown.options]

    def select_country(self, country_name):
        wait = WebDriverWait(self.browser, 30)
        country_select_element = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "select.zyxaudit-campo_pais"))
        )
        dropdown = Select(country_select_element)
        dropdown.select_by_visible_text(country_name)
        time.sleep(1)

    def click_search(self):
        wait = WebDriverWait(self.browser, 15)
        search_button = wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, "zyxaudit-btn_buscar"))
        )
        try:
            search_button.click()
        except ElementClickInterceptedException:
            print("Pop-up interceptou o clique no botão Search. Fechando pop-up...")
            close_btn = wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "pum-close"))
            )
            close_btn.click()
            time.sleep(1)
            search_button.click()

    def extract_general_info(self, audits_r_list):
        names, countries, years, links = [], [], [], []

        for line in audits_r_list:
            found_name = line.find(
                "div",
                class_="vc_col-md-6 vc_col-xs-12 zyxaudit-nombre_empresa"
            )
            found_country = line.find(
                "div",
                class_="vc_col-md-2 vc_col-xs-12 zyxaudit-pais"
            )
            found_year = line.find(
                "div",
                class_="vc_col-md-2 vc_col-xs-12 zyxaudit-anio"
            )

            name_text = found_name.get_text(strip=True) if found_name else ""
            country_text = found_country.get_text(strip=True) if found_country else ""
            year_text = found_year.get_text(strip=True) if found_year else ""

            anchor_tag = line.find("a", href=True)
            pdf_link = anchor_tag["href"] if anchor_tag else ""

            names.append(name_text)
            countries.append(country_text)
            years.append(year_text)
            links.append(pdf_link)

        df = pd.DataFrame({
            "Names": names,
            "Country": countries,
            "Year": years,
            "Links": links
        })
        df["Year"] = pd.to_numeric(df["Year"], errors="coerce")

        # Salva o CSV na pasta external_data
        csv_path = self.external_data_folder / 'certified_producers_rtrs.csv'
        df.to_csv(csv_path, index=False)

        return df, links

    def download_all_reports(self, links):
        if not links:
            print("Nenhum link disponível para download.")
            return

        pdf_folder = self.external_data_folder / 'audit_reports'
        pdf_folder.mkdir(parents=True, exist_ok=True)

        for i, link in enumerate(tqdm(links, desc="Baixando PDFs", unit="pdf"), start=1):
            if not link:
                continue
            response = requests.get(link)
            file_name = f"audit_report_rtrs{i}.pdf"
            file_path = pdf_folder / file_name

            with open(file_path, "wb") as pdf_obj:
                pdf_obj.write(response.content)

        print("\nTodos os PDFs foram baixados com sucesso.")


if __name__ == "__main__":
    options = ()
    bot = BotDriver(*options)

    # 1) Acessa o site
    bot.browser.get("https://responsiblesoy.org/public-audit-reports?lang=en")

    # 2) Lista países
    try:
        countries = bot.get_country_list()
        print("Lista de países no dropdown:")
        for c in countries:
            print(f" - {c}")
    except Exception as e:
        print(f"Erro ao tentar obter lista de países: {e}")
        bot.browser.quit()
        raise

    # 3) Seleciona "Brazil"
    try:
        bot.select_country("Brazil")
    except Exception as e:
        print(f"Erro ao selecionar o país: {e}")

    # 4) Clica em "Search"
    try:
        bot.click_search()
    except Exception as e:
        print(f"Erro ao clicar em Search: {e}")

    # 5) Coleta HTML
    time.sleep(2)
    html = BeautifulSoup(bot.browser.page_source, "html.parser")
    bot.browser.quit()

    # 6) Cada relatório -> <div class="zyxaudit-result-line">
    audits_r_list = html.find_all("div", class_="zyxaudit-result-line")
    if not audits_r_list:
        print("Nenhum relatório encontrado ou a classe 'zyxaudit-result-line' mudou.")
    else:
        df, links = bot.extract_general_info(audits_r_list)
        bot.download_all_reports(links)
