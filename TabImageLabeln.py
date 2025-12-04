# TabImageLabeln.py (optimierte Version)
import os
import subprocess
from typing import List
import ollama
from PIL import Image, UnidentifiedImageError
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTextEdit, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication
import helpers1
import text_cleaner

class Worker(QThread):
    progress_update = Signal(str, int)
    log_update = Signal(str)
    finished_signal = Signal()

    def __init__(self, image_dir: str, text_dir: str, prompt: str, model: str, trigger_words: List[str]):
        super().__init__()
        self.image_dir = image_dir
        self.text_dir = text_dir
        self.prompt = prompt
        self.model = model
        self.trigger_words = trigger_words
        self.is_running = True

    def run(self):
        try:
            self.process_images()
        except Exception as e:
            self.log_update.emit(f"❌ Fehler: {str(e)}")
        finally:
            self.finished_signal.emit()

    def stop(self):
        self.is_running = False
        self.wait()

    def process_images(self):
        os.makedirs(self.text_dir, exist_ok=True)

        image_files = sorted([
            f for f in os.listdir(self.image_dir)
            if not f.startswith('.') and f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))
        ])

        if not image_files:
            self.log_update.emit("⚠️ Keine Bilder gefunden.")
            return

        trigger_prefix = ", ".join(self.trigger_words) + ", " if self.trigger_words else ""

        for idx, filename in enumerate(image_files):
            if not self.is_running:
                self.log_update.emit("🛑 Abgebrochen")
                return

            image_path = os.path.join(self.image_dir, filename)
            text_path = os.path.join(self.text_dir, f"{os.path.splitext(filename)[0]}.txt")

            try:
                with Image.open(image_path) as img:
                    img.verify()
            except (IOError, UnidentifiedImageError):
                self.log_update.emit(f"🚫 Überspringe ungültiges Bild: {filename}")
                continue

            self.log_update.emit(f"[{filename}] 🔍 Analysiere...")

            try:
                response = ollama.generate(
                    model=self.model,
                    prompt=self.prompt,
                    images=[image_path],
                    options={"temperature": 0.5}
                )

                cleaned_text = text_cleaner.clean_text(response.get("response", "").strip())
                final_text = trigger_prefix + cleaned_text

                if final_text and not final_text.endswith('.'):
                    final_text += '.'

                with open(text_path, "w", encoding="utf-8") as f:
                    f.write(final_text)

                self.log_update.emit(f"[{filename}] ✅ Fertig")
                self.progress_update.emit(filename, int((idx + 1) / len(image_files) * 100))

            except Exception as e:
                self.log_update.emit(f"❌ Fehler bei {filename}: {str(e)}")
                continue

        if self.is_running:
            self.log_update.emit("✅ Alle Bilder verarbeitet")

