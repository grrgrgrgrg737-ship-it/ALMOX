import sqlite3
import os
import datetime
from contextlib import contextmanager
import logging

# Configuração do logging
logging.basicConfig(filename='almoxarifado.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')

DB_PATH = "almoxarifado.db"

@contextmanager
def db_connect(db_path=None):
    if db_path is None: db_path = DB_PATH
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = dict_factory
        conn.execute("PRAGMA foreign_keys = ON;")
        yield conn
    except sqlite3.Error as e:
        logging.error(f"Erro de conexão com o banco de dados: {e}")
        raise
    finally:
        if 'conn' in locals() and conn: conn.close()

def dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

# --- Funções CRUD: Itens ---
def get_all_items():
    with db_connect() as conn:
        query = """
            SELECT
                i.id, i.codigo, i.nome, i.descricao, i.unidade,
                i.estoque_minimo, i.preco_unitario, i.fornecedor_id,
                i.data_cadastro,
                COALESCE(f.nome, 'N/A') as fornecedor_nome
            FROM itens i
            LEFT JOIN fornecedores f ON i.fornecedor_id = f.id
            ORDER BY i.nome
        """
        return conn.cursor().execute(query).fetchall()

def get_item_by_id(item_id):
    with db_connect() as conn:
        return conn.cursor().execute("SELECT * FROM itens WHERE id = ?", (item_id,)).fetchone()

def get_item_by_code(codigo):
    with db_connect() as conn:
        return conn.cursor().execute("SELECT * FROM itens WHERE codigo = ?", (codigo,)).fetchone()

def add_item(codigo, nome, descricao, unidade, estoque_minimo, preco_unitario, fornecedor_id, data_cadastro):
    try:
        with db_connect() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO itens (codigo, nome, descricao, unidade, estoque_minimo, preco_unitario, fornecedor_id, data_cadastro) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (codigo, nome, descricao, unidade, estoque_minimo, preco_unitario, fornecedor_id, data_cadastro))
            conn.commit()
            return True, "Item cadastrado com sucesso!"
    except sqlite3.IntegrityError:
        return False, f"Erro: Item com o código '{codigo}' já existe."
    except Exception as e:
        return False, f"Erro ao cadastrar item: {e}"

def update_item(item_id, codigo, nome, descricao, unidade, estoque_minimo, preco_unitario, fornecedor_id, data_cadastro):
    try:
        with db_connect() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE itens SET codigo=?, nome=?, descricao=?, unidade=?, estoque_minimo=?, preco_unitario=?, fornecedor_id=?, data_cadastro=? WHERE id=?",
                        (codigo, nome, descricao, unidade, estoque_minimo, preco_unitario, fornecedor_id, data_cadastro, item_id))
            conn.commit()
            return True, "Item atualizado com sucesso!"
    except sqlite3.IntegrityError:
        return False, f"Erro: Já existe um item com o código '{codigo}'."
    except Exception as e:
        return False, f"Erro ao atualizar item: {e}"

def delete_item(item_id):
    try:
        with db_connect() as conn:
            conn.cursor().execute("DELETE FROM itens WHERE id=?", (item_id,))
            conn.commit()
            return True, "Item excluído com sucesso!"
    except sqlite3.IntegrityError:
        return False, "Erro: Não é possível excluir, pois o item possui movimentações."
    except Exception as e:
        return False, f"Erro ao excluir item: {e}"

# --- Funções CRUD: Depósitos ---
def get_all_depositos():
    with db_connect() as conn:
        return conn.cursor().execute("SELECT * FROM depositos ORDER BY nome").fetchall()

def get_deposito_by_id(deposito_id):
     with db_connect() as conn:
        return conn.cursor().execute("SELECT * FROM depositos WHERE id = ?", (deposito_id,)).fetchone()

def get_deposito_by_name(nome):
    with db_connect() as conn:
        return conn.cursor().execute("SELECT * FROM depositos WHERE nome = ?", (nome,)).fetchone()

def add_deposito(nome, localizacao):
    try:
        with db_connect() as conn:
            conn.cursor().execute("INSERT INTO depositos (nome, localizacao) VALUES (?, ?)", (nome, localizacao))
            conn.commit()
        return True, "Depósito adicionado com sucesso."
    except sqlite3.IntegrityError:
        return False, f"Erro: Depósito com o nome '{nome}' já existe."
    except Exception as e:
        return False, f"Erro ao adicionar depósito: {e}"

