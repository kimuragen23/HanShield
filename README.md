# HanShield (Python)

HanShield는 한국어 중심의 규칙 기반 SMS/메시지 스팸 & 비속어 필터입니다. 정규화, 키워드/오브퓨스(우회) 매칭, 전화번호/URL/이메일 탐지, 반복 패턴 검출, 화이트리스트·신뢰발신자 예외 등 여러 신호를 조합해 점수 기반으로 메시지를 판정합니다.

## 한눈에 보기
- 언어: Python 3
- 주요 기능: 키워드 매칭, 오브퓨스 탐지, 한글 숫자·동형문자 처리, 전화번호+금전 조합 보정, 카테고리 기반 악성 스팸(5대) 탐지
- 설정 파일: `config/spam-config.json` (가중치·임계값·화이트리스트 등)

## 빠른 시작
1. 레포지토리 루트에서 기본 동작 확인:

```powershell
python .\test.py
```

2. 회피(우회) 샘플 검사:

```powershell
python .\tools\check_evade.py
```

3. 자동 튜닝(간단 그리드서치):

```powershell
python .\tools\tune.py
```

4. 튜닝 결과 병합(백업 포함):

```powershell
python .\tools\apply_tuned_config.py
```

## 구성(요약)
`config/spam-config.json`에서 주요 설정을 조정해 민감도를 맞춥니다. 중요한 키:

- `threshold`: 스팸 판정 임계값
- `weights`: 기본 신호 가중치(예: `url`, `email`, `phone`, `repeated`, `keyword`)
- `money_keywords`: 금전 관련 키워드 리스트
- `phone_money_boost`: 전화번호+금전 조합 보너스
- `whitelist_phrases`, `ham_keywords`: 오탐 완화용 문구
- `trusted_senders`: 발신자명으로 신뢰 처리(예: 은행 이름)
- `count_url_alone`: URL 단독 포함 시 점수 카운트 여부(boolean, 기본 false)
- `domain_blacklist`, `regex_blacklist`, `blacklist_weight`: 도메인/정규식 기반 블랙리스트
- `category_keywords`, `category_weights`: 5대 악성 스팸 카테고리 키워드 및 가중치

자세한 예시는 `config/spam-config.json`을 확인하세요.

## KoNLPy (선택)
간단 요약: KoNLPy를 사용하면 한국어 형태소 분석으로 활용형(예: '갚아요' → '갚다')을 통일하여 키워드 매칭 정확도를 높일 수 있습니다.

설치(선택):

```powershell
pip install konlpy
```

주의: KoNLPy는 Java 런타임 등 추가 의존이 있을 수 있습니다. 형태소 분석은 비용이 크므로 대량 처리 환경에서는 캐시나 조건부 적용을 권장합니다. KoNLPy가 없을 경우 HanShield는 내부 규칙 기반 매칭으로 자동으로 동작합니다.

간단 사용 예:

```python
from tetrapod import Tetrapod
Tetrapod.default_load()
msg = "갚아요→연락주세요"
print(Tetrapod._lemmatize_korean(msg))
print(Tetrapod.is_spam(msg))
```

## 5대 악성 스팸 (기능)
HanShield는 다음 5대 악성 스팸 카테고리를 구성·탐지할 수 있습니다. 각 카테고리는 `category_keywords`로 정의되며 탐지 시 `category_weights`만큼 점수가 추가됩니다.

- 불법대출 (illegal_loan)
- 성인광고 (adult)
- 불법의약품 (illegal_drugs)
- 사행성 게임 (gambling)
- 부동산 분양광고 (real_estate)

운영 팁: 카테고리 키워드와 가중치는 `config/spam-config.json`에서 조정하세요. 필요 시 특정 카테고리를 발견하면 즉시 차단하도록(short-circuit) 설정을 추가할 수도 있습니다.

## 제공된 도구
- `test.py`: 기본 샘플로 필터 동작 확인
- `tools/check_evade.py`: 회피 샘플 테스트
- `tools/tune.py`: 간단 그리드서치 튜닝
- `tools/apply_tuned_config.py`: 튜닝 결과 안전 병합
- `bench_spam_bench.py`: 메시지 처리 시간 벤치(예: 120자 메시지 반복 측정)

## 성능 팁(요약)
- 정규식은 모듈 초기화 시 미리 컴파일하세요.
- KoNLPy는 조건부로 적용(키워드 히트 시에만)하면 평균 지연을 크게 줄일 수 있습니다.
- 반복 서브스트링 탐지 같은 고비용 루틴은 슬라이딩 윈도우나 해시 기반 카운트로 대체하면 빠릅니다.
- 대량 처리 시 프로세스 워커(pool)로 병렬화하세요.

## 라이선스
- 프로젝트 라이선스: MIT (루트의 `LICENSE` 파일 참조)
- 서드파티: `hangul-js`, `tetrapod` 등은 MIT 라이선스입니다(자세한 내용은 `THIRD_PARTY_LICENSES.md`).

---

더 정리할 부분이나, 특정 섹션(예: Quick Start에 더 많은 예시, config 예시 자동 생성 등)을 추가하길 원하시면 말씀해 주세요.

## 제공된 도구

- `test.py`: 간단한 샘플들로 필터 동작을 확인합니다.
- `tools/tune.py`: 레이블된 샘플(`tuning/samples.json`)로 간단한 그리드 서치 튜닝을 수행해 `config/spam-config.tuned.json`을 생성합니다.
- `tools/check_evade.py`: 회피 샘플(`tuning/evade_samples.json`)을 돌려 어떤 샘플이 통과하는지 확인합니다.
- `tools/apply_tuned_config.py`: `spam-config.tuned.json`을 `spam-config.json`에 안전하게 병합(백업 포함)합니다.

## 회피(우회) 대응 팁

- 화이트리스트는 편의상 오탐을 줄여주지만, 너무 관대하면 스팸이 통과합니다. `whitelist_subtract` 값을 낮추거나 `trusted_senders` 룰을 보강하세요.
- 영어/외국어 메시지가 많다면 영어 키워드도 추가하세요(현재 기본 키워드는 한국어 중심입니다).
- 동형문자(homoglyph), 전각 문자(fullwidth), 특수문자 삽입 등 우회 패턴을 튜닝하려면 `tuning/evade_samples.json`에 다양한 사례를 추가하고 `tools/tune.py`로 재학습하세요.

## 실전 배포 전 체크리스트

1. 충분한 정상/스팸 샘플로 `tuning/samples.json`을 채우고 튜닝 실행
2. 튜닝 결과를 검토하고 `tools/apply_tuned_config.py`로 병합(백업 확보)
3. 운영 로그로 주기적 재튜닝  새로운 회피 패턴이 나오면 샘플 추가
4. (선택) KoNLPy 전면 활성화 및 성능 테스트

## 예시: 전체 흐름

```powershell
python .\tools\check_evade.py          # 회피 샘플 검사
python .\tools\tune.py                # 튜닝 탐색
python .\tools\apply_tuned_config.py  # 튜닝 결과 병합(백업 생성)
python .\test.py                       # 결과 확인
```
