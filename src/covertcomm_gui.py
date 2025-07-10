"""
Improved CovertComm GUI Module
Enhanced version with better audio support and file path management.
"""

import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTextEdit, QFileDialog, QComboBox, QLineEdit, QFrame, QScrollArea, QMessageBox, QGraphicsDropShadowEffect
)
from PySide6.QtGui import QPixmap, QImage, QFont, QIcon, QColor
from PySide6.QtCore import Qt
from qt_material import apply_stylesheet
from PIL import Image
import numpy as np
# Import core steganography classes
from .covertcomm_core import ImageSteganography, AudioSteganography

# Palette
SHARK = "#2A2F33"
NOMAD = "#BBB6A5"
MANTLE = "#8C9491"
MANATEE = "#8C8C9C"

class Snackbar(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: #323232; color: #fff; border-radius: 8px; padding: 12px 24px; font-size: 14px;")
        self.setAlignment(Qt.AlignCenter)
        self.setWindowFlags(Qt.ToolTip)
        self.hide()
    def show_message(self, message, duration=2500):
        self.setText(message)
        self.adjustSize()
        self.move(self.parent().width()//2 - self.width()//2, self.parent().height() - self.height() - 40)
        self.show()
        self.raise_()
        self.timer = self.startTimer(duration)
    def timerEvent(self, event):
        self.killTimer(self.timer)
        self.hide()


class CovertCommMainWindow(QMainWindow):
    """Main GUI class for the CovertComm application."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CovertComm - Steganography Toolkit")
        self.setMinimumSize(1100, 750)
        self.setStyleSheet(f"background: {NOMAD};")
        self.image_stego = ImageSteganography()
        self.audio_stego = AudioSteganography()
        self.selected_image_path = None
        self.selected_audio_path = None
        self.stego_image_path = None
        self.stego_audio_path = None
        self.status_label = None
        self.theme = 'light_blue.xml'
        self.snackbar = Snackbar(self)
        self.original_image_path = None
        self.stego_image_path = None
        self.init_ui()

    def init_ui(self):
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setMovable(False)
        self.tabs.setDocumentMode(True)
        self.tabs.setStyleSheet(f"""
            QTabBar::tab {{ height: 40px; width: 220px; font-size: 16px; color: {MANATEE}; background: {SHARK}; border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 2px; }}
            QTabBar::tab:selected {{ color: {NOMAD}; background: {SHARK}; border-bottom: 3px solid {MANTLE}; }}
            QTabWidget::pane {{ border: none; }}
        """)
        self.setCentralWidget(self.tabs)
        self.image_tab = QWidget()
        self.audio_tab = QWidget()
        dark_icon = QIcon.fromTheme('image-x-generic')
        audio_icon = QIcon.fromTheme('audio-x-generic')
        self.tabs.addTab(self.image_tab, dark_icon, "Image Steganography")
        self.tabs.addTab(self.audio_tab, audio_icon, "Audio Steganography")
        self.init_image_tab()
        self.init_audio_tab()
        self.init_status_bar()

    def show_snackbar(self, message, duration=2500):
        self.snackbar.show_message(message, duration)

    def card(self, widget):
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setStyleSheet(f"background: #fff; border-radius: 16px; border: 1px solid {MANTLE};")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18)
        shadow.setColor(QColor(0,0,0,30))
        shadow.setOffset(0, 4)
        frame.setGraphicsEffect(shadow)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.addWidget(widget)
        return frame

    def init_status_bar(self):
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"color: {SHARK}; font-size: 13px; padding: 8px; background: {NOMAD};")
        self.statusBar().addWidget(self.status_label)

    # --- IMAGE TAB ---
    def init_image_tab(self):
        layout = QHBoxLayout()
        left = QVBoxLayout()
        right = QVBoxLayout()
        # Instructions
        instr = QLabel("Hide a secret message in a PNG image using the LSB (Least Significant Bit) method. Select an image, enter your message, and click 'Hide Message'. To extract, select a stego image and click 'Extract Message'.")
        instr.setWordWrap(True)
        instr.setStyleSheet(f"color: {SHARK}; font-size: 13px; background: transparent; border: none;")
        left.addWidget(instr)
        # File selection
        file_row = QHBoxLayout()
        self.image_select_btn = QPushButton(QIcon.fromTheme('document-open'), " Select Image")
        self.image_select_btn.setIcon(QIcon.fromTheme('document-open', QIcon(':/icons/dark_folder.png')))
        self.image_select_btn.setStyleSheet(f"background: {SHARK}; color: {NOMAD}; font-weight: bold; border-radius: 6px; padding: 8px 18px;")
        self.image_select_btn.clicked.connect(self.select_image)
        self.image_path_label = QLabel("No image selected")
        self.image_path_label.setStyleSheet(f"color: {SHARK}; font-size: 12px;")
        file_row.addWidget(self.image_select_btn)
        file_row.addWidget(self.image_path_label)
        left.addLayout(file_row)
        # Message input
        msg_label = QLabel("Message")
        msg_label.setStyleSheet(f"font-weight: bold; color: {SHARK}; background: transparent; border: none; padding: 0;")
        self.image_message_text = QTextEdit()
        self.image_message_text.setFixedHeight(120)
        self.image_message_text.setStyleSheet(f"font-size: 13px; border-radius: 6px; background: #fff; color: {SHARK}; border: 1px solid {MANTLE};")
        left.addWidget(msg_label)
        left.addWidget(self.image_message_text)
        password_label = QLabel("Password (AES)")
        self.image_password_input = QLineEdit()
        self.image_password_input.setEchoMode(QLineEdit.Password)
        left.addWidget(password_label)
        left.addWidget(self.image_password_input)
        # Buttons
        btn_row = QHBoxLayout()
        self.hide_image_btn = QPushButton(QIcon.fromTheme('emblem-ok', QIcon(':/icons/dark_check.png')), " Hide Message")
        self.hide_image_btn.setStyleSheet(f"background: {SHARK}; color: {NOMAD}; font-weight: bold; border-radius: 6px; padding: 10px;")
        self.hide_image_btn.clicked.connect(self.hide_image_message)
        self.extract_image_btn = QPushButton(QIcon.fromTheme('edit-find', QIcon(':/icons/dark_search.png')), " Extract Message")
        self.extract_image_btn.setStyleSheet(f"background: #fff; color: {SHARK}; font-weight: bold; border: 2px solid {MANTLE}; border-radius: 6px; padding: 10px;")
        self.extract_image_btn.clicked.connect(self.extract_image_message)
        self.clear_image_btn = QPushButton(QIcon.fromTheme('edit-clear', QIcon(':/icons/dark_clear.png')), " Clear")
        self.clear_image_btn.setStyleSheet(f"background: #fff; color: {SHARK}; border: 1px solid {MANTLE}; border-radius: 6px; padding: 10px;")
        self.clear_image_btn.clicked.connect(self.clear_image_message)
        btn_row.addWidget(self.hide_image_btn)
        btn_row.addWidget(self.extract_image_btn)
        btn_row.addWidget(self.clear_image_btn)
        left.addLayout(btn_row)
        left.addStretch()
        # Capacity
        self.image_capacity_label = QLabel("")
        self.image_capacity_label.setStyleSheet(f"color: {MANATEE}; font-size: 12px; background: transparent; border: none; padding: 0;")
        left.addWidget(self.image_capacity_label)
        # Card for left panel
        left_card = self.card(QWidget())
        left_card.layout().addLayout(left)
        # Image preview
        preview_frame = QHBoxLayout()
        self.original_image_label = QLabel("Original Image")
        self.original_image_label.setAlignment(Qt.AlignCenter)
        self.original_image_label.setStyleSheet(f"background: #fff; border: 1px solid {MANTLE}; border-radius: 8px; color: {MANATEE};")
        self.stego_image_label = QLabel("Stego Image")
        self.stego_image_label.setAlignment(Qt.AlignCenter)
        self.stego_image_label.setStyleSheet(f"background: #fff; border: 1px solid {MANTLE}; border-radius: 8px; color: {MANATEE};")
        preview_frame.addWidget(self.original_image_label)
        preview_frame.addWidget(self.stego_image_label)
        preview_card = self.card(QWidget())
        preview_card.layout().addLayout(preview_frame)
        right.addWidget(preview_card)
        right.addStretch()
        layout.addWidget(left_card, 2)
        layout.addLayout(right, 3)
        self.image_tab.setLayout(layout)

    # --- AUDIO TAB ---
    def init_audio_tab(self):
        layout = QHBoxLayout()
        left = QVBoxLayout()
        right = QVBoxLayout()
        # Instructions
        instr = QLabel("Hide a secret message in a 16-bit mono WAV audio file using LSB. Select an audio file, enter your message, and click 'Hide Message'. To extract, select a stego audio file and click 'Extract Message'. Only 16-bit mono WAV files are supported.")
        instr.setWordWrap(True)
        instr.setStyleSheet(f"color: {SHARK}; font-size: 13px; background: transparent; border: none;")
        left.addWidget(instr)
        # File selection
        file_row = QHBoxLayout()
        self.audio_select_btn = QPushButton(QIcon.fromTheme('document-open', QIcon(':/icons/dark_folder.png')), " Select Audio")
        self.audio_select_btn.setStyleSheet(f"background: {SHARK}; color: {NOMAD}; font-weight: bold; border-radius: 6px; padding: 8px 18px;")
        self.audio_select_btn.clicked.connect(self.select_audio)
        self.audio_path_label = QLabel("No audio selected")
        self.audio_path_label.setStyleSheet(f"color: {SHARK}; font-size: 12px;")
        file_row.addWidget(self.audio_select_btn)
        file_row.addWidget(self.audio_path_label)
        left.addLayout(file_row)
        # Message input
        msg_label = QLabel("Message")
        msg_label.setStyleSheet(f"font-weight: bold; color: {SHARK}; background: transparent; border: none; padding: 0;")
        self.audio_message_text = QTextEdit()
        self.audio_message_text.setFixedHeight(120)
        self.audio_message_text.setStyleSheet(f"font-size: 13px; border-radius: 6px; background: #fff; color: {SHARK}; border: 1px solid {MANTLE};")
        left.addWidget(msg_label)
        left.addWidget(self.audio_message_text)
        password_label = QLabel("Password (AES)")
        self.audio_password_input = QLineEdit()
        self.audio_password_input.setEchoMode(QLineEdit.Password)
        left.addWidget(password_label)
        left.addWidget(self.audio_password_input)
        # Buttons
        btn_row = QHBoxLayout()
        self.hide_audio_btn = QPushButton(QIcon.fromTheme('emblem-ok', QIcon(':/icons/dark_check.png')), " Hide Message")
        self.hide_audio_btn.setStyleSheet(f"background: {SHARK}; color: {NOMAD}; font-weight: bold; border-radius: 6px; padding: 10px;")
        self.hide_audio_btn.clicked.connect(self.hide_audio_message)
        self.extract_audio_btn = QPushButton(QIcon.fromTheme('edit-find', QIcon(':/icons/dark_search.png')), " Extract Message")
        self.extract_audio_btn.setStyleSheet(f"background: #fff; color: {SHARK}; font-weight: bold; border: 2px solid {MANTLE}; border-radius: 6px; padding: 10px;")
        self.extract_audio_btn.clicked.connect(self.extract_audio_message)
        self.clear_audio_btn = QPushButton(QIcon.fromTheme('edit-clear', QIcon(':/icons/dark_clear.png')), " Clear")
        self.clear_audio_btn.setStyleSheet(f"background: #fff; color: {SHARK}; border: 1px solid {MANTLE}; border-radius: 6px; padding: 10px;")
        self.clear_audio_btn.clicked.connect(self.clear_audio_message)
        btn_row.addWidget(self.hide_audio_btn)
        btn_row.addWidget(self.extract_audio_btn)
        btn_row.addWidget(self.clear_audio_btn)
        left.addLayout(btn_row)
        left.addStretch()
        # Capacity
        self.audio_capacity_label = QLabel("")
        self.audio_capacity_label.setStyleSheet(f"color: {MANATEE}; font-size: 12px; background: transparent; border: none; padding: 0;")
        left.addWidget(self.audio_capacity_label)
        # Card for left panel
        left_card = self.card(QWidget())
        left_card.layout().addLayout(left)
        # Audio info
        self.audio_info_label = QLabel("No audio loaded")
        self.audio_info_label.setStyleSheet(f"color: {SHARK}; font-size: 12px; background: #fff; border-radius: 6px; padding: 8px; border: 1px solid {MANTLE};")
        self.stego_audio_info_label = QLabel("No stego audio created")
        self.stego_audio_info_label.setStyleSheet(f"color: {SHARK}; font-size: 12px; background: #fff; border-radius: 6px; padding: 8px; border: 1px solid {MANTLE};")
        info_col = QVBoxLayout()
        info_col.addWidget(self.audio_info_label)
        info_col.addWidget(self.stego_audio_info_label)
        info_col.addStretch()
        info_card = self.card(QWidget())
        info_card.layout().addLayout(info_col)
        right.addWidget(info_card)
        right.addStretch()
        layout.addWidget(left_card, 2)
        layout.addLayout(right, 3)
        self.audio_tab.setLayout(layout)

    # --- IMAGE TAB LOGIC ---
    def select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "PNG Images (*.png);;All Files (*)")
        if file_path:
            self.selected_image_path = file_path
            self.original_image_path = file_path
            self.image_path_label.setText(os.path.basename(file_path))
            self.load_image_preview(file_path)
            self.update_image_capacity()
            self.status_label.setText(f"Selected image: {os.path.basename(file_path)}")
            self.stego_image_label.clear()
            self.image_message_text.clear()
        else:
            self.status_label.setText("Image selection cancelled.")

    def load_image_preview(self, image_path):
        try:
            img = Image.open(image_path)
            img.thumbnail((400, 400), Image.Resampling.LANCZOS)
            data = img.convert("RGBA").tobytes("raw", "RGBA")
            qimg = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimg)
            self.original_image_label.setPixmap(pixmap)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load image: {str(e)}")
            self.status_label.setText("Failed to load image.")

    def hide_image_message(self):
        if not self.selected_image_path:
            self.show_snackbar("Please select an image first", 3000)
            return
        message = self.image_message_text.toPlainText().strip()
        if not message:
            self.show_snackbar("Please enter a message to hide", 3000)
            return
        password = self.image_password_input.text().strip()
        if not password:
            self.show_snackbar("Please enter a password for encryption", 3000)
            return
        from .covertcomm_core import aes_encrypt
        encrypted_message = aes_encrypt(message, password)
        try:
            capacity = self.image_stego.calculate_capacity(self.selected_image_path, method='lsb')
            if len(encrypted_message) > capacity:
                self.show_snackbar(f"Encrypted message too long! Maximum capacity: {capacity} characters", 3500)
                return
        except Exception as e:
            self.show_snackbar(f"Error checking capacity: {str(e)}", 3500)
            return
        base = os.path.basename(self.selected_image_path)
        name, ext = os.path.splitext(base)
        output_path = os.path.join('samples', 'stego_images', f'stego_{name}.png')
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        except Exception as e:
            self.show_snackbar(f"Could not create output folder: {str(e)}", 3500)
            return
        try:
            success = self.image_stego.hide_message_in_image(self.selected_image_path, encrypted_message, output_path, method='lsb', password=password)
            if success:
                self.show_snackbar("Message hidden successfully!", 2500)
                self.load_stego_image_preview(output_path)
            else:
                self.show_snackbar("Failed to hide message.", 3000)
        except Exception as e:
            self.show_snackbar(str(e), 3500)

    def load_stego_image_preview(self, image_path):
        try:
            img = Image.open(image_path)
            img.thumbnail((400, 400), Image.Resampling.LANCZOS)
            data = img.convert("RGBA").tobytes("raw", "RGBA")
            qimg = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimg)
            self.stego_image_label.setPixmap(pixmap)
            self.stego_image_path = image_path
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load stego image: {str(e)}")

    def extract_image_message(self):
        if not self.selected_image_path:
            self.show_snackbar("Please select an image first", 3000)
            return
        password = self.image_password_input.text().strip()
        if not password:
            self.show_snackbar("Please enter the password to decrypt", 3000)
            return
        from .covertcomm_core import aes_decrypt
        try:
            message = self.image_stego.extract_message_from_image(self.selected_image_path, method='lsb', password=password)
            if message:
                decrypted_message = aes_decrypt(message, password)
                self.image_message_text.setPlainText(decrypted_message)
                self.show_snackbar("Message extracted and decrypted successfully!", 2500)
            else:
                self.show_snackbar("No hidden message found in the image", 3000)
        except Exception as e:
            self.show_snackbar(str(e), 3500)

    def clear_image_message(self):
        self.image_message_text.clear()
        self.show_snackbar("Image message cleared.", 2000)

    def update_image_capacity(self):
        try:
            capacity = self.image_stego.calculate_capacity(self.selected_image_path, method='lsb')
            self.image_capacity_label.setText(f"Image (LSB) capacity: {capacity} characters")
        except Exception as e:
            self.image_capacity_label.setText(f"Error calculating capacity: {str(e)}")

    # --- AUDIO TAB LOGIC ---
    def select_audio(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Audio", "", "WAV Files (*.wav);;All Files (*)")
        if file_path:
            self.selected_audio_path = file_path
            self.audio_path_label.setText(os.path.basename(file_path))
            self.load_audio_info(file_path)
            self.update_audio_capacity()
            self.status_label.setText(f"Selected audio: {os.path.basename(file_path)}")
            self.audio_message_text.clear()
            self.stego_audio_info_label.setText("No stego audio")
        else:
            self.status_label.setText("Audio selection cancelled.")

    def load_audio_info(self, audio_path):
        try:
            import wave
            with wave.open(audio_path, 'rb') as wav_file:
                frames = wav_file.getnframes()
                sample_rate = wav_file.getframerate()
                duration = frames / sample_rate
                channels = wav_file.getnchannels()
                sampwidth = wav_file.getsampwidth()
                info = f"Duration: {duration:.2f}s\nSample Rate: {sample_rate} Hz\nChannels: {channels}\nFrames: {frames}\nSample Width: {sampwidth * 8} bits"
                if channels != 1 or sampwidth != 2:
                    info += "\n\nWarning: Only 16-bit mono WAV files are supported."
                self.audio_info_label.setText(info)
        except Exception as e:
            self.audio_info_label.setText(f"Error loading audio info: {str(e)}")

    def hide_audio_message(self):
        if not self.selected_audio_path:
            self.show_snackbar("Please select an audio file first", 3000)
            return
        message = self.audio_message_text.toPlainText().strip()
        if not message:
            self.show_snackbar("Please enter a message to hide", 3000)
            return
        password = self.audio_password_input.text().strip()
        if not password:
            self.show_snackbar("Please enter a password for encryption", 3000)
            return
        from .covertcomm_core import aes_encrypt
        encrypted_message = aes_encrypt(message, password)
        try:
            capacity = self.audio_stego.calculate_capacity(self.selected_audio_path, method='lsb')
            if len(encrypted_message) > capacity:
                self.show_snackbar(f"Encrypted message too long! Maximum capacity: {capacity} characters", 3500)
                return
        except Exception as e:
            self.show_snackbar(f"Error checking capacity: {str(e)}", 3500)
            return
        base = os.path.basename(self.selected_audio_path)
        name, ext = os.path.splitext(base)
        output_path = os.path.join('samples', 'stego_audio', f'stego_{name}.wav')
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        except Exception as e:
            self.show_snackbar(f"Could not create output folder: {str(e)}", 3500)
            return
        try:
            success = self.audio_stego.hide_message_in_audio(self.selected_audio_path, encrypted_message, output_path, method='lsb', password=password)
            if success:
                self.show_snackbar("Message hidden successfully!", 2500)
                self.stego_audio_info_label.setText(f"Stego audio created: {os.path.basename(output_path)}")
            else:
                self.show_snackbar("Failed to hide message.", 3000)
        except Exception as e:
            self.show_snackbar(str(e), 3500)

    def extract_audio_message(self):
        if not self.selected_audio_path:
            self.show_snackbar("Please select an audio file first", 3000)
            return
        password = self.audio_password_input.text().strip()
        if not password:
            self.show_snackbar("Please enter the password to decrypt", 3000)
            return
        from .covertcomm_core import aes_decrypt
        try:
            message = self.audio_stego.extract_message_from_audio(self.selected_audio_path, method='lsb', password=password)
            if message:
                decrypted_message = aes_decrypt(message, password)
                self.audio_message_text.setPlainText(decrypted_message)
                self.show_snackbar("Message extracted and decrypted successfully!", 2500)
            else:
                self.show_snackbar("No hidden message found in the audio", 3000)
        except Exception as e:
            self.show_snackbar(str(e), 3500)

    def clear_audio_message(self):
        self.audio_message_text.clear()
        self.show_snackbar("Audio message cleared.", 2000)

    def update_audio_capacity(self):
        try:
            method = 'lsb' # Only LSB is supported
            capacity = self.audio_stego.calculate_capacity(self.selected_audio_path, method=method)
            self.audio_capacity_label.setText(f"Audio (LSB) capacity: {capacity} characters")
        except Exception as e:
            self.audio_capacity_label.setText(f"Error calculating capacity: {str(e)}")


def main():
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='light_blue.xml')
    window = CovertCommMainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()