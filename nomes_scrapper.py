from lxml import html
import fasttext
import requests

# Supressa um warning inútil.
fasttext.FastText.eprint = lambda x: None

def validar_ptbr(nomes):
    MODEL = fasttext.load_model('lid.176.ftz')
    ptbr = []

    for nome in nomes:
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

def encontrar_clans(lista: list):
    nomes = []

    for num in range(lista):
        pagina = html.fromstring(requests.get(f'https://secure.runescape.com/m=clan-hiscores/l=3/a=869/ranking?ranking=xp_total&table=0&page={num}').content)
        conteudo = pagina.xpath('.//div[@class="tableWrap"]//a')

        for elem in conteudo:
            temp = elem.get("href")
            if 'clanName=' in temp:
                temp = temp.split("clanName=")[1]
                if temp not in nomes:
                    nomes.append(temp)
    
    validar_ptbr(nomes)

def buscar_clans():
    pagina = html.fromstring(requests.get('https://secure.runescape.com/m=clan-hiscores/l=3/a=869/ranking').content)
    quantia_paginas = pagina.xpath('.//div[@class="paging"]')
    quantia_paginas = quantia_paginas[0].text_content().split("\n")
    quantia_paginas = int([elem for elem in quantia_paginas if elem.isdigit()][-1])

    encontrar_clans(quantia_paginas)

buscar_clans()