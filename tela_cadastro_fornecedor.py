import sys
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt
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

class CadastroFornecedorWindow(QDialog):
    """
    Janela para cadastro, edição e exclusão de fornecedores.
    """

    def __init__(self, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.main_window = parent
        self.setWindowTitle("Cadastro de Fornecedores")
        self.setGeometry(100, 100, 900, 650)
        self.current_fornecedor_id: Optional[int] = None
        self.setup_ui()
        self.load_fornecedores_to_table()
        self.clear_form()

    def setup_ui(self) -> None:
        """Configura os elementos da interface do usuário."""
        main_layout = QVBoxLayout(self)

        # Formulário
        form_frame = QFrame()
        form_frame.setObjectName("formFrame")
        form_layout = QGridLayout(form_frame)
        form_layout.setContentsMargins(15, 15, 15, 15)
        form_layout.setSpacing(10)

        form_layout.addWidget(QLabel("Nome:"), 0, 0)
        self.nome_input = QLineEdit()
        self.nome_input.setPlaceholderText("Nome do Fornecedor")
        form_layout.addWidget(self.nome_input, 0, 1)

        form_layout.addWidget(QLabel("Contato:"), 1, 0)
        self.contato_input = QLineEdit()
        self.contato_input.setPlaceholderText("Pessoa de contato (opcional)")
        form_layout.addWidget(self.contato_input, 1, 1)

        form_layout.addWidget(QLabel("Telefone:"), 2, 0)
        self.telefone_input = QLineEdit()
        self.telefone_input.setPlaceholderText("Telefone (ex: 11987654321)")
        form_layout.addWidget(self.telefone_input, 2, 1)

        form_layout.addWidget(QLabel("Email:"), 3, 0)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email (opcional)")
        form_layout.addWidget(self.email_input, 3, 1)

        form_layout.addWidget(QLabel("Prazo Entrega (dias):"), 4, 0)
        self.prazo_entrega_input = QLineEdit()
        self.prazo_entrega_input.setPlaceholderText("Prazo em dias (apenas números)")
        self.prazo_entrega_input.setValidator(QIntValidator(0, 999)) # Apenas números inteiros
        form_layout.addWidget(self.prazo_entrega_input, 4, 1)

        main_layout.addWidget(form_frame)

        # Botões de Ação
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Salvar")
        self.btn_save.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "save.png")))
        self.btn_save.clicked.connect(self.save_fornecedor)
        btn_layout.addWidget(self.btn_save)

        self.btn_clear = QPushButton("Limpar")
        self.btn_clear.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "clear.png")))
        self.btn_clear.setObjectName("secondaryButton")
        self.btn_clear.clicked.connect(self.clear_form)
        btn_layout.addWidget(self.btn_clear)

        self.btn_delete = QPushButton("Excluir")
        self.btn_delete.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "delete.png")))
        self.btn_delete.setObjectName("dangerButton")
        self.btn_delete.clicked.connect(self.delete_fornecedor)
        self.btn_delete.setEnabled(False) # Desabilitado até um fornecedor ser selecionado
        btn_layout.addWidget(self.btn_delete)

        main_layout.addLayout(btn_layout)

        # Tabela de Fornecedores
        table_frame = QFrame()
        table_frame.setObjectName("tableFrame")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(15, 15, 15, 15)
        table_layout.setSpacing(10)

        self.table_fornecedores = QTableWidget()
        self.table_fornecedores.setColumnCount(6) # Corrigido para 6 colunas
        self.table_fornecedores.setHorizontalHeaderLabels([
            "ID", "Nome", "Contato", "Telefone", "Email", "Prazo Entrega (dias)" # Nova coluna
        ])
        self.table_fornecedores.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_fornecedores.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_fornecedores.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_fornecedores.itemSelectionChanged.connect(self.load_fornecedor_to_form)
        table_layout.addWidget(self.table_fornecedores)

        main_layout.addWidget(table_frame)

    def clear_form(self) -> None:
        """Limpa todos os campos do formulário e redefine o ID atual."""
        self.nome_input.clear()
        self.contato_input.clear()
        self.telefone_input.clear()
        self.email_input.clear()
        self.prazo_entrega_input.clear()
        self.current_fornecedor_id = None
        self.btn_delete.setEnabled(False)
        self.btn_save.setText("Salvar")
        self.btn_save.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "save.png")))
        self.nome_input.setFocus()
        if self.main_window:
            self.main_window.show_status_message("Formulário de fornecedor limpo.", 2000)

    def save_fornecedor(self) -> None:
        """Salva um novo fornecedor ou atualiza um existente."""
        nome = self.nome_input.text().strip()
        contato = self.contato_input.text().strip()
        telefone = self.telefone_input.text().strip()
        email = self.email_input.text().strip()
        prazo_entrega_str = self.prazo_entrega_input.text().strip()

        if not nome:
            QMessageBox.warning(self, "Erro de Validação", "O campo 'Nome' é obrigatório.")
            if self.main_window:
                self.main_window.show_status_message("O campo 'Nome' é obrigatório.", 3000)
            return
        
        try:
            prazo_entrega = int(prazo_entrega_str) if prazo_entrega_str else 0
        except ValueError:
            QMessageBox.warning(self, "Erro de Validação", "O campo 'Prazo Entrega' deve ser um número inteiro.")
            if self.main_window:
                self.main_window.show_status_message("O campo 'Prazo Entrega' deve ser um número inteiro.", 3000)
            return

        if self.current_fornecedor_id:
            # Atualizar fornecedor existente
            success, message = database_manager.update_fornecedor(
                self.current_fornecedor_id, nome, contato, telefone, email, prazo_entrega
            )
            action = "atualizado"
        else:
            # Cadastrar novo fornecedor
            success, message = database_manager.add_fornecedor(
                nome, contato, telefone, email, prazo_entrega
            )
            action = "cadastrado"

        if success:
            QMessageBox.information(self, "Sucesso", f"Fornecedor {action} com sucesso!")
            if self.main_window:
                self.main_window.show_status_message(f"Fornecedor {action} com sucesso!", 3000)
            logging.info(f"Fornecedor {nome} {action} com sucesso.")
            self.load_fornecedores_to_table()
            self.clear_form()
        else:
            QMessageBox.critical(self, "Erro", f"Erro ao {action} fornecedor: {message}")
            if self.main_window:
                self.main_window.show_status_message(f"Erro ao {action} fornecedor: {message}", 5000)
            logging.error(f"Falha ao {action} fornecedor {nome}: {message}")


    def load_fornecedores_to_table(self) -> None:
        """Carrega todos os fornecedores do banco de dados para a tabela."""
        self.table_fornecedores.setRowCount(0)
        fornecedores = database_manager.get_all_fornecedores()
        if fornecedores:
            self.table_fornecedores.setRowCount(len(fornecedores))
            for row_idx, forn in enumerate(fornecedores):
                self.table_fornecedores.setItem(row_idx, 0, QTableWidgetItem(str(forn['id'])))
                self.table_fornecedores.setItem(row_idx, 1, QTableWidgetItem(forn['nome']))
                self.table_fornecedores.setItem(row_idx, 2, QTableWidgetItem(forn['contato']))
                self.table_fornecedores.setItem(row_idx, 3, QTableWidgetItem(forn['telefone']))
                self.table_fornecedores.setItem(row_idx, 4, QTableWidgetItem(forn['email']))
                self.table_fornecedores.setItem(row_idx, 5, QTableWidgetItem(str(forn['prazo_entrega']))) # Corrigido para exibir prazo_entrega
        logging.info("Fornecedores carregados na tabela.")
        if self.main_window:
            self.main_window.show_status_message("Tabela de fornecedores atualizada.", 2000)

    def load_fornecedor_to_form(self) -> None:
        """Carrega os dados do fornecedor selecionado na tabela para o formulário."""
        selected_rows = self.table_fornecedores.selectedItems()
        if not selected_rows:
            self.clear_form()
            return

        row_idx = selected_rows[0].row()
        self.current_fornecedor_id = int(self.table_fornecedores.item(row_idx, 0).text())
        self.nome_input.setText(self.table_fornecedores.item(row_idx, 1).text())
        self.contato_input.setText(self.table_fornecedores.item(row_idx, 2).text())
        self.telefone_input.setText(self.table_fornecedores.item(row_idx, 3).text())
        self.email_input.setText(self.table_fornecedores.item(row_idx, 4).text())
        self.prazo_entrega_input.setText(self.table_fornecedores.item(row_idx, 5).text()) # Carrega o prazo_entrega

        self.btn_delete.setEnabled(True)
        self.btn_save.setText("Atualizar")
        self.btn_save.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "edit.png")))
        if self.main_window:
            self.main_window.show_status_message(f"Fornecedor ID {self.current_fornecedor_id} selecionado para edição.", 2000)


    def delete_fornecedor(self) -> None:
        """Exclui o fornecedor selecionado."""
        if self.current_fornecedor_id is None:
            QMessageBox.warning(self, "Excluir Fornecedor", "Nenhum fornecedor selecionado para exclusão.")
            return

        confirm = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Tem certeza que deseja excluir o fornecedor '{self.nome_input.text()}' (ID: {self.current_fornecedor_id})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            success, message = database_manager.delete_fornecedor(self.current_fornecedor_id)
            if success:
                QMessageBox.information(self, "Sucesso", "Fornecedor excluído com sucesso!")
                if self.main_window:
                    self.main_window.show_status_message("Fornecedor excluído com sucesso!", 3000)
                logging.info(f"Fornecedor ID {self.current_fornecedor_id} excluído.")
            else:
                QMessageBox.critical(self, "Erro", f"Erro ao excluir fornecedor: {message}")
                if self.main_window:
                    self.main_window.show_status_message(f"Erro ao excluir fornecedor: {message}", 5000)
                logging.error(f"Falha ao excluir fornecedor ID {self.current_fornecedor_id}: {message}")
            self.load_fornecedores_to_table()
            self.clear_form()

def abrir_tela_cadastro_fornecedor(janela_principal: Optional[QDialog]):
    """
    Função para instanciar e exibir a janela de Cadastro de Fornecedores.
    """
    dialog = CadastroFornecedorWindow(janela_principal)
    dialog.exec()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    database_manager.create_tables()
    if not database_manager.get_all_fornecedores():
        database_manager.add_fornecedor("Fornecedor Teste X", "Contato X", "11987654321", "email@x.com", 5)
        database_manager.add_fornecedor("Fornecedor Teste Y", "Contato Y", "21912345678", "email@y.com", 7)
    dialog = CadastroFornecedorWindow(None)
    dialog.exec()
    app.exec()