def update_deposito(deposito_id, nome, localizacao):
    try:
        with db_connect() as conn:
            conn.cursor().execute("UPDATE depositos SET nome = ?, localizacao = ? WHERE id = ?", (nome, localizacao, deposito_id))
            conn.commit()
        return True, "Depósito atualizado com sucesso."
    except sqlite3.IntegrityError:
        return False, f"Erro: Já existe um depósito com o nome '{nome}'."
    except Exception as e:
        return False, f"Erro ao atualizar depósito: {e}"

def delete_deposito(deposito_id):
    try:
        with db_connect() as conn:
            conn.cursor().execute("DELETE FROM depositos WHERE id = ?", (deposito_id,))
            conn.commit()
        return True, "Depósito excluído com sucesso."
    except sqlite3.IntegrityError:
        return False, "Erro: Não é possível excluir. O depósito tem itens associados."
    except Exception as e:
        return False, f"Erro ao excluir depósito: {e}"

# --- Funções CRUD: Fornecedores ---
def get_all_fornecedores():
    with db_connect() as conn:
        return conn.cursor().execute("SELECT * FROM fornecedores ORDER BY nome").fetchall()

def get_fornecedor_by_id(fornecedor_id):
    with db_connect() as conn:
        return conn.cursor().execute("SELECT * FROM fornecedores WHERE id = ?", (fornecedor_id,)).fetchone()

def get_fornecedor_by_name(nome):
    with db_connect() as conn:
        return conn.cursor().execute("SELECT * FROM fornecedores WHERE nome = ?", (nome,)).fetchone()

def add_fornecedor(nome, contato, telefone, email, prazo_entrega):
    try:
        with db_connect() as conn:
            conn.cursor().execute("INSERT INTO fornecedores (nome, contato, telefone, email, prazo_entrega) VALUES (?, ?, ?, ?, ?)", (nome, contato, telefone, email, prazo_entrega))
            conn.commit()
        return True, "Fornecedor adicionado com sucesso."
    except sqlite3.IntegrityError:
        return False, f"Erro: Fornecedor com o nome '{nome}' já existe."
    except Exception as e:
        return False, f"Erro ao adicionar fornecedor: {e}"

def update_fornecedor(fornecedor_id, nome, contato, telefone, email, prazo_entrega):
    try:
        with db_connect() as conn:
            conn.cursor().execute("UPDATE fornecedores SET nome = ?, contato = ?, telefone = ?, email = ?, prazo_entrega = ? WHERE id = ?", (nome, contato, telefone, email, prazo_entrega, fornecedor_id))
            conn.commit()
        return True, "Fornecedor atualizado com sucesso."
    except sqlite3.IntegrityError:
        return False, f"Erro: Já existe um fornecedor com o nome '{nome}'."
    except Exception as e:
        return False, f"Erro ao atualizar fornecedor: {e}"

def delete_fornecedor(fornecedor_id):
    try:
        with db_connect() as conn:
            conn.cursor().execute("DELETE FROM fornecedores WHERE id = ?", (fornecedor_id,))
            conn.commit()
        return True, "Fornecedor excluído com sucesso."
    except sqlite3.IntegrityError:
        return False, "Erro: Não é possível excluir. O fornecedor está associado a itens."
    except Exception as e:
        return False, f"Erro ao excluir fornecedor: {e}"

# --- Funções CRUD: Técnicos ---
def get_all_tecnicos():
    with db_connect() as conn:
        return conn.cursor().execute("SELECT * FROM tecnicos ORDER BY nome").fetchall()

def get_tecnico_by_id(tecnico_id):
    with db_connect() as conn:
        return conn.cursor().execute("SELECT * FROM tecnicos WHERE id = ?", (tecnico_id,)).fetchone()

def get_tecnico_by_matricula(matricula):
    with db_connect() as conn:
        return conn.cursor().execute("SELECT * FROM tecnicos WHERE matricula = ?", (matricula,)).fetchone()

