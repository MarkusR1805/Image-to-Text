# TabRemoveBG.py
import io
import sys
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QMessageBox, QComboBox, QGroupBox,
    QCheckBox, QApplication, QProgressBar, QSizePolicy,
    QDialog, QSpinBox, QGridLayout
)
from PySide6.QtGui import QPixmap, QImage, QDragEnterEvent, QDropEvent, QIcon, QPainter, QPen, QColor
from PySide6.QtCore import Qt, QBuffer, QIODevice, QThread, Signal, QObject, QPoint, QSize

from PIL import Image, ImageFilter
import numpy as np
from skimage.morphology import binary_erosion, disk

# === Unterstützte Bildformate ===
SUPPORTED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.webp', '.tiff', '.tif'}

def is_supported_image(filepath: str) -> bool:
    return Path(filepath).suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS

def get_default_export_dir():
    desktop = Path.home() / "Desktop"
    export_dir = desktop / "RemoveBG"
    export_dir.mkdir(exist_ok=True)
    return export_dir

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

def get_models_dir():
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys.executable).parent
    else:
        base_dir = Path(__file__).parent
    return base_dir / "models"

models_dir = get_models_dir()
models_dir.mkdir(exist_ok=True)
os.environ["U2NET_HOME"] = str(models_dir)

from rembg import remove, new_session


# =============================================
# Hilfsfunktion: Widget → Bild-Koordinaten
# =============================================
def widget_to_image_coords(widget_pos: QPoint, canvas_size: QSize, img_size: QSize) -> QPoint:
    scale_x = img_size.width() / canvas_size.width()
    scale_y = img_size.height() / canvas_size.height()
    scale = min(scale_x, scale_y)

    offset_x = (canvas_size.width() - img_size.width() / scale) / 2
    offset_y = (canvas_size.height() - img_size.height() / scale) / 2

    img_x = (widget_pos.x() - offset_x) * scale
    img_y = (widget_pos.y() - offset_y) * scale

    if 0 <= img_x < img_size.width() and 0 <= img_y < img_size.height():
        return QPoint(int(img_x), int(img_y))
    return None


