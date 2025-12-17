# TabImageSplitter.py
# Bild-Splitter als Tab für die Hauptanwendung
# Splittet Bilder in drei quadratische Ausschnitte mit perfekter Vorschau.
# Unterstützt Drag & Drop, verschiedene Formate.

import os
from PIL import Image
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton,
    QLabel, QFileDialog, QMessageBox, QProgressBar, QSpinBox,
    QGroupBox, QScrollArea, QListWidgetItem, QApplication, QSizePolicy
)
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import (
    QPixmap, QFont, QDragEnterEvent, QDropEvent
)


class TabImageSplitter(QWidget):
    def __init__(self):
        super().__init__()

        self.target_folder = ""
        self.image_paths = []

        # Schriftart festlegen
        self.setFont(QFont("Arial", 14))

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Einstellungsbereich
        settings_group = QGroupBox("Einstellungen")
        settings_layout = QHBoxLayout()

        size_label = QLabel("Ausschnittgröße (px):")
        settings_layout.addWidget(size_label)

        self.size_spinbox = QSpinBox()
        self.size_spinbox.setRange(256, 4096)
        self.size_spinbox.setValue(1024)
        self.size_spinbox.setSingleStep(128)
        self.size_spinbox.valueChanged.connect(self.update_previews)
        settings_layout.addWidget(self.size_spinbox)

        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)

        # Schaltflächen
        button_layout = QHBoxLayout()
        self.btn_browse = QPushButton("Bilder auswählen")
        self.btn_browse.clicked.connect(self.select_files)
        button_layout.addWidget(self.btn_browse)

        self.btn_folder = QPushButton("Zielordner auswählen")
        self.btn_folder.clicked.connect(self.select_target_folder)
        button_layout.addWidget(self.btn_folder)

        self.btn_preview = QPushButton("Vorschau aktualisieren")
        self.btn_preview.clicked.connect(self.update_previews)
        button_layout.addWidget(self.btn_preview)

        self.btn_exit = QPushButton("Beenden")
        self.btn_exit.clicked.connect(self.close_application)
        self.btn_exit.setStyleSheet("background-color: #f44336; color: white;")
        button_layout.addWidget(self.btn_exit)

        main_layout.addLayout(button_layout)

        # Dateiliste
        list_group = QGroupBox("Ausgewählte Bilder")
        list_layout = QVBoxLayout()

        self.list_files = QListWidget()
        self.list_files.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.list_files.setMinimumHeight(200)
        self.list_files.setStyleSheet("""
            QListWidget { font-size: 14px; }
            QListWidget::item { border-bottom: 1px solid #ddd; padding: 0px; }
        """)
        list_layout.addWidget(self.list_files)

        list_group.setLayout(list_layout)
        main_layout.addWidget(list_group)

        # Vorschau-Bereich
        preview_group = QGroupBox("Vorschau")
        preview_layout = QVBoxLayout()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.preview_container = QWidget()
        self.preview_container_layout = QVBoxLayout()
        self.preview_container_layout.setAlignment(Qt.AlignTop)
        self.preview_container.setLayout(self.preview_container_layout)

        self.scroll_area.setWidget(self.preview_container)
        preview_layout.addWidget(self.scroll_area)

        preview_group.setLayout(preview_layout)
        main_layout.addWidget(preview_group)

        # Fortschrittsbalken
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Verarbeiten-Button
        self.btn_process = QPushButton("Bilder verarbeiten (JPG 80%)")
        self.btn_process.clicked.connect(self.process_images)
        self.btn_process.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 12px;
                font-size: 16px;
            }
        """)
        main_layout.addWidget(self.btn_process)

        # Status-Anzeige
        self.status_label = QLabel("Bereit. Bilder per Drag&Drop oder über 'Bilder auswählen' hinzufügen.")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-style: italic; color: #666; font-size: 14px;")
        main_layout.addWidget(self.status_label)

        # Drag & Drop aktivieren
        self.setAcceptDrops(True)

    # ========== Drag & Drop ==========
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        mimedata = event.mimeData()
        if mimedata.hasUrls():
            for url in mimedata.urls():
                path = url.toLocalFile()
                if os.path.isfile(path) and self.is_image_file(path):
                    self.add_file_to_list(path)
            self.update_previews()

    # ========== Hilfsfunktionen ==========
    def is_image_file(self, filename):
        return filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Bilder auswählen", "",
            "Bilddateien (*.png *.jpg *.jpeg *.webp)")
        if files:
            for file in files:
                if os.path.isfile(file) and self.is_image_file(file):
                    self.add_file_to_list(file)
            self.update_previews()

    def add_file_to_list(self, path):
        if path not in self.image_paths:
            self.image_paths.append(path)

            filename = os.path.basename(path)
            file_size = os.path.getsize(path) / 1024  # KB
            with Image.open(path) as img:
                width, height = img.size
                file_format = img.format or "Unknown"

            item_widget = QWidget()
            item_layout = QHBoxLayout()

            info_label = QLabel(
                f"{filename} | {width}x{height}px | "
                f"{file_format} | {file_size:.1f} KB"
            )
            info_label.setStyleSheet("font-size: 14px;")
            item_layout.addWidget(info_label, 1)

            remove_btn = QPushButton("×")
            remove_btn.setStyleSheet("""
                QPushButton {
                    font-size: 16px;
                    font-weight: bold;
                    color: white;
                    background-color: #f44336;
                    border-radius: 10px;
                    min-width: 20px;
                    max-width: 20px;
                    min-height: 20px;
                    max-height: 20px;
                }
                QPushButton:hover { background-color: #d32f2f; }
            """)
            remove_btn.clicked.connect(lambda checked=False, p=path: self.remove_image(p))
            item_layout.addWidget(remove_btn)

            item_widget.setLayout(item_layout)

            item = QListWidgetItem()
            item.setSizeHint(item_widget.sizeHint())
            self.list_files.addItem(item)
            self.list_files.setItemWidget(item, item_widget)

            self.status_label.setText(f"{len(self.image_paths)} Bilder ausgewählt")

    def remove_image(self, path):
        if path in self.image_paths:
            self.image_paths.remove(path)
            for i in range(self.list_files.count()):
                widget = self.list_files.itemWidget(self.list_files.item(i))
                if widget:
                    label = widget.findChild(QLabel)
                    if label and os.path.basename(path) in label.text():
                        self.list_files.takeItem(i)
                        break
            self.update_previews()
            self.status_label.setText(f"{len(self.image_paths)} Bilder ausgewählt")

    def select_target_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Zielordner auswählen", "")
        if folder:
            self.target_folder = folder
            self.status_label.setText(f"Ziel: {folder} | {len(self.image_paths)} Bilder")

    # ========== Vorschau ==========
    def update_previews(self):
        # Alte Vorschauen löschen
        while self.preview_container_layout.count():
            child = self.preview_container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not self.image_paths:
            return

        target_size = self.size_spinbox.value()

        for path in self.image_paths:
            try:
                # 🔥 DIREKTE LADUNG MIT QPIXMAP — Qt kümmert sich um Farben, Alpha, DPI!
                pixmap = QPixmap(path)
                if pixmap.isNull():
                    raise Exception("Bild konnte nicht geladen werden")

                width = pixmap.width()
                height = pixmap.height()
                is_portrait = height > width

                # Vorschau-Größe (max 400px für längere Seite)
                preview_max = 400
                if is_portrait:
                    preview_height = preview_max
                    preview_width = int(width * (preview_height / height))
                else:
                    preview_width = preview_max
                    preview_height = int(height * (preview_width / width))

                # Skalierte Pixmap für Vorschau
                scaled_pixmap = pixmap.scaled(
                    preview_width, preview_height,
                    Qt.KeepAspectRatio, Qt.SmoothTransformation
                )

                preview_box = QWidget()
                preview_box.setStyleSheet("""
                    border: 1px solid #ccc;
                    padding: 10px;
                    margin-bottom: 15px;
                    background-color: white;
                """)
                box_layout = QVBoxLayout()

                image_container = QWidget()
                image_container.setFixedSize(preview_width + 20, preview_height + 20)
                image_layout = QVBoxLayout()
                image_layout.setContentsMargins(0, 0, 0, 0)

                preview_label = QLabel()
                preview_label.setPixmap(scaled_pixmap)
                preview_label.setAlignment(Qt.AlignCenter)
                preview_label.setScaledContents(False)  # WICHTIG: False, da wir bereits skaliert haben

                image_layout.addWidget(preview_label, 0, Qt.AlignCenter)
                image_container.setLayout(image_layout)

                # Zielgröße berechnen (mit PIL für genaue Berechnung)
                with Image.open(path) as img_pil:
                    pil_width, pil_height = img_pil.size
                    pil_is_portrait = pil_height > pil_width

                    if pil_is_portrait:
                        target_width = target_size
                        target_height = int(pil_height * (target_width / pil_width))
                    else:
                        target_height = target_size
                        target_width = int(pil_width * (target_height / pil_height))

                info_label = QLabel(
                    f"{os.path.basename(path)}\n"
                    f"Original: {pil_width}x{pil_height}px | "
                    f"Skaliert: {target_width}x{target_height}px\n"
                    f"Ausschnitte: {target_size}x{target_size}px (JPG 80%)"
                )
                info_label.setAlignment(Qt.AlignCenter)
                info_label.setStyleSheet("font-size: 14px;")

                box_layout.addWidget(image_container, 0, Qt.AlignCenter)
                box_layout.addWidget(info_label)
                preview_box.setLayout(box_layout)

                self.preview_container_layout.addWidget(preview_box)

            except Exception as e:
                error_label = QLabel(f"Fehler bei {os.path.basename(path)}: {str(e)}")
                error_label.setStyleSheet("color: red; font-size: 14px;")
                self.preview_container_layout.addWidget(error_label)

        self.preview_container_layout.addStretch()

    # ========== Verarbeitung ==========
    def scale_image(self, img):
        target_size = self.size_spinbox.value()
        width, height = img.size
        is_portrait = height > width

        if is_portrait:
            new_width = target_size
            new_height = int(height * (new_width / width))
        else:
            new_height = target_size
            new_width = int(width * (new_height / height))

        # Konvertiere in RGB für JPEG-Ausgabe
        if img.mode != 'RGB':
            img = img.convert('RGB')

        return img.resize((new_width, new_height), Image.LANCZOS)

    def crop_three_parts(self, img, original_filename):
        target_size = self.size_spinbox.value()
        width, height = img.size
        is_portrait = height > width
        output_path = os.path.join(self.target_folder, original_filename)

        # Sicherstellen, dass das Bild RGB ist für JPEG
        if img.mode != 'RGB':
            img = img.convert('RGB')

        if is_portrait:
            top = img.crop((0, 0, target_size, target_size))
            top.save(f"{output_path}_top.jpg", "JPEG", quality=80)

            mid_y = max(0, (height - target_size) // 2)
            mid = img.crop((0, mid_y, target_size, mid_y + target_size))
            mid.save(f"{output_path}_center.jpg", "JPEG", quality=80)

            bottom_y = max(0, height - target_size)
            bottom = img.crop((0, bottom_y, target_size, height))
            bottom.save(f"{output_path}_bottom.jpg", "JPEG", quality=80)
        else:
            left = img.crop((0, 0, target_size, target_size))
            left.save(f"{output_path}_left.jpg", "JPEG", quality=80)

            mid_x = max(0, (width - target_size) // 2)
            mid = img.crop((mid_x, 0, mid_x + target_size, target_size))
            mid.save(f"{output_path}_center.jpg", "JPEG", quality=80)

            right_x = max(0, width - target_size)
            right = img.crop((right_x, 0, width, target_size))
            right.save(f"{output_path}_right.jpg", "JPEG", quality=80)

    def process_images(self):
        if not self.target_folder:
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie einen Zielordner aus!")
            return

        if not self.image_paths:
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie mindestens ein Bild aus!")
            return

        self.btn_process.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        try:
            total = len(self.image_paths)
            for i, image_path in enumerate(self.image_paths):
                self.status_label.setText(f"Verarbeite {i+1}/{total}...")
                self.progress_bar.setValue(int((i+1)/total*100))

                try:
                    original_filename = os.path.splitext(os.path.basename(image_path))[0]
                    with Image.open(image_path) as img:
                        img_scaled = self.scale_image(img)
                        self.crop_three_parts(img_scaled, original_filename)
                except Exception as e:
                    QMessageBox.warning(
                        self, "Fehler",
                        f"Fehler bei {os.path.basename(image_path)}: {str(e)}"
                    )

            QMessageBox.information(
                self, "Erfolg",
                f"Alle {total} Bilder wurden erfolgreich verarbeitet!"
            )
            self.status_label.setText("Fertig! Bilder wurden gespeichert.")

        finally:
            self.btn_process.setEnabled(True)
            self.progress_bar.setVisible(False)

    def close_application(self):
        reply = QMessageBox.question(
            self, "Beenden?",
            "Möchtest du die gesamte Anwendung beenden?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            QApplication.instance().quit()
