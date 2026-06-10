import sys
import os
import pytest


def main():
    print(f"Running tests with Python {sys.version.split()[0]}")
    print("-" * 60)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    tests_dir = os.path.join(project_root, 'tests')
    src_dir = os.path.join(project_root, 'src')

    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

    exit_code = pytest.main([
        tests_dir,
        '-v',
        '--tb=short',
        '--cov',
        '--cov-report=term-missing',
        '--cov-report=html',
    ])

    print("\n" + "=" * 60)
    if exit_code == 0:
        print("All tests passed successfully!")
        print(
            f"Coverage report generated in: "
            f"{os.path.join(project_root, 'htmlcov', 'index.html')}"
        )
    else:
        print("Some tests failed. Please review the output above.")
    print("=" * 60)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
