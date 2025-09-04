import sys
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFrame, QDateEdit, QComboBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon
import os
import database_manager
import logging

logging.basicConfig(filename='almoxarifado.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')

class CadastroFerramentaWindow(QDialog):
    def __init__(self, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.main_window = parent
        self.setWindowTitle("Cadastro de Ferramentas")
        self.setGeometry(100, 100, 900, 650)
        self.current_ferramenta_id: Optional[int] = None
        self.setup_ui()
        self.load_ferramentas_to_table()
        self.clear_form()

    def setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        form_frame = QFrame(objectName="formFrame")
        form_layout = QGridLayout(form_frame)
        form_layout.setContentsMargins(15, 15, 15, 15)

        form_layout.addWidget(QLabel("Código:"), 0, 0)
        self.input_codigo = QLineEdit(placeholderText="Ex: FER001")
        form_layout.addWidget(self.input_codigo, 0, 1)

        form_layout.addWidget(QLabel("Nome:"), 1, 0)
        self.input_nome = QLineEdit(placeholderText="Ex: Chave de Fenda Phillips")
        form_layout.addWidget(self.input_nome, 1, 1)

        form_layout.addWidget(QLabel("Descrição:"), 2, 0)
        self.input_descricao = QLineEdit(placeholderText="Detalhes da ferramenta (tamanho, marca, etc.)")
        form_layout.addWidget(self.input_descricao, 2, 1)

        form_layout.addWidget(QLabel("Localização:"), 3, 0)
        self.input_localizacao = QLineEdit(placeholderText="Ex: Armário A, Gaveta 3")
        form_layout.addWidget(self.input_localizacao, 3, 1)

        form_layout.addWidget(QLabel("Status:"), 4, 0)
        self.combo_status = QComboBox()
        self.combo_status.addItems(["Disponível", "Em Uso", "Empréstado", "Manutenção", "Perdido", "Baixado"])
        form_layout.addWidget(self.combo_status, 4, 1)

        form_layout.addWidget(QLabel("Data de Aquisição:"), 5, 0)
        self.input_data_aquisicao = QDateEdit(QDate.currentDate(), calendarPopup=True, displayFormat="yyyy-MM-dd")
        form_layout.addWidget(self.input_data_aquisicao, 5, 1)
        main_layout.addWidget(form_frame)

        buttons_layout = QHBoxLayout()
        self.btn_save = QPushButton("Salvar", clicked=self.save_ferramenta)
        self.btn_save.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "save.png")))
        buttons_layout.addWidget(self.btn_save)

        self.btn_clear = QPushButton("Limpar", clicked=self.clear_form, objectName="secondaryButton")
        self.btn_clear.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "clear.png")))
        buttons_layout.addWidget(self.btn_clear)

        self.btn_delete = QPushButton("Excluir", clicked=self.delete_ferramenta, enabled=False, objectName="dangerButton")
        self.btn_delete.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "delete.png")))
        buttons_layout.addWidget(self.btn_delete)
        main_layout.addLayout(buttons_layout)

        table_frame = QFrame(objectName="tableFrame")
        table_layout = QVBoxLayout(table_frame)
        self.table_ferramentas = QTableWidget()
        self.table_ferramentas.setColumnCount(7)
        self.table_ferramentas.setHorizontalHeaderLabels(["ID", "Código", "Nome", "Descrição", "Localização", "Status", "Data Aquisição"])
        self.table_ferramentas.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_ferramentas.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_ferramentas.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_ferramentas.itemSelectionChanged.connect(self.load_selected_ferramenta_to_form)
        table_layout.addWidget(self.table_ferramentas)
        main_layout.addWidget(table_frame)

    def load_ferramentas_to_table(self) -> None:
        self.table_ferramentas.setRowCount(0)
        ferramentas = database_manager.get_all_ferramentas()
        self.table_ferramentas.setRowCount(len(ferramentas))
        for row_idx, ferramenta in enumerate(ferramentas):
            self.table_ferramentas.setItem(row_idx, 0, QTableWidgetItem(str(ferramenta['id'])))
            self.table_ferramentas.setItem(row_idx, 1, QTableWidgetItem(ferramenta['codigo']))
            self.table_ferramentas.setItem(row_idx, 2, QTableWidgetItem(ferramenta['nome']))
            self.table_ferramentas.setItem(row_idx, 3, QTableWidgetItem(ferramenta.get('descricao', '')))
            self.table_ferramentas.setItem(row_idx, 4, QTableWidgetItem(ferramenta.get('localizacao', '')))
            self.table_ferramentas.setItem(row_idx, 5, QTableWidgetItem(ferramenta.get('status', '')))
            self.table_ferramentas.setItem(row_idx, 6, QTableWidgetItem(ferramenta.get('data_aquisicao', '')))

    def load_selected_ferramenta_to_form(self) -> None:
        selected_items = self.table_ferramentas.selectedItems()
        if not selected_items:
            self.clear_form()
            return
        row = selected_items[0].row()
        self.current_ferramenta_id = int(self.table_ferramentas.item(row, 0).text())
        ferramenta = database_manager.get_ferramenta_by_id(self.current_ferramenta_id)
        if not ferramenta: return

        self.input_codigo.setText(ferramenta['codigo'])
        self.input_nome.setText(ferramenta['nome'])
        self.input_descricao.setText(ferramenta.get('descricao', ''))
        self.input_localizacao.setText(ferramenta.get('localizacao', ''))
        self.combo_status.setCurrentText(ferramenta.get('status', 'Disponível'))
        if ferramenta.get('data_aquisicao'):
            self.input_data_aquisicao.setDate(QDate.fromString(ferramenta['data_aquisicao'], "yyyy-MM-dd"))
        
        self.btn_delete.setEnabled(True)
        self.btn_save.setText("Atualizar")

    def clear_form(self) -> None:
        self.input_codigo.clear()
        self.input_nome.clear()
        self.input_descricao.clear()
        self.input_localizacao.clear()
        self.combo_status.setCurrentIndex(0)
        self.input_data_aquisicao.setDate(QDate.currentDate())
        self.current_ferramenta_id = None
        self.btn_delete.setEnabled(False)
        self.btn_save.setText("Salvar")
        self.table_ferramentas.clearSelection()

    def save_ferramenta(self) -> None:
        codigo = self.input_codigo.text().strip().upper()
        nome = self.input_nome.text().strip()
        descricao = self.input_descricao.text().strip()
        localizacao = self.input_localizacao.text().strip()
        status = self.combo_status.currentText()
        data_aquisicao = self.input_data_aquisicao.date().toString("yyyy-MM-dd")

        if not codigo or not nome:
            QMessageBox.warning(self, "Campos Obrigatórios", "Código e Nome são obrigatórios.")
            return

        if self.current_ferramenta_id is None:
            # CORREÇÃO: A chamada agora espera apenas 2 valores de retorno.
            success, message = database_manager.add_ferramenta(
                codigo, nome, descricao, status, localizacao, data_aquisicao
            )
        else:
            success, message = database_manager.update_ferramenta(
                self.current_ferramenta_id, codigo, nome, descricao, status, localizacao, data_aquisicao
            )

        if success:
            QMessageBox.information(self, "Sucesso", message)
            self.load_ferramentas_to_table()
            self.clear_form()
        else:
            QMessageBox.critical(self, "Erro", message)

    def delete_ferramenta(self) -> None:
        if self.current_ferramenta_id is None: return
        reply = QMessageBox.question(self, "Confirmar Exclusão", "Tem certeza que deseja excluir esta ferramenta?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            success, message = database_manager.delete_ferramenta(self.current_ferramenta_id)
            if success:
                QMessageBox.information(self, "Sucesso", message)
                self.load_ferramentas_to_table()
                self.clear_form()
            else:
                QMessageBox.critical(self, "Erro", f"Erro ao excluir: {message}")

def abrir_tela_cadastro_ferramenta(janela_principal: Optional[QDialog]):
    dialog = CadastroFerramentaWindow(janela_principal)
    dialog.exec()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    database_manager.create_tables()
    dialog = CadastroFerramentaWindow()
    dialog.show()
    sys.exit(app.exec())