class TabImageLabeln(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.image_dir = "./bilder"
        self.text_dir = None
        self.prompt = "Create a text-to-image prompt, without introduction, comments, or tips at the end, without quotation marks, ending with a period."
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Directory selection
        dir_layout = QHBoxLayout()
        self.dir_label = QLabel("Bilderordner:")
        self.dir_input = QLabel("Nicht ausgewählt")
        self.dir_button = QPushButton("Ordner wählen")
        self.dir_button.clicked.connect(self.select_folder)
        dir_layout.addWidget(self.dir_label)
        dir_layout.addWidget(self.dir_input)
        dir_layout.addWidget(self.dir_button)

        # Model selection (optimiert)
        model_layout = QHBoxLayout()
        self.model_label = QLabel("Modell:")
        self.model_combo = QComboBox()
        self.load_models_button = QPushButton("Modelle laden")
        self.load_models_button.clicked.connect(self.load_models)
        model_layout.addWidget(self.model_label)
        model_layout.addWidget(self.model_combo)
        model_layout.addWidget(self.load_models_button)

        # Trigger words
        self.trigger_input = QTextEdit()
        self.trigger_input.setPlaceholderText("Trigger-Wörter (kommagetrennt)")
        self.trigger_input.setMaximumHeight(50)

        # Start button
        self.start_button = QPushButton("Beschreibungen generieren")
        self.start_button.clicked.connect(self.start_processing)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 12px;
                border-radius: 20px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        # Log output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)

        # Quit button
        self.quit_button = QPushButton("Beenden")
        self.quit_button.clicked.connect(QApplication.quit)
        self.quit_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 12px;
                border-radius: 20px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)

        # Assemble layout
        layout.addLayout(dir_layout)
        layout.addLayout(model_layout)
        layout.addWidget(QLabel("Trigger-Wörter:"))
        layout.addWidget(self.trigger_input)
        layout.addWidget(self.start_button)
        layout.addWidget(QLabel("Protokoll:"))
        layout.addWidget(self.log_output)

        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        footer_layout.addWidget(self.quit_button)
        layout.addLayout(footer_layout)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Bilderordner auswählen")
        if folder:
            self.image_dir = folder
            self.dir_input.setText(folder)

    def load_models(self):
        self.model_combo.clear()

        if not hasattr(self, 'ollama_path'):
            self.ollama_path = helpers1.get_ollama_path()

        models, error_msg = helpers1.get_ollama_models(self.ollama_path)

        if not models:
            self.model_combo.addItem("Keine Modelle gefunden. Bitte installieren (z.B. 'llava').")
            self.model_combo.setEnabled(False)
            return

        print("Verfügbare Modelle:", models)  # Debug

        # Kombinierter Ansatz: Hardcode-Liste + Capability-Check
        VISION_MODEL_PATTERNS = [
            'llava', 'bakllava', 'moondream', 'gemma', 'mistral', 'qwen2.5vl',
            'llama3.2-vision', 'cogvlm', 'minicpm', 'deepseek'
        ]

        vision_models = []
        for model in models:
            model_lower = model.lower()
            # 1. Prüfe Hardcode-Liste (Performance-Optimierung)
            if any(patt.lower() in model_lower for patt in VISION_MODEL_PATTERNS):
                vision_models.append(model)
                continue

            # 2. Capability-Check für unbekannte Modelle
            try:
                model_info = ollama.show(model)
                if hasattr(model_info, 'capabilities') and 'vision' in model_info.capabilities:
                    vision_models.append(model)
                    self.log_output.append(f"⚠️ Neu entdecktes Vision-Modell: {model}")
            except Exception as e:
                print(f"Fehler bei Capability-Check für {model}: {e}")

        # Modellauswahl (unverändert)
        if vision_models:
            self._populate_model_selector(vision_models)
        else:
            self._show_no_models_warning()

    def _populate_model_selector(self, vision_models):
        """Hilfsfunktion für Modellauswahl"""
        self.model_combo.addItems(vision_models)

        priority_order = [
            'llama3.2-vision', 'llava', 'bakllava',
            'moondream', 'gemma', 'mistral-small'
        ]

        for priority in priority_order:
            for model in vision_models:
                if priority in model.lower():
                    self.model_combo.setCurrentText(model)
                    self.log_output.append(f"Prioritätsmodell: {model}")
                    return

        self.model_combo.setCurrentIndex(0)  # Fallback

    def _show_no_models_warning(self):
        """Hilfsfunktion für Fehlermeldung"""
        self.model_combo.addItem("Keine Vision-Modelle (z.B. 'ollama pull llava')")
        self.model_combo.setEnabled(False)
        self.log_output.append("❌ Keine Vision-Modelle gefunden")

    def start_processing(self):
        if self.worker and self.worker.isRunning():
            self.cancel_processing()
            return

        model = self.model_combo.currentText()
        if not model or model == "Keine Vision-Modelle":
            QMessageBox.warning(self, "Fehler", "Bitte ein Vision-Modell auswählen!")
            return

        self.start_button.setText("Abbrechen")
        self.start_button.setStyleSheet("background-color: #d32f2f;")

        raw_trigger = self.trigger_input.toPlainText().strip()
        trigger_words = [w.strip() for w in raw_trigger.split(",") if w.strip()]

        self.worker = Worker(
            self.image_dir,
            self.image_dir,  # Speichere Texte im Bildordner
            self.prompt,
            model,
            trigger_words
        )
        self.worker.progress_update.connect(self.update_progress)
        self.worker.log_update.connect(self.append_log)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

    def cancel_processing(self):
        if self.worker:
            self.worker.stop()
            self.append_log("🛑 Verarbeitung abgebrochen")

    def update_progress(self, filename: str, percent: int):
        cursor = self.log_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.select(QTextCursor.LineUnderCursor)
        cursor.removeSelectedText()
        cursor.insertText(f"Fortschritt: {filename} ({percent}%)\n")
        self.log_output.setTextCursor(cursor)

    def append_log(self, message: str):
        self.log_output.append(message)

    def on_finished(self):
        self.start_button.setText("Beschreibungen generieren")
        self.start_button.setStyleSheet("background-color: #4CAF50;")
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
