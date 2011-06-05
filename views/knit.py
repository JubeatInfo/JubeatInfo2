
# -*- coding: utf-8 -*-
from flask import Module
knit = Module(__name__)

import json
from jubeatinfo import app

from flask import request
from flask import url_for
from flask import render_template
from flask import g
from flask import abort
from flask import jsonify
from werkzeug.exceptions import NotFound, InternalServerError
from sqlalchemy import or_

from jubeatinfo import const
from jubeatinfo import database
from jubeatinfo.database.userscore import UserScoreByMusic, UserScoreByTune
from jubeatinfo.database.dataset import\
    HistoryDataSet, RankingDataSet, DistributionDataSet, Distribution2DataSet
from jubeatinfo.views import dependency, filter
from jubeatinfo.views import redirect
from jubeatinfo.views.filter import msg, l10n
from jubeatinfo.views.const import *

@knit.route('/')
def index():
    return render_template('knit.html')


def check_user(**args):
    if not g.username: 
        user = None
        g.userdata = None
        return

    try:
        user = database.User.by(alias=g.username)
        g.userdata = user.userdata(date=g.date)
    except:
        user = None
        g.userdata = None

    if user is None:
        error = NotFound()
        error.type = 'user'
        error.msg = 'err_url_invalid_username'
        raise error
    elif user.userdata_pool.count() == 0:
        error = InternalServerError
        error.type = 'user'
        if not user.raw_main:
            error.msg = 'err_data_not_collected'
        elif u'現在システムエラーが発生しております' in user.raw_main:
            error.msg = 'err_eamusement_system'
        elif u'プレーヤーデータを公開していません' in user.raw_main:
            error.msg = 'err_eamusement_nonpublic'
        else:
            error.msg = 'err_unknown'
        raise error
    return dict(user=user, userdata=g.userdata)


def build_difftool(**args):
    user = args['user']
    return dict(played_dates=user.played_dates)
dependency.add(build_difftool, check_user)


MUSIC_ORDERS = ['version', 'title', 'sort_id']
for order in MUSIC_ORDERS[:]:
    MUSIC_ORDERS.append('-' + order)

def build_user_score_args(**args):
    order = g.getargs.get('order', '-version')
    mode = g.score_mode = g.getargs.get('mode', 'score')
    view = g.getargs.get('view', None)
    if view is None:
        view = 'music' if order in MUSIC_ORDERS else 'tune'
    fmt = filter.xform('natural') if mode != 'scaled' else filter.xform('real2')

    return dict(order=order, score_mode=mode, score_view=view, score_fmt=fmt)

def build_user_score(**args):
    mgr = {'music':UserScoreByMusic, 'tune':UserScoreByTune}[args['score_view']]
    score = mgr(args['user'], g.diffuser, g.date, g.diffdate, args['order'], g)
    return dict(score=score)
dependency.add(build_user_score, check_user)
dependency.add(build_user_score, build_user_score_args)

@knit.route('/<username>/score')
def user_score(username):
    return render_template('user/score.html',
         **dependency.build(build_user_score))

@knit.route('/<username>/rating')
def user_rating(username):
    return render_template('user/rating.html',
         **dependency.build(build_user_score))

@knit.route('/<username>/comparing')
def user_rating(username):
    return render_template('user/comparing.html',
         **dependency.build(build_user_score))


def build_user_stat(**kwargs):
    return dict(stats=USER_STATS, refs=USER_STAT_REFS())
dependency.add(build_user_stat, check_user)

@knit.route('/<username>/stat')
def user_stat(username):
    return render_template('user/stat.html',
         **dependency.build(build_user_stat))

def build_user(**kwargs): return {}
dependency.add(build_user, build_user_score)
dependency.add(build_user, build_user_stat)
dependency.add(build_user, build_difftool)

@knit.route('/<username>')
def user(username):
    return render_template('user/ .html',
         **dependency.build(build_user))


@knit.route('/<username>/toolbox')
def user_toolbox(username):
    return render_template('user/toolbox.html',
        **dependency.build(check_user))


DIF_TRANS = {'bsc':1, 'adv':2, 'ext':3, 'tot':0}
def check_tune(**args):
    mkey, dkey = args['music_key'], args['dif_key']
    if dkey.isnumeric():
        dif_id = int(dkey)
    else:
        try:
            dif_id = DIF_TRANS[dkey.lower()]
        except KeyError:
            error = NotFound()
            error.type = 'dif'
            error.msg = 'err_url_invalid_dif'
            raise error
    try:
        music_id = int(mkey)
        music = database.Music.by(music_id=music_id)
    except ValueError:
        music = database.Music.by_keyword(mkey, g.lang)
        if music is None:
            error = NotFound()
            error.type = 'music'
            error.msg = 'err_url_invalid_music'
            raise error

    subtitle = music.title
    l10n = music.localization(g.lang)
    if l10n:
        subtitle += ' (%s)' % l10n.text
    subtitle += ' ' + const.DIFFICULTY_NAMES2[dif_id]

    return dict(music=music, dif_id=dif_id, subtitle=subtitle)
