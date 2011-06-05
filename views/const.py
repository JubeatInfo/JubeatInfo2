
from jubeatinfo.views import filter
msg = filter.msg

USER_STATS = [
    ('clear_rate', 'clear_percent', {'link':True, 'reverse':False}),
    ('fullcombo_rate', 'fullcombo_percent', {'link':True, 'reverse':False}),
    ('excellent_rate', 'excellent_percent', {'link':True, 'reverse':False}),
    ('effective_excellent_rate', 'effective_excellent_percent',
        {'link':True, 'reverse':False}),
    ('saved_rate', 'saved_percent', {'link':True, 'reverse':False}),
    ('matched_player_rate', 'matched_player_percent', 
        {'link':True, 'reverse':False}),
    ('matched_victory_rate', 'matched_victory_percent',
        {'link':True, 'reverse':False}),
    ('addiction_rate', 'addiction_percent',
        {'link':False, 'reverse':True}),
    ('concentration_degree', 'concentration_degree',
        {'link':False, 'reverse':False}),
    ('efficiency_degree', 'efficiency_degree',
        {'link':True, 'reverse':False}),
]
def USER_STAT_REFS():
    return [
        ('clear_rate', '%s / %s' %\
            (msg('clear_count'), msg('play_count'))),
        ('fullcombo_rate', '%s / %s' %\
            (msg('fullcombo_count'), msg('play_count'))),
        ('excellent_rate', '%s / %s' %\
            (msg('excellent_count'), msg('play_count'))),
        ('effective_excellent_rate', '%s / %s' %\
            (msg('excellent_count'), msg('fullcombo_count'))),
        ('saved_rate', '%s / (%s - %s)' %\
            (msg('saved_count'), msg('play_count'), msg('clear_count'))),
        ('matched_player_rate', '%s / %s' %\
            (msg('matched_player_count'), msg('play_count'))),
        ('matched_victory_rate', '%s / %s' %\
            (msg('matched_victory_count'), msg('matched_player_count'))),
        ('addiction_rate', '%s / %s (%s)' %\
            (msg('play_date_count'), msg('member_date_count'),
                msg('addiction_rate-note'))),
        ('concentration_degree', '%s / %s' %\
            (msg('play_count'), msg('play_date_count'))),
        ('efficiency_degree', '%s / %s' %\
            (msg('achievement_point'), msg('play_count')))
    ]
