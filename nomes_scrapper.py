from multiprocessing import Process
from threading import Thread
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

def validar_ptbr(nomes):
    MODEL = fasttext.load_model('lid.176.ftz')
    ptbr = []

    def filtrar():
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

    for nome in nomes:
        try:
            filtrar(nome)
        except Exception:
            try:
                time.sleep(10)
                filtrar(nome)
            except Exception as e:
                print(f"Erro repetido na validação do clã {nome}: {e}")

    backend.adicionar_clans(ptbr)

def encontrar_clans(lista):
    nomes = []

    for num in lista:
        url = f'https://secure.runescape.com/m=clan-hiscores/l=3/a=869/ranking?ranking=xp_total&table=0&page={num}'
        pagina = html.fromstring(requests.get(url).content)
        conteudo = pagina.xpath('.//td[@class="col2"]//a')

        for elem in conteudo:
            temp = elem.get("href")
            if 'clanName=' in temp:
                temp = temp.split("clanName=")[1]
                nomes.append(temp)

    validar_ptbr(nomes)

def processo(nomes):
    nomes = [nomes[i::THREADS] for i in range(THREADS)]

    for i in range(THREADS):
        Thread(target = encontrar_clans, args = (nomes[i], )).start()

def buscar_clans():
    pagina = html.fromstring(requests.get('https://secure.runescape.com/m=clan-hiscores/l=3/a=869/ranking').content)
    quantia_paginas = pagina.xpath('.//div[@class="paging"]')
    quantia_paginas = quantia_paginas[0].text_content().split("\n")

    # Encontra o 6413 em ['', '', '', '1', '', '2', '', '3', '', '4', '', '5', '…', '', '6413', '', '→', ''].
    quantia_paginas = int([elem for elem in quantia_paginas if elem.isdigit()][-1])

    quantia_paginas = [num for num in range(quantia_paginas)]
    quantia_paginas = [quantia_paginas[i::PROCESSOS] for i in range(PROCESSOS)]

    for i in range(PROCESSOS):
        Process(target = processo, args = (quantia_paginas[i], )).start()