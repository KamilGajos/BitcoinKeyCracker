# build.py
import os
import subprocess
import shutil

# ═══════════════════════════════════
# BUILD CONFIG
# ═══════════════════════════════════
APP_NAME = "BTC Key"
MAIN_FILE = "menu.py"
ICON_FILE = "logo.png"
ADRESY_FILE = "adresy.txt"

# ═══════════════════════════════════
# CZYŚĆ STARE BUILDY
# ═══════════════════════════════════
print("Cleaning old builds...")
for folder in ["build", "dist"]:
    if os.path.exists(folder):
        shutil.rmtree(folder)
for file in os.listdir("."):
    if file.endswith(".spec"):
        os.remove(file)

# ═══════════════════════════════════
# BUDUJ
# ═══════════════════════════════════
print(f"Building {APP_NAME}...")

cmd = [
    "pyinstaller",
    "--onefile",
    "--windowed",
    f"--name={APP_NAME}",
    f"--icon={ICON_FILE}",
]

# Dodaj plik z adresami WEWNĄTRZ aplikacji
if os.path.exists(ADRESY_FILE):
    # PyInstaller spakuje adresy.txt do srodka
    cmd.extend(["--add-data", f"{ADRESY_FILE}:."])

cmd.append(MAIN_FILE)

subprocess.run(cmd)

# ═══════════════════════════════════
# GOTOWE
# ═══════════════════════════════════
if os.path.exists(f"dist/{APP_NAME}.app"):
    print(f"\n✅ Build complete: dist/{APP_NAME}.app")
elif os.path.exists(f"dist/{APP_NAME}"):
    size_mb = os.path.getsize(f"dist/{APP_NAME}") / 1024 / 1024
    print(f"\n✅ Build complete: dist/{APP_NAME}")
    print(f"   Size: {size_mb:.1f} MB")
else:
    print("\n❌ Build failed")