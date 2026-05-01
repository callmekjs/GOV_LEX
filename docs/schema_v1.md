# Canonical Schema v1

> GovLex-Ops의 표준 데이터 양식.  
> 모든 문서는 국가·소스에 관계없이 이 양식으로 저장됩니다.

---

## 1. 왜 표준 양식이 필요한가?

한국 법령 API, 한국 국회 API, 미국 Congress.gov API는
**필드 이름·날짜 형식·언어가 전부 다릅니다.**

```
KR 법제처 : {"법령명한글": "인공지능 기본법", "공포일자": "20260120"}
KR 국회   : {"BILL_NAME": "AI법률안",         "PROPOSE_DT": "2024-05-15"}
US 의회   : {"title": "AI Act",               "introducedDate": "2024-03-15"}
```

이 셋을 **같은 양식**으로 맞춰야 검색·비교·품질 관리가 가능합니다.

---

## 2. 9개 공통 필수 필드

| 필드 | 타입 | 설명 | 없으면 어떻게 되나 |
|---|---|---|---|
| `source_id` | string | 문서 고유 ID | 문서 구별 불가 |
| `jurisdiction` | `KR` / `US` | 국가 코드 | 국가 필터 불가 |
| `source_type` | enum (5종) | 문서 종류 | 법령/법안 구분 불가 |
| `language` | `ko` / `en` | 언어 | 언어 필터 불가 |
| `title` | string | 제목 | 검색 불가 |
| `issued_date` | YYYY-MM-DD | 발행일 | 시간 필터 불가 |
| `source_url` | string | 원문 링크 | 출처 제공 불가 |
| `content_hash` | sha256 | 정규화된 식별 메타데이터의 SHA-256 해시 (본문 해시 아님 — §6 참고) | 중복 감지 불가 |
| `ingested_at` | ISO8601 | 수집 시각 | 추적 불가 |

**핵심 원칙**: 필드가 많을수록 결측이 늘어납니다.
공통 필드는 **최소**로, 국가별 정보는 `metadata`로 분리합니다.

---

## 3. `source_type` 분류 체계 (5종)

### 3-1. 왜 5개인가?

법률 문서는 **효력 위계**와 **생산 단계**로 구분됩니다.  
한국·미국 법제의 공통 분모에서 도출한 5개 타입입니다.

(자세한 근거는 `docs/legal_domain.md` 참고)

### 3-2. 5개 타입 정의

| source_type | 한국어 | 영어 | 효력 위계 | 예시 |
|---|---|---|---|---|
| `law` | 법률 | Act / Public Law | 최상위 | 인공지능 기본법 / PL 117-xxx |
| `decree` | 시행령 | Presidential Decree | 2순위 | 인공지능 기본법 시행령 |
| `rule` | 시행규칙·행정규칙 | Enforcement Rule / Agency Rule | 3순위 | 개인정보 보호 고시 / CFR |
| `bill` | 법안 (미통과) | Bill (Pending) | — | HR 4763 / 의원발의 법률안 |
| `minutes` | 회의록 | Minutes / Hearing | — | 외교통일위 회의록 |

### 3-3. 입법 프로세스와 매핑

본 파이프라인이 다루는 입법 프로세스 단계:

| 단계 | source_type | 수집 소스 | 현재 상태 |
|---|---|---|---|
| 발의 (Introduction) | `bill` | 열린국회 ALLBILLV2, Congress.gov | ✅ |
| 심사 (Committee Review) | `minutes` | 국회 회의록 API | Week 3+ |
| 의결 (Floor Vote) | — (상태값) | `metadata.status` | ✅ |
| 공포 (Promulgation) | `law` | 국가법령정보 API | ✅ |
| 하위법령 | `decree`, `rule` | 국가법령정보 / Federal Register | Week 3+ |

### 3-4. 분류 플로우차트

