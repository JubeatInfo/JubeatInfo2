
# -*- coding: utf-8 -*-
from math import copysign
from collections import namedtuple
import datetime

from flask import g
from sqlalchemy.orm import aliased

from jubeatinfo.database import *
from jubeatinfo.lib import NamedDict, CounterDict
import jubeatinfo.const

_zerodate = datetime.date(1970, 1, 1)
ORDER_FUNCS = {
    'version':  lambda r: r.music.version_id * 0x10000 - r.music.sort_id,
    'title':    lambda r: r.music.title,
    'sort_id':  lambda r: r.music.sort_id,
    
    'score':    lambda r: r.data1.key_score,
    'level':    lambda r: r.tune.level * 1000000 + r.data1.score_,
    'notes':    lambda r: r.tune.notes,
    'date':     lambda r: r.data1.date if r.data1.date else _zerodate,
    'diff':     lambda r: r.derived.diff,
}

SCORE_KEYS = {
    'score': 'score',
    'remain': 'remain_score',
    'scaled': 'scaled_score',
}


DataDiff = namedtuple('DataDiff', ['diff', 'diffsign', 'emph'])

def diff(d1, d2, last_date):
    if g.diffusername:
        if d1.key_score > d2.key_score:
            emph = 2
        elif d2.key_score > 0 and d1.key_score == d2.key_score:
            emph = 1
        else:
            emph = 0
    else:
        if d1.date is not None and d1.date == last_date:
            emph = -1
        else:
            emph = 0
    diff = d1.key_score - d2.key_score
    diffsign = 0 if diff == 0 else copysign(1, diff)
    return DataDiff(diff=diff, diffsign=diffsign, emph=emph)


class ScoreDict(NamedDict):
    def __getattr__(self, name):
        return self.get(name, None)

class UserScore(object):
    """This is interface to provides scores data, comparing and statistics."""
    
    def __init__(self, user1, user2, date=None, diffdate=None,
                 order='-version', options=g):
        self.lang = getattr(options, 'lang', None)
        self.part1 = part1 = NamedDict(user=user1)
        self.part1.date = date
        part1.last_date = user1.userdata().last_date
        self.part2 = part2 = NamedDict(user=user2)
        self.part2.date = diffdate if diffdate is not None else date
        self.parts = (part1, part2)
        self.order = order
        self.viewmode = getattr(options, 'score_viewmode', 'music')
        self.scorekey = SCORE_KEYS[getattr(options, 'score_mode', 'score')]
        self.scoreprop = self.scorekey + '_'
        self.data = self.gen_data()
        self.data = self.normalize()
        self.ordersign, self.orderkey = self.orderinfo()
        self.data = self.sort()

    def orderinfo(self):
        sign, key = False, self.order
        if key:
            head = key[0]
            if head == '-':
                sign, key = True, key[1:]
            elif head == '+':
                sign, key = False, key[1:]
        return sign, key

    def sort(self):
        func = ORDER_FUNCS.get(self.orderkey, lambda x: 0)
        return sorted(self.data, key=func, reverse=self.ordersign)

    def get_fixed(self, row, key, dif_id):
        d = getattr(row, key)
        if d is None:
            d = PlayData(music_id=row.music.id, dif_id=dif_id, grade_key=None)
            setattr(row, key, d)
        d.key_score = getattr(d, self.scoreprop)
        return d
    

class UserScoreByMusic(UserScore):
    def gen_data(self):
        data = {}
        for music in Music.filter(Music.id > 10):
            data[music.id] = NamedDict(music=music, l10n=None)
        
        l10ns = session.query(Music.Localization).\
            filter_by(locale=self.lang).\
            filter(Music.Localization.music_id > 10)
        for l10n in l10ns:
            data[l10n.music_id].l10n = l10n

        for tune in Tune.all():
            data[tune.music_id][tune.dif_id] = ScoreDict(tune=tune)
        
        for p, part in enumerate(self.parts):
            plays = part.user.playdata(part.date).\
                filter(PlayData.music_id > 10)
            for play in plays:
                attr = 'data%d' % (p + 1)
                datum = data[play.music_id][play.dif_id]
                setattr(datum, attr, play)
        return data.values()

    def normalize(self):
        self.stats = ScoreStats()

        difrange = const.DIFFICULTY_RANGE
        res = []
        for row in self.data:
            for i in difrange:
                d1 = self.get_fixed(row, 'data1', i)
                d2 = self.get_fixed(row, 'data2', i)
                drkey = 'derived'
                setattr(row[i], drkey, diff(d1, d2, self.part1.last_date))
                self.stats.put(row.music, row[i].tune, d1, d2)
            res.append(row)
        self.stats.seal()
        return res

    def get_fixed(self, row, key, dif_id):
        d = getattr(row[dif_id], key)
        if d is None:
            d = PlayData(music_id=row.music.id, dif_id=dif_id, grade_key=None)
            setattr(row[dif_id], key, d)
        d.key_score = getattr(d, self.scoreprop)
        return d
    

