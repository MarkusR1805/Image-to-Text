# TabPromptgerator.py
import sys
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit, QComboBox,
    QMessageBox, QDialog, QDialogButtonBox, QHBoxLayout, QCheckBox
)
from PySide6.QtGui import QClipboard, QFont
from PySide6.QtCore import QTimer, Qt, QThread, Signal
import helpers2
import text_cleaner
import time
import psutil
import subprocess

def start_ollama_server():
    try:
        print("Starte Ollama-Server...")
        ollama_process = subprocess.Popen(["ollama", "serve"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(3)
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

ANWEISUNGEN_FILE = 'p-generator.txt'
PROMPTS_CSV = 'promptgenerator.csv'

class GenerationThread(QThread):
    finished = Signal(str)
    error = Signal(str)
    cancelled = Signal()

    def __init__(self, instruction, user_input, model):
        super().__init__()
        self.instruction = instruction
        self.user_input = user_input
        self.model = model
        self._is_running = True

    def run(self):
        try:
            if not self._is_running:
                self.cancelled.emit()
                return

            print("Aufruf Ollama...")
            generated_text = helpers2.generate_ollama_prompt(
                self.instruction,
                self.user_input,
                self.model
            )

            if not self._is_running:
                self.cancelled.emit()
                return

            if not generated_text:
                raise RuntimeError("Ollama gab keinen Prompt zurück")

            self.finished.emit(generated_text)

        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        self._is_running = False

class PromptEditDialog(QDialog):
    def __init__(self, prompt):
        super().__init__()
        self.setWindowTitle("Prompt bearbeiten / Edit promptly")
        self.prompt = prompt
        self.initUI()

    def initUI(self):
        self.setFixedSize(600, 400)
        layout = QVBoxLayout()
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(self.prompt)
        layout.addWidget(self.text_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        self.setLayout(layout)

    def get_edited_prompt(self):
        return self.text_edit.toPlainText()

class TabPromptgenerator(QWidget):
    def __init__(self):
        super().__init__()
        self.ollama_path = helpers2.get_ollama_path()
        self.generation_thread = None
        self.was_cancelled = False
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Promptgenerator 3.0 | WWW.DER-ZERFLEISCHER.DE ')
        layout = QVBoxLayout()
        layout.setSpacing(15)

        self.model_label = QLabel('Ollama Modelle / Ollama models:')
        layout.addWidget(self.model_label)

        self.model_combo = QComboBox()
        self.model_combo.setFixedHeight(35)
        self.load_models()
        layout.addWidget(self.model_combo)

        instruction_header_layout = QHBoxLayout()
        self.anweisungen_haupt_label = QLabel('Anweisungen / Instructions:')
        instruction_header_layout.addWidget(self.anweisungen_haupt_label)

        self.instruction_mode_checkbox = QCheckBox("Vordefiniert")
        self.instruction_mode_checkbox.setChecked(True)
        instruction_header_layout.addWidget(self.instruction_mode_checkbox)
        instruction_header_layout.addStretch(1)
        layout.addLayout(instruction_header_layout)

        self.anweisungen_combo = QComboBox()
        self.anweisungen_combo.setFixedHeight(35)
        layout.addWidget(self.anweisungen_combo)

        self.custom_instruction_input = QTextEdit()
        self.custom_instruction_input.setFixedHeight(120)
        self.custom_instruction_input.setPlaceholderText(
            "Geben Sie hier Ihre eigene Anweisung oder den gesamten Prompt ein..."
        )
        self.custom_instruction_input.setStyleSheet(
            """
            QTextEdit {
                background-color: #ECECEC; color: black; padding: 10px;
                border: 1px solid #C0C0C0; border-radius: 5px; caret-color: black;
            }
            QTextEdit:focus { background-color: #DBDBDB; border: 1px solid #A0A0A0; }
            """
        )
        layout.addWidget(self.custom_instruction_input)

        self.begriffe_label = QLabel('Begriffe / Keywords:')
        layout.addWidget(self.begriffe_label)

        self.begriffe_input = QTextEdit()
        self.begriffe_input.setFixedHeight(100)
        self.begriffe_input.setStyleSheet(
            """
            QTextEdit {
                background-color: #808080; color: white; padding: 10px;
                border: 1px solid #ff0000; border-radius: 5px; caret-color: white;
            }
            QTextEdit:focus { background-color: #707070; }
            """
        )
        self.begriffe_input.setPlaceholderText("Geben Sie hier die Begriffe ein...")
        layout.addWidget(self.begriffe_input)

        self.instruction_mode_checkbox.stateChanged.connect(self.toggle_instruction_input_type)
        self.load_anweisungen()
        self.toggle_instruction_input_type()

        button_layout = QHBoxLayout()
        self.generate_button = QPushButton('Generieren / Generate')
        self.generate_button.clicked.connect(self.generate_text)
        self.generate_button.setMinimumHeight(40)
        self.generate_button.setStyleSheet(
            "QPushButton {background-color: #2196F3; color: white; padding: 12px; border-radius: 20px;}"
            "QPushButton:hover {background-color: #0b7dda;}"
        )
        button_layout.addWidget(self.generate_button)

        self.cancel_button = QPushButton('Vorgang abbrechen / Cancel')
        self.cancel_button.clicked.connect(self.cancel_generation)
        self.cancel_button.setMinimumHeight(40)
        self.cancel_button.setEnabled(False)
        self.cancel_button.setStyleSheet(
            "QPushButton {background-color: #808080; color: white; padding: 12px; border-radius: 20px;}"
            "QPushButton:enabled {background-color: #f44336;}"
            "QPushButton:hover:enabled {background-color: #d32f2f;}"
        )
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.generated_text_edit = QTextEdit()
        self.generated_text_edit.setReadOnly(True)
        self.generated_text_edit.setStyleSheet(
            "background-color: #808080; color: white; padding: 10px;"
        )
        layout.addWidget(QLabel("Generierter Prompt:"))
        layout.addWidget(self.generated_text_edit)

        self.copy_button = QPushButton('In Zwischenablage kopieren')
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        self.copy_button.setMinimumHeight(40)
        self.copy_button.setStyleSheet(
            "QPushButton {background-color: #ff9800; color: white; padding: 12px; border-radius: 20px;}"
            "QPushButton:hover {background-color: #e68a00;}"
        )
        layout.addWidget(self.copy_button)

        self.quit_button = QPushButton('Beenden')
        self.quit_button.clicked.connect(QApplication.quit)
        self.quit_button.setMinimumHeight(40)
        self.quit_button.setStyleSheet(
            "QPushButton {background-color: #f44336; color: white; padding: 12px; border-radius: 20px;}"
            "QPushButton:hover {background-color: #d32f2f;}"
        )
        layout.addWidget(self.quit_button)

        self.setLayout(layout)

    def toggle_instruction_input_type(self):
        is_vordefiniert_checked = self.instruction_mode_checkbox.isChecked()

        if is_vordefiniert_checked:
            self.anweisungen_combo.setVisible(True)
            self.anweisungen_combo.setEnabled(True)
            self.custom_instruction_input.setVisible(False)
            self.custom_instruction_input.setEnabled(False)

            self.begriffe_label.setVisible(True)
            self.begriffe_input.setVisible(True)
            self.begriffe_input.setEnabled(True)
        else:
            self.anweisungen_combo.setVisible(False)
            self.anweisungen_combo.setEnabled(False)
            self.custom_instruction_input.setVisible(True)
            self.custom_instruction_input.setEnabled(True)
            self.custom_instruction_input.setFocus()

            self.begriffe_label.setVisible(False)
            self.begriffe_input.setVisible(False)
            self.begriffe_input.setEnabled(False)
            self.begriffe_input.clear()

    def load_anweisungen(self):
        anweisungen = helpers2.read_anweisungen(ANWEISUNGEN_FILE)
        self.anweisungen_combo.clear()
        if anweisungen:
            self.anweisungen_combo.addItems(anweisungen)
            if not self.instruction_mode_checkbox.isChecked():
                self.instruction_mode_checkbox.setChecked(True)
        else:
            QMessageBox.warning(
                self,
                "Hinweis",
                f"Keine vordefinierten Anweisungen in '{ANWEISUNGEN_FILE}' gefunden. "
                "Modus für benutzerdefinierte Eingabe aktiviert."
            )
            if self.instruction_mode_checkbox.isChecked():
                self.instruction_mode_checkbox.setChecked(False)

    def load_models(self):
        models, error = helpers2.get_ollama_models(self.ollama_path)
        if models:
            self.model_combo.addItems(models)
        else:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Keine Modelle gefunden. Fehlermeldung: {error}"
            )

    def generate_text(self):
        try:
            self.was_cancelled = False
            self.cancel_button.setEnabled(True)
            self.generate_button.setEnabled(False)

            selected_model = self.model_combo.currentText()
            final_instruction = ""
            final_user_input = ""

            if self.instruction_mode_checkbox.isChecked():
                if self.anweisungen_combo.count() == 0:
                    QMessageBox.warning(self, "Fehler",
                                        f"Keine vordefinierten Anweisungen geladen. Bitte deaktivieren Sie 'Vordefiniert' "
                                        f"und geben Sie eine eigene Anweisung ein, oder füllen Sie '{ANWEISUNGEN_FILE}'.")
                    self.reset_buttons()
                    return
                final_instruction = self.anweisungen_combo.currentText()
                if not final_instruction:
                    QMessageBox.warning(self, "Auswahl erforderlich", "Bitte wählen Sie eine vordefinierte Anweisung.")
                    self.reset_buttons()
                    return

                final_user_input = self.begriffe_input.toPlainText().strip()
                if not final_user_input:
                    QMessageBox.warning(self, "Eingabe erforderlich", "Bitte geben Sie Begriffe ein.")
                    self.reset_buttons()
                    return
            else:
                final_instruction = self.custom_instruction_input.toPlainText().strip()
                if not final_instruction:
                    QMessageBox.warning(self, "Eingabe erforderlich", "Bitte geben Sie Ihre Anweisung/Ihren Prompt ein.")
                    self.reset_buttons()
                    return
                final_user_input = "" # Im benutzerdefinierten Modus ist user_input leer

            self.generation_thread = GenerationThread(final_instruction, final_user_input, selected_model)
            self.generation_thread.finished.connect(self.on_generation_finished)
            self.generation_thread.error.connect(self.on_generation_error)
            self.generation_thread.cancelled.connect(self.on_generation_cancelled)
            self.generation_thread.start()

        except Exception as e:
            self.on_generation_error(str(e))
            self.reset_buttons()

    def on_generation_finished(self, generated_text):
        try:
            cleaned_text = text_cleaner.clean_text(generated_text)
            self.generated_text_edit.setPlainText(cleaned_text)

            dlg = PromptEditDialog(cleaned_text)
            if dlg.exec():
                edited_prompt = dlg.get_edited_prompt()
                self.generated_text_edit.setPlainText(edited_prompt)

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                keywords_for_csv = self.begriffe_input.toPlainText().strip() if self.instruction_mode_checkbox.isChecked() else self.custom_instruction_input.toPlainText().strip()

                helpers2.save_to_csv(
                    PROMPTS_CSV,
                    timestamp,
                    keywords_for_csv,
                    self.model_combo.currentText(),
                    edited_prompt
                )
                helpers2.append_to_prompt_txt(edited_prompt)
                helpers2.clean_csv(PROMPTS_CSV)

        except Exception as e:
            self.on_generation_error(str(e))
        finally:
            self.reset_buttons()

    def on_generation_cancelled(self):
        self.was_cancelled = True
        self.reset_buttons()
        QMessageBox.information(
            self,
            "Abgebrochen",
            "Die Generierung wurde abgebrochen."
        )

    def on_generation_error(self, error_msg):
        if not self.was_cancelled:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Generierung fehlgeschlagen: {error_msg}"
            )
        self.reset_buttons()

    def cancel_generation(self):
        try:
            if self.generation_thread and self.generation_thread.isRunning():
                self.generation_thread.stop()
        except Exception as e:
            print(f"Fehler beim Abbrechen des Threads: {e}")
        self.on_generation_cancelled()

    def reset_buttons(self):
        self.cancel_button.setEnabled(False)
        self.generate_button.setEnabled(True)

    def copy_to_clipboard(self):
        text = self.generated_text_edit.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.copy_button.setStyleSheet("background-color: green; color: white; padding: 12px; border-radius: 20px;")
            QTimer.singleShot(1000, lambda: self.copy_button.setStyleSheet(
                "QPushButton {background-color: #ff9800; color: white; padding: 12px; border-radius: 20px;}"
                "QPushButton:hover {background-color: #e68a00;}"
            ))
        else:
            QMessageBox.warning(self, "Fehler", "Kein Text zum Kopieren vorhanden")

if __name__ == '__main__':
    if sys.platform != 'darwin':
        print("Diese Anwendung ist primär für macOS entwickelt, könnte aber auch auf anderen Plattformen mit Ollama laufen.")

    app = QApplication(sys.argv)
    app.setStyleSheet(
        """
        QWidget { font-size: 15pt; }
        QPushButton { font-size: 14pt; padding: 10px; }
        QLabel, QCheckBox { font-size: 14pt; }
        QComboBox { font-size: 14pt; padding: 5px; }
        QTextEdit { font-size: 14pt; }
        """
    )

    window = TabPromptgenerator()
    window.resize(800, 750)
    window.show()
    sys.exit(app.exec())
