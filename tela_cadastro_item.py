import sys
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QDateEdit, QFileDialog, QFrame, QCompleter
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIntValidator, QDoubleValidator, QIcon
import database_manager
import logging
import os
from io import BytesIO

# Imports necessários para a geração de PDF
from reportlab.lib.pagesizes import A7
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER

# Importa nosso gerenciador de QR Code
import qr_code_manager

class CadastroItemWindow(QDialog):
    def __init__(self, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.main_window = parent
        self.setWindowTitle("Cadastro de Itens")
        self.setGeometry(100, 100, 1000, 700)
        self.current_item_id: Optional[int] = None
        self.setup_ui()
        self.load_initial_data()
        self.load_items_to_table()
        self.clear_form(ask_confirmation=False)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        form_frame = QFrame(objectName="formFrame")
        form_layout = QGridLayout(form_frame)
        form_layout.setContentsMargins(15, 15, 15, 15)

        form_layout.addWidget(QLabel("Código:"), 0, 0)
        self.codigo_input = QLineEdit(placeholderText="Código único do item")
        form_layout.addWidget(self.codigo_input, 0, 1)

        form_layout.addWidget(QLabel("Nome:"), 1, 0)
        self.nome_input = QLineEdit(placeholderText="Nome descritivo do item")
        form_layout.addWidget(self.nome_input, 1, 1)

        form_layout.addWidget(QLabel("Descrição:"), 2, 0)
        self.descricao_input = QLineEdit(placeholderText="Detalhes adicionais (opcional)")
        form_layout.addWidget(self.descricao_input, 2, 1)

        form_layout.addWidget(QLabel("Unidade de Medida:"), 3, 0)
        self.unidade_medida_combo = QComboBox()
        self.unidade_medida_combo.addItems(["UN", "PC", "CX", "KG", "M", "L", "PAR"])
        form_layout.addWidget(self.unidade_medida_combo, 3, 1)

        form_layout.addWidget(QLabel("Estoque Mínimo:"), 4, 0)
        self.estoque_minimo_input = QLineEdit()
        self.estoque_minimo_input.setValidator(QIntValidator(0, 999999))
        form_layout.addWidget(self.estoque_minimo_input, 4, 1)

        form_layout.addWidget(QLabel("Preço de Custo (R$):"), 5, 0)
        self.preco_custo_input = QLineEdit()
        double_validator = QDoubleValidator(0.00, 9999999.99, 2)
        double_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.preco_custo_input.setValidator(double_validator)
        form_layout.addWidget(self.preco_custo_input, 5, 1)

        form_layout.addWidget(QLabel("Fornecedor Principal:"), 6, 0)
        self.fornecedor_combo = QComboBox()
        self.fornecedor_combo.setEditable(True)
        self.fornecedor_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.fornecedor_combo.completer().setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.fornecedor_combo.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        form_layout.addWidget(self.fornecedor_combo, 6, 1)

        form_layout.addWidget(QLabel("Data de Cadastro:"), 7, 0)
        self.data_cadastro_input = QDateEdit(QDate.currentDate(), calendarPopup=True, displayFormat="yyyy-MM-dd")
        form_layout.addWidget(self.data_cadastro_input, 7, 1)
        main_layout.addWidget(form_frame)

        buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Salvar", clicked=self.save_item, objectName="primaryButton")
        self.clear_button = QPushButton("Limpar", clicked=self.clear_form, objectName="secondaryButton")
        self.delete_button = QPushButton("Excluir", clicked=self.delete_item, enabled=False, objectName="dangerButton")

        # Botão de QR Code restaurado
        self.generate_qr_button = QPushButton("Gerar Etiqueta QR", clicked=self.generate_qr_label, enabled=False, objectName="secondaryButton")
        self.generate_qr_button.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "qr_code.png")))

        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.clear_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addWidget(self.generate_qr_button)
        main_layout.addLayout(buttons_layout)

        self.table_itens = QTableWidget()
        self.table_itens.setColumnCount(8)
        self.table_itens.setHorizontalHeaderLabels(["ID", "Código", "Nome", "Descrição", "UM", "Est. Mín.", "Preço Custo", "Fornecedor"])
        self.table_itens.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_itens.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_itens.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_itens.itemSelectionChanged.connect(self.on_selection_changed)
        main_layout.addWidget(self.table_itens)

    def load_initial_data(self):
        fornecedores = database_manager.get_all_fornecedores()
        self.fornecedor_combo.clear()
        if not fornecedores:
            self.fornecedor_combo.addItem("Cadastre um Fornecedor Primeiro", None)
            self.save_button.setEnabled(False)
        else:
            self.save_button.setEnabled(True)
            self.fornecedor_combo.addItem("Selecione ou digite para buscar...", None)
            for f in fornecedores:
                self.fornecedor_combo.addItem(f['nome'], f['id'])

    def load_items_to_table(self):
        self.table_itens.setRowCount(0)
        itens = database_manager.get_all_items()
        self.table_itens.setRowCount(len(itens))
        for row, item in enumerate(itens):
            self.table_itens.setItem(row, 0, QTableWidgetItem(str(item['id'])))
            self.table_itens.setItem(row, 1, QTableWidgetItem(item['codigo']))
            self.table_itens.setItem(row, 2, QTableWidgetItem(item['nome']))
            self.table_itens.setItem(row, 3, QTableWidgetItem(item.get('descricao', '')))
            self.table_itens.setItem(row, 4, QTableWidgetItem(item['unidade']))
            self.table_itens.setItem(row, 5, QTableWidgetItem(str(item.get('estoque_minimo', 0))))
            preco_str = f"R$ {item.get('preco_unitario', 0):.2f}".replace('.', ',')
            self.table_itens.setItem(row, 6, QTableWidgetItem(preco_str))
            self.table_itens.setItem(row, 7, QTableWidgetItem(item['fornecedor_nome']))

    def on_selection_changed(self):
        if not self.table_itens.selectedItems():
            self.clear_form(ask_confirmation=False)
            return

        row = self.table_itens.selectedItems()[0].row()
        self.current_item_id = int(self.table_itens.item(row, 0).text())
        item = database_manager.get_item_by_id(self.current_item_id)
        if not item: return

        self.codigo_input.setText(item['codigo'])
        self.nome_input.setText(item['nome'])
        self.descricao_input.setText(item.get('descricao', ''))
        self.unidade_medida_combo.setCurrentText(item['unidade'])
        self.estoque_minimo_input.setText(str(item.get('estoque_minimo', 0)))
        self.preco_custo_input.setText(str(item.get('preco_unitario', 0.0)).replace('.', ','))

        index = self.fornecedor_combo.findData(item['fornecedor_id'])
        self.fornecedor_combo.setCurrentIndex(index if index != -1 else 0)

        if item.get('data_cadastro'):
            self.data_cadastro_input.setDate(QDate.fromString(item['data_cadastro'], "yyyy-MM-dd"))

        self.save_button.setText("Atualizar")
        self.delete_button.setEnabled(True)
        self.generate_qr_button.setEnabled(True)

    def clear_form(self, ask_confirmation=True):
        if ask_confirmation:
            is_dirty = any([self.codigo_input.text(), self.nome_input.text(), self.estoque_minimo_input.text(), self.preco_custo_input.text()])
            if is_dirty:
                reply = QMessageBox.question(self, "Limpar Formulário",
                                             "Deseja limpar todos os campos preenchidos?",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                             QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.No:
                    return

        self.codigo_input.clear()
        self.nome_input.clear()
        self.descricao_input.clear()
        self.unidade_medida_combo.setCurrentIndex(0)
        self.estoque_minimo_input.clear()
        self.preco_custo_input.clear()
        self.fornecedor_combo.setCurrentIndex(0)
        self.data_cadastro_input.setDate(QDate.currentDate())
        self.current_item_id = None
        self.save_button.setText("Salvar")
        self.delete_button.setEnabled(False)
        self.generate_qr_button.setEnabled(False)
        self.table_itens.clearSelection()

    def save_item(self):
        codigo = self.codigo_input.text().strip().upper()
        nome = self.nome_input.text().strip()
        fornecedor_id = self.fornecedor_combo.currentData()

        if not all([codigo, nome]) or fornecedor_id is None:
            QMessageBox.warning(self, "Campos Obrigatórios", "Código, Nome e Fornecedor são obrigatórios.")
            return

        try:
            descricao = self.descricao_input.text().strip()
            unidade = self.unidade_medida_combo.currentText()
            estoque_minimo = int(self.estoque_minimo_input.text() or 0)
            preco_unitario = float(self.preco_custo_input.text().replace(',', '.') or 0.0)
            data_cadastro = self.data_cadastro_input.date().toString("yyyy-MM-dd")
        except ValueError:
            QMessageBox.warning(self, "Erro de Validação", "Estoque Mínimo e Preço devem ser números válidos.")
            return

        if self.current_item_id is None:
            success, message = database_manager.add_item(codigo, nome, descricao, unidade, estoque_minimo, preco_unitario, fornecedor_id, data_cadastro)
        else:
            success, message = database_manager.update_item(self.current_item_id, codigo, nome, descricao, unidade, estoque_minimo, preco_unitario, fornecedor_id, data_cadastro)

        if success:
            QMessageBox.information(self, "Sucesso", message)
            self.load_items_to_table()
            self.clear_form(ask_confirmation=False)
        else:
            QMessageBox.critical(self, "Erro", message)

    def delete_item(self):
        if self.current_item_id is None: return
        reply = QMessageBox.question(self, "Confirmar Exclusão", f"Tem certeza que deseja excluir o item '{self.nome_input.text()}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            success, message = database_manager.delete_item(self.current_item_id)
            if success:
                QMessageBox.information(self, "Sucesso", message)
                self.load_items_to_table()
                self.clear_form(ask_confirmation=False)
            else:
                QMessageBox.critical(self, "Erro", f"Erro ao excluir item: {message}")

    def generate_qr_label(self):
        """Gera uma etiqueta QR Code para o item selecionado em formato PDF."""
        if self.current_item_id is None:
            QMessageBox.warning(self, "Seleção Necessária", "Selecione um item na tabela para gerar a etiqueta.")
            return

        item_data = database_manager.get_item_by_id(self.current_item_id)
        if not item_data:
            QMessageBox.critical(self, "Erro", "Não foi possível encontrar os dados do item selecionado.")
            return

        item_code = item_data['codigo']
        item_name = item_data['nome']

        # Gera a imagem do QR Code usando o nosso gerenciador
        qr_pil_img = qr_code_manager.QRCodeGenerator.generate_qr_code_pil_image(item_code)
        if not qr_pil_img:
            QMessageBox.critical(self, "Erro", "Falha ao gerar a imagem do QR Code.")
            return

        # Pede ao usuário para escolher onde salvar o arquivo PDF
        path, _ = QFileDialog.getSaveFileName(self, "Salvar Etiqueta QR", f"Etiqueta_{item_code}.pdf", "PDF Files (*.pdf)")
        if not path:
            return # Usuário cancelou

        try:
            # Configura o documento PDF para o tamanho de uma etiqueta A7
            doc = SimpleDocTemplate(path, pagesize=A7, leftMargin=5*mm, rightMargin=5*mm, topMargin=5*mm, bottomMargin=5*mm)
            styles = getSampleStyleSheet()
            style_center = styles['Normal']
            style_center.alignment = TA_CENTER

            elements = []
            elements.append(Paragraph(f"<b>{item_name}</b>", style_center))
            elements.append(Paragraph(f"<font size='8'>Cód: {item_code}</font>", style_center))
            elements.append(Spacer(1, 4*mm))

            # Converte a imagem PIL para o formato do ReportLab
            img_buffer = BytesIO()
            qr_pil_img.save(img_buffer, format='PNG')
            img_buffer.seek(0)

            qr_img = ReportLabImage(img_buffer, width=40*mm, height=40*mm)
            elements.append(qr_img)

            doc.build(elements)
            QMessageBox.information(self, "Sucesso", f"Etiqueta salva com sucesso em:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Gerar PDF", f"Ocorreu um erro: {e}")
            logging.error(f"Erro ao gerar PDF da etiqueta QR para {item_code}: {e}")


def abrir_tela_cadastro_item(janela_principal):
    dialog = CadastroItemWindow(janela_principal)
    dialog.exec()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    database_manager.create_tables()
    dialog = CadastroItemWindow()
    dialog.show()
    sys.exit(app.exec())
