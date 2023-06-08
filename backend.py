from datetime import datetime, timedelta, date
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
            return True
        except Exception as e:
            msg = f"[{datetime.now()}] Erro durante manipulação: {e}"
            adicionar_log(msg)
            print(msg)
            return False

    def consultar(self, sql) -> list[tuple]:
        try:
            cur = self._db.cursor()
            cur.execute(sql)
            return cur.fetchall()
        except Exception as e:
            msg = f"[{datetime.now()}] Erro durante consulta: {e}"
            adicionar_log(msg)
            print(msg)
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

def resgatar_rank_geral(data: date) -> list[Estatisticas]:
    try:
        db = Conexao()

        if data:
            return [
                Estatisticas(*clan) for clan in db.consultar(
                    f"SELECT DISTINCT ON (nome) nome, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total \
                    FROM estatisticas JOIN clans ON estatisticas.id_clan = clans.id \
                    WHERE (data_hora BETWEEN '{data} 00:01:00' AND '{data} 23:59:00') \
                    AND (arquivado = 'False')"
                )
            ]

        return [
            Estatisticas(*clan) for clan in db.consultar(
                "SELECT DISTINCT ON (nome) nome, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total \
                FROM estatisticas JOIN clans ON estatisticas.id_clan = clans.id \
                WHERE arquivado = 'False' \
                ORDER BY nome, data_hora DESC"
            )
        ]
    finally:
        db.fechar()

def resgatar_rank_mensal(data_inicio: date, data_fim: date):
    class Datas():
        def __init__(self, *args) -> None:
            self.data_atual, self.data_passado = args

    try:
        db = Conexao()
        
        # Não especificou mês; assume data mais recente.
        if data_inicio == None:
            fim = [
                Estatisticas(*clan) for clan in db.consultar(
                    "SELECT DISTINCT ON (nome) nome, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total \
                    FROM estatisticas JOIN clans ON estatisticas.id_clan = clans.id \
                    WHERE arquivado = 'False' \
                    ORDER BY nome, data_hora DESC"
                ) 
            ]

            mes_passado = fim[0].data_hora.date() - timedelta(days = 30)

            inicio = [
                Estatisticas(*clan) for clan in db.consultar(
                    f"SELECT DISTINCT ON (nome) nome, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total \
                    FROM estatisticas JOIN clans ON estatisticas.id_clan = clans.id \
                    WHERE (data_hora BETWEEN '{mes_passado} 00:01:00' AND '{mes_passado} 23:59:00') \
                    AND (arquivado = 'False')"
                )
            ]

            # Pega a data mais antiga disponível.
            if not inicio:
                inicio = [
                    Estatisticas(*clan) for clan in db.consultar(
                        "SELECT DISTINCT ON (nome) nome, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total \
                        FROM estatisticas JOIN clans ON estatisticas.id_clan = clans.id \
                        WHERE arquivado = 'False' \
                        ORDER BY nome, data_hora"
                    )
                ]
        else:
            if data_inicio > datetime.now().date():
                return -1
            
            if data_fim > datetime.now().date():
                return -2
            
            fim = [
                Estatisticas(*clan) for clan in db.consultar(
                    f"SELECT DISTINCT ON (nome) nome, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total \
                    FROM estatisticas JOIN clans ON estatisticas.id_clan = clans.id \
                    WHERE (data_hora BETWEEN '{data_fim} 00:01:00' AND '{data_fim} 23:59:00') \
                    AND (arquivado = 'False')"
                ) 
            ]

            if not fim:
                return -3

            inicio = [
                Estatisticas(*clan) for clan in db.consultar(
                    f"SELECT DISTINCT ON (nome) nome, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total \
                    FROM estatisticas JOIN clans ON estatisticas.id_clan = clans.id \
                    WHERE (data_hora BETWEEN '{data_inicio} 00:01:00' AND '{data_inicio} 23:59:00') \
                    AND (arquivado = 'False')"
                )
            ]

            if not inicio:
                return -4

        return [
            Estatisticas(
                a.clan_id,
                Datas(a.data_hora.strftime('%d/%m/%Y'), p.data_hora.strftime('%d/%m/%Y')),
                a.membros - p.membros,
                a.nv_fort - p.nv_fort,
                a.nv_total - p.nv_total,
                a.nv_cb_total - p.nv_cb_total,
                a.exp_total - p.exp_total
            ) for a, p in zip(fim, inicio) 
            if a.exp_total - p.exp_total != 0
        ]

    finally:
        db.fechar()

