# Bilder und Prompt Toolbox

![Beispielbild](/bilder/bild1.png)

## Beschreibung

Kurze Projektbeschreibung.

## Features

- Benötigt installiertes Ollama
- Modelle lokal nutzen
- Zugriff auf eine Vielzahl von Modellen

![Features](/bilder/icon.png)

## Beispiel-Tabelle

| Name              | Typ                                  | Beschreibung             |
| ----------------- | ------------------------------------ | ------------------------ |
| Image-to-Text     | Generiert Text durch ein Bild        | Vision-Modelle           |
| Promptgenerator   | Generiert einen Prompt aus Key-Words | LLM's und Vision-Modelle |
| RemoveBackground  | Bilder freistellen.                  | ONNX-Modelle             |
| Iconset erstellen | Icons im ICNS-Format erstellen       | Mac interne Tools        |
| VisionLabeler     | Labelt Bild in einem Verzeichnis     | Vision-Modelle           |

![Image-to-Text](/bilder/Image-to-Text.png)

# TabPromptgenerator

**Ein lokaler, datenschutzfreundlicher Prompt-Generator für Ollama-Modelle – speziell entwickelt für macOS.**

Mit dem **TabPromptgenerator** kannst du mühelos hochwertige Prompts für KI-Modelle von [Ollama](https://ollama.com/) erstellen – entweder basierend auf vordefinierten Anweisungen oder mit deinen eigenen, individuellen Eingaben. Alle Berechnungen laufen **lokal auf deinem Rechner**, ohne jegliche Cloud-Abhängigkeit.

---

## 🚀 Funktionen

- **Lokale Generierung** mit beliebigen Ollama-Modellen (z. B. `llama3`, `mistral`, `phi3` etc.)
- **Zwei Eingabemodi**:
  - **Vordefinierte Anweisungen**: Wähle aus einer Liste und ergänze mit Stichworten.
  - **Benutzerdefinierter Prompt**: Gib deinen eigenen vollständigen Prompt ein.
- **Echtzeit-Vorschau & Bearbeitung**: Der generierte Prompt kann vor dem Speichern überarbeitet werden.
- **Automatische Formatbereinigung** mittels integriertem `text_cleaner`.
- **Speichern & Protokollierung**:
  - Jeder Prompt wird mit Zeitstempel, Modell, Eingabe und Ergebnis in `promptgenerator.csv` gespeichert.
  - Zudem wird er in einer `prompts.txt`-Datei angehängt – ideal für Archivierung oder Weiterverarbeitung.
- **Ein-Klick-Zwischenablage**: Sofort in die Zwischenablage kopieren – mit visuellem Feedback.
- **Komfortables UI**:
  - Dunkles Design mit gut lesbarer Farbgestaltung.
  - Responsive Schaltflächen mit Hover-Effekten.
  - macOS-optimiertes Layout und Schriftskalierung.
- **Ressourcenschonend**: Startet den Ollama-Server bei Bedarf und beendet überflüssige Prozesse automatisch.

---

## 🛠️ Voraussetzungen

- **macOS** (primär entwickelt für macOS, läuft ggf. auch auf Linux/Windows)
- **[Ollama](https://ollama.com/)** installiert und im `PATH` verfügbar
- **Python 3.9+**
- Erforderliche Python-Pakete:
  ```bash
  pip install PySide6 psutil
  ```

![Promptgenerator](/bilder/Promptgenerator.png)
![Promptgenerator](/bilder/Remove-BG.png)
![Promptgenerator](/bilder/Iconset.png)
![VisionLabeler](/bilder/VisionLabeler.png)

## Installation

### Clone Repositorie

Repositorie auf Festplatte klonen

```sh
git clone https://github.com/MarkusR1805/Image-to-Text.git
```

Virtuelle Python-Umgebung erstellen

```sh
python3 -m venv Image-to-Text
```

Bibliotheken installieren

```sh
pip install -r requirements.txt
```
