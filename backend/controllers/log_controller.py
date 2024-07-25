from ..models import LogModel

class LogController:
    """Responsável por controlar os logs feitos pelo bot."""

    @staticmethod
    def adicionar_log(mensagem: str) -> None:
        """
        Adiciona um novo registro no arquivo de log e depois exibe no terminal.

        Parâmetros:
            mensagem: str
                Mensagem a ser salva no log.
        """

        LogModel.adicionar_log(mensagem)