dependency.add(check_tune, check_user)

def build_tune_detail(**args):
    user = args['user']
    m, dif_id = args['music'], args['dif_id']
    playdata_pool = user.playdata(date=g.date).\
        filter_by(music_id=m.id).\
        filter_by(dif_id=dif_id)
    try:
        playdata = playdata_pool[-1]
    except:
        playdata = None
    
    ext_hist = user.tune_history_ext((m.id, dif_id))
    try:
        playdetail = ext_hist[-1]
    except:
        playdetail = None
    # TODO: diffuser, diffdate, etc
    return dict(playdata=playdata, playdetail=playdetail) 
dependency.add(build_tune_detail, check_tune)

@knit.route('/<username>/tune/<music_key>_<dif_key>/detail')
def tune_detail(username, music_key, dif_key):
    return render_template('tune/detail.html',
        **dependency.build(build_tune_detail,
            music_key=music_key, dif_key=dif_key))


def build_tune_hist(**args):
    user = args['user']; userdata = args['userdata']
    m, dif_id = args['music'], args['dif_id']
    
    if g.diffusername is None and g.diffuser.friend_id in [0, user.friend_id]:
        dates = (user.userdata_pool[0].last_date, None)
    else:
        dates = None
    
    hist1 = user.tune_history([(m.id, dif_id)])
    hist2 = g.diffuser.tune_history([(m.id, dif_id)], dates=dates)
    histset = HistoryDataSet()
    histset.put_all(hist1, hist2, userdata.last_date, g.diffdata.last_date)
    
    return dict(history=histset, xfmt=args['score_fmt']) 
dependency.add(build_tune_hist, check_tune)
dependency.add(build_tune_hist, build_user_score_args) 

@knit.route('/<username>/tune/<music_key>_<dif_key>/hist')
def tune_hist(username, music_key, dif_key):
    return render_template('graph/hist.html',
        **dependency.build(build_tune_hist,
            music_key=music_key, dif_key=dif_key))


def build_tune_rank(**args):
    user = args['user']
    m, dif_id = args['music'], args['dif_id']
    rankset = RankingDataSet()
    rankset.put_all(
        database.PlayData.ranking([(m.id, dif_id)], user.friend_id, g.date))
    return dict(ranking=rankset, xfmt=args['score_fmt']) 
dependency.add(build_tune_rank, check_tune)
dependency.add(build_tune_rank, build_user_score_args) 

@knit.route('/<username>/tune/<music_key>_<dif_key>/rank')
def tune_rank(username, music_key, dif_key):
    return render_template('graph/rank.html',
        **dependency.build(build_tune_rank,
            music_key=music_key, dif_key=dif_key))


def build_tune(**args): return {}
dependency.add(build_tune, build_tune_detail)
dependency.add(build_tune, build_tune_hist)
dependency.add(build_tune, build_tune_rank)
dependency.add(build_tune, build_difftool)

@knit.route('/<username>/tune/<music_key>_<dif_key>')
def tune(username, music_key, dif_key):
    return render_template('tune/ .html',
        **dependency.build(build_tune, music_key=music_key, dif_key=dif_key))

DIST_STATS = ['card_name', 'jubility_icon', 'title', 'group_name', 'marker', 'background', 'last_location']
def check_stat(**args):
    stats = args['stat_keys'].split('+')
    view = 'dist' if stats[0] in DIST_STATS else 'num'
    fmt = filter.xform(stats[0])
    
    if not hasattr(args['userdata'], stats[0]):
        e = NotFound()
        e.type = 'stat'
        e.msg = 'err_invalid_statistics_name'
        raise e
   
    subtitle = ', '.join(map(filter.msg, stats))
    return dict(stats=stats, stat_view=view, xfmt=fmt, subtitle=subtitle)
dependency.add(check_stat, check_user)

def build_stat_hist_num(**args):
    user = args['user']; userdata = args['userdata']
    stat = args['stats'][0]

    hist1 = user.stat_history(stat)
    if g.diffusername:
        hist2 = g.diffuser.stat_history(stat)
    else:
        hist2 = []
    histset = HistoryDataSet()
    histset.put_all(hist1, hist2, userdata.last_date, g.diffdata.last_date)
    return dict(history=histset)

def build_stat_hist_dist(**args):
    histset = build_stat_hist_num(**args)['history']
    for k,item in histset.iteritems():
        if item.value is not None:
            histset[k] = item._replace(value=l10n(item.value))
        if item.diffvalue is not None:
            histset[k] = item._replace(diffvalue=l10n(item.diffvalue))
    return dict(history=histset)

build_stat_hist_funcs = {
    'dist': build_stat_hist_dist, 'num': build_stat_hist_num}
def build_stat_hist(**args):
    return build_stat_hist_funcs[args['stat_view']](**args)
dependency.add(build_stat_hist, check_stat)

@knit.route('/<username>/stat/<stat_keys>/hist')
def stat_hist(username, stat_keys):
    args = dependency.build(build_stat_hist, stat_keys=stat_keys)
    category = 'graph' if args['stat_view'] == 'num' else 'stat'
    template = category + '/hist.html'
    return render_template(template, **args)


