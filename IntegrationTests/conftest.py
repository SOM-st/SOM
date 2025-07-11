"""
Defines variables that are required for a report to be generated.
"""

import yaml

# Report Generate Logic
tests_failed_unexpectedly = []
tests_passed_unexpectedly = []
tests_passed = 0  # pylint: disable=invalid-name
tests_failed = 0  # pylint: disable=invalid-name
total_tests = 0  # pylint: disable=invalid-name
tests_skipped = 0  # pylint: disable=invalid-name

# Lists containing references to each exception test
known_failures = []
failing_as_unspecified = []
unsupported = []
do_not_run = []

# Environment variables
CLASSPATH = ""
EXECUTABLE = ""
TEST_EXCEPTIONS = ""
GENERATE_REPORT = ""


# Log data
def pytest_runtest_logreport(report):
    """
    Increment the counters for what action was performed
    """
    # Global required here to access counters
    # Not ideal but without the counters wouldn't work
    global total_tests, tests_passed, tests_failed, tests_skipped  # pylint: disable=global-statement
    if report.when == "call":  # only count test function execution, not setup/teardown
        total_tests += 1
        if report.passed:
            tests_passed += 1
        elif report.failed:
            tests_failed += 1
        elif report.skipped:
            tests_skipped += 1


# Run after all tests completed, Generate a report of failing and passing tests
def pytest_sessionfinish(exitstatus):
    """
    Generate report based on test run
    """
    if GENERATE_REPORT:
        # To make the report useful it will add the tests which have failed-
        # -unexpectedly to known_failures
        # It will also remove those that have passed from any of those lists

        for test_path in tests_passed_unexpectedly:
            test = str(test_path)
            if test in known_failures:
                known_failures.remove(test)
            if test in unsupported:
                unsupported.remove(test)
            if test in failing_as_unspecified:
                failing_as_unspecified.remove(test)

        if len(tests_failed_unexpectedly) != 0:
            for test in tests_failed_unexpectedly:
                known_failures.append(str(test))

        # Generate a report_message to save
        report_data = {
            "summary": {
                "tests_total": total_tests,
                "tests_passed": tests_passed,
                "tests_failed": tests_failed,
                "tests_skipped": tests_skipped,
                "pytest_exitstatus": exitstatus,
                "note": "Totals include expected failures",
            },
            "unexpected": {
                "passed": [str(test) for test in tests_passed_unexpectedly],
                "failed": [str(test) for test in tests_failed_unexpectedly],
            },
            "environment": {
                "executable": EXECUTABLE,
                "classpath": CLASSPATH,
                "test_exceptions": TEST_EXCEPTIONS,
                "generate_report_location": GENERATE_REPORT,
            },
            "known_failures": known_failures,
            "failing_as_unspecified": failing_as_unspecified,
            "unsupported": unsupported,
            "do_not_run": do_not_run,
        }
        with open(f"{GENERATE_REPORT}", "w", encoding="utf-8") as f:
            yaml.dump(report_data, f, default_flow_style=False, sort_keys=False)
