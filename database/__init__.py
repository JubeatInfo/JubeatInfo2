
# -*- coding: utf-8 -*-
import time
from decimal import Decimal
import collections

import sqlalchemy
from sqlalchemy import Column, ForeignKey
from sqlalchemy import CHAR, TIMESTAMP
from sqlalchemy import asc, desc
from sqlalchemy.types import *
from sqlalchemy.orm import mapper
from sqlalchemy.orm import sessionmaker, object_session
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import column_property, composite, deferred
from sqlalchemy.orm import validates
from sqlalchemy.orm import synonym
from sqlalchemy.sql import select, and_, or_, func
from sqlalchemy.sql.expression import case
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import synonym_for

from jubeatinfo.database import util
from jubeatinfo.database import secret
from jubeatinfo import const

engine = sqlalchemy.create_engine(secret.JUBEATINFO_DATABASE, echo=False)

Session = sessionmaker(autoflush=True, autocommit=True, bind=engine)
session = Session()
 
Base = declarative_base(bind=engine)

def create_schema():
    if not Base.metadata.is_bound():
        Base.metadata.connect(engine)
    Base.metadata.create_all()
    engine.execute("ALTER TABLE `user` CHANGE `friend_id` `friend_id` BIGINT NOT NULL")


#create_schema()


class Tune(Base):
    """In JubeatInfo, Tune refer to a playable unit of note pattern set."""
    __tablename__ = 'tunes'
    
    music_id = Column(Integer, ForeignKey('musics.music_id'), primary_key=True)
    dif_id = Column('difficulty', Integer, primary_key=True)
    level = Column(Integer, nullable=False)
    notes = Column(Integer, nullable=False)
    score_per_note = column_property(900000 / notes)

    def __repr__(self):
        return "<Tune(%d-%d,lv%d,#%d)>" % \
            (self.music_id, self.dif_id, self.level, self.notes)


