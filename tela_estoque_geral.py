import sys
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QLabel
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
    Janela para visualizar o estoque geral.
    Apenas exibe os itens, depósitos e quantidades.
    """

    def __init__(self, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.main_window = parent
        self.setWindowTitle("Estoque Geral")
        self.setGeometry(100, 100, 800, 500)
        self.setup_ui()
        self.load_estoque_atual_to_table()

    def setup_ui(self) -> None:
        """Configura os elementos da interface do usuário."""
        main_layout = QVBoxLayout(self)

        title_label = QLabel("Estoque Atual")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        table_frame = QFrame()
        table_frame.setObjectName("tableFrame")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(15, 15, 15, 15)
        table_layout.setSpacing(10)

        self.table_estoque_atual = QTableWidget()
        self.table_estoque_atual.setColumnCount(4)
        self.table_estoque_atual.setHorizontalHeaderLabels([
            "Item (Código - Nome)", "Depósito", "Quantidade", "Item ID"
        ])
        self.table_estoque_atual.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_estoque_atual.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_estoque_atual.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_estoque_atual.setColumnHidden(3, True)
        table_layout.addWidget(self.table_estoque_atual)
        main_layout.addWidget(table_frame)

    def load_estoque_atual_to_table(self) -> None:
        """Carrega o estoque atual para a tabela."""
        self.table_estoque_atual.setRowCount(0)
        estoque_geral = database_manager.get_estoque_geral()
        if estoque_geral:
            for row_idx, estoque in enumerate(estoque_geral):
                self.table_estoque_atual.insertRow(row_idx)
                item_info = database_manager.get_item_by_id(estoque['item_id'])
                deposito_info = database_manager.get_deposito_by_id(estoque['deposito_id'])
                item_display = f"{item_info['codigo']} - {item_info['nome']}" if item_info else "N/A"
                deposito_display = deposito_info['nome'] if deposito_info else "N/A"
                self.table_estoque_atual.setItem(row_idx, 0, QTableWidgetItem(item_display))
                self.table_estoque_atual.setItem(row_idx, 1, QTableWidgetItem(deposito_display))
                self.table_estoque_atual.setItem(row_idx, 2, QTableWidgetItem(str(estoque['quantidade'])))
                self.table_estoque_atual.setItem(row_idx, 3, QTableWidgetItem(str(estoque['item_id'])))
        logging.info("Estoque atual carregado na tabela de estoque geral.")
        if self.main_window:
            self.main_window.show_status_message("Tabela de estoque atualizada.", 2000)

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
        database_manager.add_deposito("Depósito Principal E", "Rua Teste, 10")
        database_manager.add_deposito("Depósito Secundário E", "Rua Exemplo, 20")
    dialog = EstoqueGeralWindow()
    dialog.show()
    sys.exit(app.exec())