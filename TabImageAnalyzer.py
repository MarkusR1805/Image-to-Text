# TabImageAnalyzer.py
import sys
import os
import ollama
from enum import Enum
from datetime import datetime
import csv
from pathlib import Path
import time
from PySide6.QtGui import QPixmap, QTextOption, QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton,
    QVBoxLayout, QWidget, QComboBox, QTextEdit, QHBoxLayout,
    QDialog, QFrame, QProgressBar, QScrollArea, QDialogButtonBox, QFileDialog, QLineEdit
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
import helpers1 # hier sind alle System relevanten Funktionen definiert
import text_cleaner
import psutil
import subprocess

def start_ollama_server():
    try:
        # Versuche, den Ollama-Server zu starten
        print("Starte Ollama-Server...")
        ollama_process = subprocess.Popen(["ollama", "serve"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Warte kurz, damit sich der Server initialisieren kann
        time.sleep(3)  # Sekunden warten
        print("Ollama-Server gestartet.")
        return ollama_process
    except Exception as e:
        print(f"Fehler beim Starten von Ollama: {e}")
        return None

def kill_existing_ollama_processes():
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            if 'ollama' in proc.info['name'].lower():
                p = psutil.Process(proc.info['pid'])
                p.terminate()
                p.wait(timeout=3)
                print(f"Prozess {proc.info['pid']} beendet.")
    except Exception as e:
        print(f"Fehler beim beenden von Ollama-Prozessen: {e}")

# Enums für Zustandsverwaltung
class CopyState(Enum):
    READY = 0
    SUCCESS = 1
    ERROR = 2

class AnalyzeState(Enum):
    READY = 0
    ANALYZING = 1
    SUCCESS = 2
    ERROR = 3

from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtWidgets import QTextEdit, QApplication # QApplication für Clipboard

class CustomTextEdit(QTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
            padding: 5px;
            border: 1px solid #ff0000;
            border-radius: 0px;
            color: black;
            background-color: #808080;
        """)
        # Tastenkombination für macOS: Option + Shift + Command + V
        shortcut = QShortcut(QKeySequence("Alt+Shift+Meta+V"), self)
        shortcut.activated.connect(self.paste_without_formatting)

    def paste_without_formatting(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        self.insertPlainText(text)

    def focusInEvent(self, event):
        self.setStyleSheet("""
            padding: 5px;
            border: 1px solid #ff0000;
            border-radius: 0px;
            color: black;
            background-color: #B0B0B0;
        """)
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self.setStyleSheet("""
            padding: 5px;
            border: 1px solid #ff0000;
            border-radius: 0px;
            color: black;
            background-color: #808080;
        """)
        super().focusOutEvent(event)

# Worker für Modellinstallation (Hintergrundthread)
class ModelInstallWorker(QThread):
    finished = Signal(bool, str)  # (Erfolg, Fehlermeldung)
    def __init__(self, ollama_path, model_name):
        super().__init__()
        self.ollama_path = ollama_path
        self.model_name = model_name

    def run(self):
        try:
            result = helpers1.install_model(self.model_name, self.ollama_path)
            self.finished.emit(*result)
        except Exception as e:
            self.finished.emit(False, f"Fehler bei Installation: {str(e)}")

# Hauptfenster
class TabImageAnalyzer(QWidget):
    def __init__(self):
        super().__init__()
        self.copy_state = CopyState.READY
        self.analyze_state = AnalyzeState.READY
        self.image_path = None
        self.ollama_path = helpers1.get_ollama_path()
        self.installation_started = False
        self.install_worker = None
        # Blink-Initialisierung MUSS VOR check_and_install_default_model() erfolgen
        self.blink_timer = QTimer()
        self.blink_state = False
        self.blink_timer.timeout.connect(self.toggle_blink_color)
        self.initUI()
        self.setAcceptDrops(True)
        # Schriftart setzen
        font = QFont()
        font.setPointSize(16)
        self.setFont(font)
        # Automatische Modellinstallation starten
        QTimer.singleShot(0, self.check_and_install_default_model)

    def toggle_blink_color(self):
        """Wechselt die Textfarbe des Statuslabels zwischen Rot und Orange"""
        self.blink_state = not self.blink_state
        if self.blink_state:
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.status_label.setStyleSheet("color: orange; font-weight: normal;")

    def initUI(self):
        self.setWindowTitle("IMAGE-TO-TEXT V3.0 | WWW.DER-ZERFLEISCHER.DE")
        self.center_on_screen()
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)

        # Oberer Bereich: Bildanzeige
        top_layout = QHBoxLayout()

        # Linker Bereich: Bild
        left_panel = QVBoxLayout()
        self.frame_container = QFrame()
        self.frame_container.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_container.setFixedSize(300, 300)
        self.frame_container.setStyleSheet("background-color: #5d5d5d; border-radius: 10px;")
        self.image_label = QLabel("Kein Bild ausgewählt\noder hierher ziehen")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setContentsMargins(5, 5, 5, 5)
        self.image_label.setStyleSheet("background-color: #5d5d5d; border-radius: 5px;")
        image_layout = QVBoxLayout(self.frame_container)
        image_layout.addWidget(self.image_label)
        left_panel.addWidget(self.frame_container)

        self.select_image_button = QPushButton("Bild auswählen")
        self.select_image_button.clicked.connect(self.select_image)
        self.select_image_button.setMinimumHeight(40)
        self.select_image_button.setFont(QFont('', 16, QFont.Weight.Bold))
        self.select_image_button.setStyleSheet(
            "QPushButton {background-color: #4CAF50; color: white; padding: 8px; border-radius: 20px;}"
            "QPushButton:hover {background-color: #45a049;}"
        )
        left_panel.addWidget(self.select_image_button)
        top_layout.addLayout(left_panel, 1)

        # Rechter Bereich: Einstellungen
        right_panel = QVBoxLayout()
        self.status_label = QLabel()
        self.update_ollama_status()
        right_panel.addWidget(self.status_label)
        self.model_label = QLabel("Modell:")
        right_panel.addWidget(self.model_label)
        self.model_combo = QComboBox()
        self.model_combo.setStyleSheet("padding: 5px;")
        right_panel.addWidget(self.model_combo)
        self.instruction_label = QLabel("Anweisung:")
        right_panel.addWidget(self.instruction_label)
        self.instruction_combo = QComboBox()
        self.instruction_combo.setMinimumHeight(50)
        self.instruction_combo.setStyleSheet("padding: 5px;")
        self.load_instructions()
        right_panel.addWidget(self.instruction_combo)
        self.custom_instruction_label = QLabel("Oder eigene Anweisung:")
        right_panel.addWidget(self.custom_instruction_label)
        self.custom_instruction_input = CustomTextEdit()
        self.custom_instruction_input.setFixedHeight(80)
        self.custom_instruction_input.setFont(QFont('', 16, QFont.Weight.Normal))
        self.custom_instruction_input.setStyleSheet("""
            padding: 5px;
            border: 1px solid #ff0000;
            border-radius: 0px;
            color: black;
            background-color: #808080;
        """)
        right_panel.addWidget(self.custom_instruction_input)
        top_layout.addLayout(right_panel, 1)
        main_layout.addLayout(top_layout)

        # Container für TXT/CSV-Dateinamen und Pfadstatus
        filename_container = QWidget()
        filename_container.setStyleSheet("margin-bottom: 10px;")
        filename_container_layout = QVBoxLayout(filename_container)
        filename_layout = QHBoxLayout()
        filename_layout.addWidget(QLabel("TXT-Datei:"))
        self.txt_filename_input = QLineEdit()
        self.txt_filename_input.setPlaceholderText("prompt.txt")
        filename_layout.addWidget(self.txt_filename_input)
        filename_layout.addWidget(QLabel("CSV-Datei:"))
        self.csv_filename_input = QLineEdit()
        self.csv_filename_input.setPlaceholderText("prompt.csv")
        filename_layout.addWidget(self.csv_filename_input)
        filename_container_layout.addLayout(filename_layout)
        self.path_status = QLabel(f"Dateien werden gespeichert in: {helpers1.get_documents_dir()}")
        filename_container_layout.addWidget(self.path_status)
        filename_container.setStyleSheet("""
            background-color: #5d5d5d;
            border: 1px solid #000;
            border-radius: 15px;
            margin-bottom: 0px;
            padding: 8px;
        """)
        main_layout.addWidget(filename_container)

        # Analyse-Buttons nebeneinander
        button_layout = QHBoxLayout()
        self.analyze_button = QPushButton("Bild analysieren")
        self.analyze_button.clicked.connect(self.analyze_image)
        self.analyze_button.setFont(QFont('', 16, QFont.Weight.Bold))
        self.analyze_button.setMinimumHeight(40)
        self.analyze_button.setStyleSheet(
            "QPushButton {background-color: #2196F3; color: white; padding: 10px; border-radius: 20px;}"
            "QPushButton:hover {background-color: #0b7dda;}"
        )
        self.abort_button = QPushButton("Vorgang abbrechen / Cancel")
        self.abort_button.clicked.connect(self.abort_analysis)
        self.abort_button.setFont(QFont('', 16, QFont.Weight.Bold))
        self.abort_button.setMinimumHeight(40)
        self.abort_button.setStyleSheet(
            "QPushButton {background-color: #808080; color: white; padding: 10px; border-radius: 20px;}"
            "QPushButton:hover {background-color: #d32f2f;}"
        )
        self.abort_button.setEnabled(False)
        button_layout.addWidget(self.analyze_button)
        button_layout.addWidget(self.abort_button)

        # Container für die ProgressBar mit fester Höhe
        progress_container = QWidget()
        progress_container.setFixedHeight(24)
        progress_container.setStyleSheet("background-color: #5d5d5d;")
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(
            "QProgressBar {border: 1px solid #ff0000; border-radius: 0px; text-align: center;}"
            "QProgressBar::chunk {background-color: #2196F3;}"
        )
        progress_layout.addWidget(self.progress_bar)
        middle_layout = QVBoxLayout()
        middle_layout.addLayout(button_layout)
        middle_layout.addWidget(progress_container)
        main_layout.addLayout(middle_layout)

        # Textergebnis mit Scrollbar
        bottom_layout = QVBoxLayout()
        result_label = QLabel("Analyseergebnis:")
        bottom_layout.addWidget(result_label)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: 1px solid #ccc;")
        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)
        self.text_output.setMinimumHeight(80)
        self.text_output.setFont(QFont("Arial", 14))
        text_options = self.text_output.document().defaultTextOption()
        text_options.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        self.text_output.document().setDefaultTextOption(text_options)
        self.text_output.setStyleSheet("padding: 5px; background-color: #2d2d2d; color: white;")
        scroll_area.setWidget(self.text_output)
        bottom_layout.addWidget(scroll_area)

        # Copy-Button + Beenden
        action_layout = QHBoxLayout()
        self.copy_button = QPushButton("In Zwischenablage kopieren")
        self.copy_button.clicked.connect(self.copy_text_to_clipboard)
        self.copy_button.setMinimumHeight(40)
        self.copy_button.setFont(QFont('', 16, QFont.Weight.Bold))
        self.copy_button.setStyleSheet(
            "QPushButton {background-color: #ff9800; color: white; padding: 8px; border-radius: 20px;}"
            "QPushButton:hover {background-color: #e68a00;}"
        )
        action_layout.addWidget(self.copy_button)
        self.quit_button = QPushButton("Beenden")
        self.quit_button.clicked.connect(QApplication.instance().quit)
        self.quit_button.setMinimumHeight(40)
        self.quit_button.setFont(QFont('', 16, QFont.Weight.Bold))
        self.quit_button.setStyleSheet(
            "QPushButton {background-color: #f44336; color: white; padding: 8px; border-radius: 20px;}"
            "QPushButton:hover {background-color: #d32f2f;}"
        )
        action_layout.addWidget(self.quit_button)
        bottom_layout.addLayout(action_layout)
        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

    def center_on_screen(self):
        screen_geometry = QApplication.primaryScreen().geometry()
        window_geometry = self.geometry()
        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2
        self.move(x, y)

    def check_and_install_default_model(self):
        if not self.ollama_path:
            self.status_label.setText("Ollama nicht gefunden. Bitte installiere Ollama.")
            self.status_label.setStyleSheet("color: red;")
            return
        models, _ = helpers1.get_ollama_models(self.ollama_path)
        if helpers1.DEFAULT_MODEL in models:
            self.load_models()
            return
        self.status_label.setText(f"Installiere Modell '{helpers1.DEFAULT_MODEL}'... (bitte warten)")
        self.blink_timer.start(500)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(10)
        self.install_worker = ModelInstallWorker(self.ollama_path, helpers1.DEFAULT_MODEL)
        self.install_worker.finished.connect(self.handle_model_installation)
        self.install_worker.finished.connect(lambda _, __: self.blink_timer.stop())
        self.install_worker.finished.connect(lambda _, __: self.status_label.setStyleSheet(""))
        self.install_worker.start()

    def handle_model_installation(self, success, error):
        self.progress_bar.setValue(100)
        QTimer.singleShot(1000, lambda: self.progress_bar.setVisible(False))
        if success:
            self.status_label.setText(f"Modell '{helpers1.DEFAULT_MODEL}' erfolgreich installiert ✅")
            self.status_label.setStyleSheet("color: green;")
            self.load_models()
        else:
            self.status_label.setText(f"Modellinstallation fehlgeschlagen ❌\n{error[:100]}...")
            self.status_label.setStyleSheet("color: red;")
        self.activateWindow()
        self.raise_()

    def update_ollama_status(self):
        if self.ollama_path:
            self.status_label.setText(f"Ollama gefunden: {self.ollama_path}")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText("Ollama nicht gefunden. Bitte installieren.")
            self.status_label.setStyleSheet("color: red;")

    def load_instructions(self):
        try:
            instructions_path = helpers1.get_resource_path("anweisungen.txt")
            with open(instructions_path, "r", encoding='utf-8') as f:
                instructions = [line.strip() for line in f.read().splitlines() if line.strip()]
                if instructions:
                    self.instruction_combo.addItems(instructions)
                else:
                    self.instruction_combo.addItem("Keine Anweisungen gefunden")
        except Exception as e:
            self.instruction_combo.addItem(f"Fehler: {e}")

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
            'llava', 'bakllava', 'moondream', 'gemma', 'mistral',
            'llama3.2-vision', 'cogvlm', 'minicpm', 'deepseek'
        ]

        vision_models = []
        for model in models:
            model_lower = model.lower()

            # 0. Zusätzliche Schlüsselwörter im Namen prüfen
            if 'vision' in model_lower or 'vl' in model_lower or 'image' in model_lower:
                vision_models.append(model)
                continue

            # 1. Prüfe Hardcode-Liste (Performance-Optimierung)
            if any(patt.lower() in model_lower for patt in VISION_MODEL_PATTERNS):
                vision_models.append(model)
                continue

            # 2. Capability-Check für unbekannte Modelle
            try:
                model_info = ollama.show(model)
                if hasattr(model_info, 'capabilities') and 'vision' in model_info.capabilities:
                    vision_models.append(model)
                    self.text_output.append(f"⚠️ Neu entdecktes Vision-Modell: {model}")
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
            'llava', 'llama3.2-vision', 'bakllava',
            'moondream', 'gemma', 'mistral-small'
        ]

        for priority in priority_order:
            for model in vision_models:
                if priority in model.lower():
                    self.model_combo.setCurrentText(model)
                    self.text_output.append(f"Prioritätsmodell: {model}")
                    return

        self.model_combo.setCurrentIndex(0)  # Fallback

    def _show_no_models_warning(self):
        """Hilfsfunktion für Fehlermeldung"""
        self.model_combo.addItem("Keine Vision-Modelle (z.B. 'ollama pull llava')")
        self.model_combo.setEnabled(False)
        self.text_output.append("❌ Keine Vision-Modelle gefunden")

    def select_image(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Bilder (*.png *.jpg *.jpeg *.bmp)")
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self.load_image(selected_files[0])

    def load_image(self, file_path):
        if os.path.exists(file_path) and file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            self.image_path = file_path
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                self.image_label.setText("Fehler beim Laden")
                self.image_path = None
                return
            available_width = self.image_label.width() - 10
            available_height = self.image_label.height() - 10
            scaled_pixmap = pixmap.scaled(
                available_width, available_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            self.text_output.clear()
            self.analyze_state = AnalyzeState.READY
        else:
            self.image_label.clear()
            self.image_label.setText("Ungültige Datei ausgewählt.")

    def abort_analysis(self):
        print("Abbruch-Button wurde geklickt.")
        if hasattr(self, 'worker') and self.worker is not None and self.worker.isRunning():
            print("Worker wird beendet...")
            self.worker.terminate()
            self.worker.wait()
            self.worker.deleteLater()
            self.worker = None
        self.text_output.setText("❌ Analyse wurde abgebrochen.")
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        self.analyze_state = AnalyzeState.READY
        self.update_analyze_button_style()
        self.abort_button.setEnabled(False)
        self.abort_button.setStyleSheet(
            "QPushButton {background-color: #808080; color: white; padding: 10px; border-radius: 20px;}"
            "QPushButton:hover {background-color: #d32f2f;}"
        )
        print("Analyse erfolgreich abgebrochen.")

    def analyze_image(self):
        if not self.image_path:
            self.text_output.setText("Bitte wählen Sie zuerst ein Bild aus.")
            return
        selected_model = self.model_combo.currentText()
        custom_instruction = self.custom_instruction_input.toPlainText().lstrip()
        instruction = custom_instruction or self.instruction_combo.currentText()
        if not instruction.strip():
            self.text_output.setText("⚠️ Bitte geben Sie eine Anweisung ein.")
            return
        try:
            ollama.chat(model=selected_model, messages=[{'role': 'user', 'content': 'ping'}])
        except Exception as e:
            print("Ollama nicht erreichbar. Versuche Neustart...")
            kill_existing_ollama_processes()
            self.ollama_process = start_ollama_server()
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(10)
        self.text_output.setText("🔄 Analysiere...")
        self.analyze_state = AnalyzeState.ANALYZING
        self.update_analyze_button_style()
        self.abort_button.setEnabled(True)
        self.abort_button.setStyleSheet(
            "QPushButton {background-color: #d32f2f; color: white; padding: 10px; border-radius: 20px;}"
            "QPushButton:hover {background-color: red;}"
        )
        self.worker = AnalysisWorker(selected_model, self.image_path, instruction)
        self.worker.finished.connect(self.handle_analysis_result)
        self.worker.error.connect(self.handle_analysis_error)
        self.worker.start()

    def clean_description(self, text):
        cleaned = text.strip().replace('\n', ' ').strip('"').strip("'")
        if not cleaned.endswith('.'):
            cleaned += '.'
        return cleaned

    def handle_analysis_result(self, result):
        self.progress_bar.setValue(90)
        dialog = TextEditDialog(result, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            edited_text = dialog.get_text()
            self.text_output.setText(edited_text)
            txt_filename = self.txt_filename_input.text().strip() or "prompt.txt"
            txt_path = helpers1.get_documents_dir() / txt_filename
            txt_path.parent.mkdir(parents=True, exist_ok=True)
            with open(txt_path, "a", encoding="utf-8") as f:
                f.write(f"{edited_text}\n")
            csv_filename = self.csv_filename_input.text().strip() or "prompt.csv"
            csv_path = helpers1.get_documents_dir() / csv_filename
            model_name = self.model_combo.currentText()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                csv_path.parent.mkdir(parents=True, exist_ok=True)
                file_exists = csv_path.exists()
                with open(csv_path, "a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow(["Modell", "Timestamp", "Beschreibung"])
                    writer.writerow([model_name, timestamp, edited_text])
            except Exception as e:
                print(f"Fehler beim Speichern in CSV: {e}")
        else:
            self.text_output.setText("❌ Analyse abgebrochen: Ergebnis nicht übernommen.")
            self.analyze_state = AnalyzeState.READY
            self.update_analyze_button_style()
        self.progress_bar.setValue(100)
        self.progress_bar.setVisible(False)
        self.analyze_state = AnalyzeState.READY
        self.update_analyze_button_style()
        self.abort_button.setEnabled(False)
        self.abort_button.setStyleSheet(
            "QPushButton {background-color: #808080; color: white; padding: 10px; border-radius: 20px;}"
            "QPushButton:hover {background-color: #d32f2f;}"
        )

    def handle_analysis_error(self, error):
        self.text_output.setText(f"❌ Fehler: {error}")
        self.analyze_state = AnalyzeState.ERROR
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)

    def update_analyze_button_style(self):
        if self.analyze_state == AnalyzeState.ANALYZING:
            self.analyze_button.setStyleSheet("QPushButton {background-color: #ff9800; color: white; border-radius: 20px;}")
        elif self.analyze_state == AnalyzeState.SUCCESS:
            self.analyze_button.setStyleSheet("QPushButton {background-color: green; color: white; border-radius: 20px;}")
        elif self.analyze_state == AnalyzeState.ERROR:
            self.analyze_button.setStyleSheet("QPushButton {background-color: red; color: white; border-radius: 20px;}")
        else:
            self.analyze_button.setStyleSheet("QPushButton {background-color: #2196F3; color: white; border-radius: 20px;}")

    def copy_text_to_clipboard(self):
        text = self.text_output.toPlainText().strip()
        if not text:
            self.copy_state = CopyState.ERROR
            self.update_copy_button_style()
            QTimer.singleShot(2000, self.reset_copy_button_style)
            return
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        self.copy_state = CopyState.SUCCESS
        self.update_copy_button_style()
        QTimer.singleShot(1000, self.reset_copy_button_style)

    def update_copy_button_style(self):
        if self.copy_state == CopyState.SUCCESS:
            self.copy_button.setStyleSheet("QPushButton {background-color: green; color: white; padding: 8px; border-radius: 20px;}")
        elif self.copy_state == CopyState.ERROR:
            self.copy_button.setStyleSheet("QPushButton {background-color: red; color: white; padding: 8px; border-radius: 20px;}")
        else:
            self.copy_button.setStyleSheet("QPushButton {background-color: #ff9800; color: white; padding: 8px; border-radius: 20px;}")

    def reset_copy_button_style(self):
        self.copy_state = CopyState.READY
        self.update_copy_button_style()

    def dragEnterEvent(self, event):
        mime_data = event.mimeData()
        if mime_data.hasUrls() and all(url.isLocalFile() for url in mime_data.urls()):
            for url in mime_data.urls():
                if url.toLocalFile().lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            for url in mime_data.urls():
                self.load_image(url.toLocalFile())
                event.acceptProposedAction()
                return
        event.ignore()

class TextEditDialog(QDialog):
    def __init__(self, initial_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Text bearbeiten")
        self.setModal(True)
        self.setFixedSize(500, 500)
        layout = QVBoxLayout(self)
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(initial_text)
        layout.addWidget(self.text_edit)
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_text(self):
        return self.text_edit.toPlainText()

class AnalysisWorker(QThread):
    finished = Signal(str)
    error = Signal(str)
    def __init__(self, model, image_path, instruction):
        super().__init__()
        self.model = model
        self.image_path = image_path
        self.instruction = instruction

    def run(self):
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{
                    'role': 'user',
                    'content': self.instruction,
                    'images': [self.image_path]
                }]
            )
            raw_text = response.get('message', {}).get('content', '')
            cleaned_text = text_cleaner.clean_text(raw_text)
            self.finished.emit(cleaned_text or "Kein Text erhalten")
        except Exception as e:
            self.error.emit(str(e))

# 🧠 Hauptprogramm
def main():
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Arial", 16))
    app.setStyleSheet("""
        QWidget {
            font-size: 16pt;
        }
        QPushButton {
            font-size: 16pt;
            padding: 10px;
        }
    """)
    main_window = TabImageAnalyzer()
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
