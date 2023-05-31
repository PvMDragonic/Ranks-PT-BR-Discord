from discord.ext.commands import CommandNotFound
from discord.ext import commands
import xlsxwriter
import threading
import datetime
import discord
import time
import json
import csv
import io

import nomes_scrapper
import exp_scrapper
import backend

with open("token.txt", 'r') as file:
    TOKEN = file.readline()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix = commands.when_mentioned, intents = intents)    

def loop_diario():
    NOVE = datetime.time(9)
    NOVE_MEIA = datetime.time(9, 30)

    while True:
        time.sleep(300)
        
        # Refresh de hora em hora durante DXP.
        if backend.dxp_acontecendo():
            time.sleep(3300)
            exp_scrapper.buscar_clans()

        # Calibra automaticamente pra sempre rodar logo após as 9 da manhã.
        elif NOVE <= datetime.datetime.now().time() <= NOVE_MEIA:
            exp_scrapper.buscar_clans()
            time.sleep(84000)

def loop_mensal():
    while True:
        time.sleep(84600)

        if datetime.date.today().day == 1:
            nomes_scrapper.buscar_clans()

def lista_comandos():
    embed = discord.Embed(
        title = f"LISTA DE COMANDOS",  
        color = 0x7a8ff5
    )

    embed.add_field(
        name = f'@Ranks PT-BR dxp', 
        value = f'Mostra informações sobre o DXP.', 
        inline = False
    )

    embed.add_field(name = "", value = "᲼᲼")

    embed.add_field(
        name = f'@Ranks PT-BR rank geral [data] [formato]', 
        value = f'Lista o rank geral dos clãs pt-br.\
            \n\n__Parâmetros opcionais:__\
            \n**[data] (DD MM AAAA)** — Específica uma data para o rankeamento;\
            \n**[formato] (txt/json/csv/xlsx/cru)** — Especifica o formato do arquivo.\
            \n\n__Exemplos:__\
            \n*"@Ranks PT-BR rank geral 10 04 2023"*\
            \n*"@Ranks PT-BR rank geral 10 04 2023 json"*\
            \n*"@Ranks PT-BR rank geral cru"*', 
        inline = False
    )

    embed.add_field(name = "", value = "᲼᲼")

    embed.add_field(
        name = f'@Ranks PT-BR rank mensal [datas] [formato]', 
        value = f'Lista o rank do último mês dos clãs pt-br ativos.\
            \n\n__Parâmetros opcionais:__\
            \n**[datas] (DD MM AAAA DD MM AAAA)** — Especifica um período para o rankeamento.\
            \n**[formato] (txt/json/csv/xlsx/cru)** — Especifica o formato do arquivo.\
            \n\n__Exemplos:__\
            \n*"@Ranks PT-BR rank mensal 10 04 2023 10 05 2023"*\
            \n*"@Ranks PT-BR rank mensal 10 04 2023 10 05 2023 csv"*\
            \n*"@Ranks PT-BR rank mensal xlsx"*', 
        inline = False
    )

    embed.add_field(name = "", value = "᲼᲼")

    embed.add_field(
        name = f'@Ranks PT-BR rank dxp [quantos_atrás] [formato]', 
        value = f'Lista o rank de Doubles passados dos clãs pt-br ativos.\
            \n\n__Parâmetros opcionais:__\
            \n**[quantos_atrás] (n)** — Seleciona DXP passado condigente ao número.\
            \n**[formato] (txt/json/csv/xlsx/cru)** — Especifica o formato do arquivo.\
            \n\n__Exemplos:__\
            \n*"@Ranks PT-BR rank dxp 1"*\
            \n*"@Ranks PT-BR rank dxp 1 cru"*\
            \n*"@Ranks PT-BR rank dxp txt"*', 
        inline = False
    )

    # Eis que \n não funciona no rodapé.
    embed.add_field(name = "", value = "᲼᲼")
    embed.set_footer(text = "OBS.: O formato cru dos dados limita o rankeamento ao top 50 devido ao tamanho.")

    return embed

