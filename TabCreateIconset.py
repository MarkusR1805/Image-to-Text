import sys
import os
from pathlib import Path
from PIL import Image as PILImage

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QFrame, QMessageBox, QLineEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QDragEnterEvent, QDropEvent, QDragLeaveEvent, QPixmap,
    QImage, QFont
)


def create_iconset(input_image_path, output_dir, iconset_name):
    sizes = [16, 32, 64, 128, 256, 512]
    iconset_dir = Path(output_dir) / iconset_name
    iconset_dir.mkdir(parents=True, exist_ok=True)

    img = PILImage.open(input_image_path)

    for size in sizes:
        for scale in [1, 2]:
            scaled_size = size * scale
            resized_img = img.resize((scaled_size, scaled_size), PILImage.LANCZOS)

            suffix = f"@{scale}x" if scale > 1 else ""
            filename = f"icon_{size}x{size}{suffix}.png"
            path = iconset_dir / filename
            resized_img.save(path, 'PNG')

    # Erstelle die .icns-Datei mit iconutil
    iconset_path_str = str(iconset_dir.resolve())
    os.system(f'iconutil -c icns "{iconset_path_str}"')


class PreviewLabel(QLabel):
    """Custom QLabel to display image preview with centering and scaling"""
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: #2d2d2d; border-radius: 8px; color: #aaa;")
        self.setText("Bild hierher ziehen & ablegen")
        self.setFont(QFont("Helvetica", 12))
        self.setFixedSize(400, 200)
        self.setAcceptDrops(True)  # <- Hinzugefügt

    def setPixmap(self, pixmap):
        # Scale pixmap to fit while keeping aspect ratio
        scaled = pixmap.scaled(
            self.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        super().setPixmap(scaled)
        self.setText("")  # Clear text when image is shown

    def clear(self):
        self.setPixmap(QPixmap())  # Clear image
        self.setText("Bild hierher ziehen & ablegen")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1:
                file_path = urls[0].toLocalFile()
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
                    self.setStyleSheet("background-color: #254050; border-radius: 8px; color: #80ccff;")  # Visuelles Feedback
                    event.acceptProposedAction()

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        self.setStyleSheet("background-color: #2d2d2d; border-radius: 8px; color: #aaa;")  # Zurücksetzen

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet("background-color: #2d2d2d; border-radius: 8px; color: #aaa;")  # Zurücksetzen
        urls = event.mimeData().urls()
        if urls and len(urls) == 1:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
                # Wir müssen das Haupt-Widget benachrichtigen, dass ein Bild gesetzt werden soll
                parent = self.parent().parent()  # QLabel -> QVBoxLayout -> QFrame -> TabCreateIconset
                if isinstance(parent, TabCreateIconset):
                    parent.set_input_image(file_path)


class TabCreateIconset(QWidget):  # Geändert zu QWidget
    def __init__(self):
        super().__init__()
        self.input_image_path = None
        self.preview_pixmap = None
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-family: Helvetica;
                font-size: 14px;
            }
            QLineEdit {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #444;
                padding: 6px;
                border-radius: 4px;
                font-size: 14px;
            }
            QFrame {
                background-color: #2d2d2d;
                border-radius: 8px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Input image selection row
        input_row = QHBoxLayout()
        self.input_label = QLabel("Kein Bild ausgewählt")
        self.input_label.setStyleSheet("color: #aaa; font-size: 13px;")
        input_row.addWidget(self.input_label, alignment=Qt.AlignLeft)

        self.browse_btn = QPushButton("Bild auswählen...")
        self.browse_btn.clicked.connect(self.select_input_image)
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
        """)
        input_row.addWidget(self.browse_btn)

        layout.addLayout(input_row)

        # ANCHOR Preview area (drag & drop) und Größe
        self.preview_frame = QFrame()
        self.preview_frame.setFixedSize(400, 400)
        self.preview_frame.setStyleSheet("background-color: #2d2d2d; border-radius: 8px;")

        preview_layout = QVBoxLayout(self.preview_frame)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        self.preview_label = PreviewLabel()
        preview_layout.addWidget(self.preview_label)

        layout.addWidget(self.preview_frame, alignment=Qt.AlignCenter)

        # Output directory
        output_row = QHBoxLayout()
        self.output_label = QLabel("Zielverzeichnis: ")
        output_row.addWidget(self.output_label)

        self.output_btn = QPushButton("Ordner wählen...")
        self.output_btn.clicked.connect(self.select_output_dir)
        self.output_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
        """)
        output_row.addWidget(self.output_btn)

        layout.addLayout(output_row)

        # Iconset name
        name_row = QHBoxLayout()
        name_label = QLabel("Iconset-Name:")
        name_row.addWidget(name_label)

        self.name_input = QLineEdit("Promptgenerator.iconset")
        name_row.addWidget(self.name_input)

        layout.addLayout(name_row)

        # Generate button (dynamisch)
        self.generate_btn = QPushButton("Erst Bild laden")
        self.generate_btn.clicked.connect(self.generate_iconset)
        self.generate_btn.setEnabled(False)  # Start: deaktiviert
        self.update_generate_button_style()  # Setzt den Anfangsstil
        self.generate_btn.setFixedHeight(36)
        layout.addWidget(self.generate_btn)

        # Exit button (bottom right)
        exit_layout = QHBoxLayout()
        exit_layout.addStretch()
        self.exit_btn = QPushButton("Beenden")
        self.exit_btn.clicked.connect(self.terminate_program)  # Geändert
        self.exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #A52A2A;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #B23B3B;
            }
            QPushButton:pressed {
                background-color: #8B0000;
            }
        """)
        exit_layout.addWidget(self.exit_btn)

        layout.addLayout(exit_layout)

        # Initialize default output directory
        pictures_path = Path.home() / "Pictures"
        self.output_dir = pictures_path / "Iconset"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.update_output_label()

    def update_output_label(self):
        self.output_label.setText(f"Zielverzeichnis: {self.output_dir}")

    def select_input_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Bild auswählen", "", "Bilddateien (*.png *.jpg *.jpeg *.tiff *.bmp *.gif)"
        )
        if file_path:
            self.set_input_image(file_path)

    def set_input_image(self, path):
        self.input_image_path = path
        self.input_label.setText(Path(path).name)

        # Load and show preview
        try:
            pil_img = PILImage.open(path)
            pil_img = pil_img.convert("RGBA")  # Ensure RGBA format

            data = pil_img.tobytes("raw", "RGBA")
            qimage = QImage(data, pil_img.width, pil_img.height, QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimage)

            self.preview_label.setPixmap(pixmap)
            self.preview_pixmap = pixmap

            # Aktiviere den Generate-Button
            self.generate_btn.setText("Iconset generieren")
            self.generate_btn.setEnabled(True)
            self.update_generate_button_style()

        except Exception as e:
            self.preview_label.clear()
            self.preview_label.setText("Fehler beim Laden des Bildes")
            print(f"Preview error: {e}")

    def update_generate_button_style(self):
        """Aktualisiert den Stil des Generate-Buttons basierend auf seinem Zustand"""
        if self.generate_btn.isEnabled():
            self.generate_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #66BB6A;
                }
                QPushButton:pressed {
                    background-color: #388E3C;
                }
            """)
        else:
            self.generate_btn.setStyleSheet("""
                QPushButton {
                    background-color: #666666;
                    color: #aaaaaa;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                }
            """)

    def select_output_dir(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Zielverzeichnis auswählen", str(self.output_dir)
        )
        if directory:
            self.output_dir = Path(directory)
            self.update_output_label()

    # Die drei Methoden dragEnterEvent, dragLeaveEvent und dropEvent
    # wurden aus der TabCreateIconset-Klasse entfernt,
    # da sie jetzt in der PreviewLabel-Klasse sind.

    def generate_iconset(self):
        if not self.input_image_path:
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie ein Eingabebild aus.")
            return

        iconset_name = self.name_input.text().strip()
        if not iconset_name:
            QMessageBox.warning(self, "Fehler", "Bitte geben Sie einen gültigen Namen für das Iconset ein.")
            return

        # Ensure the name ends with .iconset
        if not iconset_name.endswith('.iconset'):
            iconset_name += '.iconset'

        try:
            create_iconset(self.input_image_path, self.output_dir, iconset_name)
            final_path = self.output_dir / iconset_name
            QMessageBox.information(self, "Erfolg", f"Iconset erfolgreich erstellt:\n{final_path}")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Erstellen des Iconsets:\n{str(e)}")

    def terminate_program(self):
        sys.exit(0)  # Beendet das Programm sofort mit Exit-Code 0


# Hinweis: Entfernen Sie den folgenden Block komplett, wenn Sie diesen Code als Modul importieren:
# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = TabCreateIconset()
#     window.show()
# sys.exit(app.exec())
