import subprocess
import os
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT_PATH = os.path.join(BASE_DIR, 'scripts', 'process_tracker.py')
DIST_PATH = os.path.join(BASE_DIR, 'exe', 'dist')
BUILD_PATH = os.path.join(BASE_DIR, 'exe', 'build')

# Ensure output directories exist
os.makedirs(DIST_PATH, exist_ok=True)
os.makedirs(BUILD_PATH, exist_ok=True)

# Clean previous build/dist folders if they exist
for folder in [DIST_PATH, BUILD_PATH]:
    if os.path.exists(folder):
        shutil.rmtree(folder)
        os.makedirs(folder, exist_ok=True)

# Run PyInstaller
subprocess.run([
    'pyinstaller',
    '--onefile',
    SCRIPT_PATH,
    '--distpath', DIST_PATH,
    '--workpath', BUILD_PATH
])

print(f"\nBuild complete. Executable is in '{DIST_PATH}'.")
