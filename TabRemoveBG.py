# TabRemoveBG.py
import io
import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QMessageBox, QComboBox, QGroupBox,
    QCheckBox, QApplication, QProgressBar, QSizePolicy
)
from PySide6.QtGui import QPixmap, QImage, QDragEnterEvent, QDropEvent
from PySide6.QtCore import Qt, QBuffer, QIODevice, QThread, Signal, QObject

from PIL import Image
from rembg import remove, new_session


# === Modell-Beschreibungen ===
MODEL_DESCRIPTIONS = {
    "birefnet-general-lite": "Schnell & hochwertig – beste Wahl für die meisten Bilder (2025).",
    "birefnet-general": "Maximale Qualität für komplexe Szenen – etwas langsamer.",
    "isnet-general-use": "Sehr hochwertig, bewährt – ideal für feine Kanten (z. B. Haare).",
    "birefnet-portrait": "Spezialisiert auf Personen – exzellente Ergebnisse bei Porträts.",
    "birefnet-dis": "Für Produktfotos – scharfe Objekte auf einfachem Hintergrund.",
    "isnet-anime": "Perfekt für Anime, Cartoons und Zeichnungen.",
    "u2net": "Bewährtes Standardmodell – guter Kompromiss.",
    "u2net_human_seg": "Nur für Personen – älter, aber zuverlässig.",
    "u2netp": "Sehr schnell, geringe Qualität – für Echtzeit-Anwendungen.",
    "silueta": "Leichtes Modell – schneller als u2net, weniger Detail.",
    "birefnet-massive": "Alleskönner mit riesigem Training – sehr langsam.",
    "sam": "Universelles Meta-SAM-Modell – sehr groß (375 MB) und langsam.\nNur für Spezialfälle empfohlen."
}

# === Worker für Modell-Laden im Hintergrund ===
class ModelLoader(QObject):
    finished = Signal(object)  # session oder None
    error = Signal(str)

    def load_model(self, model_name):
        try:
            session = new_session(model_name)
            self.finished.emit(session)
        except Exception as e:
            self.error.emit(str(e))


