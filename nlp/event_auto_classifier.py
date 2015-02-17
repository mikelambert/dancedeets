# -*-*- encoding: utf-8 -*-*-

import datetime
import logging
try:
    import re2
    import re2 as re
except ImportError:
    logging.info("Could not import re2, falling back to re.")
    re2 = None
    import re

from . import event_classifier
from . import keywords
from . import regex_keywords
from . import rules
from util import dates


# house side?
# lock side?
# experimental side?
# TODO: make sure this doesn't match... 'mc hiphop contest'

start_judge_keywords_regex = regex_keywords.make_regexes_raw(rules.FULL_JUDGE.as_expanded_regex(), wrapper='^[^\w\n]*%s', flags=re.MULTILINE)

def has_list_of_good_classes(classified_event):
    if not classified_event.is_dance_event():
        return (False, 'not a dance event')

    # if title is good strong keyword, and we have a list of classes:
    # why doesn't this get found by the is_workshop title classifier? where is our "camp" keyword
    # http://www.dancedeets.com/events/admin_edit?event_id=317006008387038

    #(?!20[01][05])
    time = r'\b[012]?\d[:.,h]?(?:[0-5][05])?(?:am|pm)?\b'
    time_with_minutes = r'\b[012]?\d[:.,h]?(?:[0-5][05])(?:am|pm)?\b'
    time_to_time = r'%s ?(?:to|do|до|til|till|alle|a|-|[^\w,.]) ?%s' % (time, time)

    text = classified_event.search_text
    club_only_matches = classified_event.processed_text.get_tokens(keywords.CLUB_ONLY)
    if len(club_only_matches) > 2:
        return False, 'too many club keywords: %s' % club_only_matches
    title_wrong_style_matches = classified_event.processed_title.get_tokens(keywords.DANCE_WRONG_STYLE)
    if title_wrong_style_matches:
        return False, 'wrong style in the title: %s' % title_wrong_style_matches
    lines = text.split('\n')
    idx = 0
    schedule_lines = []
    while idx < len(lines):
        first_idx = idx
        while idx < len(lines):
            line = lines[idx]
            # if it has
            # grab time one and time two, store diff
            # store delimiters
            # maybe store description as well?
            # compare delimiters, times, time diffs, styles, etc
            times = re.findall(time_to_time, line)
            if not times or len(line) > 80:
                if idx - first_idx >= 1:
                    schedule_lines.append(lines[first_idx:idx])
                break
            idx += 1
        first_idx = idx
        while idx < len(lines):
            line = lines[idx]
            times = re.findall(time, line)
            # TODO(lambert): Somehow track "1)" that might show up here? :(
            times = [x for x in times if x not in ['1.', '2.']]
            if not times or len(line) > 80:
                if idx - first_idx >= 3:
                    schedule_lines.append(lines[first_idx:idx])
                break
            idx += 1
        idx += 1

    for sub_lines in schedule_lines:
        good_lines = []
        if not [x for x in sub_lines if re.search(time_with_minutes, x)]:
            continue
        for line in sub_lines:
            proc_line = event_classifier.StringProcessor(line, classified_event.boundaries)
            proc_line.tokenize(keywords.AMBIGUOUS_DANCE_MUSIC)
            dance_class_style_matches = proc_line.get_tokens(rules.GOOD_DANCE)
            dance_and_music_matches = proc_line.get_tokens(keywords.AMBIGUOUS_DANCE_MUSIC)
            manual_dancers = proc_line.get_tokens(rules.MANUAL_DANCER[keywords.STRONG])
            dance_wrong_style_matches = event_classifier.all_regexes['dance_wrong_style_title_regex'][classified_event.boundaries].findall(line)
            # Sometimes we have a schedule with hiphop and ballet
            # Sometimes we have a schedule with hiphop and dj and beatbox/rap (more on music side)
            # Sometimes we have a schedule with hiphop, house, and beatbox (legit, crosses boundaries)
            # TODO: Should do a better job of classifying the ambiguous music/dance types, based on the presence of non-ambiguous dance types too
            if (dance_class_style_matches or manual_dancers or dance_and_music_matches) and not dance_wrong_style_matches:
                good_lines.append(dance_class_style_matches + manual_dancers + dance_and_music_matches)
        start_time = dates.parse_fb_start_time(classified_event.fb_event)
        end_time = dates.parse_fb_end_time(classified_event.fb_event)
        if len(good_lines) > len(sub_lines) / 10 and (not end_time or end_time.time() > datetime.time(12) or end_time - start_time > datetime.timedelta(hours=12)):
            return True, 'found good schedule: %s: %s' % ('\n'.join(sub_lines), good_lines)
    return False, ''

