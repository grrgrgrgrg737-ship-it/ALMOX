import sys
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFileDialog, QFrame, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon, QColor, QBrush, QPainter, QFont
from PyQt6.QtCharts import QChart, QChartView, QPieSeries, QPieSlice
import database_manager
import logging
import os

class RelatorioABCWindow(QDialog):
    """
    Janela para exibir a Análise ABC de consumo de itens por valor, com visual e interatividade aprimorados.
    """
    def __init__(self, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.main_window = parent
        self.setWindowTitle("Análise de Curva ABC por Valor de Consumo")
        self.setGeometry(100, 100, 1200, 750)
        self.setup_ui()
        self.generate_report()

    def setup_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(15)
        
        left_column = QVBoxLayout()
        
        filter_frame = QFrame(objectName="formFrame")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.addWidget(QLabel("Período de Análise:"))
        self.start_date_input = QDateEdit(calendarPopup=True, date=QDate.currentDate().addMonths(-6))
        self.end_date_input = QDateEdit(calendarPopup=True, date=QDate.currentDate())
        self.btn_generate = QPushButton("Gerar Análise", clicked=self.generate_report)
        self.btn_generate.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "report_generate.png")))
        filter_layout.addWidget(self.start_date_input)
        filter_layout.addWidget(QLabel("a"))
        filter_layout.addWidget(self.end_date_input)
        filter_layout.addWidget(self.btn_generate)
        filter_layout.addStretch()
        left_column.addWidget(filter_frame)

        self.table_report = QTableWidget()
        self.table_report.setColumnCount(5)
        self.table_report.setHorizontalHeaderLabels(["Classe", "Item", "Valor Consumido (R$)", "% do Total", "% Acumulada"])
        self.table_report.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_report.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_report.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        left_column.addWidget(self.table_report)
        
        right_column_frame = QFrame(objectName="formFrame")
        right_column = QVBoxLayout(right_column_frame)
        right_column.addWidget(QLabel("Distribuição de Valor por Classe", objectName="sectionHeaderLabel"))
        
        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.chart_view.setMinimumSize(400, 400)
        right_column.addWidget(self.chart_view)

        self.chart_tooltip_label = QLabel("Passe o mouse sobre o gráfico para ver os detalhes.")
        self.chart_tooltip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chart_tooltip_label.setStyleSheet("font-style: italic; color: #BDC3C7; margin-top: 10px;")
        right_column.addWidget(self.chart_tooltip_label)
        
        main_layout.addLayout(left_column, 2)
        main_layout.addWidget(right_column_frame, 1)

    def generate_report(self):
        start_date = self.start_date_input.date().toString("yyyy-MM-dd")
        end_date = self.end_date_input.date().toString("yyyy-MM-dd")
        
        consumo_valorado = database_manager.get_analise_consumo_valorado(start_date, end_date)
        
        self.table_report.setRowCount(0)
        self.chart_view.setChart(QChart())
        self.chart_tooltip_label.setText("Passe o mouse sobre o gráfico para ver os detalhes.")

        if not consumo_valorado:
            QMessageBox.information(self, "Análise ABC", "Nenhum consumo registrado no período selecionado.")
            return

        total_valor_consumo = sum(item['valor_consumo'] for item in consumo_valorado)
        if total_valor_consumo == 0:
             QMessageBox.information(self, "Análise ABC", "O valor total de consumo no período é zero.")
             return
        
        consumo_ordenado = sorted(consumo_valorado, key=lambda x: x['valor_consumo'], reverse=True)
        
        self.table_report.setRowCount(len(consumo_ordenado))
        percent_acumulado = 0
        valores_por_classe = {'A': 0, 'B': 0, 'C': 0}

        for row, item in enumerate(consumo_ordenado):
            percent_item = (item['valor_consumo'] / total_valor_consumo) * 100
            percent_acumulado += percent_item
            
            if percent_acumulado <= 80: classe = 'A'; cor = QColor("#C0392B")
            elif percent_acumulado <= 95: classe = 'B'; cor = QColor("#D35400")
            else: classe = 'C'; cor = QColor("#2980B9")

            valores_por_classe[classe] += item['valor_consumo']

            class_item = QTableWidgetItem(classe)
            class_item.setBackground(QBrush(cor)); class_item.setForeground(QBrush(Qt.GlobalColor.white)); class_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            self.table_report.setItem(row, 0, class_item)
            self.table_report.setItem(row, 1, QTableWidgetItem(f"{item['codigo']} - {item['nome']}"))
            self.table_report.setItem(row, 2, QTableWidgetItem(f"{item['valor_consumo']:.2f}"))
            self.table_report.setItem(row, 3, QTableWidgetItem(f"{percent_item:.2f}%"))
            self.table_report.setItem(row, 4, QTableWidgetItem(f"{percent_acumulado:.2f}%"))
        
        self.update_pie_chart(valores_por_classe, total_valor_consumo)

    def update_pie_chart(self, valores_por_classe, total_valor):
        series = QPieSeries()
        
        slice_a = QPieSlice("Classe A", valores_por_classe['A']); slice_a.setBrush(QColor("#C0392B"))
        slice_b = QPieSlice("Classe B", valores_por_classe['B']); slice_b.setBrush(QColor("#D35400"))
        slice_c = QPieSlice("Classe C", valores_por_classe['C']); slice_c.setBrush(QColor("#2980B9"))
        
        series.append([slice_a, slice_b, slice_c])

        # --- CORREÇÃO: Lógica para remover e configurar as fatias ---
        
        # 1. Identificar as fatias a serem removidas sem modificar a lista durante a iteração
        slices_to_remove = []
        for s in series.slices():
            if s.value() == 0:
                slices_to_remove.append(s)

        # 2. Remover as fatias identificadas
        for s in slices_to_remove:
            series.remove(s)
            
        # 3. Agora, configurar apenas as fatias que restaram
        for s in series.slices():
            s.setLabelVisible(True)
            s.setLabel(f"<b>{s.percentage()*100:.1f}%</b>")
            s.setLabelFont(QFont("Segoe UI", 8))
            s.setLabelColor(Qt.GlobalColor.white)
        # --- FIM DA CORREÇÃO ---
        
        series.hovered.connect(self.handle_pie_slice_hover)

        chart = QChart()
        chart.addSeries(series)
        chart.setTheme(QChart.ChartTheme.ChartThemeDark)
        chart.setTitle("Distribuição de Valor ABC")
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        chart.legend().setColor(QColor("#ECF0F1"))
        
        self.chart_view.setChart(chart)

    def handle_pie_slice_hover(self, slice: QPieSlice, state: bool):
        """
        Esta função é chamada quando o mouse entra ou sai de uma fatia do gráfico.
        """
        slice.setExploded(state)

        if state:
            label_text = slice.label() # O nome da fatia (ex: "Classe A")
            value = slice.value()
            percent = slice.percentage() * 100
            self.chart_tooltip_label.setText(f"<b>{label_text}</b>: R$ {value:.2f} ({percent:.1f}%)")
        else:
            self.chart_tooltip_label.setText("Passe o mouse sobre o gráfico para ver os detalhes.")


def abrir_tela_relatorio_abc(janela_principal):
    dialog = RelatorioABCWindow(janela_principal)
    dialog.exec()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Adicionar dados de teste se necessário
    dialog = RelatorioABCWindow()
    dialog.show()
    sys.exit(app.exec())