def add_tecnico(nome, matricula, setor):
    try:
        with db_connect() as conn:
            conn.cursor().execute("INSERT INTO tecnicos (nome, matricula, setor) VALUES (?, ?, ?)", (nome, matricula, setor))
            conn.commit()
        return True, "Técnico adicionado com sucesso."
    except sqlite3.IntegrityError:
        return False, f"Erro: Técnico com a matrícula '{matricula}' já existe."
    except Exception as e:
        return False, f"Erro ao adicionar técnico: {e}"

def update_tecnico(tecnico_id, nome, matricula, setor):
    try:
        with db_connect() as conn:
            conn.cursor().execute("UPDATE tecnicos SET nome = ?, matricula = ?, setor = ? WHERE id = ?", (nome, matricula, setor, tecnico_id))
            conn.commit()
            return True, "Técnico atualizado com sucesso."
    except sqlite3.IntegrityError:
        return False, f"Erro: Já existe um técnico com a matrícula '{matricula}'."
    except Exception as e:
        return False, f"Erro ao atualizar técnico: {e}"

def delete_tecnico(tecnico_id):
    try:
        with db_connect() as conn:
            conn.cursor().execute("DELETE FROM tecnicos WHERE id = ?", (tecnico_id,))
            conn.commit()
        return True, "Técnico excluído com sucesso."
    except sqlite3.IntegrityError:
        return False, "Erro: Não é possível excluir, pois o técnico tem movimentações ou empréstimos associados."
    except Exception as e:
        return False, f"Erro ao excluir técnico: {e}"

# --- Funções CRUD: Ferramentas ---
def get_all_ferramentas():
    with db_connect() as conn:
        return conn.cursor().execute("SELECT * FROM ferramentas ORDER BY nome").fetchall()

def get_ferramenta_by_id(ferramenta_id):
    with db_connect() as conn:
        return conn.cursor().execute("SELECT * FROM ferramentas WHERE id = ?", (ferramenta_id,)).fetchone()

def get_ferramenta_by_codigo(codigo):
    with db_connect() as conn:
        return conn.cursor().execute("SELECT * FROM ferramentas WHERE codigo = ?", (codigo,)).fetchone()

def add_ferramenta(codigo, nome, descricao, status, localizacao, data_aquisicao):
    try:
        with db_connect() as conn:
            conn.cursor().execute("INSERT INTO ferramentas (codigo, nome, descricao, status, localizacao, data_aquisicao) VALUES (?, ?, ?, ?, ?, ?)",
                                  (codigo, nome, descricao, status, localizacao, data_aquisicao))
            conn.commit()
            return True, "Ferramenta cadastrada com sucesso!"
    except sqlite3.IntegrityError:
        return False, f"Erro: Ferramenta com código '{codigo}' já existe."
    except Exception as e:
        return False, f"Erro ao cadastrar ferramenta: {e}"

def update_ferramenta(ferramenta_id, codigo, nome, descricao, status, localizacao, data_aquisicao):
    try:
        with db_connect() as conn:
            conn.cursor().execute("UPDATE ferramentas SET codigo=?, nome=?, descricao=?, status=?, localizacao=?, data_aquisicao=? WHERE id=?",
                                  (codigo, nome, descricao, status, localizacao, data_aquisicao, ferramenta_id))
            conn.commit()
            return True, "Ferramenta atualizada com sucesso!"
    except sqlite3.IntegrityError:
        return False, f"Erro: Já existe uma ferramenta com o código '{codigo}'."
    except Exception as e:
        return False, f"Erro ao atualizar ferramenta: {e}"

def delete_ferramenta(ferramenta_id):
    try:
        with db_connect() as conn:
            conn.cursor().execute("DELETE FROM ferramentas WHERE id = ?", (ferramenta_id,))
            conn.commit()
            return True, "Ferramenta excluída com sucesso!"
    except sqlite3.IntegrityError:
        return False, "Erro: Não é possível excluir, a ferramenta possui empréstimos associados."
    except Exception as e:
        return False, f"Erro ao excluir ferramenta: {e}"

# --- Funções de Movimentação e Estoque ---
def get_estoque_by_item_deposito(item_id, deposito_id):
    with db_connect() as conn:
        return conn.cursor().execute("SELECT * FROM estoque WHERE item_id = ? AND deposito_id = ?", (item_id, deposito_id)).fetchone()

