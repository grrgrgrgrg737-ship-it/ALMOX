import sys
import os
from typing import Optional, Callable
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QMessageBox, QFrame, QSizePolicy, QStatusBar, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtGui import QIcon, QCloseEvent
from PyQt6.QtCore import Qt, QSize, QTimer

import database_manager
import logging

# Importa TODAS as telas secundárias, incluindo as novas de análise
import tela_estoque_geral
import tela_entrada_estoque
import tela_saida_estoque
import tela_relatorio_movimentacao
import tela_relatorio_consumo
import tela_cadastro_item
import tela_cadastro_deposito
import tela_cadastro_fornecedor
import tela_cadastro_tecnico
import tela_auditoria
import tela_cadastro_ferramenta
import tela_emprestimo_ferramenta
import tela_relatorio_abc
import tela_ponto_ressuprimento
import tela_ajuste_estoque

logging.basicConfig(filename='almoxarifado.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Almoxarifado - Dashboard")
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "app_icon.png")))
        self.showFullScreen()
        self.setup_ui()
        self.apply_stylesheet()
        
        # Timer para atualizar o dashboard periodicamente
        self.dashboard_timer = QTimer(self)
        self.dashboard_timer.timeout.connect(self.refresh_dashboard)
        self.dashboard_timer.start(30000) # Atualiza a cada 30 segundos
        self.refresh_dashboard() # Carga inicial

    def setup_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # --- Coluna da Esquerda (Dashboard) ---
        dashboard_column = QVBoxLayout()
        dashboard_column.setSpacing(15)
        
        # Painel de Alertas
        alertas_frame = QFrame(objectName="formFrame")
        alertas_layout = QVBoxLayout(alertas_frame)
        alertas_layout.addWidget(QLabel("Alertas Rápidos", objectName="sectionHeaderLabel"))
        self.lbl_estoque_baixo = QLabel("Itens com estoque baixo: <b>-</b>")
        self.lbl_emprestimos_atrasados = QLabel("Empréstimos atrasados: <b>-</b>")
        alertas_layout.addWidget(self.lbl_estoque_baixo)
        alertas_layout.addWidget(self.lbl_emprestimos_atrasados)
        dashboard_column.addWidget(alertas_frame)

        # Painel de Atividade Recente
        atividade_frame = QFrame(objectName="formFrame")
        atividade_layout = QVBoxLayout(atividade_frame)
        atividade_layout.addWidget(QLabel("Atividade Recente", objectName="sectionHeaderLabel"))
        self.tbl_atividade_recente = QTableWidget()
        self.tbl_atividade_recente.setColumnCount(3)
        self.tbl_atividade_recente.setHorizontalHeaderLabels(["Item", "Tipo", "Qtd."])
        self.tbl_atividade_recente.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_atividade_recente.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        atividade_layout.addWidget(self.tbl_atividade_recente)
        dashboard_column.addWidget(atividade_frame)
        dashboard_column.addStretch(1)

        # --- Coluna da Direita (Menu de Botões) ---
        menu_column = QVBoxLayout()
        
        menu_grid = QGridLayout()
        menu_grid.setSpacing(15)

        # Agrupando botões por função em frames
        self._add_menu_section(menu_grid, 0, "Operações de Estoque", [
            ("Estoque Geral", tela_estoque_geral.abrir_tela_estoque_geral, "stock_general.png"),
            ("Registrar Entrada", tela_entrada_estoque.abrir_tela_entrada_estoque, "stock_in.png"),
            ("Registrar Saída", tela_saida_estoque.abrir_tela_saida_estoque, "stock_out.png"),
            ("Ajuste de Inventário", tela_ajuste_estoque.abrir_tela_ajuste_estoque, "inventory.png")
        ])
        self._add_menu_section(menu_grid, 1, "Gestão de Ferramentas", [
            ("Empréstimos", tela_emprestimo_ferramenta.abrir_tela_emprestimo_ferramenta, "tool_loan.png"),
        ])
        self._add_menu_section(menu_grid, 2, "Relatórios e Análises", [
            ("Curva ABC", tela_relatorio_abc.abrir_tela_relatorio_abc, "report_abc.png"),
            ("Ponto de Ressuprimento", tela_ponto_ressuprimento.abrir_tela_ponto_ressuprimento, "report_low_stock.png"),
            ("Histórico de Movimentações", tela_relatorio_movimentacao.abrir_tela_relatorio_movimentacao, "report_movement.png"),
            ("Logs de Auditoria", tela_auditoria.abrir_tela_auditoria, "audit_log.png"),
        ])
        self._add_menu_section(menu_grid, 3, "Cadastros", [
            ("Itens", tela_cadastro_item.abrir_tela_cadastro_item, "item_register.png"),
            ("Ferramentas", tela_cadastro_ferramenta.abrir_tela_cadastro_ferramenta, "tool_register.png"),
            ("Depósitos", tela_cadastro_deposito.abrir_tela_cadastro_deposito, "deposit_register.png"),
            ("Fornecedores", tela_cadastro_fornecedor.abrir_tela_cadastro_fornecedor, "supplier_register.png"),
            ("Técnicos", tela_cadastro_tecnico.abrir_tela_cadastro_tecnico, "technician_register.png"),
        ])
        
        menu_column.addLayout(menu_grid)
        menu_column.addStretch(1)
        
        exit_button = self._create_button("Sair", self.close, "exit.png", "Ctrl+Q", is_danger=True)
        menu_column.addWidget(exit_button, alignment=Qt.AlignmentFlag.AlignRight)

        main_layout.addLayout(dashboard_column, 1)
        main_layout.addLayout(menu_column, 2)

        self.setStatusBar(QStatusBar())

    def _add_menu_section(self, grid_layout, row, title, buttons_data):
        frame = QFrame(objectName="formFrame")
        layout = QVBoxLayout(frame)
        layout.addWidget(QLabel(title, objectName="sectionHeaderLabel"))
        
        button_grid = QGridLayout()
        for idx, (text, handler, icon) in enumerate(buttons_data):
            button_grid.addWidget(self._create_button(text, handler, icon), idx // 2, idx % 2)
        layout.addLayout(button_grid)
        
        grid_layout.addWidget(frame, row, 0)

    def _create_button(self, text, handler, icon_name=None, shortcut=None, is_danger=False):
        button = QPushButton(text)
        # O handler é a função 'abrir_tela_...' que espera 'janela_principal' como argumento
        button.clicked.connect(lambda: handler(self))
        if icon_name:
            icon_path = os.path.join(os.path.dirname(__file__), "icons", icon_name)
            if os.path.exists(icon_path):
                button.setIcon(QIcon(icon_path))
                button.setIconSize(QSize(24, 24))
            else:
                logging.warning(f"Ícone não encontrado: {icon_path}")
        if shortcut:
            button.setShortcut(shortcut)
        if is_danger:
            button.setObjectName("dangerButton")
        button.setMinimumHeight(40)
        return button

    def refresh_dashboard(self):
        """Atualiza os dados exibidos no dashboard."""
        try:
            # Atualiza alertas de estoque baixo
            itens_baixo = database_manager.get_itens_abaixo_do_minimo()
            self.lbl_estoque_baixo.setText(f"Itens com estoque baixo: <b style='color: #E74C3C;'>{len(itens_baixo)}</b>")

            # Atualiza alertas de empréstimos atrasados
            atrasados = database_manager.get_emprestimos_atrasados()
            self.lbl_emprestimos_atrasados.setText(f"Empréstimos atrasados: <b style='color: #F39C12;'>{len(atrasados)}</b>")

            # Atualiza tabela de atividade recente
            recentes = database_manager.get_movimentacoes_recentes(limit=5)
            self.tbl_atividade_recente.setRowCount(len(recentes))
            for row, mov in enumerate(recentes):
                tipo = mov['tipo_movimentacao'].replace('_', ' ').capitalize()
                qtd = mov['quantidade']
                
                if 'entrada' in tipo.lower():
                    tipo_item = QTableWidgetItem(f"⬆ {tipo}")
                    tipo_item.setForeground(Qt.GlobalColor.green)
                elif 'saida' in tipo.lower():
                    tipo_item = QTableWidgetItem(f"⬇ {tipo}")
                    tipo_item.setForeground(Qt.GlobalColor.red)
                else: # Ajuste
                    tipo_item = QTableWidgetItem(f"⚙️ {tipo}")
                    tipo_item.setForeground(Qt.GlobalColor.yellow)

                self.tbl_atividade_recente.setItem(row, 0, QTableWidgetItem(mov['item_nome']))
                self.tbl_atividade_recente.setItem(row, 1, tipo_item)
                self.tbl_atividade_recente.setItem(row, 2, QTableWidgetItem(str(qtd)))
            
            self.show_status_message("Dashboard atualizado.", 2000)
        except Exception as e:
            logging.error(f"Falha ao atualizar dashboard: {e}")
            self.show_status_message(f"Erro ao carregar dados do dashboard.", 5000)

    def apply_stylesheet(self):
        qss_path = os.path.join(os.path.dirname(__file__), "style.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as file:
                self.setStyleSheet(file.read())
        else:
            logging.warning(f"Arquivo de estilo não encontrado: {qss_path}")

    def show_status_message(self, message: str, timeout: int = 3000):
        self.statusBar().showMessage(message, timeout)

    def closeEvent(self, event: QCloseEvent):
        reply = QMessageBox.question(self, 'Sair', 'Tem certeza que deseja sair?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    try:
        # Garante que as tabelas existam antes de rodar a aplicação
        database_manager.create_tables()
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logging.critical(f"Erro fatal ao iniciar a aplicação: {e}")
        QMessageBox.critical(None, "Erro Crítico", f"Não foi possível iniciar a aplicação.\nVerifique o log para detalhes:\n{e}")
        sys.exit(1)