class Music(Base):
    """In JubeatInfo, Music refer to a playable unit of music as art."""
    __tablename__ = 'musics'
   
    class BPM(object):
        """Composition object to represent BPM."""
        
        def __init__(self, min, max):
            self.min, self.max = min, max

        def __composite_values__(self):
            return self.min, self.max

        def __eq__(self, other):
            return isinstance(other, BPM) and\
                other.min == self.min and other.max == self.max

        def __ne__(self, other):
            return not self.__eq__(other)

        def __repr__(self):
            return "<BPM(%d,%d)>" % (self.min, self.max)

        def __str__(self):
            if self.min == self.max:
                return str(self.min)
            return "%d-%d" % (self.min, self.max)

        @property
        def category(self):
            if self.max >= 180: return 'fast'
            if self.max <= 120: return 'slow'
            return 'mid'

    class Localization(Base):
        __tablename__ = 'tracks_localization'

        music_id = Column(Integer, ForeignKey('musics.music_id'),
                          primary_key=True)
        locale = Column(CHAR(2), primary_key=True)
        text = Column(UnicodeText)

        def __repr__(self):
            return "<Music.Localization(%d,'%s','%s')>" % \
                (self.music_id, self.locale, self.text)

    class Alias(Base):
        __tablename__ = 'tracks_alias'

        music_id = Column(Integer, ForeignKey('musics.music_id'),
                          primary_key=True)
        locale = Column(CHAR(2), primary_key=True)
        text = Column(UnicodeText, primary_key=True)
        priority = Column(Integer(4))

        def __repr__(self):
            return "<Music.Alias(%d,'%s','%s',%d)>" % \
                (self.music_id, self.locale, self.text, self.priority)
    
    aliases_pool = Alias.__table__

    music_id = Column(Integer, primary_key=True)
    id = synonym('music_id')
    title = Column(UnicodeText)
    artist = Column(UnicodeText)
    sort_id = Column(Integer(6))
    icon_path = Column(UnicodeText)
    bpm = composite(BPM,
                    Column('bpm_min', Integer), Column('bpm_max', Integer))
    version_id = Column('version', Integer(4))

    bsc = relationship(Tune, uselist=False,
                       primaryjoin=and_(Tune.music_id == music_id,
                                        Tune.dif_id == 1))
    adv = relationship(Tune, uselist=False,
                       primaryjoin=and_(Tune.music_id == music_id,
                                        Tune.dif_id == 2))
    ext = relationship(Tune, uselist=False,
                       primaryjoin=and_(Tune.music_id == music_id,
                                        Tune.dif_id == 3))
    tunes = {1: bsc, 2:adv, 3:ext}

    @property
    def version_name(self):
        return const.VERSION_NAMES[self.version_id]

    @property
    def version_key(self):
        return const.VERSION_KEYS[self.version_id]
    
    @property
    def knit_icon_path(self):
        return const.KNIT_IMAGE_PREFIX + self.icon_path

    @classmethod
    def by_title(cls, keyword, locale=None):
        """Search a music with its title and localized title.
        Whitespaces are ignored.
        """

        """# Search a music its title exactly matched to keyword"""
        music = session.query(cls).filter(cls.title == keyword).first()
        if music: return music
       
        """# Search a music its title includes keyword"""
        reduced_keyword = keyword.replace(' ', '')
        reduced_title = func.replace(cls.title, ' ', '')
        music = session.query(cls).\
            filter(or_(
                cls.title.contains(keyword),
                reduced_title.contains(reduced_keyword))).\
            limit(1).first()
        if music: return music
        
        """# Search a music its localized title includes keyword"""
        if locale is None: return None

        reduced_text = func.replace(cls.Localization.text, ' ', '')
        music_data = session.query(cls.Localization).\
            filter(cls.Localization.locale == locale).\
            filter(or_(
                cls.Localization.text.contains(keyword),
                reduced_text.contains(reduced_keyword))).\
            limit(1).first()
        if music_data is not None:
            return cls.by(music_id=music_data.music_id)

    @classmethod
    def by_keyword(cls, keyword, locale=None):
        """Search a music with its title, localized title, search alias.
        Whitespaces are ignored
        """

        """# Search a music its title or localized text includes keyword"""
        music = cls.by_title(keyword, locale)
        if music: return music
        
        def music_by_id(music_id):
            return session.query(cls).filter(music_id=music_id).first()

        """# Search a music its alias includes keyword"""
        reduced_keyword = keyword.replace(' ', '')
        reduced_text = func.replace('text', ' ', '')
        if locale is not None:
            data = session.query(cls.Alias).\
                filter(or_(
                    cls.Alias.locale == locale, cls.Alias.locale == None)).\
                filter(or_(
                    cls.Alias.text.contains(keyword),
                    reduced_text.contains(reduced_keyword))).\
                order_by(cls.Alias.priority).\
                limit(1).first()
            if data:
                return music_by_id(data.music_id)
        
        """# Search a music its localized text includes keyword with unmatching
        locales"""
        data = session.query(cls.Localization).\
            filter(or_(
                cls.Localization.text.contains(keyword),
                reduced_text.contains(reduced_keyword))).\
            limit(1).first()
        if data:
            return music_by_id(data.music_id)
            
        """# Search a music its alias includes keyword with unmatching locales
        """
        data = session.query(cls.Alias).\
            filter(or_(
                cls.Alias.text.contains(keyword),
                reduced_text.contains(reduced_keyword))).\
            order_by(cls.Alias.priority).\
            limit(1).first()
        if data:
            return music_by_id(data.music_id)
    
    @property
    def has_long_title(self):
        """Mark too long title for front-end"""
        return self.music_id == 19425132

    @property
    def tunes(self):
        return {1:self.bsc, 2:self.adv, 3:self.ext}

    def localization(self, locale):
        return session.query(Music.Localization).\
            filter_by(music_id=self.id, locale=locale).first()

    def local_aliases(self, locale):
        return self.aliases.filter_by(locale=locale).all()

    def __repr__(self):
        return "<Music(%d,'%s',#%d,bsc%s,adv%s,ext%s,%s)>" % \
            (self.music_id, self.title, self.sort_id,
             self.bsc, self.adv, self.ext, self.bpm)


