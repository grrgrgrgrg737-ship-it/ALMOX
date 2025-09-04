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

class CadastroTecnicoWindow(QDialog):
    """
    Janela para cadastro, edição e exclusão de técnicos.
    """

    def __init__(self, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.main_window = parent
        self.setWindowTitle("Cadastro de Técnicos")
        self.setGeometry(100, 100, 850, 600)
        self.current_tecnico_id: Optional[int] = None
        self.setup_ui()
        self.load_tecnicos_to_table()
        self.clear_form()

    def setup_ui(self) -> None:
        """Configura os elementos da interface do usuário."""
        main_layout = QVBoxLayout(self)

        # Formulário
        form_frame = QFrame(objectName="formFrame")
        form_layout = QGridLayout(form_frame)
        form_layout.setContentsMargins(15, 15, 15, 15)
        form_layout.setSpacing(10)

        form_layout.addWidget(QLabel("Nome:"), 0, 0)
        self.nome_input = QLineEdit(placeholderText="Nome completo do técnico")
        form_layout.addWidget(self.nome_input, 0, 1)

        form_layout.addWidget(QLabel("Matrícula:"), 1, 0)
        self.matricula_input = QLineEdit(placeholderText="Matrícula única do técnico")
        form_layout.addWidget(self.matricula_input, 1, 1)

        form_layout.addWidget(QLabel("Setor:"), 2, 0)
        self.setor_input = QLineEdit(placeholderText="Setor (Ex: Manutenção, TI, Elétrica)")
        form_layout.addWidget(self.setor_input, 2, 1)
        main_layout.addWidget(form_frame)

        # Botões de Ação
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Salvar", clicked=self.save_tecnico)
        self.btn_save.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "save.png")))
        btn_layout.addWidget(self.btn_save)

        self.btn_clear = QPushButton("Limpar", clicked=self.clear_form)
        self.btn_clear.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "clear.png")))
        self.btn_clear.setObjectName("secondaryButton")
        btn_layout.addWidget(self.btn_clear)

        self.btn_delete = QPushButton("Excluir", clicked=self.delete_tecnico, enabled=False)
        self.btn_delete.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "delete.png")))
        self.btn_delete.setObjectName("dangerButton")
        btn_layout.addWidget(self.btn_delete)
        main_layout.addLayout(btn_layout)

        # Tabela de Técnicos
        table_frame = QFrame(objectName="tableFrame")
        table_layout = QVBoxLayout(table_frame)
        self.table_tecnicos = QTableWidget()
        self.table_tecnicos.setColumnCount(4)
        self.table_tecnicos.setHorizontalHeaderLabels(["ID", "Nome", "Matrícula", "Setor"])
        self.table_tecnicos.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_tecnicos.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_tecnicos.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_tecnicos.itemSelectionChanged.connect(self.load_tecnico_to_form)
        table_layout.addWidget(self.table_tecnicos)
        main_layout.addWidget(table_frame)

    def clear_form(self):
        self.nome_input.clear()
        self.matricula_input.clear()
        self.setor_input.clear()
        self.current_tecnico_id = None
        self.btn_delete.setEnabled(False)
        self.btn_save.setText("Salvar")
        self.nome_input.setFocus()
        self.table_tecnicos.clearSelection()

    def save_tecnico(self) -> None:
        nome = self.nome_input.text().strip()
        matricula = self.matricula_input.text().strip()
        setor = self.setor_input.text().strip()

        if not nome or not matricula:
            QMessageBox.warning(self, "Erro de Validação", "Os campos 'Nome' e 'Matrícula' são obrigatórios.")
            return

        # Validação de matrícula duplicada
        existing_tecnico = database_manager.get_tecnico_by_matricula(matricula)
        if existing_tecnico and existing_tecnico['id'] != self.current_tecnico_id:
            QMessageBox.warning(self, "Matrícula Existente", f"A matrícula '{matricula}' já está em uso.")
            return

        if self.current_tecnico_id:
            # Atualizar técnico existente
            success, message = database_manager.update_tecnico(self.current_tecnico_id, nome, matricula, setor)
        else:
            # Cadastrar novo técnico
            success, message = database_manager.add_tecnico(nome, matricula, setor)

        if success:
            QMessageBox.information(self, "Sucesso", message)
            self.load_tecnicos_to_table()
            self.clear_form()
        else:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar técnico: {message}")
            logging.error(f"Falha ao salvar técnico '{nome}': {message}")

    def load_tecnicos_to_table(self) -> None:
        self.table_tecnicos.setRowCount(0)
        tecnicos = database_manager.get_all_tecnicos()
        if tecnicos:
            self.table_tecnicos.setRowCount(len(tecnicos))
            for row_idx, tec in enumerate(tecnicos):
                self.table_tecnicos.setItem(row_idx, 0, QTableWidgetItem(str(tec['id'])))
                self.table_tecnicos.setItem(row_idx, 1, QTableWidgetItem(tec['nome']))
                self.table_tecnicos.setItem(row_idx, 2, QTableWidgetItem(tec.get('matricula', '')))
                self.table_tecnicos.setItem(row_idx, 3, QTableWidgetItem(tec.get('setor', '')))

    def load_tecnico_to_form(self) -> None:
        selected_rows = self.table_tecnicos.selectedItems()
        if not selected_rows:
            self.clear_form()
            return

        row_idx = selected_rows[0].row()
        self.current_tecnico_id = int(self.table_tecnicos.item(row_idx, 0).text())
        
        tecnico = database_manager.get_tecnico_by_id(self.current_tecnico_id)
        if not tecnico: return

        self.nome_input.setText(tecnico['nome'])
        self.matricula_input.setText(tecnico.get('matricula', ''))
        self.setor_input.setText(tecnico.get('setor', ''))
        self.btn_delete.setEnabled(True)
        self.btn_save.setText("Atualizar")

    def delete_tecnico(self) -> None:
        if self.current_tecnico_id is None:
            QMessageBox.warning(self, "Excluir", "Nenhum técnico selecionado.")
            return

        reply = QMessageBox.question(self, "Confirmar Exclusão",
            f"Tem certeza que deseja excluir o técnico '{self.nome_input.text()}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            success, message = database_manager.delete_tecnico(self.current_tecnico_id)
            if success:
                QMessageBox.information(self, "Sucesso", "Técnico excluído com sucesso!")
                self.load_tecnicos_to_table()
                self.clear_form()
            else:
                QMessageBox.critical(self, "Erro", f"Erro ao excluir técnico: {message}")

def abrir_tela_cadastro_tecnico(janela_principal: Optional[QDialog]):
    dialog = CadastroTecnicoWindow(janela_principal)
    dialog.exec()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    database_manager.create_tables()
    dialog = CadastroTecnicoWindow()
    dialog.exec()