@bot.command()
async def dxp(ctx, *args):
    inicio_dxp = backend.resgatar_data_dxp()[1]

    if backend.dxp_acontecendo():
        ranks = backend.resgatar_rank_dxp(0)

        if ranks == -3:
            embed = discord.Embed(
                title = f"EXP EM DOBRO ATIVO — {backend.dxp_restante()}", 
                description = f"__Não há dados suficientes para gerar um rank ainda.__", 
                color = 0x7a8ff5)
            embed.add_field(name = "\n", value = "Tente novamente dentro de 1 hora.", inline = False) 

            return await ctx.message.channel.send(embed = embed)           
        
        ranks = sorted(
            ranks, 
            reverse = True, 
            key = lambda x: x.exp_total
        )[0:10]

        embed = discord.Embed(
            title = f"EXP EM DOBRO ATIVO — {backend.dxp_restante()}", 
            description = f"__Top 10 clãs:__", 
            color = 0x7a8ff5
        )

        for index, clan in enumerate(ranks):
            embed.add_field(
                name = f'*{index + 1}º — {clan.clan_id.replace("+", " ")}*', 
                value = f'{clan.exp_total:,}'.replace(",","."), 
                inline = False
            )
        embed.add_field(name = "\n", value = "Para o rank completo, use **@Ranks PT-BR rank dxp**.", inline = False)

        return await ctx.message.channel.send(embed = embed)

    # Double ainda não passou.
    if inicio_dxp > datetime.datetime.now():
        embed = discord.Embed(
            title = f"O próximo EXP em Dobro se aproxima!", 
            description = f"O DXP começa em __{inicio_dxp.strftime('%d/%m/%Y')}__ às __09:00__, horário de Brasília (12:00 do jogo).", 
            color = 0x7a8ff5)
        embed.add_field(name = "", value = "Para o rank completo do último DXP, use **@Ranks PT-BR rank dxp**.", inline = False)

        return await ctx.message.channel.send(embed = embed)
    
    embed = discord.Embed(
        title = f"Nenhum EXP em Dobro ativo no momento.", 
        description = f"O próximo DXP __ainda não foi anunciado__.", 
        color = 0x7a8ff5)
    embed.add_field(name = "", value = "Para o rank completo do último DXP, use **@Ranks PT-BR rank dxp**.", inline = False)
    
    await ctx.message.channel.send(embed = embed)

