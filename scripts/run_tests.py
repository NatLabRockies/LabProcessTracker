import sys
import os
import pytest

def main():
    python_version = sys.version_info

    if python_version < (3, 10):
        print("This script requires Python 3.10 or higher.")
        sys.exit(1)

    print(f"Running tests with Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    print("-" * 60)

    # Get project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    tests_dir = os.path.join(project_root, 'tests')

    # Run pytest tests with coverage
    exit_code = pytest.main([
        '-v',
        '--tb=short',
        tests_dir,
        '--cov=src',
        '--cov-report=term-missing',
    ])

    sys.exit(exit_code)

if __name__ == "__main__":
    main()
