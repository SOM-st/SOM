# pylint: disable=missing-function-docstring, missing-class-docstring, too-many-arguments, too-many-positional-arguments, too-few-public-methods
"""
This is the SOM integration test runner file. Pytest automatically discovers
this file and will find all .som test files in the below directories.
"""

import subprocess
from pathlib import Path
from difflib import ndiff
import os
import pytest
import yaml
import conftest as external_vars


class Definition:
    def __init__(
        self,
        name: str,
        stdout: list[str],
        stderr: list[str],
        custom_classpath: str | None,
        case_sensitive: bool,
        definition_fail_msg: str | None = None,
    ):
        self.name = name
        self.stdout = stdout
        self.stderr = stderr
        self.custom_classpath = custom_classpath
        self.case_sensitive = case_sensitive
        self.definition_fail_msg = definition_fail_msg


class ParseError(Exception):
    """
    Exception raised when a test file cannot be parsed correctly.
    This is used to fail the test in the test runner.
    """

    def __init__(self, message):
        super().__init__(message)
        self.message = message


def is_som_test(path):
    if path.suffix == ".som":
        with open(path, "r", encoding="utf-8") as f:
            contents = f.read()
            if "VM:" in contents:
                return True
    return False


def discover_test_files(path, test_files):
    """
    Recursively read the directory tree and add all .som test files to `test_files`.
    """
    for element in Path(path).iterdir():
        if element.is_dir():
            discover_test_files(element, test_files)
        elif element.is_file() and is_som_test(element):
            test_files.append(str(element))


def collect_tests(test_files) -> list[Definition]:
    """
    Assemble a dictionary of
    name: the name of the test file
    stdout/stderr: the expected output of the test
    """
    tests = []
    for file_path in test_files:
        test_dict = parse_test_file(file_path)
        if test_dict is None:
            continue
        tests.append(test_dict)

    return tests


# pylint: disable=too-many-nested-blocks
def parse_custom_classpath(comment) -> str | None:
    """
    Based on the comment will calculate the custom_classpath
    for the current test

    Return: The custom classpath
    """
    comment_lines = comment.split("\n")
    for line in comment_lines:
        if "custom_classpath" in line:
            classpath = line.split("custom_classpath:")[1].strip()

            classpath_t = classpath

            # Now check our custom classpath for any tags
            # Tags are defined as @tag in the classpath
            # Will then assign the EXACT value of the
            # Environment variable to that spot

            if classpath_t.find("@") >= 0:

                classpath_joined = ""
                # Does the classpath have a splitter ":"
                if ":" in classpath_t:
                    split_list = classpath_t.split(":")
                    for tag in split_list:
                        if tag.find("@") >= 0:
                            tag = tag.replace("@", "")
                            if tag in os.environ:
                                classpath_joined += os.environ[tag] + ":"
                                continue
                            raise ParseError(f"Environment variable {tag} not set")
                        # Add a normal classpath inside of tags
                        classpath_joined += tag + ":"

                else:
                    classpath_t = classpath_t.replace("@", "")
                    if classpath_t in os.environ:
                        classpath_joined += os.environ[classpath_t]
                    else:
                        raise ParseError(f"Environment variable {classpath_t} not set")

                # Remove the final ":"
                classpath = classpath_joined[:-1]

            return classpath
    return None


def parse_case_sensitive(comment):
    """
    Based on a comment decide whether a case_sensitive is requried
    """
    comment_lines = comment.split("\n")
    for line in comment_lines:
        if "case_sensitive" in line:
            return bool(line.split("case_sensitive:")[1].strip().lower() == "true")

    return False


def parse_stdout(comment):
    """
    Based on a comment parse the expected stdout
    """
    std_out = comment.split("stdout:")[1]
    if "stderr" in std_out:
        std_err_inx = std_out.index("stderr:")
        std_out = std_out[:std_err_inx]
    std_err_l = std_out.split("\n")
    std_err_l = [line.strip() for line in std_err_l if line.strip()]
    return std_err_l


def parse_stderr(comment):
    """
    Based on a comment parse the expected stderr
    """
    std_err = comment.split("stderr:")[1]
    if "stdout" in std_err:
        std_out_inx = std_err.index("stdout:")
        std_err = std_err[:std_out_inx]
    std_err_l = std_err.split("\n")
    std_err_l = [line.strip() for line in std_err_l if line.strip()]
    return std_err_l


def parse_test_file(test_file) -> Definition:
    """
    parse the test file to extract the important information
    """
    name = test_file
    stdout = []
    stderr = []
    custom_classpath = None
    case_sensitive = False

    try:
        with open(test_file, "r", encoding="utf-8") as open_file:
            contents = open_file.read()
            comment = contents.split('"')[1]

            # Make sure if using a custom test classpath that it is above
            # Stdout and Stderr
            if "custom_classpath" in comment:
                custom_classpath = parse_custom_classpath(comment)

            if "case_sensitive" in comment:
                case_sensitive = parse_case_sensitive(comment)

            if "stdout" in comment:
                stdout = parse_stdout(comment)

            if "stderr" in comment:
                stderr = parse_stderr(comment)

            if not case_sensitive:
                stdout = [s.lower() for s in stdout]
                stderr = [s.lower() for s in stderr]
    except ParseError as e:
        return Definition(name, [], [], None, False, e.message)

    return Definition(name, stdout, stderr, custom_classpath, case_sensitive)


