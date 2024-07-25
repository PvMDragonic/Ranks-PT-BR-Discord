class LogModel:
    """Responsável por fazer registros no log."""

    @staticmethod
    def adicionar_log(mensagem: str) -> None:
        """
        Adiciona um novo registro no arquivo de log e depois exibe no terminal.

        Parâmetros:
            mensagem: str
                Mensagem a ser salva no log.
        """

        with open('log.txt', 'a') as arqv:
            arqv.writelines(f'{mensagem}\n')
            print(mensagem)