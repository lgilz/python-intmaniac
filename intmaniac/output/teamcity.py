# EVERY OUTPUT file must have a class and a get() method

from intmaniac.output.base import GenericOutput


class TeamcityOutput(GenericOutput):

    str_message = "##teamcity[message text='{message}'{status}{details}]"
    str_message_details = " errorDetails='{details}'"
    str_message_status = " status='{status}'"

    str_test_suite_open = "##teamcity[testSuiteStarted name='{name}']"
    str_test_suite_done = "##teamcity[testSuiteFinished name='{name}']"
    str_test_open = "##teamcity[testStarted name='{name}']"

    str_test_fail = "##teamcity[testFailed name='{name}'" \
                    "{type}{message}{details}]"
    str_test_fail_type = " type='{type}'"
    str_test_fail_message = " message='{message}'"
    str_test_fail_details = " details='{details}'"

    str_test_stdout = "##teamcity[testStdOut name='{name}' out='{text}']"
    str_test_stderr = "##teamcity[testStdErr name='{name}' out='{text}']"
    str_test_done = "##teamcity[testFinished name='{name}']"
    str_block_open = "##teamcity[blockOpened name='{name}']"
    str_block_done = "##teamcity[blockClosed name='{name}']"

    @staticmethod
    def format_name(name):
        # I really don't remember why we had to do the first replacement.
        return name.replace("-", ".").replace("'", "|'")

    @staticmethod
    def format_content(s):
        if s:
            return s\
                .replace("'", "|'") \
                .replace("\n", "|n") \
                .replace("\r", "|r")


def get():
    return TeamcityOutput()
