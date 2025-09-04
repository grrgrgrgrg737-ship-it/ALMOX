import sys
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFrame, QDateEdit, QComboBox, QTabWidget, QWidget
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon
import os
import datetime
import logging
import database_manager

logging.basicConfig(filename='almoxarifado.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')

class EmprestimoFerramentaWindow(QDialog):
    def __init__(self, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.main_window = parent
        self.setWindowTitle("Gestão de Empréstimos de Ferramentas")
        self.setGeometry(100, 100, 1200, 750)
        self.current_emprestimo_id: Optional[int] = None
        self.setup_ui()
        self.load_initial_data()
        self.load_emprestimos_to_table()

    def setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        
        tabs = QTabWidget()
        emprestimo_tab = QWidget()
        devolucao_tab = QWidget()
        tabs.addTab(emprestimo_tab, "Registrar Empréstimo")
        tabs.addTab(devolucao_tab, "Devolução e Consulta")

        self.setup_emprestimo_tab(emprestimo_tab)
        self.setup_devolucao_tab(devolucao_tab)
        
        main_layout.addWidget(tabs)

    def setup_emprestimo_tab(self, tab):
        layout = QVBoxLayout(tab)
        form_frame = QFrame(objectName="formFrame")
        form_layout = QGridLayout(form_frame)
        form_layout.setContentsMargins(15, 15, 15, 15)
        form_layout.setSpacing(10)

        form_layout.addWidget(QLabel("Ferramenta:"), 0, 0)
        self.ferramenta_combo = QComboBox()
        form_layout.addWidget(self.ferramenta_combo, 0, 1, 1, 2)
        
        form_layout.addWidget(QLabel("Técnico:"), 1, 0)
        self.tecnico_combo = QComboBox()
        form_layout.addWidget(self.tecnico_combo, 1, 1, 1, 2)

        form_layout.addWidget(QLabel("Data Empréstimo:"), 2, 0)
        self.data_emprestimo_dateedit = QDateEdit(calendarPopup=True, date=QDate.currentDate())
        form_layout.addWidget(self.data_emprestimo_dateedit, 2, 1)

        form_layout.addWidget(QLabel("Devolução Prevista:"), 3, 0)
        self.data_devolucao_prevista_dateedit = QDateEdit(calendarPopup=True, date=QDate.currentDate().addDays(7))
        form_layout.addWidget(self.data_devolucao_prevista_dateedit, 3, 1)

        form_layout.addWidget(QLabel("Observações (Saída):"), 4, 0)
        self.observacoes_input = QLineEdit(placeholderText="Condição da ferramenta na saída, etc.")
        form_layout.addWidget(self.observacoes_input, 4, 1, 1, 2)
        
        layout.addWidget(form_frame)

        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Registrar Empréstimo", clicked=self.save_emprestimo)
        self.btn_save.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "save.png")))
        btn_layout.addWidget(self.btn_save)

        self.btn_clear = QPushButton("Limpar Formulário", clicked=self.clear_form)
        self.btn_clear.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "clear.png")))
        btn_layout.addWidget(self.btn_clear)
        layout.addLayout(btn_layout)
        layout.addStretch(1)

    def setup_devolucao_tab(self, tab):
        layout = QVBoxLayout(tab)
        
        filter_frame = QFrame(objectName="formFrame")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.addWidget(QLabel("Status:"))
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems(["Todos", "Emprestado", "Devolvido", "Atrasado"])
        self.status_filter_combo.currentIndexChanged.connect(self.load_emprestimos_to_table)
        filter_layout.addWidget(self.status_filter_combo)
        filter_layout.addStretch(1)
        layout.addWidget(filter_frame)

        self.table_emprestimos = QTableWidget()
        self.table_emprestimos.setColumnCount(8)
        self.table_emprestimos.setHorizontalHeaderLabels(["ID", "Ferramenta", "Técnico", "Data Empréstimo", "Dev. Prevista", "Dev. Real", "Status", "Observações"])
        self.table_emprestimos.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_emprestimos.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_emprestimos.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_emprestimos.itemSelectionChanged.connect(self.on_emprestimo_selected)
        layout.addWidget(self.table_emprestimos)

        self.devolucao_frame = QFrame(objectName="formFrame")
        self.devolucao_frame.setEnabled(False)
        devolucao_layout = QGridLayout(self.devolucao_frame)
        
        self.devolucao_info_label = QLabel("Selecione um empréstimo 'Emprestado' para registrar a devolução.")
        self.devolucao_info_label.setStyleSheet("font-style: italic; color: #BDC3C7;")
        devolucao_layout.addWidget(self.devolucao_info_label, 0, 0, 1, 3)
        
        devolucao_layout.addWidget(QLabel("Data Devolução Real:"), 1, 0)
        self.data_devolucao_real_dateedit = QDateEdit(calendarPopup=True, date=QDate.currentDate())
        devolucao_layout.addWidget(self.data_devolucao_real_dateedit, 1, 1)

        devolucao_layout.addWidget(QLabel("Observações (Devolução):"), 2, 0)
        self.observacoes_devolucao_input = QLineEdit()
        devolucao_layout.addWidget(self.observacoes_devolucao_input, 2, 1, 1, 2)

        self.btn_confirmar_devolucao = QPushButton("Confirmar Devolução", clicked=self._confirmar_devolucao)
        devolucao_layout.addWidget(self.btn_confirmar_devolucao, 3, 2, Qt.AlignmentFlag.AlignRight)
        
        layout.addWidget(self.devolucao_frame)

    def load_initial_data(self):
        self.ferramenta_combo.clear()
        self.ferramenta_combo.addItem("Selecione a ferramenta...", None)
        ferramentas = database_manager.get_all_ferramentas()
        if ferramentas:
            for f in ferramentas:
                if f['status'] == 'Disponível':
                    self.ferramenta_combo.addItem(f"{f['codigo']} - {f['nome']}", f['id'])

        self.tecnico_combo.clear()
        self.tecnico_combo.addItem("Selecione o técnico...", None)
        tecnicos = database_manager.get_all_tecnicos()
        if tecnicos:
            for t in tecnicos:
                self.tecnico_combo.addItem(f"{t['nome']} ({t['matricula']})", t['id'])

    def load_emprestimos_to_table(self):
        self.table_emprestimos.setRowCount(0)
        status_filter = self.status_filter_combo.currentText()
        emprestimos = database_manager.get_emprestimos_ferramentas(status_filter=status_filter)

        if not emprestimos: return
        self.table_emprestimos.setRowCount(len(emprestimos))
        for row, emp in enumerate(emprestimos):
            self.table_emprestimos.setItem(row, 0, QTableWidgetItem(str(emp['id'])))
            self.table_emprestimos.setItem(row, 1, QTableWidgetItem(f"{emp['ferramenta_codigo']} - {emp['ferramenta_nome']}"))
            self.table_emprestimos.setItem(row, 2, QTableWidgetItem(emp['tecnico_nome']))
            self.table_emprestimos.setItem(row, 3, QTableWidgetItem(emp['data_emprestimo']))
            self.table_emprestimos.setItem(row, 4, QTableWidgetItem(emp['data_devolucao_prevista']))
            self.table_emprestimos.setItem(row, 5, QTableWidgetItem(emp.get('data_devolucao_real') or "Pendente"))
            self.table_emprestimos.setItem(row, 6, QTableWidgetItem(emp['status']))
            self.table_emprestimos.setItem(row, 7, QTableWidgetItem(emp.get('observacoes') or ""))
            
            if emp['status'] == 'Emprestado' and emp['data_devolucao_prevista'] < datetime.date.today().strftime('%Y-%m-%d'):
                for col in range(self.table_emprestimos.columnCount()):
                    self.table_emprestimos.item(row, col).setBackground(Qt.GlobalColor.darkRed)

    def on_emprestimo_selected(self):
        selected_rows = self.table_emprestimos.selectedItems()
        if not selected_rows:
            self.devolucao_frame.setEnabled(False)
            self.devolucao_info_label.setText("Selecione um empréstimo 'Emprestado' para registrar a devolução.")
            self.current_emprestimo_id = None
            return

        row = selected_rows[0].row()
        emprestimo_id = int(self.table_emprestimos.item(row, 0).text())
        status = self.table_emprestimos.item(row, 6).text()
        
        self.current_emprestimo_id = emprestimo_id

        if status == "Emprestado":
            ferramenta_nome = self.table_emprestimos.item(row, 1).text()
            tecnico_nome = self.table_emprestimos.item(row, 2).text()
            self.devolucao_frame.setEnabled(True)
            self.devolucao_info_label.setText(f"Devolvendo: <b>{ferramenta_nome}</b> (Técnico: {tecnico_nome})")
        else:
            self.devolucao_frame.setEnabled(False)
            self.devolucao_info_label.setText("Este item já foi devolvido ou o status não permite devolução.")

    def save_emprestimo(self):
        ferramenta_id = self.ferramenta_combo.currentData()
        tecnico_id = self.tecnico_combo.currentData()
        
        if ferramenta_id is None or tecnico_id is None:
            QMessageBox.warning(self, "Dados Incompletos", "Selecione a ferramenta e o técnico.")
            return

        ferramenta = database_manager.get_ferramenta_by_id(ferramenta_id)
        if not ferramenta or ferramenta['status'] != 'Disponível':
            QMessageBox.warning(self, "Ferramenta Indisponível", f"A ferramenta '{ferramenta['nome']}' não está disponível para empréstimo.")
            return

        data_emprestimo = self.data_emprestimo_dateedit.date().toString("yyyy-MM-dd")
        data_devolucao_prevista = self.data_devolucao_prevista_dateedit.date().toString("yyyy-MM-dd")
        observacoes = self.observacoes_input.text().strip()

        success, message, new_id = database_manager.add_emprestimo_ferramenta(ferramenta_id, tecnico_id, data_emprestimo, data_devolucao_prevista, observacoes)

        if success:
            tecnico = database_manager.get_tecnico_by_id(tecnico_id)
            nova_localizacao = f"Com {tecnico['nome']}"
            database_manager.update_ferramenta(ferramenta_id, ferramenta['codigo'], ferramenta['nome'], ferramenta['descricao'], "Emprestado", nova_localizacao, ferramenta['data_aquisicao'])

            QMessageBox.information(self, "Sucesso", message)
            self.load_emprestimos_to_table()
            self.load_initial_data()
            self.clear_form()
        else:
            QMessageBox.critical(self, "Erro", message)

    def _confirmar_devolucao(self):
        if self.current_emprestimo_id is None:
            QMessageBox.warning(self, "Erro", "Nenhum empréstimo selecionado para devolução.")
            return

        emprestimo = database_manager.get_emprestimo_ferramenta_by_id(self.current_emprestimo_id)
        if not emprestimo:
            QMessageBox.critical(self, "Erro", "Empréstimo não encontrado no banco de dados.")
            return

        data_devolucao_real = self.data_devolucao_real_dateedit.date().toString("yyyy-MM-dd")
        observacoes = self.observacoes_devolucao_input.text().strip()
        obs_final = f"{emprestimo.get('observacoes','') or ''} | Devolução: {observacoes}".strip(" | ")

        success, msg = database_manager.update_emprestimo_ferramenta(
            emprestimo['id'], emprestimo['ferramenta_id'], emprestimo['tecnico_id'],
            emprestimo['data_emprestimo'], emprestimo['data_devolucao_prevista'],
            data_devolucao_real, obs_final, "Devolvido"
        )
        
        if success:
            ferramenta = database_manager.get_ferramenta_by_id(emprestimo['ferramenta_id'])
            if ferramenta:
                database_manager.update_ferramenta(
                    ferramenta['id'], ferramenta['codigo'], ferramenta['nome'], 
                    ferramenta['descricao'], "Disponível", "Almoxarifado", ferramenta['data_aquisicao']
                )
            
            QMessageBox.information(self, "Sucesso", "Devolução registrada com sucesso!")
            self.load_emprestimos_to_table()
            self.load_initial_data()
            self.devolucao_frame.setEnabled(False)
            self.devolucao_info_label.setText("Selecione um empréstimo 'Emprestado' para registrar a devolução.")
            self.observacoes_devolucao_input.clear()
        else:
            QMessageBox.critical(self, "Erro", f"Falha ao registrar devolução: {msg}")

    def clear_form(self):
        self.ferramenta_combo.setCurrentIndex(0)
        self.tecnico_combo.setCurrentIndex(0)
        self.data_emprestimo_dateedit.setDate(QDate.currentDate())
        self.data_devolucao_prevista_dateedit.setDate(QDate.currentDate().addDays(7))
        self.observacoes_input.clear()
        
def abrir_tela_emprestimo_ferramenta(janela_principal: Optional[QDialog]):
    dialog = EmprestimoFerramentaWindow(janela_principal)
    dialog.exec()