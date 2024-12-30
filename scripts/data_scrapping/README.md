# Web Scraping Bot

This script performs web scraping on `https://responsiblesoy.org/public-audit-reports` to extract general information and download reports.

## Requirements

- Python 3.8+
- Python libraries: 
    - `requests 2.25.1`
    - `pandas 1.2.3`
    - `beautifulsoup4 4.9.3`
    - `selenium 3.141.0`
    - `Firefox (comentar a versão usada em BotDriver)`
    - `Geckodriver (compatível com a versão do Firefox)`

## Installation

Install the dependencies using pip:

```bash
pip install requests pandas beautifulsoup4 selenium

```

### Script Structure

```python
BotDriver class
__init__(self, driver_path, *options)

```
- Description: Initializes the browser driver.
- Parameters:
        driver_path: Path to the Geckodriver executable.
        *options: Additional options for the Firefox browser.
- Functionality: Creates an instance of the Firefox browser with the options provided and sets the root directory to save the downloaded files.

```python
make_firefox_browser(self, path, *options)
```

- Description: Creates an instance of the Firefox browser.
- Parameters:
        path: Path to the Geckodriver executable.
        *options: Additional options for the Firefox browser.
- Return: Firefox browser instance configured.

```python
extract_general_info(self, html_tags, audits_r)
```

- Description: Extracts general information from audit reports from an HTML page.
- Parameters:
    - html_tags: List of CSS classes to locate the HTML elements containing the desired information.
    - audits_r: BeautifulSoup object representing the HTML of the reports page.
    - Return: pandas DataFrame containing the extracted information and the list of download links.

```python
download_all_reports(self, links)
```
- Description: Downloads all the reports listed in the links provided.
- Parameters:
- links: List of URLs of the reports to download.
- Functionality: Iterates over the list of links, downloads each report and saves it in the specified directory.
