

class GenericOutput:
    str_message = "MESSAGE: {message}{status}{details}"
    str_message_details = "\n  - DETAILS: {details})"
    str_message_status = "\n  - STATUS:  {status})"
    str_test_suite_open = "\n### TEST SUITE: {name}"
    str_test_suite_done = "\n### /TEST SUITE: {name}"
    str_test_open = "## TEST: {name}"
    str_test_fail = "TEST FAILURE{type}{message}{details}"
    str_test_fail_type = "\nTYPE:    {type}"
    str_test_fail_message = "\nMESSAGE: {message}"
    str_test_fail_details = "\nDETAILS: {details}"
    str_test_stdout = "TEST STDOUT:\n{text}"
    str_test_stderr = "TEST STDERR:\n{text}"
    str_test_done = "## /TEST {name}"
    str_block_open = "\n**** BLOCK {name}"
    str_block_done = "**** /BLOCK {name}"

    def __init__(self):
        self.open_tests = []
        self.open_test_suits = []
        self.open_blocks = []

    # name format helper

    @staticmethod
    def format_name(name):
        if name:
            return name

    @staticmethod
    def format_content(s):
        return s

    # generic message

    def message(self, s, details=None, status=None):
        details = self.format_content(details)
        status = self.format_content(status)
        details = self.str_message_details.format(details=details) \
            if details else ""
        status = self.str_message_status.format(status=status) \
            if status else ""
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
        test_suite_name = self.open_test_suits.pop()
        self.dump(self.str_test_suite_done.format(name=test_suite_name))

    # test_open, ONE of the middle methods, then test_done

    def test_open(self, s):
        name = self.format_name(s)
        self.dump(self.str_test_open.format(name=name))
        self.open_tests.append(name)

    def test_stdout(self, s):
        s = self.format_content(s)
        self.dump(self.str_test_stdout.format(text=s.strip(),
                                              name=self.open_tests[-1]))

    def test_stderr(self, s):
        s = self.format_content(s)
        self.dump(self.str_test_stderr.format(text=s.strip(),
                                              name=self.open_tests[-1]))

    def test_failed(self, type=None, message=None, details=None):
        type, message, details = self.format_content(type), \
                                 self.format_content(message), \
                                 self.format_content(details)
        type = self.str_test_fail_type.format(type=type) \
            if type else ""
        message = self.str_test_fail_message.format(message=message) \
            if message else ""
        details = self.str_test_fail_details.format(details=details) \
            if details else ""
        self.dump(self.str_test_fail.format(name=self.open_tests[-1],
                                            type=type,
                                            message=message,
                                            details=details))

    def test_done(self):
        self.dump(self.str_test_done.format(name=self.open_tests.pop()))

    # generic print

    @staticmethod
    def dump(*args):
        thing = "".join(args)
        print(thing)


def get():
    return GenericOutput()
