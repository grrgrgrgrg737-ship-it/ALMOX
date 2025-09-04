import sys
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QDateEdit, QComboBox, QMessageBox, QFileDialog, QFrame
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon
import database_manager
import logging
import csv
import datetime
import os

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.colors import black, HexColor

logging.basicConfig(filename='almoxarifado.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')

class RelatorioMovimentacaoWindow(QDialog):
    def __init__(self, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.main_window = parent
        self.setWindowTitle("Relatório de Movimentação")
        self.setGeometry(100, 100, 1200, 700)
        self.setup_ui()
        self.load_initial_data()
        self.generate_report()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        filter_frame = QFrame()
        filter_frame.setObjectName("formFrame")
        filter_layout = QGridLayout(filter_frame)
        filter_layout.setContentsMargins(15, 15, 15, 15)
        filter_layout.setSpacing(10)
        filter_layout.addWidget(QLabel("Data Início:"), 0, 0)
        self.start_date_input = QDateEdit(calendarPopup=True)
        self.start_date_input.setDate(QDate.currentDate().addMonths(-1))
        self.start_date_input.setDisplayFormat("dd/MM/yyyy")
        filter_layout.addWidget(self.start_date_input, 0, 1)
        filter_layout.addWidget(QLabel("Data Fim:"), 0, 2)
        self.end_date_input = QDateEdit(calendarPopup=True)
        self.end_date_input.setDate(QDate.currentDate())
        self.end_date_input.setDisplayFormat("dd/MM/yyyy")
        filter_layout.addWidget(self.end_date_input, 0, 3)
        filter_layout.addWidget(QLabel("Filtrar por Item:"), 1, 0)
        self.item_filter_combo = QComboBox()
        self.item_filter_combo.addItem("Todos", -1)
        filter_layout.addWidget(self.item_filter_combo, 1, 1)
        filter_layout.addWidget(QLabel("Filtrar por Depósito:"), 1, 2)
        self.deposito_filter_combo = QComboBox()
        self.deposito_filter_combo.addItem("Todos", -1)
        filter_layout.addWidget(self.deposito_filter_combo, 1, 3)
        filter_layout.addWidget(QLabel("Tipo de Movimentação:"), 2, 0)
        self.tipo_movimentacao_combo = QComboBox()
        self.tipo_movimentacao_combo.addItems(["Todos", "Entrada", "Saída", "Ajuste_entrada", "Ajuste_saida"])
        filter_layout.addWidget(self.tipo_movimentacao_combo, 2, 1)
        filter_layout.addWidget(QLabel("Origem/Destino:"), 2, 2)
        self.origem_destino_filter_combo = QComboBox()
        self.origem_destino_filter_combo.addItem("Todos", "Todos")
        filter_layout.addWidget(self.origem_destino_filter_combo, 2, 3)
        btn_layout = QHBoxLayout()
        self.btn_generate_report = QPushButton("Gerar Relatório")
        self.btn_generate_report.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "report_generate.png")))
        self.btn_generate_report.clicked.connect(self.generate_report)
        btn_layout.addWidget(self.btn_generate_report)
        self.btn_export_csv = QPushButton("Exportar para CSV")
        self.btn_export_csv.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "export.png")))
        self.btn_export_csv.setObjectName("secondaryButton")
        self.btn_export_csv.clicked.connect(self.export_to_csv)
        btn_layout.addWidget(self.btn_export_csv)
        self.btn_print_pdf = QPushButton("Imprimir PDF")
        self.btn_print_pdf.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "print_pdf.png")))
        self.btn_print_pdf.setObjectName("secondaryButton")
        self.btn_print_pdf.clicked.connect(self.imprimir_relatorio_pdf)
        btn_layout.addWidget(self.btn_print_pdf)
        filter_layout.addLayout(btn_layout, 3, 0, 1, 4, Qt.AlignmentFlag.AlignRight)
        main_layout.addWidget(filter_frame)
        table_frame = QFrame()
        table_frame.setObjectName("tableFrame")
        table_layout = QVBoxLayout(table_frame)
        self.tabela_movimentacoes = QTableWidget()
        self.tabela_movimentacoes.setColumnCount(8)
        self.tabela_movimentacoes.setHorizontalHeaderLabels(["ID", "Item (Código - Nome)", "Tipo", "Qtd", "Data", "Depósito", "Origem/Destino", "Obs."])
        self.tabela_movimentacoes.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela_movimentacoes.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela_movimentacoes.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table_layout.addWidget(self.tabela_movimentacoes)
        main_layout.addWidget(table_frame)

    def load_initial_data(self):
        self.item_filter_combo.clear()
        self.item_filter_combo.addItem("Todos", -1)
        items = database_manager.get_all_items()
        if items: [self.item_filter_combo.addItem(f"{item['codigo']} - {item['nome']}", item['id']) for item in items]
        self.deposito_filter_combo.clear()
        self.deposito_filter_combo.addItem("Todos", -1)
        depositos = database_manager.get_all_depositos()
        if depositos: [self.deposito_filter_combo.addItem(deposito['nome'], deposito['id']) for deposito in depositos]
        self.origem_destino_filter_combo.clear()
        self.origem_destino_filter_combo.addItem("Todos", "Todos")
        origens_destinos = database_manager.get_all_origem_destino()
        if origens_destinos: [self.origem_destino_filter_combo.addItem(od, od) for od in sorted(origens_destinos)]
        if self.main_window: self.main_window.show_status_message("Dados para filtros carregados.", 2000)

    def generate_report(self):
        start_date = self.start_date_input.date().toString("yyyy-MM-dd")
        end_date = self.end_date_input.date().toString("yyyy-MM-dd")
        selected_item_id = self.item_filter_combo.currentData()
        selected_deposito_id = self.deposito_filter_combo.currentData()
        selected_tipo = self.tipo_movimentacao_combo.currentText()
        selected_origem_destino = self.origem_destino_filter_combo.currentData()

        self.tabela_movimentacoes.setRowCount(0)

        movimentacoes = database_manager.get_movimentacoes(
            start_date=start_date,
            end_date=end_date,
            item_id=selected_item_id,
            deposito_id=selected_deposito_id,
            tipo_movimentacao=selected_tipo,
            origem_destino_filter=selected_origem_destino
        )

        if movimentacoes:
            self.tabela_movimentacoes.setRowCount(len(movimentacoes))
            for row_idx, mov in enumerate(movimentacoes):
                self.tabela_movimentacoes.setItem(row_idx, 0, QTableWidgetItem(str(mov['id'])))
                self.tabela_movimentacoes.setItem(row_idx, 1, QTableWidgetItem(mov['item_display']))
                self.tabela_movimentacoes.setItem(row_idx, 2, QTableWidgetItem(mov['tipo_movimentacao'].replace('_', ' ').capitalize()))
                self.tabela_movimentacoes.setItem(row_idx, 3, QTableWidgetItem(str(mov['quantidade'])))
                self.tabela_movimentacoes.setItem(row_idx, 4, QTableWidgetItem(mov['data_movimentacao']))
                self.tabela_movimentacoes.setItem(row_idx, 5, QTableWidgetItem(mov['deposito_display']))
                self.tabela_movimentacoes.setItem(row_idx, 6, QTableWidgetItem(mov.get('origem_destino') or "N/A"))
                self.tabela_movimentacoes.setItem(row_idx, 7, QTableWidgetItem(mov.get('observacoes') or "N/A"))
            if self.main_window: self.main_window.show_status_message(f"Relatório gerado com {len(movimentacoes)} registros.", 2000)
        else:
            if self.main_window: self.main_window.show_status_message("Nenhum registro encontrado.", 2000)

    def export_to_csv(self):
        if self.tabela_movimentacoes.rowCount() == 0:
            QMessageBox.warning(self, "Exportar CSV", "Não há dados para exportar.")
            return
        file_name, _ = QFileDialog.getSaveFileName(self, "Salvar Relatório", f"relatorio_movimentacao_{datetime.date.today().strftime('%Y%m%d')}.csv", "CSV (*.csv)")
        if file_name:
            try:
                with open(file_name, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    headers = [self.tabela_movimentacoes.horizontalHeaderItem(i).text() for i in range(self.tabela_movimentacoes.columnCount())]
                    writer.writerow(headers)
                    for row in range(self.tabela_movimentacoes.rowCount()):
                        writer.writerow([self.tabela_movimentacoes.item(row, col).text() if self.tabela_movimentacoes.item(row, col) else "" for col in range(self.tabela_movimentacoes.columnCount())])
                QMessageBox.information(self, "Sucesso", "Relatório exportado para CSV com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao exportar CSV: {e}")

    def imprimir_relatorio_pdf(self):
        if self.tabela_movimentacoes.rowCount() == 0:
            QMessageBox.warning(self, "Imprimir PDF", "Não há dados para imprimir.")
            return
        file_name, _ = QFileDialog.getSaveFileName(self, "Salvar PDF", f"relatorio_movimentacao_{datetime.date.today().strftime('%Y%m%d')}.pdf", "PDF (*.pdf)")
        if file_name:
            try:
                doc = SimpleDocTemplate(file_name, pagesize=landscape(A4), rightMargin=10*mm, leftMargin=10*mm, topMargin=10*mm, bottomMargin=10*mm)
                styles = getSampleStyleSheet()
                elements = []

                # Title
                title_style = styles['h1']
                title_style.alignment = TA_CENTER
                title_style.textColor = HexColor('#002060')
                elements.append(Paragraph("Relatório de Movimentação de Estoque", title_style))
                elements.append(Spacer(1, 12*mm))

                # Table Data
                headers = [self.tabela_movimentacoes.horizontalHeaderItem(i).text() for i in range(self.tabela_movimentacoes.columnCount())]
                data = [headers]
                for row in range(self.tabela_movimentacoes.rowCount()):
                    row_data = [self.tabela_movimentacoes.item(row, col).text() if self.tabela_movimentacoes.item(row, col) else "" for col in range(self.tabela_movimentacoes.columnCount())]
                    data.append(row_data)

                # Create Table
                table = Table(data, repeatRows=1)
                style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#002060')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#FFFFFF')),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), HexColor('#DDEBF7')),
                    ('GRID', (0, 0), (-1, -1), 1, black)
                ])
                table.setStyle(style)
                elements.append(table)

                doc.build(elements)
                QMessageBox.information(self, "Sucesso", "Relatório salvo em PDF com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao gerar PDF: {e}")

def abrir_tela_relatorio_movimentacao(janela_principal):
    dialog = RelatorioMovimentacaoWindow(janela_principal)
    dialog.exec()
