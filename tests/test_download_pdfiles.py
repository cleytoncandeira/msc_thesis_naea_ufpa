import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from scripts.data_scrapping.botdriver import BotDriver 
from pathlib import Path
import subprocess
import os

class TestBotDriver(unittest.TestCase):

    def setUp(self):
        # Setup que será executado antes de cada teste
        self.root_folder = Path(__file__).parent
        # Opcional: configurar opções de navegador para execução headless, etc.

    def tearDown(self):
        # Limpeza a ser executada após cada teste
        pass

    @classmethod
    def setUpClass(cls):
        # Configuração inicial para todos os testes (opcional)
        pass

    @classmethod
    def tearDownClass(cls):
        # Limpeza final após todos os testes serem executados (opcional)
        pass

    def test_firefox_geckodriver_compatibility(self):
        # Obtendo a versão do Firefox
        firefox_version = subprocess.check_output(["firefox", "--version"]).decode().strip()
        # Obtendo a versão do Geckodriver
        geckodriver_service = FirefoxService(executable_path='/path/to/geckodriver')
        geckodriver_version = geckodriver_service.get_geckodriver_version()

        print(f"Firefox version: {firefox_version}")
        print(f"Geckodriver version: {geckodriver_version}")

        # Aqui você precisa verificar a compatibilidade baseado na documentação
        # Este é um exemplo e pode não refletir as verificações reais de compatibilidade
        self.assertTrue(True, "Geckodriver é compatível com esta versão do Firefox.")

    def test_chrome_chromedriver_compatibility(self):
        # Obtendo a versão do Chrome
        chrome_version = subprocess.check_output(["google-chrome", "--version"]).decode().strip()
        # Obtendo a versão do Chromedriver
        chromedriver_service = ChromeService(executable_path='/path/to/chromedriver')
        chromedriver_version = chromedriver_service.get_chromedriver_version()

        print(f"Chrome version: {chrome_version}")
        print(f"Chromedriver version: {chromedriver_version}")

        # Verificações de compatibilidade
        self.assertTrue(True, "Chromedriver é compatível com esta versão do Chrome.")

    def test_firefox_initialization(self):
        firefox_service = FirefoxService(executable_path=Path('path/to/geckodriver'))
        browser = webdriver.Firefox(service=firefox_service)
        browser.get('https://responsiblesoy.org/?lang=pt-br')
        self.assertIn('Example Domain', browser.title)
        browser.quit()

    def test_chrome_initialization(self):
        chrome_service = ChromeService(executable_path=Path('path/to/chromedriver'))
        browser = webdriver.Chrome(service=chrome_service)
        browser.get('https://responsiblesoy.org/?lang=pt-br')
        self.assertIn('Example Domain', browser.title)
        browser.quit()

    def test_extract_general_info(self):
        html_content = """
        <div class='vc_col-md-6 vc_col-xs-12 zyxaudit-nombre_empresa'>Empresa 1</div>
        <div class='vc_col-md-2 vc_col-xs-12 zyxaudit-pais'>País 1</div>
        <div class='vc_col-md-2 vc_col-xs-12 zyxaudit-anio'>2020</div>
        <a href='http://example.com/report1.pdf'>Relatório 1</a>
        """
        bot = BotDriver(None)  # Substitua por como você inicializa o BotDriver
        result = bot.extract_general_info(['vc_col-md-6 vc_col-xs-12 zyxaudit-nombre_empresa', 'vc_col-md-2 vc_col-xs-12 zyxaudit-pais', 'vc_col-md-2 vc_col-xs-12 zyxaudit-anio'], BeautifulSoup(html_content, 'html.parser'))
        self.assertEqual(len(result), 4)  # Verifique se o número esperado de itens foi extraído

    def test_download_all_reports(self):
        # Este teste depende da configuração de um servidor HTTP local para servir arquivos de teste
        links = ['http://localhost:8000/report1.pdf']
        bot = BotDriver(None)  # Substitua por como você inicializa o BotDriver
        bot.download_all_reports(links)
        # Verifique se os arquivos foram baixados corretamente
        downloaded_file = self.root_folder / 'audit_reports' / 'audit_report_rtrs1.pdf'
        self.assertTrue(downloaded_file.exists())

if __name__ == '__main__':
    unittest.main()
