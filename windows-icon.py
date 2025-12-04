from PIL import Image
import os

# Pfade anpassen
input_path = "windowsicon.png" # Dein 1024x1024 PNG
output_path = "icon.ico"

# Öffne das PNG-Bild
img = Image.open(input_path)

# Größe für das Windows-Icon festlegen (üblich ist 256x256 oder 512x512, kann aber mehrere Größen enthalten)
# Pillow kann mehrere Größen in einer .ico speichern, was gut ist
sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256), (512, 512)]
icon_sizes = []
for size in sizes:
    # Resizen mit resampling
    resized_img = img.resize(size, Image.Resampling.LANCZOS)
    icon_sizes.append(resized_img)

# Speichere als .ico mit mehreren Größen
icon_sizes[0].save(output_path, format='ICO', append_images=icon_sizes[1:])

print(f"Icon erfolgreich erstellt: {output_path}")
