from discord.ext import commands
from datetime import datetime
import discord

from backend import ClanController

class Dxp(commands.Cog):
    """Cog responsável pelo comando de Double XP."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def dxp(self, ctx):
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
                dias = restante.days
                horas = restante.seconds // 3600
                minutos = (restante.seconds % 3600) // 60

                if dias >= 2:
                    restante = f"{dias} dias e {horas} horas"
                elif dias >= 1:
                    restante = f"1 dia e {horas} hora{'s' if horas > 1 else ''}"
                elif restante.seconds > 7200:
                    restante = f"{horas} horas e {minutos} minuto{'s' if minutos > 1 else ''}"
                elif restante.seconds > 3600:
                    restante = f"1 hora e {minutos} minuto{'s' if minutos > 1 else ''}"
                elif restante.seconds > 300:   
                    restante = f"{minutos} minutos"
                else:
                    restante = "Menos de cinco minutos"

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

async def setup(bot):
    await bot.add_cog(Dxp(bot))