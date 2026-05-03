# build.py
import os
import subprocess
import shutil

# Build configuration
APP_NAME = "BTC Key"
MAIN_FILE = "menu.py"
ICON_FILE = "logo.png"
ADRESY_FILE = "adresy.txt"

# Clean old builds
print("Cleaning old builds...")
for folder in ["build", "dist"]:
    if os.path.exists(folder):
        shutil.rmtree(folder)
for file in os.listdir("."):
    if file.endswith(".spec"):
        os.remove(file)

# Build the application
print(f"Building {APP_NAME}...")

cmd = [
    "pyinstaller",
    "--onefile",
    "--windowed",
    f"--name={APP_NAME}",
    f"--icon={ICON_FILE}",
]

# Add address file inside the application
if os.path.exists(ADRESY_FILE):
    # PyInstaller will pack adresy.txt inside
    cmd.extend(["--add-data", f"{ADRESY_FILE}:."])

cmd.append(MAIN_FILE)

subprocess.run(cmd)

# Finished
if os.path.exists(f"dist/{APP_NAME}.app"):
    print(f"\nBuild complete: dist/{APP_NAME}.app")
elif os.path.exists(f"dist/{APP_NAME}"):
    size_mb = os.path.getsize(f"dist/{APP_NAME}") / 1024 / 1024
    print(f"\nBuild complete: dist/{APP_NAME}")
    print(f"   Size: {size_mb:.1f} MB")
else:
    print("\nBuild failed")
