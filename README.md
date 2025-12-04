# Bilder und Prompt Toolbox

![Beispielbild](/bilder/gguf-q8_00001.png)

## Beschreibung

Kurze Projektbeschreibung.

## Features

- Benötigt installiertes Ollama
- Modelle lokal nutzen
- Zugriff auf eine Vielzahl von Modellen

## Beispiel-Tabelle

| Name            | Typ                                  | Beschreibung             |
| --------------- | ------------------------------------ | ------------------------ |
| Image-to-Text   | Generiert Text durch ein Bild        | Vision-Modelle           |
| Promptgenerator | Generiert einen Prompt aus Key-Words | LLM's und Vision-Modelle |
| VisionLabeler   | Labelt Bild in einem Verzeichnis     | Vision-Modelle           |

![Image-to-Text](/bilder/Image-to-Text.png)
![Promptgenerator](/bilder/Promptgenerator.png)
![Promptgenerator](/bilder/Promptgenerator-2.png)
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
