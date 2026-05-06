from discord.ext import commands, tasks
from datetime import datetime, date, time
import discord

from backend import AdminController
from backend import ClanController
from backend import LogController

class LoopDiario(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tarefa_diaria.start()
        self.tarefa_dxp.start()

    def cog_unload(self):
        self.tarefa_diaria.cancel()
        self.tarefa_dxp.cancel()

    async def msg_padrao(self):
        await self.bot.change_presence(activity = discord.Game(name = 'Marca o bot p/ cmd'))

    async def coletar_xp(self):
        await self.bot.change_presence(activity = discord.Game(name = 'Coletando EXP...'))
        exp_scrapper.buscar_clans()
        await self.msg_padrao()

    # Função separada porque não estava dando certo chamar self.tarefa_diaria.coro().
    async def _coletar_clans_xp(self):
        if date.today().day == 1 or ClanController.resgatar_clans() is None:
            await self.bot.change_presence(activity = discord.Game(name = 'Buscando clãs...'))
            nomes_scrapper.buscar_clans()
            await self.msg_padrao()

        try:
            ultima_coleta = ClanController.resgatar_rank_geral()[0][2].date()
            dxp_recem_acabou = datetime.now().date() == ClanController.resgatar_data_dxp()[2].date()

            if (datetime.now().date() > ultima_coleta) or (dxp_recem_acabou and datetime.now().time() <= time(10, 0)):
                await self.coletar_xp()
        except TypeError:
            await self.coletar_xp()

        try:
            data_comeco, data_fim = dxp_scrapper.procurar_double()
            if not ClanController.verificar_dxp(data_comeco, data_fim):
                if AdminController.adicionar_dxp(data_comeco, data_fim):
                    LogController.adicionar_log(
                        f"[{datetime.now()}] registro automático de novo DXP para "
                        f"{data_comeco.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}."
                    )
        except ValueError:
            pass

    @tasks.loop(time = time(9, 5))
    async def tarefa_diaria(self):
        await self._coletar_clans_xp()

    @tasks.loop(hours = 1)
    async def tarefa_dxp(self):
        if not ClanController.dxp_acontecendo():
            return
        await self.coletar_xp()

    @tarefa_diaria.before_loop
    async def antes_da_tarefa_diaria(self):
        await self.bot.wait_until_ready()
        if datetime.now().time() > time(9, 5):
            await self._coletar_clans_xp()

    @tarefa_dxp.before_loop
    async def antes_da_tarefa_dxp(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(LoopDiario(bot))