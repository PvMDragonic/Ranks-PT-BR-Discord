from discord.ext import commands
from datetime import datetime, timedelta
import discord

from backend import ClanController

class Ranks(commands.Cog):
    """Cog responsável pelo comando de exibir os diferentes rankings."""

    def __init__(self, bot):
        self.bot = bot

    async def _enviar_mensagem(self, msg: str, query: list[str], tipo: int, ctx: commands.Context):
        """Função de suporte para formatar os rankings."""

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

    def _selecionar_tipo(self, *args: str) -> tuple[int, list[str]]:
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

        return (tipo, args)

    @commands.group(invoke_without_command = True)
    async def rank(self, ctx):
        await ctx.send(f"Use `rank geral`, `rank mensal` ou `rank dxp`! {ctx.message.author.mention}")

    @rank.command(name = "geral")
    async def rank_geral(self, ctx, *args):
        tipo, args = self._selecionar_tipo(args)

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
                    f"Use `rank geral [DD] [MM] [AAAA]`! {ctx.message.author.mention}"
                )

        query = ClanController.resgatar_rank_geral(data)
        if not query:
            return await ctx.message.channel.send(
                f"Não há registros do dia `{data.strftime('%d/%m/%Y')}`. {ctx.message.author.mention}"
            )

        msg = f"Rank Geral `{query[0][2].strftime('%d/%m/%Y')}`"
        return await self._enviar_mensagem(msg, query, tipo, ctx)
    
    @rank.command(name = "mensal")
    async def rank_mensal(self, ctx, *args):
        tipo, args = self._selecionar_tipo(args)

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
                    f"Use `rank mensal [DD] [MM] [AAAA] [DD] [MM] [AAAA]`! {ctx.message.author.mention}"
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
        return await self._enviar_mensagem(msg, query, tipo, ctx)

    @rank.command(name = "dxp")
    async def rank_dxp(self, ctx, *args):
        tipo, args = self._selecionar_tipo(args)

        if len(args) > 2:
            return await ctx.message.channel.send(
                f"Use `rank dxp [n]`. {ctx.message.author.mention}"
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
        return await self._enviar_mensagem(msg, query, tipo, ctx)

async def setup(bot):
    await bot.add_cog(Ranks(bot))