def make_a_diff(expected, given):
    """
    Creates a string that represents the difference between two
    lists of Strings.
    """
    diff_string = ""
    for diff in ndiff(expected, given):
        diff_string += f"\n{str(diff)}"

    return diff_string


# pylint: disable=too-many-positional-arguments
# pylint: disable=too-many-arguments
def build_error_message(
    stdout, stderr, exp_stdout, exp_stderr, command, case_sensitive
):
    """
    Build an error message for the test runner
    """

    error_message = f"""\n
Command: {command}
Case Sensitive: {case_sensitive}
    """

    if stdout.strip() != "":
        error_message += "\nstdout diff with stdout expected\n"
        error_message += make_a_diff(exp_stdout, stdout.strip().split("\n"))

    if stderr.strip() != "":
        error_message += "\nstderr diff with stderr expected\n"
        error_message += make_a_diff(exp_stderr, stderr.strip().split("\n"))

    return error_message


def check_partial_word(word, exp_word):
    """
    Check a partial expected String against a line

    returns True if the line matches
    """

    # Creates a list of words that are expected
    exp_word_needed = exp_word.split("***")[0]
    exp_word_optional = exp_word.split("***")[1]

    if exp_word_needed in word:
        where = word.find(exp_word_needed) + len(exp_word_needed)
        counter = 0
        for character in exp_word_optional:

            if counter + where > len(word) - 1:
                return True

            if word[counter + where] == character:
                counter += 1
                continue
            return False
    else:
        return False

    if counter + where < len(word):
        return False

    return True


def check_output_matches(given, expected):
    """
    Check if the expected output is contained in the given output

    given: list of strings representing the actual output
    expected: list of strings representing the expected output
    """
    # Check if the stdout matches the expected stdout
    exp_std_inx = 0
    for g_out in given:
        # Check that checks don't pass before out of outputs
        if exp_std_inx >= len(expected):
            return True

        if expected[exp_std_inx] == "...":
            # If the expected output is '...' then we skip this line
            exp_std_inx += 1
            continue

        # This is incompaptible with ... for line skipping
        if "***" in expected[exp_std_inx]:
            # Now do some partial checking
            partial_output = check_partial_word(g_out, expected[exp_std_inx])
            if partial_output:
                exp_std_inx += 1
            continue

        if g_out.strip() != expected[exp_std_inx].strip():
            # Check if expected has ...
            if "..." in expected[exp_std_inx]:
                # If it does then we need to remove it and check for that line containing string
                without_gap = expected[exp_std_inx].split("...")
                if all(without_gap in g_out for without_gap in without_gap):
                    exp_std_inx += 1
                    continue

            # If the output does not match, continue without incrementing
            continue

        exp_std_inx += 1

    if exp_std_inx != len(expected):
        # It is not all contained in the output
        return False

    return True


def check_output(test_outputs, expected_std_out, expected_std_err):
    """
    check if the output of the test matches the expected output
    test_outputs: The object returned by subprocess.run
    expected_std_out: The expected standard output
    expected_std_err: The expected standard error output
    Returns: Boolean indicating if result matches expected output

    note: This method does not directly error, just checks conditions

    stdout and stderr do not match in all SOMs
    stderr checked against stdout and stderr
    stdout checked against stdout and stderr

    This is relatively robust for most test cases
    """
    given_std_out = test_outputs.stdout.split("\n")
    given_std_err = test_outputs.stderr.split("\n")

    return check_output_matches(
        given_std_out, expected_std_out
    ) and check_output_matches(given_std_err, expected_std_err)


# Read the test exceptions file and set the variables correctly
# pylint: disable=too-many-branches
def read_test_exceptions(filename):
    """
    Read a TEST_EXCEPTIONS file and extract the core information
    Filename should be either a relative path from CWD to file
    or an absolute path.
    """
    if not filename:
        return

    with open(f"{filename}", "r", encoding="utf-8") as file:
        yaml_file = yaml.safe_load(file)

        if yaml_file is not None:
            external_vars.known_failures = yaml_file.get("known_failures", []) or []
            external_vars.failing_as_unspecified = (
                yaml_file.get("failing_as_unspecified", []) or []
            )
            external_vars.unsupported = yaml_file.get("unsupported", []) or []
            external_vars.do_not_run = yaml_file.get("do_not_run", []) or []

            path = os.path.relpath(os.path.dirname(__file__))
            if path == ".":
                path = ""

            external_vars.known_failures = [
                os.path.join(path, test)
                for test in external_vars.known_failures
                if test is not None
            ]
            external_vars.failing_as_unspecified = [
                os.path.join(path, test)
                for test in external_vars.failing_as_unspecified
                if test is not None
            ]
            external_vars.unsupported = [
                os.path.join(path, test)
                for test in external_vars.unsupported
                if test is not None
            ]
            external_vars.do_not_run = [
                os.path.join(path, test)
                for test in external_vars.do_not_run
                if test is not None
            ]


