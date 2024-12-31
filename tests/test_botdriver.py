import pytest
import os
from unittest.mock import patch, MagicMock
from pathlib import Path
from scripts.data_scrapping.botdriver import BotDriver 

@pytest.fixture
def bot():
    """
    Cria uma instância do BotDriver em modo headless 
    para ser usada nos testes. 
    """
    return BotDriver("--headless") 

def test_botdriver_instantiation(bot):
    """
    Testa se o BotDriver é instanciado corretamente.
    """
    assert bot is not None
    assert bot.browser is not None
    assert isinstance(bot.root_folder, Path)

def test_get_country_list(bot):
    """
    Testa se get_country_list() retorna algo plausível.
    (Aqui, rodamos de verdade, então pode abrir o navegador e acessar a página.)
    Se você quiser evitar abrir o navegador, use mock. 
    """
    bot.browser.get("https://responsiblesoy.org/public-audit-reports?lang=en")
    countries = bot.get_country_list()
    assert isinstance(countries, list)
    assert len(countries) > 0
    print("Países encontrados:", countries)
    # Verifica se "Brazil" está na lista (pode mudar se a página mudar)
    assert "Brazil" in countries

def test_select_country(bot):
    """
    Testa se select_country("Brazil") não gera erro.
    """
    bot.browser.get("https://responsiblesoy.org/public-audit-reports?lang=en")
    countries = bot.get_country_list()
    if "Brazil" in countries:
        bot.select_country("Brazil")
        # Se chegar aqui sem dar exceção, consideramos OK
        assert True
    else:
        pytest.skip("País 'Brazil' não está na lista neste momento.")

def test_click_search(bot):
    """
    Testa se click_search() funciona (inclusive fechando pop-up).
    """
    bot.browser.get("https://responsiblesoy.org/public-audit-reports?lang=en")
    bot.get_country_list()  # garante que a página carregue
    bot.select_country("Brazil")
    try:
        bot.click_search()
        assert True
    except Exception as e:
        pytest.fail(f"Erro ao clicar em Search: {e}")

def test_extract_and_download(bot):
    """
    Faz um teste de fluxo completo:
    1) Acessa página
    2) Seleciona 'Brazil'
    3) Clica em Search
    4) Coleta <div class='zyxaudit-result-line'>
    5) Extrai info e faz download (mas usando mock pra requests.get, p/ não baixar de fato)
    """
    import time
    from bs4 import BeautifulSoup

    # 1) Acessa e configura
    bot.browser.get("https://responsiblesoy.org/public-audit-reports?lang=en")
    bot.get_country_list()
    bot.select_country("Brazil")
    bot.click_search()
    time.sleep(2)

    # 2) Pega o HTML
    html = BeautifulSoup(bot.browser.page_source, "html.parser")
    audits_r_list = html.find_all("div", class_="zyxaudit-result-line")

    # 3) Se não há relatórios, não há o que fazer
    if not audits_r_list:
        pytest.skip("Nenhum relatório encontrado na página no momento.")
    
    # 4) Mockar requests.get para não baixar PDFs de verdade
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"%PDF-1.4\nFake PDF Content"

        df, links = bot.extract_general_info(audits_r_list)
        assert not df.empty
        assert len(links) == len(df)

        bot.download_all_reports(links)
        # Verifica se chamou requests.get ao menos uma vez
        assert mock_get.called

def test_cleanup(bot):
    """
    Fecha o browser no fim.
    """
    bot.browser.quit()
    assert True
