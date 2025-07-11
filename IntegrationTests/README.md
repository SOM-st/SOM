# SOM Integration Tests

Most of the tests for the integration testing come from lang_tests of [yksom](https://github.com/softdevteam/yksom/tree/master/lang_tests). Tests are identified by their path from core-lib to test.som, this ensures there can be multiple tests named test.som in different directories. Different directories should only be used when necessary for subclass testing.

## Running the Integration Tests
The tests can be run using pytest by simply running pytest in the base directory of any SOM implementation that includes a version of the core-library with IntegrationTests. It requires multiple python modules installed and environment variables set.

### Simple Test Run
```
EXECUTABLE=./path-to-build CLASSPATH=./core-lib/Smalltalk pytest
```

## Prerequisites
The integration tests require two python modules to be installed:


## Environment variables
The environment variables are split into required and optional. Some optionals may be required for different implementations of SOM.

#### EXECUTABLE
This is the path from the current working directory to the executable of SOM.
#### CLASSPATH
The exact classpath required by SOM to find the Object class etc.
#### TEST_EXCEPTIONS
A yaml file which details the tags of tests. Specifically it labels tests that are expected to fail for one reason or another.
#### GENERATE_REPORT
Generates a yaml file which can be used as a **TEST_EXCEPTIONS** file. It will also include additional information about how many tests passed, which tests passed that were not expected to and which tests failed.
#### DEBUG
Allows the printing of detailed run information. Shows currently running test and the configuration before all tests are ran. Must run pytest with the -s flag when using DEBUG.

## TEST_EXCEPTIONS (How to write a file)
There are four tags that are currently supported by the SOM integration tests. All tags will run the tests still, other than do_not_run, but will not fail on test failure, a tagged test will cause the run to fail only when it passes unexpectedly. Check for example file IntegrationTests/test_tags.yaml.

For a test to be given that tag specify it's location path like this:
```
core-lib/IntegrationTests/Tests/test.som
```

### known_failures
Any test located in this tag is assumed to fail, it should only be used when another more suitable tag is not available.

### failing_as_unspecified
Any test located in this tag failed because SOM does not specify behaviour in this instance, this means that each implementation may treat this situation differently. *Example dividing by 0.*

### unsupported
Any test located here has a feature which is not suppoprted in this SOM.

### do_not_run
This test should not be ran ever as it causes an error in the python level code. The test may also cause a SOM level error but does not have to. For example invalid UTF-8 characters inside of a test.

## How to write a new test
For a test to be collected by Pytest it has to start with a comment, the comment should be structured with the expected output for either stderr or stdout.

```
"
VM:
    status: error
    custom_classpath: ./core-lib/Examples/AreWeFastYet/Core:./core-lib/Smalltalk
    case_sensitive: False
    stdout:
        1000
        ...
        2 is an integer
    stderr:
        ...
        ERROR MESSAGE
"
```

**When structuring a test all options must come before stderr and stdout**

### Tags for structuring a test
Below is a list of tags which structure how a test works.

#### VM: 
This is required as the base of the test structure and what allows the tests to be identified as an integration test.

#### custom_classpath: 
This allows for the specification of a custom classpath to be used. This is useful for loading different versions of classes with the same name. I.e. AWFY Vector instead of core-lib Vector. **The path to ./Smalltalk must still be specified after so that the Object class can be loaded**

#### case_sensitive
By default the tests are case insensitive (All outputs and expecteds are converted to be lower case) but by specifying True in case_sensitive that test can be checked as case_sensitive.

#### stderr or stdout:
This is your expected output, each new line will be a new "thing" to check for. So each line is checked as a whole order is not checked. Writing ... will be ignored by the checker.

Due to the differences between SOM implementations not all will output to stderr for errors, some SOMs will output errors to stdout instead. Thus the **expected outputs are checked against both stderr or stdout**.

### Good test practice
To make it clear to others how the test works please follow these guidelines.

- Any error regardless of where it is output (stderr/stdout) should be under stderr to make it clear.
- Expected outputs should be written in the order they are being expected regardless of the lack of order checking.
- Use ... to show a break in output checking.