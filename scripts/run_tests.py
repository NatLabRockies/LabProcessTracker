import sys
import os
import pytest

def main():
    python_version = sys.version_info
    print(
        f"Running tests with Python "
        f"{python_version.major}.{python_version.minor}.{python_version.micro}"
    )
    print("-" * 60)

    # Get project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    tests_dir = os.path.join(project_root, 'tests')
    src_dir = os.path.join(project_root, 'src')

    # Add src to Python path for imports
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

    # Run pytest with verbose output and coverage
    exit_code = pytest.main([
        tests_dir,
        '-v',
        '--tb=short',
        '--cov=src',
        '--cov-report=term-missing',
        '--cov-report=html',
    ])

    if exit_code == 0:
        print("\n" + "=" * 60)
        print("All tests passed successfully!")
        print(
            f"Coverage report generated in: "
            f"{os.path.join(project_root, 'htmlcov', 'index.html')}"
        )
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("Some tests failed. Please review the output above.")
        print("=" * 60)

    sys.exit(exit_code)

if __name__ == "__main__":
    main()