def get_estoque_geral(search_term=None):
    with db_connect() as conn:
        query = """
            SELECT e.item_id, e.deposito_id, e.quantidade, i.nome as item_nome, i.codigo as item_codigo, d.nome as deposito_nome
            FROM estoque e JOIN itens i ON e.item_id = i.id JOIN depositos d ON e.deposito_id = d.id
        """
        params = []
        if search_term:
            query += " WHERE i.nome LIKE ? OR i.codigo LIKE ?"
            params.extend([f"%{search_term}%", f"%{search_term}%"])
        query += " ORDER BY i.nome, d.nome"
        return conn.cursor().execute(query, params).fetchall()

def _registrar_movimentacao(item_id, deposito_id, tipo, quantidade, data, origem_destino, observacoes, conn, tecnico_id=None):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO movimentacoes (item_id, deposito_id, tipo_movimentacao, quantidade, data_movimentacao, origem_destino, observacoes, tecnico_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (item_id, deposito_id, tipo, quantidade, data, origem_destino, observacoes, tecnico_id))

def register_entry(item_id, quantidade, deposito_id, data, origem=None, observacao=None):
    with db_connect() as conn:
        _registrar_movimentacao(item_id, deposito_id, 'entrada', quantidade, data, origem, observacao, conn)
        conn.cursor().execute("""
            INSERT INTO estoque (item_id, deposito_id, quantidade) VALUES (?, ?, ?)
            ON CONFLICT(item_id, deposito_id) DO UPDATE SET quantidade = quantidade + excluded.quantidade;
        """, (item_id, deposito_id, quantidade))
        conn.commit()
    return True, "Entrada registrada com sucesso!"

def register_exit(item_id, quantidade, deposito_id, data, destino=None, observacao=None, tecnico_id=None):
    try:
        with db_connect() as conn:
            cur = conn.cursor()
            stock_row = cur.execute("SELECT quantidade FROM estoque WHERE item_id = ? AND deposito_id = ?", (item_id, deposito_id)).fetchone()
            if not stock_row or stock_row['quantidade'] < quantidade:
                return False, "Quantidade em estoque insuficiente!"
            _registrar_movimentacao(item_id, deposito_id, 'saida', quantidade, data, destino, observacao, conn, tecnico_id=tecnico_id)
            cur.execute("UPDATE estoque SET quantidade = quantidade - ? WHERE item_id = ? AND deposito_id = ?", (quantidade, item_id, deposito_id))
            conn.commit()
        return True, "Saída registrada com sucesso."
    except Exception as e:
        return False, f"Erro ao registrar saída: {e}"

def ajustar_estoque(item_id, deposito_id, quantidade_ajuste, observacao):
    data_hoje = datetime.date.today().strftime("%Y-%m-%d")
    if quantidade_ajuste == 0: return True, "Nenhum ajuste necessário."
    tipo_mov = 'ajuste_entrada' if quantidade_ajuste > 0 else 'ajuste_saida'
    with db_connect() as conn:
        _registrar_movimentacao(item_id, deposito_id, tipo_mov, abs(quantidade_ajuste), data_hoje, "Inventário", observacao, conn)
        conn.cursor().execute("""
            INSERT INTO estoque (item_id, deposito_id, quantidade) VALUES (?, ?, ?)
            ON CONFLICT(item_id, deposito_id) DO UPDATE SET quantidade = quantidade + excluded.quantidade;
        """, (item_id, deposito_id, quantidade_ajuste))
        conn.commit()
    return True, "Estoque ajustado com sucesso."

# --- Funções de Empréstimos ---
def add_emprestimo_ferramenta(ferramenta_id, tecnico_id, data_emprestimo, data_devolucao_prevista, observacoes):
    try:
        with db_connect() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO emprestimos_ferramentas (ferramenta_id, tecnico_id, data_emprestimo, data_devolucao_prevista, observacoes, status) VALUES (?, ?, ?, ?, ?, 'Emprestado')",
                        (ferramenta_id, tecnico_id, data_emprestimo, data_devolucao_prevista, observacoes))
            loan_id = cur.lastrowid
            conn.commit()
            return True, "Empréstimo registrado com sucesso!", loan_id
    except Exception as e:
        return False, f"Erro ao registrar empréstimo: {e}", None