# =============================================
# Eigenes Canvas-Widget
# =============================================
class PaintCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.background_pixmap = None
        self.mouse_widget_pos = None
        self.brush_size = 20
        self.draw_mode = "keep"
        self.setMouseTracking(True)
        self.setMinimumSize(800, 600)
        self.setStyleSheet("background-color: #2a2a2a;")
        self._cursor_hidden = False

    def set_background(self, pixmap: QPixmap):
        self.background_pixmap = pixmap
        self.update()

    def set_brush(self, size: int, mode: str):
        self.brush_size = size
        self.draw_mode = mode
        self.update()

    def enterEvent(self, event):
        self.setCursor(Qt.BlankCursor)
        self._cursor_hidden = True
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setCursor(Qt.ArrowCursor)
        self._cursor_hidden = False
        self.mouse_widget_pos = None
        self.update()
        super().leaveEvent(event)

    def mouseMoveEvent(self, event):
        self.mouse_widget_pos = event.position().toPoint()
        self.update()
        super().mouseMoveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.background_pixmap:
            scaled = self.background_pixmap.scaled(
                self.width(), self.height(),
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)

            if self.mouse_widget_pos and self._cursor_hidden:
                color = Qt.green if self.draw_mode == "keep" else Qt.red
                pen = QPen(color, 1, Qt.DashLine)
                pen.setCosmetic(True)
                painter.setPen(pen)
                r = self.brush_size // 2
                if r > 2:
                    painter.drawEllipse(self.mouse_widget_pos, r, r)
                    painter.drawLine(self.mouse_widget_pos.x() - r//2, self.mouse_widget_pos.y(),
                                     self.mouse_widget_pos.x() + r//2, self.mouse_widget_pos.y())
                    painter.drawLine(self.mouse_widget_pos.x(), self.mouse_widget_pos.y() - r//2,
                                     self.mouse_widget_pos.x(), self.mouse_widget_pos.y() + r//2)

        painter.end()


# =============================================
# Masken-Nachbearbeitungsdialog
# =============================================
class MaskRefinementDialog(QDialog):
    def __init__(self, original_image: Image.Image, mask_image: Image.Image, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Masken-Nachbearbeitung")
        self.resize(900, 700)
        self.original_image = original_image.convert("RGBA")
        self.mask = mask_image.convert("L")
        self.refined_mask = self.mask.copy()
        self.brush_size = 20
        self.draw_mode = "keep"
        self.drawing = False
        self.setup_ui()
        self.render_background()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.canvas = PaintCanvas()
        layout.addWidget(self.canvas)

        control_layout = QGridLayout()
        control_layout.addWidget(QLabel("Pinselgröße:"), 0, 0)
        self.brush_spin = QSpinBox()
        self.brush_spin.setRange(5, 100)
        self.brush_spin.setValue(self.brush_size)
        self.brush_spin.valueChanged.connect(self.on_brush_size_change)
        control_layout.addWidget(self.brush_spin, 0, 1)

        self.mode_keep_btn = QPushButton("Behalten (weiß)")
        self.mode_keep_btn.setCheckable(True)
        self.mode_keep_btn.setChecked(True)
        self.mode_keep_btn.clicked.connect(lambda: self.set_draw_mode("keep"))
        control_layout.addWidget(self.mode_keep_btn, 0, 2)

        self.mode_remove_btn = QPushButton("Entfernen (schwarz)")
        self.mode_remove_btn.setCheckable(True)
        self.mode_remove_btn.clicked.connect(lambda: self.set_draw_mode("remove"))
        control_layout.addWidget(self.mode_remove_btn, 0, 3)

        reset_btn = QPushButton("Maske zurücksetzen")
        reset_btn.clicked.connect(self.reset_mask)
        control_layout.addWidget(reset_btn, 1, 0, 1, 2)

        ok_btn = QPushButton("Übernehmen")
        ok_btn.clicked.connect(self.accept)
        control_layout.addWidget(ok_btn, 1, 2, 1, 2)

        layout.addLayout(control_layout)
        self.setLayout(layout)

    def set_draw_mode(self, mode):
        self.draw_mode = mode
        self.mode_keep_btn.setChecked(mode == "keep")
        self.mode_remove_btn.setChecked(mode == "remove")
        self.canvas.set_brush(self.brush_size, self.draw_mode)

    def on_brush_size_change(self, value):
        self.brush_size = value
        self.canvas.set_brush(self.brush_size, self.draw_mode)

    def reset_mask(self):
        self.refined_mask = self.mask.copy()
        self.render_background()

    def render_background(self):
        overlay = Image.new("RGBA", self.original_image.size, (0, 0, 0, 0))
        mask_rgba = Image.merge("RGBA", [
            self.refined_mask,
            self.refined_mask,
            self.refined_mask,
            self.refined_mask
        ])
        combined = Image.alpha_composite(self.original_image, mask_rgba)

        try:
            from PIL.ImageQt import ImageQt
            qimage = ImageQt(combined)
        except:
            data = combined.tobytes("raw", "RGBA")
            qimage = QImage(data, combined.width, combined.height, QImage.Format_RGBA8888)
            qimage = qimage.convertToFormat(QImage.Format_RGBA8888)

        pixmap = QPixmap.fromImage(qimage)
        self.canvas.set_background(pixmap)

    def get_canvas_image_pos(self, widget_pos: QPoint):
        if not self.canvas.background_pixmap:
            return None
        return widget_to_image_coords(
            widget_pos,
            self.canvas.size(),
            self.canvas.background_pixmap.size()
        )

    def mouseMoveEvent(self, event):
        widget_pos = event.position().toPoint()
        img_point = self.get_canvas_image_pos(widget_pos)
        if self.drawing and img_point is not None:
            self.apply_brush_to_mask(img_point)
            self.render_background()
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            widget_pos = event.position().toPoint()
            img_point = self.get_canvas_image_pos(widget_pos)
            if img_point is not None:
                self.drawing = True
                self.apply_brush_to_mask(img_point)
                self.render_background()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False
        super().mouseReleaseEvent(event)

    def apply_brush_to_mask(self, img_point: QPoint):
        r = self.brush_size // 2
        x, y = img_point.x(), img_point.y()
        mask_np = np.array(self.refined_mask)
        h, w = mask_np.shape

        x1, x2 = max(0, x - r), min(w, x + r)
        y1, y2 = max(0, y - r), min(h, y + r)

        if self.draw_mode == "keep":
            mask_np[y1:y2, x1:x2] = 255
        else:
            mask_np[y1:y2, x1:x2] = 0

        self.refined_mask = Image.fromarray(mask_np, mode="L")

    def get_refined_mask(self):
        return self.refined_mask


# =============================================
# Hilfsfunktionen
# =============================================
def refine_mask(mask_image: Image.Image, erosion_px=0, blur_radius=0):
    mask_np = np.array(mask_image)
    if erosion_px > 0:
        binary_mask = mask_np > 128
        eroded = binary_erosion(binary_mask, disk(erosion_px))
        mask_np = (eroded * 255).astype(np.uint8)
    refined = Image.fromarray(mask_np, mode="L")
    if blur_radius > 0:
        refined = refined.filter(ImageFilter.GaussianBlur(blur_radius))
    return refined

def apply_mask_to_image(original: Image.Image, mask: Image.Image) -> Image.Image:
    if original.mode != "RGBA":
        original = original.convert("RGBA")
    if mask.mode != "L":
        mask = mask.convert("L")
    original.putalpha(mask)
    return original


# === Worker für Modell-Laden im Hintergrund ===
class ModelLoader(QObject):
    finished = Signal(object)
    error = Signal(str)

    def load_model(self, model_name):
        try:
            session = new_session(model_name)
            self.finished.emit(session)
        except Exception as e:
            self.error.emit(str(e))


# =============================================
# Haupt-Tab-Klasse
# =============================================
class TabRemoveBG(QWidget):
    def __init__(self):
        super().__init__()
        self.original_pixmap = None
        self.result_pixmap = None
        self.session = None
        self.model_loader = None
        self.thread = None
        self.current_model = "birefnet-general-lite"
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
        self.model_combo.setCurrentText("birefnet-general-lite")
        self.model_combo.currentTextChanged.connect(self.on_model_change)
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        options_layout.addLayout(model_layout)

        # Post-Processing
        self.postprocess_checkbox = QCheckBox("Kanten verbessern (Post-Processing)")
        self.postprocess_checkbox.setChecked(False)
        options_layout.addWidget(self.postprocess_checkbox)

        # Feine Kanten (Erosion)
        erosion_layout = QHBoxLayout()
        self.erosion_checkbox = QCheckBox("Feine Kanten (Verkleinern):")
        self.erosion_spin = QSpinBox()
        self.erosion_spin.setRange(1, 5)
        self.erosion_spin.setValue(2)
        self.erosion_spin.setEnabled(False)
        self.erosion_checkbox.toggled.connect(self.erosion_spin.setEnabled)
        erosion_layout.addWidget(self.erosion_checkbox)
        erosion_layout.addWidget(self.erosion_spin)
        erosion_layout.addStretch()
        options_layout.addLayout(erosion_layout)

        # Weiche Übergänge (Weichzeichnung)
        blur_layout = QHBoxLayout()
        self.blur_checkbox = QCheckBox("Weiche Übergänge (Radius):")
        self.blur_spin = QSpinBox()
        self.blur_spin.setRange(1, 10)
        self.blur_spin.setValue(3)
        self.blur_spin.setEnabled(False)
        self.blur_checkbox.toggled.connect(self.blur_spin.setEnabled)
        blur_layout.addWidget(self.blur_checkbox)
        blur_layout.addWidget(self.blur_spin)
        blur_layout.addStretch()
        options_layout.addLayout(blur_layout)

        # Maske speichern
        self.save_mask_checkbox = QCheckBox("Maske zusätzlich speichern")
        self.save_mask_checkbox.setChecked(False)
        options_layout.addWidget(self.save_mask_checkbox)

        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)

        # === Fortschrittsbalken ===
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(20)
        self.progress_bar.setRange(0, 0)
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

        self.btn_edit_mask = QPushButton("Maskenbearbeitung")
        self.btn_edit_mask.clicked.connect(self.open_mask_editor)
        self.btn_edit_mask.setEnabled(False)
        self.btn_edit_mask.hide()  # Standardmäßig versteckt

        btn_save = QPushButton("Ergebnis speichern…")
        btn_save.clicked.connect(self.save_result)
        btn_save.setEnabled(False)
        self.btn_save = btn_save

        btn_quit = QPushButton("Beenden")
        btn_quit.clicked.connect(self.confirm_quit)

        button_layout.addWidget(btn_load)
        button_layout.addWidget(btn_remove)
        button_layout.addWidget(self.btn_edit_mask)
        button_layout.addWidget(btn_save)
        button_layout.addStretch()
        button_layout.addWidget(btn_quit)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

        # Drag & Drop
        self.setAcceptDrops(True)
        self.label_before.setAcceptDrops(True)

        # Initiales Modell laden (ohne Popup)
        self.on_model_change("birefnet-general-lite", show_info=False)

    # === Drag & Drop ===
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            file_path = urls[0].toLocalFile()
            if is_supported_image(file_path):
                self.load_image_from_path(file_path)
            else:
                ext_list = ", ".join(sorted(SUPPORTED_IMAGE_EXTENSIONS))
                QMessageBox.warning(
                    self,
                    "Ungültiges Format",
                    f"Bitte nur Bilddateien im Format {ext_list.upper()} ziehen."
                )

    # === Modellwechsel ===
    def on_model_change(self, model_name, show_info=True):
        self.current_model = model_name
        if show_info:
            desc = MODEL_DESCRIPTIONS.get(model_name, "Keine Beschreibung verfügbar.")
            QMessageBox.information(self, f"Modell: {model_name}", desc)

        # Maskenbearbeitung nur bei SAM sichtbar
        if model_name.lower() == "sam":
            self.btn_edit_mask.show()
        else:
            self.btn_edit_mask.hide()

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
        exts = " ".join(f"*{ext}" for ext in sorted(SUPPORTED_IMAGE_EXTENSIONS))
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Bild zum Freistellen auswählen", "", f"Bilder ({exts})"
        )
        if file_path and is_supported_image(file_path):
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
            self.original_image = Image.open(bytes_img).convert("RGB")

            # Maske generieren
            self.raw_mask = remove(
                self.original_image,
                session=self.session,
                only_mask=True,
                post_process_mask=self.postprocess_checkbox.isChecked()
            )

            # Nachbearbeitung
            erosion = self.erosion_spin.value() if self.erosion_checkbox.isChecked() else 0
            blur = self.blur_spin.value() if self.blur_checkbox.isChecked() else 0
            self.refined_mask = refine_mask(self.raw_mask, erosion_px=erosion, blur_radius=blur)

            # Ergebnis erstellen
            result_image = apply_mask_to_image(self.original_image, self.refined_mask)
            output_bytes = io.BytesIO()
            result_image.save(output_bytes, format="PNG")
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

            # Masken-Button aktivieren (nur bei SAM)
            if self.current_model.lower() == "sam":
                self.btn_edit_mask.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Hintergrundentfernung fehlgeschlagen:\n{str(e)}")

    # === Maskenbearbeitung öffnen ===
    def open_mask_editor(self):
        if not hasattr(self, 'refined_mask') or not hasattr(self, 'original_image'):
            return
        dialog = MaskRefinementDialog(self.original_image, self.refined_mask, self)
        if dialog.exec() == QDialog.Accepted:
            self.refined_mask = dialog.get_refined_mask()
            result_image = apply_mask_to_image(self.original_image, self.refined_mask)
            output_bytes = io.BytesIO()
            result_image.save(output_bytes, format="PNG")
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

    # === Speichern ===
    def save_result(self):
        if self.result_pixmap is None or not hasattr(self, 'original_image'):
            return

        export_dir = get_default_export_dir()
        default_path = export_dir / "freigestellt.png"
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Freigestelltes Bild speichern",
            str(default_path),
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
            mask_path = Path(save_path).with_stem(Path(save_path).stem + "_maske")
            self.refined_mask.save(mask_path, "PNG")
            messages.append(f"Maske:\n{mask_path}")

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
