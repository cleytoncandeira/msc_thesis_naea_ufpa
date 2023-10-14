import requests
import pandas as pd
from pathlib import Path
from PyPDF2 import PdfFileReader
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By 
from selenium.webdriver.chrome.service import Service
from time import sleep

############################################################
############# HERE BEGINS THE OPERA ########################
############################################################

class BotDriver:

    def make_chrome_browser(path, *options: str) -> webdriver.Chrome:
        
        chrome_options = webdriver.ChromeOptions()  #create chrome options obj
        
        if options is not None:
            for option in options:
                chrome_options.add_argument(option) #type: ignore
            
        chrome_service = Service(               
            executable_path = str(path),
        )
        
        browser = webdriver.Chrome(
            service = chrome_service, 
            options = chrome_options
        )
        
        return browser

    def extract_general_info(html_tags, audits_r):

            names, country, year, links = ([] for i in range(4))

            for html_tag in html_tags:
                for audit in audits_r:
                    found = audit.find('div', attrs = {'class':html_tag})
    
                    if html_tag.endswith('nombre_empresa'):
                        names.append(found.text)
                    elif html_tag.endswith('pais'):
                        country.append(found.text)
                    else:
                        year.append(found.text)

            #links to download audit reports             
            a_tags = audits_r.find_all('a', href = True)
            links = [tag['href'] for tag in a_tags]      

            #create a data frame obj

            certified_producers_rtrs = pd.DataFrame(list(zip(
                names[1:len(names)],
                country[1:len(country)],
                year[1:len(year)],
                links)), 
                columns = ['Names', 'Country', 'Year', 'Links'])
            
            certified_producers_rtrs['Year'] = pd.to_numeric(certified_producers_rtrs['Year'])
            certified_producers_rtrs.to_csv(ROOT_FOLDER / 'certified_producers_rtrs.csv')
        
            return certified_producers_rtrs, links

    def download_all_reports(links):
        i = 0

        for link in links:

            i += 1
            response = requests.get(link)

            naming_files = 'audit_report_rtrs' + str(i) + '.pdf'
            files = ROOT_FOLDER / 'audit_reports' / naming_files
            files.touch()

            with open(files, 'wb') as PdfObj:
                PdfObj.write(response.content)

                print("File ", i, " downloaded")
        return print("All PDF files downloaded!")

########################################################################
#################### ACTION! ###########################################
########################################################################

ROOT_FOLDER = Path(__file__).parent

CHROME_DRIVER_PATH = ROOT_FOLDER / 'drivers' / 'chromedriver'

html_tags = ['vc_col-md-6 vc_col-xs-12 zyxaudit-nombre_empresa',
                    'vc_col-md-2 vc_col-xs-12 zyxaudit-pais', 
                    'vc_col-md-2 vc_col-xs-12 zyxaudit-anio', ]

#options = 'user-data-dir=Perfil'
options = ()

browser = BotDriver.make_chrome_browser(CHROME_DRIVER_PATH, *options)
        
browser.get('https://responsiblesoy.org/public-audit-reports?lang=en')

browser.find_element(By.CLASS_NAME, 'zyxaudit-btn_buscar').click()

sleep(2)

#Integrate bs4 and Selenium -- When Vegeta and Goku merge!

html = BeautifulSoup(browser.page_source, 'html.parser')

browser.quit()

audits_r = html.find('div', 
            attrs={'class': 'zyxaudit-buscador_results vc_col-xs-12 col-xs-12 zyxaudit-results-active'})

certified_producers_rtrs, links = BotDriver.extract_general_info(html_tags, audits_r)

if __name__ == '__main__':  

    BotDriver.download_all_reports(links) #Problem: it's so lazy! 
    
########################################################################################################
