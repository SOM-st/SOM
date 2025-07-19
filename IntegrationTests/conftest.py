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
VM = ""
TEST_EXCEPTIONS = ""
GENERATE_REPORT = ""


def pytest_configure(config):
    """
    Add a marker to pytest
    """
    config.addinivalue_line("markers", "tester: test the testing framework")


def pytest_collection_modifyitems(config, items):
    """
    Make sure the correct tests are being selected for the mode that is running
    """
    # Check if "-m tester" was specified
    marker_expr = config.getoption("-m")
    run_tester_selected = False

    if marker_expr:
        # Simplistic check: if "tester" is anywhere in the -m expression
        # (You can improve parsing if needed)
        run_tester_selected = "tester" in marker_expr.split(" or ")

    if not run_tester_selected:
        deselected = [item for item in items if "tester" in item.keywords]
        if deselected:
            for item in deselected:
                items.remove(item)
            config.hook.pytest_deselected(items=deselected)


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
                # Remove the part of the path that is incompatible with multiple directory running
                known_failures.append(
                    "Tests/" + str(test).rsplit("Tests/", maxsplit=1)[-1]
                )

        # Generate a report_message to save
        report_data = {
            "summary": {
                "tests_total": total_tests,
                "tests_passed": tests_passed,
                "tests_failed": tests_failed,
                "tests_skipped": tests_skipped,
                "pytest_exitstatus": str(exitstatus),
                "note": "Totals include expected failures",
            },
            "unexpected": {
                "passed": [
                    "Tests/" + str(test).rsplit("Tests/", maxsplit=1)[-1]
                    for test in tests_passed_unexpectedly
                ],
                "failed": [
                    "Tests/" + str(test).rsplit("Tests/", maxsplit=1)[-1]
                    for test in tests_failed_unexpectedly
                ],
            },
            "environment": {
                "virtual machine": VM,
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
