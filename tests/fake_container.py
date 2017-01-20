class FakeContainer:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def start(self):
        return 0

    def logs(self, *args, **kwargs):
        return [b'thisisafakelog', b'thisisanotherfakelog']
