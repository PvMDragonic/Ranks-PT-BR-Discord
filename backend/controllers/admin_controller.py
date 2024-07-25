from datetime import datetime
from ..models import Conexao
from ..models import LogModel

class AdminController:
    """Responsável por controlar ações de acesso limitado no bot."""

    @staticmethod
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
        except Exception as e:
            LogModel.adicionar_log(f"[{datetime.now()}] Erro na consulta de nível de acesso: {e}")
            return False
        finally:
            db.fechar()

    @staticmethod
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
        except Exception as e:
            LogModel.adicionar_log(f"[{datetime.now()}] Erro ao adicionar novo moderador: {e}")
            return False
        finally:
            db.fechar()

    @staticmethod
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
            return db.manipular("DELETE FROM admins WHERE id_discord = %s", id_usuario)    
        except Exception as e:
            LogModel.adicionar_log(f"[{datetime.now()}] Erro ao remover um moderador: {e}")
            return False
        finally:
            db.fechar()

    @staticmethod
    def adicionar_dxp(data_comeco: datetime, data_fim: datetime) -> bool:
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
        except Exception as e:
            LogModel.adicionar_log(f"[{datetime.now()}] Erro ao adicionar novo DXP: {e}")
            return False
        finally:
            db.fechar()

    @staticmethod
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
        except Exception as e:
            LogModel.adicionar_log(f"[{datetime.now()}] Erro ao deletar um DXP: {e}")
            return None
        finally:
            db.fechar()

    @staticmethod
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

            if db.consultar("SELECT * FROM clans WHERE id = %s", id):
                return False

            db.manipular("INSERT INTO clans (id, arquivado) VALUES (%s, 'False')", id)
            ultimo_nome = db.consultar("SELECT nome FROM nomes WHERE id_clan = %s ORDER BY data_alterado DESC LIMIT 1", id)
            if ultimo_nome != nome:
                return db.manipular(
                    "INSERT INTO nomes (id_clan, nome, data_alterado) VALUES (%s, %s, %s)",
                    id, nome, datetime.now().date()
                )

            return False
        except Exception as e:
            LogModel.adicionar_log(f"[{datetime.now()}] Erro ao adicionar um clã: {e}")
            return False
        finally:
            db.fechar()

    @staticmethod
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
        except Exception as e:
            LogModel.adicionar_log(f"[{datetime.now()}] Erro ao remover um clã: {e}")
            return False
        finally:
            db.fechar()