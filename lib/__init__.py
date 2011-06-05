
class NamedDict(dict):
    def __getattr__(self, name):
        return self[name]
    def __setattr__(self, name, value):
        self[name] = value

class CounterDict(NamedDict):
    def __getitem__(self, name):
        return super(CounterDict, self).get(name, 0)
