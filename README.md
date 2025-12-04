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

## Tab Image-to-Text

**Lokale, visuelle KI-Analyse für Bilder – direkt auf deinem Mac. Keine Cloud, kein Tracking.**

Der **TabImageAnalyzer** nutzt Ollamas Vision-fähige Modelle (z. B. `llava`, `llama3.2-vision`) zur **lokalen Bildbeschreibung und -interpretation**. Ziehe einfach ein Bild per Drag & Drop in das Fenster, gib eine Anweisung ein – und erhalte innerhalb von Sekunden eine präzise, KI-generierte Beschreibung **ohne Internetverbindung**.

---

## 🖼️ Was kann das Tool?

- **Bildanalyse mit lokaler KI**: Keine Daten verlassen deinen Rechner.
- **Unterstützung aller Vision-Modelle** von Ollama:
  - Automatische Erkennung installierter Modelle (`llava`, `bakllava`, `llama3.2-vision`, `moondream` etc.)
  - Capability-basierte Erkennung neuer Vision-Modelle
- **Flexible Anweisungen**:
  - Wähle aus vordefinierten Prompts (`anweisungen.txt`)
  - Oder gib eine eigene Anleitung ein – inklusive **Formatierungsfreiem Einfügen** per `⌥⇧⌘V`
- **Interaktive Ergebnisbearbeitung**: Der generierte Text kann vor dem Speichern korrigiert werden.
- **Automatischer Export**:
  - Speichert jede Analyse als **Zeile in einer CSV-Datei** (Modell, Zeitstempel, Ergebnis)
  - Hängt den Text außerdem an eine **TXT-Datei** an – ideal für Weiterverarbeitung
- **macOS-optimiert**:
  - Drag & Drop
  - Zentriertes Fenster
  - Große, gut lesbare Schrift
  - Dunkles UI mit Kontrast für bessere Lesbarkeit

---

## 🛠️ Voraussetzungen

- **macOS** (empfohlen – läuft ggf. auch auf Linux/Windows)
- **[Ollama](https://ollama.com/)** installiert und im Systempfad
- **Python 3.9+**
- Benötigte Pakete:
  ```bash
  pip install PySide6 psutil ollama
  ```

![Promptgenerator](/bilder/Promptgenerator.png)

## Tab Promptgenerator

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
