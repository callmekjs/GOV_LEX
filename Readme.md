# GovLex-Ops

> **한국과 미국의 법·입법 공개 데이터를 자동으로 수집하고, 하나의 표준 양식으로 정제하며, 품질을 숫자로 관리하는 데이터 파이프라인**

---

## 1. 이 프로젝트가 증명하는 것

> **"법률·정책 AI 서비스의 기반 데이터를 책임질 수 있는 사람"**임을 증명합니다.

GovLex-Ops는 챗봇을 만드는 프로젝트가 아닙니다.  
이 프로젝트의 핵심은 **법률·입법 공개 문서를 신뢰 가능한 데이터 자산으로 바꾸는 것**입니다.

즉, 이 프로젝트는 아래를 보여주기 위한 포트폴리오입니다.

- 여러 공개 소스에서 문서를 안정적으로 수집할 수 있다.
- 한국과 미국의 서로 다른 문서를 하나의 공통 스키마로 맞출 수 있다.
- 데이터 품질 문제를 자동으로 감지하고 기록할 수 있다.
- 실행 결과를 추적 가능한 형태로 남길 수 있다.
- 나중에 검색, RAG, 챗앱 위에 올릴 수 있는 데이터 기반을 만들 수 있다.

---

## 2. 한마디로 뭘 하는 프로젝트인가요?

여러 나라의 법·입법 문서를

**자동으로 모으고 → 같은 양식으로 정리하고 → 오류를 검사하고 → 저장하고 → 검색 가능한 상태로 만드는 프로젝트**입니다.

쉽게 말하면,
**한국과 미국의 법률 문서 도서관에 공통 색인 카드를 만드는 일**입니다.

원문은 각 사이트에 그대로 있지만,
이 프로젝트는 그 원문을 **같은 규칙으로 정리된 데이터**로 바꿉니다.

---

## 3. 왜 만들었나요?

정책·법률 데이터를 다루는 서비스는 겉으로 보면 "질문하면 답하는 AI"처럼 보입니다.  
하지만 실제로는 그 아래에 있는 데이터가 먼저 정리되어 있어야 합니다.

현실의 법률·입법 공개 문서는 이런 문제가 있습니다.

- 사이트가 흩어져 있음
- PDF, HTML, API 등 형식이 제각각임
- 날짜, 제목, 문서 종류 표기가 일정하지 않음
- 중복, 누락, 날짜 오류가 생기기 쉬움
- 그대로는 검색·비교·요약에 쓰기 어려움

GovLex-Ops는 이 문제를 해결하기 위해,
**AI 이전 단계의 데이터 인프라**를 만드는 데 집중합니다.

---

## 4. 프로젝트 범위

### 이번 MVP에서 다루는 범위

- **국가**: 한국, 미국
- **초점 문서**: 법·입법 공개 데이터
- **주요 소스**:
  - 한국 국회 회의록
  - 한국 국가법령정보 Open API
  - 미국 Congress.gov API

### 이번 MVP에서 의도적으로 제외한 것

| 제외 항목 | 이유 |
|---|---|
| 뉴스 수집 | 법·입법 문서 표준화에 집중하기 위해 |
| 일본 등 제3국 확장 | 2주 안에 KR+US 2개국 완성이 우선 |
| LLM 답변 생성 | 데이터 품질 증명이 목적. LLM 답변 품질은 변수가 너무 많음 |
| 자동 스케줄링 | 수동 실행 + 문서화로 대체 가능 |
| Replay 완성본 | events.jsonl 구조만 남겨두면 Week 3+에서 하루면 추가 가능 |
| 복잡한 외부 DB 인프라 | 로컬 파일만으로 재현성 보장. 확장은 어댑터만 맞추면 됨 |

즉, 이 프로젝트는 **넓고 화려한 서비스**보다  
**작지만 끝까지 동작하는 데이터 파이프라인**을 목표로 합니다.

---

## 5. 전체 구조

```text
[공개 데이터 소스]
   ├─ 한국 국회 회의록
   ├─ 한국 국가법령정보 API
   └─ 미국 Congress.gov API

                ↓

           [GovLex-Ops]
   수집 → 정제 → 표준화 → QA → 저장

                ↓

    [정리된 통합 데이터 저장소]
   ├─ data_index/raw/
   ├─ data_index/normalized/docs.jsonl
   ├─ runs/<run_id>/events.jsonl
   ├─ runs/<run_id>/quality_failures.jsonl
   └─ runs/<run_id>/quality_report.md

                ↓

      [검증용 검색 / 이후 RAG 연결 가능]
```

---

## 6. 파이프라인 단계

