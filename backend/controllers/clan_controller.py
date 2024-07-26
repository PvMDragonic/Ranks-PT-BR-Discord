from datetime import datetime, timedelta, date
from ..models import Conexao, LogModel

class ClanController:
    """Responsável pelos métodos de resgatar e manipular dados de clã(s)."""

    @staticmethod
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
        except Exception as e:
            LogModel.adicionar_log(f"[{datetime.now()}] Erro na consulta de clãs: {e}")
            return []
        finally:
            db.fechar()

    @staticmethod
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
        except Exception as e:
            LogModel.adicionar_log(f"[{datetime.now()}] Erro ao adicionar clãs em sequência: {e}")
        finally:
            db.fechar()

    @staticmethod
    def adicionar_estatisticas(lista: list[str]) -> None:
        """
        Adiciona novos registros de XP para os clãs no banco de dados.

        Parâmetros:
            lista: list
                [[id, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total], ...]
        """

        try:
            db = Conexao()
            for (id, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total) in lista:
                db.manipular(
                    "INSERT INTO estatisticas (id_clan, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total) \
                    VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    id, data_hora, membros, nv_fort, nv_total, nv_cb_total, exp_total
                )
        except Exception as e:
            LogModel.adicionar_log(f"[{datetime.now()}] Erro ao adicionar estatísticas em sequência: {e}")
        finally:
            db.fechar()

    @staticmethod
    def resgatar_rank_geral(data: date = None) -> list[tuple[str, int, datetime]] | None:
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
        except Exception as e:
            LogModel.adicionar_log(f"[{datetime.now()}] Erro no ranking geral: {e}")
            return None
        finally:
            db.fechar()

    @staticmethod
    def resgatar_rank_mensal(data_inicio: date = None, data_fim: date = None) -> tuple[datetime, datetime, list[tuple[str, int]]] | int:
        """
        Retorna ranking dos últimos 30 dias com todos os clãs que não estejam arquivados.

        Parâmetros:
            data_inicio (opcional): date
                Ponto inicial para o ranking;
            data_fim (opcional): date
                Ponto limite para o ranking.

        Retorna: 
            tuple: 
                (data_inicio, data_fim, [(nome, exp_total), ...])
            int: 
                Código de erro caso dê problema com alguma data.
        """
        
        try:
            db = Conexao()

            if not data_inicio:
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

                mes_passado = fim[0][2].date() - timedelta(days=30)

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
                
            data_hora_inicio = inicio[0][2].strftime('%d/%m/%Y')
            data_hora_fim = fim[0][2].strftime('%d/%m/%Y')

            rank = [
                (nome, final_exp - inicio_exp)
                for (nome, final_exp, _), (_, inicio_exp, _) in zip(fim, inicio)
                if final_exp != inicio_exp
            ]
            
            return (
                data_hora_inicio,
                data_hora_fim,
                rank
            )
        except Exception as e:
            LogModel.adicionar_log(f"[{datetime.now()}] Erro no ranking mensal: {e}")
            return -5
        finally:
            db.fechar()

    @staticmethod
    def resgatar_rank_dxp(quantos_atras: int) -> tuple[datetime, datetime, tuple[str, int]] | int:
        """
        Retorna ranking dos últimos 30 dias com todos os clãs que não estejam arquivados.

        Parâmetros:
            quantos_atras (opcional): int
                Número de quantos DXPs atrás deve ser o DXP escolhido para o ranking.

        Retorna: 
            tuple: 
                (data_inicio, data_fim, [(nome, exp_total), ...])
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

            # Usa o clã em primeiro lugar como base pras datas.4
            data_hora_inicio = max(xp_inicio, key = lambda x: x[1])[2].strftime('%d/%m/%Y %H:%M')
            data_hora_fim = max(xp_fim, key = lambda x: x[1])[2].strftime('%d/%m/%Y %H:%M')
            
            rank = [
                (nome, final_exp - inicio_exp)
                for (nome, final_exp, _), (_, inicio_exp, _) in zip(xp_fim, xp_inicio)
            ]

            return (
                data_hora_inicio,
                data_hora_fim,
                rank
            )
        except Exception as e:
            LogModel.adicionar_log(f"[{datetime.now()}] Erro no ranking DXP: {e}")
            return -4
        finally:
            db.fechar()

    @staticmethod
    def resgatar_data_dxp() -> tuple[int, datetime, datetime] | None:
        """
        Retorna as informações do DXP que foi registrado por último.

        Retorna: 
            tuple: 
                (id, data_inicio, data_fim)
        """

        try:
            db = Conexao()
            return db.consultar("SELECT * FROM dxp ORDER BY data_comeco DESC LIMIT 1")[0]
        except Exception as e:
            LogModel.adicionar_log(f"[{datetime.now()}] Erro ao resgatar dados do DXP mais recene: {e}")
            return None
        finally:
            db.fechar()

    @staticmethod
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
        except Exception as e:
            LogModel.adicionar_log(f"[{datetime.now()}] Erro na verificação da existência de DXP: {e}")
            return False
        finally:
            db.fechar()

    @staticmethod
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
        except Exception as e:
            LogModel.adicionar_log(f"[{datetime.now()}] Erro na verificação de DXP acontecendo: {e}")
            return False
        finally:
            db.fechar()

    @staticmethod
    def dxp_restante() -> str:
        """
        Retorna o tempo restante até o DXP em ocorrência acabar.

        Retorna:
            str:
                String já formatada com o tempo restante.
        """

        try:
            db = Conexao()
            fim = db.consultar("SELECT data_fim FROM dxp ORDER BY data_comeco DESC LIMIT 1")[0][0]
            restante = fim - datetime.now()

            if restante.days >= 2:
                return f"{restante.days} dias e {restante.seconds // 3600} horas restantes!"
            elif restante.days >= 1:
                return f"1 dia e {restante.seconds // 3600} horas restantes!"
            elif restante.seconds > 7200:
                return f"{restante.seconds // 3600} horas restantes!"
            elif restante.seconds > 3600:
                return f"1 hora restante!"
            elif restante.seconds > 300:   
                return f"{restante.seconds // 60} minutos restantes!"
            else:
                return "Encerramento iminente!"
        except Exception as e:
            LogModel.adicionar_log(f"[{datetime.now()}] Erro na verificação de DXP restante: {e}")
            return "Tempo restante desconhecido" 
        finally:
            db.fechar()

    @staticmethod
    def dxp_fim_eminente() -> bool:
        """
        Retorna se o DXP está a 1 hora ou menos do fim.

        Retorna:
            bool:
                Verdadeiro caso esteja no fim; Falso caso não.
        """

        try:
            db = Conexao()
            fim = db.consultar("SELECT data_fim FROM dxp ORDER BY data_comeco DESC LIMIT 1")[0][0]
            restante = fim - datetime.now()
            return restante.total_seconds() <= 3600
        except Exception as e:
            LogModel.adicionar_log(f"[{datetime.now()}] Erro na verificação de DXP em fim eminente: {e}")
            return False
        finally:
            db.fechar()