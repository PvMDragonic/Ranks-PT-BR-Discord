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

def resgatar_clans() -> list:
    try:
        db = Conexao()
        return db.consultar("SELECT * FROM clans")
    finally:
        db.fechar()

def resgatar_rank_geral(data: date) -> list[str]:
    try:
        db = Conexao()

        if data:
            return db.consultar(
                f"SELECT DISTINCT ON (nome) nome, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total \
                FROM estatisticas JOIN clans ON estatisticas.id_clan = clans.id \
                WHERE (data_hora BETWEEN '{data} 00:01:00' AND '{data} 23:59:00') \
                AND (arquivado = 'False')"
            )

        return db.consultar(
            "SELECT DISTINCT ON (nome) nome, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total \
            FROM estatisticas JOIN clans ON estatisticas.id_clan = clans.id \
            WHERE arquivado = 'False' \
            ORDER BY nome, data_hora DESC"
        )
    finally:
        db.fechar()

def resgatar_rank_mensal(data_inicio: date, data_fim: date):
    try:
        db = Conexao()
        
        # Não especificou mês; assume data mais recente.
        if data_inicio == None:
            fim = db.consultar(
                "SELECT DISTINCT ON (nome) nome, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total \
                FROM estatisticas JOIN clans ON estatisticas.id_clan = clans.id \
                WHERE arquivado = 'False' \
                ORDER BY nome, data_hora DESC"
            ) 

            mes_passado = fim[0].data_hora.date() - timedelta(days = 30)

            inicio = db.consultar(
                f"SELECT DISTINCT ON (nome) nome, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total \
                FROM estatisticas JOIN clans ON estatisticas.id_clan = clans.id \
                WHERE (data_hora BETWEEN '{mes_passado} 00:01:00' AND '{mes_passado} 23:59:00') \
                AND (arquivado = 'False')"
            )

            # Pega a data mais antiga disponível.
            if not inicio:
                inicio = db.consultar(
                    "SELECT DISTINCT ON (nome) nome, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total \
                    FROM estatisticas JOIN clans ON estatisticas.id_clan = clans.id \
                    WHERE arquivado = 'False' \
                    ORDER BY nome, data_hora"
                )
        else:
            hoje = datetime.now().date()
            
            if data_inicio > hoje:
                return -1
            
            if data_fim > hoje:
                return -2
            
            fim = db.consultar(
                f"SELECT DISTINCT ON (nome) nome, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total \
                FROM estatisticas JOIN clans ON estatisticas.id_clan = clans.id \
                WHERE (data_hora BETWEEN '{data_fim} 00:01:00' AND '{data_fim} 23:59:00') \
                AND (arquivado = 'False')"
            ) 

            if not fim:
                return -3

            inicio = db.consultar(
                f"SELECT DISTINCT ON (nome) nome, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total \
                FROM estatisticas JOIN clans ON estatisticas.id_clan = clans.id \
                WHERE (data_hora BETWEEN '{data_inicio} 00:01:00' AND '{data_inicio} 23:59:00') \
                AND (arquivado = 'False')"
            )

            if not inicio:
                return -4

        # Pegando um valor aleatório pra servir de referência pra data.
        data_hora_inicio = inicio[0][1].strftime('%d/%m/%Y')
        data_hora_fim = fim[0][1].strftime('%d/%m/%Y')

        return [
            data_hora_inicio,
            data_hora_fim,
            [
                [
                    f[0], # Nome
                    f[2] - i[2], # Quantos membros
                    f[3] - i[3], # Qual nível da fort
                    f[4] - i[4], # Qual nível total
                    f[5] - i[5], # Qual nível total de combate
                    f[6] - i[6] # Quanto de exp total
                ]
                for f, i in zip(fim, inicio)
                if f[6] != i[6] # Se teve algum XP feito nesse período.
            ] 
        ]
    finally:
        db.fechar()

def resgatar_rank_dxp(quantos_atras: int) -> list:
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
            
        xp_inicio = db.consultar(
            f"SELECT DISTINCT ON (nome) nome, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total \
            FROM estatisticas JOIN clans ON estatisticas.id_clan = clans.id \
            WHERE (data_hora BETWEEN '{inicio}' AND '{fim}') \
            AND (arquivado = 'False') \
            ORDER BY nome, data_hora"
        )

        # DXP começou mas ainda não houve a primeira coleta de XP.
        if not xp_inicio:
            return -3

        xp_fim = db.consultar(
            f"SELECT DISTINCT ON (nome) nome, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total \
            FROM estatisticas JOIN clans ON estatisticas.id_clan = clans.id \
            WHERE (data_hora BETWEEN '{inicio}' AND '{fim}') \
            AND (arquivado = 'False') \
            ORDER BY nome, data_hora DESC"
        )

        # Só houve uma coleta de XP desde o início do Double.
        if xp_inicio == xp_fim:
            return -3

        # Pegando um valor aleatório pra servir de referência pra data.
        data_hora_inicio = xp_inicio[0][1].strftime('%d/%m/%Y %H:%M')
        data_hora_fim = xp_fim[0][1].strftime('%d/%m/%Y %H:%M')

        return [
            data_hora_inicio,
            data_hora_fim,
            [
                [
                    f[0], # Nome
                    f[2] - i[2], # Quantos membros
                    f[3] - i[3], # Qual nível da fort
                    f[4] - i[4], # Qual nível total
                    f[5] - i[5], # Qual nível total de combate
                    f[6] - i[6] # Quanto de exp total
                ]
                for f, i in zip(fim, inicio)
            ]
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

def adicionar_estatisticas(lista: list[str]) -> None:
    db = Conexao()
    for clan in lista:
        db.manipular(
            f"INSERT INTO estatisticas (id_clan, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total) \
            VALUES ({clan[0]}, '{clan[1]}', {clan[2]}, {clan[3]}, {clan[4]}, {clan[5]}, {clan[6]})"
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