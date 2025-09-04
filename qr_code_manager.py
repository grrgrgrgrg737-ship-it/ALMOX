import qrcode
from io import BytesIO
from PIL import Image
import logging
from typing import Optional

# Configuração do logging
logging.basicConfig(
    filename='almoxarifado.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

class QRCodeGenerator:
    """
    Classe utilitária para gerar QR Codes em diferentes formatos.
    """
    @staticmethod
    def generate_qr_code_pil_image(
        data_string: str, box_size: int = 10, border: int = 4
    ) -> Optional[Image.Image]:
        """
        Gera um QR Code como uma imagem PIL (Pillow), ideal para usar com ReportLab.
        Args:
            data_string: Dados a serem codificados no QR Code (ex: código do item).
            box_size: Tamanho dos blocos do QR code.
            border: Largura da borda.
        Returns:
            Imagem PIL do QR Code, ou None em caso de erro.
        """
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=box_size,
                border=border,
            )
            qr.add_data(data_string)
            qr.make(fit=True)
            
            # Cria a imagem PIL
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Garante que a imagem esteja no modo RGB, se necessário
            if not isinstance(img, Image.Image):
                img = img.convert("RGB")
            
            return img
        except Exception as e:
            logging.error(f"Erro ao gerar QR Code como PIL Image: {e}")
            return None