class User(Base):
    """In JubeatInfo, User refer to a unit that represent identity to
    determine each friend id of e-amusement pass.
    """
    __tablename__ = 'user'

    class Raw(object):
        """Temporary raw data to support Jubegraph update."""
        
        def __init__(self, time, main, score):
            self.main, self.score, self.time = main, score, time

        def __composite_values__(self):
            return self.time, self.main, self.score

        def __repr__(self):
            return "<User.Raw(%s,\n\t'%s',\n\t'%s'\n\t)>" %\
                (self.time, self.main, self.score)

    friend_id = Column(BigInteger, primary_key=True)
    id = synonym('friend_id')
    alias = Column(Unicode(33), nullable=False)
    password = deferred(Column(CHAR(40), nullable=False))
    #raw = composite(
    #    Column('raw_timestamp', DateTime, nullable=False),
    #    deferred(Column('raw_main', UnicodeText, nullable=False)),
    #    deferred(Column('raw_score', UnicodeText, nullable=False)))
    raw_time = Column('raw_timestamp', DateTime, nullable=False)
    raw_main = deferred(Column(UnicodeText, nullable=False))
    raw_score = deferred(Column(UnicodeText, nullable=False))
    enroll_time = Column('enroll_time', DateTime, nullable=False)
    ban = Column(Integer, nullable=False)
    status = Column(Integer, nullable=False)

    userdata_pool = relationship('UserData', order_by="UserData.last_date",
                        primaryjoin="User.friend_id == UserData.friend_id",
                        backref="user", lazy='dynamic')
    playdata_pool = relationship('PlayData',
                        primaryjoin="User.friend_id == PlayData.friend_id",
                        backref="user", lazy='dynamic')

    def userdata(self, date=None):
        """Find recent UserData object just before given date."""

        pool = self.userdata_pool
        if date is not None:
            pool = pool.filter(UserData.last_date <= date)
        try:
            return pool[-1]
        except IndexError:
            return None

    def playdata(self, date=None, music_id=None, dif_id=None):
        """Find set of recent PlayData objects just before given date."""
        
        dates =\
            select([PlayData.music_id, PlayData.dif_id,
                        func.max(PlayData.date).label('recent_date')],
                    from_obj=PlayData.__table__).\
            where(PlayData.friend_id == self.friend_id)
        if date is not None:
            dates = dates.where(PlayData.date <= date)
        dates = dates.group_by(PlayData.music_id, PlayData.dif_id).alias()
            
        return session.query(PlayData).\
            filter(PlayData.friend_id == self.friend_id).\
            filter(PlayData.music_id == dates.c.music_id).\
            filter(PlayData.dif_id == dates.c.difficulty).\
            filter(PlayData.date == dates.c.recent_date)

    def __init__(self, friend_id, alias, password='', ban=False, status=0):
        self.friend_id = friend_id
        self.alias = alias
        self.password = password
        self.raw_main, self.raw_score = '', ''
        self.ban = ban
        self.status = status
    
    def __repr__(self):
        return "<User(%d,'%s',%s,%d)>" % \
            (self.friend_id, self.alias, self.ban, self.status)

    def __str__(self):
        return "%s(%d)" % (self.alias, self.friend_id)

    @validates('friend_id')
    def validate_friend_id(self, key, friend_id):
        strval = str(friend_id)
        assert len(strval) == 14
        assert strval.startswith('244000')
        return friend_id

    @property
    def played_dates(self):
        values = self.userdata_pool.group_by(UserData.last_date).\
            values(UserData.last_date)
        return [value.last_date for value in values]

    def stat_history(self, stat, desc=False, dates=None):
        if type(getattr(UserData, stat)) is property:
            return self.stat_history_by_property(stat, desc, dates)
        return self.stat_history_by_query(stat, desc, dates)

    def stat_history_by_query(self, stat, desc=False, dates=None):
        order = UserData.date
        if desc: order = sqlalchemy.desc(order)
        
        value_column = getattr(UserData, stat).label('value')
        query = object_session(self).\
            query(value_column, UserData.date,
                func.unix_timestamp(UserData.last_date).label('unixtime')).\
            filter(UserData.friend_id == self.friend_id)

        if dates is not None:
            query = util.cutoff_dates(query, UserData.last_date, dates)
        
        return query

    def stat_history_by_property(self, stat, desc=False, dates=None):
        order = UserData.date
        if desc: order = sqlalchemy.desc(order)
        
        query = object_session(self).\
            query(UserData,
                func.unix_timestamp(UserData.last_date).label('unixtime')).\
            filter(UserData.friend_id == self.friend_id)
        
        if dates is not None:
            query = util.cutoff_dates(query, UserData.last_date, dates)
       
        HistItem = collections.namedtuple('HistItem',
                                          ['value', 'date', 'unixtime'])
        for row in query:
            yield HistItem(
                value=getattr(row.UserData, stat),
                date=row.UserData.last_date,
                unixtime=row.unixtime)

    def tune_history(self, tunes, desc=False, dates=None):
        order = PlayData.date
        if desc: order = sqlalchemy.desc(order)
        query = object_session(self).\
            query(PlayData.score.label('value'), PlayData.date,
                func.unix_timestamp(PlayData.date).label('unixtime')).\
            filter(PlayData.friend_id == self.friend_id).\
            filter(util.tune_conds(tunes, PlayData))

        if dates is not None:
            query = util.cutoff_dates(query, PlayData.date, dates)

        return query

    def tune_history_ext(self, tune, desc=False, dates=None):
        order = PlayData.Detail.date
        if desc: order = sqlalchemy.desc(order)
        query = object_session(self).\
            query(PlayData.Detail,
                func.unix_timestamp(PlayData.Detail.date).
                    label('unixtime')).\
            filter(PlayData.Detail.friend_id == self.friend_id).\
            filter(PlayData.Detail.music_id == tune[0]).\
            filter(PlayData.Detail.dif_id == tune[1])

        if dates is not None:
            query = util.cutoff_dates(query, PlayData.date, dates)

        return query


