# pylint: disable=missing-function-docstring
"""
Tests that will check if the test_runner is wokring ok
"""

import os
import pytest
from _pytest.outcomes import Failed

from test_runner import (
    parse_test_file,
    read_directory,
    check_exp_given,
    read_test_exceptions,
    check_partial_word,
    parse_custom_classpath,
    parse_case_sensitive,
    parse_stdout,
    parse_stderr,
)
import conftest as external_vars


@pytest.mark.tester
def test_check_partial_word():
    """
    Test whether checking a partial word works correctly
    """

    expected = "1.111111111***1111111111"
    assert not check_partial_word("", expected)
    assert not check_partial_word("1", expected)
    assert not check_partial_word("1.", expected)
    assert not check_partial_word("1.1", expected)
    assert not check_partial_word("1.11", expected)
    assert not check_partial_word("1.111", expected)
    assert not check_partial_word("1.1111", expected)
    assert not check_partial_word("1.11111", expected)
    assert not check_partial_word("1.111111", expected)
    assert not check_partial_word("1.1111111", expected)
    assert not check_partial_word("1.11111111", expected)
    assert check_partial_word("1.111111111", expected)
    assert check_partial_word("1.1111111111", expected)
    assert not check_partial_word("1.1111111112", expected)
    assert check_partial_word("1.11111111111", expected)
    assert check_partial_word("1.111111111111", expected)
    assert check_partial_word("1.1111111111111", expected)
    assert check_partial_word("1.11111111111111", expected)
    assert check_partial_word("1.111111111111111", expected)
    assert not check_partial_word("1.211111111111111", expected)
    assert check_partial_word("1.1111111111111111", expected)
    assert check_partial_word("1.11111111111111111", expected)
    assert check_partial_word("1.111111111111111111", expected)
    assert check_partial_word("1.1111111111111111111", expected)
    assert not check_partial_word("1.11111111111111111111", expected)
    assert not check_partial_word("1.11111111111111111112", expected)


@pytest.mark.tester
def test_parse_file():
    """
    Test that the test_runner can parse a file correctly.
    Expected output should be lower-case
    """

    # EXAMPLE TUPLE
    # 0. test_info_dict["name"],
    # 1. test_info_dict["stdout"],
    # 2. test_info_dict["stderr"],
    # 3. test_info_dict["custom_classpath"],
    # 4. test_info_dict["case_sensitive"],

    soms_for_testing_location = os.path.relpath(
        os.path.dirname(__file__) + "/test_runner_tests/soms_for_testing"
    )

    # Firstly assign what is expected from parsing som_test_1.som
    exp_stdout = ["1", "2", "3", "4", "5", "...", "10"]
    exp_stderr = ["this is an error", "...", "hello, world"]
    custom_classpath = None
    case_sensitive = False

    # Parse test and assert values are as above
    result_tuple = parse_test_file(soms_for_testing_location + "/som_test_1.som")
    assert result_tuple[1] == exp_stdout
    assert result_tuple[2] == exp_stderr
    assert result_tuple[3] is custom_classpath
    assert result_tuple[4] is case_sensitive

    # Firstly assign what is expected from parsing som_test_2.som
    exp_stdout = ["I AM cAsE sensitiVe", "...", "Dots/inTest"]
    exp_stderr = ["CaSE sensitive ErrOr", "...", "TestCaseSensitivity"]
    custom_classpath = None
    case_sensitive = True

    # Parse test and assert values are as above
    result_tuple = parse_test_file(soms_for_testing_location + "/som_test_2.som")
    assert result_tuple[1] == exp_stdout
    assert result_tuple[2] == exp_stderr
    assert result_tuple[3] is custom_classpath
    assert result_tuple[4] is case_sensitive

    # Firstly assign what is expected from parsing som_test_3.som
    exp_stdout = ["..."]
    exp_stderr = ["..."]
    custom_classpath = "core-lib/AreWeFastYet/Core"
    case_sensitive = False

    # Parse test and assert values are as above
    result_tuple = parse_test_file(soms_for_testing_location + "/som_test_3.som")
    assert result_tuple[1] == exp_stdout
    assert result_tuple[2] == exp_stderr
    assert result_tuple[3] == custom_classpath
    assert result_tuple[4] is case_sensitive

    # Now test the ability to parse a test file which contains a
    # @tag classpath object som_test_4.som
    custom_classpath = "core-lib/AreWeFastYet/Core:experiments/Classpath:anotherOne"
    os.environ["AWFYtest"] = "core-lib/AreWeFastYet/Core"
    os.environ["experimental"] = "experiments/Classpath"
    os.environ["oneWord"] = "anotherOne"

    result_tuple = parse_test_file(soms_for_testing_location + "/som_test_4.som")
    assert result_tuple[1] == exp_stdout
    assert result_tuple[2] == exp_stderr
    assert result_tuple[3] == custom_classpath
    assert result_tuple[4] is case_sensitive

    # Now test the ability to interleave regular classpaths
    custom_classpath = "one/the/outside:core-lib/AreWeFastYet/Core:then/another/one"
    result_tuple = parse_test_file(soms_for_testing_location + "/som_test_5.som")
    assert result_tuple[1] == exp_stdout
    assert result_tuple[2] == exp_stderr
    assert result_tuple[3] == custom_classpath
    assert result_tuple[4] is case_sensitive

    # Now assert a failure on a classpath envvar that hasnt been set
    with pytest.raises(Failed, match=r"Environment variable IDontExist not set"):
        parse_test_file(soms_for_testing_location + "/som_test_6.som")


