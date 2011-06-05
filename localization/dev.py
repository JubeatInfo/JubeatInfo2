
class SelfDict(object):
    def __getitem__(self, key):
        return key

messages = SelfDict()
contents = SelfDict()
