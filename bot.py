from discord.ext.commands import CommandNotFound
from discord.ext import commands
import threading
import datetime
import discord
import time
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
        name = f'@Ranks PT-BR rank geral [data]', 
        value = f'Lista o rank geral dos clãs pt-br.\n\nParâmetros opcionais:\n   [data] (YYYY MM DD) — Seleciona DXP anterior.\n*"@Ranks PT-BR rank geral 2023 04 10"*', 
        inline = False
    )

    embed.add_field(name = "", value = "᲼᲼")

    embed.add_field(
        name = f'@Ranks PT-BR rank mensal [datas]', 
        value = f'Lista o rank do último mês dos clãs pt-br ativos.\n\nParâmetros opcionais:\n   [datas] (YYYY MM DD YYYY MM DD) — Seleciona período específico.\n*"@Ranks PT-BR rank mensal 2023 04 10 2023 05 10"*', 
        inline = False
    )

    embed.add_field(name = "", value = "᲼᲼")

    embed.add_field(
        name = f'@Ranks PT-BR rank dxp [número]', 
        value = f'Lista o rank de Doubles passados dos clãs pt-br ativos.\n\nParâmetros opcionais:\n   [número] (n) — Seleciona DXP passado condigente ao número.\n*"@Ranks PT-BR rank dxp 1"*', 
        inline = False
    )

    return embed

@bot.command()
async def dxp(ctx, *args):
    inicio_dxp = backend.resgatar_data_dxp()[1]

    if backend.dxp_acontecendo():
        ranks = backend.resgatar_rank_dxp(0)

        ranks = sorted(
            ranks, 
            reverse = True, 
            key = lambda x: x.exp_total
        )[0:10]

        embed = discord.Embed(
            title = f"EXP EM DOBRO ATIVO — {backend.dxp_restante()}", 
            description = f"__Top 10 clãs:__", 
            color = 0x7a8ff5)
        for index, clan in enumerate(ranks):
            embed.add_field(
                name = f'*{index + 1}º — {clan.clan_id.replace("+", " ")}*', 
                value = f'{clan.exp_total:,}'.replace(",","."), 
                inline = False
            )
        embed.add_field(name = "\n", value = "Para o rank completo, use **@Ranks PT-BR rank dxp**.", inline = False)
    
        await ctx.message.channel.send(embed = embed)
    else:
        hoje = datetime.datetime.now()

        # Double ainda não passou.
        if inicio_dxp > hoje:
            embed = discord.Embed(
                title = f"O próximo EXP em Dobro se aproxima!", 
                description = f"O DXP começa em __{inicio_dxp.strftime('%d/%m/%Y')}__ às __09:00__, horário de Brasília (12:00 do jogo).", 
                color = 0x7a8ff5)
            embed.add_field(name = "", value = "Para o rank completo do último DXP, use **@Ranks PT-BR rank dxp**.", inline = False)

            await ctx.message.channel.send(embed = embed)
        else:
            embed = discord.Embed(
                title = f"Nenhum EXP em Dobro ativo no momento.", 
                description = f"O próximo DXP __ainda não foi anunciado__.", 
                color = 0x7a8ff5)
            embed.add_field(name = "", value = "Para o rank completo do último DXP, use **@Ranks PT-BR rank dxp**.", inline = False)
            
            await ctx.message.channel.send(embed = embed)