@pytest.mark.tester
def test_test_discovery():
    """
    Test the som test discovery methods in the test_runner_tests directory
    Three tests should be located, Update this method if more tests are added
    """
    # Locate all SOM tests
    test_runner_tests_location = os.path.relpath(
        os.path.dirname(__file__) + "/test_runner_tests"
    )
    tests = []
    read_directory(test_runner_tests_location, tests)
    tests = sorted(tests)

    # If a new tests is added to soms_for_testing then please add it here
    expected_tests = [
        f"{str(test_runner_tests_location)}/soms_for_testing/som_test_1.som",
        f"{str(test_runner_tests_location)}/soms_for_testing/som_test_2.som",
        f"{str(test_runner_tests_location)}/soms_for_testing/som_test_3.som",
        f"{str(test_runner_tests_location)}/soms_for_testing/som_test_4.som",
        f"{str(test_runner_tests_location)}/soms_for_testing/som_test_5.som",
        f"{str(test_runner_tests_location)}/soms_for_testing/som_test_6.som",
    ]

    assert tests == expected_tests


@pytest.mark.tester
def test_check_output():
    """
    Test that the check_output function complies with the expected output.
    """

    stdout = "Hello World\nSome other output in the Middle\nThis is a test\n"

    expected_stdout = ["hello world", "...", "this is a test"]

    # For checking case sensitivity all are converted to lower at differnt parts of the program
    # This just simulates that. It is very difficult to actually run this

    # Check case sensitive
    assert check_exp_given(stdout.split("\n"), expected_stdout) == 0

    # Check case insensitive
    assert check_exp_given(stdout.lower().split("\n"), expected_stdout) == 1

    # Check large output file with ... used inline at beginning and at end
    stdout = """This is SOM++
Hello Rhys this is some sample output
1\n2\n3\n4\n4\n56\n6\n7\n7\n8\n9\n9
1010101\n10101\n1010101
1010101010101010100101010101010010101
Rhys Walker
Moving on
Extra text
more Numbers
NUMBER NUMBER NUMBER NUMBER
"""
    expected_stdout = [
        "Hello ... this is ... sample output",
        "Rhys Walker",
        "... on",
        "more ...",
        "... NUMBER ... NUMBER",
    ]

    assert check_exp_given(stdout.split("\n"), expected_stdout) == 1

    stdout = """This is SOM++
Hello, this is some sample output
There is some more on this line
And a little more here
"""
    expected_stdout = [
        "Hello, ... sample ...",
        "... is ... this line",
        "... little ...",
    ]

    assert check_exp_given(stdout.split("\n"), expected_stdout) == 1

    expected = ["...", "Really***LongWord"]

    stdout = "Some output, as an example\nExtra Line\nReallyLongWord"
    assert check_exp_given(stdout.split("\n"), expected)

    stdout = "Some output, as an example\nExtra Line\nReally"
    assert check_exp_given(stdout.split("\n"), expected)

    stdout = "Some output, as an example\nExtra Line\nReallyLong"
    assert check_exp_given(stdout.split("\n"), expected)

    stdout = "Some output, as an example\nExtra Line\nReallyLo"
    assert check_exp_given(stdout.split("\n"), expected)

    # Now assert some failures to test when it should fail
    stdout = "Some output, as an example\nExtra Line\nReallyLongTestFunction"
    assert not check_exp_given(stdout.split("\n"), expected)

    # This one should fail as there is still more word than expected
    stdout = "Some output, as an example\nExtra Line\nReallyLongWordExtra"
    assert not check_exp_given(stdout.split("\n"), expected)


