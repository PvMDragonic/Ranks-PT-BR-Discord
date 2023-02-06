from discord.ext.commands import CommandNotFound
from discord.ext import commands
import threading
import datetime
import discord
import time

import nomes_scrapper

with open("token.txt", 'r') as file:
    TOKEN = file.readline()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix = commands.when_mentioned, intents = intents)    

def loop_mensal():
    while True:
        time.sleep(84600)

        if datetime.date.today().day == 1:
            nomes_scrapper.buscar_clans()

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
    threading.Thread(target = loop_mensal).start()
    bot.run(TOKEN)