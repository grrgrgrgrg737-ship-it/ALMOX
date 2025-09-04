import sys
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QComboBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
import os
import database_manager

class AjusteEstoqueWindow(QDialog):
    estoque_ajustado = pyqtSignal()

    def __init__(self, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.main_window = parent
        self.setWindowTitle("Ajuste de Inventário")
        self.setGeometry(150, 150, 950, 650)
        self.setup_ui()
        self.load_depositos()
        self.table_inventario.itemChanged.connect(self.on_item_changed)

    def setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Selecione o Depósito para Inventariar:"))
        self.deposito_combo = QComboBox()
        self.deposito_combo.currentIndexChanged.connect(self.load_inventory_data)
        filter_layout.addWidget(self.deposito_combo)
        filter_layout.addStretch(1)
        main_layout.addLayout(filter_layout)

        self.table_inventario = QTableWidget()
        self.table_inventario.setColumnCount(5)
        self.table_inventario.setHorizontalHeaderLabels(["Item", "Código", "Qtd. Sistema", "Qtd. Contada (Editar)", "Divergência"])
        self.table_inventario.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_inventario.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        main_layout.addWidget(self.table_inventario)
        
        self.btn_confirmar_ajuste = QPushButton("Confirmar Ajuste das Divergências", clicked=self.confirmar_ajuste)
        self.btn_confirmar_ajuste.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "save.png")))
        self.btn_confirmar_ajuste.setEnabled(False)
        main_layout.addWidget(self.btn_confirmar_ajuste, alignment=Qt.AlignmentFlag.AlignRight)

    def load_depositos(self):
        self.deposito_combo.clear()
        self.deposito_combo.addItem("Selecione...", None)
        for d in database_manager.get_all_depositos():
            self.deposito_combo.addItem(d['nome'], d['id'])

    def load_inventory_data(self):
        deposito_id = self.deposito_combo.currentData()
        self.table_inventario.setRowCount(0)
        self.btn_confirmar_ajuste.setEnabled(False)
        if not deposito_id: return
        
        itens_filtrados = [item for item in database_manager.get_estoque_geral() if item['deposito_id'] == deposito_id]
        
        self.table_inventario.setRowCount(len(itens_filtrados))
        self.table_inventario.blockSignals(True)

        for row, item_data in enumerate(itens_filtrados):
            qtd_sistema = item_data['quantidade']
            self.table_inventario.setItem(row, 0, QTableWidgetItem(item_data['item_nome']))
            self.table_inventario.setItem(row, 1, QTableWidgetItem(item_data['item_codigo']))
            item_qtd_sistema = QTableWidgetItem(str(qtd_sistema)); item_qtd_sistema.setFlags(item_qtd_sistema.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_inventario.setItem(row, 2, item_qtd_sistema)
            self.table_inventario.setItem(row, 3, QTableWidgetItem(str(qtd_sistema)))
            item_divergencia = QTableWidgetItem("0"); item_divergencia.setFlags(item_divergencia.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_inventario.setItem(row, 4, item_divergencia)
            self.table_inventario.item(row, 0).setData(Qt.ItemDataRole.UserRole, item_data['item_id'])

        self.table_inventario.blockSignals(False)
        self.btn_confirmar_ajuste.setEnabled(True)
        self.table_inventario.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)

    def on_item_changed(self, item: QTableWidgetItem):
        if item.column() != 3: return
        row = item.row()
        try:
            qtd_sistema = int(self.table_inventario.item(row, 2).text())
            qtd_contada = int(item.text().strip() or 0)
        except (ValueError, AttributeError):
            qtd_contada = qtd_sistema
            
        divergencia = qtd_contada - qtd_sistema
        self.table_inventario.item(row, 4).setText(str(divergencia))

    def confirmar_ajuste(self):
        deposito_id = self.deposito_combo.currentData()
        if not deposito_id: return

        ajustes = [{'item_id': self.table_inventario.item(r, 0).data(Qt.ItemDataRole.UserRole), 
                    'divergencia': int(self.table_inventario.item(r, 4).text())} 
                   for r in range(self.table_inventario.rowCount()) if int(self.table_inventario.item(r, 4).text()) != 0]

        if not ajustes:
            QMessageBox.information(self, "Inventário", "Nenhuma divergência encontrada.")
            return

        if QMessageBox.question(self, "Confirmar", f"Realizar {len(ajustes)} ajustes no estoque?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            for ajuste in ajustes:
                database_manager.ajustar_estoque(ajuste['item_id'], deposito_id, ajuste['divergencia'], "Ajuste de inventário")
            QMessageBox.information(self, "Sucesso", "Ajustes realizados!")
            self.estoque_ajustado.emit()
            self.load_inventory_data()

def abrir_tela_ajuste_estoque(janela_principal):
    dialog = AjusteEstoqueWindow(janela_principal)
    dialog.exec()