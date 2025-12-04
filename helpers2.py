#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# für Promptgenerator
# helpers2.py
import os
import sys
import platform
import subprocess
import csv
from typing import List, Optional, Tuple
import shutil
from pathlib import Path
import psutil

DEFAULT_MODEL = "llama2:latest"  # Standard-Modellname (passend zu Ollama)

def get_documents_dir() -> Path:
    return Path.home() / "Documents"

def get_platform_info() -> str:
    """Informationen über das Betriebssystem."""
    return f"{platform.system()} {platform.release()} ({platform.machine()})"

def get_ollama_path() -> Optional[str]:
    system = platform.system()
    paths = []

    if system == "Darwin":  # macOS
        paths = [
            '/usr/local/bin/ollama',
            '/opt/homebrew/bin/ollama',
            os.path.expanduser('~/bin/ollama')
        ]
    else:
        return None  # Nur macOS wird unterstützt

    # Erst suche im PATH
    ollama_in_path = shutil.which("ollama")
    if ollama_in_path:
        return ollama_in_path

    # Dann prüfe die vorgegebenen Pfade
    for path in paths:
        if os.path.isfile(path):
            return path

    return None

def read_anweisungen(file_name: str) -> List[str]:
    try:
        file_path = get_resource_path(file_name)
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Fehler beim Lesen der Anweisungen: {str(e)}")
        return []

def get_resource_path(relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def get_ollama_models(ollama_path: Optional[str] = None) -> Tuple[List[str], str]:
    error_msg = ""
    models = []

    if not ollama_path:
        ollama_path = get_ollama_path()
        if not ollama_path:
            return [], "Ollama nicht gefunden"

    try:
        result = subprocess.run(
            [ollama_path, "list"],
            capture_output=True,
            text=True,
            check=True
        )
        lines = result.stdout.splitlines()
        if len(lines) > 1:
            models = [line.split()[0] for line in lines[1:]]
    except subprocess.CalledProcessError as e:
        error_msg = f"Fehler: {e.stderr}"
    except Exception as e:
        error_msg = str(e)

    return models, error_msg

def generate_ollama_prompt(instruction: str, user_terms: str, model: str) -> str:
    ollama_path = get_ollama_path()
    if not ollama_path:
        raise RuntimeError("Ollama nicht gefunden!")

    try:
        command = [ollama_path, "run", model, f"{instruction}: {user_terms}"]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Ollama-Fehler: {e.stderr}") from e
    except Exception as e:
        raise RuntimeError(f"Unbekannter Fehler: {str(e)}") from e

def save_to_csv(
    filename: str,
    timestamp: str,
    user_input: str,
    model_name: str,
    prompt: str
) -> None:
    file_path = get_documents_dir() / filename
    file_exists = file_path.exists()

    try:
        with open(file_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=';')  # Semikolon als Trennzeichen

            # Wenn die Datei neu ist, schreibe zuerst die Spaltenüberschriften
            if not file_exists:
                writer.writerow(["Zeitstempel", "Schlüsselwörter", "Modell", "Prompt"])

            writer.writerow([timestamp, user_input, model_name, prompt])
    except Exception as e:
        raise RuntimeError(f"Fehler beim Speichern in CSV: {str(e)}")

def append_to_prompt_txt(text: str) -> None:
    file_path = get_documents_dir() / "promptgenerator.txt"
    try:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"{text}\n")
    except Exception as e:
        raise RuntimeError(f"Fehler beim Hinzufügen zur TXT-Datei: {str(e)}")

def clean_csv(filename: str) -> None:
    file_path = get_documents_dir() / filename
    try:
        # Prüfe, ob die Datei existiert
        if not file_path.exists():
            return

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if not lines:
            return

        # Behalte die erste Zeile (Überschriften)
        header = lines[0]
        data_lines = lines[1:] if len(lines) > 1 else []

        # Entferne Duplikate und leere Zeilen
        unique_lines = []
        seen = set()
        for line in data_lines:
            stripped = line.strip()
            if stripped and stripped not in seen:
                unique_lines.append(line)
                seen.add(stripped)

        with open(file_path, "w", newline="", encoding="utf-8") as f:
            f.write(header)  # Schreibe die Überschriften
            f.writelines(unique_lines)  # Schreibe die bereinigten Daten
    except Exception as e:
        raise RuntimeError(f"Fehler beim Bereinigen der CSV: {str(e)}")