def find_competitor_list(classified_event):
    text = classified_event.search_text
    results = re.search(r'\n0*1[^\d].+\n^0*2[^\d].+\n(?:^\d+.+\n){2,}', text, re.MULTILINE)
    if results:
        numbered_list = results.group(0)
        num_lines = numbered_list.count('\n')
        if len(re.findall(r'\d ?[.:h] ?\d\d|\bam\b|\bpm\b', numbered_list)) > num_lines / 4:
            return False # good list of times! workshops, etc! performance/shows/club-set times!
        processed_numbered_list = event_classifier.StringProcessor(numbered_list, classified_event.boundaries)
        keyword_list = [
            keywords.CLASS,
            keywords.N_X_N,
            keywords.BATTLE,
            keywords.OBVIOUS_BATTLE,
            keywords.AUDITION,
            keywords.CYPHER,
            keywords.JUDGE,
            keywords.AMBIGUOUS_CLASS,
        ]
        processed_numbered_list.tokenize_all(*keyword_list)
        event_keywords = processed_numbered_list.find_with_rule(rules.EVENT)
        if len(event_keywords) > num_lines / 8:
            return False
        if classified_event.processed_text.get_tokens(keywords.WRONG_NUMBERED_LIST):
            return False
        if num_lines > 10:
            return True
        else:
            lines = numbered_list.split('\n')
            qualified_lines = len([x for x in lines if re.search(r'[^\d\W].*[-(]', x)])
            if qualified_lines > num_lines / 2:
                return True
            for type in ['crew', 'pop|boog', 'lock', 'b\W?(?:boy|girl)']:
                qualified_lines = len([x for x in lines if re.search(type, x)])
                if qualified_lines > num_lines / 8:
                    return True
            if classified_event.boundaries == regex_keywords.WORD_BOUNDARIES: # maybe separate on kana vs kanji?
                avg_words = 1.0 * sum([len([y for y in x.split(' ')]) for x in lines]) / num_lines
                if avg_words < 3:
                    return True
    return False

# TODO: accumulate reasons why we did/didn't accept. each event has a story
# TODO: also track "was a battle, but not sure about kind". good for maybe-queue.
# TODO: the above is useful for "ish" keywords, where if we know its a dance-event due to the magic bit, and it appears to be battle-ish-but-not-sure-about-dance-ish, then mark it battle-ish
# TOOD: in an effort to simplify, can we make a "battle-ish" bit be computed separately, and then try to figure out if it's dance-y after that using other keywords?
# TODO: If it has certain battle names in title, include automatically? redbull bc one cypher, etc

#TODO: UNUSED!
def is_any_battle(classified_event):
    search_text = classified_event.final_search_text
    has_competitors = find_competitor_list(classified_event)
    has_start_judges = start_judge_keywords_regex[classified_event.boundaries].search(search_text)
    has_n_x_n_battle = (
        classified_event.processed_text.count_tokens(keywords.BATTLE) and
        classified_event.processed_text.count_tokens(keywords.N_X_N)
    )
    no_wrong_battles_processed = classified_event.processed_text.delete_with_rule(rules.WRONG_BATTLE)
    has_dance_battle = (
        no_wrong_battles_processed.find_with_rule(rules.DANCE_BATTLE) and
        not classified_event.processed_title.get_tokens(keywords.BAD_COMPETITION_TITLE_ONLY)
    )
    return has_competitors or has_start_judges or has_n_x_n_battle or has_dance_battle

