import sys
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QDateEdit, QFrame
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIntValidator, QIcon
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

class EntradaEstoqueWindow(QDialog):
    """
    Janela para registrar entradas de itens no estoque.
    Permite selecionar o item, depósito, quantidade e fornecedor/origem.
    """

    def __init__(self, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.main_window = parent
        self.setWindowTitle("Registrar Entrada de Estoque")
        self.setGeometry(100, 100, 900, 650)
        self.setup_ui()
        self.load_initial_data()
        self.load_estoque_atual_to_table()
        self.clear_form()

    def setup_ui(self) -> None:
        """Configura os elementos da interface do usuário."""
        main_layout = QVBoxLayout(self)

        # Formulário de entrada
        form_frame = QFrame()
        form_frame.setObjectName("formFrame")
        form_layout = QGridLayout(form_frame)
        form_layout.setContentsMargins(15, 15, 15, 15)
        form_layout.setSpacing(10)

        form_layout.addWidget(QLabel("Item:"), 0, 0)
        self.cmb_item = QComboBox()
        self.cmb_item.addItem("-- Selecione um Item --", userData=None)
        form_layout.addWidget(self.cmb_item, 0, 1)

        form_layout.addWidget(QLabel("Depósito:"), 1, 0)
        self.cmb_deposito = QComboBox()
        self.cmb_deposito.addItem("-- Selecione um Depósito --", userData=None)
        form_layout.addWidget(self.cmb_deposito, 1, 1)

        form_layout.addWidget(QLabel("Quantidade:"), 2, 0)
        self.txt_quantidade = QLineEdit()
        self.txt_quantidade.setValidator(QIntValidator(1, 999999))
        self.txt_quantidade.setPlaceholderText("Ex: 100")
        form_layout.addWidget(self.txt_quantidade, 2, 1)

        form_layout.addWidget(QLabel("Data da Entrada:"), 3, 0)
        self.data_entrada_input = QDateEdit(calendarPopup=True)
        self.data_entrada_input.setDate(QDate.currentDate())
        self.data_entrada_input.setDisplayFormat("dd/MM/yyyy")
        form_layout.addWidget(self.data_entrada_input, 3, 1)

        form_layout.addWidget(QLabel("Origem (Fornecedor/Outro):"), 4, 0)
        self.txt_origem = QLineEdit()
        self.txt_origem.setPlaceholderText("Ex: Nome do Fornecedor, Transferência")
        form_layout.addWidget(self.txt_origem, 4, 1)

        form_layout.addWidget(QLabel("Observações:"), 5, 0)
        self.txt_observacoes = QLineEdit()
        self.txt_observacoes.setPlaceholderText("Ex: Nota Fiscal 12345")
        form_layout.addWidget(self.txt_observacoes, 5, 1)

        main_layout.addWidget(form_frame)

        # Botões do formulário
        button_layout = QHBoxLayout()
        self.btn_register_entry = QPushButton("Registrar Entrada")
        self.btn_register_entry.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "stock_in.png")))
        self.btn_register_entry.clicked.connect(self.register_entry)
        button_layout.addWidget(self.btn_register_entry)

        self.btn_clear = QPushButton("Limpar Formulário")
        self.btn_clear.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "clear.png")))
        self.btn_clear.setObjectName("secondaryButton")
        self.btn_clear.clicked.connect(self.clear_form)
        button_layout.addWidget(self.btn_clear)

        main_layout.addLayout(button_layout)

        # Tabela de Estoque Atual
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

        # Sinais para validação em tempo real
        self.cmb_item.currentIndexChanged.connect(lambda: self._validate_field(self.cmb_item))
        self.cmb_deposito.currentIndexChanged.connect(lambda: self._validate_field(self.cmb_deposito))
        self.txt_quantidade.textChanged.connect(lambda: self._validate_field(self.txt_quantidade, is_numeric=True))

    def _validate_field(self, field_widget, is_numeric=False) -> None:
        """
        Valida um campo de entrada em tempo real e aplica/remove estilo de erro.
        """
        is_valid = True
        if isinstance(field_widget, QLineEdit):
            text = field_widget.text().strip()
            if not text:
                is_valid = False
            elif is_numeric:
                try:
                    val = int(text)
                    if val <= 0 or not field_widget.hasAcceptableInput():
                        is_valid = False
                except ValueError:
                    is_valid = False
        elif isinstance(field_widget, QComboBox):
            if field_widget.currentData() is None:
                is_valid = False
        if not is_valid:
            field_widget.setStyleSheet("border: 2px solid red; border-radius: 6px;")
        else:
            field_widget.setStyleSheet("")

    def clear_form(self) -> None:
        """Limpa os campos do formulário."""
        self.cmb_item.setCurrentIndex(0)
        self.cmb_deposito.setCurrentIndex(0)
        self.txt_quantidade.clear()
        self.data_entrada_input.setDate(QDate.currentDate())
        self.txt_origem.clear()
        self.txt_observacoes.clear()
        logging.info("Formulário de entrada de estoque limpo.")
        self.cmb_item.setStyleSheet("")
        self.cmb_deposito.setStyleSheet("")
        self.txt_quantidade.setStyleSheet("")

    def load_initial_data(self) -> None:
        """Carrega itens e depósitos para os comboboxes."""
        self.cmb_item.clear()
        self.cmb_item.addItem("-- Selecione um Item --", userData=None)
        items = database_manager.get_all_items()
        if items:
            for item in items:
                self.cmb_item.addItem(f"{item['codigo']} - {item['nome']}", userData=item['id'])
        logging.info("Itens carregados no combobox de entrada.")

        self.cmb_deposito.clear()
        self.cmb_deposito.addItem("-- Selecione um Depósito --", userData=None)
        depositos = database_manager.get_all_depositos()
        if depositos:
            for deposito in depositos:
                self.cmb_deposito.addItem(deposito['nome'], userData=deposito['id'])
        logging.info("Depósitos carregados no combobox de entrada.")

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
        logging.info("Estoque atual carregado na tabela de entrada.")
        if self.main_window:
            self.main_window.show_status_message("Tabela de estoque atualizada.", 2000)

    def register_entry(self) -> None:
        """Registra uma nova entrada de estoque."""
        item_id = self.cmb_item.currentData()
        deposito_id = self.cmb_deposito.currentData()
        quantidade_str = self.txt_quantidade.text().strip()
        data_movimentacao = self.data_entrada_input.date().toString("yyyy-MM-dd")
        origem = self.txt_origem.text().strip() or None
        observacoes = self.txt_observacoes.text().strip() or None

        # Validação antes de registrar
        is_valid = True
        if item_id is None:
            self._validate_field(self.cmb_item)
            is_valid = False
        if deposito_id is None:
            self._validate_field(self.cmb_deposito)
            is_valid = False
        if not quantidade_str or not self.txt_quantidade.hasAcceptableInput():
            self._validate_field(self.txt_quantidade, is_numeric=True)
            is_valid = False

        if not is_valid:
            QMessageBox.warning(self, "Campos Inválidos", "Por favor, corrija os campos destacados em vermelho.")
            if self.main_window:
                self.main_window.show_status_message("Erro: Por favor, corrija os campos destacados.", 3000)
            return

        quantidade = int(quantidade_str)

        # Corrigido: sempre retorna uma tupla (success, message)
        result = database_manager.register_entry(
            item_id, quantidade, deposito_id, data_movimentacao, origem, observacoes
        )
        if isinstance(result, tuple):
            success, message = result
        else:
            success, message = result, "Entrada registrada."

        if success:
            QMessageBox.information(self, "Sucesso", "Entrada de estoque registrada com sucesso!")
            if self.main_window:
                self.main_window.show_status_message("Entrada de estoque registrada com sucesso!", 3000)
            logging.info(f"Entrada registrada: Item ID {item_id}, Qtd {quantidade}, Depósito ID {deposito_id}.")
        else:
            QMessageBox.critical(self, "Erro", f"Erro ao registrar entrada: {message}")
            if self.main_window:
                self.main_window.show_status_message(f"Erro ao registrar entrada: {message}", 5000)
            logging.error(f"Falha ao registrar entrada: Item ID {item_id}, Qtd {quantidade}, Depósito ID {deposito_id}. Erro: {message}")

        self.load_estoque_atual_to_table()
        self.clear_form()

def abrir_tela_entrada_estoque(janela_principal: Optional[QDialog]):
    """
    Função para instanciar e exibir a janela de Entrada de Estoque.
    """
    dialog = EntradaEstoqueWindow(janela_principal)
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
        database_manager.add_deposito("Depósito Principal E")
        database_manager.add_deposito("Depósito Secundário E")

    dialog = EntradaEstoqueWindow()
    dialog.show()
    sys.exit(app.exec())