def get_emprestimo_ferramenta_by_id(emprestimo_id):
    with db_connect() as conn:
        return conn.cursor().execute("SELECT ef.*, f.codigo AS ferramenta_codigo, f.nome AS ferramenta_nome, t.nome AS tecnico_nome FROM emprestimos_ferramentas ef JOIN ferramentas f ON ef.ferramenta_id = f.id JOIN tecnicos t ON ef.tecnico_id = t.id WHERE ef.id = ?",
                                      (emprestimo_id,)).fetchone()

def get_emprestimos_ferramentas(status_filter=None, ferramenta_id=None):
    with db_connect() as conn:
        query = "SELECT ef.id, f.codigo AS ferramenta_codigo, f.nome AS ferramenta_nome, t.nome AS tecnico_nome, ef.data_emprestimo, ef.data_devolucao_prevista, ef.data_devolucao_real, ef.observacoes, ef.status, ef.ferramenta_id, ef.tecnico_id FROM emprestimos_ferramentas ef JOIN ferramentas f ON ef.ferramenta_id = f.id JOIN tecnicos t ON ef.tecnico_id = t.id WHERE 1=1"
        params = []
        if status_filter and status_filter != "Todos":
            if status_filter == "Atrasado": query += " AND ef.status = 'Emprestado' AND ef.data_devolucao_prevista < DATE('now')"
            else:
                query += " AND ef.status = ?"
                params.append(status_filter)
        if ferramenta_id is not None and ferramenta_id != -1:
            query += " AND ef.ferramenta_id = ?"
            params.append(ferramenta_id)
        query += " ORDER BY ef.data_emprestimo DESC, ef.id DESC"
        return conn.cursor().execute(query, params).fetchall()

def update_emprestimo_ferramenta(emprestimo_id, ferramenta_id, tecnico_id, data_emprestimo, data_devolucao_prevista, data_devolucao_real, observacoes, status):
    try:
        with db_connect() as conn:
            conn.cursor().execute("UPDATE emprestimos_ferramentas SET ferramenta_id = ?, tecnico_id = ?, data_emprestimo = ?, data_devolucao_prevista = ?, data_devolucao_real = ?, observacoes = ?, status = ? WHERE id = ?",
                                  (ferramenta_id, tecnico_id, data_emprestimo, data_devolucao_prevista, data_devolucao_real, observacoes, status, emprestimo_id))
            conn.commit()
            return True, "Empréstimo atualizado com sucesso!"
    except Exception as e:
        return False, f"Erro ao atualizar empréstimo: {e}"

# --- Funções de Relatórios e Inteligência ---
def get_itens_abaixo_do_minimo():
    with db_connect() as conn:
        return conn.cursor().execute("""
            SELECT i.id, i.codigo, i.nome, i.estoque_minimo, COALESCE(SUM(e.quantidade), 0) as total_estoque
            FROM itens i LEFT JOIN estoque e ON i.id = e.item_id
            GROUP BY i.id, i.codigo, i.nome, i.estoque_minimo
            HAVING total_estoque < i.estoque_minimo
        """).fetchall()

def get_emprestimos_atrasados():
    with db_connect() as conn:
        today = datetime.date.today().strftime("%Y-%m-%d")
        return conn.cursor().execute("""
            SELECT ef.*, f.nome as ferramenta_nome, t.nome as tecnico_nome
            FROM emprestimos_ferramentas ef
            JOIN ferramentas f ON ef.ferramenta_id = f.id
            JOIN tecnicos t ON ef.tecnico_id = t.id
            WHERE ef.status = 'Emprestado' AND ef.data_devolucao_prevista < ?
        """, (today,)).fetchall()

def get_movimentacoes_recentes(limit=5):
    with db_connect() as conn:
        return conn.cursor().execute("""
            SELECT m.tipo_movimentacao, m.quantidade, i.nome as item_nome
            FROM movimentacoes m JOIN itens i ON m.item_id = i.id
            ORDER BY m.id DESC LIMIT ?
        """, (limit,)).fetchall()

