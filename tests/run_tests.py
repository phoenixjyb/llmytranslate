#!/usr/bin/env python3
"""
Test Runner for LLM Translation Service

This script provides a comprehensive test runner that can execute
different categories of tests with proper reporting.

Usage:
    python run_tests.py --unit           # Run unit tests only
    python run_tests.py --integration    # Run integration tests only
    python run_tests.py --examples       # Run example/demo tests
    python run_tests.py --all            # Run all tests
    python run_tests.py --coverage       # Run with coverage report
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

def get_python_executable():
    """Get the appropriate Python executable."""
    # Try virtual environment first
    venv_paths = [
        ".venv/Scripts/python.exe",  # Windows
        ".venv/bin/python",          # Unix
        "venv/Scripts/python.exe",   # Alternative Windows
        "venv/bin/python"            # Alternative Unix
    ]
    
    for venv_path in venv_paths:
        abs_path = os.path.abspath(venv_path)
        if os.path.exists(abs_path):
            return abs_path
    
    # Fallback to system python
    return sys.executable

def run_command(command, description):
    """Run a command and return success status."""
    print(f"\n🔄 {description}")
    print("=" * 50)
    
    # Use the appropriate Python executable
    python_exe = get_python_executable()
    command = command.replace("python ", f'"{python_exe}" ')
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(f"Warnings: {result.stderr}")
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Error: {e.stderr}")
        return False

def run_unit_tests():
    """Run unit tests."""
    return run_command(
        "python -m pytest tests/unit/ -v --tb=short",
        "Running Unit Tests"
    )

def run_integration_tests():
    """Run integration tests."""
    return run_command(
        "python -m pytest tests/integration/ -v --tb=short",
        "Running Integration Tests"
    )

def run_example_tests():
    """Run example/demo tests."""
    print("\n🔄 Running Example Tests")
    print("=" * 50)
    
    python_exe = get_python_executable()
    success = True
    example_files = [
        "tests/examples/simple_test.py",
        "tests/examples/quick_test.py",
        "tests/examples/final_test.py",
        "tests/examples/validate.py"
    ]
    
    for test_file in example_files:
        if os.path.exists(test_file):
            print(f"\n▶️  Running {test_file}")
            try:
                result = subprocess.run(f'"{python_exe}" {test_file}', shell=True, check=True, capture_output=True, text=True)
                print(result.stdout)
                print(f"✅ {test_file} completed")
            except subprocess.CalledProcessError as e:
                print(f"❌ {test_file} failed: {e.stderr}")
                success = False
        else:
            print(f"⚠️  {test_file} not found")
    
    return success

def run_with_coverage():
    """Run all tests with coverage reporting."""
    return run_command(
        "python -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing -v",
        "Running All Tests with Coverage"
    )

def run_linting():
    """Run code quality checks."""
    success = True
    
    # Run flake8
    success &= run_command(
        "python -m flake8 src/ tests/ --max-line-length=100 --extend-ignore=E203,W503",
        "Running Code Style Check (flake8)"
    )
    
    # Run mypy (if available)
    try:
        subprocess.run("python -m mypy --version", shell=True, check=True, capture_output=True)
        success &= run_command(
            "python -m mypy src/ --ignore-missing-imports",
            "Running Type Check (mypy)"
        )
    except subprocess.CalledProcessError:
        print("ℹ️  mypy not available, skipping type checking")
    
    return success

def main():
    parser = argparse.ArgumentParser(description="Run tests for LLM Translation Service")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--examples", action="store_true", help="Run example tests only")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage report")
    parser.add_argument("--lint", action="store_true", help="Run code quality checks")
    parser.add_argument("--install-deps", action="store_true", help="Install test dependencies")
    
    args = parser.parse_args()
    
    # Change to project root directory
    os.chdir(Path(__file__).parent)
    
    if args.install_deps:
        print("📦 Installing test dependencies...")
        subprocess.run("pip install pytest pytest-cov pytest-asyncio flake8 mypy", shell=True)
        return
    
    print("🧪 LLM Translation Service Test Runner")
    print("=====================================")
    
    success = True
    
    if args.unit:
        success &= run_unit_tests()
    elif args.integration:
        success &= run_integration_tests()
    elif args.examples:
        success &= run_example_tests()
    elif args.coverage:
        success &= run_with_coverage()
    elif args.lint:
        success &= run_linting()
    elif args.all:
        success &= run_unit_tests()
        success &= run_integration_tests()
        success &= run_example_tests()
        success &= run_linting()
    else:
        # Default: run unit and integration tests
        success &= run_unit_tests()
        success &= run_integration_tests()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
