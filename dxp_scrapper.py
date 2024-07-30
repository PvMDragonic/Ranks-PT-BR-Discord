import mwparserfromhell
import requests
import datetime
import re

def _buscar_wikitext(page_title):
    url = 'https://runescape.wiki/api.php'
    params = {
        'action': 'query',
        'titles': page_title,
        'prop': 'revisions',
        'rvprop': 'content',
        'format': 'json'
    }
    response = requests.get(url, params = params)
    data = response.json()
    pages = data['query']['pages']
    page = next(iter(pages.values()))
    return page['revisions'][0]['*'] 

def procurar_double():
    wikitext = _buscar_wikitext("Double XP")
    wikicode = mwparserfromhell.parse(wikitext)
    regex_datas = r'\[\[(\d{1,2} \w+)\]\] \[\[(\d{4})\]\]'
    hoje = datetime.datetime.now().date()

    dxp = [
        section for section in wikicode.get_sections() 
        for heading in section.filter_headings() 
        if '==Events==' in heading
    ][0].split('|-')

    datas = []
    for entrada in dxp:
        if len(datas) >= 2:
            break

        if not entrada.startswith('\n|'):
            continue

        matches = re.findall(regex_datas, entrada)

        datas_encontradas = [
            datetime.datetime.strptime(f"{day} {year} 09:00", "%d %B %Y %H:%M") for day, year in matches
        ]

        for data in datas_encontradas:
            if data.date() > hoje:
                datas.append(data)

    return datas