def is_battle(classified_event):
    if not classified_event.is_dance_event():
        return (False, 'not a dance event')

    search_text = classified_event.final_search_text
    has_sparse_keywords = classified_event.calc_inverse_keyword_density >= 5.2
    has_competitors = find_competitor_list(classified_event)
    #print has_competitors, has_sparse_keywords, classified_event.calc_inverse_keyword_density
    if not has_competitors and has_sparse_keywords:
        return (False, 'relevant keywords too sparse')
    
    no_wrong_battles_processed = classified_event.processed_text.delete_with_rule(rules.WRONG_BATTLE)
    has_dance_battle = no_wrong_battles_processed.find_with_rule(rules.DANCE_BATTLE)
    has_good_dance_battle = no_wrong_battles_processed.find_with_rule(rules.GOOD_DANCE_BATTLE)

    has_n_x_n = classified_event.processed_text.count_tokens(keywords.N_X_N)
    has_battle = classified_event.processed_text.count_tokens(keywords.BATTLE)
    has_wrong_battle = classified_event.processed_text.find_with_rule(rules.WRONG_BATTLE)
    is_wrong_competition_title = classified_event.processed_title.get_tokens(keywords.BAD_COMPETITION_TITLE_ONLY)
    is_wrong_style_battle_title = classified_event.processed_title.find_with_rule(rules.DANCE_WRONG_STYLE_TITLE)
    has_many_real_dance_keywords = len(set(classified_event.real_dance_matches + classified_event.manual_dance_keywords_matches)) > 1
    has_start_judge = start_judge_keywords_regex[classified_event.boundaries].findall(search_text)

    #print rules.WRONG_BATTLE.as_expanded_regex().encode('utf8')
    #print has_dance_battle
    #print is_wrong_competition_title
    #print is_wrong_style_battle_title
    #print has_wrong_battle
    #print has_good_dance_battle
    #print classified_event.real_dance_matches
    #print classified_event.manual_dance_keywords_matches
    #print classified_event.processed_text.get_tokenized_text().encode('utf8')
    #print classified_event.processed_text.match_on_word_boundaries
    #print has_start_judge
    #print classified_event.real_dance_matches + classified_event.manual_dance_keywords_matches
    #print has_many_real_dance_keywords
    if not has_good_dance_battle and not (classified_event.real_dance_matches or classified_event.manual_dance_keywords_matches):
        return (False, 'no strong dance keywords')

    if has_good_dance_battle and not is_wrong_competition_title and not is_wrong_style_battle_title:
        return (True, 'real dance-style battle/comp! %s' % has_good_dance_battle)
    elif has_dance_battle and not is_wrong_competition_title and not is_wrong_style_battle_title and not has_wrong_battle:
        return (True, 'good-style real dance battle/comp! %s with keywords %s' % (has_dance_battle, (classified_event.real_dance_matches or classified_event.manual_dance_keywords_matches)))
    elif has_n_x_n and has_battle and not has_wrong_battle:
        return (True, 'battle keyword, NxN, good dance style')
    elif has_competitors and has_many_real_dance_keywords and not has_wrong_battle:
        return (True, 'has a list of competitors, and some strong dance keywords')
    elif has_start_judge and not has_wrong_battle:
        return (True, 'no ambiguous wrong-battle-style keywords')
    elif has_start_judge and has_many_real_dance_keywords:
        return (True, 'had some ambiguous keywords, but enough strong dance matches anyway')
    return (False, 'no judge/jury or battle/NxN')

def is_audition(classified_event):
    if not classified_event.is_dance_event():
        return (False, 'not a dance event')

    has_audition = classified_event.processed_title.get_tokens(keywords.AUDITION)
    has_good_dance_title = classified_event.processed_title.get_tokens(rules.GOOD_DANCE)
    has_extended_good_crew_title = classified_event.processed_title.get_tokens(rules.MANUAL_DANCER[keywords.STRONG_WEAK])


    has_good_dance = classified_event.processed_text.get_tokens(rules.GOOD_DANCE)
    has_wrong_style = classified_event.processed_text.get_tokens(rules.DANCE_WRONG_STYLE_TITLE)
    has_wrong_audition = classified_event.processed_text.get_tokens(keywords.WRONG_AUDITION)

    if has_audition and (has_good_dance_title or has_extended_good_crew_title):
        return (True, 'has audition with strong title')
    elif has_audition and has_good_dance and not has_wrong_style and not has_wrong_audition:
        return (True, 'has audition with good-and-not-bad dance style')
    return (False, 'no audition')

# Workshop examples to search for:
# - (Locking) 9.30am to 11.00am- 
# - (Popping) 11.15am to 12.45pm 

# - 16:30 - 17:30 - Maniek
# - 17:40 - 18:40 - Sandy
# - 18:50 - 19:50 - collabo Sandy & Maniek

# 14H00 – 15H30 DANCEHALL
# 15H30 – 17H00 HIP-HOP/NEWSTYLE
# 17H00 – 18H30 HOUSEDANCE
# 18H30 – 20H00 POPPING

