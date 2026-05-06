from discord.ext.commands.errors import MissingRequiredArgument, BadArgument
from discord.ext.commands import CommandNotFound
from discord.ext import commands
import discord

class RanksPtBr(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix = commands.when_mentioned,
            intents = intents
        )

    async def setup_hook(self):
        extensions = (
            'cogs.loop_diario',
            'cogs.eventos',
            'cogs.criacao',
            'cogs.remocao',
            'cogs.ranks',
            'cogs.dxp'
        )

        for ext in extensions:
            await self.load_extension(ext)

    def run(self):
        with open("token.txt", 'r') as file:
            super().run(file.readline())

if __name__ == '__main__':
    RanksPtBr().run()