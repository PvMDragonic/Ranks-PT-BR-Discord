from datetime import timedelta, datetime, date, time
from discord.ext.commands import CommandNotFound
from discord.ext import commands
from time import sleep
import xlsxwriter
import threading
import discord
import asyncio
import json
import csv
import io

from backend import ClanController
from backend import AdminController
from backend import LogController
import nomes_scrapper
import exp_scrapper
import dxp_scrapper

with open("token.txt", 'r') as file:
    TOKEN = file.readline()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix = commands.when_mentioned, intents = intents)    

def loop_diario():
    def tempo_para_nove_horas(prox_dia = True):
        agr = datetime.now()
        nove_horas = agr.replace(hour = 9, minute = 5)
        
        if prox_dia:
            nove_horas = nove_horas + timedelta(days = 1)
        
        diferenca = nove_horas - agr
        return diferenca.total_seconds()

    async def msg_padrao():
        await bot.change_presence(activity = discord.Game(name = 'Marca o bot p/ cmd'))

    async def coletar_xp():
        await bot.change_presence(activity = discord.Game(name = 'Coletando EXP...'))
        exp_scrapper.buscar_clans()
        await msg_padrao()

    async def asincrono():
        while True:
            if date.today().day == 1 or len(ClanController.resgatar_clans()) == 0:
                # Espera o bot iniciar (para não dar erro ao tentar mudar a presença).
                sleep(30)

                await bot.change_presence(activity = discord.Game(name = 'Buscando clãs...'))
                nomes_scrapper.buscar_clans()
                await msg_padrao()

            if ClanController.dxp_acontecendo():
                # Evita erro, porque esse thread começa a ser executado antes do bot ficar online.
                sleep(30) 

                agora = datetime.now()
                await coletar_xp()
                
                # Dorme por 1h menos o tempo que levou para o scrap.
                sleep(3600 - (datetime.now().timestamp() - agora.timestamp()))

                # Se faltar menos de 1h, ele segue e vai esperar pelas 9:05 da manhã.
                if not ClanController.dxp_fim_eminente():                
                    continue
            
            agora = datetime.now() 

            # Bot foi iniciado antes das nove da manhã.
            if agora.time() <= time(9, 5):
                await msg_padrao()
                sleep(tempo_para_nove_horas(prox_dia = False))
                continue

            try:
                ultima_coleta_registrada = ClanController.resgatar_rank_geral()[0][2].date()
                dxp_recem_acabou = agora.date() == ClanController.resgatar_data_dxp()[2].date()
                
                if (agora.date() > ultima_coleta_registrada) or (dxp_recem_acabou and agora.time() <= time(10, 0)):
                    await coletar_xp()
            except TypeError:
                # Não há dados no BD para ter 'ultima_coleta_registrada' ou 'dxp_recem_acabou'.
                await coletar_xp() 

            try:
                data_comeco, data_fim = dxp_scrapper.procurar_double()
                if not ClanController.verificar_dxp(data_comeco, data_fim):
                    if AdminController.adicionar_dxp(data_comeco, data_fim):
                        LogController.adicionar_log(
                            f"[{datetime.now()}] registro automático de novo DXP para \
                            {data_comeco.strftime('%d/%m/%Y')} até \
                            {data_fim.strftime('%d/%m/%Y')}."
                        )
            except ValueError:
                pass # Nenhum DXP encontrado; jogo que segue.
            
            sleep(tempo_para_nove_horas())

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(asincrono())

async def lista_comandos(message):
    if AdminController.possui_nv_acesso(1, int(message.author.id)):
        embed = discord.Embed(
            title = "COMANDOS DA MODERAÇÃO",
            description = "Comandos para quem faz parte da Equipe de Moderação.\n\n᲼᲼",
            color = 0x7a8ff5
        )

        comandos = [
            ("@Ranks PT-BR criar dxp [DD MM AAAA] [DD MM AAAA]", "Registra um novo DXP entre [data início] e [data fim].\n᲼᲼"),
            ("@Ranks PT-BR deletar dxp", "Deleta o DXP que foi registrado por último.\n᲼᲼"),
            ("@Ranks PT-BR adicionar clan [nome]", "Adiciona um clã ao banco de dados do bot.\n᲼᲼"),
            ("@Ranks PT-BR remover clan [nome]", "Remove um clã do banco de dados do bot.\n᲼᲼"),
        ]

        for cmd, descricao in comandos:
            embed.add_field(name = cmd, value = descricao, inline = False)

        embed.set_footer(text = "OBS.: O uso desses comandos é registrado no log, com o nome de quem usou.")

        await message.author.send(embed = embed)

    with open('lista_comandos.json', 'r', encoding = 'utf-8') as json_file:
        comandos = json.load(json_file)

    for comando in comandos:
        embed = discord.Embed(
            title = comando['title'],
            description = comando['description'],
            color = 0x7a8ff5
        )

        for field in comando['fields']:
            embed.add_field(
                name = field['name'], 
                value = field['value'], 
                inline = field['inline']
            )
        
        if comando['footer']:
            embed.set_footer(text = comando['footer'])

        await message.channel.send(embed = embed)
        sleep(0.25)

