import sys
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QDateEdit, QFrame, QCompleter
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIntValidator, QIcon
import os
import database_manager
import logging

# Importa a nova janela do scanner
from qr_code_scanner import QRScannerDialog

class SaidaEstoqueWindow(QDialog):
    def __init__(self, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.main_window = parent
        self.setWindowTitle("Registrar Saída de Estoque")
        self.setGeometry(100, 100, 950, 700)
        self.current_item_stock = 0
        self.setup_ui()
        self.load_initial_data()
        self.load_estoque_atual_to_table()

    def setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        form_frame = QFrame(objectName="formFrame")
        form_layout = QGridLayout(form_frame)
        form_layout.setContentsMargins(15, 15, 15, 15)

        # Linha para seleção de item e botão de QR Code
        item_selection_layout = QHBoxLayout()
        self.item_combobox = QComboBox()
        self.item_combobox.setEditable(True)
        self.item_combobox.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.item_combobox.completer().setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.item_combobox.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        self.item_combobox.currentIndexChanged.connect(self.update_item_info)
        item_selection_layout.addWidget(self.item_combobox)

        # NOVO BOTÃO para escanear QR Code
        self.btn_scan_qr = QPushButton()
        self.btn_scan_qr.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "qr_code_scan.png")))
        self.btn_scan_qr.setToolTip("Escanear QR Code do Item")
        self.btn_scan_qr.setFixedWidth(40)
        self.btn_scan_qr.clicked.connect(self.open_qr_scanner)
        item_selection_layout.addWidget(self.btn_scan_qr)

        form_layout.addWidget(QLabel("Item:"), 0, 0)
        form_layout.addLayout(item_selection_layout, 0, 1)

        form_layout.addWidget(QLabel("Depósito:"), 1, 0)
        self.deposito_combobox = QComboBox()
        self.deposito_combobox.currentIndexChanged.connect(self.update_item_info)
        form_layout.addWidget(self.deposito_combobox, 1, 1)

        form_layout.addWidget(QLabel("Estoque Disponível:"), 2, 0)
        self.estoque_atual_display = QLineEdit("0")
        self.estoque_atual_display.setReadOnly(True)
        form_layout.addWidget(self.estoque_atual_display, 2, 1)

        form_layout.addWidget(QLabel("Quantidade a Retirar:"), 3, 0)
        self.quantidade_input = QLineEdit()
        self.quantidade_input.setValidator(QIntValidator(1, 999999))
        form_layout.addWidget(self.quantidade_input, 3, 1)

        form_layout.addWidget(QLabel("Técnico/Destino:"), 4, 0)
        self.tecnico_combobox = QComboBox()
        self.tecnico_combobox.setEditable(True)
        self.tecnico_combobox.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.tecnico_combobox.completer().setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.tecnico_combobox.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        form_layout.addWidget(self.tecnico_combobox, 4, 1)

        form_layout.addWidget(QLabel("Data da Saída:"), 5, 0)
        self.data_saida_dateedit = QDateEdit(calendarPopup=True, date=QDate.currentDate())
        form_layout.addWidget(self.data_saida_dateedit, 5, 1)

        form_layout.addWidget(QLabel("Observações:"), 6, 0)
        self.observacoes_input = QLineEdit()
        form_layout.addWidget(self.observacoes_input, 6, 1)
        main_layout.addWidget(form_frame)

        button_layout = QHBoxLayout()
        self.registrar_button = QPushButton("Registrar Saída", clicked=self.registrar_saida)
        self.limpar_button = QPushButton("Limpar", clicked=self.clear_form)
        button_layout.addWidget(self.registrar_button)
        button_layout.addWidget(self.limpar_button)
        main_layout.addLayout(button_layout)

        self.estoque_table = QTableWidget()
        self.estoque_table.setColumnCount(4)
        self.estoque_table.setHorizontalHeaderLabels(["Item", "Código", "Depósito", "Quantidade"])
        self.estoque_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.estoque_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        main_layout.addWidget(self.estoque_table)

    def load_initial_data(self):
        # Carrega Itens
        self.item_combobox.blockSignals(True)
        self.item_combobox.clear()
        self.item_combobox.addItem("Selecione ou digite para buscar...", None)
        items = database_manager.get_all_items()
        for item in items: self.item_combobox.addItem(f"{item['codigo']} - {item['nome']}", item['id'])
        self.item_combobox.blockSignals(False)

        # Carrega Depósitos
        self.deposito_combobox.clear()
        self.deposito_combobox.addItem("Selecione um depósito...", None)
        for dep in database_manager.get_all_depositos(): self.deposito_combobox.addItem(dep['nome'], dep['id'])

        # Carrega Técnicos
        self.tecnico_combobox.blockSignals(True)
        self.tecnico_combobox.clear()
        self.tecnico_combobox.addItem("Selecione ou digite para buscar...", None)
        for tec in database_manager.get_all_tecnicos(): self.tecnico_combobox.addItem(f"{tec['nome']} ({tec['matricula']})", tec['id'])
        self.tecnico_combobox.blockSignals(False)
        self.update_item_info()

    def update_item_info(self):
        item_id = self.item_combobox.currentData()
        deposito_id = self.deposito_combobox.currentData()
        if item_id is None or deposito_id is None:
            self.estoque_atual_display.setText("0")
            self.current_item_stock = 0
            return
        estoque_data = database_manager.get_estoque_by_item_deposito(item_id, deposito_id)
        self.current_item_stock = estoque_data['quantidade'] if estoque_data else 0
        self.estoque_atual_display.setText(str(self.current_item_stock))

    def registrar_saida(self):
        item_id = self.item_combobox.currentData()
        deposito_id = self.deposito_combobox.currentData()
        tecnico_id = self.tecnico_combobox.currentData()
        qtd_str = self.quantidade_input.text().strip()

        if not all([item_id, deposito_id, tecnico_id, qtd_str]):
            QMessageBox.warning(self, "Campos Obrigatórios", "Todos os campos devem ser preenchidos.")
            return

        try:
            quantidade = int(qtd_str)
            if quantidade <= 0 or quantidade > self.current_item_stock:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Quantidade Inválida", f"A quantidade deve ser um número entre 1 e {self.current_item_stock}.")
            return

        tecnico = database_manager.get_tecnico_by_id(tecnico_id)
        destino = tecnico['nome'] if tecnico else self.tecnico_combobox.currentText()
        data = self.data_saida_dateedit.date().toString("yyyy-MM-dd")
        obs = self.observacoes_input.text().strip()

        success, message = database_manager.register_exit(item_id, quantidade, deposito_id, data, destino, obs, tecnico_id=tecnico_id)
        if success:
            QMessageBox.information(self, "Sucesso", message)
            self.load_estoque_atual_to_table()
            self.update_item_info()
            self.clear_form(ask_confirmation=False)
        else:
            QMessageBox.critical(self, "Erro", message)

    def clear_form(self, ask_confirmation=True):
        if ask_confirmation:
            if any([self.quantidade_input.text(), self.observacoes_input.text()]):
                reply = QMessageBox.question(self, "Limpar", "Deseja limpar os campos?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.No: return
        self.item_combobox.setCurrentIndex(0)
        self.deposito_combobox.setCurrentIndex(0)
        self.tecnico_combobox.setCurrentIndex(0)
        self.quantidade_input.clear()
        self.observacoes_input.clear()
        self.data_saida_dateedit.setDate(QDate.currentDate())

    def load_estoque_atual_to_table(self):
        self.estoque_table.setRowCount(0)
        estoque_geral = database_manager.get_estoque_geral()
        self.estoque_table.setRowCount(len(estoque_geral))
        for row, item in enumerate(estoque_geral):
            self.estoque_table.setItem(row, 0, QTableWidgetItem(item['item_nome']))
            self.estoque_table.setItem(row, 1, QTableWidgetItem(item['item_codigo']))
            self.estoque_table.setItem(row, 2, QTableWidgetItem(item['deposito_nome']))
            self.estoque_table.setItem(row, 3, QTableWidgetItem(str(item['quantidade'])))

    def open_qr_scanner(self):
        """Abre a janela do scanner de QR Code."""
        scanner_dialog = QRScannerDialog(self)
        # Conecta o sinal do diálogo a um método de tratamento nesta janela
        scanner_dialog.qr_code_result.connect(self.handle_qr_code_scanned)
        scanner_dialog.exec()

    def handle_qr_code_scanned(self, qr_data: str):
        """
        Processa o código QR recebido do scanner e seleciona o item no ComboBox.
        """
        # O QR code contém o CÓDIGO do item.
        item = database_manager.get_item_by_code(qr_data)

        if item:
            item_id_scaneado = item['id']
            # Procura o item no ComboBox pelo seu ID
            for i in range(self.item_combobox.count()):
                if self.item_combobox.itemData(i) == item_id_scaneado:
                    self.item_combobox.setCurrentIndex(i)
                    QMessageBox.information(self, "Item Encontrado", f"Item '{item['nome']}' selecionado via QR Code.")
                    return
            QMessageBox.warning(self, "Erro", "O item escaneado foi encontrado no banco, mas não na lista. Tente recarregar a tela.")
        else:
            QMessageBox.warning(self, "Item Não Encontrado", f"Nenhum item encontrado com o código '{qr_data}' do QR Code.")

def abrir_tela_saida_estoque(janela_principal):
    dialog = SaidaEstoqueWindow(janela_principal)
    dialog.exec()
