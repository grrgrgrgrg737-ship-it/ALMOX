import sys
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
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

class CadastroDepositoWindow(QDialog):
    """
    Janela para cadastro, edição e exclusão de depósitos.
    """

    def __init__(self, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.main_window = parent
        self.setWindowTitle("Cadastro de Depósitos")
        self.setGeometry(100, 100, 800, 600)
        self.current_deposito_id: Optional[int] = None
        self.setup_ui()
        self.load_depositos_to_table()
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
        self.nome_input.setPlaceholderText("Nome do Depósito")
        form_layout.addWidget(self.nome_input, 0, 1)

        # Adicionado o campo de Localização
        form_layout.addWidget(QLabel("Localização:"), 1, 0)
        self.localizacao_input = QLineEdit()
        self.localizacao_input.setPlaceholderText("Localização física (ex: Setor A, Prateleira 3)")
        form_layout.addWidget(self.localizacao_input, 1, 1)

        main_layout.addWidget(form_frame)

        # Botões de Ação
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Salvar")
        self.btn_save.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "save.png")))
        self.btn_save.clicked.connect(self.save_deposito)
        btn_layout.addWidget(self.btn_save)

        self.btn_clear = QPushButton("Limpar")
        self.btn_clear.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "clear.png")))
        self.btn_clear.setObjectName("secondaryButton")
        self.btn_clear.clicked.connect(self.clear_form)
        btn_layout.addWidget(self.btn_clear)

        self.btn_delete = QPushButton("Excluir")
        self.btn_delete.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "delete.png")))
        self.btn_delete.setObjectName("dangerButton")
        self.btn_delete.clicked.connect(self.delete_deposito)
        self.btn_delete.setEnabled(False) # Desabilitado até um depósito ser selecionado
        btn_layout.addWidget(self.btn_delete)

        main_layout.addLayout(btn_layout)

        # Tabela de Depósitos
        table_frame = QFrame()
        table_frame.setObjectName("tableFrame")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(15, 15, 15, 15)
        table_layout.setSpacing(10)

        self.table_depositos = QTableWidget()
        self.table_depositos.setColumnCount(3) # Agora são 3 colunas: ID, Nome, Localização
        self.table_depositos.setHorizontalHeaderLabels([
            "ID", "Nome", "Localização"
        ])
        self.table_depositos.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_depositos.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_depositos.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_depositos.itemSelectionChanged.connect(self.load_deposito_to_form)
        table_layout.addWidget(self.table_depositos)

        main_layout.addWidget(table_frame)

    def clear_form(self) -> None:
        """Limpa todos os campos do formulário e redefine o ID atual."""
        self.nome_input.clear()
        self.localizacao_input.clear() # Limpa o campo de localização
        self.current_deposito_id = None
        self.btn_delete.setEnabled(False)
        self.btn_save.setText("Salvar")
        self.btn_save.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "save.png")))
        self.nome_input.setFocus()
        if self.main_window:
            self.main_window.show_status_message("Formulário de depósito limpo.", 2000)

    def save_deposito(self) -> None:
        """Salva um novo depósito ou atualiza um existente."""
        nome = self.nome_input.text().strip()
        localizacao = self.localizacao_input.text().strip() # Obter o texto do campo de localização

        if not nome:
            QMessageBox.warning(self, "Erro de Validação", "O campo 'Nome' é obrigatório.")
            if self.main_window:
                self.main_window.show_status_message("O campo 'Nome' é obrigatório.", 3000)
            return
        
        # Verifica se o depósito já existe pelo nome, exceto se for o próprio que está sendo editado
        existing_deposito = database_manager.get_deposito_by_name(nome)
        if existing_deposito and (self.current_deposito_id is None or existing_deposito['id'] != self.current_deposito_id):
            QMessageBox.warning(self, "Depósito Existente", "Um depósito com este nome já existe.")
            if self.main_window:
                self.main_window.show_status_message("Depósito com este nome já existe.", 3000)
            return


        if self.current_deposito_id:
            # Atualizar depósito existente
            success, message = database_manager.update_deposito(
                self.current_deposito_id, nome, localizacao
            )
            action = "atualizado"
        else:
            # Cadastrar novo depósito
            success, message = database_manager.add_deposito(nome, localizacao)
            action = "cadastrado"

        if success:
            QMessageBox.information(self, "Sucesso", f"Depósito {action} com sucesso!")
            if self.main_window:
                self.main_window.show_status_message(f"Depósito {action} com sucesso!", 3000)
            logging.info(f"Depósito '{nome}' {action} com sucesso.")
            self.load_depositos_to_table()
            self.clear_form()
        else:
            QMessageBox.critical(self, "Erro", f"Erro ao {action} depósito: {message}")
            if self.main_window:
                self.main_window.show_status_message(f"Erro ao {action} depósito: {message}", 5000)
            logging.error(f"Falha ao {action} depósito '{nome}': {message}")


    def load_depositos_to_table(self) -> None:
        """Carrega todos os depósitos do banco de dados para a tabela."""
        self.table_depositos.setRowCount(0)
        depositos = database_manager.get_all_depositos()
        if depositos:
            self.table_depositos.setRowCount(len(depositos))
            for row_idx, dep in enumerate(depositos):
                self.table_depositos.setItem(row_idx, 0, QTableWidgetItem(str(dep['id'])))
                self.table_depositos.setItem(row_idx, 1, QTableWidgetItem(dep['nome']))
                self.table_depositos.setItem(row_idx, 2, QTableWidgetItem(dep['localizacao'])) # Adicionado localização
        logging.info("Depósitos carregados na tabela.")
        if self.main_window:
            self.main_window.show_status_message("Tabela de depósitos atualizada.", 2000)

    def load_deposito_to_form(self) -> None:
        """Carrega os dados do depósito selecionado na tabela para o formulário."""
        selected_rows = self.table_depositos.selectedItems()
        if not selected_rows:
            self.clear_form()
            return

        row_idx = selected_rows[0].row()
        self.current_deposito_id = int(self.table_depositos.item(row_idx, 0).text())
        self.nome_input.setText(self.table_depositos.item(row_idx, 1).text())
        self.localizacao_input.setText(self.table_depositos.item(row_idx, 2).text()) # Carrega localização

        self.btn_delete.setEnabled(True)
        self.btn_save.setText("Atualizar")
        self.btn_save.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "edit.png")))
        if self.main_window:
            self.main_window.show_status_message(f"Depósito ID {self.current_deposito_id} selecionado para edição.", 2000)

    def delete_deposito(self) -> None:
        """Exclui o depósito selecionado."""
        if self.current_deposito_id is None:
            QMessageBox.warning(self, "Excluir Depósito", "Nenhum depósito selecionado para exclusão.")
            return

        confirm = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Tem certeza que deseja excluir o depósito '{self.nome_input.text()}' (ID: {self.current_deposito_id})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            success, message = database_manager.delete_deposito(self.current_deposito_id)
            if success:
                QMessageBox.information(self, "Sucesso", "Depósito excluído com sucesso!")
                if self.main_window:
                    self.main_window.show_status_message("Depósito excluído com sucesso!", 3000)
                logging.info(f"Depósito ID {self.current_deposito_id} excluído.")
            else:
                QMessageBox.critical(self, "Erro", f"Erro ao excluir depósito: {message}")
                if self.main_window:
                    self.main_window.show_status_message(f"Erro ao excluir depósito: {message}", 5000)
                logging.error(f"Falha ao excluir depósito ID {self.current_deposito_id}: {message}")
            self.load_depositos_to_table()
            self.clear_form()

def abrir_tela_cadastro_deposito(janela_principal: Optional[QDialog]):
    """
    Função para instanciar e exibir a janela de Cadastro de Depósitos.
    """
    dialog = CadastroDepositoWindow(janela_principal)
    dialog.exec()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    database_manager.create_tables()
    if not database_manager.get_all_depositos():
        # Exemplo de adição com localização
        database_manager.add_deposito("Depósito Principal", "Almoxarifado Central")
        database_manager.add_deposito("Depósito Secundário", "Setor de Manutenção")
    dialog = CadastroDepositoWindow(None)
    dialog.exec()
    app.exec()