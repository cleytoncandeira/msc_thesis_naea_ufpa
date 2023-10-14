import unittest
import os
from selenium import webdriver
from pathlib import Path
from bot_driver import BotDriver

class TestBotDriver(unittest.TestCase):
    def setUp(self):
        self.chrome_driver_path = Path("path/to/chromedriver")  # Replace with the actual path
        self.bot_driver = BotDriver()
    
    def test_make_chrome_browser(self):
        options = ['--headless']
        browser = self.bot_driver.make_chrome_browser(self.chrome_driver_path, *options)
        self.assertIsInstance(browser, webdriver.Chrome)
        browser.quit()
    
    def test_extract_general_info(self):
        html_tags = ['vc_col-md-6 vc_col-xs-12 zyxaudit-nombre_empresa',
                     'vc_col-md-2 vc_col-xs-12 zyxaudit-pais',
                     'vc_col-md-2 vc_col-xs-12 zyxaudit-anio']
        audits_r = BeautifulSoup('<html>Your HTML content here</html>', 'html.parser')  # Replace with actual HTML content
        certified_producers_rtrs, links = self.bot_driver.extract_general_info(html_tags, audits_r)
        self.assertIsInstance(certified_producers_rtrs, pd.DataFrame)
        self.assertIsInstance(links, list)
    
    def test_download_all_reports(self):
        links = ['https://example.com/report1.pdf', 'https://example.com/report2.pdf']  # Replace with actual links
        self.bot_driver.download_all_reports(links)
        # Check if files were downloaded
        for i in range(1, len(links) + 1):
            file_name = f'audit_report_rtrs{i}.pdf'
            self.assertTrue(os.path.isfile(file_name))
    
if __name__ == '__main__':
    unittest.main()

