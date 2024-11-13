# scraping por campeonato
# baseado na planilha
# caso precise gerar mais links, já tem todos que você tinha pedido

import scrapy
from scrapy.selector import Selector
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd

class FlashScoreSpider(scrapy.Spider):
    name = 'flashscore'
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 OPR/112.0.0.0',
        'FEED_EXPORT_ENCODING': 'utf-8',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver = self.get_webdriver()
        self.path_file = 'Lista de Campeonatos e Temporadas por País.xlsx'
        self.file = pd.read_excel(self.path_file)

    def get_webdriver(self):
        options = webdriver.ChromeOptions()
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    def start_requests(self):
        yield scrapy.Request('https://www.flashscore.com.br/futebol/', callback=self.parse_main_page)

    def parse_main_page(self, response):
        self.driver.get(response.url)
        time.sleep(3)
        for _ in self.load_more_events(self.driver):
            pass
        time.sleep(1)
        selector = Selector(text=self.driver.page_source)
        yield from self.parse_countries(selector)

    def load_more_events(self, driver):
        items = []
        while True:
            try:
                show_more = WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.XPATH, '//span[@class="lmc__itemMore"]')))
                driver.execute_script("arguments[0].scrollIntoView();", show_more)
                driver.execute_script("window.scrollBy(0, -200);")
                show_more.click()
                time.sleep(5)
                items.append(True)  # Add a placeholder item to the list
            except Exception as e:
                print(f'Failed to load more events: {e}')
                break
        return items

    def parse_countries(self, selector):
        countries = list(self.file['País'].unique())
        table_countries = selector.xpath('//div[@class="lmc__menu"]//div[contains(@class, "lmc__block")]')

        for country_element in table_countries:
            country_name = country_element.xpath('.//span/text()').get()
            if country_name in countries:
                country_link = country_element.xpath('.//a/@href').get()
                if country_link.startswith('/'):
                    country_link = f'https://www.flashscore.com.br{country_link}'

                yield from self.parse_country(country_name, country_link)
                # yield {'coo': country_name, 'll': country_link}

    def parse_country(self, country_name, country_link):
        self.driver.get(country_link)
        time.sleep(2)
        
        # Clica no botão "mostrar mais" até que não haja mais botões
        while True:
            try:
                show_more = WebDriverWait(self.driver, 4).until(
                    EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "show-more leftMenu__item leftMenu__item--more")]'))
                )
                self.driver.execute_script("arguments[0].scrollIntoView();", show_more)
                self.driver.execute_script("window.scrollBy(0, -200);")
                show_more.click()
                time.sleep(2)
            except Exception as e:
                print(f'Não há mais botões de mostrar mais para {country_name}: {e}')
                break

        selector = Selector(text=self.driver.page_source)
        league_elements = selector.xpath('//div[@class="menu selected-country-list leftMenu leftMenu--selected"]//div[contains(@class, "leftMenu__item--width")]')

        for league_element in league_elements:
            league_name = league_element.xpath('.//a/text()').get()
            league_link = league_element.xpath('.//a/@href').get()
            if league_link and league_link.startswith('/'):
                league_link = f'https://www.flashscore.com.br{league_link}arquivo/'

            if league_name and league_link:
                yield from self.parse_league(country_name, league_name, league_link)

    # def find_league_link(self, league_name, page_source):
    #     selector = Selector(text=page_source)
    #     league_elements = selector.xpath('//div[@class="menu selected-country-list leftMenu leftMenu--selected"]//div[contains(@class, "leftMenu__item--width")]')

    #     for league_element in league_elements:
    #         candidate_league_name = league_element.xpath('.//a/text()').get()
    #         if candidate_league_name == league_name:
    #             league_link = league_element.xpath('.//a/@href').get()
    #             if league_link.startswith('/'):
    #                 league_link = f'https://www.flashscore.com.br{league_link}arquivo/'
    #             return league_link

    #     return None

    def parse_league(self, country_name, league_name, league_link):
        self.driver.get(league_link)
        time.sleep(2)
        selector = Selector(text=self.driver.page_source)
        # seasons = self.parse_seasons(selector)
        seasons_link = self.parse_seasons(selector)
        yield {'country': country_name, 'league': league_name, 'seasons': seasons_link}

    def parse_seasons(self, selector):
        season_elements = selector.xpath('//section[contains(@id, "tournament-page-archiv")]//div[contains(@class, "archive__row")]')
        seasons = [season_element.xpath('.//a/text()').get().strip() for season_element in season_elements]
        seasons_link = [season_element.xpath('.//a/@href').get() for season_element in season_elements]
        return seasons_link

    def closed(self, reason):
        self.driver.quit()
        print("Webdriver closed.")