from datetime import datetime, timedelta, date, time
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
    def __init__(self, *args) -> None:
        self.clan_id, self.data_hora, self.membros, self.nv_fort, self.nv_total, self.nv_cb_total, self.exp_total = args

class Clan():
    def __init__(self, *args) -> None:
        self.id, self.nome = args

def resgatar_clans() -> list[Clan]:
    try:
        db = Conexao()
        return [Clan(*clan) for clan in db.consultar("SELECT * FROM clans")]
    finally:
        db.fechar()

def resgatar_rank_geral() -> list[Estatisticas]:
    try:
        db = Conexao()
        return [
            Estatisticas(*clan) for clan in db.consultar(
                "SELECT DISTINCT ON (nome) nome, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total \
                FROM estatisticas JOIN clans ON estatisticas.id_clan = clans.id \
                ORDER BY nome, data_hora DESC"
            )
        ]
    finally:
        db.fechar()

def resgatar_rank_mensal():
    class Datas():
        def __init__(self, *args) -> None:
            self.data_atual, self.data_passado = args

    try:
        db = Conexao()
        
        atual = [
            Estatisticas(*clan) for clan in db.consultar(
                "SELECT DISTINCT ON (nome) nome, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total \
                FROM estatisticas JOIN clans ON estatisticas.id_clan = clans.id \
                ORDER BY nome, data_hora DESC"
            ) 
        ]

        mes_passado = atual[0].data_hora.date() - timedelta(days = 30)

        passado = [
            Estatisticas(*clan) for clan in db.consultar(
                f"SELECT DISTINCT ON (nome) nome, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total \
                FROM estatisticas JOIN clans ON estatisticas.id_clan = clans.id \
                WHERE data_hora BETWEEN '{mes_passado} 00:01:00' AND '{mes_passado} 23:59:00'"
            )
        ]

        if not passado:
            # Pega a data mais antiga disponível.
            passado = [
                Estatisticas(*clan) for clan in db.consultar(
                    "SELECT DISTINCT ON (nome) nome, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total \
                    FROM estatisticas JOIN clans ON estatisticas.id_clan = clans.id \
                    ORDER BY nome, data_hora"
                )
            ]

        return [
            Estatisticas(
                a.clan_id,
                Datas(a.data_hora.date(), p.data_hora.date()),
                a.membros - p.membros,
                a.nv_fort - p.nv_fort,
                a.nv_total - p.nv_total,
                a.nv_cb_total - p.nv_cb_total,
                a.exp_total - p.exp_total
            ) for a, p in zip(atual, passado) 
            if a.exp_total - p.exp_total != 0
        ]

    finally:
        db.fechar()

def resgatar_rank_dxp():
    class Datas():
        def __init__(self, *args) -> None:
            self.data_fim, self.data_inicio = args

    try:
        db = Conexao()

        query = db.consultar("SELECT * FROM dxp ORDER BY data_comeco DESC")
        double_atual = query[0]
        inicio = double_atual[1]
        hoje = datetime.now().date()

        # Double ainda não passou.
        if inicio > hoje:

            # Se o primeiro DXP do banco de dados ainda está pra vir.
            if len(query) == 1:
                return None

            # Se há mais de um DXP registrados no banco de dados.
            else:
                ultimo_double = query[1]
                inicio = ultimo_double[1]
                fim = ultimo_double[2]

        # Data de início já passou.
        else:
            fim = double_atual[2]
            
        xp_inicio = [
            Estatisticas(*clan) for clan in db.consultar(
                f"SELECT DISTINCT ON (nome) nome, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total \
                FROM estatisticas JOIN clans ON estatisticas.id_clan = clans.id \
                WHERE data_hora BETWEEN '{inicio}' AND '{fim}' \
                ORDER BY nome, data_hora"
            )
        ]

        xp_fim = [
            Estatisticas(*clan) for clan in db.consultar(
                f"SELECT DISTINCT ON (nome) nome, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total \
                FROM estatisticas JOIN clans ON estatisticas.id_clan = clans.id \
                WHERE data_hora BETWEEN '{inicio}' AND '{fim}' \
                ORDER BY nome, data_hora DESC"
            )
        ]

        return [
            Estatisticas(
                f.clan_id,
                Datas(f.data_hora.strftime('%Y-%m-%d %H:%M'), i.data_hora.strftime('%Y-%m-%d %H:%M')),
                f.membros - i.membros,
                f.nv_fort - i.nv_fort,
                f.nv_total - i.nv_total,
                f.nv_cb_total - i.nv_cb_total,
                f.exp_total - i.exp_total
            ) for f, i in zip(xp_fim, xp_inicio)
        ]
    finally:
        db.fechar()

def resgatar_data_dxp() -> date:
    try:
        db = Conexao()
        return db.consultar("SELECT * FROM dxp ORDER BY data_comeco DESC")[0]
    finally:
        db.fechar()

def verificar_dxp(data_comeco: date, data_fim: date) -> bool:
    try:
        db = Conexao()
        return db.consultar(
            f"SELECT * FROM dxp WHERE (data_comeco <= '{data_fim}') and ('{data_comeco}' <= data_fim);"
        )
    finally:
        db.fechar()

def dxp_acontecendo() -> bool:
    try:
        db = Conexao()
        datas_dxp = db.consultar("SELECT * FROM dxp ORDER BY data_comeco DESC")[0]
        inicio = datetime.combine(datas_dxp[1], time(9))
        fim = datetime.combine(datas_dxp[2],  time(9))
        return fim > datetime.now() > inicio
    finally:
        db.fechar()

def adicionar_dxp(data_comeco: date, data_fim: date) -> None:
    db = Conexao()
    db.manipular(
        f"INSERT INTO dxp (data_comeco, data_fim) VALUES ('{data_comeco}', '{data_fim}')"
    )
    db.fechar()

def adicionar_estatisticas(lista: list[Estatisticas]) -> None:
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

def adicionar_log(texto: str) -> None:
    with open('log.txt', 'a') as arqv:
        arqv.writelines(texto)