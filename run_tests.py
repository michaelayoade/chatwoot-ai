#!/usr/bin/env python
"""
Test runner script for the Langchain-Chatwoot integration.
Runs all tests and generates a coverage report.
"""
import os
import sys
import unittest
import coverage
import argparse

def run_tests_with_coverage(test_pattern="test_*.py", html_report=True):
    """Run tests with coverage reporting."""
    # Start coverage measurement
    cov = coverage.Coverage(
        source=["agents", "langchain_integration.py", "semantic_cache.py", "prometheus_metrics.py"],
        omit=["*/__pycache__/*", "*/tests/*", "*/test_*.py"]
    )
    cov.start()
    
    # Discover and run tests
    loader = unittest.TestLoader()
    
    # First look in the tests directory
    start_dir = os.path.join(os.path.dirname(__file__), "tests")
    if os.path.exists(start_dir):
        suite = loader.discover(start_dir, pattern=test_pattern)
    else:
        # If no tests directory, look in the current directory
        suite = loader.discover(".", pattern=test_pattern)
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Stop coverage measurement and generate report
    cov.stop()
    cov.save()
    
    # Print coverage report to console
    print("\nCoverage Report:")
    cov.report()
    
    # Generate HTML report if requested
    if html_report:
        html_dir = os.path.join(os.path.dirname(__file__), "coverage_html")
        cov.html_report(directory=html_dir)
        print(f"\nHTML coverage report generated in {html_dir}")
    
    return result

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run tests with coverage reporting")
    parser.add_argument(
        "--pattern", 
        default="test_*.py", 
        help="Pattern to match test files (default: test_*.py)"
    )
    parser.add_argument(
        "--no-html", 
        action="store_false", 
        dest="html_report",
        help="Don't generate HTML coverage report"
    )
    return parser.parse_args()

if __name__ == "__main__":
    # Set test mode
    os.environ["TEST_MODE"] = "true"
    os.environ["OPENAI_API_KEY"] = "sk-test-key"
    
    # Parse command line arguments
    args = parse_args()
    
    # Run tests with coverage
    result = run_tests_with_coverage(
        test_pattern=args.pattern,
        html_report=args.html_report
    )
    
    # Exit with appropriate status code
    sys.exit(not result.wasSuccessful())