class UserData(Base):
    """In JubeatInfo, UserData is refer to a set of data that can be extracted
    from User.raw_main and derived from the former one.
    """
    __tablename__ = 'user_data'
    
    friend_id = Column(BigInteger, ForeignKey('user.friend_id'),
                       primary_key=True)
    card_name = Column(Unicode(9), nullable=False)
    title = Column(Unicode(30), nullable=False)
    group_name = Column(Unicode(20), nullable=False)
    last_location = Column(Unicode(20), nullable=False)
    last_date = Column(Date, nullable=False)
    date = synonym('last_date')
    jubility_icon = Column(Unicode(12), nullable=False)
    jubility = Column(Float, nullable=False)
    jubility_diff = Column(Float, nullable=False)
    jubility_icon_path = Column(UnicodeText, nullable=False)
    achievement_point = Column(Integer, nullable=False)
    achievement_rank = Column(Integer, nullable=False)
    play_count = Column(Integer, nullable=False)
    clear_count = Column(Integer, nullable=False)
    save_count = Column(Integer, nullable=False)
    saved_count = Column(Integer, nullable=False)
    excellent_count = Column(Integer, nullable=False)
    excellent_tune_count = Column(Integer, nullable=False)
    fullcombo_count = Column(Integer, nullable=False)
    fullcombo_tune_count = Column(Integer, nullable=False)
    matched_player_count = Column(Integer, nullable=False)
    matched_victory_count = Column(Integer, nullable=False)
    matched_victory_rate = Column(Float, nullable=False)
    marker = Column(Unicode(15), nullable=False)
    marker_path = Column(UnicodeText, nullable=False)
    background = Column(Unicode(15), nullable=False)
    timestamp = Column(TIMESTAMP, primary_key=True)

    failed_count = column_property(play_count - clear_count)
    clear_rate = column_property(clear_count / play_count)
    saved_rate = column_property(saved_count / (play_count - clear_count))
    fullcombo_rate = column_property(fullcombo_count / play_count)
    excellent_rate = column_property(excellent_count / play_count)
    effective_excellent_rate = column_property(
        excellent_count / fullcombo_count)
    efficiency_degree = column_property(achievement_point / play_count)
    matched_player_rate = column_property(matched_player_count / play_count)

    @property
    def knit_jubility_icon_path(self):
        return const.KNIT_IMAGE_PREFIX + self.jubility_icon_path
    
    @property
    def knit_marker_path(self):
        return const.KNIT_IMAGE_PREFIX + self.marker_path

    @property
    def playday_count(self):
        sess = object_session(self)
        return sess.\
            query(sess.query(UserData).
                filter_by(friend_id=self.friend_id).
                filter(UserData.last_date <= self.last_date).
                group_by(UserData.last_date).
                subquery()).\
            count()

    @property
    def memberday_count(self):
        row =\
            select(
                [(func.unix_timestamp(self.timestamp) - 
                    func.unix_timestamp(UserData.last_date)).
                        label('seconds')]).\
            where(UserData.friend_id == self.friend_id).\
            order_by(UserData.last_date).\
            limit(1).execute().first()
        seconds = row.seconds if row is not None else 0
        return seconds / 86400.0

    @property
    def memberday_count_capped(self):
        bound = 60.0
        memberday_count = self.memberday_count
        if memberday_count < bound:
            memberday_count += 1
            memberday_count *= 1 + (1 - memberday_count/bound) ** 2
        return memberday_count 

    @property
    def addiction_rate(self):
        return self.playday_count / self.memberday_count_capped

    @property
    def concentration_degree(self):
        base_play_count = select([UserData.play_count]).\
            where(UserData.friend_id == self.friend_id).\
            order_by(UserData.timestamp).\
            limit(1).execute().first().play_count
        playday_count = self.playday_count
        if playday_count == 1:
            return 0
            #return base_play_count
        return (self.play_count - base_play_count) / (self.playday_count - 1.0)

    def __init__(self, friend_id, timestamp):
        self.friend_id = friend_id
        self.timestamp = timestamp

    def __repr__(self):
        return "<UserData(%d('%s'),date:'%s','%s')>" % \
            (self.friend_id, self.card_name, self.last_date, self.timestamp)

    @classmethod
    def recent_dates(cls, date=None):
        """Set of recent play date just before given date for all users."""

        recent_dates =\
            select([cls.friend_id, func.max(cls.date).label('recent_date')]).\
                where(cls.friend_id > 0)
        if date is not None:
            recent_dates = recent_dates.where(cls.last_date <= date)
        return recent_dates.group_by(cls.friend_id).alias()

    @classmethod
    def ranking(cls, stat, friend_id=0, date=None, desc=True):
        """Export ranking for selected user statistics."""
       
        if type(getattr(cls, stat)) is property:
            return cls.ranking_by_property(stat, friend_id, date, desc)
        return cls.ranking_by_query(stat, friend_id, date, desc)

    @classmethod
    def ranking_by_query(cls, stat, friend_id=0, date=None, desc=True):
        order = 'value' if not desc else sqlalchemy.desc('value')
        dates = cls.recent_dates(date)
        val_col = getattr(cls, stat).label('value')
        query = session.\
            query(val_col,
                (cls.friend_id == friend_id).label('is_mine')).\
            filter(cls.friend_id == dates.c.friend_id). \
            filter(cls.last_date == dates.c.recent_date). \
            order_by(order)
        return query

    @classmethod
    def ranking_by_property(cls, stat, friend_id=0, date=None, desc=True):
        return False # TODO: cache required
        dates = cls.recent_dates(date)
        query = session.\
            query(cls, (cls.friend_id == friend_id).label('is_mine')).\
            filter(cls.friend_id == dates.c.friend_id).\
            filter(cls.last_date == dates.c.recent_date)
        
        RankItem = collections.namedtuple('RankItem', ['value', 'is_mine']) 
        data = []
        for row in query:
            data.append(RankItem(value=getattr(row.UserData, stat),
                                 is_mine=row.is_mine))
        data.sort(key=lambda item: item.value, reverse=desc)
        return data

    @classmethod
    def distribution(cls, stats, friend_id=0, date=None):
        """Export distribution of selected user statistics."""

        dates = cls.recent_dates(date)
        valueattrs = []
        for i, stat in enumerate(stats):
            valueattrs.append(getattr(cls, stat))
            try:
                pathattr = getattr(cls, 'knit_' + stat + '_path')
                valueattrs.append(pathattr.label(stat + '_path'))
            except AttributeError:
                pass
        query = session.\
            query(func.count('*').label('count'),
                func.max(cls.friend_id == friend_id).label('is_mine'),
                *valueattrs).\
            filter(cls.friend_id == dates.c.friend_id).\
            filter(cls.last_date == dates.c.recent_date)
        for stat in stats:
            query = query.group_by(getattr(cls, stat))
        query = query.order_by(desc('count'))
        return query


