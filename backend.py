import psycopg2

class Conexao(object):    
    def __init__(self) -> None:
        self._db = psycopg2.connect(
            host = 'localhost', 
            database = 'clansptbr', 
            user = 'postgres',  
            password = 123456
        )

    def manipular(self, sql) -> bool:
        try:
            cur = self._db.cursor()
            cur.execute(sql)
            cur.close()
            self._db.commit()
            return True
        except Exception as e:
            print(e)
            return False

    def consultar(self, sql) -> list[tuple]:
        try:
            cur = self._db.cursor()
            cur.execute(sql)
            return cur.fetchall()
        except Exception as e:
            print(e)
            return None

    def fechar(self):
        self._db.close()

def resgatar_clans() -> list:
    db = Conexao()
    nomes = db.consultar("SELECT * FROM clans")
    db.fechar()
    return nomes

def adicionar_clans(lista: list) -> None:
    db = Conexao()
    for nome in lista:
        if not db.consultar(f"SELECT 1 FROM clans WHERE nome='{nome}'"):
            db.manipular(f"INSERT INTO clans (nome) VALUES ('{nome}')")
    db.fechar()