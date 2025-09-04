import sys
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFileDialog, QFrame
)
from PyQt6.QtCore import Qt
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
from reportlab.lib.colors import black, HexColor

class RelatorioEstoqueMinimoWindow(QDialog):
    """
    Janela para exibir um relatório de itens que estão abaixo do estoque mínimo.
    """
    def __init__(self, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.main_window = parent
        self.setWindowTitle("Relatório de Itens com Estoque Baixo")
        self.setGeometry(150, 150, 900, 600)
        self.setup_ui()
        self.load_report_data()

    def setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        title_label = QLabel("Itens que Precisam de Reposição")
        title_label.setObjectName("sectionHeaderLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # Tabela do relatório
        table_frame = QFrame(objectName="tableFrame")
        table_layout = QVBoxLayout(table_frame)
        self.table_report = QTableWidget()
        self.table_report.setColumnCount(5)
        self.table_report.setHorizontalHeaderLabels([
            "Código do Item", "Nome do Item", "Estoque Mínimo", "Estoque Atual", "Necessidade de Compra"
        ])
        self.table_report.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_report.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table_layout.addWidget(self.table_report)
        main_layout.addWidget(table_frame)
        
        # Botões de exportação
        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)
        
        self.btn_export_csv = QPushButton("Exportar para CSV", clicked=self.export_to_csv)
        self.btn_export_csv.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "export.png")))
        btn_layout.addWidget(self.btn_export_csv)

        self.btn_print_pdf = QPushButton("Imprimir PDF", clicked=self.imprimir_relatorio_pdf)
        self.btn_print_pdf.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "print_pdf.png")))
        btn_layout.addWidget(self.btn_print_pdf)
        main_layout.addLayout(btn_layout)


    def load_report_data(self) -> None:
        """Carrega os dados dos itens abaixo do estoque mínimo e popula a tabela."""
        self.table_report.setRowCount(0)
        report_data = database_manager.get_itens_abaixo_do_minimo()

        if not report_data:
            QMessageBox.information(self, "Estoque OK", "Nenhum item abaixo do estoque mínimo encontrado.")
            return

        self.table_report.setRowCount(len(report_data))
        for row_idx, item in enumerate(report_data):
            necessidade = item['estoque_minimo'] - item['total_estoque']
            
            self.table_report.setItem(row_idx, 0, QTableWidgetItem(item['codigo']))
            self.table_report.setItem(row_idx, 1, QTableWidgetItem(item['nome']))
            self.table_report.setItem(row_idx, 2, QTableWidgetItem(str(item['estoque_minimo'])))
            self.table_report.setItem(row_idx, 3, QTableWidgetItem(str(item['total_estoque'])))
            self.table_report.setItem(row_idx, 4, QTableWidgetItem(str(necessidade)))
            
            # Destaca a necessidade com cor
            self.table_report.item(row_idx, 4).setForeground(Qt.GlobalColor.red)
            self.table_report.item(row_idx, 4).setFont(self.font()) # Garante que a fonte seja negrito se necessário
            
        if self.main_window:
            self.main_window.show_status_message(f"Relatório de estoque baixo gerado: {len(report_data)} itens.", 3000)

    def export_to_csv(self):
        # Implementação da exportação para CSV
        if self.table_report.rowCount() == 0:
            QMessageBox.warning(self, "Exportar", "Não há dados para exportar.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Salvar CSV", "relatorio_compras.csv", "CSV Files (*.csv)")
        if path:
            try:
                with open(path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    headers = [self.table_report.horizontalHeaderItem(i).text() for i in range(self.table_report.columnCount())]
                    writer.writerow(headers)
                    for row in range(self.table_report.rowCount()):
                        row_data = [self.table_report.item(row, col).text() for col in range(self.table_report.columnCount())]
                        writer.writerow(row_data)
                QMessageBox.information(self, "Sucesso", "Relatório exportado com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao exportar CSV: {e}")

    def imprimir_relatorio_pdf(self):
        # Implementação da impressão em PDF
        if self.table_report.rowCount() == 0:
            QMessageBox.warning(self, "Imprimir", "Não há dados para imprimir.")
            return
            
        path, _ = QFileDialog.getSaveFileName(self, "Salvar PDF", "relatorio_compras.pdf", "PDF Files (*.pdf)")
        if path:
            try:
                doc = SimpleDocTemplate(path, pagesize=portrait(A4))
                styles = getSampleStyleSheet()
                elements = []
                
                elements.append(Paragraph("Relatório de Necessidade de Compras", styles['h1']))
                elements.append(Spacer(1, 12))
                
                data = [[self.table_report.horizontalHeaderItem(i).text() for i in range(self.table_report.columnCount())]]
                for row in range(self.table_report.rowCount()):
                    data.append([self.table_report.item(row, col).text() for col in range(self.table_report.columnCount())])
                    
                table = Table(data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), HexColor("#c0c0c0")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), HexColor("#f0f0f0")),
                    ('GRID', (0, 0), (-1, -1), 1, black)
                ]))
                elements.append(table)
                doc.build(elements)
                QMessageBox.information(self, "Sucesso", "Relatório salvo em PDF com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao gerar PDF: {e}")


def abrir_tela_relatorio_estoque_minimo(janela_principal):
    dialog = RelatorioEstoqueMinimoWindow(janela_principal)
    dialog.exec()