| 단계 | 하는 일 | 산출물 |
|---|---|---|
| **Extract** | 공개 소스에서 원문 수집 | raw JSON / raw text / PDF |
| **Transform** | 날짜, 제목, 문서 종류, 국가 등 정규화 | 공통 스키마 객체 |
| **Validate** | 중복, 결측, 날짜 충돌 검사 | quality_failures.jsonl |
| **Load** | 정리된 문서를 저장 | docs.jsonl |
| **Record** | 실행 이력과 품질 결과 저장 | events.jsonl, quality_report.md |
| **Search-ready** | 검색 가능한 형태로 준비 | BM25/간단 인덱스 |

핵심은 "가져오기"가 아니라  
**"가져온 문서를 같은 규칙으로 바꾸고, 품질을 확인하고, 추적 가능하게 남기는 것"**입니다.

---

## 7. 주요 기능

### 반드시 있어야 하는 기능

| 번호 | 기능 | 설명 |
|---|---|---|
| F1 | 2개국 자동 수집 | 한국·미국 공개 소스에서 문서를 가져옴 |
| F2 | 출처 카탈로그 | 어디서 어떤 데이터를 가져오는지 문서화 |
| F3 | 공통 스키마 통일 | 서로 다른 문서를 하나의 9개 필드 구조로 통일 |
| F4 | 필수값 검증 | 제목·날짜·링크 등 누락 감지 |
| F5 | 중복 감지 | 같은 문서가 두 번 들어오면 차단 |
| F6 | 품질 실패 기록 | 문제 건을 별도 JSONL로 저장 |
| F7 | 품질 리포트 생성 | 실행마다 리포트 자동 생성 |
| F8 | 실행 이력 저장 | run_id 단위로 결과와 로그 보존 |
| F9 | 검색 가능 상태 준비 | 간단 검색 또는 검색용 인덱스 구성 |

### 있으면 좋은 기능

| 번호 | 기능 | 설명 |
|---|---|---|
| O1 | 검증용 검색 UI | 문서가 실제로 검색 가능한지 확인하는 Streamlit UI |

---

## 8. 데이터 소스

| 국가 | 소스 | 접근 방식 | 비고 |
|---|---|---|---|
| KR | 국회 회의록 | PDF 크롤링 | 기존 프로젝트 자산 재사용 가능 |
| KR | 국가법령정보 Open API | API 호출 | 법령 데이터 구조화 |
| US | Congress.gov API | API 호출 | bill 중심 메타데이터 수집 |

### 왜 이 3개만 선택했나?

- **한국 2개 + 미국 1개**만으로도 다국가 파이프라인을 증명할 수 있기 때문
- 서로 다른 포맷(PDF / API)을 다룰 수 있기 때문
- 법률 데이터를 표준화하는 데 충분한 최소 범위이기 때문
- 14일 안에 끝낼 수 있는 현실적 범위이기 때문

---

## 9. 표준 데이터 양식 (Canonical Schema)

GovLex-Ops의 핵심은 **모든 문서를 같은 상자에 담는 것**입니다.

### 공통 9개 필드

| 필드 | 의미 |
|---|---|
| `source_id` | 문서 고유 ID |
| `jurisdiction` | 국가 (KR / US) |
| `source_type` | 문서 종류 (minutes / law / bill 등) |
| `language` | 언어 |
| `title` | 문서 제목 |
| `issued_date` | 발행일 |
| `source_url` | 원문 링크 |
| `content_hash` | 본문 기반 해시 |
| `ingested_at` | 수집 시각 |

### `metadata`에 들어가는 보조 정보

공통 필드에 다 넣기 어려운 값은 `metadata`에 넣습니다.

- **KR 예시**: 위원회명, 회차, 차수
- **US 예시**: congress, billType, sponsor, latestAction

### 왜 필드를 최소로 잡았나?

필드가 너무 많으면 국가마다 결측이 늘어나고, 스키마 유지가 어려워집니다.  
그래서 **공통 필드는 최소화**하고, 국가별 특수 정보는 `metadata`로 분리합니다.

### `metadata` 자유도에 대한 방어

`metadata`는 현재 `dict[str, Any]`로 **의도적으로 자유도를 열어둔** 영역입니다.  
이유는 다음과 같습니다.

- 국가/소스별로 필드 구조가 불안정해서 초반에 강제 스키마를 고정하면 수집이 막힘
- MVP 단계에서는 "어떤 필드가 실제로 필요한지"를 먼저 수집해서 관찰해야 함

단, 자유도는 방치하지 않습니다. 다음 원칙으로 관리합니다.