class UserScoreByTune(UserScore):
    def gen_data(self):
        data = {}
        
        l10n = aliased(Music.Localization,
            session.query(Music.Localization).\
                filter_by(locale=self.lang).\
                subquery(),
            name='Localization')
        musictunes = session.\
            query(Music, l10n, Tune).\
            outerjoin((l10n, Music.id == l10n.music_id)).\
            join((Tune, Music.id == Tune.music_id))
        for tune in musictunes:
            key = tune.Tune.music_id * 4 + tune.Tune.dif_id
            data[key] = ScoreDict(
                tune=tune.Tune, music=tune.Music, l10n=tune.Localization)
        
        for p, part in enumerate(self.parts):
            attr = 'data%d' % (p + 1)
            plays = part.user.playdata(part.date).\
                filter(PlayData.music_id > 10)
            for play in plays:
                key = play.music_id * 4 + play.dif_id
                setattr(data[key], attr, play)
        return data.values()

    def normalize(self):
        self.stats = ScoreStats()
        difrange = xrange(1, 4)
        res = []
        for row in self.data:
            d1 = self.get_fixed(row, 'data1', row.tune.dif_id)
            d2 = self.get_fixed(row, 'data2', row.tune.dif_id)
            dr = diff(d1, d2, self.part1.last_date)
            self.stats.put(row.music, row.tune, d1, d2)
            res.append(NamedDict(
                music=row.music, l10n=row.l10n, tune=row.tune,
                data1=d1, data2=d2, derived=dr
            ))
        self.stats.seal()
        return res


class StatDict(NamedDict):
    def __init__(self):
        self.count = 0
        self.count2 = 0
        self.accum = 0
        self.win = 0
        self.lose = 0
        self.draw = 0
        self.sum1 = 0
        self.sum2 = 0
        self.max_date = None

class ScoreStats(object):
    def __init__(self):
        verrange = const.VERSION_RANGE
        difrange = const.DIFFICULTY_RANGE
        lvrange = xrange(1, 11)

        self.all = StatDict()
        self.ver = [self.all] + [StatDict() for x in verrange]
        
        self.dif = [self.all] + [StatDict() for x in difrange]
        self.verdif = [self.dif] + \
            [([self.ver[v]] + [StatDict() for x in difrange])
                for v in verrange]

        self.lv = [self.all] + [StatDict() for x in lvrange]
        self.verlv = [self.lv] + \
            [([self.ver[v]] + [StatDict() for x in lvrange])
                for v in verrange]

        self.grade = {}
        self.vergrade = [self.grade] + [{} for x in verrange]
        for vd in self.vergrade:
            for k in jubeatinfo.const.GRADE_KEYS:
                vd[k] = StatDict()
        
        self.difgrade = [self.grade] + [{} for x in difrange]
        self.verdifgrade = [self.difgrade] +\
            [([self.vergrade[v]] + [{} for x in difrange]) for v in verrange]
        for v,vd in enumerate(self.verdifgrade):
            for d,dd in enumerate(vd):
                for k in jubeatinfo.const.GRADE_KEYS:
                    dd[k] = StatDict()

        self.lvgrade = [self.grade] + [{} for x in lvrange]
        self.verlvgrade = [self.lvgrade] +\
            [([self.vergrade[v]] + [{} for x in lvrange]) for v in verrange]
        for v,vl in enumerate(self.verlvgrade):
            for d,dl in enumerate(vl):
                for k in jubeatinfo.const.GRADE_KEYS:
                    dl[k] = StatDict()

    def put(self, music, tune, play1, play2):
        ver = music.version_id
        dif = tune.dif_id
        lv = tune.level
        gkey = play1.grade_key

        for gd in [self.grade, self.vergrade[ver],
                   self.difgrade[dif], self.verdifgrade[ver][dif],
                   self.lvgrade[lv], self.verlvgrade[ver][lv]]:
            for k in jubeatinfo.const.GRADE_KEYS:
                gd[k].count += gkey == k
                gd[k].accum += k is None or gkey >= k

        for c in [self.all, self.ver[ver], self.dif[dif],
                  self.verdif[ver][dif], self.lv[lv], self.verlv[ver][lv]]:
            if play1.date is not None:
                c.count += 1
                c.win += play1.key_score > play2.key_score
                c.draw += play1.key_score == play2.key_score
                c.lose += play1.key_score < play2.key_score 
                c.sum1 += play1.key_score
                if c.max_date is None or play1.date > c.max_date:
                    c.max_date = play1.date
            if play2.date is not None:
                c.count2 += 1
                c.sum2 += play2.key_score

    def seal(self):
        targets = []
        for dic in self.verdif:
            targets += dic
        
        for c in targets:
            c.sumd = diff(NamedDict(key_score=c.sum1, date=c.max_date),
                          NamedDict(key_score=c.sum2),
                          self.all.max_date)
            c.avg1 = PlayData(score=c.sum1 / c.count if c.count > 0 else 0,
                              date=c.max_date)
            c.avg1.key_score = c.avg1.score
            c.avg2 = PlayData(score=c.sum2 / c.count2 if c.count2 > 0 else 0)
            c.avg2.key_score = c.avg2.score
            c.avgd = diff(c.avg1, c.avg2, self.all.max_date)

    @property
    def ver_ids(self):
        res = []
        for i, stat in enumerate(self.ver):
            if stat.count > 0:
                res.append(i)
        return res

    def __repr__(self):
        res = '<ScoreStats(\n'
        for key in ['all', 'ver', 'dif', 'verdif',
                    'grade', 'vergrade', 'difgrade', 'verdifgrade']:
            res += '\t' + key + ':%s\n'
        res += ')>'
        return res % (self.all, self.ver, self.dif, self.verdif,
                    self.grade, self.vergrade, self.difgrade, self.verdifgrade)