class PlayData(Base):
    """In JubeatInfo, PlayData refer to a unit contains best score of each
    tunes distinguished by user(friend_id), tune(music_id and dif_id) and a
    date."""
    __tablename__ = 'play_data'

    class Detail(Base):
        """In JubeatInfo, PlayData Detail refer to a unit contains accumulated
        playing data, as like play_count, fullcombo_count or rank of each tunes
        in same manner of PlayData."""
        __tablename__ = 'play_data_special'

        friend_id = Column(BigInteger, ForeignKey(User.friend_id),
                           primary_key=True)
        music_id = Column(Integer, ForeignKey(Music.music_id),
                          primary_key=True)
        dif_id = Column('difficulty', Integer(4), ForeignKey(Tune.dif_id),
                        primary_key=True)
        play_count = Column(Integer(6))
        clear_count = Column(Integer(6))
        fullcombo_count = Column(Integer(6))
        excellent_count = Column(Integer(6))
        rank = Column(Integer(6))
        play_date = Column('date', Date, primary_key=True)
        date = synonym('play_date')

        music = relationship(Music)

        def __repr__(self):
            return "<PlayData.Detail(%d, %d-%d,%d/%d(%d-%d),%d,'%s'>" % \
                (self.friend_id, self.music_id, self.dif_id,
                 self.play_count, self.clear_count,
                 self.fullcombo_count, self.excellent_count,
                 self.rank, self.date)
    
    extensions_pool = Detail.__table__

    friend_id = Column(BigInteger, ForeignKey(User.friend_id),
                       primary_key=True)
    music_id = Column(Integer, ForeignKey(Music.music_id), primary_key=True)
    dif_id = Column('difficulty', Integer, ForeignKey(Tune.dif_id),
                    primary_key=True)
    play_date = Column('date', Date, primary_key=True)
    date = synonym('play_date')
    score = Column(Integer, default=0)
    grade_key = Column('gscore', Integer)
    
    music = relationship(Music)
    tune = relationship(Tune, primaryjoin=and_(Tune.music_id == music_id,
                                               Tune.dif_id == dif_id),
                        lazy=False)
   
    @property
    def grade(self):
        """Character string representation of grade"""
        return const.GRADES[self.grade_key]

    @property
    def extension(self):
        return object_session(self).query(self.Detail). \
            filter_by(friend_id=self.friend_id). \
            filter_by(music_id=self.music_id). \
            filter_by(dif_id=self.dif_id). \
            filter(self.Detail.date <= self.date). \
            order_by(self.Detail.date).first()

    @property
    def score_(self):
        if self.score is not None:
            return self.score
        return 0

    remain_score = column_property(score - 1000000)
    @property
    def remain_score_(self):
        if self.remain_score is not None:
            return self.remain_score
        return -1000000
   
    scaled_score = column_property(
        select([(score - 1000000) / \
            select([Tune.score_per_note]). \
                where(Tune.music_id == music_id). \
                where(Tune.dif_id == dif_id)
            ]))
    @property
    def scaled_score_(self):
        if self.scaled_score is not None:
            return self.scaled_score
        res = session.query(Tune.notes).\
            filter(Tune.music_id == self.music_id).\
            filter(Tune.dif_id == self.dif_id)
        return res.one()[0]

    @property
    def scaled_score2(self):
        return self.scaled_score * 10 / 3

    @property
    def scaled_score2_(self):
        return self.scaled_score_ * 10 / 3

    @property
    def analyze(self):
        scaled = -self.scaled_score
        if scaled is None:
            return None, None
        miss = int(scaled / 3) * 3
        great = int(scaled % 3 / Decimal('0.3'))
        return miss, great

    def __init__(self, friend_id=0, music_id=0, dif_id=0, date=None,
                 score=0, grade_key=False):
        self.friend_id = friend_id
        self.music_id = music_id
        self.dif_id = dif_id
        self.date = date
        self.score = score
        self.grade_key = grade_key if grade_key != False else\
                         const.GRADE_KEY_BY_SCORE(score)
        
    def __repr__(self):
        return "<PlayData(%d,%d-%d,'%s',%d(%s))>" % \
            (self.friend_id, self.music_id, self.dif_id, self.date,
             self.score, self.grade)

    @classmethod
    def ranking(cls, tunes, friend_id=0, date=None):
        """Export ranking for selected tunes.
        Each tune is described as like a tuple (music_id, dif_id)
        """

        query = session.\
            query(cls.friend_id, func.max(cls.score).label('score')).\
            filter(cls.friend_id > 10).\
            filter(util.tune_conds(tunes, PlayData))
        if date is not None:
            query = query.filter(cls.date <= date)
        query = query.group_by(cls.friend_id, cls.music_id, cls.dif_id)
        max_set = query.subquery().alias()
        
        return session.\
            query(
                func.sum(max_set.c.score).label('value'),
                (max_set.c.friend_id == friend_id).label('is_mine')).\
            group_by(max_set.c.friend_id).order_by(desc('value'))
            

