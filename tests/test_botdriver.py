import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import scripts.data_scrapping.botdriver as botdriver_module
from scripts.data_scrapping.botdriver import BotDriver


@pytest.fixture
def browser():
    return MagicMock(name="browser")


@pytest.fixture
def bot(tmp_path, browser):
    return BotDriver(browser=browser, external_data_folder=tmp_path)


def test_init_uses_custom_external_data_folder(bot, tmp_path):
    assert bot.external_data_folder == tmp_path
    assert bot.external_data_folder.exists()


def test_get_country_list_returns_trimmed_names(bot, monkeypatch):
    fake_element = MagicMock()
    wait_mock = MagicMock(return_value=fake_element)
    monkeypatch.setattr(bot, "_wait_until", wait_mock)

    fake_select = MagicMock()
    fake_select.options = [MagicMock(text=" Brazil "), MagicMock(text="USA")]
    monkeypatch.setattr(botdriver_module, "Select", MagicMock(return_value=fake_select))

    result = bot.get_country_list()

    assert result == ["Brazil", "USA"]
    wait_mock.assert_called_once()
    botdriver_module.Select.assert_called_once_with(fake_element)


def test_select_country_invokes_select(bot, monkeypatch):
    fake_element = MagicMock()
    monkeypatch.setattr(bot, "_wait_until", MagicMock(return_value=fake_element))

    fake_select = MagicMock()
    monkeypatch.setattr(botdriver_module, "Select", MagicMock(return_value=fake_select))

    bot.select_country("Brazil")

    fake_select.select_by_visible_text.assert_called_once_with("Brazil")


def test_click_search_handles_pop_up(bot, monkeypatch):
    wait_mock = MagicMock()
    search_button = MagicMock()
    search_button.click.side_effect = [
        botdriver_module.ElementClickInterceptedException("popup"),
        None,
    ]
    close_button = MagicMock()

    wait_mock.until.side_effect = [search_button, search_button, close_button]
    monkeypatch.setattr(botdriver_module, "WebDriverWait", MagicMock(return_value=wait_mock))

    bot.click_search()

    assert search_button.click.call_count == 2
    close_button.click.assert_called_once()


def test_extract_general_info_creates_csv(bot, tmp_path):
    sample_html = BeautifulSoup(
        """
        <div class="zyxaudit-result-line">
            <div class="vc_col-md-6 vc_col-xs-12 zyxaudit-nombre_empresa">Empresa 1</div>
            <div class="vc_col-md-2 vc_col-xs-12 zyxaudit-pais">Brazil</div>
            <div class="vc_col-md-2 vc_col-xs-12 zyxaudit-anio">2023</div>
            <a href="http://example.com/report1.pdf">PDF</a>
        </div>
        <div class="zyxaudit-result-line">
            <div class="vc_col-md-6 vc_col-xs-12 zyxaudit-nombre_empresa">Empresa 2</div>
            <div class="vc_col-md-2 vc_col-xs-12 zyxaudit-pais">Argentina</div>
            <div class="vc_col-md-2 vc_col-xs-12 zyxaudit-anio">2022</div>
            <a href="http://example.com/report2.pdf">PDF</a>
        </div>
        """,
        "html.parser",
    )

    audits = sample_html.find_all("div", class_="zyxaudit-result-line")
    df, links = bot.extract_general_info(audits, csv_name="test_reports.csv")

    assert list(df["Names"]) == ["Empresa 1", "Empresa 2"]
    assert list(df["Country"]) == ["Brazil", "Argentina"]
    assert links == ["http://example.com/report1.pdf", "http://example.com/report2.pdf"]

    csv_path = tmp_path / "test_reports.csv"
    assert csv_path.exists()
    assert "Empresa 1" in csv_path.read_text()


def test_download_all_reports_streams_content(bot, tmp_path, monkeypatch):
    fake_response = MagicMock()
    fake_response.iter_content.return_value = [b"chunk1", b"", b"chunk2"]
    fake_response.raise_for_status = MagicMock()

    def fake_get(url, stream, timeout):
        assert stream is True
        assert timeout == bot.request_timeout
        return fake_response

    monkeypatch.setattr(botdriver_module.requests, "get", fake_get)
    monkeypatch.setattr(botdriver_module, "tqdm", lambda iterable, **_: iterable)

    bot.download_all_reports(["http://example.com/report1.pdf", ""])

    pdf_folder = tmp_path / "audit_reports"
    pdf_file = pdf_folder / "audit_report_rtrs1.pdf"

    assert pdf_file.exists()
    assert pdf_file.read_bytes() == b"chunk1chunk2"
    fake_response.raise_for_status.assert_called_once()


def test_download_all_reports_skips_existing(bot, tmp_path, monkeypatch):
    pdf_folder = tmp_path / "audit_reports"
    pdf_folder.mkdir()
    existing_file = pdf_folder / "audit_report_rtrs1.pdf"
    existing_file.write_bytes(b"old")

    fake_response = MagicMock()
    fake_response.iter_content.return_value = [b"new"]
    fake_response.raise_for_status = MagicMock()

    monkeypatch.setattr(botdriver_module.requests, "get", lambda *args, **kwargs: fake_response)
    monkeypatch.setattr(botdriver_module, "tqdm", lambda iterable, **_: iterable)

    bot.download_all_reports(["http://example.com/report1.pdf"])

    assert existing_file.read_bytes() == b"old"
    fake_response.raise_for_status.assert_called_once()


def test_close_quits_browser(bot):
    original_browser = MagicMock()
    bot.browser = original_browser
    bot.close()

    original_browser.quit.assert_called_once_with()
    assert bot.browser is None
