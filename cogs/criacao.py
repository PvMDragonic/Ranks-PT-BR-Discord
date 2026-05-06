from discord.ext import commands
from datetime import datetime
import discord

from backend import AdminController
from backend import ClanController
from backend import LogController

class Adicionar(commands.Cog):
    """Cog responsável por adicionar novos clãs, double xps ou moderadores."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command = True)
    async def adicionar(self, ctx):
        await ctx.send(f"Use `adicionar clan <nome>`, `adicionar mod <id>` ou `adicionar dxp <data_começo> <data_fim>`! {ctx.message.author.mention}")

    @adicionar.command(name = "clan", aliases = ["cla", "clã"])
    async def adicionar_clan(self, ctx, *args):
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
            
    @adicionar.command(name = "mod")
    async def adicionar_mod(self, ctx, *args):
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

        nome = self.bot.get_user(usuario).display_name

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

    @adicionar.command(name = "dxp")
    async def adicionar_dxp(self, ctx, *args):
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

async def setup(bot):
    await bot.add_cog(Adicionar(bot))