```
문서가 통과되었는가?
├─ 아니오 → bill
└─ 예
    │
    국회가 직접 만들었나?
    ├─ 예 → law
    └─ 아니오
         │
         대통령령인가?
         ├─ 예 → decree
         └─ 아니오 → rule

심사 과정 기록인가? → minutes
```

---

## 4. `metadata` 필드 규약

### 4-1. 역할

공통 9개 필드에 담기 어려운 **국가·소스별 특수 정보**를 저장합니다.  
`dict[str, Any]`로 자유도를 열어두되, **네이밍 규약**으로 통제합니다.

### 4-2. KR 법령 (source_type: law)

```json
{
  "law_type": "법률",
  "ministry": "과학기술정보통신부",
  "enforcement_date": "20260120",
  "law_serial": "282791"
}
```

| 키 | 타입 | 설명 |
|---|---|---|
| `law_type` | string | 법률 / 시행령 / 시행규칙 |
| `ministry` | string | 소관 부처명 |
| `enforcement_date` | YYYYMMDD | 시행일 |
| `law_serial` | string | 법제처 법령일련번호 |

### 4-3. KR 국회 법안 (source_type: bill)

```json
{
  "committee": "과학기술정보방송통신위원회",
  "session": "제22대",
  "sub_session": "제416회",
  "proposer_type": "의원발의",
  "proposer_name": "홍길동 등 12인",
  "bill_status": "계류",
  "bill_no": "2100123"
}
```

| 키 | 타입 | 설명 |
|---|---|---|
| `committee` | string | 소관 상임위원회 |
| `session` | string | 대수 (제22대) |
| `sub_session` | string | 회차 |
| `proposer_type` | string | 의원발의 / 정부제출 / 위원장제안 |
| `proposer_name` | string | 발의자 |
| `bill_status` | string | 계류 / 원안가결 / 수정가결 / 폐기 |
| `bill_no` | string | 의안번호 |

### 4-4. US Congress 법안 (source_type: bill)

```json
{
  "congress": 118,
  "bill_type": "HR",
  "bill_number": "4763",
  "origin_chamber": "House",
  "sponsor": "Rep. Smith",
  "latest_action": "Referred to committee",
  "latest_action_date": "2024-04-15",
  "policy_area": "Science, Technology, Communications"
}
```

| 키 | 타입 | 설명 |
|---|---|---|
| `congress` | int | 의회 회기 (현재 119) |
| `bill_type` | string | HR / S / HJRES 등 |
| `bill_number` | string | 법안 번호 |
| `origin_chamber` | string | House / Senate |
| `sponsor` | string | 발의자 |
| `latest_action` | string | 최신 진행 상태 |
| `policy_area` | string | 정책 분야 |

### 4-5. 자유도 관리 원칙

1. **네이밍 규약 고정** — 위 표가 정식 키
2. **관찰 → 승격** — 반복 사용되는 키는 다음 스키마 버전에 **공통 필드로 승격**
3. **깨진 값은 QA로 회수**
   - R06 (예정): `metadata` 필수 key 누락 → 경고
   - R07 (예정): `metadata` 타입 불일치 → 격리

즉, `metadata`는 **"스키마 승격 대기실"**입니다.

---

## 5. 실제 저장 예시

### 5-1. KR 법령 (source_type: law)

```json
{
  "source_id": "kr_law_014820",
  "jurisdiction": "KR",
  "source_type": "law",
  "language": "ko",
  "title": "인공지능 발전과 신뢰 기반 조성 등에 관한 기본법",
  "issued_date": "2026-01-20",
  "source_url": "https://www.law.go.kr/lsInfoP.do?lsiSeq=282791",
  "content_hash": "a3f8b2c1d4e5...",
  "ingested_at": "2026-04-19T12:25:12",
  "metadata": {
    "law_type": "법률",
    "ministry": "과학기술정보통신부",
    "enforcement_date": "20260120",
    "law_serial": "282791"
  }
}
```

### 5-2. KR 국회 법안 (source_type: bill)

