import sys
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QLabel, QComboBox
)
from PyQt6.QtCore import Qt
import os

import database_manager
import logging

# Configuração do logging
logging.basicConfig(
    filename='almoxarifado.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

class EstoqueGeralWindow(QDialog):
    """
    Janela para visualizar o estoque geral, com filtro por tipo de depósito.
    """

    def __init__(self, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.main_window = parent
        self.setWindowTitle("Estoque Geral")
        self.setGeometry(100, 100, 900, 600)
        self.setup_ui()
        self.load_estoque_atual_to_table()

    def setup_ui(self) -> None:
        """Configura os elementos da interface do usuário."""
        main_layout = QVBoxLayout(self)

        # Filtro por tipo de depósito
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filtrar por Tipo de Depósito:"))
        self.tipo_filter_combo = QComboBox()
        self.tipo_filter_combo.addItems(["Todos", "Principal", "Emergência"])
        self.tipo_filter_combo.currentIndexChanged.connect(self.load_estoque_atual_to_table)
        filter_layout.addWidget(self.tipo_filter_combo)
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)

        table_frame = QFrame(objectName="tableFrame")
        table_layout = QVBoxLayout(table_frame)

        self.table_estoque_atual = QTableWidget()
        self.table_estoque_atual.setColumnCount(4)
        self.table_estoque_atual.setHorizontalHeaderLabels([
            "Item (Código - Nome)", "Depósito", "Tipo", "Quantidade"
        ])
        self.table_estoque_atual.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_estoque_atual.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_estoque_atual.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table_layout.addWidget(self.table_estoque_atual)
        main_layout.addWidget(table_frame)

    def load_estoque_atual_to_table(self) -> None:
        """Carrega o estoque atual para a tabela, aplicando o filtro de tipo."""
        self.table_estoque_atual.setRowCount(0)

        selected_type = self.tipo_filter_combo.currentText()

        estoque_geral = database_manager.get_estoque_geral(tipo_deposito=selected_type)

        if estoque_geral:
            self.table_estoque_atual.setRowCount(len(estoque_geral))
            for row_idx, estoque in enumerate(estoque_geral):
                self.table_estoque_atual.setItem(row_idx, 0, QTableWidgetItem(f"{estoque['item_codigo']} - {estoque['item_nome']}"))
                self.table_estoque_atual.setItem(row_idx, 1, QTableWidgetItem(estoque['deposito_nome']))
                self.table_estoque_atual.setItem(row_idx, 2, QTableWidgetItem(estoque.get('deposito_tipo', 'Principal')))
                self.table_estoque_atual.setItem(row_idx, 3, QTableWidgetItem(str(estoque['quantidade'])))

        logging.info(f"Estoque geral carregado com filtro: {selected_type}.")
        if self.main_window:
            self.main_window.show_status_message(f"Tabela de estoque atualizada (Filtro: {selected_type}).", 2000)

def abrir_tela_estoque_geral(janela_principal: Optional[QDialog]):
    """
    Função para instanciar e exibir a janela de Estoque Geral.
    """
    dialog = EstoqueGeralWindow(janela_principal)
    dialog.exec()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    database_manager.create_tables()
    if not database_manager.get_all_fornecedores():
        database_manager.add_fornecedor("Fornecedor Entrada", "Contato E", "11912345678", "entrada@email.com", 7)
    fornecedor_id = database_manager.get_fornecedor_by_name("Fornecedor Entrada")['id']
    if not database_manager.get_all_items():
        database_manager.add_item("MON27", "Monitor 27p", "Monitor Dell 27 polegadas", "UN", 2, 1200.00, fornecedor_id, "2024-03-01")
        database_manager.add_item("TECSFW", "Teclado Sem Fio", "Teclado Logitech sem fio", "UN", 5, 150.00, fornecedor_id, "2024-03-05")
    if not database_manager.get_all_depositos():
        database_manager.add_deposito("Depósito Principal E", "Rua Teste, 10", "Principal")
        database_manager.add_deposito("Depósito Emergência Elétrica", "Rua Exemplo, 20", "Emergência")
    dialog = EstoqueGeralWindow()
    dialog.show()
    sys.exit(app.exec())