@bot.command()
async def rank(ctx, *args):
    def formatar_mensagem(dados):
        dados = sorted(
            dados, 
            reverse = True, 
            key = lambda x: x.exp_total
        )

        dados = [
            ' — '.join([
                f'{index + 1}º', 
                f'{clan.clan_id}'.replace("+", " "), 
                f'{clan.exp_total:,}'.replace(",",".")
            ]) for index, clan in enumerate(dados)
        ]

        return '\n'.join(dados)

    async def enviar_mensagem(dados, mensagem):
        await ctx.channel.send(
            content = f"{msg} {ctx.message.author.mention}", 
            file = discord.File(fp = io.StringIO(dados), 
            filename = f"{msg}.txt")
        )

    if "geral" in args:
        def selecionar_data() -> list:
            if 4 > len(args) > 1:
                return f"Use o formato `@Ranks PT-BR rank geral YYYY MM DD`. {ctx.message.author.mention}"
            
            if len(args) == 4:
                # Precisa converter os args pra int, porque eles vem em str.
                try:
                    return datetime.date(
                        year = int(args[1]), 
                        month = int(args[2]), 
                        day = int(args[3])
                    )
                except ValueError:
                    return f"Use o formato `YYYY MM DD` para representar a data. {ctx.message.author.mention}"

            # Não tinha data; assume mais recente.
            return None

        data = selecionar_data()
        if type(data) == str:
            return await ctx.message.channel.send(data)
        
        query = backend.resgatar_rank_geral(data)
        if not query:
            return await ctx.message.channel.send(
                f"Não há registros do dia `{data.strftime('%d/%m/%Y')}`. {ctx.message.author.mention}"
            )
        
        dados = formatar_mensagem(query)
        msg = f"Rank Geral `{query[0].data_hora.strftime('%d/%m/%Y')}`"
        return await enviar_mensagem(dados, msg)
    
    if "mensal" in args:
        def selecionar_datas() -> list:
            if 7 > len(args) > 1:
                return f"Use o formato `@Ranks PT-BR rank mensal YYYY MM DD YYYY MM DD`. {ctx.message.author.mention}"
            
            if len(args) == 7:
                # Precisa converter os args pra int, porque eles vem em str.
                try:
                    inicio = datetime.date(
                        year = int(args[1]), 
                        month = int(args[2]), 
                        day = int(args[3])
                    )
                    fim = datetime.date(
                        year = int(args[4]), 
                        month = int(args[5]), 
                        day = int(args[6])
                    )
                except ValueError:
                    return f"Use o formato `YYYY MM DD` para representar as datas. {ctx.message.author.mention}"
                
                return [inicio, fim]

            # Não tinha data; assume mais recente.
            return [None, None]

        datas = selecionar_datas()
        if type(datas) == str:
            return await ctx.message.channel.send(datas)

        query = backend.resgatar_rank_mensal(datas[0], datas[1])

        if query == -1:
            return await ctx.message.channel.send(
                f"A data `{datas[0].strftime('%d/%m/%Y')}` ainda não chegou! {ctx.message.author.mention}"
            )
        elif query == -2:
            return await ctx.message.channel.send(
                f"A data `{datas[1].strftime('%d/%m/%Y')}` ainda não chegou! {ctx.message.author.mention}"
            )
        elif query == -3:
            return await ctx.message.channel.send(
                f"Não há dados registrados para o período terminando em `{datas[1].strftime('%d/%m/%Y')}`! {ctx.message.author.mention}"
            )
        elif query == -4:
            return await ctx.message.channel.send(
                f"Não há dados registrados para o período começando em `{datas[0].strftime('%d/%m/%Y')}`! {ctx.message.author.mention}"
            )

        dados = formatar_mensagem(query)
        msg = f"Rank Mensal de `{query[0].data_hora.data_passado}` até `{query[0].data_hora.data_atual}`"
        return await enviar_mensagem(dados, msg)
    
    if "dxp" in args:
        def selecionar_quantia() -> int:
            if len(args) != 2:
                return 0
            
            try:
                return int(args[1])
            except ValueError:
                return f"Especifique um número inteiro que condiga com quantos Doubles atrás foi o DXP desejado! {ctx.message.author.mention}"

        quantos_atras = selecionar_quantia()
        if type(quantos_atras) == str:
            return await ctx.message.channel.send(quantos_atras)

        query = backend.resgatar_rank_dxp(quantos_atras)

        if query == -1:
            return await ctx.message.channel.send(
                f"Não há histórico de um DXP tão antigo assim para exibir; tente um número menor. {ctx.message.author.mention}"
            )
        elif query == -2:
            return await ctx.message.channel.send(
                f"Não há histórico de DXP para exibir; use `@Ranks PT-BR dxp` para ver informações sobre futuros Doubles. {ctx.message.author.mention}"
            )
        
        dados = formatar_mensagem(query)
        msg = f"Rank DXP de `{query[0].data_hora.data_inicio}` até `{query[0].data_hora.data_fim}`"
        return await enviar_mensagem(dados, msg)
    
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
        _, comeco_ano, comeco_mes, comeco_dia, fim_ano, fim_mes, fim_dia = args
    except ValueError:
        return await ctx.message.channel.send(
            f"Use o formato `@Ranks PT-BR criar dxp YYYY MM DD YYYY MM DD` para registrar um novo DXP! {ctx.message.author.mention}"
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