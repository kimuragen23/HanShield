import json
import os
try:
    # when used as a package
    from . import hangul
except Exception:
    # when executed as script (top-level)
    import hangul
import re
import unicodedata

bad_words = []
normal_words = []
soft_search_words = []


class Utils:

    @staticmethod
    def get_position_all(message, search, is_string=True):
        indexes = []
        i = message.find(search)
        while i != -1:
            indexes.append(i)
            i = message.find(search, i + 1)

        if not is_string:
            return indexes

        string_poses = []
        for word_index in indexes:
            if word_index == -1:
                continue
            for _ in range(len(search)):
                string_poses.append(word_index)
                word_index += 1
        return string_poses

    @staticmethod
    def grab_couple(many_array):
        couple = []
        i = 0
        while True:
            if (len(many_array) - i) == 1:
                break
            couple.append([many_array[i], many_array[i + 1]])
            i += 1
            if i >= len(many_array):
                break
        return couple

    @staticmethod
    def word_to_array(word):
        return [c for c in word]

    @staticmethod
    def length_split(message, limit):
        if len(message) <= limit:
            return [message]
        fixed = []
        split_list = []
        current_length = 0
        full_length = len(message)
        while True:
            if current_length == full_length:
                if current_length != 0 and split_list:
                    fixed.append(''.join(split_list))
                    split_list = []
                break
            if current_length != 0 and current_length % limit == 0 and split_list:
                fixed.append(''.join(split_list))
                split_list = []
            split_list.append(message[current_length])
            current_length += 1
        return fixed

    @staticmethod
    def sort_map(input_map):
        return dict(sorted(input_map.items()))


