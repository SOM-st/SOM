# SOM Integration Tests

Most of the tests for the integration testing come from lang_tests of [yksom](https://github.com/softdevteam/yksom/tree/master/lang_tests). Tests are identified by their path from core-lib to test.som, this ensures there can be multiple tests named test.som in different directories.

This integration test does not replace the unit tests located in TestSuite but acts as a compliment to it. These integration tests can test more than unit tests can:
- SOM level errors that would cause the VM to exit
- Multiple different classpaths

## Running the Integration Tests
The tests can be run using pytest by simply running pytest in the base directory of any SOM implementation that includes a version of the core-library with IntegrationTests. It requires multiple python modules installed and environment variables set.

### Simple Test Run
```
VM=./path-to-build CLASSPATH=./core-lib/Smalltalk python3 -m pytest
```

### Optionals
A set of optionals have been created for this test suite which can be added.

## Environment variables
The environment variables are split into required and optional. Some optionals may be required for different implementations of SOM.

#### VM
This is the path from the current working directory to the executable VM of SOM.
#### CLASSPATH
The exact classpath required by SOM to find the Object class etc.
#### TEST_EXCEPTIONS
A yaml file which details the tags of tests. Specifically it labels tests that are expected to fail for one reason or another. **Give the whole path to the file from CWD**.
#### GENERATE_REPORT
Generates a yaml file which can be used as a **TEST_EXCEPTIONS** file. It will also include additional information about how many tests passed, which tests passed that were not expected to and which tests failed. **Give a full path from CWD to where it should be saved including .yaml**.
#### ARBITRARY ENVVARS
When setting custom_classpaths in a test environment variables can be specified to replace tags in those tests, specify those along with all the other variables being specified. Check custom_classpath for more information on runtime classpaths.

## TEST_EXCEPTIONS (How to write a file)
There are four tags that are currently supported by the SOM integration tests. All tags will run the tests still, other than do_not_run, but will not fail on test failure, a tagged test will cause the run to fail only when it passes unexpectedly. Check for example file IntegrationTests/test_tags.yaml.

For a test to be given a tag specify it's location path like this:
```
known_failures:
    core-lib/IntegrationTests/Tests/test.som
```

### known_failures
Any test located in this tag is assumed to fail, it should only be used when another more suitable tag is not available.

### failing_as_unspecified
Any test located in this tag failed because SOM does not specify behaviour in this instance, this means that each implementation may treat this situation differently. *Example dividing by 0.*

### unsupported
Any test located here has a feature which is not suppoprted in this SOM.

### do_not_run
This test should not be ran ever as it causes an error in the python level code. The test may also cause a SOM level error but does not have to. (*This does not include Unicode errors, they are handled at runtime*)

## How to write a new test
For a test to be collected by Pytest it has to start with a comment, the comment should be structured with the expected output for either stderr or stdout.

```
"
VM:
    status: error
    custom_classpath: @AWFY:example/classpath:@CLASSPATH
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

Tags can be used to specify a different classpaths at runtime, this is generally recommended otherwise tests would be directory dependent. These tags can be specified with ```@tag``` where tag is the **exact** spelling and caputalisation of the environment variable that matches. Currently to run the tests ```@AWFY``` must be specified alongside ```@CLASSPATH```.

#### case_sensitive
By default the tests are case insensitive (All outputs and expecteds are converted to be lower case) but by specifying True in case_sensitive that test can be checked as case_sensitive.

#### stderr or stdout:
This is your expected output, each new line will be a new "thing" to check for. Writing ... signifies a gap in checking, the output does not have to feature this gap but may do. Another option that is featured in stdout, stderr checking is *** which signifies an arbitrary precision "word".

**Please note that *** is not compatible in the same line as ...**
```python
# not accpeted
... 1.11***11 ...

# accpeted
... this line ...
Hel***lo
... another ... line
```

### Understanding how the "***" works in test_runner
A word is loosely defined as any connected string of characters in this instance, it can be both numbers or letters. What placing the *** in the word does is as follows:
1. All characters before the *** must be present
2. Not all characters after the *** have to be present, but if they are present must match exactly.
3. There cannot be more characters than the stdout specifies.

This allows for different SOM implementations to pass tests on different levels of precision. But no SOM will pass on an incorrect result.

#### Example
```python
# Expected
stdout:
    1.111***123

# Accepted outputs

1.111
1.1111
1.11112
1.111123

# Not accepted
1.1
1.11
1.111124
1.1111234
```

### Understanding how the "..." works in test_runner
There are situations where the ... is necessary for your output. Here are some example use cases, when they may be necessary and how to write the tests for it. As a preface the check_output will check a line as a whole so writing ... allows for a gap, a more precise check can be made by including as much of the expected output as possible.

#### Possible evaluations of "..."
```
stdout:
    Hello, World
    ...
    Goodbye
```
This would be true for:
```
Hello, World
Today is a Monday
Goodbye

/

Hello, World
Goodbye
```

Line 1 in the below expected stdout says match on a whole line which has Hello, some other text as a gap then the word sample then whatever comes after on that line. Line 2 specifies that we must end with the word line. Whilst line 3 says somewhere in this line the word little must appear.

#### Stdout
```
This is SOM++
Hello, this is some sample output
There is some more on this line
And a little more here
```

#### Expected
```
VM:
    status: success
    case_sensitive: False
    stdout:
        Hello, ... sample ...
        ... is ... this line
        ... little ...
```

### When not to use "..."
- When the word you are searching for is the end of the line do not do this "*word* ...".
- When the word you are searching for is at the beginning of the line do not do this "... *word*"

## Developing the test_runner
For development of the test_runner with more features in the future I have created another set of tests that can be run. These tests test the test_runner itself, they make sure parsing a test file works, output checking works and setting dynamic classpaths works as expected.


#### Run this command below to execute those tests
```
pytest -m tester
```