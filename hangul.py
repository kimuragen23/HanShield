# Minimal Hangul utilities ported from Hangul.js (needed parts only)

HANGUL_OFFSET = 0xAC00

COMPLETE_CHO = [
    'ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ',
    'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'
]

COMPLETE_JUNG = [
    'ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ',
    'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ'
]

COMPLETE_JONG = [
    '', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ',
    'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'
]


def is_complete(char):
    if not char or not isinstance(char, str):
        return False
    code = ord(char)
    return 0xAC00 <= code <= 0xD7A3


def disassemble(char):
    """Return a minimal decomposition for a single character.

    For Hangul syllables returns a list where first element is initial consonant (cho),
    followed by medial and final if present. For non-hangul returns [char].
    """
    if not char or not isinstance(char, str):
        return []
    ch = char[0]
    code = ord(ch)
    if is_complete(ch):
        code -= HANGUL_OFFSET
        jong = code % 28
        jung = (code - jong) // 28 % 21
        cho = (code - jong) // 28 // 21

        result = [COMPLETE_CHO[cho]]
        # use COMPLETE_JUNG mapping
        result.append(COMPLETE_JUNG[jung])
        if jong > 0:
            result.append(COMPLETE_JONG[jong])
        return result
    else:
        return [ch]


__all__ = ['disassemble', 'is_complete']
