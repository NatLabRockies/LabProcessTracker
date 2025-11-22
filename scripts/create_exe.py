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

def build_exe(target='both'):
    """Build executable(s) for the process tracker.

    Args:
        target: 'cli', 'gui', or 'both' (default)
    """
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

    print(f"Building Process Tracker v{version}")
    print("-" * 60)

    builds = []
    if target in ['cli', 'both']:
        builds.append(('cli', 'process_tracker.py', f'process_tracker_cli_v{version}.exe'))
    if target in ['gui', 'both']:
        builds.append(('gui', 'process_tracker_gui.py', f'process_tracker_gui_v{version}.exe'))

    for build_type, script_name, exe_name in builds:
        print(f"\nBuilding {build_type.upper()} executable...")

        script_path = os.path.join(src_dir, script_name)

        # Common PyInstaller arguments
        args = [
            script_path,
            '--onefile',
            '--name', exe_name.replace('.exe', ''),
            '--distpath', os.path.join(exe_dir, 'dist'),
            '--workpath', os.path.join(exe_dir, 'build'),
            '--specpath', os.path.join(exe_dir, 'spec'),
            '--clean',
            '--add-data', f'{os.path.join(project_root, "tools_processes.json")}{os.pathsep}.',
        ]

        # GUI-specific arguments
        if build_type == 'gui':
            args.extend([
                '--windowed',  # No console window
                '--noconsole',
            ])

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

            print(f"✓ {build_type.upper()} executable created: {final_path}")

        except Exception as e:
            print(f"✗ Error building {build_type.upper()} executable: {e}")
            return False

    print("\n" + "=" * 60)
    print("Build completed successfully!")
    print(f"Executables are in: {os.path.join(exe_dir, 'dist')}")
    print("=" * 60)

    return True

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build Process Tracker executables")
    parser.add_argument(
        '--target',
        choices=['cli', 'gui', 'both'],
        default='both',
        help="Which executable(s) to build (default: both)"
    )

    args = parser.parse_args()

    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("Error: PyInstaller is not installed.")
        print("Install it with: pip install .[build]")
        sys.exit(1)

    success = build_exe(target=args.target)
    sys.exit(0 if success else 1)
