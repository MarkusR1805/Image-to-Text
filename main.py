#!/usr/bin/env python3
# image-to-text von Gerüstscript main.py

__version__ = "6.1"   # Versionsnummer der App

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget
from PySide6.QtGui import QFont

# Datei der Testversion – soll gelöscht werden, falls vorhanden
START_FILE = Path.home() / '.dzitt'

def cleanup_test_file():
    if START_FILE.exists():
        try:
            START_FILE.unlink()  # Löscht die Datei
            print(f"Testdatei gelöscht: {START_FILE}")
        except OSError as e:
            print(f"Fehler beim Löschen der Testdatei: {e}")

# Lösche die Testdatei, falls vorhanden
cleanup_test_file()

# Importiere deine Tabs
from TabImageAnalyzer import TabImageAnalyzer   # ← Sucht nach TabImageAnalyzer.py und lädt die Klasse TabApp1
from TabPromptgenerator import TabPromptgenerator   # ← Sucht nach TabPromptgenerator.py und lädt die Klasse TabApp2
from TabImageLabeln import TabImageLabeln   # ← Sucht nach TabImageLabeln.py und lädt die Klasse TabApp2
from TabCreateIconset import TabCreateIconset  # TabCreatorIconset importieren
from TabRemoveBGModels import TabRemoveBG  # RemoveBackground Tab importieren
from TabImageSplitter import TabImageSplitter

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Bilder und Prompt Toolbox {__version__} ")

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

        self.TabRemoveBG = TabRemoveBG()
        self.tabs.addTab(self.TabRemoveBG, "RemoveBackground")

        self.TabImageSplitter = TabImageSplitter()
        self.tabs.addTab(self.TabImageSplitter, "Image-Splitter")

        self.TabCreateIconset = TabCreateIconset()  # ← Tab Icon-Set erstellen
        self.tabs.addTab(self.TabCreateIconset, "Iconset erstellen")

        self.TabImageLabeln = TabImageLabeln() # ← Tab ImageLabeln erstellen
        self.tabs.addTab(self.TabImageLabeln, "VisionLabeler")

        print("Verfügbare Tabs:", [self.tabs.tabText(i) for i in range(self.tabs.count())])

# Starte Anwendung
app = QApplication(sys.argv)
window = MainWindow()
window.resize(980, 790)
window.show()
sys.exit(app.exec())
