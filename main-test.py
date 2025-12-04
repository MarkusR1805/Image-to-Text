# oder z. B. ~/Library/Application Support/pythonapps/.start_time.txt oder .image-to-text.txt
import sys
from datetime import datetime, timedelta
from pathlib import Path
from cryptography.fernet import Fernet

# Versteckte Datei im Home-Verzeichnis des Nutzers
START_FILE = Path.home() / '.dzitt'
# MAX_RUNTIME = timedelta(hours=48)
MAX_RUNTIME = timedelta(days=2)

# Ein festes Passwort (als Schlüssel für die Verschlüsselung)
# NICHT VERGESSEN: Diesen Schlüssel geheim halten!
ENCRYPTION_KEY = b'mXDQ1h4ShMhCK4BaqTeiQgbI0WjQN62zY8ZYgYPJDzE='  # Muss 32 Bytes lang sein (Base64-encoded) crypto.py starten für einen neuen Schlüssel
# Beispiel für einen gültigen Schlüssel:
# ENCRYPTION_KEY = Fernet.generate_key()  # Nur einmalig generieren und dann fest einbetten

def get_or_create_encrypted_start_time():
    if START_FILE.exists():
        with open(START_FILE, 'rb') as f:
            encrypted_data = f.read()
        try:
            cipher = Fernet(ENCRYPTION_KEY)
            start_time_str = cipher.decrypt(encrypted_data).decode()
            start_time = datetime.fromisoformat(start_time_str)
        except Exception:
            # Falls Datei beschädigt oder falscher Schlüssel
            start_time = datetime.now()
            save_encrypted_start_time(start_time)
    else:
        start_time = datetime.now()
        save_encrypted_start_time(start_time)
    return start_time

def save_encrypted_start_time(start_time):
    cipher = Fernet(ENCRYPTION_KEY)
    encrypted_data = cipher.encrypt(start_time.isoformat().encode())
    with open(START_FILE, 'wb') as f:
        f.write(encrypted_data)

def is_expired():
    start_time = get_or_create_encrypted_start_time()
    now = datetime.now()
    return now > (start_time + MAX_RUNTIME)

def show_expiry_message(text="Diese Testversion ist abgelaufen."):
    from PySide6.QtWidgets import QApplication, QMessageBox
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowTitle("Testlaufzeit abgelaufen")
    msg.setText(text)
    msg.exec_()
    sys.exit()

if is_expired():
    show_expiry_message()


# Normaler Programmcode hier
#!/usr/bin/env python3
# image-to-text von Gerüstscript main.py
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget
from PySide6.QtGui import QPixmap, QTextOption, QFont

# Importiere deine Tabs
from TabImageAnalyzer import TabImageAnalyzer   # ← Sucht nach TabImageAnalyzer.py und lädt die Klasse TabApp1
from TabPromptgenerator import TabPromptgenerator   # ← Sucht nach TabPromptgenerator.py und lädt die Klasse TabApp2
from TabImageLabeln import TabImageLabeln   # ← Sucht nach TabImageLabeln.py und lädt die Klasse TabApp2

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bilder und Prompt Toolbox 3.5 | Testversion ")
        self.resize(980, 790)  # Startgröße, wird später ignoriert durch setFixedSize

        # 🔒 Fenstergröße fixieren
        self.setFixedSize(980, 790)

        # 🔘 Tabs erstellen
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.tabs.setStyleSheet("""
            QTabBar::tab {
                padding: 8px 10px;
                margin-right: 10px;
                font-size: 14px;
                color: #333333;
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                border-bottom: none;
                transition: all 0.3s ease;
            }

            QTabBar::tab:hover {
                background-color: #808080;
                color: #222222;
            }

            QTabBar::tab:selected {
                /* background-color: white; */
                border-bottom: 3px solid #f44336; /* 🔴 Rote Linie unten */
                color: #404040;
                font-weight: normal;
            }
        """)

        # 🖋 Globale Schriftart
        app.setFont(QFont("Arial", 16))

        # Füge Tabs hinzu
        self.TabImageAnalyzer = TabImageAnalyzer()   # ← Erstelle eine Instanz von TabApp1
        self.tabs.addTab(self.TabImageAnalyzer, "Image-to-Text")

        self.TabPromptgenerator = TabPromptgenerator()   # ← Erstelle eine Instanz von TabApp2
        self.tabs.addTab(self.TabPromptgenerator, "Promptgenerator")

        self.TabImageLabeln = TabImageLabeln()
        self.tabs.addTab(self.TabImageLabeln, "VisionLabeler")

        print("Verfügbare Tabs:", [self.tabs.tabText(i) for i in range(self.tabs.count())])

# Starte Anwendung
app = QApplication(sys.argv)
window = MainWindow()
window.resize(980, 790)
window.show()
sys.exit(app.exec())
