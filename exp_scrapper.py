from datetime import datetime
from threading import Thread
from lxml import html
import requests
import time

import backend

def atualizar_exp(clans: list[backend.Clan]):
    estatisticas = []

    for clan in clans:
        tentativas = 3

        while True:
            try:
                pagina_clan = f'https://secure.runescape.com/m=clan-hiscores/l=3/a=869/compare.ws?clanName={clan.nome}'
                requisicao = requests.get(pagina_clan).content
                conteudo = html.fromstring(requisicao)

                # O primeiro 'OrnamentalBoxContent' é da Visão Geral, enquanto o segundo é das 'Habilidades'.
                quadro_visao_geral = conteudo.xpath('.//div[@class="OrnamentalBoxContent"]')[0]

                # Os indices em 'quadro_visao_geral[x]' são referentes a linha do quadro de Visão Geral que é lido.
                membros = [elem.replace(".", "") for elem in quadro_visao_geral[0].text_content().split("\n") if elem.replace(".", "").isnumeric()][0]
                nv_total = [elem.replace(".", "") for elem in quadro_visao_geral[1].text_content().split("\n") if elem.replace(".", "").isnumeric()][0]
                exp_total = [elem.replace(".", "") for elem in quadro_visao_geral[2].text_content().split("\n") if elem.replace(".", "").isnumeric()][0]
                nv_cb_total = [elem.replace(".", "") for elem in quadro_visao_geral[3].text_content().split("\n") if elem.replace(".", "").isnumeric()][0]
                nv_fort = [elem.replace(".", "") for elem in quadro_visao_geral[11].text_content().split("\n") if elem.replace(".", "").isnumeric()][0]

                estatisticas.append(
                    backend.Estatisticas(
                        clan.id,
                        datetime.now(),
                        membros,
                        nv_fort,
                        nv_total,
                        nv_cb_total,
                        exp_total
                    )
                )

                break
            except (requests.exceptions.RequestException, IndexError) as erro:
                tentativas -= tentativas
                if tentativas == 0:
                    msg_log = f"[{datetime.now()}] Erro na coleta de XP de {clan.nome}: {erro}"
                    backend.adicionar_log(msg_log)
                    print(msg_log)
                    break

                time.sleep(60)

    backend.adicionar_estatisticas(estatisticas)

def buscar_clans():
    PARTES = 3

    clans = backend.resgatar_clans()
    clans = [clans[i::PARTES] for i in range(PARTES)]

    msg = f"[{datetime.now()}] Iniciando scrapping de EXP..."
    backend.adicionar_log(msg)
    print(msg)

    threads = [
        Thread(target = atualizar_exp, args = (clans[i], )) for i in range(PARTES)
    ]
    
    for t in threads:
        t.start()

    for t in threads:
        t.join()

    msg = f"[{datetime.now()}] Scrapping de EXP finalizado."
    backend.adicionar_log(msg)
    print(msg)