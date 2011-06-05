
INFO_VERSION = 'knit'

TOTAL_MUSIC_ID = 0
AVERAGE_MUSIC_ID = 1

MAX_VERSION = 5
VERSION_NAMES = ['', 'Jubeat', 'Ripples', 'Ripples Append', 'Knit', 'Knit Append']
VERSION_KEYS = [None, 'jb', 'rp', 'rpap', 'kn', 'knap']
VERSION_CLASSES = [None, 'Jubeat', 'Ripples', 'Ripples', 'Knit', 'Knit']

VERSION_RANGE = xrange(1, MAX_VERSION + 1)
VERSION_RANGE2 = xrange(0, MAX_VERSION + 1)

DIFFICULTY_KEYS = {1:'bsc', 2:'adv', 3:'ext'}
DIFFICULTY_NAMES = {1:'BASIC', 2:'ADVANCED', 3:'EXTREME'}

DIFFICULTY_KEYS2 = {0:'tot', 1:'bsc', 2:'adv', 3:'ext'}
DIFFICULTY_NAMES2 = {0:'TOTAL', 1:'BASIC', 2:'ADVANCED', 3:'EXTREME'}

DIFFICULTY_RANGE = xrange(1, 4)
DIFFICULTY_RANGE2 = xrange(0, 4)

GRADES = {
    1000000:'EXC', 980000:'SSS', 950000:'SS', 900000:'S', 850000:'A',
    800000:'B', 700000:'C', 500000:'D', 0:'E', None:'-'
}

GRADE_KEYS = [1000000, 980000, 950000, 900000, 850000, 800000, 700000, 500000, 0, None]

def GRADE_KEY_BY_SCORE(score):
    for key in GRADE_KEYS:
        if score >= key:
            return key

KNIT_IMAGE_PREFIX = 'https://www.ea-pass.konami.net/contents/jubeat/knit/'

