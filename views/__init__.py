
# -*- coding: utf-8 -*-
from jubeatinfo import app

import flask
from flask import Markup
from flask import request
from flask import g
from flask import url_for
from flask import render_template
from werkzeug.exceptions import NotFound, InternalServerError

from jubeatinfo import database
from jubeatinfo import localization
from jubeatinfo.lib import NamedDict
import jubeatinfo.const
import jubeatinfo.views.filter

def modules():
    return dict(knit=knit)

def redirect(url, **args):
    return flask.redirect(url.encode('utf-8'), **args)

@app.before_request
def before_request():
    g.const = jubeatinfo.const
    g.path = request.path
    g.getargs = request.args
    g.lang = request.args.get('lang', None)
    if g.lang is None:
        g.lang = request.accept_languages.best_match(['en', 'ko', 'zh-tw'])
    if g.lang is None:
        g.lang = 'en'
    path_comps = request.path.split('/')
    g.info_ver = path_comps[1]
    try:
        g.username = path_comps[2]
    except:
        g.username = None
    g.date = request.args.get('date')
    g.diffdate = request.args.get('diff_date')
    g.diffusername = g.getargs.get('rival')
    
    diffusername = g.diffusername
    if diffusername is None:
        diffusername = g.username if g.diffdate else 'AVERAGE'
    try:
        g.diffuser = database.User.by(alias=diffusername)
    except:
        g.diffuser = database.User.by(friend_id=-1)
    diffdatadate = g.diffdate if g.username == diffusername else g.date
    g.diffdata = g.diffuser.userdata(date=diffdatadate)


@app.route('/')
def index():
    return redirect(url_for('knit.index'), code=307)

@app.route('/select')
def select():
    g.info_ver = request.args.get('ver')
    if not g.info_ver in modules().keys():
        flask.abort(404)
    username = request.args.get('alias')
    url = url_for(g.info_ver + '.user', username=username) +\
        filter.params(ver=None, alias=None)
    return redirect(url)

@app.route('/enroll')
def enroll():
    g.info_ver = request.args.get('ver')
    if not g.info_ver in modules().keys():
        flask.abort(404)
    
    username = request.args.get('alias')
    friend_id = request.args.get('friend_id')
    if not username or not friend_id:
        error = NotFound()
        error.type = 'enroll'
        error.msg = 'err_no_alias' if not username else\
                    'err_enroll_friend_id'
        raise error
    url = url_for(g.info_ver + '.enroll',
        username=username, friend_id=friend_id)
    return redirect(url)

@app.route('/static/<filename>')
def static(filename):
    return app.send_static_file(filename)

@app.route('/images/<filename>')
def static_image(filename):
    return static('images/'+filename)

@app.route('/favicon.ico')
def favicon():
    return static_image('favicon.ico')

@app.errorhandler(404)
def error404(e):
    mods = modules()
    username=getattr(g, 'username', None),
    args = NamedDict(error=e)
    msg = getattr(e, 'msg', None)
    if msg:
        args.errormsg = msg
    if g.info_ver in mods.keys():
        args.username = username
        return mods[g.info_ver].error(**args)
    g.username = None
    args.errormsg = filter.msg('err_url_invalid_info_ver')
    return mods[jubeatinfo.const.INFO_VERSION].error(username=None, **args)

@app.errorhandler(405)
def error405(e):
    mods = modules()
    args = NamedDict(username=g.username, error=e)
    msg = getattr(e, 'msg', None)
    if msg:
        args.errormsg = msg
    return mods[g.info_ver].error(**args)

@app.errorhandler(500)
def error500(e):
    mods = modules()
    args = NamedDict(username=g.username, error=e)
    args.errormsg = filter.msg(getattr(e, 'msg', 'err_unknown'))
    return mods[g.info_ver].error(**args)