class UserRequest(Base):
    __tablename__ = 'user_queue'

    friend_id = Column(BigInteger, primary_key=True)
    requested_time = Column('timestamp', DateTime, nullable=False)

    def __init__(self, friend_id):
        self.friend_id = friend_id
        self.requested_time = func.current_timestamp()


class MusicRequest(Base):
    __tablename__ = 'music_queue'

    friend_id = Column(BigInteger, primary_key=True)
    music_id = Column(Integer, primary_key=True)
    requested_time = Column('timestamp', DateTime, nullable=False)
    
    def __init__(self, friend_id, music_id):
        self.friend_id = friend_id
        self.music_id = music_id
        self.requested_time = func.current_timestamp()


"""Add shortcut methods filter_by, filter, by to each declarative class.
# filter_by: shortcut of filter_by query from global session
# filter: shortcut of filter query from global session
# by: shortcut of filter query from glabal session, and take one() from it
"""
import sys
import inspect
import types
for name, cls in inspect.getmembers(sys.modules[__name__]):
    if inspect.isclass(cls) and issubclass(cls, Base) and cls != Base:
        def filter_by(cls, **kwargs):
            return session.query(cls).filter_by(**kwargs)
        def filter(cls, criterion):
            return session.query(cls).filter(criterion)
        def filter_one_by(cls, **kwargs):
            return cls.filter_by(**kwargs).one()
        def all(cls):
            return session.query(cls)
        setattr(cls, 'filter_by', types.MethodType(filter_by, cls, cls))
        setattr(cls, 'filter', types.MethodType(filter, cls, cls))
        setattr(cls, 'by', types.MethodType(filter_one_by, cls, cls))
        setattr(cls, 'all', types.MethodType(all, cls, cls))

