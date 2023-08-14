from datetime import datetime, timedelta, date
import psycopg2

class Conexao(object):
    """Classe para conexão com o banco de dados."""  

    def __init__(self) -> None:
        self._db = psycopg2.connect(
            host = 'localhost', 
            database = 'clansptbr', 
            user = 'postgres',  
            password = 123456
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
        except Exception as e:
            adicionar_log(f"[{datetime.now()}] Erro durante manipulação: {e}")
            return False

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
            return cur.fetchall()
        except Exception as e:
            adicionar_log(f"[{datetime.now()}] Erro durante consulta: {e}")
            return None

    def fechar(self):
        self._db.close()

def resgatar_clans() -> list:
    """
    Retorna todos os clãs com seus nomes mais recentes.
    
    Retorna:
        list: 
            [(id_clan, nome), ...]
    """

    try:
        db = Conexao()
        return db.consultar("""
            SELECT DISTINCT ON (id_clan) id_clan, nome
            FROM nomes
            ORDER BY id_clan, data_alterado DESC
        """)
    finally:
        db.fechar()

def resgatar_rank_geral(data: date = None) -> list[tuple[str]]:
    """
    Retorna ranking com todos os clãs que não estejam arquivados.

    Parâmetros:
        data (opcional): date
            Data para pesquisar os registros.

    Retorna: 
        list: 
            [(nome, exp_total, data_hora), ...]
    """

    try:
        db = Conexao()

        if data:
            return db.consultar("""
                SELECT DISTINCT ON (n.nome) n.nome, e.exp_total, e.data_hora 
                FROM clans c
                JOIN (
                    SELECT DISTINCT ON (id_clan) id_clan, nome
                    FROM nomes
                    ORDER BY id_clan, data_alterado DESC
                ) n ON c.id = n.id_clan
                JOIN estatisticas e ON c.id = e.id_clan
                WHERE c.arquivado = false
                AND date_trunc('day', e.data_hora) = %s
            """, data)

        return db.consultar("""
            SELECT DISTINCT ON (n.nome) n.nome, e.exp_total, e.data_hora
            FROM clans c
            JOIN (
                SELECT DISTINCT ON (id_clan) id_clan, nome
                FROM nomes
                ORDER BY id_clan, data_alterado DESC
            ) n ON c.id = n.id_clan
            JOIN estatisticas e ON c.id = e.id_clan
            WHERE c.arquivado = false
            ORDER BY n.nome, e.data_hora DESC
        """)
    finally:
        db.fechar()

def resgatar_rank_mensal(data_inicio: date = None, data_fim: date = None) -> list[tuple[str]] | int:
    """
    Retorna ranking dos últimos 30 dias com todos os clãs que não estejam arquivados.

    Parâmetros:
        data_inicio (opcional): date
            Ponto inicial para o ranking;
        data_fim (opcional): date
            Ponto limite para o ranking.

    Retorna: 
        list: 
            [data_inicio, data_fim, [(nome, exp_total), ...]]
        int: 
            Código de erro caso dê problema com alguma data.
    """

    try:
        db = Conexao()
        
        # Não especificou mês; assume data mais recente.
        if data_inicio == None:
            fim = db.consultar("""
                SELECT DISTINCT ON (n.nome) n.nome, e.exp_total, e.data_hora
                FROM clans c
                JOIN (
                    SELECT DISTINCT ON (id_clan) id_clan, nome
                    FROM nomes
                    ORDER BY id_clan, data_alterado DESC
                ) n ON c.id = n.id_clan
                JOIN estatisticas e ON c.id = e.id_clan
                WHERE c.arquivado = false 
                ORDER BY n.nome, e.data_hora DESC
            """)

            mes_passado = fim[0][2].date() - timedelta(days = 30)

            inicio = db.consultar("""
                SELECT DISTINCT ON (n.nome) n.nome, e.exp_total, e.data_hora
                FROM clans c
                JOIN (
                    SELECT DISTINCT ON (id_clan) id_clan, nome
                    FROM nomes
                    ORDER BY id_clan, data_alterado DESC
                ) n ON c.id = n.id_clan
                JOIN estatisticas e ON c.id = e.id_clan
                WHERE c.arquivado = false
                AND date_trunc('day', e.data_hora) = %s
                ORDER BY n.nome, e.exp_total
            """, mes_passado)

            # Pega a data mais antiga disponível.
            if not inicio:
                inicio = db.consultar("""
                    SELECT DISTINCT ON (n.nome) n.nome, e.exp_total, e.data_hora
                    FROM clans c
                    JOIN (
                        SELECT DISTINCT ON (id_clan) id_clan, nome
                        FROM nomes
                        ORDER BY id_clan, data_alterado DESC
                    ) n ON c.id = n.id_clan
                    JOIN estatisticas e ON c.id = e.id_clan
                    WHERE c.arquivado = false
                    ORDER BY n.nome, e.data_hora
                """)
        else:
            hoje = datetime.now().date()
            
            if data_inicio > hoje:
                return -1
            
            if data_fim > hoje:
                return -2
            
            fim = db.consultar("""
                SELECT DISTINCT ON (n.nome) n.nome, e.exp_total, e.data_hora 
                FROM clans c 
                JOIN ( 
                    SELECT DISTINCT ON (id_clan) id_clan, nome 
                    FROM nomes 
                    ORDER BY id_clan, data_alterado DESC 
                ) n ON c.id = n.id_clan 
                JOIN estatisticas e ON c.id = e.id_clan 
                WHERE c.arquivado = false 
                AND date_trunc('day', e.data_hora) = %s
                ORDER BY n.nome, e.exp_total
            """, data_fim) 

            if not fim:
                return -3

            inicio = db.consultar("""
                SELECT DISTINCT ON (n.nome) n.nome, e.exp_total, e.data_hora
                FROM clans c
                JOIN (
                    SELECT DISTINCT ON (id_clan) id_clan, nome
                    FROM nomes
                    ORDER BY id_clan, data_alterado DESC
                ) n ON c.id = n.id_clan
                JOIN estatisticas e ON c.id = e.id_clan
                WHERE c.arquivado = false
                AND date_trunc('day', e.data_hora) = %s
                ORDER BY n.nome, e.exp_total
            """, data_inicio)

            if not inicio:
                return -4

        # Pegando um valor qualquer pra servir de referência pra data.
        data_hora_inicio = inicio[0][2].strftime('%d/%m/%Y')
        data_hora_fim = fim[0][2].strftime('%d/%m/%Y')
        rank = [
            (nome, final_exp - inicio_exp)
            for (nome, final_exp, _), (_, inicio_exp, _) in zip(fim, inicio)
            if final_exp != inicio_exp
        ]

        return [
            data_hora_inicio,
            data_hora_fim,
            rank
        ]
    finally:
        db.fechar()

def resgatar_rank_dxp(quantos_atras: int) -> list[tuple[str]] | int:
    """
    Retorna ranking dos últimos 30 dias com todos os clãs que não estejam arquivados.

    Parâmetros:
        quantos_atras (opcional): int
            Número de quantos DXPs atrás deve ser o DXP escolhido para o ranking.

    Retorna: 
        list: 
            [data_inicio, data_fim, [(nome, exp_total), ...]]
        int: 
            Código de erro caso dê problema com alguma data.
    """

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
            
        xp_inicio = db.consultar("""
            SELECT DISTINCT ON (n.nome) n.nome, e.exp_total, e.data_hora
            FROM clans c
            JOIN (
                SELECT DISTINCT ON (id_clan) id_clan, nome
                FROM nomes
                ORDER BY id_clan, data_alterado DESC
            ) n ON c.id = n.id_clan
            JOIN estatisticas e ON c.id = e.id_clan
            WHERE c.arquivado = false
            AND (data_hora BETWEEN %s AND %s)
            ORDER BY n.nome, e.exp_total
        """, inicio, fim)

        # DXP começou mas ainda não houve a primeira coleta de XP.
        if not xp_inicio:
            return -3

        xp_fim = db.consultar("""
            SELECT DISTINCT ON (n.nome) n.nome, e.exp_total, e.data_hora
            FROM clans c
            JOIN (
                SELECT DISTINCT ON (id_clan) id_clan, nome
                FROM nomes
                ORDER BY id_clan, data_alterado DESC
            ) n ON c.id = n.id_clan
            JOIN estatisticas e ON c.id = e.id_clan
            WHERE c.arquivado = false
            AND (data_hora BETWEEN %s AND %s)
            ORDER BY n.nome, e.exp_total DESC
        """, inicio, fim)

        # Só houve uma coleta de XP desde o início do Double.
        if xp_inicio == xp_fim:
            return -3

        # Pegando um valor qualquer pra servir de referência pra data.
        data_hora_inicio = xp_inicio[0][2].strftime('%d/%m/%Y %H:%M')
        data_hora_fim = xp_fim[0][2].strftime('%d/%m/%Y %H:%M')
        rank = [
            (nome, final_exp - inicio_exp)
            for (nome, final_exp, _), (_, inicio_exp, _) in zip(xp_fim, xp_inicio)
        ]

        return [
            data_hora_inicio,
            data_hora_fim,
            rank
        ]
    finally:
        db.fechar()

def resgatar_data_dxp() -> tuple[str]:
    """
    Retorna as informações do DXP que foi registrado por último.

    Retorna: 
        tuple: 
            (id, data_inicio, data_fim)
    """

    try:
        db = Conexao()
        datahora = db.consultar("SELECT * FROM dxp ORDER BY data_comeco DESC LIMIT 1")[0]
        return datahora
    finally:
        db.fechar()

def verificar_dxp(data_comeco: datetime, data_fim: datetime) -> bool:
    """
    Verifica se há um DXP registrado para o período entre duas datas.

    Parâmetros:
        data_comeco: datetime
            Data de início do DXP;
        data_fim: datetime
            Data de encerramento do DXP.

    Retorna: 
        bool: 
            Verdadeiro caso exista; Falso caso não.
    """

    try:
        db = Conexao()
        return db.consultar(
            "SELECT * FROM dxp WHERE (data_comeco <= %s) and (%s <= data_fim)",
            data_fim, data_comeco
        )
    finally:
        db.fechar()

def dxp_acontecendo() -> bool:
    """
    Verifica se há um DXP acontecendo.

    Retorna:
        bool:
            Verdadeiro caso esteja acontecendo; Falso caso não.
    """

    try:
        db = Conexao()
        inicio, fim = db.consultar("SELECT data_comeco, data_fim FROM dxp ORDER BY data_comeco DESC LIMIT 1")[0]
        return fim > datetime.now() > inicio
    finally:
        db.fechar()

def dxp_restante() -> str:
    """
    Retorna o tempo restante até o DXP mais recente acabar.

    Retorna:
        str:
            String já formatada com o tempo restante.
    """

    try:
        db = Conexao()
        fim = db.consultar("SELECT data_fim FROM dxp ORDER BY data_comeco DESC LIMIT 1")[0][0]
        restante = fim - datetime.now()

        if restante.days >= 1:
            return f"{restante.days} dias e {restante.seconds // 3600} horas restantes!"
        elif restante.seconds > 3600:
            return f"{restante.seconds // 3600} horas restantes!"
        elif 300 < restante.seconds < 3600:   
            return f"{restante.seconds // 60} minutos restantes!"     
        else:
            return f"{restante.seconds // 60} encerramento iminente!" 
    finally:
        db.fechar()

def adicionar_dxp(data_comeco: datetime, data_fim: datetime) -> None:
    """
    Adiciona um novo registro de DXP no banco de dados.

    Parâmetros:
        data_comeco: datetime
            Data de início do DXP.
        data_fim: datetime
            Data de encerramento do DXP.
    """

    try:
        db = Conexao()
        return db.manipular(
            "INSERT INTO dxp (data_comeco, data_fim) VALUES (%s, %s)",
            data_comeco, data_fim
        )
    finally:
        db.fechar()

def deletar_dxp() -> list[datetime] | None:
    """
    Remove e retorna os registros do último DXP registrado.

    Retorna:
        list:
            [data_comeco, data_fim]
        None:
            Caso não haja registro algum para ser deletado.
    """

    try:
        db = Conexao()
        query = db.consultar("SELECT data_comeco, data_fim FROM dxp ORDER BY id DESC LIMIT 1")
        
        if query:
            data_comeco, data_fim = query[0]
            db.manipular("DELETE FROM dxp WHERE data_comeco = %s AND data_fim = %s", data_comeco, data_fim)
            return [data_comeco, data_fim]
        
        return None
    finally:
        db.fechar()

def adicionar_estatisticas(lista: list[str]) -> None:
    """
    Adiciona novos registros de XP para os clãs no banco de dados.

    Parâmetros:
        lista: list
            [[id, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total], ...]
    """

    db = Conexao()
    for (id, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total) in lista:
        db.manipular(
            "INSERT INTO estatisticas (id_clan, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total) \
            VALUES (%s, %s, %s, %s, %s, %s, %s)",
            id, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total
        )
    db.fechar()

def adicionar_clans(clans: list[str]) -> None:
    """
    Adiciona novos clãs ao banco de dados.

    Parâmetros:
        clans: list
            [[id, nome], ...]
    """

    try:
        db = Conexao()
        for (id, nome) in clans:
            if not db.consultar("SELECT * FROM clans WHERE id = %s", id):
                db.manipular("INSERT INTO clans (id, arquivado) VALUES (%s, 'False')", id)
                continue
            
            ultimo_nome = db.consultar("SELECT nome FROM nomes WHERE id_clan = %s ORDER BY data_alterado DESC LIMIT 1", id)
            if ultimo_nome != nome:
                db.manipular(
                    "INSERT INTO nomes (id_clan, nome, data_alteracao) VALUES (%s, %s, %s)",
                    id, nome, datetime.now().date()
                )
    finally:
        db.fechar()

def adicionar_clan(id: int, nome: str) -> bool:
    """
    Adiciona um clã novo ao banco de dados, individualmente.

    Parâmetros:
        id: int
            Atributo 'clanId' retirado da página do clã no site do RuneScape.
        nome: str
            Nome do clã.

    Retorna:
        bool:
            Verdadeiro caso tenha sido registrado; Falso caso não.
    """

    try:
        db = Conexao()

        if not db.consultar("SELECT * FROM clans WHERE id = %s", id):
            db.manipular("INSERT INTO clans (id, arquivado) VALUES (%s, 'False')", id)
        else:
            return False

        ultimo_nome = db.consultar("SELECT nome FROM nomes WHERE id_clan = %s ORDER BY data_alterado DESC LIMIT 1", id)
        if ultimo_nome != nome:
            return db.manipular(
                "INSERT INTO nomes (id_clan, nome, data_alterado) VALUES (%s, %s, %s)",
                id, nome, datetime.now().date()
            )

        return False
    finally:
        db.fechar()

def remover_clan(clan: str) -> bool:
    """
    Arquiva um clã registrado no banco de dados, individualmente.

    Parâmetros:
        clan: str
            Nome do clã a ser removido/arquivado.

    Retorna:
        bool:
            Verdadeiro caso o clã seja encontrado e arquivado; Falso caso não.
    """

    try:
        db = Conexao()
        query = db.consultar("SELECT id_clan FROM nomes WHERE nome = %s", clan)
        if query:
            return db.manipular("UPDATE clans SET arquivado = 'True' WHERE id = %s", query[0])
        return False
    finally:
        db.fechar()

def adicionar_log(mensagem: str) -> None:
    """
    Adiciona um novo registro no arquivo de log e depois exibe no terminal.

    Parâmetros:
        mensagem: str
            String a ser salva no log.
    """

    with open('log.txt', 'a') as arqv:
        arqv.writelines(f'{mensagem}\n')
        print(mensagem)

def possui_nv_acesso(nv_requerido: int, id_usuario: int) -> bool:
    """
    Verifica se um id de usuário de Discord tem nível de acesso.

    Parâmetros:
        nv_requerido: int
            Qual nível é requerido para a ação.
        id_usuario: int
            ID do Discord do usuário em questão.
    """

    try:
        db = Conexao()
        nv_acesso = db.consultar("SELECT nv_acesso FROM admins WHERE id_discord = %s", id_usuario)
        if nv_acesso:
            return nv_requerido <= nv_acesso[0][0]
        return False
    finally:
        db.fechar()

def adicionar_moderador(id_usuario: int) -> bool:
    """
    Adiciona um novo ID de Discord ao banco de dados como nível 1 de acesso.

    Parâmetros:
        id_usuario: int
            ID do Discord do usuário em questão.

    Retorna:
        bool:
            Verdadeiro se o registro acontecer; Falso caso contrário.
    """

    try:
        db = Conexao()
        if not db.consultar("SELECT * FROM admins WHERE id_discord = %s", id_usuario):
            return db.manipular("INSERT INTO admins(id_discord, nv_acesso) VALUES (%s, 1)", id_usuario)
        return False
    finally:
        db.fechar()

def remover_moderador(id_usuario: int) -> bool:
    """
    Remove um ID de Discord da lista de moderadores do banco de dados.

    Parâmetros:
        id_usuario: int
            ID do Discord do usuário em questão.

    Retorna:
        bool:
            Verdadeiro se for removido; Falso caso contrário.
    """

    try:
        db = Conexao()
        if db.consultar("SELECT * FROM admins WHERE id_discord = %s", id_usuario):
            return db.manipular("DELETE FROM admins WHERE id_discord = %s", id_usuario)        
        return False
    finally:
        db.fechar()