@pytest.mark.tester
def test_different_yaml():
    """
    Test different yaml files which may be missing some information
    Or be malformed
    """

    # First, save the variables that will change in external_vars
    temp_known = external_vars.known_failures
    temp_unspecified = external_vars.failing_as_unspecified
    temp_unsupported = external_vars.unsupported
    temp_do_not_run = external_vars.do_not_run

    yaml_for_testing_location = os.path.relpath(
        os.path.dirname(__file__) + "/test_runner_tests/yaml_for_testing"
    )
    full_path_from_cwd = os.path.relpath(os.path.dirname(__file__))
    if full_path_from_cwd == ".":
        full_path_from_cwd = ""

    # Read a yaml file with nothing after tag (Should all be empty lists)
    read_test_exceptions(yaml_for_testing_location + "/missing_known_declaration.yaml")
    assert external_vars.known_failures == []
    assert external_vars.failing_as_unspecified == []
    assert external_vars.unsupported == []
    assert external_vars.do_not_run == []

    # Read a yaml file with null after each tag (Should all be [])
    read_test_exceptions(yaml_for_testing_location + "/set_to_be_null.yaml")
    assert external_vars.known_failures == []
    assert external_vars.failing_as_unspecified == []
    assert external_vars.unsupported == []
    assert external_vars.do_not_run == []

    # Read a yaml file where the yamlFile object will evaluate to None type (Should be all [])
    read_test_exceptions(yaml_for_testing_location + "/missing_all_tags.yaml")
    assert external_vars.known_failures == []
    assert external_vars.failing_as_unspecified == []
    assert external_vars.unsupported == []
    assert external_vars.do_not_run == []

    # Read a yaml file where each tag has one test included
    # [core-lib/IntegrationTests/Tests/mutate_superclass_method/test.som]
    read_test_exceptions(yaml_for_testing_location + "/tests_in_each.yaml")
    test_list = [f"{str(full_path_from_cwd)}Tests/mutate_superclass_method/test.som"]
    assert external_vars.known_failures == test_list
    assert external_vars.failing_as_unspecified == test_list
    assert external_vars.unsupported == test_list
    assert external_vars.do_not_run == test_list

    # Reset external vars after test
    external_vars.known_failures = temp_known
    external_vars.failing_as_unspecified = temp_unspecified
    external_vars.unsupported = temp_unsupported
    external_vars.do_not_run = temp_do_not_run


# ######################################### #
# ALL TEST BELOW HERE SHARE THESE COMMENTS  #
# ######################################### #

COMMENT_TESTERS = """
VM:
    status: success
    case_sensitive: True
    custom_classpath: @custom_1:./some/other/one:@custom_2
    stdout:
        Some random output
        ... some other output
        even more output ...
        ...
        the last bit std
    stderr:
        Some random error
        ... some other error
        even more error ...
        ...
        the last bit of error
"""

# Causes fail on parse_custom_classpath
# False in case_sensitive
COMMENT_TESTERS_2 = """
VM:
    status: success
    case_sensitive: False
    custom_classpath: @no_exist_1:./some/other/one:@no_exist_2
    stdout:
        ...
    stderr:
        ...
"""


@pytest.mark.tester
def test_custom_classpath():
    """
    Test parsing a custom_classpath
    """
    os.environ["custom_1"] = "classpath_1"
    os.environ["custom_2"] = "classpath_2"

    expected = "classpath_1:./some/other/one:classpath_2"

    assert expected == parse_custom_classpath(COMMENT_TESTERS)

    # Now assert a failure on a classpath envvar that hasnt been set
    with pytest.raises(Failed, match=r"Environment variable no_exist_1 not set"):
        parse_custom_classpath(COMMENT_TESTERS_2)

    os.environ["no_exist_1"] = "exists_1"

    # Now assert we fail on the second
    with pytest.raises(Failed, match=r"Environment variable no_exist_2 not set"):
        parse_custom_classpath(COMMENT_TESTERS_2)

    os.environ["no_exist_2"] = "exists_2"

    # Now we should pass
    expected = "exists_1:./some/other/one:exists_2"
    assert expected == parse_custom_classpath(COMMENT_TESTERS_2)


@pytest.mark.tester
def test_case_sensitive():
    """
    Test that parsing case_sensitive generates the correct values
    """
    assert parse_case_sensitive(COMMENT_TESTERS)
    assert not parse_case_sensitive(COMMENT_TESTERS_2)


# THESE BELOW MUST BE DIFFERENT EVEN THOUGH THE FUNCTIONS DO ESSENTIALLY THE SAME THING


@pytest.mark.tester
def test_parse_stdout():
    """
    Check that parsing the test comment generates the correct output
    """
    comment_testers_expected_1 = [
        "Some random output",
        "... some other output",
        "even more output ...",
        "...",
        "the last bit std",
    ]
    comment_testers_expected_2 = ["..."]

    assert comment_testers_expected_1 == parse_stdout(COMMENT_TESTERS)
    assert comment_testers_expected_2 == parse_stdout(COMMENT_TESTERS_2)


@pytest.mark.tester
def test_parse_stderr():
    """
    Check that parsing the test comment generates the correct output
    """
    comment_testers_expected_1 = [
        "Some random error",
        "... some other error",
        "even more error ...",
        "...",
        "the last bit of error",
    ]
    comment_testers_expected_2 = ["..."]

    assert comment_testers_expected_1 == parse_stderr(COMMENT_TESTERS)
    assert comment_testers_expected_2 == parse_stderr(COMMENT_TESTERS_2)
