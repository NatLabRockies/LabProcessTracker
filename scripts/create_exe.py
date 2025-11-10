import subprocess
import os
import shutil
import sys

# Allow overriding output paths via environment variables
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT_PATH = os.path.join(BASE_DIR, 'scripts', 'process_tracker.py')
DIST_PATH = os.environ.get('DIST_PATH', os.path.join(BASE_DIR, 'exe', 'dist'))
BUILD_PATH = os.environ.get('BUILD_PATH', os.path.join(BASE_DIR, 'exe', 'build'))

# Ensure output directories exist
try:
    os.makedirs(DIST_PATH, exist_ok=True)
    os.makedirs(BUILD_PATH, exist_ok=True)
except Exception as e:
    print(f"Error creating output directories: {e}")
    sys.exit(1)

# Clean previous build/dist folders if they exist
for folder in [DIST_PATH, BUILD_PATH]:
    try:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            os.makedirs(folder, exist_ok=True)
    except Exception as e:
        print(f"Error cleaning folder '{folder}': {e}")
        sys.exit(1)

# Run PyInstaller with error handling
try:
    result = subprocess.run([
        'pyinstaller',
        '--onefile',
        SCRIPT_PATH,
        '--distpath', DIST_PATH,
        '--workpath', BUILD_PATH
    ], check=True)
except subprocess.CalledProcessError as e:
    print(f"PyInstaller failed with exit code {e.returncode}")
    sys.exit(e.returncode)
except Exception as e:
    print(f"Error running PyInstaller: {e}")
    sys.exit(1)

print(f"\nBuild complete. Executable is in '{DIST_PATH}'.")