# -------- 17:00 CLASE GRATUITA de House Dance con Crazy Toe 

# Sala 2 Danza Contemporanea Inter Atzewi Dance
# Company
# 17:30-18:50    Sala 1    Hip Hop princ Sacchetta Marcello+
# Raimondo
# Sala 2    Fusion inter     Antonio Fiore
# 19:00-20:20    Sala 1    Hip Hop Inter Sacchetta Marcello+     Raimondo

# = pondělí 19:15-20:45 – step
# = úterý 19:00-20:30 – street dance
# = úterý 19:00-20:00 – společenské tance pro páry
# = středa 19:00-20:30 – jazz dance

# Kyle Hanagami - Hip Hop
# Desiree Robbins - Jazz
# Alex Wong - Ballet/Jazz
# Mikey Trasoras - Hip Hop

# Di 5. Juni 2012 
# Performance Practice / Workshop Hip-Hop
# 
# Mi 6. Juni 2012 
# Performance Practice / Workshop BodyParkour / Performance im öffentlichen Raum / Österreich TANZT - Abend 1 / Österreich TANZT – Eröffnungsfest im Café Publik

# Commercial Dance 
# Úterky od 29.5. - 26.6. v 18:30-19:30 hod. (60 min.)

# LEECO & GIANINNI - SATURDAY, JUNE 16, 2012 @ 4:30PM
# somehow combined with bios below?

# SATURDAY July 14th, 2012
# 11:00 -12:25 Krumpin - Valerie Chartier 
# 12:30 - 1:55 House - JoJo Diggs
# 2:30 - 3:55 Dancehall - Neeks
# 4:00 - 5:30 Waacking - Cherry & Ebony

# Workshops KRUMP - BigFreezee (Royal Skillz, Cracow)
#
# Warsztaty Bboying - S-kel (Universal Zulu Nation )
#
# Workshops Street Dance - Prices (Royal Skillz)

# 1-2:30pm - Sexy Caribbean moves (Kay-Ann Ward)
# 2:30-4pm - Hip Hop Boot Camp


# 'dancehall workshop' in title should work as-is? why not?

# ALREADY CONFIRMED INSTRUCTORS!
# As of 06.14.12
# Subject to Change
# 
# Nika Kjlun
# Mr. Lucky


def is_workshop(classified_event):
    trimmed_title = classified_event.processed_title.delete_with_rule(rules.WRONG_CLASS)
    has_class_title = trimmed_title.find_with_rule(rules.EXTENDED_CLASS)
    has_good_dance_class_title = trimmed_title.find_with_rule(rules.GOOD_DANCE_CLASS)

    has_non_dance_event_title = classified_event.processed_title.get_tokens(keywords.BAD_COMPETITION_TITLE_ONLY)
    has_good_dance_title = trimmed_title.find_with_rule(rules.GOOD_DANCE)
    has_extended_good_crew_title = trimmed_title.find_with_rule(rules.MANUAL_DANCER[keywords.STRONG_WEAK])
    has_wrong_style_title = event_classifier.all_regexes['dance_wrong_style_title_regex'][classified_event.boundaries].findall(classified_event.final_title)

    lee_lee_hiphop = 'lee lee' in classified_event.final_title and re.findall('hip\W?hop', classified_event.final_title)

    trimmed_text = classified_event.processed_text.delete_with_rule(rules.WRONG_CLASS)
    has_good_dance_class = trimmed_text.find_with_rule(rules.GOOD_DANCE_CLASS)
    has_good_dance = classified_event.processed_text.find_with_rule(rules.GOOD_DANCE)
    has_wrong_style = classified_event.processed_text.find_with_rule(rules.DANCE_WRONG_STYLE_TITLE)

    has_good_crew = classified_event.processed_text.get_tokens(rules.MANUAL_DANCER[keywords.STRONG])

    #print has_class_title
    #print has_good_dance_title
    #print has_extended_good_crew_title
    #print has_wrong_style_title

    #print classified_event.final_search_text
    #print classified_event.processed_text.get_tokenized_text()
    #print ''
    #print has_class_title
    #print has_wrong_style
    #print has_good_dance
    #print has_good_crew
    if has_class_title and (has_good_dance_title or has_extended_good_crew_title) and not has_wrong_style_title:
        return (True, 'has class with strong class-title: %s %s' % (has_class_title, (has_good_dance_title or has_extended_good_crew_title)))
    elif classified_event.is_dance_event() and has_good_dance_title and has_extended_good_crew_title and not has_wrong_style_title and not has_non_dance_event_title:
        return (True, 'has class with strong style-title: %s %s' % (has_good_dance_title, has_extended_good_crew_title))
    elif classified_event.is_dance_event() and lee_lee_hiphop and not has_wrong_style_title and not has_non_dance_event_title:
        return (True, 'has class with strong style-title: %s %s' % (has_good_dance_title, has_extended_good_crew_title))
    elif has_class_title and not has_wrong_style and (has_good_dance or has_good_crew):
        return (True, 'has dance class title: %s, that contains strong description %s' % (has_class_title, has_good_dance + has_good_crew))
    elif has_good_dance_class_title:
        return (True, 'has good dance class title: %s' % has_good_dance_class_title)
    elif has_good_dance_class and not has_wrong_style_title:
        return (True, 'has good dance class: %s' % has_good_dance_class)
    return (False, 'nothing')


