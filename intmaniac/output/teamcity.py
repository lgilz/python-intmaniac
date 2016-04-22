# EVERY OUTPUT file must have a class and a get() method

from intmaniac.output.base import GenericOutput


class TeamcityOutput(GenericOutput):

    @staticmethod
    def format_name(name):
        return name.replace("-", ".")

    str_message = "##teamcity[message text='{message}' " \
                  "errorDetails='{details}' status='{status}']"
    str_test_suite_open = "##teamcity[testSuiteStarted name='{name}']"
    str_test_suite_done = "##teamcity[testSuiteFinished name='{name}']"
    str_test_open = "##teamcity[testStarted name='{name}']"
    str_test_fail = "##teamcity[testFailed name='{name}' " \
                    "{type} {message} {details}]"
    str_test_stdout = "##teamcity[testStdOut name='{name}' out='{text}']"
    str_test_stderr = "##teamcity[testStdErr name='{name}' out='{text}']"
    str_test_done = "##teamcity[testFinished name='{name}']"
    str_block_open = "##teamcity[blockOpened name='{name}']"
    str_block_done = "##teamcity[blockClosed name='{name}']"

    def test_failed(self, type=None, message=None, details=None):
        use_typ = "type='{}'".format(type) if type else None
        use_mes = "message='{}'".format(message) if message else None
        use_det = "details='{}'".format(details) if details else None
        self.dump(self.str_test_fail.format(name=self.open_tests[-1],
                                            type=use_typ,
                                            message=use_mes,
                                            details=use_det))


def get():
    return TeamcityOutput()
