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

        # Calibra automaticamente pra sempre rodar logo após as 9 da manhã.
        if NOVE <= datetime.datetime.now().time() <= NOVE_MEIA:
            exp_scrapper.buscar_clans()
            time.sleep(84000)

def loop_mensal():
    while True:
        time.sleep(84600)

        if datetime.date.today().day == 1:
            nomes_scrapper.buscar_clans()

@bot.command()
async def dxp(ctx, *args):
    return await ctx.message.channel.send(
        f"O último DXP foi em: `{backend.resgatar_ultimo_dxp()}` {ctx.message.author.mention}."
    )

@bot.command()
async def rank(ctx, *args):
    if "geral" in args:
        dados = backend.resgatar_rank_geral()
        dados = sorted(dados, reverse = True, key = lambda x: x.exp_total)
        dados = [' — '.join([
                f'{index + 1}º', 
                f'{clan.clan_id}'.replace("+", " "), 
                f'{clan.exp_total:,}'.replace(",",".")
            ]) for index, clan in enumerate(dados)]
        txt = '\n'.join(dados)

        await ctx.channel.send(
            content = "Rank Geral", file = discord.File(fp = io.StringIO(txt), filename = "Rank Geral.txt")
        )
    '''elif "mensal" in args:

    elif "dxp" in args:

    else:
        await ctx.message.channel.send(
            f"Você precisa especificar o tipo de rank, {ctx.message.author.mention}! Use:\n> `rank geral`;\n> `rank mensal`;\n> `rank dxp`"
        )'''

@bot.command()
async def criar(ctx, *args):
    if not "dxp" in args:
        raise CommandNotFound

    try:
        # o _ é pra desempacotar o 'dxp' que vem junto do comando.
        _, comeco_ano, comeco_mes, comeco_dia, fim_ano, fim_mes, fim_dia = args
    except ValueError:
        return await ctx.message.channel.send(
            f"Você não especificou todos os valores necessários para estabelecer a(s) data(s)! Use o formato `YYYY-MM-DD` {ctx.message.author.mention}."
        )
    
    try:
        data_comeco = datetime.date(
            int(comeco_ano), 
            int(comeco_mes), 
            int(comeco_dia)
        )
        data_fim = datetime.date(
            int(fim_ano), 
            int(fim_mes), 
            int(fim_dia)
        )
    except ValueError:
        return await ctx.message.channel.send(
            f"Você não inseriu uma data correta {ctx.message.author.mention}!"
        )

    if backend.verificar_dxp(data_comeco, data_fim):
        return await ctx.message.channel.send(
            f"Já há um DXP registrado cujas datas coincidem com o período entre `{data_comeco}` e `{data_fim}`, {ctx.message.author.mention}!"
        )

    backend.adicionar_dxp(data_comeco, data_fim)
    await ctx.message.channel.send(
        f"Double XP para as datas entre `{data_comeco}` e `{data_fim}` registrado com sucesso {ctx.message.author.mention}!"
    )

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
    if message.content == "<@1071957068262674582>":
        return await message.channel.send(
            f"Segue abaixo a lista de comandos:\
                \n> `@Ranks PT-BR dxp` — Informações sobre o Double XP;\
                \n> `@Ranks PT-BR rank geral` — Lista com o rank de todos os clãs pt-br;\
                \n> `@Ranks PT-BR rank mensal` — Lista com o rank do último mês de todos os clãs pt-br ativos;\
                \n> `@Ranks PT-BR rank dxp` — Lista com o rank de Doubles passados dos clãs pt-br ativos."
        )
     
    await bot.process_commands(message)

if __name__ == '__main__':
    threading.Thread(target = loop_diario).start()
    threading.Thread(target = loop_mensal).start()
    bot.run(TOKEN)