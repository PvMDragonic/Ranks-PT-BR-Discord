from threading import Thread
from lxml import html
import requests
import datetime

import backend

class Estatisticas():
    def __init__(self, clan_id, membros, nv_fort, nv_total, exp_total, nv_cb_total) -> None:
        self.data_hora = datetime.datetime.now()
        self.clan_id = clan_id
        self.membros = membros
        self.nv_fort = nv_fort
        self.nv_total = nv_total
        self.exp_total = exp_total
        self.nv_cb_total = nv_cb_total

class Clan():
    def __init__(self, tupla) -> None:
        self.id, self.nome = tupla

def atualizar_exp(clans: list[Clan]):
    estatisticas = []

    for clan in clans:
        pagina_clan = f'https://secure.runescape.com/m=clan-hiscores/l=3/a=869/compare.ws?clanName={clan.nome}'
        conteudo = html.fromstring(requests.get(pagina_clan).content)

        # O primeiro 'OrnamentalBoxContent' é da Visão Geral, enquanto o segundo é das 'Habilidades'.
        quadro_visao_geral = conteudo.xpath('.//div[@class="OrnamentalBoxContent"]')[0]

        # Os indices em 'quadro_visao_geral[x]' são referentes a linha do quadro de Visão Geral que é lido.
        membros = [elem.replace(".", "") for elem in quadro_visao_geral[0].text_content().split("\n") if elem.replace(".", "").isnumeric()][0]
        nv_total = [elem.replace(".", "") for elem in quadro_visao_geral[1].text_content().split("\n") if elem.replace(".", "").isnumeric()][0]
        exp_total = [elem.replace(".", "") for elem in quadro_visao_geral[2].text_content().split("\n") if elem.replace(".", "").isnumeric()][0]
        nv_cb_total = [elem.replace(".", "") for elem in quadro_visao_geral[3].text_content().split("\n") if elem.replace(".", "").isnumeric()][0]
        nv_fort = [elem.replace(".", "") for elem in quadro_visao_geral[11].text_content().split("\n") if elem.replace(".", "").isnumeric()][0]

        estatisticas.append(
            Estatisticas(
                clan.id,
                membros,
                nv_fort,
                nv_total,
                exp_total,
                nv_cb_total
            )
        )

    backend.adicionar_estatisticas(estatisticas)

def buscar_clans():
    PARTES = 3

    clans = backend.resgatar_clans()
    clans = [Clan(clan) for clan in clans]
    clans = [clans[i::PARTES] for i in range(PARTES)]

    for i in range(PARTES):
       Thread(target = atualizar_exp, args = (clans[i], )).start()