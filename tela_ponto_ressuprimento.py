import sys
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor
import database_manager
import logging

class PontoRessuprimentoWindow(QDialog):
    """
    Exibe um relatório inteligente de itens que atingiram ou ultrapassaram o ponto de ressuprimento.
    """
    def __init__(self, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.main_window = parent
        self.setWindowTitle("Relatório de Ponto de Ressuprimento")
        self.setGeometry(150, 150, 1000, 600)
        self.setup_ui()
        self.load_report_data()

    def setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        title_label = QLabel("Itens que Precisam de Compra (Ponto de Ressuprimento)")
        title_label.setObjectName("sectionHeaderLabel")
        main_layout.addWidget(title_label)

        table_frame = QFrame(objectName="tableFrame")
        table_layout = QVBoxLayout(table_frame)
        self.table_report = QTableWidget()
        self.table_report.setColumnCount(6)
        self.table_report.setHorizontalHeaderLabels([
            "Item", "Fornecedor", "Estoque Atual", "Consumo Médio Diário", "Lead Time (dias)", "Ponto de Ressuprimento"
        ])
        self.table_report.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table_layout.addWidget(self.table_report)
        main_layout.addWidget(table_frame)

    def load_report_data(self):
        self.table_report.setRowCount(0)
        # Analisa os últimos 90 dias para o consumo médio
        report_data = database_manager.get_ponto_ressuprimento_data(periodo_dias=90)
        
        if not report_data:
            QMessageBox.information(self, "Estoque OK", "Nenhum item atingiu o ponto de ressuprimento.")
            return

        self.table_report.setRowCount(len(report_data))
        for row, item in enumerate(report_data):
            self.table_report.setItem(row, 0, QTableWidgetItem(f"{item['item_codigo']} - {item['item_nome']}"))
            self.table_report.setItem(row, 1, QTableWidgetItem(item['fornecedor_nome']))
            self.table_report.setItem(row, 2, QTableWidgetItem(str(item['total_estoque'])))
            self.table_report.setItem(row, 3, QTableWidgetItem(f"{item['consumo_medio_diario']:.2f}"))
            self.table_report.setItem(row, 4, QTableWidgetItem(str(item['lead_time'])))
            self.table_report.setItem(row, 5, QTableWidgetItem(f"{item['ponto_ressuprimento']:.2f}"))

            # Destaque visual
            self.table_report.item(row, 2).setForeground(QBrush(QColor("red")))

def abrir_tela_ponto_ressuprimento(janela_principal):
    dialog = PontoRessuprimentoWindow(janela_principal)
    dialog.exec()