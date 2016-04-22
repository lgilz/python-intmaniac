

class GenericOutput:
    str_message = "{message} (status: {status}, details: {details})"
    str_test_suite_open = "\n### TEST SUITE: {name}\n"
    str_test_suite_done = "\n### /TEST SUITE: {name}\n"
    str_test_open = "## TEST: {name}"
    str_test_fail = "TEST FAILURE:\nTYPE: {type}\nMESSAGE: {message}\nDETAILS:\n{details}\n"
    str_test_stdout = "TEST STDOUT:\n{text}"
    str_test_stderr = "TEST STDERR:\n{text}"
    str_test_done = "## /TEST {name}\n"
    str_block_open = "\n**** BLOCK {name}"
    str_block_done = "**** /BLOCK {name}\n"

    def __init__(self):
        self.open_tests = []
        self.open_test_suits = []
        self.open_blocks = []

    # name format helper

    @staticmethod
    def format_name(name):
        return name

    # generic message

    def message(self, s, details='-', status='-'):
        self.dump(self.str_message.format(message=s,
                                          details=details,
                                          status=status))

    # generic grouping of output

    def block_open(self, s):
        name = self.format_name(s)
        self.dump(self.str_block_open.format(name=name))
        self.open_blocks.append(name)

    def block_done(self):
        self.dump(self.str_block_done.format(name=self.open_blocks.pop()))

    # test suites

    def test_suite_open(self, s):
        name = self.format_name(s)
        self.dump(self.str_test_suite_open.format(name=name))
        self.open_test_suits.append(name)

    def test_suite_done(self):
        self.dump(self.str_test_suite_done.format(name=self.open_test_suits.pop()))

    # test_open, ONE of the middle methods, then test_done

    def test_open(self, s):
        name = self.format_name(s)
        self.dump(self.str_test_open.format(name=name))
        self.open_tests.append(name)

    def test_stdout(self, s):
        self.dump(self.str_test_stdout.format(text=s.strip(),
                                              name=self.open_tests[-1]))

    def test_stderr(self, s):
        self.dump(self.str_test_stderr.format(text=s.strip(),
                                              name=self.open_tests[-1]))

    def test_failed(self, type="GenericFailure", message="No reason available", details="No details available"):
        self.dump(self.str_test_fail.format(name=self.open_tests[-1],
                                            type=type,
                                            message=message.strip(),
                                            details=details.strip()))

    def test_done(self):
        self.dump(self.str_test_done.format(name=self.open_tests.pop()))

    # generic print

    @staticmethod
    def dump(*args):
        thing = "".join(args)
        print(thing)


def get():
    return GenericOutput()
