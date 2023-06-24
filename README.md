# Ranks-PT-BR-Discord
O Ranks PT-BR (Discord) é um bot de Discord feito com Python e Postgres para catalogar a performance ao longo do tempo dos clãs que usam a língua portuguesa. 

## Funcionamento
Os dados de todos os clãs são extraídos do código-fonte do site oficial do RuneScape e filtrados por um modelo de machine learning que prediz se o lema e/ou a descrição de cada um dos clãs está ou não em Português. Após determinar quais clãs são e não são luso-brasileiros, é feita a coleta de dados relevantes diretamente da página de cada clã, ainda no site oficial do jogo.

## Requisitos
Para fazer o Ranks PT-BR (Discord) funcionar, os seguintes requisitos são necessários:
- **Back-end**
    - PostgreSQL 14.4 (ou superior);
    - Python 3.10 (ou superior);
        - [discord.py](https://pypi.org/project/discord.py/) — Wrapper da API do Discord para Python;
        - [fasttext](https://pypi.org/project/fasttext/) — Wrapper da API feita pelo Facebook para reconhecimento de linguas;
        - [psycopg2](https://pypi.org/project/psycopg/) — Adaptador Postgres para linguagem Python;
        - [XlsxWriter](https://pypi.org/project/XlsxWriter/) — Módulo para escrita de arquivos no formato XLSX Excel 2007;
        - [requests](https://pypi.org/project/requests/) — Biblioteca para requisições HTTP. 
        - [lxml](https://pypi.org/project/lxml/) — Biblioteca para processamento de XML;
- **Front-end**
    - [Aplicação Discord](https://discord.com/developers/applications) — Uma aplicação de Discord que seja um bot. 
        - O token do bot deve ser colocado em um arquivo chamado `token.txt` no mesmo diretório, junto dos demais arquivos da aplicação.

___
Versão descontinuada para desktop: [Ranks PT-BR](https://github.com/PvMDragonic/Ranks-PT-BR)     
