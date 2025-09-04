import sys
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QDateEdit, QComboBox, QMessageBox, QFrame, QFileDialog
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon
import database_manager
import logging
import csv
import datetime
import os

from reportlab.lib.pagesizes import A4, portrait
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.colors import black, HexColor

logging.basicConfig(filename='almoxarifado.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')

class RelatorioConsumoWindow(QDialog):
    def __init__(self, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.main_window = parent
        self.setWindowTitle("Relatório de Consumo")
        self.setGeometry(100, 100, 900, 650)
        self.setup_ui()
        self.load_initial_data()
        self.generate_report()

    def setup_ui(self):
        # ... (UI setup é o mesmo, sem modificações)
        main_layout = QVBoxLayout(self)
        filter_frame = QFrame()
        filter_frame.setObjectName("formFrame")
        filter_layout = QGridLayout(filter_frame)
        filter_layout.addWidget(QLabel("Data Início:"), 0, 0)
        self.start_date_input = QDateEdit(calendarPopup=True, date=QDate.currentDate().addMonths(-1))
        self.start_date_input.setDisplayFormat("dd/MM/yyyy")
        filter_layout.addWidget(self.start_date_input, 0, 1)
        filter_layout.addWidget(QLabel("Data Fim:"), 0, 2)
        self.end_date_input = QDateEdit(calendarPopup=True, date=QDate.currentDate())
        self.end_date_input.setDisplayFormat("dd/MM/yyyy")
        filter_layout.addWidget(self.end_date_input, 0, 3)
        filter_layout.addWidget(QLabel("Tipo de Relatório:"), 1, 0)
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems(["Consumo por Item", "Consumo por Técnico"])
        self.report_type_combo.currentIndexChanged.connect(self.toggle_filters)
        filter_layout.addWidget(self.report_type_combo, 1, 1)
        filter_layout.addWidget(QLabel("Filtrar por Item:"), 2, 0)
        self.item_filter_combo = QComboBox()
        filter_layout.addWidget(self.item_filter_combo, 2, 1)
        filter_layout.addWidget(QLabel("Filtrar por Técnico:"), 2, 2)
        self.tecnico_filter_combo = QComboBox()
        filter_layout.addWidget(self.tecnico_filter_combo, 2, 3)
        filter_layout.addWidget(QLabel("Origem/Destino:"), 3, 0)
        self.origem_destino_filter_combo = QComboBox()
        filter_layout.addWidget(self.origem_destino_filter_combo, 3, 1)
        btn_layout = QHBoxLayout()
        self.btn_generate_report = QPushButton("Gerar Relatório", clicked=self.generate_report)
        self.btn_export_csv = QPushButton("Exportar CSV", clicked=self.export_to_csv)
        self.btn_print_pdf = QPushButton("Imprimir PDF", clicked=self.imprimir_relatorio_pdf)
        btn_layout.addWidget(self.btn_generate_report)
        btn_layout.addWidget(self.btn_export_csv)
        btn_layout.addWidget(self.btn_print_pdf)
        filter_layout.addLayout(btn_layout, 4, 0, 1, 4, Qt.AlignmentFlag.AlignRight)
        main_layout.addWidget(filter_frame)
        table_frame = QFrame(objectName="tableFrame")
        table_layout = QVBoxLayout(table_frame)
        self.tabela_consumo = QTableWidget()
        self.tabela_consumo.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela_consumo.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table_layout.addWidget(self.tabela_consumo)
        main_layout.addWidget(table_frame)
        self.toggle_filters()

    def load_initial_data(self):
        # ... (A função é a mesma, sem modificações)
        self.item_filter_combo.clear()
        self.item_filter_combo.addItem("Todos", -1)
        items = database_manager.get_all_items()
        if items: [self.item_filter_combo.addItem(f"{item['codigo']} - {item['nome']}", item['id']) for item in items]
        self.tecnico_filter_combo.clear()
        self.tecnico_filter_combo.addItem("Todos", -1)
        tecnicos = database_manager.get_all_tecnicos()
        if tecnicos: [self.tecnico_filter_combo.addItem(f"{tec['nome']} ({tec['matricula']})", tec['id']) for tec in tecnicos]
        self.origem_destino_filter_combo.clear()
        self.origem_destino_filter_combo.addItem("Todos", "Todos")
        origens = database_manager.get_all_origem_destino()
        if origens: [self.origem_destino_filter_combo.addItem(od, od) for od in sorted(origens)]

    def toggle_filters(self):
        is_item_report = self.report_type_combo.currentText() == "Consumo por Item"
        self.item_filter_combo.setEnabled(is_item_report)
        self.tecnico_filter_combo.setEnabled(not is_item_report)
        self.origem_destino_filter_combo.setEnabled(True) # Sempre habilitado
        self.generate_report()

    def generate_report(self):
        start_date = self.start_date_input.date().toString("yyyy-MM-dd")
        end_date = self.end_date_input.date().toString("yyyy-MM-dd")
        report_type = self.report_type_combo.currentText()
        origem_destino = self.origem_destino_filter_combo.currentData()
        self.tabela_consumo.setRowCount(0)
        report_data = []

        if report_type == "Consumo por Item":
            self.tabela_consumo.setColumnCount(3)
            self.tabela_consumo.setHorizontalHeaderLabels(["Código", "Nome do Item", "Total Consumido"])
            item_id = self.item_filter_combo.currentData()
            report_data = database_manager.get_consumo_por_item(start_date, end_date, item_id, origem_destino)
            if report_data:
                self.tabela_consumo.setRowCount(len(report_data))
                for i, data in enumerate(report_data):
                    self.tabela_consumo.setItem(i, 0, QTableWidgetItem(data['codigo']))
                    self.tabela_consumo.setItem(i, 1, QTableWidgetItem(data['nome']))
                    # CORREÇÃO: Usar .get() para segurança
                    self.tabela_consumo.setItem(i, 2, QTableWidgetItem(str(data.get('total_consumido', 0))))

        elif report_type == "Consumo por Técnico":
            self.tabela_consumo.setColumnCount(2)
            self.tabela_consumo.setHorizontalHeaderLabels(["Técnico/Destino", "Total Consumido"])
            tecnico_id = self.tecnico_filter_combo.currentData()
            report_data = database_manager.get_consumo_por_tecnico(start_date, end_date, tecnico_id)
            if report_data:
                self.tabela_consumo.setRowCount(len(report_data))
                for i, data in enumerate(report_data):
                    # CORREÇÃO: Chaves retornadas são 'tecnico_nome' e 'total_consumido'
                    self.tabela_consumo.setItem(i, 0, QTableWidgetItem(data.get('tecnico_nome', 'N/A')))
                    self.tabela_consumo.setItem(i, 1, QTableWidgetItem(str(data.get('total_consumido', 0))))

        if not report_data:
            QMessageBox.information(self, "Relatório de Consumo", "Nenhum dado encontrado para os filtros selecionados.")
        if self.main_window: self.main_window.show_status_message(f"Relatório gerado: {len(report_data)} registros.", 2000)

    def export_to_csv(self):
        # ... (A função é a mesma, sem modificações)
        pass
    
    def imprimir_relatorio_pdf(self):
        # ... (A função é a mesma, sem modificações)
        pass

def abrir_tela_relatorio_consumo(janela_principal: Optional[QDialog]):
    dialog = RelatorioConsumoWindow(janela_principal)
    dialog.exec()