1. **네이밍 규약 고정**  
   - KR: `committee`, `session`, `sub_session`, …  
   - US: `congress`, `bill_type`, `sponsor`, `latest_action`, …
2. **관찰 → 승격**  
   - 반복적으로 쓰이는 key는 다음 스키마 버전에서 **공통 필드로 승격**
   - 또는 국가별 `KRMetadata` / `USMetadata` 서브모델로 고정
3. **깨진 값은 QA로 회수**  
   - 예정된 R06: `metadata` 필수 key 누락 (국가별) → 경고
   - 예정된 R07: `metadata` 타입 불일치 → 격리

즉, `metadata`는 "영원한 자유 공간"이 아니라  
**"스키마 승격 대기실"**로 설계되어 있습니다.

---

## 10. 품질 관리 (QA Rule Engine)

GovLex-Ops는 단순 수집기가 아니라 **품질검사 엔진이 붙은 수집기**입니다.

### 핵심 룰

| 룰 ID | 검사 내용 | 처리 방식 |
|---|---|---|
| R01 | 같은 문서 중복 적재 | 신규 문서 거부 |
| R02 | 필수 필드 결측 | 격리 + 실패 기록 |
| R05 | 같은 내용인데 날짜만 다름 | 병합 또는 검토 대상으로 표시 |

### 예약된 룰 (다음 단계)
| 룰 ID | 검사 내용 | 도입 시점 | 처리 방식(예정) |
|---|---|---|---|
| R03 | 본문 언어와 `language` 필드 불일치 | Week 3+ | 경고 + 언어 자동 판별 재태깅 |
| R04 | `source_url`이 유효하지 않거나 접근 불가 | Week 3+ | 실패 기록 + 재시도 큐로 격리 |

### 품질 산출물

- `quality_failures.jsonl` : 문제 건 상세 기록
- `quality_report.md` : 이번 실행 요약 보고서

즉, GovLex-Ops는 "수집 성공"만 기록하는 게 아니라  
**"무엇이 왜 실패했는지도 기록"**합니다.

---

## 11. 폴더 구조

```text
GovLex-Ops/
├── README.md
├── docs/
│   ├── source_catalog.md
│   ├── schema_v1.md
│   └── design_decisions.md
├── schemas/
│   ├── legal_document.schema.json
│   └── quality_failure.schema.json
├── src/govlexops/
│   ├── core/
│   │   ├── run_context.py
│   │   └── logging.py
│   ├── schemas/
│   │   └── legal_document.py
│   ├── etl/
│   │   ├── ingest/
│   │   │   ├── kr_assembly.py
│   │   │   ├── kr_law.py
│   │   │   └── us_congress.py
│   │   ├── normalize/
│   │   │   └── text_cleanser.py
│   │   └── pipeline.py
│   ├── qa/
│   │   ├── rules.py
│   │   └── report.py
│   └── search/
│       └── indexer.py
├── data_index/
│   ├── raw/
│   │   ├── kr/
│   │   └── us/
│   └── normalized/
│       └── docs.jsonl
├── runs/
│   └── run_YYYYMMDD_xxxxxx/
│       ├── events.jsonl
│       ├── quality_failures.jsonl
│       └── quality_report.md
├── tests/
│   ├── test_schema_validation.py
│   ├── test_qa_rules.py
│   └── test_pipeline_integration.py
├── app.py
├── requirements.txt
├── pyproject.toml
└── .env.example
```

---

## 12. 기술 스택

| 계층 | 선택 | 이유 |
|---|---|---|
| 언어 | Python 3.11+ | 기존 자산 활용 가능 |
| 데이터 검증 | pydantic v2 | 스키마 검증 자동화 |
| 저장 | JSONL | 단순하고 추적 쉬움 |
| 검색 | BM25 또는 가벼운 인덱스 | MVP 범위에 적합 |
| UI | Streamlit (선택) | 검증용 검색 화면 |
| 테스트 | pytest | 파이프라인 안정성 확인 |

### 왜 무거운 인프라를 안 쓰나?

이번 MVP의 목적은 **데이터 파이프라인 구조를 증명하는 것**입니다.  
그래서 처음부터 pgvector, Neo4j, Docker, GPU까지 넣기보다,
**로컬 한 줄 실행으로도 돌아가는 구조**를 우선합니다.

---

## 13. 실행 방법

### 환경 준비

```bash
git clone <this-repo>
cd GovLex-Ops

python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -e .
pip install -r requirements.txt

cp .env.example .env           # API 키 입력
```

### 파이프라인 실행

```bash
python -m govlexops.etl.pipeline --sources kr,us
```