def is_vogue_event(classified_event):
    # We use sets here to get unique keywords
    vogue_matches = set(classified_event.processed_text.get_tokens(keywords.VOGUE))
    easy_vogue_matches = set(classified_event.processed_text.get_tokens(keywords.EASY_VOGUE))
    match_count = len(vogue_matches) + 0.33 * len(easy_vogue_matches)
    if match_count > 2:
        return True, 'has vogue keywords: %s' % (vogue_matches.union(easy_vogue_matches))
    return False, 'not enough vogue keywords'

solo_lines_regex = None

def build_regexes():
    global solo_lines_regex

    if solo_lines_regex is not None:
        return

    event_classifier.build_regexes()

    solo_lines_regex = event_classifier.make_regexes([rules.GOOD_DANCE.as_expanded_regex(), rules.MANUAL_DANCER[keywords.STRONG].as_expanded_regex()])

def has_standalone_keywords(classified_event):
    build_regexes()

    text = classified_event.search_text
    good_matches = set()
    for line in text.split('\n'):
        alpha_line = re.sub(r'\W', '', line)
        if not alpha_line:
            continue
        remaining_line = solo_lines_regex[classified_event.boundaries].sub('', line)
        alpha_remaining_line = re.sub(r'\W', '', remaining_line)
        if 0.5 > 1.0 * len(alpha_remaining_line) / len(alpha_line):
            good_matches.add(solo_lines_regex[classified_event.boundaries].findall(line)[0]) # at most one keyword per line
    if len(good_matches) >= 2:
        return True, 'found good keywords on lines by themselves: %s' % set(good_matches)
    return False, 'no good keywords on lines by themselves'

def has_good_event_title(classified_event):
    non_dance_title_keywords = classified_event.processed_title.get_tokens(keywords.BAD_COMPETITION_TITLE_ONLY)
    wrong_battles_title = classified_event.processed_title.find_with_rule(rules.WRONG_BATTLE)
    title_keywords = classified_event.processed_title.find_with_rule(keywords.COMPETITION[keywords.STRONG])
    if title_keywords and not non_dance_title_keywords and not wrong_battles_title:
        return True, 'looks like a good event title: %s' % title_keywords
    return False, 'no good event title'

def has_good_djs_title(classified_event):
    non_dance_title_keywords = classified_event.processed_title.get_tokens(keywords.BAD_COMPETITION_TITLE_ONLY)
    wrong_battles_title = classified_event.processed_title.find_with_rule(rules.WRONG_BATTLE)
    title_keywords = event_classifier.all_regexes['good_djs_regex'][classified_event.boundaries].findall(classified_event.final_title)

    if title_keywords and not non_dance_title_keywords and not wrong_battles_title:
        return True, 'looks like a good dj title: %s' % title_keywords
    return False, 'no good dj title'

def is_performance_or_practice(classified_event):
    text = classified_event.processed_text.get_tokenized_text()

    performances_and_practices = []
    for line in text.split('\n'):
        pline = event_classifier.StringProcessor(line, classified_event.boundaries)
        if len(line) > 500:
            continue
        performances_and_practices.extend(pline.find_with_rule(rules.PERFORMANCE_PRACTICE))
    if performances_and_practices:
        return True, 'found good performance/practice keywords: %s' % performances_and_practices
    return False, 'no good keywords'

def is_intentional(classified_event):
    if 'dancedeets' in classified_event.final_search_text:
        return True, 'found dancedeets reference'
    return False, 'no dancedeets reference'

