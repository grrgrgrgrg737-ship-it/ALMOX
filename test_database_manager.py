import unittest
import os
import sqlite3
import time
import datetime
import database_manager

class TestDatabaseManager(unittest.TestCase):
    """Classe de testes unitários para o database_manager.py, usando um DB em arquivo."""

    DB_PATH = "test_almoxarifado.db"

    def setUp(self):
        """Configura o ambiente antes de cada teste."""
        if os.path.exists(self.DB_PATH):
            os.remove(self.DB_PATH)

        self.original_db_path = database_manager.DB_PATH
        database_manager.DB_PATH = self.DB_PATH

        database_manager.create_tables()
        self.populate_test_data()

    def tearDown(self):
        """Limpa o ambiente após cada teste."""
        database_manager.DB_PATH = self.original_db_path
        if os.path.exists(self.DB_PATH):
            os.remove(self.DB_PATH)

    def populate_test_data(self):
        """Popula as tabelas com dados para os testes."""
        database_manager.add_fornecedor("Fornecedor A", "Contato A", "111", "a@a.com", 1)
        database_manager.add_fornecedor("Fornecedor B", "Contato B", "222", "b@b.com", 10)
        database_manager.add_deposito("Depósito Central", "Rua X")
        database_manager.add_deposito("Depósito Secundário", "Rua Y")
        fornecedor_a_id = database_manager.get_fornecedor_by_name("Fornecedor A")['id']
        fornecedor_b_id = database_manager.get_fornecedor_by_name("Fornecedor B")['id']
        database_manager.add_item("ITM001", "Item 1", "Desc 1", "UN", 10, 1.0, fornecedor_a_id, "2024-01-01")
        database_manager.add_item("ITM002", "Item 2", "Desc 2", "PC", 20, 2.0, fornecedor_b_id, "2024-01-02")
        database_manager.add_tecnico("João", "MAT001", "TI")
        database_manager.add_tecnico("Maria", "MAT002", "Manutenção")
        database_manager.add_ferramenta("FER001", "Furadeira", "Furadeira de Impacto", "Disponível", "Armário A", "2024-01-01")
        database_manager.add_ferramenta("FER002", "Martelo", "Martelo de Pena", "Em Manutenção", "Armário B", "2024-01-02")
        item1_id = database_manager.get_item_by_code("ITM001")['id']
        deposito_id = database_manager.get_deposito_by_name("Depósito Central")['id']
        database_manager.register_entry(item1_id, 100, deposito_id, "2024-02-01", "Fornecedor A")

    def test_add_and_get_item(self):
        """Testa adicionar e buscar um item."""
        fornecedor_b_id = database_manager.get_fornecedor_by_name("Fornecedor B")['id']
        success, message = database_manager.add_item("ITM003", "Item 3", "Desc 3", "M", 30, 3.0, fornecedor_b_id, "2024-01-03")
        self.assertTrue(success)

        item = database_manager.get_item_by_code("ITM003")
        self.assertIsNotNone(item)
        self.assertEqual(item['nome'], "Item 3")

        success, message = database_manager.add_item("ITM001", "Item Dup", "Desc Dup", "UN", 1, 1.0, fornecedor_b_id, "2024-01-01")
        self.assertFalse(success)
        self.assertIn("já existe", message)

    def test_update_item(self):
        """Testa a atualização de um item."""
        item1 = database_manager.get_item_by_code("ITM001")
        success, message = database_manager.update_item(item1['id'], "ITM001", "Item 1 Atualizado", "Nova Desc", "CX", 15, 1.5, item1['fornecedor_id'], "2024-03-01")
        self.assertTrue(success)

        updated_item = database_manager.get_item_by_id(item1['id'])
        self.assertEqual(updated_item['nome'], "Item 1 Atualizado")
        self.assertEqual(updated_item['estoque_minimo'], 15)

    def test_register_entry_and_exit(self):
        """Testa a lógica de entrada e saída de estoque."""
        item1_id = database_manager.get_item_by_code("ITM001")['id']
        deposito_id = database_manager.get_deposito_by_name("Depósito Central")['id']

        estoque = database_manager.get_estoque_by_item_deposito(item1_id, deposito_id)
        self.assertEqual(estoque['quantidade'], 100)

        success, message = database_manager.register_exit(item1_id, 10, deposito_id, "2024-03-01", "João")
        self.assertTrue(success)
        estoque = database_manager.get_estoque_by_item_deposito(item1_id, deposito_id)
        self.assertEqual(estoque['quantidade'], 90)

        success, message = database_manager.register_exit(item1_id, 100, deposito_id, "2024-03-02", "Maria")
        self.assertFalse(success)
        self.assertIn("insuficiente", message)

        estoque = database_manager.get_estoque_by_item_deposito(item1_id, deposito_id)
        self.assertEqual(estoque['quantidade'], 90)

        success, message = database_manager.register_entry(item1_id, 20, deposito_id, "2024-03-03", "Fornecedor A")
        self.assertTrue(success)
        estoque = database_manager.get_estoque_by_item_deposito(item1_id, deposito_id)
        self.assertEqual(estoque['quantidade'], 110)

    def test_get_movimentacoes(self):
        """Testa a busca de movimentações com filtros."""
        item1_id = database_manager.get_item_by_code("ITM001")['id']
        deposito_id = database_manager.get_deposito_by_name("Depósito Central")['id']
        database_manager.register_exit(item1_id, 10, deposito_id, "2024-03-01", "João")

        movs = database_manager.get_movimentacoes("2024-01-01", "2024-12-31")
        self.assertEqual(len(movs), 2)

        entradas = database_manager.get_movimentacoes("2024-01-01", "2024-12-31", tipo_movimentacao="entrada")
        self.assertEqual(len(entradas), 1)
        self.assertEqual(entradas[0]['quantidade'], 100)

    def test_relatorios_consumo(self):
        """Testa os relatórios de consumo."""
        item1_id = database_manager.get_item_by_code("ITM001")['id']
        deposito_id = database_manager.get_deposito_by_name("Depósito Central")['id']
        tecnico_joao_id = database_manager.get_tecnico_by_matricula("MAT001")['id']

        database_manager.register_exit(
            item_id=item1_id,
            quantidade=10,
            deposito_id=deposito_id,
            data="2024-03-01",
            destino="Projeto Y",
            tecnico_id=tecnico_joao_id
        )

        consumo_item = database_manager.get_consumo_por_item("2024-01-01", "2024-12-31")
        self.assertEqual(len(consumo_item), 1)
        self.assertEqual(consumo_item[0]['total_consumido'], 10)
        self.assertEqual(consumo_item[0]['nome'], "Item 1")

        consumo_tecnico = database_manager.get_consumo_por_tecnico("2024-01-01", "2024-12-31")
        self.assertEqual(len(consumo_tecnico), 1)
        self.assertEqual(consumo_tecnico[0]['total_consumido'], 10)
        self.assertEqual(consumo_tecnico[0]['tecnico_nome'], "João")

        consumo_joao = database_manager.get_consumo_por_tecnico("2024-01-01", "2024-12-31", tecnico_id=tecnico_joao_id)
        self.assertEqual(len(consumo_joao), 1)
        self.assertEqual(consumo_joao[0]['tecnico_nome'], "João")

        tecnico_maria_id = database_manager.get_tecnico_by_matricula("MAT002")['id']
        consumo_maria = database_manager.get_consumo_por_tecnico("2024-01-01", "2024-12-31", tecnico_id=tecnico_maria_id)
        self.assertEqual(len(consumo_maria), 0)

    def test_auditoria(self):
        """Testa a funcionalidade de auditoria."""
        database_manager.log_auditoria("Ação Teste", "Referência Teste", "Detalhes Teste")
        logs = database_manager.get_auditoria_logs(acao="Ação Teste")
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]['referencia'], "Referência Teste")

    def test_emprestimo_ferramentas(self):
        """Testa o ciclo de vida do empréstimo de uma ferramenta."""
        ferramenta_id = database_manager.get_ferramenta_by_codigo("FER001")['id']
        tecnico_id = database_manager.get_tecnico_by_matricula("MAT001")['id']

        success, msg, emprestimo_id = database_manager.add_emprestimo_ferramenta(ferramenta_id, tecnico_id, "2024-04-01", "2024-04-08", "Para projeto X")
        self.assertTrue(success)
        self.assertIsNotNone(emprestimo_id)

        emprestimos = database_manager.get_emprestimos_ferramentas(status_filter="Emprestado")
        self.assertEqual(len(emprestimos), 1)
        self.assertEqual(emprestimos[0]['id'], emprestimo_id)

        success, msg = database_manager.update_emprestimo_ferramenta(emprestimo_id, ferramenta_id, tecnico_id, "2024-04-01", "2024-04-08", "2024-04-05", "Devolvido OK", "Devolvido")
        self.assertTrue(success)

        emprestimos_devolvidos = database_manager.get_emprestimos_ferramentas(status_filter="Devolvido")
        self.assertEqual(len(emprestimos_devolvidos), 1)
        self.assertEqual(emprestimos_devolvidos[0]['status'], "Devolvido")
        self.assertEqual(emprestimos_devolvidos[0]['data_devolucao_real'], "2024-04-05")

    def test_ponto_ressuprimento(self):
        """Testa a função de cálculo de ponto de ressuprimento."""
        item_id = database_manager.get_item_by_code("ITM002")['id']
        deposito_id = database_manager.get_deposito_by_name("Depósito Central")['id']

        database_manager.register_entry(item_id, 100, deposito_id, "2024-08-01", "Fornecedor B")

        for i in range(50):
             data = (datetime.date.today() - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
             database_manager.register_exit(item_id, 1, deposito_id, data, "Consumo Teste")

        ressuprimento_list = database_manager.get_ponto_ressuprimento_data()
        self.assertFalse(any(d['item_id'] == item_id for d in ressuprimento_list))

        database_manager.register_exit(item_id, 45, deposito_id, datetime.date.today().strftime("%Y-%m-%d"), "Consumo Teste 2")

        ressuprimento_list = database_manager.get_ponto_ressuprimento_data()
        self.assertTrue(any(d['item_id'] == item_id for d in ressuprimento_list))


if __name__ == '__main__':
    unittest.main()