@bot.command()
async def dxp(ctx):
    if ClanController.dxp_acontecendo():
        ranks = ClanController.resgatar_rank_dxp(0)
        dxp_restante = ClanController.dxp_restante()

        if ranks == -3:
            embed = discord.Embed(
                title = f"EXP EM DOBRO ATIVO — {dxp_restante}", 
                description = f"__Não há dados suficientes para gerar um rank ainda.__", 
                color = 0x7a8ff5)
            embed.add_field(name = "\n", value = "Tente novamente dentro de 1 hora.", inline = False) 

            return await ctx.message.channel.send(embed = embed)           
        
        ranks = sorted(
            ranks[-1],
            reverse = True, 
            key = lambda x: x[1] # XP total
        )[0:10]

        embed = discord.Embed(
            title = f"EXP EM DOBRO ATIVO — {dxp_restante}", 
            description = f"__Top 10 clãs:__", 
            color = 0x7a8ff5
        )

        for index, (clan_nome, clan_exp) in enumerate(ranks):
            embed.add_field(
                name = f'*{index + 1}º — {clan_nome.replace("+", " ")}*', # Nome
                value = f'{clan_exp:,}'.replace(",","."), # XP total
                inline = False
            )
        embed.add_field(name = "\n", value = "Para o rank completo, use **@Ranks PT-BR rank dxp**.", inline = False)

        return await ctx.message.channel.send(embed = embed)

    # Double ainda não passou.
    try:
        inicio_dxp = ClanController.resgatar_data_dxp()[1]
        agora = datetime.now()

        if inicio_dxp > agora:
            restante = inicio_dxp - agora

            data = f"no dia __{inicio_dxp.strftime('%d/%m/%Y')}__" if restante.days > 0 else "__HOJE__"

            if restante.days >= 2:
                restante = f"{restante.days} dias e {restante.seconds // 3600} horas"
            elif restante.days >= 1:
                restante = f"1 dia e {restante.seconds // 3600} horas"
            elif restante.seconds > 7200:
                restante = f"{restante.seconds // 3600} horas"
            elif restante.seconds > 3600:
                restante = f"1 hora"
            elif restante.seconds > 300:   
                restante = f"{restante.seconds // 60} minutos"
            else:
                restante = "Menos de um minuto"

            embed = discord.Embed(
                title = f"{restante} para o próximo DXP!", 
                description = f"O evento começa {data} às __09:00__, horário de Brasília (12:00 do jogo).", 
                color = 0x7a8ff5)
            embed.add_field(
                name = "", 
                value = "Para o rank completo do último DXP, use **@Ranks PT-BR rank dxp**.", 
                inline = False
            )

            return await ctx.message.channel.send(embed = embed)
    except TypeError:
        pass # 'inicio_dxp' retornou como None, devido a erro.
    
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
            key = lambda x: x[1] # XP total
        )

        # txt
        if tipo == 1: 
            dados = '\n'.join([
                f'{index + 1}º — {nome.replace("+", " ")} — {exp_total:,}'.replace(",", ".")
                for index, (nome, exp_total, *_) in enumerate(dados)
            ])

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
                [index + 1, nome, exp_total] 
                for index, (nome, exp_total, *_) in enumerate(dados)
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

            for (nome, exp_total, *_) in dados:
                csv_writer.writerow(
                    [nome, exp_total]
                )

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

            for index, (nome, exp_total, *_) in enumerate(dados):
                worksheet1.write(f'A{index + 1}', nome)
                worksheet1.write(f'B{index + 1}', exp_total)

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
            dados = '\n'.join([
                f'{index + 1}º — {nome.replace("+", " ")} — {exp_total:,}'.replace(",", ".")
                for index, (nome, exp_total, *_) in enumerate(dados[:50])
            ])
        
            await ctx.message.channel.send(f"{msg} {ctx.message.author.mention}\n\n{dados}")

    # 'args' vem como tupla, que é imutável.
    args = list(args)

    # Detecta se a pessoa botou o formato antes, depois ou até sem uma data.
    FORMATOS = {"txt": 1, "json": 2, "csv": 3, "xlsx": 4, "cru": 5}

    tipo = None

    for formato, valor in FORMATOS.items():
        if formato in args:
            args.remove(formato)
            tipo = valor
            break
    else: 
        # Formato não foi especificado ou é inválido.
        tipo = 1 

        # Tenta remover o formato (não-suportado) que foi dado ao comando.
        if len(args) > 1:
            # Ignora números, logo, ignora possíveis datas.
            if not args[1].isdigit():
                args.pop(1)
            if not args[-1].isdigit():
                args.pop(-1)

    if "geral" in args:
        if len(args) == 1:
            data = datetime.now().date()
        else:
            try:
                ano = int(args[3])
                ano += 2000 if ano < 100 else 0
                if ano < 2000:
                    return await ctx.message.channel.send(
                        f"Informe um ano válido. {ctx.message.author.mention}"
                    )

                data = date(year = ano, month = int(args[2]), day = int(args[1]))
            except (ValueError, IndexError):
                return await ctx.message.channel.send(
                    f"Use o formato `DD MM AAAA` para representar uma data válida. {ctx.message.author.mention}"
                )

        query = ClanController.resgatar_rank_geral(data)
        if not query:
            return await ctx.message.channel.send(
                f"Não há registros do dia `{data.strftime('%d/%m/%Y')}`. {ctx.message.author.mention}"
            )

        msg = f"Rank Geral `{query[0][2].strftime('%d/%m/%Y')}`"
        return await enviar_mensagem()
    
    if "mensal" in args:
        if len(args) == 1:
            inicio = datetime.now().date() - timedelta(days = 30)
            fim = datetime.now().date()
        else:
            try:
                ano_inicio = int(args[3])
                ano_inicio += 2000 if ano_inicio < 100 else 0
                if ano_inicio < 2000:
                    return await ctx.message.channel.send(
                        f"Informe um ano de início válido. {ctx.message.author.mention}"
                    )
                
                ano_fim = int(args[6])
                ano_fim += 2000 if ano_fim < 100 else 0
                if ano_fim < 2000:
                    return await ctx.message.channel.send(
                        f"Informe um ano de fim válido. {ctx.message.author.mention}"
                    )

                inicio = date(year = ano_inicio, month = int(args[2]), day = int(args[1]))
                fim = date(year = ano_fim, month = int(args[5]), day = int(args[4]))
            except (ValueError, IndexError):
                return await ctx.message.channel.send(
                    f"Use o formato `DD MM AAAA DD MM AAAA` para representar datas válidas. {ctx.message.author.mention}"
                )

        query = ClanController.resgatar_rank_mensal(inicio, fim)
        erros = {
            -1: f"A data `{inicio.strftime('%d/%m/%Y')}` ainda não chegou! {ctx.message.author.mention}",
            -2: f"A data `{fim.strftime('%d/%m/%Y')}` ainda não chegou! {ctx.message.author.mention}",
            -3: f"Não há dados registrados para o período terminando em `{fim.strftime('%d/%m/%Y')}`! {ctx.message.author.mention}",
            -4: f"Não há dados registrados para o período começando em `{inicio.strftime('%d/%m/%Y')}`! {ctx.message.author.mention}",
            -5: f"Ocorreu um erro no resgate dos dados! {ctx.message.author.mention}"
        }

        if isinstance(query, int):
            return await ctx.message.channel.send(erros[query])

        data_inicio, data_fim, query = query
        msg = f"Rank Mensal de `{data_inicio}` até `{data_fim}`"
        return await enviar_mensagem()

    if "dxp" in args:
        if len(args) > 2:
            return await ctx.message.channel.send(
                f"Use o formato `@Ranks PT-BR rank dxp N`. {ctx.message.author.mention}"
            )

        quantos_atras = int(args[1]) if len(args) > 1 and args[1].isdigit() else 0

        query = ClanController.resgatar_rank_dxp(quantos_atras)
        erros = {
            -1: f"Não há histórico de um DXP tão antigo assim para exibir; tente um número menor. {ctx.message.author.mention}",
            -2: f"Não há histórico de DXP para exibir; use `@Ranks PT-BR dxp` para ver informações sobre futuros Doubles. {ctx.message.author.mention}",
            -3: f"Não há dados suficientes para gerar um rank ainda; tente novamente dentro de 1 hora. {ctx.message.author.mention}",
            -4: f"Ocorreu um erro no resgate dos dados! {ctx.message.author.mention}"
        }

        if isinstance(query, int):
            return await ctx.message.channel.send(erros[query])

        data_inicio, data_fim, query = query
        msg = f"Rank DXP de `{data_inicio}` até `{data_fim}`"
        return await enviar_mensagem()

    await ctx.message.channel.send(
        f"Você precisa especificar o tipo de rank! {ctx.message.author.mention}"
    )