def build_stat_rank(**args):
    user = args['user']
    stat = args['stats'][0]
    desc = stat not in ['achievement_rank']
    data = database.UserData.ranking(stat, user.friend_id, g.date, desc=desc)
    if not data:
        return {}
    rankset = RankingDataSet()
    rankset.put_all(data)
    return dict(ranking=rankset)
dependency.add(build_stat_rank, check_stat)

@knit.route('/<username>/stat/<stat_keys>/rank')
def stat_rank(username, stat_keys):
    return render_template('graph/rank.html',
        **dependency.build(build_stat_rank, stat_keys=stat_keys))


def build_stat_dist(**args):
    if args['stat_view'] == 'num': return {}
    user = args['user']
    stats = args['stats']
    length = len(stats)
    dist_type = '1' if length != 2 else '2'
    dataset_types = {'1':DistributionDataSet, '2':Distribution2DataSet}
    distset = dataset_types[dist_type](stats)
    distset.put_all(
        database.UserData.distribution(stats, user.friend_id, g.date))
    return dict(distribution=distset, dist_type=dist_type)
dependency.add(build_stat_dist, check_stat)

@knit.route('/<username>/stat/<stat_keys>/dist')
def stat_dist(username, stat_keys):
    return render_template('stat/dist.html',
        **dependency.build(build_stat_dist, stat_keys=stat_keys))
@knit.route('/<username>/stat/<stat_keys>/dist1')
def stat_dist(username, stat_keys):
    return render_template('stat/dist1.html',
        **dependency.build(build_stat_dist, stat_keys=stat_keys))
@knit.route('/<username>/stat/<stat_keys>/dist2')
def stat_dist(username, stat_keys):
    return render_template('stat/dist2.html',
        **dependency.build(build_stat_dist, stat_keys=stat_keys))

def build_stat(**args): return {}
dependency.add(build_stat, build_stat_hist)
dependency.add(build_stat, build_stat_rank)
dependency.add(build_stat, build_stat_dist)
dependency.add(build_stat, build_difftool)

@knit.route('/<username>/stat/<stat_keys>')
def stat(username, stat_keys):
    args = dependency.build(build_stat, stat_keys=stat_keys) 
    template = ' ' if args['stat_view'] == 'dist' else 'num'
    return render_template('stat/' + template + '.html', **args)


@knit.route('/<username>/request', methods=['POST'])
def request(username):
    args = dependency.build(check_user)
    user = args['user']
    database.session.add(database.UserRequest(user.friend_id))
    return render_template('request.html', **args)

@knit.route('/<username>/request/<music_key>', methods=['POST'])
def request_music(username, music_key):
    if music_key.isnumeric():
        music_id = int(music_key)
    else:
        music_id = Music.by_keyword(music_key, g.lang)
    args = dependency.build(check_user)
    user = args['user']
    try:
        database.MusicRequest.by(friend_id=user.friend_id)
        e = InternalServerError()
        e.type = 'request'
        e.title = 'err_request_denied'
        e.msg = 'err_request_duplicated'
        raise e
    except:
        pass
    database.session.add(database.MusicRequest(user.friend_id, music_id))
    return render_templace('request.html', **args)

@knit.route('/<username>/enroll/<friend_id>')
def enroll(username, friend_id):
    error = InternalServerError()
    error.type = 'enroll'
    
    if len(friend_id) != 14 or not friend_id.isnumeric()\
                            or not friend_id.startswith('2440'):
        error.msg = 'err_enroll_friend_id_knit'
        raise error
    if len(username) <= 2:
        error.msg = 'err_username_too_short'
        raise error
        
    friend_id = int(friend_id)
    query = database.User.filter(or_(
        database.User.friend_id == int(friend_id),
        database.User.alias.contains(username)))
    if query.count() > 0:
        user = query.first()
        if user.friend_id == friend_id:
            error.msg = 'err_enroll_duplicated_friend_id'
        elif user.alias == username:
            error.msg = 'err_enroll_duplicated_alias'
        else:
            error.msg = 'err_enroll_duplicate' # available?
        raise error

    database.session.add(database.User(friend_id, username))
    database.session.add(database.UserRequest(friend_id))
    return render_template('enroll.html', username=username)

@knit.route('/<username>/tbs')
def tbs(username):
    return tune(username=username, music_key='total', dif_key=u'0')

@knit.route('/<username>/raw/<page>')
def raw(username, page):
    path = 'http://jubeat.3rddev.org/knit/%s/raw/%s' % (username, page)
    return redirect(path)

@knit.route('/<username>/error')
def error(username, **args):
    error = args.get('error', None)
    if not hasattr(error, 'code'):
        error = InternalServerError()
        args['error'] = error
        args['errormsg'] = 'Critical error! If you found this page through any link of JubeatInfo, please report URL of this page to us. Thank you!'
    if error is None:
        error = NotFound()
    return render_template('error.html', **args), error.code