@bot.command()
async def rank(ctx, *args):
    async def enviar_mensagem():
        dados = sorted(
            query, 
            reverse = True, 
            key = lambda x: x.exp_total
        )

        # txt
        if tipo == 1: 
            dados = [
                ' — '.join([
                    f'{index + 1}º', 
                    f'{clan.clan_id}'.replace("+", " "), 
                    f'{clan.exp_total:,}'.replace(",",".")
                ]) for index, clan in enumerate(dados)
            ]

            dados = '\n'.join(dados)

            await ctx.channel.send(
                content = f"{msg} {ctx.message.author.mention}", 
                file = discord.File(
                    fp = io.StringIO(dados), 
                    filename = f"{msg}.txt"
                )
            )

        # json
        if tipo == 2:
            dados = [
                [index + 1, clan.clan_id, clan.exp_total] for index, clan in enumerate(dados)
            ]

            await ctx.channel.send(
                content = f"{msg} {ctx.message.author.mention}", 
                file = discord.File(
                    fp = io.StringIO(
                        json.dumps(
                            obj = dados,
                            indent = 4
                        )
                    ), 
                    filename = f"{msg}.json"
                )
            )
        
        # csv
        if tipo == 3:
            saida = io.StringIO()
            csv_writer = csv.writer(saida)

            for clan in dados:
                csv_writer.writerow([clan.clan_id, clan.exp_total])

            saida.seek(0)

            await ctx.channel.send(
                content = f"{msg} {ctx.message.author.mention}", 
                file = discord.File(
                    filename = f"{msg}.csv",
                    fp = saida 
                )
            )
        
        # xlsx
        if tipo == 4:
            saida = io.BytesIO()
            workbook = xlsxwriter.Workbook(saida)
            worksheet1 = workbook.add_worksheet()
            worksheet1.set_column(0, 3, 20)

            for index, clan in enumerate(dados):
                worksheet1.write(f'A{index + 1}', clan.clan_id)
                worksheet1.write(f'B{index + 1}', clan.exp_total)

            workbook.close()
            saida.seek(0) 
        
            await ctx.channel.send(
                content = f"{msg} {ctx.message.author.mention}", 
                file = discord.File(
                    filename = f"{msg}.xlsx",
                    fp = saida 
                )
            )

        # cru
        if tipo == 5:
            dados = [
                ' — '.join([
                    f'{i + 1}º', 
                    f'{dados[i].clan_id}'.replace("+", " "), 
                    f'{dados[i].exp_total:,}'.replace(",",".")
                ]) for i in range(50)
            ]

            dados = '\n'.join(dados)
        
            await ctx.message.channel.send(f"{msg} {ctx.message.author.mention}\n\n{dados}")

    # 'args' vem como tupla, que é imutável.
    args = list(args)

    # Detecta se a pessoa botou o formato antes, depois ou até sem uma data.
    if "txt" in args:
        args.remove("txt")
        tipo = 1
    elif "json" in args:
        args.remove("json")
        tipo = 2
    elif "csv" in args:
        args.remove("csv")
        tipo = 3
    elif "xlsx" in args:
        args.remove("xlsx")
        tipo = 4
    elif "cru" in args:
        args.remove("cru")
        tipo = 5
    else:
        # Se colocar algum formato que não é suportado.
        if len(args) > 1:
            if not args[1].isdigit():
                args[1].pop()
            if not args[-1].isdigit():
                args[-1].pop()
        tipo = 1

    if "geral" in args:
        if 4 > len(args) > 1:
            return await ctx.message.channel.send(
                f"Use o formato `@Ranks PT-BR rank geral DD MM AAAA`. {ctx.message.author.mention}"
            )
        
        data = None
        
        if len(args) == 4:
            try:
                data = datetime.date(
                    year = int(args[3]), 
                    month = int(args[2]), 
                    day = int(args[1])
                )
            except ValueError:
                return await ctx.message.channel.send(
                    f"Use o formato `DD MM AAAA` para representar a data. {ctx.message.author.mention}"
                )
        
        query = backend.resgatar_rank_geral(data)
        if not query:
            return await ctx.message.channel.send(
                f"Não há registros do dia `{data.strftime('%d/%m/%Y')}`. {ctx.message.author.mention}"
            )
        
        msg = f"Rank Geral `{query[0].data_hora.strftime('%d/%m/%Y')}`"
        return await enviar_mensagem()
    
    if "mensal" in args:
        if 7 > len(args) > 1:
            return await ctx.message.channel.send(
                f"Use o formato `@Ranks PT-BR rank mensal DD MM AAAA DD MM AAAA`. {ctx.message.author.mention}"
            )
        
        inicio, fim = None, None
        
        if len(args) == 7:
            try:
                inicio = datetime.date(
                    year = int(args[3]), 
                    month = int(args[2]), 
                    day = int(args[1])
                )
                fim = datetime.date(
                    year = int(args[6]), 
                    month = int(args[5]), 
                    day = int(args[4])
                )
            except ValueError:
                return await ctx.message.channel.send(
                    f"Use o formato `DD MM AAAA` para representar as datas. {ctx.message.author.mention}"
                )

        query = backend.resgatar_rank_mensal(inicio, fim)

        if query == -1:
            return await ctx.message.channel.send(
                f"A data `{inicio.strftime('%d/%m/%Y')}` ainda não chegou! {ctx.message.author.mention}"
            )
        elif query == -2:
            return await ctx.message.channel.send(
                f"A data `{fim.strftime('%d/%m/%Y')}` ainda não chegou! {ctx.message.author.mention}"
            )
        elif query == -3:
            return await ctx.message.channel.send(
                f"Não há dados registrados para o período terminando em `{fim.strftime('%d/%m/%Y')}`! {ctx.message.author.mention}"
            )
        elif query == -4:
            return await ctx.message.channel.send(
                f"Não há dados registrados para o período começando em `{inicio.strftime('%d/%m/%Y')}`! {ctx.message.author.mention}"
            )

        msg = f"Rank Mensal de `{query[0].data_hora.data_passado}` até `{query[0].data_hora.data_atual}`"
        return await enviar_mensagem()
    
    if "dxp" in args:
        if len(args) > 2:
            return await ctx.message.channel.send(
                f"Use o formato `@Ranks PT-BR rank dxp N`. {ctx.message.author.mention}"
            )

        quantos_atras = 0

        if len(args) > 1:
            if args[1].isdigit():
                quantos_atras = int(args[1])
            else:
                return await ctx.message.channel.send(
                    f"Especifique um número inteiro que condiga a quantos Doubles atrás foi o DXP desejado! {ctx.message.author.mention}"
                )

        query = backend.resgatar_rank_dxp(quantos_atras)
        if query == -1:
            return await ctx.message.channel.send(
                f"Não há histórico de um DXP tão antigo assim para exibir; tente um número menor. {ctx.message.author.mention}"
            )
        elif query == -2:
            return await ctx.message.channel.send(
                f"Não há histórico de DXP para exibir; use `@Ranks PT-BR dxp` para ver informações sobre futuros Doubles. {ctx.message.author.mention}"
            )
        elif query == -3:
            return await ctx.message.channel.send(
                f"Não há dados suficientes para gerar um rank ainda; tente novamente dentro de 1 hora. {ctx.message.author.mention}"
            )
        
        msg = f"Rank DXP de `{query[0].data_hora.data_inicio}` até `{query[0].data_hora.data_fim}`"
        return await enviar_mensagem()
    
    await ctx.message.channel.send(
        f"Você precisa especificar o tipo de rank! {ctx.message.author.mention}",
        embed = lista_comandos()
    )

