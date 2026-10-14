"""Raspagem de relatórios públicos da RTRS via Selenium.

Exemplo rápido (Python):
    from scripts.data_scrapping.botdriver import run_scraping
    df, links, countries = run_scraping(country="Brazil", download_pdfs=True)

Exemplo CLI:
    python scripts/data_scrapping/botdriver.py --country Brazil --download-pdfs --headless
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Any, Iterable, List, Optional, Sequence, Tuple, Union

import pandas as pd
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from tqdm import tqdm
from webdriver_manager.chrome import ChromeDriverManager

PathLike = Union[str, Path]


class BotDriver:
    """Automatiza a coleta de relatórios públicos da RTRS."""

    DEFAULT_BASE_URL: str = "https://responsiblesoy.org/public-audit-reports?lang=en"

    def __init__(
        self,
        *options: str,
        browser: Optional[WebDriver] = None,
        external_data_folder: Optional[PathLike] = None,
        base_url: Optional[str] = None,
        wait_timeout: int = 30,
        click_timeout: int = 15,
        request_timeout: int = 60,
        chrome_binary: Optional[PathLike] = None,
        driver_path: Optional[PathLike] = None,
        user_agent: Optional[str] = None,
        stealth_mode: bool = True,
    ) -> None:
        """Configura o driver Selenium e caminhos de saída."""

        self.chrome_binary = Path(chrome_binary).expanduser().resolve() if chrome_binary else None
        self.driver_path = Path(driver_path).expanduser().resolve() if driver_path else None
        self.user_agent = user_agent
        self.stealth_mode = stealth_mode
        self.browser = browser or self.make_chrome_browser(*options)
        self.root_folder = Path(__file__).resolve().parent

        default_data_folder = self.root_folder.parent.parent / "data" / "external_data"
        if external_data_folder:
            self.external_data_folder = Path(external_data_folder).expanduser().resolve()
        else:
            self.external_data_folder = default_data_folder
        self.external_data_folder.mkdir(parents=True, exist_ok=True)

        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.wait_timeout = wait_timeout
        self.click_timeout = click_timeout
        self.request_timeout = request_timeout

    def make_chrome_browser(self, *options: str) -> WebDriver:
        """Cria uma instância do Chrome com as opções informadas."""

        chrome_options = webdriver.ChromeOptions()
        for opt in options:
            chrome_options.add_argument(opt)

        if self.chrome_binary:
            chrome_options.binary_location = str(self.chrome_binary)

        if self.user_agent:
            chrome_options.add_argument(f"--user-agent={self.user_agent}")

        if self.stealth_mode:
            # Ajustes simples para reduzir detecção do Selenium.
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)

        if self.driver_path:
            service = Service(str(self.driver_path))
        else:
            service = Service(ChromeDriverManager().install())
        browser = webdriver.Chrome(service=service, options=chrome_options)
        if self.stealth_mode:
            browser.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});",
                },
            )
        browser.maximize_window()
        return browser

    def close(self) -> None:
        """Fecha o navegador, se estiver aberto."""

        if self.browser:
            self.browser.quit()
            self.browser = None

    def load_base_page(self) -> None:
        """Abre a página inicial e trata o banner de cookies."""

        self.browser.get(self.base_url)
        self._handle_cookie_banner()

    def _handle_cookie_banner(self) -> None:
        """Tenta aceitar o banner de cookies, quando presente."""

        try:
            wait = WebDriverWait(self.browser, 10)
            modal = wait.until(
                EC.presence_of_element_located((By.ID, "pop_up_cookies"))
            )
        except Exception:
            return

        if not modal.is_displayed():
            return

        try:
            agree_button = modal.find_element(By.LINK_TEXT, "Agree")
        except Exception:
            # fallback: pega o último link/botão visível
            clickable_elements = [
                elem for elem in modal.find_elements(By.TAG_NAME, "a") + modal.find_elements(By.TAG_NAME, "button")
                if elem.is_displayed() and elem.is_enabled()
            ]
            agree_button = clickable_elements[-1] if clickable_elements else None

        if agree_button:
            agree_button.click()
            time.sleep(1)

    def _wait_until(self, condition: Any, timeout: Optional[int] = None) -> Any:
        """Atalho para waits explícitos do Selenium."""

        wait = WebDriverWait(self.browser, timeout or self.wait_timeout)
        return wait.until(condition)

    def get_country_list(self) -> List[str]:
        """Retorna a lista de países disponíveis no dropdown."""

        country_select_element = self._wait_until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "select.zyxaudit-campo_pais"))
        )
        dropdown = Select(country_select_element)
        return [opt.text.strip() for opt in dropdown.options]

    def select_country(self, country_name: str) -> None:
        """Seleciona um país no dropdown."""

        country_select_element = self._wait_until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "select.zyxaudit-campo_pais"))
        )
        dropdown = Select(country_select_element)
        dropdown.select_by_visible_text(country_name)
        time.sleep(1)

    def click_search(self) -> None:
        """Clica no botão de busca, lidando com pop-ups."""

        wait = WebDriverWait(self.browser, self.click_timeout)
        try:
            search_button = wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "zyxaudit-btn_buscar"))
            )
        except Exception:
            search_button = self.browser.find_element(By.CLASS_NAME, "zyxaudit-btn_buscar")

        self.browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", search_button)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "zyxaudit-btn_buscar")))
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
        except Exception:
            # Fallback quando o click padrão não funciona.
            self.browser.execute_script("arguments[0].click();", search_button)

    def extract_general_info(
        self,
        audits_r_list: Iterable[Tag],
        csv_name: str = "certified_producers_rtrs.csv",
    ) -> Tuple[pd.DataFrame, List[str]]:
        """Extrai nome, país, ano e link do PDF a partir do HTML."""

        names: List[str] = []
        countries: List[str] = []
        years: List[str] = []
        links: List[str] = []

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

        df = pd.DataFrame(
            {
                "Names": names,
                "Country": countries,
                "Year": years,
                "Links": links,
            }
        )
        df["Year"] = pd.to_numeric(df["Year"], errors="coerce")

        csv_path = self.external_data_folder / csv_name
        df.to_csv(csv_path, index=False)

        return df, links

    def download_all_reports(self, links: Iterable[str]) -> None:
        """Baixa todos os PDFs fornecidos e salva em disco."""

        if not links:
            print("Nenhum link disponível para download.")
            return

        pdf_folder = self.external_data_folder / "audit_reports"
        pdf_folder.mkdir(parents=True, exist_ok=True)

        for i, link in enumerate(tqdm(links, desc="Baixando PDFs", unit="pdf"), start=1):
            if not link:
                continue
            try:
                response = requests.get(link, stream=True, timeout=self.request_timeout)
                response.raise_for_status()
            except requests.RequestException as exc:
                print(f"Falha ao baixar {link}: {exc}")
                continue

            file_name = f"audit_report_rtrs{i}.pdf"
            file_path = pdf_folder / file_name

            if file_path.exists():
                print(f"Arquivo já existe e será mantido: {file_path.name}")
                continue

            with open(file_path, "wb") as pdf_obj:
                # Streaming evita carregar PDFs grandes na memória.
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        pdf_obj.write(chunk)

        print("\nTodos os PDFs foram baixados com sucesso.")


def run_scraping(
    *,
    country: str = "Brazil",
    base_url: Optional[str] = None,
    csv_name: str = "certified_producers_rtrs.csv",
    chrome_options: Optional[Sequence[str]] = None,
    download_pdfs: bool = False,
    external_data_folder: Optional[PathLike] = None,
    chrome_binary: Optional[PathLike] = None,
    driver_path: Optional[PathLike] = None,
    user_agent: Optional[str] = None,
    stealth_mode: bool = True,
    wait_timeout: int = 30,
    click_timeout: int = 15,
    request_timeout: int = 60,
    delay_after_search: float = 2.0,
) -> Tuple[pd.DataFrame, List[str], List[str]]:
    """Executa o fluxo completo de scraping.

    Returns:
        (df, links, countries)

    Example:
        >>> df, links, countries = run_scraping(
        ...     country="Brazil",
        ...     download_pdfs=True,
        ...     chrome_options=["--headless=new"],
        ... )
    """

    chrome_options = tuple(chrome_options or ())
    bot = BotDriver(
        *chrome_options,
        base_url=base_url,
        external_data_folder=external_data_folder,
        wait_timeout=wait_timeout,
        click_timeout=click_timeout,
        request_timeout=request_timeout,
        chrome_binary=chrome_binary,
        driver_path=driver_path,
        user_agent=user_agent,
        stealth_mode=stealth_mode,
    )

    df: pd.DataFrame = pd.DataFrame()
    links: List[str] = []
    countries: List[str] = []

    try:
        bot.load_base_page()
        countries = bot.get_country_list()
        print("Lista de países no dropdown:")
        for c in countries:
            print(f" - {c}")

        if country not in countries:
            raise ValueError(f"País '{country}' não está disponível no filtro.")

        bot.select_country(country)
        bot.click_search()

        time.sleep(delay_after_search)
        html = BeautifulSoup(bot.browser.page_source, "html.parser")
        audits_r_list = html.find_all("div", class_="zyxaudit-result-line")

        if not audits_r_list:
            print("Nenhum relatório encontrado ou a classe 'zyxaudit-result-line' mudou.")
        else:
            df, links = bot.extract_general_info(audits_r_list, csv_name=csv_name)
            print(f"Dados salvos em: {bot.external_data_folder / csv_name}")
            if download_pdfs:
                bot.download_all_reports(links)
    finally:
        bot.close()

    return df, links, countries


def build_argument_parser() -> argparse.ArgumentParser:
    """Cria o parser de argumentos do CLI."""

    parser = argparse.ArgumentParser(description="Coleta relatórios públicos da RTRS via Selenium.")
    parser.add_argument("--country", default="Brazil", help="País a ser filtrado no dropdown.")
    parser.add_argument("--base-url", default=BotDriver.DEFAULT_BASE_URL, help="URL base da página de auditorias.")
    parser.add_argument("--csv-name", default="certified_producers_rtrs.csv", help="Nome do arquivo CSV gerado.")
    parser.add_argument("--external-data-folder", type=Path, help="Pasta em que os dados serão salvos.")
    parser.add_argument("--download-pdfs", action="store_true", help="Baixa os PDFs das auditorias.")
    parser.add_argument("--headless", action="store_true", help="Executa o Chrome em modo headless.")
    parser.add_argument(
        "--chrome-option",
        action="append",
        default=[],
        dest="chrome_options",
        help="Argumento adicional para o Chrome (pode ser usado múltiplas vezes).",
    )
    parser.add_argument("--chrome-binary", type=Path, help="Caminho para o executável do Chrome/Chromium.")
    parser.add_argument("--driver-path", type=Path, help="Caminho para um chromedriver já existente.")
    parser.add_argument("--user-agent", help="User-Agent customizado para o navegador.")
    parser.add_argument("--no-stealth", action="store_true", help="Desativa ajustes anti-detecção do Selenium.")
    parser.add_argument("--wait-timeout", type=int, default=30, help="Timeout padrão para waits explícitos.")
    parser.add_argument("--click-timeout", type=int, default=15, help="Timeout para cliques no botão de busca.")
    parser.add_argument("--request-timeout", type=int, default=60, help="Timeout das requisições HTTP de download.")
    parser.add_argument("--delay-after-search", type=float, default=2.0, help="Delay após clicar em Search antes de capturar o HTML.")
    return parser


if __name__ == "__main__":
    args = build_argument_parser().parse_args()

    chrome_opts = args.chrome_options or []
    if args.headless:
        # '--headless=new' funciona bem nas versões recentes do Chrome.
        chrome_opts.append("--headless=new")
        chrome_opts.append("--disable-gpu")
        chrome_opts.append("--no-sandbox")
        chrome_opts.append("--disable-dev-shm-usage")
        chrome_opts.append("--window-size=1920,1080")

    df, links, countries = run_scraping(
        country=args.country,
        base_url=args.base_url,
        csv_name=args.csv_name,
        chrome_options=chrome_opts,
        download_pdfs=args.download_pdfs,
        external_data_folder=args.external_data_folder,
        chrome_binary=args.chrome_binary,
        driver_path=args.driver_path,
        user_agent=args.user_agent,
        stealth_mode=not args.no_stealth,
        wait_timeout=args.wait_timeout,
        click_timeout=args.click_timeout,
        request_timeout=args.request_timeout,
        delay_after_search=args.delay_after_search,
    )

    print("\nResumo:")
    print(f"Total de países encontrados: {len(countries)}")
    print(f"Total de relatórios na filtragem: {len(links)}")
    if not df.empty:
        print(df.head())
