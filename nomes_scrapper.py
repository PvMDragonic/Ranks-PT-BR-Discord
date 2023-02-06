from multiprocessing import Process
from threading import Thread
from lxml import html
import fasttext
import requests

import backend

# Supressa um warning inútil.
fasttext.FastText.eprint = lambda x: None

# Quantia pra dividir as listas nos processos e threads.
PARTES = 4

def validar_ptbr(nomes):
    MODEL = fasttext.load_model('lid.176.ftz')
    ptbr = []

    for nome in nomes:
        try:
            pagina_clan = f'https://secure.runescape.com/m=clan-home/l=3/a=869/clan/{nome}'
            conteudo = html.fromstring(requests.get(pagina_clan).content)
            sobre = " ".join(conteudo.xpath('.//p[@id="aboutOurClan"]/text()'))
            lema = " ".join(conteudo.xpath('.//p[@id="ourMotto"]/text()'))[1:-2].replace("\n", " ")

            # Verifica se é clã PT-BR
            resultado = [
                ('__label__pt') in MODEL.predict(sobre, k = 1)[0],
                ('__label__pt') in MODEL.predict(lema, k = 1)[0]
            ]

            if any(resultado):
                ptbr.append(nome)
        except Exception as e:
            print(f"Erro durante validação de clãs: {e}")

    backend.adicionar_clans(ptbr)

def encontrar_clans(lista):
    nomes = []

    for num in lista:
        pagina = html.fromstring(requests.get(f'https://secure.runescape.com/m=clan-hiscores/l=3/a=869/ranking?ranking=xp_total&table=0&page={num}').content)
        conteudo = pagina.xpath('.//div[@class="tableWrap"]//a')

        for elem in conteudo:
            temp = elem.get("href")
            if 'clanName=' in temp:
                temp = temp.split("clanName=")[1]
                if temp not in nomes:
                    nomes.append(temp)
    
    validar_ptbr(nomes)

def processo(nomes):
    nomes = [nomes[i::PARTES] for i in range(PARTES)]

    for i in range(PARTES):
        Thread(target = encontrar_clans, args = (nomes[i], )).start()

def quantia_clans() -> list:
    pagina = html.fromstring(requests.get('https://secure.runescape.com/m=clan-hiscores/l=3/a=869/ranking').content)
    quantia_paginas = pagina.xpath('.//div[@class="paging"]')
    quantia_paginas = quantia_paginas[0].text_content().split("\n")

    # Encontra o 6413 em ['', '', '', '1', '', '2', '', '3', '', '4', '', '5', '…', '', '6413', '', '→', ''].
    quantia_paginas = int([elem for elem in quantia_paginas if elem.isdigit()][-1])

    divisao_nomes = [num for num in range(quantia_paginas)]
    divisao_nomes = [divisao_nomes[i::PARTES] for i in range(PARTES)]
    return divisao_nomes

def buscar_clans():
    numero_clans = quantia_clans()

    for i in range(PARTES):
        Process(target = processo, args = (numero_clans[i], )).start()