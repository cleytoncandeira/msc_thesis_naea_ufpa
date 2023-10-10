import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from time import sleep
from pathlib import Path

class UFPAScraper:
    def __init__(self, chromedriver_path):
        self.chromedriver_path = chromedriver_path
        self.browser = self.make_chrome_browser()

    def make_chrome_browser(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")  # Para executar em segundo plano sem abrir uma janela do navegador
        chrome_service = Service(executable_path=str(self.chromedriver_path))
        browser = webdriver.Chrome(service=chrome_service, options=chrome_options)
        return browser

    def extract_theses_info(self, start_year, end_year):
        thesis_data = []

        for year in range(start_year, end_year + 1):
            url = f"https://www.ppgdstu.propesp.ufpa.br/index.php/br/teses-e-dissertacoes/teses?limit=10&start=0&year={year}"
            self.browser.get(url)
            sleep(2)  # Aguarda carregar a página

            html = BeautifulSoup(self.browser.page_source, 'html.parser')
            theses = html.find_all("div", class_="item-page")

            for thesis in theses:
                author = thesis.find("p", class_="teses-autor").text.strip()
                title = thesis.find("h2", class_="item-title").text.strip()
                advisor = thesis.find("p", text="Orientador:").find_next("p").text.strip()

                thesis_info = {
                    "Year": year,
                    "Author": author,
                    "Title": title,
                    "Advisor": advisor,
                }

                thesis_data.append(thesis_info)

        return thesis_data

    def scrape_and_save_theses(self, start_year, end_year, output_csv):
        thesis_data = self.extract_theses_info(start_year, end_year)

        df = pd.DataFrame(thesis_data)
        df.to_csv(output_csv, index=False)

if __name__ == "__main__":
    ROOT_FOLDER = Path(__file__).parent
    CHROME_DRIVER_PATH = ROOT_FOLDER / 'drivers' / 'chromedriver.exe'
    OUTPUT_CSV = ROOT_FOLDER / 'teses_ufpa.csv'

    scraper = UFPAScraper(CHROME_DRIVER_PATH)
    scraper.scrape_and_save_theses(2003, 2023, OUTPUT_CSV)
