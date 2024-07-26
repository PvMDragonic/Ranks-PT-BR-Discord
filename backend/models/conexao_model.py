import psycopg2

class Conexao:
    """Responsável pela conexão com o banco de dados."""  

    def __init__(self):
        self._db = psycopg2.connect(
            host = 'localhost',
            database = 'clansptbr',
            user = 'postgres',
            password = '123456'
        )

    def manipular(self, query: str, *args: tuple) -> bool:
        """
        Método para alterar ou inserir dados no banco.
        
        Parâmetros:
            query: str
                A query SQL.
            args: tuple
                Valores a serem inseridos na query.

        Retorna:
            bool: 
                Status da operação realizada.
        """

        try:
            cur = self._db.cursor()
            cur.execute(query, args)
            cur.close()
            self._db.commit()
            return True
        except psycopg2.errors:
            raise

    def consultar(self, query: str, *args: tuple) -> list[tuple] | None:
        """
        Método para consultar o banco de dados.
        
        Parâmetros:
            query: str
                A query SQL.
            args: tuple
                Valores a serem inseridos na query.

        Retorna:
            list: 
                [(...), ...]
            None: 
                Caso a query não seja válida.
        """

        try:
            cur = self._db.cursor()
            cur.execute(query, args)
            res = cur.fetchall()
            return res if res else None
        except psycopg2.errors:
            raise

    def fechar(self):
        """Encerra a conexão com o banco de dados."""
        
        self._db.close()