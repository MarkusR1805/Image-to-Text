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

## Tab Image-to-Text

![Image-to-Text](/bilder/Image-to-Text.png)

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

## Tab Promptgenerator

![Promptgenerator](/bilder/Promptgenerator.png)

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

## Tab RemoveBackground

![Promptgenerator](/bilder/Remove-BG.png)

**Lokales Freistellen von Bildern – ohne Cloud, ohne Upload, ohne Kompromisse.**

Mit **TabRemoveBG** entfernst du Hintergründe **vollständig offline** auf deinem Mac. Das Tool nutzt hochmoderne, lokal laufende KI-Modelle wie `birefnet`, `isnet` oder `u2net`, um Personen, Produkte oder Objekte blitzschnell freizustellen – **alle Daten bleiben auf deinem Gerät**.

Ob Foto, Porträt, Produktbild oder Anime: Wähle das passende Modell, optimiere die Kanten und exportiere sofort als transparentes PNG.

---

## ✂️ Hauptfunktionen

- **100 % offline** – keine Internetverbindung nötig, kein Datentransfer
- **12 spezialisierte KI-Modelle** für unterschiedliche Bildtypen:
  - `birefnet-general-lite` – **Standardempfehlung**: schnell + hochwertig (2025)
  - `birefnet-portrait` – perfekt für **Gesichter & Haare**
  - `isnet-anime` – optimiert für **Cartoons & Zeichnungen**
  - `birefnet-dis` – ideal für **Produktfotos**
  - `sam` – universelles Segmentierungstool (Meta SAM) mit **manueller Maskenbearbeitung**
- **Drag & Drop** – ziehe Bilder direkt ins Fenster
- **Vorher/Nachher-Ansicht** – direkter visueller Vergleich
- **Post-Processing**:
  - **Kantenverkleinerung** (Erosion) für präzise Haar- oder Fellstrukturen
  - **Weiche Übergänge** (Gaußscher Weichzeichner) für natürliche Transparenz
- **Optionale Maskenspeicherung** – für Weiterverarbeitung in Photoshop, GIMP etc.
- **Interaktive Maskenbearbeitung** (nur bei SAM-Modell):
  - Malen mit **grünen (behält)** und **roten (entfernt)** Pinseln
  - Echtzeit-Vorschau über Originalbild
  - Pinselgröße anpassbar

---

## 🖼️ Unterstützte Formate

- **Eingabe**: `PNG`, `JPG`, `JPEG`, `BMP`, `WEBP`, `TIFF`
- **Ausgabe**: `PNG` mit **Alpha-Kanal** (transparenter Hintergrund)

> Export erfolgt standardmäßig auf dem **Desktop** im Ordner `RemoveBG`.

---

## 🛠️ Voraussetzungen

- **macOS** (empfohlen – läuft ggf. auch auf Linux/Windows)
- **Python 3.9+**
- Benötigte Pakete:
  ```bash
  pip install PySide6 pillow numpy scikit-image rembg
  ```

## Tab Iconset erstellen

![Promptgenerator](/bilder/Iconset.png)

**Erstelle professionelle macOS-Iconsets – lokal, schnell und mit Drag & Drop.**

Mit **TabCreateIconset** generierst du aus einem beliebigen Bild ein vollständiges `.iconset`-Verzeichnis **und eine fertige `.icns`-Datei** – direkt auf deinem Mac. Das Tool nutzt **native macOS-Technologie** (`iconutil`) für maximale Kompatibilität mit Finder, Dock, Apps und DMG-Installationen.

Kein Upload, kein Web-Service – alles läuft **100 % lokal**.

---

## 🍏 macOS-Integration

Dieses Tool ist **ausschließlich für macOS** gedacht und nutzt:

- **`iconutil`** – das offizielle Apple-Tool zur Konvertierung von `.iconset` → `.icns`
- **Native PNG-Generierung** in allen benötigten Auflösungen:
  - 16×16 bis 512×512 Pixel
  - Jeweils mit **1x und 2x (Retina)** Skalierung
- **Automatische `.icns`-Erstellung** – sofort verwendbar in:
  - App-Bundles (`Contents/Resources/`)
  - DMG-Images
  - Dokumenten-Icons
  - Dock und Finder

> ⚠️ **Hinweis**: `iconutil` ist **nur auf macOS verfügbar**. Das Tool funktioniert **nicht unter Windows oder Linux**.

---

## ✨ Funktionen

- **Drag & Drop** – ziehe ein Bild direkt in das Vorschaufenster
- **Live-Vorschau** mit visuellem Feedback beim Ziehen
- **Unterstützte Eingabeformate**: PNG, JPG, JPEG, TIFF, BMP, GIF
- **Automatische Konvertierung** in transparentes RGBA (für saubere `.icns`-Dateien)
- **Benennung frei wählbar** – z. B. `MeineApp.iconset`
- **Standard-Export nach `~/Pictures/Iconset/`** – anpassbar per Button
- **Ein-Klick-Generierung** – inklusive Validierung und Fehlermeldungen
- **Dunkles UI** mit macOS-typischer Ästhetik

---

## 🛠️ Voraussetzungen

- **macOS** (mindestens macOS 10.7+, da `iconutil` vorausgesetzt wird)
- **Python 3.9+**
- Benötigte Pakete:
  ```bash
  pip install PySide6 pillow
  ```

## Tab VisionLabeler

![VisionLabeler](/bilder/VisionLabeler.png)

**Automatisches Batch-Labeling von Bildern mit lokaler Vision-KI – 100 % offline, 100 % macOS.**

Mit **VisionLabeler** generierst du **KI-basierte Beschreibungen für ganze Bildordner** – ideal für:

- **Stable Diffusion-Trainingssätze**
- **Bildarchivierung**
- **Metadaten-Generierung**
- **Prompt-Engineering auf Bestand**

Alle Analysen laufen **lokal mit Ollama Vision-Modellen** (`llava`, `llama3.2-vision` etc.). **Kein Upload, kein Cloud-Dienst, keine Abhängigkeit vom Internet.**

---

## 📦 Hauptfunktionen

- **Batch-Verarbeitung**: Analysiere **ganze Ordner** auf einmal – kein manuelles Klicken pro Bild
- **Lokale Vision-KI**: Nutzt Ollamas **offline-fähige Modelle** wie `llava`, `llama3.2-vision`, `moondream` etc.
- **Einheitliche Ausgabe**: Jedes Bild erhält eine passende `.txt`-Datei im selben Ordner (z. B. `urlaub_001.jpg` → `urlaub_001.txt`)
- **Trigger-Wörter**: Füge vorangestellte Begriffe hinzu (z. B. `photorealistic, 8k, HDR`) – ideal für **Stable Diffusion-Prompts**
- **Automatische Bereinigung**: Entfernt Anführungszeichen, unnötige Einleitungen und fügt einen Punkt am Ende hinzu
- **Echtzeit-Protokoll**: Zeigt Fortschritt, Fehler und Erfolgsmeldungen live an
- **Abbrechen jederzeit möglich**: Stoppe die Verarbeitung bei Bedarf – ohne Datenverlust

---

## 🛠️ Voraussetzungen

- **macOS** (primär entwickelt für macOS, läuft ggf. auch auf Linux/Windows)
- **[Ollama](https://ollama.com/)** mit mindestens einem **Vision-Modell** installiert
  Beispiel:
  ```bash
  ollama pull llava
  ollama pull llama3.2-vision
  ```

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
