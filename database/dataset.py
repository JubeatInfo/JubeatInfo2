
# -*- coding: utf-8 -*-
import time
from collections import namedtuple

from jubeatinfo.lib import NamedDict, CounterDict

HistoryItem = namedtuple('HistoryItem', ['label', 'value', 'diffvalue'])
class HistoryDataSet(object):
    def __init__(self):
        self.data = {}
        self.prev, self.skipped = -1, False
        self.diffprev, self.diffskipped = -1, False

    def put(self, item):
        if item.value is None: return
        
        self.skipped = self.prev == item.value
        if self.skipped: return

        self.prev = item.value
        if item.unixtime in self.data.keys():
            self.data[item.unixtime] = self.data[item.unixtime].\
                _replace(value=item.value)
        else:
            self.data[item.unixtime] = HistoryItem(
                label=item.date, value=item.value, diffvalue=None)

    def put_diff(self, item):
        if item.value is None: return

        self.diffskipped = self.diffprev == item.value
        if self.diffskipped: return

        self.diffprev = item.value
        if item.unixtime in self.data.keys():
            self.data[item.unixtime] = self.data[item.unixtime].\
                _replace(diffvalue=item.value)
        else:
            self.data[item.unixtime] = HistoryItem(
                label=item.date, diffvalue=item.value, value=None)

    def seal(self, last_date=None, diff_last_date=None):
        if True: #self.skipped and last_date:
            unixtime = time.mktime(last_date.timetuple())
            item = NamedDict(
                date=last_date, unixtime=unixtime, value=self.prev)
            self.prev = None
            self.put(item)

        if self.diffskipped and diff_last_date:
            unixtime = time.mktime(diff_last_date.timetuple())
            item = NamedDict(
                date=diff_last_date, unixtime=unixtime, value=self.diffprev)
            self.prev = None
            self.put_diff(item)
        
        self._keys = self.data.keys()
        self._keys.sort()
        self._keys.reverse()

    def keys(self):
        return _keys

    def __len__(self):
        return len(self.data)

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def iteritems(self):
        for key in self._keys:
            yield key, self.data[key]

    def put_all(self, items1, items2, date1, date2):
        for item in items1:
            self.put(item)
        for item in items2:
            self.put_diff(item)
        self.seal(date1, date2)

RankingItem = namedtuple('RankingItem', ['rank', 'value', 'is_mine'])
class RankingDataSet(object):
    def __init__(self):
        self.data = []
        self.count = 0
        self.rank = 0
        self.prev = -1

    def put(self, item):
        if item.value is None: return
        self.count += 1
        if item.value != self.prev:
            self.rank = self.count
            self.prev = item.value
        self.data.append(RankingItem(
            rank=self.rank, value=item.value, is_mine=item.is_mine))

    def seal(self):
        pass

    def put_all(self, items):
        for item in items:
            self.put(item)
        self.seal()

    def __len__(self):
        return len(self.data)

    def __getitem__(self, key):
        return self.data[key]

class DistributionDataSet(object):
    def __init__(self, domains):
        self.domains = domains
        self.degree = len(domains)
        self.data = []
        
    def put(self, item):
        self.data.append(item)

    def seal(self):
        pass

    def put_all(self, items):
        self.data += items
        self.seal()

    def __len__(self):
        return len(self.data)

    def __getitem__(self, key):
        return self.data[key]

class Distribution2DataSet(DistributionDataSet):
    def __init__(self, domains):
        super(Distribution2DataSet, self).__init__(domains)
        self.domain1, self.domain2 = domains[0], domains[1]
        self.keys1, self.keys2 = [], []
        self.sum1, self.sum2 = CounterDict(), CounterDict()
        self.total = 0

        self.is_mine1, self.is_mine2 = '', ''
        self.grid = {}

    def put(self, item):
        super(Distribution2DataSet, self).put(item)
        key1 = getattr(item, self.domain1)
        key2 = getattr(item, self.domain2)
        if not key1 in self.keys1:
            self.keys1.append(key1)
            self.grid[key1] = {}
        if not key2 in self.keys2:
            self.keys2.append(key2)
        self.grid[key1][key2] = item.count
        self.sum1[key1] += item.count
        self.sum2[key2] += item.count
        self.total += item.count
        if item.is_mine:
            self.is_mine1 = getattr(item, self.domain1)
            self.is_mine2 = getattr(item, self.domain2)
    
    def put_all(self, items):
        for item in items:
            self.put(item)
        self.seal()

