#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# helpers.py - Hilfsfunktionen für ImageAnalyzer
# helpers1.py
import os
import sys
import platform
import subprocess
from typing import List, Optional, Tuple
import shutil
from pathlib import Path

DEFAULT_MODEL = "llava:latest"

def get_documents_dir() -> Path:
    """Gibt den Pfad zum Documents-Ordner des Benutzers als Path-Objekt zurück."""
    return Path.home() / "Documents"

def get_platform_info() -> str:
    """Gibt Informationen über das Betriebssystem zurück."""
    return f"{platform.system()} {platform.release()} ({platform.machine()})"

def get_ollama_path() -> Optional[str]:
    """Findet den Pfad zur Ollama-Executable basierend auf dem Betriebssystem."""
    system = platform.system()

    # Standardpfade basierend auf Betriebssystem
    if system == "Windows":
        possible_paths = [
            os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'), 'Ollama', 'ollama.exe'),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'), 'Ollama', 'ollama.exe'),
            os.path.join(os.environ.get('LOCALAPPDATA', 'C:\\Users\\' + os.getenv('USERNAME') + '\\AppData\\Local'), 'Ollama', 'ollama.exe')
        ]
    elif system == "Darwin":  # macOS
        possible_paths = [
            '/usr/local/bin/ollama',
            '/opt/homebrew/bin/ollama',
            os.path.expanduser('~/bin/ollama')
        ]
    else:  # Linux und andere Unix-Systeme
        possible_paths = [
            '/usr/bin/ollama',
            '/usr/local/bin/ollama',
            '/opt/ollama/bin/ollama',
            os.path.expanduser('~/bin/ollama')
        ]

    # Suche in PATH
    ollama_in_path = shutil.which('ollama')
    if ollama_in_path:
        return ollama_in_path

    # Überprüfe die möglichen Pfade
    for path in possible_paths:
        if os.path.isfile(path):
            return path

    return None

def run_ollama_command(command: List[str], ollama_path: Optional[str] = None) -> Tuple[int, str, str]:
    """Führt einen Ollama-Befehl aus und gibt den Rückgabecode, stdout und stderr zurück."""
    if ollama_path is None:
        ollama_path = get_ollama_path()
        if ollama_path is None:
            return 1, "", "Ollama nicht gefunden. Bitte installieren Sie Ollama."

    try:
        cmd = [ollama_path] + command
        process = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return process.returncode, process.stdout, process.stderr
    except Exception as e:
        return 1, "", f"Fehler bei der Ausführung von Ollama: {str(e)}"

def get_ollama_models(ollama_path: Optional[str] = None) -> Tuple[List[str], str]:
    """
    Holt die Liste der installierten Ollama-Modelle.
    Gibt eine Tuple zurück: (Liste der Modelle, Fehlermeldung falls vorhanden)
    """
    models = []
    error_msg = ""

    returncode, stdout, stderr = run_ollama_command(['list'], ollama_path)

    if returncode == 0 and stdout:
        lines = stdout.strip().splitlines()
        if len(lines) > 1:  # Überschriftzeile überspringen
            for line in lines[1:]:
                parts = line.split()
                if parts:
                    models.append(parts[0])
    else:
        error_msg = stderr if stderr else f"Fehler bei 'ollama list' (Code: {returncode})"

    return models, error_msg

def install_model(model_name: str, ollama_path: Optional[str] = None) -> Tuple[bool, str]:
    """
    Installiert ein Ollama-Modell.
    Gibt ein Tuple zurück: (Erfolg, Fehlermeldung falls vorhanden)
    """
    returncode, stdout, stderr = run_ollama_command(['pull', model_name], ollama_path)

    if returncode == 0:
        return True, ""
    else:
        return False, stderr if stderr else f"Fehler beim Installieren des Modells (Code: {returncode})"

def get_app_data_dir() -> str:
    """
    Gibt das Verzeichnis zurück, in dem Anwendungsdaten gespeichert werden sollen.
    Erstellt das Verzeichnis, falls es nicht existiert.
    """
    system = platform.system()

    if system == "Windows":
        base_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'image-to-prompt')
    elif system == "Darwin":  # macOS
        base_dir = os.path.expanduser('~/Library/Application Support/image-to-prompt')
    else:  # Linux und andere Unix-Systeme
        base_dir = os.path.expanduser('~/.config/image-to-prompt')

    # Verzeichnis erstellen, falls es nicht existiert
    os.makedirs(base_dir, exist_ok=True)

    return base_dir

def get_output_file_path(filename: str = "llama-vision.txt") -> str:
    """
    Gibt den vollständigen Pfad zur Ausgabedatei zurück.
    """
    return os.path.join(get_app_data_dir(), filename)

def save_text_to_file(text: str, filename: str = "llama-vision.txt") -> Tuple[bool, str]:
    """
    Speichert Text in eine Datei im Anwendungsdatenverzeichnis.
    Gibt ein Tuple zurück: (Erfolg, Fehlermeldung falls vorhanden)
    """
    try:
        file_path = get_output_file_path(filename)
        with open(file_path, 'a', encoding='utf-8') as file:
            file.write(text + "\n")
        return True, file_path
    except Exception as e:
        return False, f"Fehler beim Speichern der Datei: {str(e)}"

def get_resource_path(relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)