def get_movimentacoes(start_date, end_date, item_id=None, deposito_id=None, tipo_movimentacao=None, origem_destino_filter=None):
    with db_connect() as conn:
        query = "SELECT * FROM movimentacoes WHERE data_movimentacao BETWEEN ? AND ?"
        params = [start_date, end_date]
        if item_id is not None and item_id != -1: query += " AND item_id = ?"; params.append(item_id)
        if deposito_id is not None and deposito_id != -1: query += " AND deposito_id = ?"; params.append(deposito_id)
        if tipo_movimentacao and tipo_movimentacao != "Todos": query += " AND tipo_movimentacao = ?"; params.append(tipo_movimentacao.lower())
        if origem_destino_filter and origem_destino_filter != "Todos": query += " AND origem_destino LIKE ?"; params.append(f"%{origem_destino_filter}%")
        query += " ORDER BY data_movimentacao DESC, id DESC"
        return conn.cursor().execute(query, params).fetchall()

def get_consumo_por_item(start_date, end_date, item_id=None, origem_destino_filter=None):
    with db_connect() as conn:
        query = "SELECT m.item_id, i.codigo, i.nome, SUM(m.quantidade) as total_consumido FROM movimentacoes m JOIN itens i ON m.item_id = i.id WHERE m.tipo_movimentacao = 'saida' AND m.data_movimentacao BETWEEN ? AND ?"
        params = [start_date, end_date]
        if item_id is not None and item_id != -1:
            query += " AND m.item_id = ?"
            params.append(item_id)
        if origem_destino_filter and origem_destino_filter != "Todos":
            query += " AND m.origem_destino LIKE ?"
            params.append(f"%{origem_destino_filter}%")
        query += " GROUP BY m.item_id, i.codigo, i.nome ORDER BY total_consumido DESC"
        return conn.cursor().execute(query, params).fetchall()

def get_consumo_por_tecnico(start_date, end_date, tecnico_id=None, item_id=None):
    with db_connect() as conn:
        query = """
            SELECT t.nome as tecnico_nome, SUM(m.quantidade) as total_consumido
            FROM movimentacoes m
            JOIN tecnicos t ON m.tecnico_id = t.id
            WHERE m.tipo_movimentacao IN ('saida', 'ajuste_saida') AND m.data_movimentacao BETWEEN ? AND ?
        """
        params = [start_date, end_date]
        if tecnico_id is not None and tecnico_id != -1:
            query += " AND m.tecnico_id = ?"
            params.append(tecnico_id)
        if item_id is not None and item_id != -1:
            query += " AND m.item_id = ?"
            params.append(item_id)
        query += " GROUP BY t.nome ORDER BY total_consumido DESC"
        return conn.cursor().execute(query, params).fetchall()

def get_all_origem_destino():
    with db_connect() as conn:
        return [row["origem_destino"] for row in conn.cursor().execute("SELECT DISTINCT origem_destino FROM movimentacoes WHERE origem_destino IS NOT NULL AND origem_destino != '' ORDER BY origem_destino")]

def get_analise_consumo_valorado(start_date, end_date):
    with db_connect() as conn:
        query = """
            SELECT i.id as item_id, i.nome as nome, i.codigo as codigo, SUM(m.quantidade) * i.preco_unitario as valor_consumo
            FROM movimentacoes m JOIN itens i ON m.item_id = i.id
            WHERE m.tipo_movimentacao = 'saida' AND i.preco_unitario > 0 AND m.data_movimentacao BETWEEN ? AND ?
            GROUP BY i.id, i.nome, i.codigo, i.preco_unitario
            HAVING valor_consumo IS NOT NULL
        """
        return conn.cursor().execute(query, (start_date, end_date)).fetchall()

def get_ponto_ressuprimento_data(periodo_dias=90):
    start_date = (datetime.date.today() - datetime.timedelta(days=periodo_dias)).strftime("%Y-%m-%d")
    with db_connect() as conn:
        query = """
            SELECT
                i.id as item_id, i.nome as item_nome, i.codigo as item_codigo,
                f.nome as fornecedor_nome, COALESCE(f.prazo_entrega, 0) as lead_time,
                (SELECT COALESCE(SUM(quantidade), 0) FROM estoque WHERE item_id = i.id) as total_estoque,
                (SELECT COALESCE(SUM(quantidade), 0) FROM movimentacoes
                 WHERE item_id = i.id AND tipo_movimentacao IN ('saida', 'ajuste_saida') AND data_movimentacao >= ?) as consumo_periodo
            FROM itens i
            LEFT JOIN fornecedores f ON i.fornecedor_id = f.id
        """
        items_data = conn.cursor().execute(query, (start_date,)).fetchall()

        result = []
        for item in items_data:
            consumo_medio_diario = item['consumo_periodo'] / periodo_dias if periodo_dias > 0 else 0
            estoque_seguranca = consumo_medio_diario * (item['lead_time'] * 0.5)
            ponto_ressuprimento = (consumo_medio_diario * item['lead_time']) + estoque_seguranca

            if item['total_estoque'] <= ponto_ressuprimento:
                item['consumo_medio_diario'] = consumo_medio_diario
                item['ponto_ressuprimento'] = ponto_ressuprimento
                result.append(item)
        return result

