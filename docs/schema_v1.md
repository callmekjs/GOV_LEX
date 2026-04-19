# Canonical Schema v1

> GovLex-Ops의 표준 데이터 양식.
> 모든 문서는 국가·소스에 관계없이 이 양식으로 저장됩니다.

---

## 왜 표준 양식이 필요한가?

한국 법령 API와 미국 Congress.gov API는 필드 이름도, 날짜 형식도, 언어도 다릅니다.

이 둘을 **같은 양식**으로 맞춰야 검색·비교·품질 관리가 가능합니다.

---

## 9개 필수 필드

| 필드 | 타입 | 설명 | 없으면 어떻게 되나 |
|---|---|---|---|
| `source_id` | string | 문서 고유 ID | 문서 구별 불가 |
| `jurisdiction` | KR / US | 국가 코드 | 국가 필터 불가 |
| `source_type` | string | 문서 종류 | 법령/법안 구분 불가 |
| `language` | ko / en | 언어 | 언어 필터 불가 |
| `title` | string | 제목 | 검색 불가 |
| `issued_date` | YYYY-MM-DD | 발행일 | 시간 필터 불가 |
| `source_url` | string | 원문 링크 | 출처 제공 불가 |
| `content_hash` | sha256 | 본문 지문 | 중복 감지 불가 |
| `ingested_at` | ISO8601 | 수집 시각 | 추적 불가 |

---

## `metadata` 필드

9개 공통 필드에 담기 어려운 국가별 정보는 `metadata`에 저장합니다.

**KR 예시**:
```json
{
  "law_type": "법률",
  "ministry": "과학기술정보통신부",
  "enforcement_date": "20260120",
  "law_serial": "282791"
}
```

**US 예시**:
```json
{
  "congress": 118,
  "bill_type": "HR",
  "bill_number": "4763",
  "latest_action": "Referred to committee",
  "policy_area": "Science, Technology, Communications"
}
```

---

## 실제 저장 예시

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
    "enforcement_date": "20260120"
  }
}
```

```json
{
  "source_id": "us_congress_118_hr4763",
  "jurisdiction": "US",
  "source_type": "bill",
  "language": "en",
  "title": "Artificial Intelligence Accountability Act",
  "issued_date": "2023-07-27",
  "source_url": "https://congress.gov/bill/118th-congress/house-bill/4763",
  "content_hash": "b7e2d4f0c1a3...",
  "ingested_at": "2026-04-19T12:25:15",
  "metadata": {
    "congress": 118,
    "bill_type": "HR",
    "bill_number": "4763",
    "policy_area": "Science, Technology, Communications"
  }
}
```

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|---|---|---|
| v1.0 | 2026-04-19 | 초기 9개 필드 확정 |

---

## Week 3+ 확장 예정

반복적으로 나타나는 `metadata` 키는 정식 필드로 승격 예정:
- `law_type` → 정식 필드 `document_subtype`
- `ministry` / `origin_chamber` → 정식 필드 `issuing_body`