실행이 끝나면 `runs/<run_id>/` 아래에 다음 파일이 생성됩니다:
- `events.jsonl` — 실행 이력
- `quality_failures.jsonl` — 품질 실패 건
- `quality_report.md` — 품질 요약 리포트

### 검증용 검색 UI (선택)

```bash
streamlit run app.py
```

### 테스트

```bash
pytest tests/
```

---

## 14. 이 프로젝트가 어디서 왔는가

GovLex-Ops는 완전히 새로 생긴 프로젝트가 아니라,
이전에 했던 프로젝트들의 강점을 **법률 데이터 파이프라인 방향으로 재조합한 결과물**입니다.

### 1) National_Assembly에서 가져온 것

- 한국 국회 회의록 데이터 자산
- PDF 기반 정책 문서 처리 경험
- 회의록 ETL/RAG 경험

### 2) HelixOps에서 가져온 것

- `run_id` 기반 실행 기록 구조
- 산출물/로그/검증을 분리하는 운영 감각
- raw / normalized 분리 철학
- 스키마 우선 설계 방식

### 3) 애널리스트 프로젝트에서 가져온 것

- ETL를 비전공자도 이해하게 설명하는 방식
- 원본을 문서화 레이어로 바꾸는 사고
- 메타데이터가 검색 품질을 좌우한다는 감각

즉,
- **GovLex-Ops** = 메인 프로젝트
- **HelixOps** = 운영 구조 참고서
- **애널리스트 프로젝트** = ETL/문서화 참고서

---

## 15. 실행 결과물

최종적으로 GovLex-Ops는 아래 결과물을 남깁니다.

### 데이터 자산
- `data_index/raw/...`
- `data_index/normalized/docs.jsonl`

### 실행 기록
- `runs/<run_id>/events.jsonl`

### 품질 관리 결과
- `runs/<run_id>/quality_failures.jsonl`
- `runs/<run_id>/quality_report.md`

### 검증
- 스키마 테스트
- QA 룰 테스트
- 파이프라인 통합 테스트

즉, 이 프로젝트의 끝은 챗봇이 아니라  
**"신뢰 가능한 법률 데이터 자산 + 실행 기록 + 품질 리포트"**입니다.

---

## 16. 시연 플로우

### 1분
프로젝트 한 줄 소개  
→ "한국과 미국의 법·입법 공개 데이터를 공통 스키마와 QA 룰로 정리하는 데이터 파이프라인입니다"

### 3분
데이터 소스 설명  
→ 어떤 사이트에서 어떤 데이터를 가져오는지 보여주기

### 3분
`docs.jsonl` 확인  
→ KR과 US 문서가 같은 필드 구조로 저장된 것을 보여주기

### 3분
`quality_report.md` 확인  
→ 중복, 결측, 날짜 충돌이 어떻게 기록되는지 보여주기

### 3분
`events.jsonl` 확인  
→ 실행 흔적이 남는 구조를 보여주기

### 2분
간단 검색 확인  
→ 키워드 검색 시 문서 제목, 국가, 날짜, 원문 링크가 나오는지 보여주기

---

## 17. CODIT Legal Data Specialist 직무 매핑

| CODIT JD 요구사항 | GovLex-Ops에서 증명하는 방식 |
|---|---|
| 글로벌 법률·규제 공개 데이터 리서치·확보 | `docs/source_catalog.md` — 2개국 3개 소스 + 라이선스·제한 명시 |
| 내부 데이터 표준에 맞춘 구조화·정제 | 9필드 canonical schema + pydantic 자동 검증 |
| 백엔드 개발자와 협업한 파이프라인 설계 | 모듈 분리(ingest/normalize/qa) + 어댑터 인터페이스 |
| 가공된 데이터 품질 검증(QA)·정확도/일관성 | `qa/rules.py` R01·R02·R05 + 자동 품질 리포트 |
| 데이터 관리 프로세스 개선·자동화 | run_id 실행 기록 + 리포트 자동 생성 + pytest 검증 |

---

## 18. 로드맵

### Week 1
- 레포 세팅
- run_id 구조 생성
- 9개 필드 스키마 확정
- 한국 데이터 연결

### Week 2
- 미국 Congress.gov 연결
- KR/US 통합 저장
- QA 룰 3개 구현
- 품질 리포트 자동 생성
- README/시연 정리

### Week 3+
- Federal Register 등 미국 규제 데이터 추가
- 검색 고도화
- RAG 연결
- GovLex-Chat 같은 활용 레이어 추가

---

## 19. 한 줄 요약

> **GovLex-Ops는 법률 문서를 해석하는 AI가 아니라, 법률·입법 공개 문서를 신뢰 가능한 데이터 자산으로 바꾸는 파이프라인입니다.**