def is_auto_add_event(classified_event):
    result = is_intentional(classified_event)
    if result[0]:
        return result
    result = is_battle(classified_event)
    if result[0]:
        return result
    result = is_audition(classified_event)
    if result[0]:
        return result
    result = is_workshop(classified_event)
    if result[0]:
        return result
    result = has_list_of_good_classes(classified_event)
    if result[0]:
        return result
    result = is_vogue_event(classified_event)
    if result[0]:
        return result
    result = has_standalone_keywords(classified_event)
    if result[0]:
        return result
    result = has_good_event_title(classified_event)
    if result[0]:
        return result
    result = is_performance_or_practice(classified_event)
    if result[0]:
        return result
    return (False, 'nothing')

def is_bad_club(classified_event):
    has_battles = classified_event.processed_text.find_with_rule(rules.DANCE_BATTLE)
    has_style = classified_event.processed_text.find_with_rule(rules.GOOD_DANCE)
    has_manual_keywords = classified_event.processed_text.find_with_rule(rules.MANUAL_DANCE[keywords.STRONG_WEAK])
    has_cypher = classified_event.processed_text.count_tokens(keywords.CYPHER)

    has_other_event_title = classified_event.processed_title.get_tokens(keywords.EVENT)

    has_ambiguous_text = has_battles or has_style or has_manual_keywords or has_cypher
    if classified_event.processed_text.count_tokens(keywords.BAD_CLUB) and not has_ambiguous_text and not has_other_event_title:
        return True, 'has bad keywords: %s' % classified_event.processed_text.get_tokens(keywords.BAD_CLUB)
    return False, 'not a bad club'


def is_bad_wrong_dance(classified_event):
    dance_and_music_matches = classified_event.processed_text.get_tokens(keywords.AMBIGUOUS_DANCE_MUSIC)
    real_dance_keywords = set(classified_event.real_dance_matches + dance_and_music_matches)
    manual_keywords = classified_event.manual_dance_keywords_matches

    nodance_processed_text = event_classifier.StringProcessor(classified_event.search_text, classified_event.boundaries)
    nodance_processed_text.real_tokenize(rules.MANUAL_DANCE[keywords.STRONG])
    nodance_processed_text.real_tokenize(rules.GOOD_DANCE)
    weak_classical_dance_keywords = nodance_processed_text.get_tokens(keywords.SEMI_BAD_DANCE)
    strong_classical_dance_keywords = nodance_processed_text.find_with_rule(rules.DANCE_WRONG_STYLE_TITLE)

    has_house = classified_event.processed_text.get_tokens(keywords.HOUSE)
    club_only_matches = classified_event.processed_text.get_tokens(keywords.CLUB_ONLY)


    keyword_count = len(strong_classical_dance_keywords) + 0.5 * len(weak_classical_dance_keywords)

    just_free_style_dance = len(real_dance_keywords) == 1 and list(real_dance_keywords)[0].startswith('free')

    has_wrong_style_title = event_classifier.all_regexes['dance_wrong_style_title_regex'][classified_event.boundaries].findall(classified_event.final_title)
    has_decent_style = classified_event.processed_title.find_with_rule(rules.DECENT_DANCE)
    if has_wrong_style_title and not has_decent_style:
        return True, 'Title is too strong a negative, without any compensating good title keywords'
    elif not real_dance_keywords and not has_house and len(club_only_matches) <= 1 and len(manual_keywords) <= 1 and keyword_count >= 2:
        return True, 'Has strong classical keywords %s, but only real keywords %s' % (strong_classical_dance_keywords + weak_classical_dance_keywords, manual_keywords)
    elif keyword_count >= 2 and just_free_style_dance and not manual_keywords:
        return True, 'Has strong classical keywords %s with freestyle dance, but only dance keywords %s' % (strong_classical_dance_keywords + weak_classical_dance_keywords, real_dance_keywords.union(manual_keywords))
    return False, 'not a bad classical dance event'

def is_auto_notadd_event(classified_event, auto_add_result=None):
    result = auto_add_result or is_auto_add_event(classified_event)
    if result[0]:
        return False, 'is auto_add_event: %s' % result[1]

    result = is_bad_club(classified_event)
    if result[0]:
        return result
    result = is_bad_wrong_dance(classified_event)
    if result[0]:
        return result
    return False, 'not a bad enough event'