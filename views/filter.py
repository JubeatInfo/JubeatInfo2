
# -*- coding: utf-8 -*-
import os
import locale
from copy import deepcopy
from jubeatinfo import app
from flask import g
from flask import url_for
from flask import Markup
from jubeatinfo import localization

@app.template_filter('msg')
def msg(key, params=None):
    msg = localization.message(g.lang, key)
    if params is not None:
        try:
            msg %= params
        except:
            msg += params
    return Markup(msg)

@app.template_filter('l10n')
def l10n(value):
    return localization.contents(g.lang, value)

@app.template_filter('mtime')
def mtime(filename):
    return os.path.getmtime('/home/toepeu/jubeatinfo/static/' + filename)
    return os.path.getmtime(os.path.abspath(__name__.split('.')[0] + \
        '/static/' + filename))

@app.template_filter('numeric_filter')
def numeric_filter(places=0):
    def numeric(num, places=places):
        if num is None: return 'N/A'
        current_locale = locale.getlocale()
        locale.setlocale(locale.LC_NUMERIC, '')
        res = locale.format("%.*f", (places, num), True)
        #locale.setlocale(current_locale)
        return Markup(res)
    return numeric

app.jinja_env.filters['numeric'] = numeric = numeric_filter()

@app.template_filter('percent')
def percent(num):
    if num is None: return 'N/A'
    return "%.2f%%" % (num * 100)

XFORM_PROTOS = {
    'natural': {
        'mult': 1, 'digits': 0, 'sign': 0,
        'prefix':'', 'suffix':'', 'flip':False },
    '-natural': {
        'mult': 1, 'digits': 0, 'sign': 0,
        'prefix':'', 'suffix':'', 'flip':True },
    'real1': {
        'mult': 1, 'digits': 2, 'sign': 0,
        'prefix':'', 'suffix':'', 'flip':False },
    'real2': {
        'mult': 1, 'digits': 2, 'sign': 0,
        'prefix':'', 'suffix':'', 'flip':False },
    '+real2': {
        'mult': 1, 'digits': 2, 'sign': 1,
        'prefix':'', 'suffix':'', 'flip':False },
    'rank': {
        'mult': 1, 'digits': 0, 'sign': 0,
        'prefix':'#', 'suffix':'', 'flip':True },
    'percent': {
        'mult': 100, 'digits': 2, 'sign': 0,
        'prefix':'', 'suffix':'%', 'flip':False },
    '-percent': {
        'mult': 100, 'digits': 2, 'sign': 0,
        'prefix':'', 'suffix':'%', 'flip':True },
}
XFORMS = {
    'jubility': 'real2',
    'jubility_diff': '+real2',
    'achievement_rank': 'rank',
    'matched_victory_rate': 'percent',
    'saved_count': '-natural',
    'concentration_degree': 'real2',
    'efficiency_degree': 'real1',
}

@app.template_filter('xform')
def xform(key):
    xform = key
    try:
        xform = XFORMS[xform]
    except:
        if xform.endswith('_rate'):
            xform = 'percent'
        elif not xform in XFORM_PROTOS.keys():
            xform = 'natural'
    xform = XFORM_PROTOS[xform]
    return xform

@app.template_filter('xformat')
def xformat(val, fmt):
    if val is None: val = 0 if not fmt['flip'] else float('Inf')
    w = numeric_filter(fmt['digits'])(val * fmt['mult'])
    try:
        w = {
            1: '+' if val >= 0 else '',
            2: '+' if val > 0 else '' if val < 0 else '±'
        }[fmt['sign']] + w
    except:
        pass
    return fmt['prefix'] + w + fmt['suffix']

@app.template_filter('if')
def if_(true_val, cond, false_val=''):
    return true_val if cond else false_val

def params_dict(*args, **kwargs):
    params = {}
    for key in g.getargs:
        if not args or key in args:
            params[key] = g.getargs.get(key)
    for key,val in kwargs.iteritems():
        if val is not None:
            params[key] = val
        else:
            if key in params.keys():
                del(params[key])
    return params

@app.template_filter('params')
def params(*args, **kwargs):
    params = params_dict(*args, **kwargs)
    values = []
    for key,val in params.iteritems():
        values += [key+'='+val]
    return Markup('?' + '&'.join(values) if values else '')

@app.template_filter('params_hidden_value')
def params_hidden_value(depth=0, *args, **kwargs):
    params = params_dict(*args, **kwargs)
    values = []
    depthtab = '\t' * depth
    for key,val in params.iteritems():
        values += [depthtab +
            '<input name="%s" type="hidden" value="%s" />\n' % (key, val)]
    return Markup(''.join(values))

@app.template_filter('link_stat')
def link_stat(key, label=None):
    if label is None: label = key
    return Markup('<a href="%s" title="%s">%s</a>') % \
        (url_for('stat', username=g.username, stat_keys=key) + params(order=None, mode=None),
         msg(key), msg(label))

@app.template_filter('link_statrank')
def link_statrank(key, label=None):
    if label is None: label = key
    return Markup('<a href="%s" title="%s">%s</a>') % \
        (url_for('stat', username=g.username, stat_keys=key) + params(order=None, mode=None),
         msg(key), msg(label))

@app.template_filter('user_stat_diff')
def user_stat_diff(key, reverse=False):
    fmt = xform(key)
    keyval = getattr(g.userdata, key)
    title = '<a href="%s" title="%s">%s</a>' % \
        (url_for('stat', username=g.username, stat_keys=key) + params(), key, xformat(keyval, fmt))
    res = '<strong>' + title + '</strong>'
    if g.diffusername is not None or g.diffdate is not None:
        diffval = getattr(g.diffdata, key)
        res += '<span>(</span><span class="ip">%s</span>' % \
            xformat(diffval, fmt)
        try:
            valdiff = keyval - diffval
        except:
            valdiff = None
        diffclass = 'iu' if valdiff > 0 else 'id' if valdiff < 0 else 'in'
        if reverse: diffclass = {'iu':'id', 'id':'iu', 'in':'in'}[diffclass]
        diff_fmt = deepcopy(fmt); diff_fmt['sign'] = 2; diff_fmt['prefix'] = ''
        res += '<span class="%s">%s</span>' % (diffclass, xformat(valdiff, diff_fmt))
    return Markup(res)

@app.template_filter('link_order')
def link_order(key, label=None, desc=False):
    icons = {True:u'▼', False:u'▲'}
    current_key = g.getargs.get('order', '-version')
    check_key = alt_key = key
    if desc: 
        check_key = '-' + check_key
    else:
        alt_key = '-' + alt_key
    key_matched = current_key == check_key
    link_key = check_key if not key_matched else alt_key
    if label is None: label = 'order-' + key
    title = msg(label)
    
    return Markup('<a href="%s"%s>%s%s</a>') %\
        (params(order=link_key), Markup(' class="current"') if key_matched else '', title, icons[desc ^ key_matched])

app.jinja_env.globals.update(msg=msg, l10n=l10n, mtime=mtime,
    numeric=numeric, xform=xform, xformat=xformat,
    params=params, params_hidden_value=params_hidden_value,
    link_order=link_order,
    link_stat=link_stat, link_statrank=link_statrank,
    user_stat_diff=user_stat_diff)


