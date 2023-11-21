<p align="center">
    <img 
        style="border-radius: 10px"
        src="https://cdn.discordapp.com/avatars/1071957068262674582/ec3cd4297f503a8875f1164875e36e07?size=128"
        alt="Ícone"
    />
</p>
<h1 align="center">Ranks PT-BR Discord</h1>
<p align="center">
    O Ranks PT-BR (Discord) é um bot de Discord feito com Python e PostgreSQL<br>para catalogar a performance ao longo do tempo dos clãs que usam a língua portuguesa. 
</p>
<br>

## Funcionamento
Os dados de todos os clãs são extraídos do site oficial do RuneScape e filtrados por um modelo de aprendizado estatístico que prediz se o lema e/ou a descrição de cada um dos clãs está ou não em Português. Após determinar quais clãs são e não são luso-brasileiros, é feita a coleta de dados relevantes diretamente da página de cada clã, ainda no site oficial do jogo.

### Comandos
Basta marcar o bot (sem dizer mais nada) para receber a lista de comandos.

| Comando | Descrição | Exemplo |
| -------- | -------- | -------- |
| rank geral | Lista o ranking geral dos clãs pt-br. | @Ranks PT-BR rank geral |
| rank mensal | Lista o ranking do último mês dos clãs pt-br ativos. | @Ranks PT-BR rank mensal |
| rank dxp | Lista o ranking de Doubles dos clãs pt-br ativos. | @Ranks PT-BR rank dxp |
| dxp | Mostra informações sobre o DXP. | @Ranks PT-BR dxp |
<br>

Todos os comandos possuem parâmetros adicionais, permitindo ver dados de momentos específicos ou em outros formatos de arquivo além de txt. A lista completa pode ser encontrada na lista de comandos do bot.

| Comando | Parâmetro | Formato | Exemplo | Resultado
| -------- | -------- | -------- | -------- | -------- |
| rank geral | data | MM DD AAAA | @Ranks PT-BR rank geral 10 05 2023 | Lista ranking geral da data 10/05/2023.
| rank dxp | quantos atrás | n | @Ranks PT-BR dxp 2 | Lista o resultado de dois Doubles atrás.
<br>

Ainda, há comandos especiais para aqueles usuários marcados como moderadores que permitem controlar algumas funções mais delicadas do bot.

| Comando | Descrição | Exemplo |
| -------- | -------- | -------- |
| criar dxp | Registra um novo DXP. | @Ranks PT-BR criar dxp 10 11 2023 20 11 2023 |
| deletar dxp | Deleta o DXP registrado mais recente. | @Ranks PT-BR deletar dxp |
| adicionar clan  | Adiciona um clã ao banco de dados do bot. | @Ranks PT-BR rank dxp |
| remover clan | Remove um clã do banco de dados do bot. | @Ranks PT-BR dxp |

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