```json
{
  "source_id": "kr_bill_2100123",
  "jurisdiction": "KR",
  "source_type": "bill",
  "language": "ko",
  "title": "인공지능 산업 육성 및 신뢰 확보에 관한 법률안",
  "issued_date": "2024-05-15",
  "source_url": "https://likms.assembly.go.kr/bill/billDetail.do?billId=...",
  "content_hash": "b7e2d4f0c1a3...",
  "ingested_at": "2026-04-19T12:25:15",
  "metadata": {
    "committee": "과학기술정보방송통신위원회",
    "session": "제22대",
    "proposer_type": "의원발의",
    "bill_status": "계류",
    "bill_no": "2100123"
  }
}
```

### 5-3. US Congress 법안 (source_type: bill)

```json
{
  "source_id": "us_congress_118_hr4763",
  "jurisdiction": "US",
  "source_type": "bill",
  "language": "en",
  "title": "Artificial Intelligence Accountability Act",
  "issued_date": "2023-07-27",
  "source_url": "https://congress.gov/bill/118th-congress/house-bill/4763",
  "content_hash": "c9d1e2f3a4b5...",
  "ingested_at": "2026-04-19T12:25:18",
  "metadata": {
    "congress": 118,
    "bill_type": "HR",
    "bill_number": "4763",
    "policy_area": "Science, Technology, Communications"
  }
}
```

---

## 6. `content_hash` 생성 규칙

> ⚠️ **이 해시는 본문(full text) 해시가 아니다.**
> v1 스키마에서는 의도적으로 **정규화된 식별 메타데이터(제목·발행일·소스 식별자)의 SHA-256 해시**로 정의한다. 이유와 한계, 승격 계획은 아래에서 자세히 설명한다.

### 6-1. 무엇을 해시하는가? (현재 v1)

**현재 정의: "정규화된 식별 메타데이터(제목·발행일·소스 식별자)의 SHA-256 해시"**

각 소스별 입력 문자열은 다음과 같다:

| 소스 | source_type | 입력 식 | 코드 위치 |
|---|---|---|---|
| KR 법령 | `law` | `f"{title}_{공포일자_YYYYMMDD}"` | `etl/ingest/kr_law.py::_convert_to_document` |
| KR 국회 법안 | `bill` | `f"{title}_{PPSL_DT_digits}_{BILL_NO}"` | `etl/ingest/assembly_bills.py::_bill_to_legal_document` |
| US Congress | `bill` | `f"{title}_{introducedDate}_{bill_number}"` | `etl/ingest/us_congress.py::_convert_to_document` |

이 문자열에 `make_content_hash()`가 다음 정규화를 적용한 뒤 SHA-256 해시:

1. 유니코드 **NFC 정규화** — 한글 조합형/완성형 차이를 흡수
2. **연속 공백 단일화** — `re.sub(r'\s+', ' ', text)`
3. **앞뒤 공백 제거** — `strip()`

```python
# src/govlexops/schemas/legal_document.py
def make_content_hash(text: str) -> str:
    normalized = _normalize_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
```

### 6-2. 왜 본문 해시가 아닌가?

본문 텍스트 자체를 해시하는 게 의미상 더 정확하지만, MVP 단계에선 **의도적으로** 메타데이터 ID 해시를 채택했다.

| # | 이유 | 설명 |
|---|---|---|
| 1 | **API 제공 비대칭** | KR 법제처는 법령 본문을 별도 API(목록 → 본문 2단계)로만 제공. US Congress.gov v3 목록 API는 title·요약만 반환. 세 소스에서 본문 일관 확보가 비현실적이다. |
| 2 | **분량 부담** | 법안 1건 본문이 수십~수백 KB. 5,000건 수집 시 본문 적재만 수백 MB → MVP 1주 일정 초과. |
| 3 | **정확도 vs 구현비용** | 같은 (title, date)인데 본문이 미세 수정된 케이스는 R05(제목 동일·날짜 다름)와 향후 source_url 변경 감지로 부분 보완. |
| 4 | **운영 안정성** | 본문 텍스트는 띄어쓰기·문장부호 변경에 매우 민감 → 같은 문서가 다른 해시로 잡히는 false-positive 위험이 메타데이터 해시보다 높음. |

