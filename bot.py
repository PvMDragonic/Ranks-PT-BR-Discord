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

@bot.command()
async def dxp(ctx, *args):
    inicio_dxp = backend.resgatar_data_dxp()[1]

    if backend.dxp_acontecendo():
        ranks = backend.resgatar_rank_dxp()

        ranks = sorted(
            ranks, 
            reverse = True, 
            key = lambda x: x.exp_total
        )[0:10]

        embed = discord.Embed(
            title = f"EXP EM DOBRO ACONTECENDO!!", 
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
        hoje = datetime.datetime.now().date()

        # Double ainda não passou.
        if inicio_dxp > hoje:
            embed = discord.Embed(
                title = f"Nenhum EXP em Dobro ativo no momento.", 
                description = f"O próximo DXP será em __{inicio_dxp}__ às __09:00:00 BSB__.", 
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
        query = backend.resgatar_rank_geral()
        dados = formatar_mensagem(query)
        msg = f"Rank Geral {query.data_hora}"
        await enviar_mensagem(dados, msg)
    elif "mensal" in args:
        query = backend.resgatar_rank_mensal()
        dados = formatar_mensagem(query)
        msg = f"Rank Mensal {query[0].data_hora.data_passado} {query[0].data_hora.data_atual}"
        await enviar_mensagem(dados, msg)
    elif "dxp" in args:
        query = backend.resgatar_rank_dxp()
        if query:
            dados = formatar_mensagem(query)
            msg = f"Rank DXP {query[0].data_hora.data_inicio} {query[0].data_hora.data_fim}"
            await enviar_mensagem(dados, msg)
        else:
            await ctx.message.channel.send(
                f"Não há histórico de DXP para exibir, {ctx.message.author.mention}. Para ver informações sobre futuros Double EXP, use `@Ranks PT-BR dxp`."
            )
    else:
        await ctx.message.channel.send(
            f"Você precisa especificar o tipo de rank, {ctx.message.author.mention}! \
                Use:\n> `rank geral`;\n> `rank mensal`;\n> `rank dxp`"
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

    msg = f"[{datetime.now()}] DXP registrado de {data_comeco} até {data_fim} por {ctx.message.author}."
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
        if message.content == "<@1071957068262674582>":
            return await message.channel.send(
                f"Segue abaixo a lista de comandos:\
                    \n> `@Ranks PT-BR dxp` — Informações sobre o Double XP;\
                    \n> `@Ranks PT-BR rank geral` — Lista com o rank de todos os clãs pt-br;\
                    \n> `@Ranks PT-BR rank mensal` — Lista com o rank do último mês de todos os clãs pt-br ativos;\
                    \n> `@Ranks PT-BR rank dxp` — Lista com o rank de Doubles passados dos clãs pt-br ativos."
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