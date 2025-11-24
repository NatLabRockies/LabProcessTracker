import PyInstaller.__main__
import os
import sys
import shutil
import tomllib

def get_version():
    """Get version from pyproject.toml or use default."""
    try:
        pyproject_path = os.path.join(os.path.dirname(__file__), '..', 'pyproject.toml')
        with open(pyproject_path, 'rb') as f:
            data = tomllib.load(f)
            return data['project']['version']
    except:
        return "0.1.0"

def build_exe():
    """Build executable for the process tracker GUI."""
    version = get_version()

    # Get project root and paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    src_dir = os.path.join(project_root, 'src')
    exe_dir = os.path.join(project_root, 'exe')

    # Clean previous builds
    build_dir = os.path.join(project_root, 'build')
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)

    print(f"Building Process Tracker GUI v{version}")
    print("-" * 60)

    script_name = 'process_tracker_gui.py'
    exe_name = f'process_tracker_gui_v{version}.exe'

    print(f"\nBuilding GUI executable...")

    script_path = os.path.join(src_dir, script_name)

    # PyInstaller arguments
    args = [
        script_path,
        '--onefile',
        '--name', exe_name.replace('.exe', ''),
        '--distpath', os.path.join(exe_dir, 'dist'),
        '--workpath', os.path.join(exe_dir, 'build'),
        '--specpath', os.path.join(exe_dir, 'spec'),
        '--clean',
        '--add-data', f'{os.path.join(project_root, "tools_processes.json")}{os.pathsep}.',
        '--windowed',
        '--noconsole',
    ]

    # Add icon if available
    icon_path = os.path.join(project_root, 'assets', 'icon.ico')
    if os.path.exists(icon_path):
        args.extend(['--icon', icon_path])

    # Run PyInstaller
    try:
        PyInstaller.__main__.run(args)

        # Rename the output file to include version
        output_path = os.path.join(exe_dir, 'dist', exe_name.replace('.exe', '') + '.exe')
        final_path = os.path.join(exe_dir, 'dist', exe_name)

        if os.path.exists(output_path) and output_path != final_path:
            if os.path.exists(final_path):
                os.remove(final_path)
            os.rename(output_path, final_path)

        print(f"✓ GUI executable created: {final_path}")

    except Exception as e:
        print(f"✗ Error building GUI executable: {e}")
        return False

    print("\n" + "=" * 60)
    print("Build completed successfully!")
    print(f"Executable is in: {os.path.join(exe_dir, 'dist')}")
    print("=" * 60)

    return True

if __name__ == "__main__":
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("Error: PyInstaller is not installed.")
        print("Install it with: pip install .[build]")
        sys.exit(1)

    success = build_exe()
    sys.exit(0 if success else 1)
