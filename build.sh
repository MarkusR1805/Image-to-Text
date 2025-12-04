#!/bin/bash
python3 -m nuitka \
  --standalone \
  --enable-plugin=pyside6 \
  --macos-create-app-bundle \
  --include-data-file=anweisungen.txt=anweisungen.txt \
  --include-data-file=p-generator.txt=p-generator.txt \
  --include-package=ollama \
  --follow-imports \
  --macos-app-icon=icon.icns \
  Image-to-Text.py