@bot.command()
async def criar(ctx, *args):
    if not "dxp" in args:
        raise CommandNotFound
    
    if not AdminController.possui_nv_acesso(1, int(ctx.message.author.id)):
        return await ctx.message.channel.send(
            f"Você não tem permissão para acessar esse comando! {ctx.message.author.mention}"
        )

    try:
        # 'args[1:]' elimina o primeiro elemento que é "dxp". 
        comeco_dia, comeco_mes, comeco_ano, fim_dia, fim_mes, fim_ano = [int(arg) for arg in args[1:]]

        comeco_ano += 2000 if comeco_ano < 100 else 0
        if comeco_ano < 2000:
            return await ctx.message.channel.send(
                f"Informe um ano de início válido. {ctx.message.author.mention}"
            )
        
        fim_ano += 2000 if fim_ano < 100 else 0
        if fim_ano < 2000:
            return await ctx.message.channel.send(
                f"Informe um ano de fim válido. {ctx.message.author.mention}"
            )
    except ValueError:
        return await ctx.message.channel.send(
            f"Use o formato `@Ranks PT-BR criar dxp DD MM AAAA DD MM AAAA` para registrar um novo DXP! {ctx.message.author.mention}"
        )
    
    try:
        data_comeco = datetime(comeco_ano, comeco_mes, comeco_dia, 9, 0, 0)
        data_fim = datetime(fim_ano, fim_mes, fim_dia, 9, 0, 0)
    except ValueError:
        return await ctx.message.channel.send(
            f"Você não inseriu uma data correta {ctx.message.author.mention}!"
        )

    if ClanController.verificar_dxp(data_comeco, data_fim):
        return await ctx.message.channel.send(
            f"Já há um DXP registrado para as datas entre `{data_comeco.strftime('%d/%m/%Y')}` e `{data_fim.strftime('%d/%m/%Y')}`, {ctx.message.author.mention}!"
        )

    if AdminController.adicionar_dxp(data_comeco, data_fim):
        await ctx.message.channel.send(
            f"Double XP para as datas entre `{data_comeco.strftime('%d/%m/%Y')}` e `{data_fim.strftime('%d/%m/%Y')}` registrado com sucesso {ctx.message.author.mention}!"
        )

        LogController.adicionar_log(
            f"[{datetime.now()}] {ctx.message.author} registrou novo DXP de {data_comeco.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}."
        )

