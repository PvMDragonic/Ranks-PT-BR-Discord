from datetime import datetime, date
import psycopg2

class Conexao(object):    
    def __init__(self) -> None:
        self._db = psycopg2.connect(
            host = 'localhost', 
            database = 'clansptbr', 
            user = 'postgres',  
            password = 123456
        )

    def manipular(self, sql) -> None:
        try:
            cur = self._db.cursor()
            cur.execute(sql)
            cur.close()
            self._db.commit()
        except Exception as e:
            print(e)

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

class Estatisticas():
    def __init__(self, clan_id, membros, nv_fort, nv_total, exp_total, nv_cb_total) -> None:
        self.data_hora = datetime.now()
        self.clan_id = clan_id
        self.membros = membros
        self.nv_fort = nv_fort
        self.nv_total = nv_total
        self.exp_total = exp_total
        self.nv_cb_total = nv_cb_total

class Clan():
    def __init__(self, tupla) -> None:
        self.id, self.nome = tupla

def resgatar_clans() -> list[Clan]:
    db = Conexao()
    nomes = db.consultar("SELECT * FROM clans")
    nomes = [Clan(clan) for clan in nomes]
    db.fechar()
    return nomes

def resgatar_ultimo_dxp() -> list[date]:
    db = Conexao()
    data = db.consultar("SELECT * FROM dxp ORDER BY data_comeco")[0][1]
    db.fechar()
    return data.strftime("%m/%d/%Y")

def verificar_dxp(data_comeco: date, data_fim: date) -> bool:
    db = Conexao()
    data_ocupada = db.consultar(
        f"SELECT * FROM dxp WHERE data_comeco >= '{data_comeco}' AND data_fim < '{data_fim}'"
    )
    db.fechar()
    return True if data_ocupada else False

def adicionar_dxp(data_comeco: date, data_fim: date) -> None:
    db = Conexao()
    db.manipular(
        f"INSERT INTO dxp (data_comeco, data_fim) \
            VALUES ('{data_comeco}', '{data_fim}')"
    )
    db.fechar()

def adicionar_estatisticas(lista: list) -> None:
    db = Conexao()
    for clan in lista:
        db.manipular(
            f"INSERT INTO estatisticas (id_clan, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total) \
                VALUES ({clan.clan_id}, '{clan.data_hora}', {clan.membros}, {clan.nv_fort}, {clan.nv_total}, {clan.nv_cb_total}, {clan.exp_total})"
        )
    db.fechar()

def adicionar_clans(lista: list) -> None:
    db = Conexao()
    for nome in lista:
        if not db.consultar(f"SELECT 1 FROM clans WHERE nome='{nome}'"):
            db.manipular(f"INSERT INTO clans (nome) VALUES ('{nome}')")
    db.fechar()