def prepare_tests():
    location = os.path.relpath(os.path.dirname(__file__))
    if not os.path.exists(location + "/Tests"):
        return [
            Definition(
                "test-setup",
                [],
                [],
                None,
                False,
                "`Tests` directory not found. Please make sure the lang_tests are installed",
            )
        ]

    # Work out settings for the application (They are labelled REQUIRED or OPTIONAL)
    if "CLASSPATH" not in os.environ:  # REQUIRED
        return [
            Definition(
                "test-setup",
                [],
                [],
                None,
                False,
                "Please set the CLASSPATH environment variable",
            )
        ]

    if "VM" not in os.environ:  # REQUIRED
        return [
            Definition(
                "test-setup",
                [],
                [],
                None,
                False,
                "Please set the VM environment variable",
            )
        ]

    if "TEST_EXCEPTIONS" in os.environ:  # OPTIONAL
        external_vars.TEST_EXCEPTIONS = os.environ["TEST_EXCEPTIONS"]

    if "GENERATE_REPORT" in os.environ:  # OPTIONAL
        external_vars.GENERATE_REPORT = os.environ["GENERATE_REPORT"]

    external_vars.CLASSPATH = os.environ["CLASSPATH"]
    external_vars.VM = os.environ["VM"]

    read_test_exceptions(external_vars.TEST_EXCEPTIONS)

    test_files = []
    discover_test_files(location + "/Tests", test_files)
    test_files = sorted(test_files)
    return collect_tests(test_files)


def get_test_id(test):
    print(test)
    return "Tests/" + test.name.split("Tests/")[-1]


@pytest.mark.parametrize(
    "test",
    prepare_tests(),
    ids=get_test_id,
)
# pylint: disable=too-many-branches
def tests_runner(test):
    """
    Take an array of dictionaries with test file names and expected output
    Run all of the tests and check the output
    Cleanup the build directory if required
    """

    # Check if a test should not be ran
    if test.name in external_vars.do_not_run:
        pytest.skip("Test included in do_not_run")

    if test.definition_fail_msg:
        pytest.fail(test.definition_fail_msg)

    if test.custom_classpath is not None:
        command = f"{external_vars.VM} -cp {test.custom_classpath} {test.name}"
    else:
        command = f"{external_vars.VM} -cp {external_vars.CLASSPATH} {test.name}"

    try:
        result = subprocess.run(
            command, capture_output=True, text=True, shell=True, check=False
        )
    except UnicodeDecodeError:
        pytest.skip(
            "Test output could not be decoded SOM may not support "
            "full Unicode. Result object not generated."
        )

    # lower-case comparisons unless specified otherwise
    if test.case_sensitive is False:
        result.stdout = str(result.stdout).lower()
        result.stderr = str(result.stderr).lower()

    # Produce potential error messages now and then run assertion
    error_message = build_error_message(
        result.stdout,
        result.stderr,
        test.stdout,
        test.stderr,
        command,
        test.case_sensitive,
    )

    # Related to above line (Rather than change how stdout and stderr are
    # represented just joining and then splitting again)

    if result.returncode != 0:
        error_message += f"Command failed with return code: {result.returncode}\n"

    test_pass_bool = check_output(result, test.stdout, test.stderr)

    # Check if we have any unexpectedly passing tests
    if (
        test.name in external_vars.known_failures and test_pass_bool
    ):  # Test passed when it is not expected to
        external_vars.tests_passed_unexpectedly.append(test.name)
        assert False, f"Test {test.name} is in known_failures but passed"

    if test.name in external_vars.failing_as_unspecified and test_pass_bool:
        # Test passed when it is not expected tp
        external_vars.tests_passed_unexpectedly.append(test.name)
        assert False, f"Test {test.name} is in failing_as_unspecified but passed"

    if test.name in external_vars.unsupported and test_pass_bool:
        # Test passed when it is not expected tp
        external_vars.tests_passed_unexpectedly.append(test.name)
        assert False, f"Test {test.name} is in unsupported but passed"

    if (
        test.name not in external_vars.unsupported
        and test.name not in external_vars.known_failures
        and test.name not in external_vars.failing_as_unspecified
    ):
        if not test_pass_bool:
            external_vars.tests_failed_unexpectedly.append(test.name)
        assert (
            test_pass_bool
        ), f"Error on test, {test.name} expected to pass: {error_message}"
