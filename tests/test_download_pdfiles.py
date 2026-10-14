"""Testes unitários da camada legada de download, sem navegador ou rede real."""

from pathlib import Path
from unittest.mock import MagicMock

from bs4 import BeautifulSoup

from scripts.data_scrapping.botdriver import BotDriver


def test_extract_general_info_from_result_row(tmp_path: Path):
    browser = MagicMock()
    bot = BotDriver(browser=browser, external_data_folder=tmp_path)
    html = BeautifulSoup(
        """
        <div class='zyxaudit-result-line'>
          <div class='vc_col-md-6 vc_col-xs-12 zyxaudit-nombre_empresa'>Empresa 1</div>
          <div class='vc_col-md-2 vc_col-xs-12 zyxaudit-pais'>Brazil</div>
          <div class='vc_col-md-2 vc_col-xs-12 zyxaudit-anio'>2020</div>
          <a href='https://example.org/report1.pdf'>Relatório 1</a>
        </div>
        """,
        "html.parser",
    )

    data, links = bot.extract_general_info(html.select(".zyxaudit-result-line"))

    assert data.loc[0, "Names"] == "Empresa 1"
    assert data.loc[0, "Year"] == 2020
    assert links == ["https://example.org/report1.pdf"]


def test_download_all_reports_uses_injected_browser_and_downloads(tmp_path: Path, monkeypatch):
    browser = MagicMock()
    bot = BotDriver(browser=browser, external_data_folder=tmp_path)
    response = MagicMock()
    response.iter_content.return_value = [b"%PDF-1.7", b" body"]
    monkeypatch.setattr("scripts.data_scrapping.botdriver.requests.get", lambda *args, **kwargs: response)
    monkeypatch.setattr("scripts.data_scrapping.botdriver.tqdm", lambda items, **_: items)

    bot.download_all_reports(["https://example.org/report1.pdf"])

    assert (tmp_path / "audit_reports" / "audit_report_rtrs1.pdf").read_bytes() == b"%PDF-1.7 body"
