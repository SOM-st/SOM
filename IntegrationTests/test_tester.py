# pylint: disable=missing-function-docstring,redefined-outer-name
"""
Tests for the tester functionality itself.
"""

import os
import pytest

from test_runner import (
    parse_test_file,
    discover_test_files,
    check_output_matches,
    read_test_exceptions,
    check_partial_word,
    parse_custom_classpath,
    parse_case_sensitive,
    parse_stdout,
    parse_stderr,
    ParseError,
)
import conftest as external_vars


@pytest.mark.parametrize(
    "word",
    [
        "1.111111111",
        "1.1111111111",
        "1.11111111111",
        "1.1111111111111",
        "1.11111111111111",
        "1.111111111111111",
        "1.1111111111111111",
        "1.11111111111111111",
        "1.111111111111111111",
        "1.1111111111111111111",
    ],
)
@pytest.mark.tester
def test_check_partial_word_matches(word):
    assert check_partial_word(word, "1.111111111***1111111111")


@pytest.mark.parametrize(
    "word",
    [
        "",
        "1",
        "1.",
        "1.1",
        "1.11",
        "1.111",
        "1.1111",
        "1.11111",
        "1.111111",
        "1.1111111",
        "1.11111111",
        "1.1111111112",
        "1.211111111111111",
        "1.11111111111111111111",
        "1.11111111111111111112",
    ],
)
@pytest.mark.tester
def test_check_partial_word_does_not_match(word):
    assert not check_partial_word(word, "1.111111111***1111111111")


@pytest.fixture
def soms_for_testing_location():
    return os.path.relpath(
        os.path.dirname(__file__) + "/test_runner_tests/soms_for_testing"
    )


@pytest.mark.parametrize(
    "test_file, exp_stdout, exp_stderr, custom_classpath, case_sensitive",
    [
        (
            "/som_test_1.som",
            ["1", "2", "3", "4", "5", "...", "10"],
            ["this is an error", "...", "hello, world"],
            None,
            False,
        ),
        (
            "/som_test_2.som",
            ["I AM cAsE sensitiVe", "...", "Dots/inTest"],
            ["CaSE sensitive ErrOr", "...", "TestCaseSensitivity"],
            None,
            True,
        ),
        ("/som_test_3.som", ["..."], ["..."], "core-lib/AreWeFastYet/Core", False),
    ],
)
@pytest.mark.tester
def test_parse_file(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    test_file,
    exp_stdout,
    exp_stderr,
    custom_classpath,
    case_sensitive,
    soms_for_testing_location,
):
    result = parse_test_file(soms_for_testing_location + test_file)
    assert result.stdout == exp_stdout
    assert result.stderr == exp_stderr
    assert result.custom_classpath == custom_classpath
    assert result.case_sensitive is case_sensitive


@pytest.mark.tester
def test_parse_file_correctly_using_envvars(soms_for_testing_location):
    custom_classpath = "core-lib/AreWeFastYet/Core:experiments/Classpath:anotherOne"
    os.environ["AWFYtest"] = "core-lib/AreWeFastYet/Core"
    os.environ["experimental"] = "experiments/Classpath"
    os.environ["oneWord"] = "anotherOne"

    result = parse_test_file(soms_for_testing_location + "/som_test_4.som")
    assert result.custom_classpath == custom_classpath

    # Now test the ability to interleave regular classpaths
    custom_classpath = "one/the/outside:core-lib/AreWeFastYet/Core:then/another/one"
    result = parse_test_file(soms_for_testing_location + "/som_test_5.som")
    assert result.custom_classpath == custom_classpath


@pytest.mark.tester
def test_parse_file_failing_because_of_envvar_not_being_set(soms_for_testing_location):
    result = parse_test_file(soms_for_testing_location + "/som_test_6.som")
    assert result.definition_fail_msg == "Environment variable IDontExist not set"


@pytest.mark.tester
def test_discover_test_files():
    test_runner_tests_location = os.path.relpath(
        os.path.dirname(__file__) + "/test_runner_tests"
    )
    tests = []
    discover_test_files(test_runner_tests_location, tests)
    tests = sorted(tests)

    expected_tests = [
        f"{test_runner_tests_location}/soms_for_testing/som_test_{i}.som"
        # add missing tests here, or make the test independent of the actual test files
        for i in range(1, 7)
    ]

    assert tests == expected_tests


@pytest.mark.parametrize(
    "out, expected",
    [
        (
            "Hello World\nSome other output in the Middle\nThis is a test\n".lower(),
            ["hello world", "...", "this is a test"],
        ),
        (
            """This is SOM++
Hello Rhys this is some sample output
1\n2\n3\n4\n4\n56\n6\n7\n7\n8\n9\n9
1010101\n10101\n1010101
1010101010101010100101010101010010101
Rhys Walker
Moving on
Extra text
more Numbers
NUMBER NUMBER NUMBER NUMBER
""",
            [
                "Hello ... this is ... sample output",
                "Rhys Walker",
                "... on",
                "more ...",
                "... NUMBER ... NUMBER",
            ],
        ),
        (
            """This is SOM++
Hello, this is some sample output
There is some more on this line
And a little more here
""",
            [
                "Hello, ... sample ...",
                "... is ... this line",
                "... little ...",
            ],
        ),
        (
            "Some output, as an example\nExtra Line\nReallyLongWord",
            ["...", "Really***LongWord"],
        ),
        (
            "Some output, as an example\nExtra Line\nReally",
            ["...", "Really***LongWord"],
        ),
        (
            "Some output, as an example\nExtra Line\nReallyLong",
            ["...", "Really***LongWord"],
        ),
        (
            "Some output, as an example\nExtra Line\nReallyLo",
            ["...", "Really***LongWord"],
        ),
    ],
)
@pytest.mark.tester
def test_check_output_matches(out, expected):
    assert check_output_matches(out.split("\n"), expected)


@pytest.mark.parametrize(
    "out, expected",
    [
        (
            "Hello World\nSome other output in the Middle\nThis is a test\n",
            ["hello world", "...", "this is a test"],
        ),
        (
            "Some output, as an example\nExtra Line\nReallyLongTestFunction",
            ["...", "Really***LongWord"],
        ),
        (
            "Some output, as an example\nExtra Line\nReallyLongWordExtra",
            ["...", "Really***LongWord"],
        ),
    ],
)
@pytest.mark.tester
def test_check_output_does_not_match(out, expected):
    assert not check_output_matches(out.split("\n"), expected)


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
    with pytest.raises(ParseError, match=r"Environment variable no_exist_1 not set"):
        parse_custom_classpath(COMMENT_TESTERS_2)

    os.environ["no_exist_1"] = "exists_1"

    # Now assert we fail on the second
    with pytest.raises(ParseError, match=r"Environment variable no_exist_2 not set"):
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