def resgatar_rank_dxp(quantos_atras: int) -> list:
    class Datas():
        def __init__(self, *args) -> None:
            self.data_fim, self.data_inicio = args

    try:
        db = Conexao()

        query = db.consultar("SELECT * FROM dxp ORDER BY data_comeco DESC")

        # Selecionou um DXP antigo demais que não tá na base de dados.
        if quantos_atras > (len(query) - 1):
            return -1

        double_atual = query[quantos_atras]
        inicio = double_atual[1]

        # Double ainda não passou.
        if inicio > datetime.now():

            # Se o único DXP do banco de dados ainda está pra vir.
            if len(query) == 1:
                return -2

            # Se há mais de um DXP registrados no banco de dados.
            ultimo_double = query[quantos_atras + 1]
            inicio = ultimo_double[1]
            fim = ultimo_double[2]

        # Data de início já passou.
        else:
            fim = double_atual[2]
            
        xp_inicio = [
            Estatisticas(*clan) for clan in db.consultar(
                f"SELECT DISTINCT ON (nome) nome, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total \
                FROM estatisticas JOIN clans ON estatisticas.id_clan = clans.id \
                WHERE (data_hora BETWEEN '{inicio}' AND '{fim}') \
                AND (arquivado = 'False') \
                ORDER BY nome, data_hora"
            )
        ]

        # DXP começou mas ainda não houve a primeira coleta de XP.
        if not xp_inicio:
            return -3

        xp_fim = [
            Estatisticas(*clan) for clan in db.consultar(
                f"SELECT DISTINCT ON (nome) nome, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total \
                FROM estatisticas JOIN clans ON estatisticas.id_clan = clans.id \
                WHERE (data_hora BETWEEN '{inicio}' AND '{fim}') \
                AND (arquivado = 'False') \
                ORDER BY nome, data_hora DESC"
            )
        ]

        # Só houve uma coleta de XP desde o início do Double.
        if xp_inicio == xp_fim:
            return -3

        return [
            Estatisticas(
                fim.clan_id,
                Datas(
                    fim.data_hora.strftime('%d/%m/%Y %H:%M'), 
                    inicio.data_hora.strftime('%d/%m/%Y %H:%M')
                ),
                fim.membros - inicio.membros,
                fim.nv_fort - inicio.nv_fort,
                fim.nv_total - inicio.nv_total,
                fim.nv_cb_total - inicio.nv_cb_total,
                fim.exp_total - inicio.exp_total
            ) for fim, inicio in zip(xp_fim, xp_inicio)
        ]
    finally:
        db.fechar()

def resgatar_data_dxp() -> datetime:
    try:
        db = Conexao()
        datahora = db.consultar("SELECT * FROM dxp ORDER BY data_comeco DESC")[0]
        return datahora
    finally:
        db.fechar()

def verificar_dxp(data_comeco: datetime, data_fim: datetime) -> bool:
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
        inicio = datas_dxp[1]
        fim = datas_dxp[2]
        return fim > datetime.now() > inicio
    finally:
        db.fechar()

def dxp_restante() -> str:
    try:
        db = Conexao()
        datas_dxp = db.consultar("SELECT * FROM dxp ORDER BY data_comeco DESC")[0]
        fim = datas_dxp[2]
        restante = fim - datetime.now()

        if restante.days >= 1:
            return f"{restante.days} dias e {restante.seconds // 3600} horas restantes!"
        elif restante.seconds > 3600:
            return f"{restante.seconds // 3600} horas restantes!"
        elif 300 < restante.seconds < 3600:   
            return f"{restante.seconds // 60} minutos restantes!"     
        else:
            return f"{restante.seconds // 60} encerramento eminente!" 
    finally:
        db.fechar()

