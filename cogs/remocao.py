from discord.ext import commands
from datetime import datetime
import discord

from backend import AdminController
from backend import LogController

class Remocao(commands.Cog):
    """Cog responsável por remover novos clãs, double xps ou moderadores."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command = True)
    async def remover(self, ctx):
        await ctx.send(f"Use `remover clan <nome>`, `remover mod <id>` ou `remover dxp`! {ctx.message.author.mention}")

    @remover.command(name = "clan", aliases = ["cla", "clã"])
    async def remover_clan(self, ctx, *args):
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
            
    @remover.command(name = "mod")
    async def remover_mod(self, ctx, *args):
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

    @remover.command(name = "dxp")
    async def remover_dxp(self, ctx):
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

async def setup(bot):
    await bot.add_cog(Remocao(bot))