따라서 현재 `content_hash`는 의미상 **"같은 문서를 두 번 가져왔는지 판별하는 고유 ID 해시"** 에 가깝다.

### 6-3. 한계 (정직 노선)

| 한계 | 영향 |
|---|---|
| **본문 변경 추적 불가** | 같은 (title, date)의 법안 본문이 수정돼도 같은 해시. "법안 수정 알림"은 별도 로직 필요. |
| **소스별 입력 비대칭** | KR law는 식별자 없이 (title, date) 2-튜플, bill은 (title, date, id) 3-튜플. 정규화된 title이 비정상적으로 잘리면 다른 소스의 동일 해시 충돌 이론적 가능(실측 0건). |
| **빈 title 처리** | 수집기에서 title이 빈 문자열이면 해시는 `(_, date, _)` 형태로 생성됨 → R02(필수 필드 결측)에서 격리. |

### 6-4. 승격 계획 (Phase 2 / schema v2)

[`pipline_upgrade.md` Phase 2-2의 옵션 B](../pipline_upgrade.md)에서 source_type별 본문 해시로 분리 승격 예정:

| source_type | v2 입력 (예정) | 비고 |
|---|---|---|
| `law` | 시행일 + 소관부처 + 조문 본문(앞 N kB) | 법제처 본문 API 추가 필요 |
| `bill` | 의안 요약(SUMMARY) + 발의자 + bill_no | 국회 BPMBILLSUMMARY 활용, US는 Congress text API |
| `minutes` | PDF 추출 텍스트 정규화 | National_Assembly 자산 재활용 |

승격 시 `LegalDocument.schema_version`을 `"2.0.0"`으로 올리고, v1 해시는 `metadata.content_hash_v1`로 이관해 호환을 유지한다.

### 6-5. 정규화 결과를 검증하는 간단 예제

```python
from govlexops.schemas.legal_document import make_content_hash

# NFC + 공백 단일화 + strip
assert make_content_hash("AI 기본법_20260120") \
    == make_content_hash(" AI  기본법_20260120 ")

# 본문이 다르더라도 (title, date)가 같으면 같은 해시 (이게 v1의 한계)
# → 본문 변경 추적은 v2 승격 후에 가능
```

---

## 7. 변경 이력

| 버전 | 날짜 | 변경 내용 |
|---|---|---|
| v1.0 | 2026-04-19 | 초기 9개 필드 확정 |
| v1.1 | 2026-04-20 | `metadata` 자유도 관리 원칙 추가 |
| v1.2 | 2026-04-21 | `source_type` 5종 분류 근거 명시, 입법 프로세스 매핑 추가 |
| v1.3 | 2026-04-21 | KR 국회 API 연결 후 `metadata.bill_status` 등 KR bill 스키마 확정 |
| v1.4 | 2026-04-30 | **`content_hash` 정의 명확화** — '본문 해시'에서 '정규화된 식별 메타데이터 해시'로 정정. 본문 해시가 아닌 이유·한계·v2 승격 계획 §6 박제 ([pipline_upgrade.md 0-2](../pipline_upgrade.md)) |

---

## 8. Week 3+ 확장 예정

반복적으로 나타나는 `metadata` 키는 정식 필드로 승격 예정:

| 현재 metadata 키 | 승격 예정 필드 | 이유 |
|---|---|---|
| `law_type` / `bill_type` | `document_subtype` | 양국 공통으로 자주 쓰임 |
| `ministry` / `origin_chamber` | `issuing_body` | 생산 주체 식별 |
| `enforcement_date` / `latest_action_date` | `effective_date` | 실효성 추적 |

---

## 9. 참고

- 법률 도메인 이해: `docs/legal_domain.md`
- 소스 카탈로그: `docs/source_catalog.md`
- 설계 결정 기록: `docs/design_decisions.md`