def adicionar_dxp(data_comeco: datetime, data_fim: datetime) -> None:
    try:
        db = Conexao()
        return db.manipular(f"INSERT INTO dxp (data_comeco, data_fim) VALUES ('{data_comeco}', '{data_fim}')")
    finally:
        db.fechar()

def deletar_dxp() -> list[datetime]:
    try:
        db = Conexao()
        query = db.consultar("SELECT * FROM dxp ORDER BY id DESC LIMIT 1")
        
        if query:
            data_comeco, data_fim = query[0][1:3]
            db.manipular(f"DELETE FROM dxp WHERE data_comeco = '{data_comeco}' AND data_fim = '{data_fim}'")
            return [data_comeco, data_fim]
        
        return None
    finally:
        db.fechar()

def adicionar_estatisticas(lista: list[Estatisticas]) -> None:
    db = Conexao()
    for clan in lista:
        db.manipular(
            f"INSERT INTO estatisticas (id_clan, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total) \
            VALUES ({clan.clan_id}, '{clan.data_hora}', {clan.membros}, {clan.nv_fort}, {clan.nv_total}, {clan.nv_cb_total}, {clan.exp_total})"
        )
    db.fechar()

def adicionar_clans(clans: list[str]) -> None:
    db = Conexao()
    for nome in clans:
        if not db.consultar(f"SELECT * FROM clans WHERE nome = '{nome}'"):
            db.manipular(f"INSERT INTO clans (nome, arquivado) VALUES ('{nome}', 'False')")
    db.fechar()

def adicionar_clan(clan: str) -> bool:
    try:
        db = Conexao()
        query = db.consultar(f"SELECT * FROM clans WHERE nome = '{clan}'")

        if not query:
            return db.manipular(f"INSERT INTO clans (nome, arquivado) VALUES ('{clan}', 'False')")
        
        # Clã existe, mas arquivado.
        if query[3] == True:
            return db.manipular(f"UPDATE clans SET arquivado = 'False' WHERE nome = '{clan}'")
        
        return False
    finally:
        db.fechar()

def remover_clan(clan: str) -> bool:
    try:
        db = Conexao()
        query = db.consultar(f"SELECT * FROM clans WHERE nome = '{clan}'")

        if query:
            return db.manipular(f"UPDATE clans SET arquivado = 'True' WHERE nome = '{clan}'")
                
        return False
    finally:
        db.fechar()

def adicionar_log(texto: str) -> None:
    with open('log.txt', 'a') as arqv:
        arqv.writelines(f'{texto}\n')

def possui_nv_acesso(nv_requerido: int, id_usuario: int) -> bool:
    try:
        db = Conexao()
        nv_acesso = db.consultar(f"SELECT nv_acesso FROM admins WHERE id_discord = {id_usuario};")
        
        if nv_acesso:
            nv_acesso = nv_acesso[0][0]
            return nv_requerido <= nv_acesso
        
        return False
    finally:
        db.fechar()

def adicionar_moderador(id_usuario: int) -> bool:
    try:
        db = Conexao()
        
        if not db.consultar(f"SELECT * FROM admins WHERE id_discord = {id_usuario}"):
            return db.manipular(f"INSERT INTO admins(id_discord, nv_acesso) VALUES ({id_usuario}, 1)")
        
        return False
    finally:
        db.fechar()

def remover_moderador(id_usuario: int) -> bool:
    try:
        db = Conexao()
        
        if db.consultar(f"SELECT * FROM admins WHERE id_discord = {id_usuario}"):
            return db.manipular(f"DELETE FROM admins WHERE id_discord = {id_usuario}")        
        
        return False
    finally:
        db.fechar()