class TabRemoveBG(QWidget):
    def __init__(self):
        super().__init__()
        self.original_pixmap = None
        self.result_pixmap = None
        self.session = None
        self.model_loader = None
        self.thread = None
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        # === Optionen-Gruppe ===
        options_group = QGroupBox("Einstellungen")
        options_layout = QVBoxLayout()

        # Modellauswahl
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Modell:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(list(MODEL_DESCRIPTIONS.keys()))
        self.model_combo.setCurrentText("birefnet-general-lite")  # ← NEU: bestes Standardmodell
        self.model_combo.currentTextChanged.connect(self.on_model_change)
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        options_layout.addLayout(model_layout)

        # Post-Processing
        self.postprocess_checkbox = QCheckBox("Kanten verbessern (Post-Processing)")
        self.postprocess_checkbox.setChecked(False)
        options_layout.addWidget(self.postprocess_checkbox)

        # Maske speichern
        self.save_mask_checkbox = QCheckBox("Maske zusätzlich speichern")
        self.save_mask_checkbox.setChecked(False)
        options_layout.addWidget(self.save_mask_checkbox)

        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)

        # === Fortschrittsbalken (standardmäßig versteckt) ===
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(20)
        self.progress_bar.setRange(0, 0)  # Unbestimmt
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        self.progress_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_layout.addWidget(self.progress_bar)

        # === Bildanzeige: Vorher / Nachher ===
        image_layout = QHBoxLayout()

        self.label_before = QLabel("Ziehe ein Bild hierher\noder klicke 'Bild laden'")
        self.label_before.setAlignment(Qt.AlignCenter)
        self.label_before.setMinimumSize(400, 400)
        self.label_before.setStyleSheet("QLabel { background-color: #2a2a2a; border: 2px dashed #555; color: #cccccc; }")

        self.label_after = QLabel("Ergebnis")
        self.label_after.setAlignment(Qt.AlignCenter)
        self.label_after.setMinimumSize(400, 400)
        self.label_after.setStyleSheet("QLabel { background-color: #2a2a2a; border: 2px solid #555; color: #cccccc; }")

        image_layout.addWidget(self.label_before)
        image_layout.addWidget(self.label_after)
        main_layout.addLayout(image_layout)

        # === Buttons ===
        button_layout = QHBoxLayout()
        btn_load = QPushButton("Bild laden…")
        btn_load.clicked.connect(self.open_image)

        btn_remove = QPushButton("Hintergrund entfernen")
        btn_remove.clicked.connect(self.remove_background)
        btn_remove.setEnabled(False)
        self.btn_remove = btn_remove

        btn_save = QPushButton("Ergebnis speichern…")
        btn_save.clicked.connect(self.save_result)
        btn_save.setEnabled(False)
        self.btn_save = btn_save

        btn_quit = QPushButton("Beenden")
        btn_quit.clicked.connect(self.confirm_quit)

        button_layout.addWidget(btn_load)
        button_layout.addWidget(btn_remove)
        button_layout.addWidget(btn_save)
        button_layout.addStretch()
        button_layout.addWidget(btn_quit)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

        # Drag & Drop
        self.setAcceptDrops(True)
        self.label_before.setAcceptDrops(True)

        # Initiales Modell laden
        self.on_model_change("birefnet-general-lite")

    # === Drag & Drop ===
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                self.load_image_from_path(file_path)
            else:
                QMessageBox.warning(self, "Ungültiges Format", "Bitte nur Bilddateien (PNG, JPG, BMP) ziehen.")

    # === Modellwechsel mit Info + Ladebalken ===
    def on_model_change(self, model_name):
        # Zeige Beschreibung
        desc = MODEL_DESCRIPTIONS.get(model_name, "Keine Beschreibung verfügbar.")
        QMessageBox.information(self, f"Modell: {model_name}", desc)

        # Starte Ladevorgang im Hintergrund
        self.progress_bar.show()
        self.btn_remove.setEnabled(False)

        self.thread = QThread()
        self.model_loader = ModelLoader()
        self.model_loader.moveToThread(self.thread)

        self.thread.started.connect(lambda: self.model_loader.load_model(model_name))
        self.model_loader.finished.connect(self.on_model_loaded)
        self.model_loader.error.connect(self.on_model_error)
        self.model_loader.finished.connect(self.thread.quit)
        self.model_loader.error.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def on_model_loaded(self, session):
        self.session = session
        self.progress_bar.hide()
        if self.original_pixmap is not None:
            self.btn_remove.setEnabled(True)

    def on_model_error(self, error_msg):
        self.progress_bar.hide()
        self.session = None
        QMessageBox.critical(self, "Modell-Fehler", f"Konnte Modell nicht laden:\n{error_msg}")

    # === Bild laden ===
    def open_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Bild zum Freistellen auswählen",
            "",
            "Bilder (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.load_image_from_path(file_path)

    def load_image_from_path(self, path):
        self.original_pixmap = QPixmap(path)
        self.label_before.setPixmap(
            self.original_pixmap.scaled(
                self.label_before.width(),
                self.label_before.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )
        if self.session is not None:
            self.btn_remove.setEnabled(True)
        self.btn_save.setEnabled(False)
        self.result_pixmap = None
        self.label_after.clear()
        self.label_after.setText("Ergebnis")

    # === Hintergrund entfernen ===
    def remove_background(self):
        if self.original_pixmap is None or self.session is None:
            return

        try:
            qimg = self.original_pixmap.toImage()
            buffer = QBuffer()
            buffer.open(QIODevice.WriteOnly)
            qimg.save(buffer, "PNG")
            bytes_img = io.BytesIO(buffer.data().data())
            input_image = Image.open(bytes_img)

            output_image = remove(
                input_image,
                session=self.session,
                post_process_mask=self.postprocess_checkbox.isChecked()
            )

            output_bytes = io.BytesIO()
            output_image.save(output_bytes, format="PNG")
            output_bytes.seek(0)
            qimg_result = QImage.fromData(output_bytes.read(), "PNG")
            self.result_pixmap = QPixmap.fromImage(qimg_result)

            self.label_after.setPixmap(
                self.result_pixmap.scaled(
                    self.label_after.width(),
                    self.label_after.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            )
            self.btn_save.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Hintergrundentfernung fehlgeschlagen:\n{str(e)}")

    # === Speichern (Bild + Maske) ===
    def save_result(self):
        if self.result_pixmap is None or self.original_pixmap is None:
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Freigestelltes Bild speichern",
            "freigestellt.png",
            "PNG-Bild (*.png)"
        )
        if not save_path:
            return
        if not save_path.lower().endswith(".png"):
            save_path += ".png"

        if not self.result_pixmap.save(save_path, "PNG"):
            QMessageBox.warning(self, "Fehler", "Speichern fehlgeschlagen.")
            return

        messages = [f"Freigestelltes Bild:\n{save_path}"]

        if self.save_mask_checkbox.isChecked():
            try:
                qimg = self.original_pixmap.toImage()
                buffer = QBuffer()
                buffer.open(QIODevice.WriteOnly)
                qimg.save(buffer, "PNG")
                bytes_img = io.BytesIO(buffer.data().data())
                input_image = Image.open(bytes_img)

                mask_image = remove(input_image, session=self.session, only_mask=True)
                mask_path = Path(save_path).with_stem(Path(save_path).stem + "_maske")
                mask_image.save(mask_path, "PNG")
                messages.append(f"Maske:\n{mask_path}")
            except Exception as e:
                QMessageBox.warning(self, "Maske-Fehler", f"Maske konnte nicht gespeichert werden:\n{str(e)}")

        QMessageBox.information(self, "Erfolg", "\n\n".join(messages))

    # === Beenden ===
    def confirm_quit(self):
        reply = QMessageBox.question(
            self,
            "Beenden bestätigen",
            "Möchtest du die Anwendung wirklich beenden?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            QApplication.quit()