class Tetrapod:

    @staticmethod
    def load(input_badwords,
             input_dictionary,
             input_soft_search_words,
             disable_auto_parse=None):
        global bad_words, normal_words, soft_search_words

        bad_words = input_badwords
        normal_words = input_dictionary
        soft_search_words = input_soft_search_words

        if disable_auto_parse is not False:
            Tetrapod.parse()
            Tetrapod.mapping()

    @staticmethod
    def load_file(bad_words_path, normal_words_path, soft_search_words_path):
        data = {}
        with open(bad_words_path, 'r', encoding='utf-8') as f:
            raw_bad = json.load(f).get('badwords', [])
            # expand nested components (same behavior as original JS recursiveList)
            data['badWords'] = Tetrapod.recursive_list(raw_bad)
        with open(normal_words_path, 'r', encoding='utf-8') as f:
            data['normalWords'] = json.load(f).get('dictionary', [])
        with open(soft_search_words_path, 'r', encoding='utf-8') as f:
            data['softSearchWords'] = json.load(f).get('badwords', [])
        Tetrapod.load(data['badWords'], data['normalWords'],
                      data['softSearchWords'])

    @staticmethod
    def default_load():
        base = os.path.dirname(__file__)
        bad_path = os.path.join(base, 'dictionary', 'bad-words.json')
        normal_path = os.path.join(base, 'dictionary', 'normal-words.json')
        soft_path = os.path.join(base, 'dictionary', 'soft-search-words.json')
        spam_path = os.path.join(base, 'dictionary', 'spam-words.json')
        config_path = os.path.join(base, 'config', 'spam-config.json')
        Tetrapod.load_file(bad_path, normal_path, soft_path)
        # load spam words if present
        try:
            with open(spam_path, 'r', encoding='utf-8') as f:
                Tetrapod.spam_words = json.load(f).get('spamwords', [])
        except Exception:
            Tetrapod.spam_words = []
        # load spam config (weights, threshold, whitelist)
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                Tetrapod.spam_config = json.load(f)
        except Exception:
            # default fallback
            Tetrapod.spam_config = {
                'threshold': 4,
                'weights': {
                    'url': 3,
                    'email': 2,
                    'phone': 2,
                    'repeated': 1,
                    'keyword': 1,
                    'ham_keyword_subtract': 1
                },
                'whitelist_phrases': [],
                'ham_keywords': []
            }

    @staticmethod
    def parse():
        global parsed_bad_words
        parsed_bad_words = []
        for w in bad_words:
            parsed_bad_words.append(Utils.word_to_array(w))

    @staticmethod
    def mapping():
        global bad_words_map, normal_words_map, soft_search_words_map
        bad_words_map = {}
        normal_words_map = {}
        soft_search_words_map = {}
        for w in bad_words:
            bad_words_map[w] = True
        for w in normal_words:
            normal_words_map[w] = True
        for w in soft_search_words:
            soft_search_words_map[w] = True

    @staticmethod
    def is_bad(message):
        return len(Tetrapod.find(message, False)) != 0

    @staticmethod
    def find(message, need_multiple_check=False, split_check=15):
        total_result = []
        if split_check is None:
            split_check = 15
        messages = Utils.length_split(
            message, split_check) if split_check != 0 else [message]
        for msg in messages:
            current = Tetrapod.native_find(msg, need_multiple_check)
            if need_multiple_check:
                if current is not None:
                    for f in current['founded']:
                        total_result.append(f)
            else:
                if current is not None:
                    total_result.append(current['founded'])
        return total_result

    @staticmethod
    def native_find(message, need_multiple_check=False):
        normal_word_positions = {}
        founded_bad_words = []
        founded_bad_word_positions = []

        # find positions of normal words to exclude
        for nw in normal_words:
            if len(message) == 0:
                break
            for pos in Utils.get_position_all(message, nw):
                if pos != -1:
                    normal_word_positions[pos] = True

        # iterate parsed bad words (array of chars)
        for bad_word in parsed_bad_words:
            find_count = set()
            bad_word_positions = []

            for bad_char in bad_word:
                bad_one = str(bad_char).lower()
                # search each char in message
                for idx, ch in enumerate(message):
                    if idx in normal_word_positions:
                        continue
                    unsafe_one = str(ch).lower()
                    if bad_one == unsafe_one:
                        find_count.add(bad_one)
                        bad_word_positions.append(idx)
                        break

            if len(bad_word) == len(find_count):
                # check shuffle
                is_shuffled = False
                sorted_positions = sorted(bad_word_positions)
                if sorted_positions != bad_word_positions:
                    is_shuffled = True
                    bad_word_positions = sorted_positions

                is_need_to_pass = False
                for diff_ranges in Utils.grab_couple(bad_word_positions):
                    diff = ''
                    for di in range(diff_ranges[0] + 1, diff_ranges[1]):
                        diff += message[di]

                    if is_shuffled:
                        if not Tetrapod.shuffled_message_filter(diff):
                            is_need_to_pass = True

                if is_need_to_pass:
                    continue

                founded = ''.join(bad_word)
                if not need_multiple_check:
                    return {
                        'founded': founded,
                        'positions': bad_word_positions
                    }
                founded_bad_words.append(founded)
                founded_bad_word_positions.append(bad_word_positions)

        if not need_multiple_check:
            return None
        return {
            'founded': founded_bad_words,
            'positions': founded_bad_word_positions
        }

    @staticmethod
    def fix(message, replace_character='*'):
        fixed = message
        founded = Tetrapod.find(message, True)
        for fw in founded:
            for ch in fw:
                fixed = fixed.replace(ch, replace_character)
        return fixed

    @staticmethod
    def is_exist_normal_word(word):
        return normal_words_map.get(word) is not None

    @staticmethod
    def add_normal_words(words):
        for w in words:
            if not w:
                continue
            if Tetrapod.is_exist_normal_word(w):
                continue
            normal_words_map[w] = True
            normal_words.append(w)

    @staticmethod
    def shuffled_message_filter(message, is_char=False):
        for ch in message:
            d = hangul.disassemble(ch)
            if len(d) > 0 and d[0] == 'ㅇ':
                continue
            if hangul.is_complete(ch):
                return False
        return True

    @staticmethod
    def recursive_component(data):
        # data: [before_list, after_list]
        for i in range(2):
            j = 0
            while j < len(data[i]):
                item = data[i][j]
                if isinstance(item, list):
                    solved = Tetrapod.recursive_component(item)
                    data[i][j] = None
                    data[i].extend(solved)
                j += 1

        solved_data = []
        for before in data[0]:
            if before is None:
                continue
            for after in data[1]:
                if after is None:
                    continue
                solved_data.append(before + after)
        return solved_data

    @staticmethod
    def recursive_list(lst, default_type=str):
        rebuild = []
        for item in lst:
            if isinstance(item, default_type):
                rebuild.append(item)
            else:
                rebuild.extend(Tetrapod.recursive_component(item))
        return rebuild

    # -------------------- Spam detection helpers --------------------
    @staticmethod
    def _has_url(message):
        # simple url detection
        url_re = re.compile(r"https?://|www\.|\.[a-z]{2,3}/", re.IGNORECASE)
        return bool(url_re.search(message))

    @staticmethod
    def _has_email(message):
        email_re = re.compile(r"[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}")
        return bool(email_re.search(message))

    @staticmethod
    def _has_phone_number(message):
        # matches Korean phone numbers and common numeric sequences
        phone_re = re.compile(
            r"(01[0-9][- ]?\d{3,4}[- ]?\d{4}|0\d{1,2}[- ]?\d{3,4}[- ]?\d{4}|\d{2,3}[- ]?\d{3,4}[- ]?\d{3,4})"
        )
        if phone_re.search(message):
            return True

        # Additional robust detection: normalize and map Korean number words and homoglyphs
        norm = Tetrapod._normalize_text(message)
        digits_candidate = Tetrapod._korean_numberword_to_digits(norm)
        # remove non-digits to get continuous digits sequence
        digit_only = re.sub(r"\D", "", digits_candidate)
        # look for typical phone lengths (9~11 digits) or 10/11 starts with 01
        if re.search(r"01\d{8,9}", digit_only) or re.search(
                r"\d{9,11}", digit_only):
            return True
        return False

    @staticmethod
    def _korean_numberword_to_digits(message):
        """Convert Korean single-digit numerals and common obfuscations into digits.

        Examples: '공일공.일이삼사.일이삼사' -> '010.1234.1234'
        Also maps common letter homographs like l/I/| -> 1, o/O -> 0
        """
        if not isinstance(message, str):
            return ''
        mapping = {
            '공': '0',
            '영': '0',
            '영.': '0',
            '일': '1',
            '이': '2',
            '삼': '3',
            '사': '4',
            '오': '5',
            '육': '6',
            '륙': '6',
            '칠': '7',
            '팔': '8',
            '구': '9'
        }
        # quick homoglyph cleanup
        s = message
        s = s.replace('l', '1').replace('L', '1').replace('|', '1')
        s = s.replace('i', '1').replace('I', '1')
        s = s.replace('o', '0').replace('O', '0')
        # replace Korean number characters with digits where they appear standalone or adjacent
        result_chars = []
        for ch in s:
            if ch in mapping:
                result_chars.append(mapping[ch])
            else:
                result_chars.append(ch)
        return ''.join(result_chars)

    @staticmethod
    def _has_repeated_chars(message, threshold=4):
        # detect same char repeated threshold times (e.g., ㅋㅋㅋㅋ, !!!!!)
        pattern = re.compile(r"(.)\1{" + str(threshold - 1) + r",}")
        return bool(pattern.search(message))

    @staticmethod
    def _has_repeated_substring(message, min_len=6, repeats=3):
        """Detect if any substring (after removing spaces/punct) of length>=min_len
        appears at least `repeats` times in the message. Returns (bool, substring, count).
        """
        if not isinstance(message, str):
            return False, None, 0
        # normalize (lowercase, NFKC already applied elsewhere)
        norm = Tetrapod._normalize_text(message)
        # skeleton: keep alnum and hangul characters
        skeleton = re.sub(r'[^0-9a-z가-힣]', '', norm)
        n = len(skeleton)
        if n < min_len:
            return False, None, 0

        max_len = min(50, n // 1)
        # search for substrings of varying length
        for L in range(min_len, max_len + 1):
            counts = {}
            for i in range(0, n - L + 1):
                sub = skeleton[i:i + L]
                counts[sub] = counts.get(sub, 0) + 1
                if counts[sub] >= repeats:
                    return True, sub, counts[sub]
        return False, None, 0

    @staticmethod
    def _extract_domains(message):
        """Extract domain names from URLs found in the message."""
        # simple domain extractor from http(s) and bare www.
        domains = set()
        try:
            url_re = re.compile(r"https?://([^/\s]+)|www\.([^/\s]+)",
                                re.IGNORECASE)
            for m in url_re.findall(message):
                # m is a tuple because of two capture groups
                dom = m[0] or m[1]
                if dom:
                    # strip possible port
                    dom = dom.split(':')[0].lower()
                    # remove leading www.
                    if dom.startswith('www.'):
                        dom = dom[4:]
                    domains.add(dom)
        except re.error:
            pass
        return list(domains)

    @staticmethod
    def _spam_keyword_matches(message):
        matches = []
        # message expected to be normalized (lowercase)
        seen = set()
        for kw in getattr(Tetrapod, 'spam_words', []):
            if not kw:
                continue
            try:
                pattern = re.compile(r'(?<!\w)' + re.escape(kw) + r'(?!\w)',
                                     re.IGNORECASE)
                if pattern.search(message):
                    seen.add(kw)
            except re.error:
                if kw.lower() in message.lower():
                    seen.add(kw)
        return list(seen)

    @staticmethod
    def _category_matches(normalized_message):
        """Return a dict of category -> matched keywords (both exact and obfuscated)."""
        cfg = getattr(Tetrapod, 'spam_config', {}) or {}
        cat_kws = cfg.get('category_keywords', {}) or {}
        results = {}
        # check exact/word-boundary matches first
        for cat, kws in cat_kws.items():
            seen = set()
            for kw in kws:
                if not kw:
                    continue
                try:
                    pattern = re.compile(
                        r'(?<!\w)' + re.escape(kw) + r'(?!\w)', re.IGNORECASE)
                    if pattern.search(normalized_message):
                        seen.add(kw)
                except re.error:
                    if kw.lower() in normalized_message.lower():
                        seen.add(kw)
            # obfuscated skeleton match
            if not seen:
                # build skeleton once
                skel = re.sub(r'[^0-9a-z가-힣]', '', normalized_message)
                for kw in kws:
                    if not kw:
                        continue
                    kw_skel = re.sub(r'[^0-9a-z가-힣]', '',
                                     Tetrapod._normalize_text(kw))
                    if kw_skel and kw_skel in skel:
                        seen.add(kw)
            if seen:
                results[cat] = list(seen)
        return results

    @staticmethod
    def _normalize_text(message):
        """Normalize text for robust matching:
        - Unicode NFKC (converts fullwidth to ASCII, compat chars)
        - remove zero-width and control chars
        - lowercase
        """
        if not isinstance(message, str):
            return ''
        # NFKC converts fullwidth latin to ascii etc.
        s = unicodedata.normalize('NFKC', message)
        # remove zero-width and invisibles
        s = re.sub(r'[\u200B-\u200F\uFEFF\u2060]', '', s)
        s = s.lower()
        return s

    @staticmethod
    def _obfuscated_keyword_matches(normalized_message):
        """Detect keywords even when obfuscated by inserting punctuation/spaces or using homoglyphs
        Strategy: build an alnum+hangul-only skeleton (remove punctuation) and search for keyword skeletons.
        Returns list of keywords detected in obfuscated form.
        """
        skeleton = re.sub(r'[^0-9a-z가-힣]', '', normalized_message)
        matches = set()
        for kw in getattr(Tetrapod, 'spam_words', []):
            if not kw:
                continue
            kw_norm = Tetrapod._normalize_text(kw)
            kw_skel = re.sub(r'[^0-9a-z가-힣]', '', kw_norm)
            if kw_skel and kw_skel in skeleton:
                matches.add(kw)
        return list(matches)

    @staticmethod
    def _lemmatize_korean(message):
        """Attempt to lemmatize Korean text using KoNLPy if available.

        Returns the lemmatized string (space-joined lemmas) or original message
        if KoNLPy is not installed.
        """
        try:
            # try to import KoNLPy (optional dependency)
            from konlpy.tag import Okt
            okt = Okt()
            # get lemmas via morphemes (rough) or pos with base form
            # Okt doesn't provide direct lemmatize, but we can use morphs
            morphs = okt.morphs(message)
            return ' '.join(morphs)
        except Exception:
            # fallback: return original
            return message

    @staticmethod
    def _trusted_sender_indicator(normalized_message):
        """Return True if message contains indicators of trusted/legit senders (e.g., bank names + 수신거부)"""
        cfg = getattr(Tetrapod, 'spam_config', {})
        trusted = cfg.get('trusted_senders', [])
        # unsubscribe patterns configurable via config
        unsub_patterns = cfg.get('unsubscribe_patterns', [])
        for t in trusted:
            if t and t.lower() in normalized_message:
                # require unsubscribe or phone to be present to be safer
                for up in unsub_patterns:
                    if up and up.lower() in normalized_message:
                        return True, t
        return False, None

    @staticmethod
    def spam_score(message):
        # weighted scoring using config to reduce false positives
        cfg = getattr(Tetrapod, 'spam_config', None) or {}
        weights = cfg.get('weights', {})
        score = 0
        details = {}
        # normalize message first
        norm = Tetrapod._normalize_text(message)

        # collect whitelist matches; do not short-circuit here (we'll subtract later)
        whitelist_matches = []
        for wp in cfg.get('whitelist_phrases', []):
            if wp and wp.lower() in norm:
                whitelist_matches.append(wp)

        # trusted sender indicator (e.g., bank name + 수신거부)
        trusted, which = Tetrapod._trusted_sender_indicator(norm)
        if trusted:
            details['trusted_sender'] = which
            return 0, details

        # URL detection: by default a URL alone should not always mark spam.
        # Controlled via config flag `count_url_alone` (default False).
        # If `count_url_alone` is False, we only count URL when combined with
        # other risky signals (money keywords, phone number, repeated substrings).
        url_flag = False
        if Tetrapod._has_url(message):
            url_flag = True
            details['url'] = True
            if cfg.get('count_url_alone', False):
                score += weights.get('url', 3)
        if Tetrapod._has_email(message):
            score += weights.get('email', 2)
            details['email'] = True
        if Tetrapod._has_phone_number(message):
            score += weights.get('phone', 2)
            details['phone'] = True
            phone_flag = True
        else:
            phone_flag = False
        if Tetrapod._has_repeated_chars(message):
            score += weights.get('repeated', 1)
            details['repeated'] = True

        # exact/word-boundary keyword matches (on normalized message)
        kws = Tetrapod._spam_keyword_matches(norm)
        if kws:
            score += len(kws) * weights.get('keyword', 1)
            details['keywords'] = kws

        # obfuscated matches: check skeleton (letters-only) to catch 'ｔelegram' or 't.e.l.e.g.r.a.m' etc.
        obf = Tetrapod._obfuscated_keyword_matches(norm)
        if obf:
            # contribute at lower weight (half)
            score += len(obf) * weights.get('keyword', 1) * 0.5
            details['obfuscated'] = obf

        # rule: phone number present + money-related keyword -> boost
        money_keywords = cfg.get('money_keywords', [])
        # collect unique money-related matches (avoid double-counting variants)
        money_found_set = set()
        for mk in money_keywords:
            if not mk:
                continue
            if mk.lower() in norm:
                money_found_set.add(mk)

        # optional lemmatization: try to extract stems using KoNLPy (if installed)
        lemmatized = Tetrapod._lemmatize_korean(norm)

        # detect repayment verb forms like '갚아', '갚아요', '갚아라' and treat them as money signals
        try:
            repay_re = re.compile(r'갚\w*')
            for m in repay_re.findall(norm):
                if m:
                    money_found_set.add('갚다')
        except re.error:
            pass

        money_found = list(money_found_set)
        if money_found:
            # phone+money still gives a dedicated boost
            if phone_flag:
                boost = cfg.get('phone_money_boost', 3)
                score += boost
                details['phone_money_combo'] = {
                    'money_keywords': money_found,
                    'boost': boost
                }

            # base contribution from unique money keywords
            kw_weight = weights.get('keyword', 1)
            contrib = len(money_found) * kw_weight
            score += contrib
            details['money_found'] = money_found
            details['money_contrib'] = contrib

            # urgent-word boost (config-driven list)
            urgent_words = cfg.get('urgent_words') or []
            urgent_boost = cfg.get('urgent_money_boost', 2)
            for uw in urgent_words:
                if uw and uw in norm:
                    score += urgent_boost
                    details['urgent_word'] = uw
                    details['urgent_boost'] = urgent_boost
                    break

            # repeated token (e.g., same name appears multiple times) gives extra suspicion
            tokens = re.findall(r'[0-9a-z가-힣]+', norm)
            token_counts = {}
            for t in tokens:
                token_counts[t] = token_counts.get(t, 0) + 1
            repeated_names = [
                t for t, c in token_counts.items() if c >= 2 and len(t) >= 2
            ]
            if repeated_names:
                name_boost = cfg.get('repeat_name_boost', 2)
                score += name_boost
                details['repeated_names'] = repeated_names
                details['repeat_name_boost'] = name_boost

        # --- category detection (5대 악성 스팸) ---
        # detect category keywords and add category-specific weights
        categories_found = Tetrapod._category_matches(norm)
        if categories_found:
            cat_weights = cfg.get('category_weights', {}) or {}
            for cat, matches in categories_found.items():
                w = cat_weights.get(cat, 4)
                score += w
                details.setdefault('categories', []).append({
                    cat: matches,
                    'weight': w
                })

        # ham keywords reduce score (common polite phrases)
        ham_count = 0
        for hk in cfg.get('ham_keywords', []):
            if hk and hk.lower() in norm:
                ham_count += 1
        if ham_count:
            subtract = ham_count * weights.get('ham_keyword_subtract', 1)
            score = max(0, score - subtract)
            details['ham_count'] = ham_count

        # repeated substring detection (spammy repeated phrases)
        rep_found, rep_sub, rep_count = Tetrapod._has_repeated_substring(
            message, min_len=8, repeats=3)
        if rep_found:
            # give a significant boost for repeated phrases
            boost = 3
            score += boost
            details['repeated_substring'] = {
                'substr': rep_sub,
                'count': rep_count,
                'boost': boost
            }

        # If a URL was present but not already counted (count_url_alone==False),
        # add its weight only when combined with other high-risk signals.
        if url_flag and not cfg.get('count_url_alone', False):
            try:
                money_present = bool(money_found)
            except NameError:
                money_present = False
            if money_present or phone_flag or rep_found:
                score += weights.get('url', 3)
                details['url_counted'] = True

        # Domain blacklist and regex blacklist checks: these are explicit
        # pattern-based or domain-based rules that should strongly affect score.
        # `domain_blacklist` is a list of domain strings (exact or suffix like example.com)
        # `regex_blacklist` is a list of regex patterns to match against the message.
        domain_blacklist = cfg.get('domain_blacklist', []) or []
        regex_blacklist = cfg.get('regex_blacklist', []) or []
        blacklist_weight = cfg.get('blacklist_weight', 5)

        # check domains found in the message
        try:
            domains = Tetrapod._extract_domains(message)
            for d in domains:
                for bad_dom in domain_blacklist:
                    if not bad_dom:
                        continue
                    bd = bad_dom.lower()
                    # allow suffix match: if bad_dom is example.com it matches sub.example.com
                    if d == bd or d.endswith('.' + bd) or d.endswith(bd):
                        score += blacklist_weight
                        details.setdefault('domain_blacklist', []).append({
                            'domain':
                            d,
                            'matched':
                            bad_dom
                        })
                        # do not double count same domain
                        break
        except Exception:
            pass

        # check regex blacklist against normalized message
        try:
            for pat in regex_blacklist:
                if not pat:
                    continue
                try:
                    r = re.compile(pat, re.IGNORECASE)
                    if r.search(norm):
                        score += blacklist_weight
                        details.setdefault('regex_blacklist', []).append(pat)
                except re.error:
                    # fallback to simple substring
                    if pat.lower() in norm:
                        score += blacklist_weight
                        details.setdefault('regex_blacklist', []).append(pat)
        except Exception:
            pass

        # apply whitelist subtraction AFTER all other signals so whitelist reduces score but
        # does not fully exempt dangerous messages (whitelist_subtract configurable)
        if 'whitelist_matches' in locals() and whitelist_matches:
            subtract_val = cfg.get('whitelist_subtract', 0)
            if subtract_val:
                total_sub = subtract_val * len(whitelist_matches)
                score = max(0, score - total_sub)
                details['whitelist_matches'] = whitelist_matches
                details['whitelist_subtracted'] = total_sub

        return score, details

    @staticmethod
    def is_spam(message, threshold=3):
        """Return (is_spam_bool, score, details)

        threshold: integer score above which message considered spam (default 3)
        """
        s, d = Tetrapod.spam_score(message)
        return (s >= threshold, s, d)


__all__ = ['Tetrapod']
