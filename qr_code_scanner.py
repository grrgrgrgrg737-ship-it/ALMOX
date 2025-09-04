import sys
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QImage, QPixmap
import os
import cv2
import logging

class QRScannerThread(QThread):
    """
    Thread em segundo plano para capturar vídeo e detectar QR Codes sem congelar a GUI.
    """
    frame_captured = pyqtSignal(QImage)
    qr_scanned = pyqtSignal(str)
    camera_error = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self.detector = cv2.QRCodeDetector()

    def run(self):
        self._running = True
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            self.camera_error.emit("Não foi possível acessar a câmera. Verifique se está conectada e não está em uso por outro programa.")
            return

        while self._running:
            ret, frame = cap.read()
            if not ret:
                logging.warning("Não foi possível ler o frame da câmera.")
                continue

            # Converte o frame do OpenCV (BGR) para QImage (RGB)
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            self.frame_captured.emit(qt_image)

            # Tenta decodificar o QR code
            decoded_info, _, _ = self.detector.detectAndDecode(frame)
            if decoded_info:
                self.qr_scanned.emit(decoded_info)
                self._running = False # Para a thread após encontrar um código

        cap.release()

    def stop(self):
        self._running = False


class QRScannerDialog(QDialog):
    """
    Janela de diálogo que exibe o feed da câmera e gerencia a thread do scanner.
    """
    qr_code_result = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Escanear QR Code do Item")
        self.setFixedSize(640, 520)
        self.setModal(True)

        # Configura a interface
        main_layout = QVBoxLayout(self)
        self.camera_feed_label = QLabel("Iniciando câmera...")
        self.camera_feed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_feed_label.setStyleSheet("background-color: black; border: 1px solid #444;")
        main_layout.addWidget(self.camera_feed_label)
        
        self.status_label = QLabel("Aponte a câmera para o QR Code")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        cancel_button = QPushButton("Cancelar")
        cancel_button.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "cancel.png")))
        cancel_button.clicked.connect(self.reject)
        main_layout.addWidget(cancel_button, alignment=Qt.AlignmentFlag.AlignRight)

        # Configura a thread do scanner
        self.scanner_thread = QRScannerThread(self)
        self.scanner_thread.frame_captured.connect(self.update_camera_feed)
        self.scanner_thread.qr_scanned.connect(self.handle_scanned_data)
        self.scanner_thread.camera_error.connect(self.show_camera_error)
        
        self.scanner_thread.start()

    def update_camera_feed(self, image: QImage):
        """Atualiza a QLabel com a imagem vinda da câmera."""
        pixmap = QPixmap.fromImage(image)
        self.camera_feed_label.setPixmap(pixmap.scaled(self.camera_feed_label.size(),
                                                       Qt.AspectRatioMode.KeepAspectRatio,
                                                       Qt.TransformationMode.SmoothTransformation))

    def handle_scanned_data(self, data: str):
        """Recebe o dado do QR Code, emite um sinal e fecha a janela."""
        logging.info(f"QR Code detectado: {data}")
        self.status_label.setText(f"Código encontrado: {data}")
        self.qr_code_result.emit(data)
        self.accept() # Fecha a janela com sucesso

    def show_camera_error(self, message: str):
        """Mostra uma mensagem de erro se a câmera falhar."""
        QMessageBox.critical(self, "Erro de Câmera", message)
        self.reject() # Fecha a janela com erro

    def closeEvent(self, event):
        """Garante que a thread da câmera seja parada ao fechar a janela."""
        self.scanner_thread.stop()
        self.scanner_thread.wait()
        super().closeEvent(event)