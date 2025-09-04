import sys
from typing import Optional, List
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

logging.basicConfig(
    filename='almoxarifado.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

class AuditoriaWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.setWindowTitle("Logs de Auditoria")
        self.setGeometry(100, 100, 1200, 700)
        self.setup_ui()
        self.load_initial_data()
        self.generate_report()

    def setup_ui(self) -> None:
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
        filter_layout.addWidget(QLabel("Filtrar por Ação:"), 1, 0)
        self.action_filter_combo = QComboBox()
        self.action_filter_combo.addItem("Todos", "Todos")
        filter_layout.addWidget(self.action_filter_combo, 1, 1)
        filter_layout.addWidget(QLabel("Filtrar por Usuário:"), 1, 2)
        self.user_filter_combo = QComboBox()
        self.user_filter_combo.addItem("Todos", "Todos")
        filter_layout.addWidget(self.user_filter_combo, 1, 3)
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
        filter_layout.addLayout(btn_layout, 2, 0, 1, 4, Qt.AlignmentFlag.AlignRight)
        main_layout.addWidget(filter_frame)
        table_frame = QFrame()
        table_frame.setObjectName("tableFrame")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(15, 15, 15, 15)
        table_layout.setSpacing(10)
        self.tabela_auditoria = QTableWidget()
        self.tabela_auditoria.setColumnCount(5)
        self.tabela_auditoria.setHorizontalHeaderLabels(["ID", "Data/Hora", "Referência (Usuário)", "Ação", "Detalhes"])
        self.tabela_auditoria.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela_auditoria.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) # Detalhes
        self.tabela_auditoria.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela_auditoria.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table_layout.addWidget(self.tabela_auditoria)
        main_layout.addWidget(table_frame)

    def load_initial_data(self) -> None:
        all_logs = database_manager.get_auditoria_logs()
        if not all_logs: return
        actions = sorted({log['acao'] for log in all_logs if log['acao']})
        users = sorted({log['referencia'] for log in all_logs if log['referencia']})
        self.action_filter_combo.clear()
        self.action_filter_combo.addItem("Todos", "Todos")
        self.user_filter_combo.clear()
        self.user_filter_combo.addItem("Todos", "Todos")
        for action in actions: self.action_filter_combo.addItem(action, action)
        for user in users: self.user_filter_combo.addItem(user, user)
        logging.info("Dados iniciais carregados para filtros de logs de auditoria.")
        if self.main_window: self.main_window.show_status_message("Dados de filtros de auditoria carregados.", 2000)

    def generate_report(self) -> None:
        start_date = self.start_date_input.date().toString("yyyy-MM-dd")
        end_date = self.end_date_input.date().toString("yyyy-MM-dd")
        selected_action = self.action_filter_combo.currentData()
        selected_user = self.user_filter_combo.currentData()
        self.tabela_auditoria.setRowCount(0)
        logs = database_manager.get_auditoria_logs(start_date, end_date, selected_action, selected_user)

        if logs:
            self.tabela_auditoria.setRowCount(len(logs))
            for row_idx, log in enumerate(logs):
                self.tabela_auditoria.setItem(row_idx, 0, QTableWidgetItem(str(log['id'])))
                # CORREÇÃO: A chave no DB é 'data_hora', não 'timestamp'. Usar .get() para segurança.
                self.tabela_auditoria.setItem(row_idx, 1, QTableWidgetItem(log.get('data_hora', 'N/A')))
                self.tabela_auditoria.setItem(row_idx, 2, QTableWidgetItem(log.get('referencia', 'N/A')))
                self.tabela_auditoria.setItem(row_idx, 3, QTableWidgetItem(log.get('acao', 'N/A')))
                self.tabela_auditoria.setItem(row_idx, 4, QTableWidgetItem(log.get('detalhes', 'N/A')))
            if self.main_window: self.main_window.show_status_message(f"Relatório de auditoria gerado: {len(logs)} registros.", 2000)
        else:
            QMessageBox.information(self, "Logs de Auditoria", "Nenhum log encontrado para os filtros selecionados.")
            if self.main_window: self.main_window.show_status_message("Nenhum log de auditoria encontrado.", 3000)
        logging.info(f"Relatório de auditoria gerado de {start_date} a {end_date}.")

    def export_to_csv(self) -> None:
        if self.tabela_auditoria.rowCount() == 0:
            QMessageBox.warning(self, "Exportar CSV", "Não há dados na tabela para exportar.")
            return

        file_name, _ = QFileDialog.getSaveFileName(self, "Salvar Logs de Auditoria", f"logs_auditoria_{datetime.date.today().strftime('%Y%m%d')}.csv", "Arquivos CSV (*.csv)")
        if file_name:
            try:
                with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    header = [self.tabela_auditoria.horizontalHeaderItem(i).text() for i in range(self.tabela_auditoria.columnCount())]
                    writer.writerow(header)
                    for row in range(self.tabela_auditoria.rowCount()):
                        row_data = [self.tabela_auditoria.item(row, col).text() if self.tabela_auditoria.item(row, col) else "" for col in range(self.tabela_auditoria.columnCount())]
                        writer.writerow(row_data)
                QMessageBox.information(self, "Exportar CSV", f"Dados exportados com sucesso para:\n{file_name}")
                if self.main_window: self.main_window.show_status_message("Logs exportados para CSV.", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Erro de Exportação", f"Ocorreu um erro ao exportar para CSV: {e}")
                logging.error(f"Erro ao exportar logs de auditoria para CSV: {e}")

    def imprimir_relatorio_pdf(self) -> None:
        if self.tabela_auditoria.rowCount() == 0:
            QMessageBox.warning(self, "Imprimir PDF", "Não há dados na tabela para imprimir.")
            return

        file_name, _ = QFileDialog.getSaveFileName(self, "Salvar Logs de Auditoria (PDF)", f"relatorio_auditoria_{datetime.date.today().strftime('%Y%m%d')}.pdf", "Arquivos PDF (*.pdf)")
        if not file_name: return

        try:
            doc = SimpleDocTemplate(file_name, pagesize=landscape(A4), rightMargin=10*mm, leftMargin=10*mm, topMargin=10*mm, bottomMargin=10*mm)
            styles = getSampleStyleSheet()
            story = []
            title_style = styles['h1']
            title_style.alignment = TA_CENTER
            story.append(Paragraph("Relatório de Logs de Auditoria", title_style))
            story.append(Spacer(1, 5*mm))
            filter_info_style = styles['Normal']
            filter_info_style.alignment = TA_LEFT
            story.append(Paragraph(f"<b>Período:</b> {self.start_date_input.date().toString('dd/MM/yyyy')} a {self.end_date_input.date().toString('dd/MM/yyyy')}", filter_info_style))
            story.append(Paragraph(f"<b>Ação:</b> {self.action_filter_combo.currentText()}", filter_info_style))
            story.append(Paragraph(f"<b>Usuário:</b> {self.user_filter_combo.currentText()}", filter_info_style))
            story.append(Spacer(1, 5*mm))
            data = [[self.tabela_auditoria.horizontalHeaderItem(i).text() for i in range(self.tabela_auditoria.columnCount())]]
            for row_idx in range(self.tabela_auditoria.rowCount()):
                data.append([self.tabela_auditoria.item(row_idx, col_idx).text() if self.tabela_auditoria.item(row_idx, col_idx) else "" for col_idx in range(self.tabela_auditoria.columnCount())])
            
            # Aumentar a largura da coluna de detalhes
            col_widths = [20*mm, 40*mm, 40*mm, 50*mm, 100*mm]
            table = Table(data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#E7E7E7')),
                ('TEXTCOLOR', (0, 0), (-1, 0), black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (4, 1), (4, -1), 'LEFT'), # Alinhar detalhes à esquerda
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
                ('BOX', (0, 0), (-1, -1), 1, HexColor('#AAAAAA')),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
            ]))
            story.append(table)
            doc.build(story)
            QMessageBox.information(self, "Imprimir PDF", f"Relatório PDF gerado com sucesso em:\n{file_name}")
        except Exception as e:
            QMessageBox.critical(self, "Erro de Impressão", f"Ocorreu um erro ao gerar o PDF:\n{e}")
            logging.error(f"Erro ao gerar PDF de auditoria: {e}")

def abrir_tela_auditoria(janela_principal):
    dialog = AuditoriaWindow(janela_principal)
    dialog.exec()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    database_manager.create_tables()
    if not database_manager.get_auditoria_logs():
        database_manager.log_auditoria("Sistema", "START", "Aplicação Almoxarifado iniciada.")
        database_manager.log_auditoria("Cadastro Item", "Usuário1", "Novo item 'Parafuso M5' (PARF005) adicionado.")
    dialog = AuditoriaWindow()
    dialog.show()
    sys.exit(app.exec())