import requests
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By 
from selenium.webdriver.chrome.service import Service
from time import sleep

class BotDriver:
    def __init__(self, driver_path, *options):
        self.browser = self.make_firefox_browser(driver_path, *options)
        self.root_folder = Path(__file__).parent

    def make_firefox_browser(self, path, *options):
        firefox_options = webdriver.FirefoxOptions()
        if options:
            for option in options:
                firefox_options.add_argument(option)
        
        firefox_service = Service(executable_path=str(path))
        browser = webdriver.Firefox(service=firefox_service, options=firefox_options)
        return browser

    def extract_general_info(self, html_tags, audits_r):
        names, country, year, links = ([] for _ in range(4))

        for html_tag in html_tags:
            for audit in audits_r:
                found = audit.find('div', attrs={'class': html_tag})
                if found:
                    if html_tag.endswith('nombre_empresa'):
                        names.append(found.text)
                    elif html_tag.endswith('pais'):
                        country.append(found.text)
                    else:
                        year.append(found.text)

        a_tags = audits_r.find_all('a', href=True)
        links = [tag['href'] for tag in a_tags]

        certified_producers_rtrs = pd.DataFrame(list(zip(names[1:], country[1:], year[1:], links)),
                                                columns=['Names', 'Country', 'Year', 'Links'])
        certified_producers_rtrs['Year'] = pd.to_numeric(certified_producers_rtrs['Year'])
        certified_producers_rtrs.to_csv(self.root_folder / 'certified_producers_rtrs.csv')
        
        return certified_producers_rtrs, links

    def download_all_reports(self, links):
        for i, link in enumerate(links, start=1):
            response = requests.get(link)
            naming_files = f'audit_report_rtrs{i}.pdf'
            files = self.root_folder / 'audit_reports' / naming_files
            files.touch()
            with open(files, 'wb') as PdfObj:
                PdfObj.write(response.content)
                print(f"File {i} downloaded")
        print("All PDF files downloaded!")

if __name__ == '__main__':
    ROOT_FOLDER = Path(__file__).parent
    GECKO_DRIVER_PATH = ROOT_FOLDER / 'geckodriver'  
    html_tags = ['vc_col-md-6 vc_col-xs-12 zyxaudit-nombre_empresa', 'vc_col-md-2 vc_col-xs-12 zyxaudit-pais', 'vc_col-md-2 vc_col-xs-12 zyxaudit-anio']
    options = ()

    bot = BotDriver(GECKO_DRIVER_PATH, *options)
    bot.browser.get('https://responsiblesoy.org/public-audit-reports?lang=en')
    bot.browser.find_element(By.CLASS_NAME, 'zyxaudit-btn_buscar').click()
    sleep(2)  
    html = BeautifulSoup(bot.browser.page_source, 'html.parser')
    bot.browser.quit()
    audits_r = html.find('div', attrs={'class': 'zyxaudit-buscador_results vc_col-xs-12 col-xs-12 zyxaudit-results-active'})
    _, links = bot.extract_general_info(html_tags, audits_r)
    bot.download_all_reports(links)
