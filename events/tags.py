
FREESTYLE_CLUB = 'FREESTYLE_CLUB'
FREESTYLE_COMPETITION = 'FREESTYLE_COMPETITION'
FREESTYLE_PERFORMANCE = 'FREESTYLE_PERFORMANCE'
FREESTYLE_WORKSHOP = 'FREESTYLE_WORKSHOP'
FREESTYLE_AUDITION = 'FREESTYLE_AUDITION'
FREESTYLE_CLASS = 'FREESTYLE_CLASS'
FREESTYLE_SESSION = 'FREESTYLE_SESSION'
FREESTYLE_OTHER = 'FREESTYLE_OTHER'

CHOREO_PERFORMANCE = 'CHOREO_PERFORMANCE'
CHOREO_WORKSHOP = 'CHOREO_WORKSHOP'
CHOREO_AUDITION = 'CHOREO_AUDITION'
CHOREO_CLASS = 'CHOREO_CLASS'
CHOREO_CLUB = 'CHOREO_CLUB'
CHOREO_OTHER = 'CHOREO_OTHER'

STYLE_CHOREOHIPHOP = 'STYLE_CHOREOHIPHOP'
STYLE_BREAKING = 'STYLE_BREAKING'
STYLE_POPPING = 'STYLE_POPPING'
STYLE_LOCKING = 'STYLE_LOCKING'
STYLE_WAACKING = 'STYLE_WAACKING'
STYLE_HOUSE = 'STYLE_HOUSE'
STYLE_OLDHIPHOP = 'STYLE_OLDHIPHOP'
STYLE_OTHER = 'STYLE_OTHER'

FREESTYLE_EVENT = 'FREESTYLE'
FREESTYLE_EVENT_LIST = [
    (FREESTYLE_WORKSHOP, 'Workshop'),
    (FREESTYLE_AUDITION, 'Audition'),
    (FREESTYLE_PERFORMANCE, 'Performance'),
    (FREESTYLE_SESSION, 'Practice Session'),
    (FREESTYLE_COMPETITION, 'Battle'),
    (FREESTYLE_CLUB, 'Club'),
    (FREESTYLE_OTHER, 'Other'),
]

FREESTYLE_FAN_EVENTS = [FREESTYLE_PERFORMANCE, FREESTYLE_COMPETITION, FREESTYLE_OTHER]

CHOREO_EVENT = 'CHOREO'
CHOREO_EVENT_LIST = [
    (CHOREO_WORKSHOP, 'Workshop'),
    (CHOREO_AUDITION, 'Audition'),
    (CHOREO_PERFORMANCE, 'Performance'),
    (CHOREO_CLUB, 'Club'),
    (CHOREO_OTHER, 'Other'),
]
CHOREO_FAN_EVENTS = [CHOREO_PERFORMANCE, CHOREO_CLUB, CHOREO_OTHER]

EVENT_TYPE_LOOKUP = {}
EVENT_TYPE_LOOKUP.update(dict((x[0], 'Choreo %s' % x[1]) for x in CHOREO_EVENT_LIST))
EVENT_TYPE_LOOKUP.update(dict((x[0], 'Freestyle %s' % x[1]) for x in FREESTYLE_EVENT_LIST))

TIME_PAST = 'PAST'
TIME_FUTURE = 'FUTURE'

STYLES = [
    (STYLE_CHOREOHIPHOP, 'hiphop choreography, new-school hiphop, street jazz, jazz funk'),
    (STYLE_BREAKING, 'bboying, bgirling, breaking, breakdancing'),
    (STYLE_POPPING, 'popping, isolation, hitting, tutting, gliding, animation, robot'),
    (STYLE_LOCKING, 'locking'),
    (STYLE_WAACKING, 'waacking, punking, vogueing'),
    (STYLE_HOUSE, 'house dance'),
    (STYLE_OLDHIPHOP, '90s hiphop, middle school hiphop, new jack swing'),
    (STYLE_OTHER, 'other'),
]

STYLES_DICT = dict(STYLES)

# minimum age (18+, 21+)
# price
# ?

