# BotDriver: Selenium Web Scraper for Audit Reports

This script automates the extraction of audit report data from the RTRS website using Selenium. It collects data such as producer names, countries, years, and links to audit reports, and saves the information as a CSV file. Additionally, it downloads the audit reports in PDF format.

## Features

- Automates navigation and interaction with the RTRS website.
- Extracts country options from a dropdown menu.
- Retrieves data (producer name, country, year, and report links) from the audit reports table.
- Saves the extracted data to a CSV file.
- Downloads all audit reports in PDF format.

## Requirements

- Python 3.7+
- Google Chrome browser

## Installation

1. Clone this repository:

   ```bash
   git clone <https://github.com/cleytoncandeira/msc_thesis_naea_ufpa/tree/main/scripts/data_scrapping>
   ```

2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the script:

   ```bash
   python botdriver.py
   ```

2. The script will:

   - Open the RTRS audit reports webpage.
   - Display a list of available countries from the dropdown menu.
   - Automatically select "Brazil" and initiate a search.
   - Extract relevant data and save it as a CSV file in the `data/external_data` folder.
   - Download the PDF audit reports to the `data/external_data/audit_reports` folder.

## File Structure

- **data/external_data/**
  - Contains the CSV file with extracted data.
  - Subfolder for downloaded audit reports in PDF format.

## Customization

- You can modify the default country selection by changing the `bot.select_country("Brazil")` line to your desired country.

## Notes

- Ensure that Google Chrome is installed on your machine.
- If the website layout changes, some selectors may need to be updated in the script.
- Adjust the timeout durations in `WebDriverWait` if necessary for your network conditions.

## Dependencies

Refer to the `requirements.txt` file for the list of Python dependencies.