@bot.command()
async def deletar(ctx, *args):
    if not "dxp" in args:
        raise CommandNotFound
    
    if not AdminController.possui_nv_acesso(1, int(ctx.message.author.id)):
        return await ctx.message.channel.send(
            f"Você não tem permissão para acessar esse comando! {ctx.message.author.mention}"
        )
    
    datas = AdminController.deletar_dxp()

    if not datas:
        return await ctx.message.channel.send(
            f"Não há outro DXP registrado para ser deletado! {ctx.message.author.mention}"
        )

    await ctx.message.channel.send(
            f"O DXP de {datas[0].strftime('%d/%m/%Y')} até {datas[1].strftime('%d/%m/%Y')} foi deletado. {ctx.message.author.mention}"
        )

    LogController.adicionar_log(
        f"[{datetime.now()}] {ctx.message.author} deletou o DXP de {datas[0].strftime('%d/%m/%Y')} até {datas[1].strftime('%d/%m/%Y')}."
    )

@bot.command()
async def adicionar(ctx, *args):
    if any([palavra in args for palavra in ["clan", "clã", "cla"]]):
        if not AdminController.possui_nv_acesso(1, int(ctx.message.author.id)):
            return await ctx.message.channel.send(
                f"Você não tem permissão para acessar esse comando! {ctx.message.author.mention}"
            )
        
        # Remove 'clan' que vem junto no *args.
        nome = "+".join(list(args)[1:])
        clan_id = nomes_scrapper.verificar_clan_existe(nome)
        nome = nome.replace("+", " ")

        if not clan_id:
            return await ctx.message.channel.send(
                f"O clã `{nome}` não foi encontrado no site oficial do RuneScape. {ctx.message.author.mention}"
            )

        if not AdminController.adicionar_clan(clan_id, nome):
            return await ctx.message.channel.send(
                f"O clã `{nome}` já está registrado. {ctx.message.author.mention}"
            )
        
        LogController.adicionar_log(
            f"[{datetime.now()}] {ctx.message.author.name} adicionou o clã {nome}."
        )

        return await ctx.message.channel.send(
            f"O clã `{nome}` foi registrado com sucesso. {ctx.message.author.mention}"
        ) 
        
    if "mod" in args:
        if not AdminController.possui_nv_acesso(2, int(ctx.message.author.id)):
            return await ctx.message.channel.send(
                f"Você não tem permissão para acessar esse comando! {ctx.message.author.mention}"
            )
        
        try:
            usuario = int(args[1])
        except ValueError:
            return await ctx.message.channel.send(
                f"Você não inseriu um ID de usuário de Discord válido! {ctx.message.author.mention}"
            )

        nome = bot.get_user(usuario).display_name

        if not AdminController.adicionar_moderador(usuario):
            return await ctx.message.channel.send(
                f"`{nome}` já faz parte da moderação. {ctx.message.author.mention}"
            )
        
        LogController.adicionar_log(
            f"[{datetime.now()}] {ctx.message.author.name} adicionou {nome} à moderação."
        )

        await ctx.message.channel.send(
            f"`{nome}` agora faz parte da moderação! {ctx.message.author.mention}"
        ) 