@bot.command()
async def criar(ctx, *args):
    if not "dxp" in args:
        raise CommandNotFound

    try:
        # o _ é pra desempacotar o 'dxp' que vem junto do comando.
        _, comeco_dia, comeco_mes, comeco_ano, fim_dia, fim_mes, fim_ano = args
    except ValueError:
        return await ctx.message.channel.send(
            f"Use o formato `@Ranks PT-BR criar dxp DD MM AAAA DD MM AAAA` para registrar um novo DXP! {ctx.message.author.mention}"
        )
    
    try:
        data_comeco = datetime.datetime(
            int(comeco_ano), 
            int(comeco_mes), 
            int(comeco_dia),
            9, 0, 0
        )

        data_fim = datetime.datetime(
            int(fim_ano), 
            int(fim_mes), 
            int(fim_dia),
            9, 0, 0
        )
    except ValueError:
        return await ctx.message.channel.send(
            f"Você não inseriu uma data correta {ctx.message.author.mention}!"
        )

    if backend.verificar_dxp(data_comeco, data_fim):
        return await ctx.message.channel.send(
            f"Já há um DXP registrado para as datas entre `{data_comeco.date()}` e `{data_fim.date()}`, {ctx.message.author.mention}!"
        )

    backend.adicionar_dxp(data_comeco, data_fim)
    await ctx.message.channel.send(
        f"Double XP para as datas entre `{data_comeco.date()}` e `{data_fim.date()}` registrado com sucesso {ctx.message.author.mention}!"
    )

    msg = f"[{datetime.datetime.now()}] DXP registrado de {data_comeco} até {data_fim} por {ctx.message.author}."
    backend.adicionar_log(msg)
    print(msg)

@bot.event
async def on_ready():
    await bot.change_presence(activity = discord.Game(name = 'Marca o bot p/ cmd'))
    print(f'>> {bot.user} on-line!')
    
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        return await ctx.message.channel.send(
            f"Você digitou um comando inválido {ctx.message.author.mention}!"
        )
    raise error

@bot.event
async def on_message(message):
    try:
        if not bot.user.mentioned_in(message):
            return

        await message.channel.typing()

        # Se alguém só marcou o bot, sem pedir algum comando.
        if message.content == "<@1071957068262674582>":
            return await message.channel.send(
                message.author.mention, 
                embed = lista_comandos()
            )
        
        await bot.process_commands(message)
    except discord.errors.Forbidden as e:
        msg = f"[{datetime.datetime.now()}] Erro de permissão em {message.guild.name}: {e}"
        backend.adicionar_log(msg)
        print(msg)

if __name__ == '__main__':
    threading.Thread(target = loop_diario).start()
    threading.Thread(target = loop_mensal).start()
    bot.run(TOKEN)