# --- Auditoria ---
def log_auditoria(acao, referencia, detalhes):
    with db_connect() as conn:
        conn.cursor().execute("INSERT INTO auditoria (acao, referencia, detalhes, data_hora) VALUES (?, ?, ?, datetime('now', 'localtime'))",
                              (acao, referencia, detalhes))
        conn.commit()

def get_auditoria_logs(start_date=None, end_date=None, acao=None, usuario=None):
    with db_connect() as conn:
        query = "SELECT * FROM auditoria WHERE 1=1"
        params = []
        if start_date: query += " AND date(data_hora) >= date(?)"; params.append(start_date)
        if end_date: query += " AND date(data_hora) <= date(?)"; params.append(end_date)
        if acao and acao != "Todos": query += " AND acao LIKE ?"; params.append(f"%{acao}%")
        if usuario and usuario != "Todos": query += " AND referencia LIKE ?"; params.append(f"%{usuario}%")
        query += " ORDER BY data_hora DESC"
        return conn.cursor().execute(query, params).fetchall()

# --- Criação de Tabelas ---
def create_tables():
    with db_connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fornecedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL UNIQUE, contato TEXT,
                telefone TEXT, email TEXT, prazo_entrega INTEGER
            )""")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS depositos (
                id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL UNIQUE, localizacao TEXT
            )""")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tecnicos (
                id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL,
                matricula TEXT NOT NULL UNIQUE, setor TEXT
            )""")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS itens (
                id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT NOT NULL UNIQUE, nome TEXT NOT NULL,
                descricao TEXT, unidade TEXT, estoque_minimo INTEGER, preco_unitario REAL,
                fornecedor_id INTEGER, data_cadastro TEXT,
                FOREIGN KEY (fornecedor_id) REFERENCES fornecedores(id) ON DELETE RESTRICT
            )""")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ferramentas (
                id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT NOT NULL UNIQUE, nome TEXT NOT NULL,
                descricao TEXT, status TEXT, localizacao TEXT, data_aquisicao TEXT
            )""")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS estoque (
                item_id INTEGER NOT NULL, deposito_id INTEGER NOT NULL, quantidade INTEGER NOT NULL,
                PRIMARY KEY (item_id, deposito_id),
                FOREIGN KEY (item_id) REFERENCES itens(id) ON DELETE CASCADE,
                FOREIGN KEY (deposito_id) REFERENCES depositos(id) ON DELETE CASCADE
            )""")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS movimentacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER, deposito_id INTEGER,
                tipo_movimentacao TEXT, quantidade INTEGER, data_movimentacao TEXT,
                origem_destino TEXT, observacoes TEXT, tecnico_id INTEGER,
                FOREIGN KEY (item_id) REFERENCES itens(id) ON DELETE SET NULL,
                FOREIGN KEY (deposito_id) REFERENCES depositos(id) ON DELETE SET NULL,
                FOREIGN KEY (tecnico_id) REFERENCES tecnicos(id) ON DELETE SET NULL
            )""")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS emprestimos_ferramentas (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ferramenta_id INTEGER NOT NULL, tecnico_id INTEGER NOT NULL,
                data_emprestimo TEXT NOT NULL, data_devolucao_prevista TEXT NOT NULL,
                data_devolucao_real TEXT, observacoes TEXT, status TEXT NOT NULL,
                FOREIGN KEY (ferramenta_id) REFERENCES ferramentas(id) ON DELETE RESTRICT,
                FOREIGN KEY (tecnico_id) REFERENCES tecnicos(id) ON DELETE RESTRICT
            )""")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS auditoria (
                id INTEGER PRIMARY KEY AUTOINCREMENT, acao TEXT, referencia TEXT,
                detalhes TEXT, data_hora TEXT
            )""")
        conn.commit()