@bot.command()
async def remover(ctx, *args):
    if any([palavra in args for palavra in ["clan", "clã", "cla"]]):
        if not AdminController.possui_nv_acesso(1, int(ctx.message.author.id)):
            return await ctx.message.channel.send(
                f"Você não tem permissão para acessar esse comando! {ctx.message.author.mention}"
            )
        
        clan = "+".join(list(args))
        nome = clan.replace("+", " ") 

        if not AdminController.remover_clan(clan):
            return await ctx.message.channel.send(
                f"O clã `{nome}` não está registrado. {ctx.message.author.mention}"
            )
        
        LogController.adicionar_log(
            f"[{datetime.now()}] {ctx.message.author.name} removeu o clã {nome}."
        )

        return await ctx.message.channel.send(
            f"O clã `{nome}` foi removido com sucesso. {ctx.message.author.mention}"
        ) 
        
    if "mod" in args:
        if not AdminController.possui_nv_acesso(2, int(ctx.message.author.id)):
            return await ctx.message.channel.send(
                f"Você não tem permissão para acessar esse comando! {ctx.message.author.mention}"
            )
        
        try:
            usuario = int(args[1])
        except ValueError:
            return await ctx.message.channel.send(
                f"Você não inseriu um ID de usuário de Discord válido! {ctx.message.author.mention}"
            )

        nome = bot.get_user(usuario).display_name

        if not AdminController.remover_moderador(usuario):
            return await ctx.message.channel.send(
                f"`{nome}` não faz parte da moderação. {ctx.message.author.mention}"
            )
        
        LogController.adicionar_log(
            f"[{datetime.now()}] {ctx.message.author.name} removeu {nome} da moderação."
        )

        await ctx.message.channel.send(
            f"`Agora {nome}` não faz mais parte da moderação. {ctx.message.author.mention}"
        )

@bot.event
async def on_ready():
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
        
        # Ignora mensagem privada.
        if isinstance(message.channel, discord.channel.DMChannel):
            return

        await message.channel.typing()

        # Se alguém só marcou o bot, sem pedir algum comando.
        if message.content == "<@1071957068262674582>":
            return await lista_comandos(message)
        
        await bot.process_commands(message)
    except discord.errors.Forbidden as e:
        LogController.adicionar_log(
            f"[{datetime.now()}] Erro de permissão em {message.guild.name}: {e}"
        )

if __name__ == '__main__':
    threading.Thread(target = loop_diario).start()
    bot.run(TOKEN)