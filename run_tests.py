#!/usr/bin/env python3
"""
Test runner script for strands_agent_factory.

This script provides a convenient way to run different test suites
with various options and configurations.
"""

import argparse
import sys
import subprocess
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and handle the result."""
    if description:
        print(f"\n{'='*60}")
        print(f"Running: {description}")
        print(f"Command: {' '.join(cmd)}")
        print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"Command not found: {cmd[0]}")
        print("Make sure pytest is installed: pip install pytest")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Run tests for strands_agent_factory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    # Run all tests
  python run_tests.py --unit             # Run only unit tests
  python run_tests.py --integration      # Run only integration tests
  python run_tests.py --coverage         # Run with coverage report
  python run_tests.py --verbose          # Run with verbose output
  python run_tests.py --fast             # Skip slow tests
  python run_tests.py --file test_config # Run specific test file
        """
    )
    
    # Test selection options
    parser.add_argument(
        "--unit", 
        action="store_true",
        help="Run only unit tests"
    )
    
    parser.add_argument(
        "--integration",
        action="store_true", 
        help="Run only integration tests"
    )
    
    parser.add_argument(
        "--file",
        type=str,
        help="Run specific test file (without .py extension)"
    )
    
    parser.add_argument(
        "--function",
        type=str,
        help="Run specific test function"
    )
    
    # Output options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Quiet output"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run with coverage report"
    )
    
    parser.add_argument(
        "--html-coverage",
        action="store_true",
        help="Generate HTML coverage report"
    )
    
    # Test filtering options
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Skip slow tests"
    )
    
    parser.add_argument(
        "--no-network",
        action="store_true",
        help="Skip tests requiring network access"
    )
    
    parser.add_argument(
        "--no-models",
        action="store_true",
        help="Skip tests requiring actual model access"
    )
    
    # Pytest options
    parser.add_argument(
        "--parallel", "-n",
        type=int,
        help="Run tests in parallel (requires pytest-xdist)"
    )
    
    parser.add_argument(
        "--failfast", "-x",
        action="store_true",
        help="Stop on first failure"
    )
    
    parser.add_argument(
        "--lf",
        action="store_true",
        help="Run last failed tests only"
    )
    
    parser.add_argument(
        "--tb",
        choices=["short", "long", "line", "native", "no"],
        default="short",
        help="Traceback style"
    )
    
    args = parser.parse_args()
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test selection
    if args.unit:
        cmd.extend(["-m", "unit"])
    elif args.integration:
        cmd.extend(["-m", "integration"])
    elif args.file:
        test_file = f"tests/**/test_{args.file}.py"
        cmd.append(test_file)
    elif args.function:
        cmd.extend(["-k", args.function])
    else:
        cmd.append("tests/")
    
    # Add output options
    if args.verbose:
        cmd.append("-v")
    elif args.quiet:
        cmd.append("-q")
    
    # Add coverage options
    if args.coverage or args.html_coverage:
        cmd.extend(["--cov=strands_agent_factory"])
        if args.html_coverage:
            cmd.extend(["--cov-report=html", "--cov-report=term-missing"])
        else:
            cmd.extend(["--cov-report=term-missing"])
    
    # Add filtering options
    if args.fast:
        cmd.extend(["-m", "not slow"])
    
    if args.no_network:
        cmd.extend(["-m", "not requires_network"])
    
    if args.no_models:
        cmd.extend(["-m", "not requires_models"])
    
    # Add pytest options
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])
    
    if args.failfast:
        cmd.append("-x")
    
    if args.lf:
        cmd.append("--lf")
    
    cmd.extend(["--tb", args.tb])
    
    # Run the tests
    success = run_command(cmd, "Running tests")
    
    if success:
        print("\n✅ All tests passed!")
        if args.coverage or args.html_coverage:
            print("\n📊 Coverage report generated")
            if args.html_coverage:
                print("   HTML report: htmlcov/index.html")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()