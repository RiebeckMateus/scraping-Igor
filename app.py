from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from scrapy import Selector
import scrapy
import time

class FlashScore(scrapy.Spider):
    name = 'flashscore'
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 OPR/112.0.0.0',
        'FEED_EXPORT_ENCODING': 'utf-8'
    }
    
    def __init__(self, *args, **kwargs):
        super(FlashScore, self).__init__(*args, **kwargs)
        options = webdriver.ChromeOptions()
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.link_count = 0  # Contador para os links acessados
    
    def start_requests(self):
        # Inicia a requisição para a página principal
        yield scrapy.Request('https://www.flashscore.com.br/futebol/brasil/brasileirao-betano/resultados/', callback=self.parse_with_selenium)

    def parse_with_selenium(self, response):
        # Carrega a página com Selenium
        self.driver.get(response.url)
        print("Página inicial carregada.")
        
        while True:
            try:
                mostrar_mais = WebDriverWait(self.driver, 6).until(
                    EC.presence_of_element_located((By.XPATH, '//a[@class="event__more event__more--static"]'))
                )

                self.driver.execute_script("arguments[0].scrollIntoView();", mostrar_mais)
                self.driver.execute_script("window.scrollBy(0, -200);")
                mostrar_mais.click()
                print("Botão 'event_more' clicado.")
                time.sleep(2)
            
            except Exception as e:
                print(f'Falhou ao carregar mais eventos: {e}')
                break
        
        self.page_html = self.driver.page_source
        print("HTML da página carregada.")

        # Passa o HTML para o Scrapy para ser processado
        selector = Selector(text=self.page_html)
        yield from self.parse_html(selector)  # Chama o método de parse passando o selector

    def parse_html(self, selector):
        tabela = selector.xpath('//div[@class="sportName soccer"]//div[contains(@class, "event__match")]')
        
        for i in tabela:
            link = i.xpath('.//a/@href').get()
            if link:
                # Cria o link completo se for necessário
                if link.startswith('/'):
                    link = f'https://www.flashscore.com.br{link}'
                
                # Acessa o link e extrai dados usando Selenium
                dados = self.acessa_link(link)
                
                yield dados  # Retorna os dados extraídos do link
                
                self.link_count += 1  # Incrementa o contador
                if self.link_count >= 3:  # Limita a 3 links
                    print("Limite de 3 links alcançado.")
                    break

    def acessa_link(self, link):
        # Função dedicada para acessar o link e extrair dados específicos
        self.driver.get(link)
        time.sleep(3)
        
        pagina_carregada = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located( (By.XPATH, '//div[@class="duelParticipant"]'))
        )
        
        # Atualiza o `Selector` com o HTML da nova página
        selector = Selector(text=self.driver.page_source)
        
        # Extração dos dados com Scrapy após acessar o link
        id = selector.xpath('//div[@class="duelParticipant__startTime"]//div/text()').get()
        time_casa = selector.xpath('//div[contains(@class, "duelParticipant__home")]//a[contains(@class, "participant__participantName")]/text()').get()
        time_fora = selector.xpath('//div[contains(@class, "duelParticipant__away")]//a[contains(@class, "participant__participantName")]/text()').get()
        
        ocorrencias_casa = selector.xpath('//div[contains(@class, "smv__verticalSections")]//div[contains(@class, "smv__participantRow smv__homeParticipant")]//div[@class="smv__incident"]')
        
        detalhe_ocorrencia = []
        
        for i in ocorrencias_casa:
            cartao = i.xpath('.//div[@class="smv__incidentIcon"]//svg/@class').get()
            
            detalhe_ocorrencia.append({cartao})
        
        # Retorna os dados extraídos como dicionário
        return {
            'link': link,
            'id': id,
            'time_casa': time_casa,
            'time_fora': time_fora,
            'ocorrencia': detalhe_ocorrencia
        }
        
    def closed(self, reason):
        self.driver.quit()
        print("Driver encerrado.")
