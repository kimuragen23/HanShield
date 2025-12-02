from tetrapod import Tetrapod


def main():
    Tetrapod.default_load()

    samples = [
        '''안녕하세요 여러분. 오늘은 정말 좋은 날입니다.''',
    ]

    for s in samples:
        found = Tetrapod.find(s, True)
        is_bad = len(found) > 0
        fixed = Tetrapod.fix(s, '*') if is_bad else s
        is_spam, score, details = Tetrapod.is_spam(s)
        print('원문 :', s)
        print('비속어 발견 :', found)
        print('차단여부 :', is_bad)
        print('수정문 :', fixed)
        print('스팸판정 :', is_spam, '점수:', score, '상세:', details)
        print('---')


if __name__ == '__main__':
    main()
