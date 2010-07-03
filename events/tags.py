
FREESTYLE_CLUB = 'FREESTYLE_CLUB'
FREESTYLE_COMPETITION = 'FREESTYLE_COMPETITION'
FREESTYLE_PERFORMANCE = 'FREESTYLE_PERFORMANCE'
FREESTYLE_WORKSHOP = 'FREESTYLE_WORKSHOP'
FREESTYLE_CLASS = 'FREESTYLE_CLASS'
FREESTYLE_SESSION = 'FREESTYLE_SESSION'
FREESTYLE_OTHER = 'FREESTYLE_OTHER'

CHOREO_PERFORMANCE = 'CHOREO_PERFORMANCE'
CHOREO_WORKSHOP = 'CHOREO_WORKSHOP'
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
    (FREESTYLE_WORKSHOP, 'workshop, master class, audition, tryout'),
    (FREESTYLE_PERFORMANCE, 'performance, show'),
    (FREESTYLE_SESSION, 'practice session'),
    (FREESTYLE_COMPETITION, 'competition, battle, tournament'),
    (FREESTYLE_CLUB, 'club with cyphers'),
    (FREESTYLE_OTHER, 'other'),
]

CHOREO_EVENT = 'CHOREO'
CHOREO_EVENT_LIST = [
    (CHOREO_WORKSHOP, 'workshop, master class, audition, tryout'),
    (CHOREO_PERFORMANCE, 'performance, show, competition'),
    (CHOREO_CLUB, 'club with performances'),
    (CHOREO_OTHER, 'other'),
]

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

