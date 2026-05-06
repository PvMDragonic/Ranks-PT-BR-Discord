from discord.ext.commands import CommandNotFound
from discord.ext import commands
from datetime import datetime
from time import sleep
import discord
import json

from backend import LogController
from backend import AdminController

class Eventos(commands.Cog):
    """
    Cog responsável pelos seguintes eventos do bot:
        - on_ready();
        - on_command_error(); e
        - on_message()
    
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'>> {self.bot.user} on-line!')

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, CommandNotFound):
            return await ctx.message.channel.send(
                f"Você digitou um comando inválido {ctx.message.author.mention}!"
            )
        raise error

    async def lista_comandos(self, message):
        if AdminController.possui_nv_acesso(1, int(message.author.id)):
            embed = discord.Embed(
                title = "COMANDOS DA MODERAÇÃO",
                description = "Comandos para quem faz parte da Equipe de Moderação.\n\n᲼᲼",
                color = 0x7a8ff5
            )

            comandos = [
                ("@Ranks PT-BR adicionar dxp [DD] [MM] [AAAA] [DD] [MM] [AAAA]", "Registra um novo DXP entre [data início] e [data fim].\n᲼᲼"),
                ("@Ranks PT-BR remover dxp", "Deleta o DXP que foi registrado por último.\n᲼᲼"),
                ("@Ranks PT-BR adicionar clan [nome]", "Adiciona um clã ao banco de dados do bot.\n᲼᲼"),
                ("@Ranks PT-BR remover clan [nome]", "Remove um clã do banco de dados do bot.\n᲼᲼"),
            ]

            for cmd, descricao in comandos:
                embed.add_field(name = cmd, value = descricao, inline = False)

            embed.set_footer(text = "OBS.: O uso desses comandos é registrado no log, com o nome de quem usou.")

            await message.author.send(embed = embed)

        with open('dados/comandos.json', 'r', encoding = 'utf-8') as json_file:
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

    @commands.Cog.listener()
    async def on_message(self, message):
        try:
            if not self.bot.user.mentioned_in(message):
                return
            
            # Ignora mensagem privada.
            if isinstance(message.channel, discord.channel.DMChannel):
                return

            # Se alguém só marcou o bot, sem pedir algum comando.
            if message.content == self.bot.user.mention:
                async with message.channel.typing():
                    await self.lista_comandos(message)

        except discord.errors.Forbidden as e:
            LogController.adicionar_log(
                f"[{datetime.now()}] Erro de permissão em {message.guild.name}: {e}"
            )

async def setup(bot):
    await bot.add_cog(Eventos(bot))