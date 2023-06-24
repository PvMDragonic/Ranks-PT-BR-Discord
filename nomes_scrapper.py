from multiprocessing import Process
from threading import Thread
from datetime import datetime
from lxml import html
import fasttext
import requests
import time

import backend

# Supressa um warning inútil.
fasttext.FastText.eprint = lambda x: None

# Quantia pra definir o paralelismo dos dados.
PROCESSOS = 2
THREADS = 2

def buscar_uid(nome: str) -> str:
    pagina_clan = f'https://secure.runescape.com/m=clan-hiscores/l=3/a=869/compare.ws?clanName={nome}'
    requisicao = requests.get(pagina_clan).content
    conteudo = html.fromstring(requisicao)
    return conteudo.xpath('.//input[@name="clanId"]/@value')[0]

def verificar_clan_existe(nome: str) -> str | bool:
    try:
        pagina_clan = f'https://secure.runescape.com/m=clan-home/l=3/a=869/clan/{nome}'
        requisicao = requests.get(pagina_clan).content
        conteudo = html.fromstring(requisicao)

        if conteudo.xpath('.//h2[@id="noClanError"]'):
            return False
        
        return buscar_uid(nome)
    except requests.exceptions.RequestException:
        return False

def validar_ptbr(nomes: str) -> None:
    MODEL = fasttext.load_model('lid.176.ftz')
    ptbr = []

    for nome in nomes:
        tentativas = 3

        while True:
            try:
                pagina_clan = f'https://secure.runescape.com/m=clan-home/l=3/a=869/clan/{nome}'
                requisicao = requests.get(pagina_clan).content
                conteudo = html.fromstring(requisicao)

                sobre = " ".join(conteudo.xpath('.//p[@id="aboutOurClan"]/text()'))
                lema = " ".join(conteudo.xpath('.//p[@id="ourMotto"]/text()'))[1:-2].replace("\n", " ")

                # Verifica se é clã PT-BR
                resultado = [
                    ('__label__pt') in MODEL.predict(sobre, k = 1)[0],
                    ('__label__pt') in MODEL.predict(lema, k = 1)[0]
                ]

                if any(resultado):
                    ptbr.append(
                        [buscar_uid(nome), nome]
                    )
                    
                break
            except (requests.exceptions.RequestException, IndexError) as erro:
                tentativas -= tentativas
                if tentativas == 0:
                    msg_log = f"[{datetime.now()}] Erro na coleta do clã {nome}: {erro}"
                    backend.adicionar_log(msg_log)
                    print(msg_log)
                    break

                time.sleep(60)

    backend.adicionar_clans(ptbr)

def encontrar_clans(lista: list) -> None:
    nomes = []

    for num in lista:
        url = f'https://secure.runescape.com/m=clan-hiscores/l=3/a=869/ranking?ranking=xp_total&table=0&page={num}'
        requisicao = requests.get(url).content
        pagina = html.fromstring(requisicao)
        
        conteudo = pagina.xpath('.//td[@class="col2"]//a')

        for elem in conteudo:
            temp = elem.get("href")
            if 'clanName=' in temp:
                temp = temp.split("clanName=")[1]
                nomes.append(temp)

    validar_ptbr(nomes)

def processo(nomes: list) -> None:
    nomes = [nomes[i::THREADS] for i in range(THREADS)]

    for i in range(THREADS):
        Thread(target = encontrar_clans, args = (nomes[i], )).start()

def buscar_clans() -> None:
    pagina = html.fromstring(requests.get('https://secure.runescape.com/m=clan-hiscores/l=3/a=869/ranking').content)
    quantia_paginas = pagina.xpath('.//div[@class="paging"]')
    quantia_paginas = quantia_paginas[0].text_content().split("\n")

    # Encontra o 6413 em ['', '', '', '1', '', '2', '', '3', '', '4', '', '5', '…', '', '6413', '', '→', ''].
    quantia_paginas = int([elem for elem in quantia_paginas if elem.isdigit()][-1])

    quantia_paginas = [num for num in range(quantia_paginas)]
    quantia_paginas = [quantia_paginas[i::PROCESSOS] for i in range(PROCESSOS)]

    msg = f"[{datetime.now()}] Iniciando scrapping de clãs..."
    backend.adicionar_log(msg)
    print(msg)

    processos = [
        Process(target = processo, args = (quantia_paginas[i], )) for i in range(PROCESSOS)
    ]

    for p in processos:
       p.start()

    for p in processos:
       p.join()

    msg = f"[{datetime.now()}] Scrapping de clãs finalizado."
    backend.adicionar_log(msg)
    print(msg)