# GovLex-Ops

![CI](https://github.com/callmekjs/GOV_LEX/actions/workflows/ci.yml/badge.svg)
![Coverage](https://img.shields.io/badge/coverage-74%25-brightgreen)

> **한국과 미국의 법·입법 공개 데이터를 자동으로 수집하고, 하나의 표준 양식으로 정제하며, 품질을 숫자로 관리하는 데이터 파이프라인**

운영 지표는 [`docs/dashboard.md`](docs/dashboard.md) 에서 확인할 수 있습니다.
도메인 개념 초안은 [`docs/ontology/`](docs/ontology/) 에서 확인할 수 있습니다.
아키텍처 의사결정 기록은 [`docs/adr/`](docs/adr/) 에서 확인할 수 있습니다.

---

## 1. 이 프로젝트가 증명하는 것

> **"Legal Corpus를 다룰 줄 아는 데이터 엔지니어"**임을 증명합니다.

GovLex-Ops는 챗봇을 만드는 프로젝트가 아닙니다.  
이 프로젝트의 핵심은 **Legal Corpus를 Jurisdiction별로 수집하고,
입법 프로세스 단계(Bill → Act → Decree → Rule)에 맞춰
canonical schema로 표준화하는 데이터 인프라**입니다.

즉, Chat CODIT 같은 Regulatory Intelligence 서비스에 투입 가능한
Legal Document를 생산하는 백엔드 역할을 가정합니다.

이 프로젝트는 아래를 보여주기 위한 포트폴리오입니다.

- 여러 공개 소스(KR 법제처·KR 국회·US Congress)에서 **Statute, Bill, Minutes**를 안정적으로 수집할 수 있다.
- 한국·미국의 서로 다른 법제 구조를 하나의 공통 스키마로 매핑할 수 있다.
- 데이터 품질 문제(중복·결측·Jurisdiction 불일치)를 자동으로 감지하고 기록할 수 있다.
- 실행 결과를 run_id 단위로 추적 가능한 형태로 남길 수 있다.
- RAG·Policy Monitoring 같은 응용 레이어의 기반 데이터를 만들 수 있다.

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
- **파이프라인에 연결된 소스 (3개)**:
  - 한국 국가법령정보 Open API (`kr_law.py`) — 현행 법령
  - 한국 열린국회정보 Open API (`assembly_bills.py`) — 발의 법안
  - 미국 Congress.gov API v3 (`us_congress.py`) — 법안
- **문서·로드맵에만 있는 소스 (미연결)**: 국회 회의록 PDF, Federal Register 등은 `docs/source_catalog.md` Week 3+ 항목 참고

### 이번 MVP에서 의도적으로 제외한 것

| 제외 항목 | 이유 |
|---|---|
| 뉴스 수집 | 법·입법 문서 표준화에 집중하기 위해 |
| 일본 등 제3국 확장 | 2주 안에 KR+US 2개국 완성이 우선 |
| LLM 답변 생성 | 데이터 품질 증명이 목적. LLM 답변 품질은 변수가 너무 많음 |
| 자동 스케줄링 | 수동 실행 + 문서화로 대체 가능 |
| 복잡한 외부 DB 인프라 | 로컬 파일만으로 재현성 보장. 확장은 어댑터만 맞추면 됨 |

즉, 이 프로젝트는 **넓고 화려한 서비스**보다  
**작지만 끝까지 동작하는 데이터 파이프라인**을 목표로 합니다.

---

## 5. 전체 구조

```text
[공개 데이터 소스]
   ├─ 한국 국가법령정보 Open API   (source_type: law)
   ├─ 한국 열린국회정보 Open API   (source_type: bill)
   └─ 미국 Congress.gov API        (source_type: bill)

                ↓

           [GovLex-Ops]
   수집 → 표준 스키마 변환 → QA → 저장 + 영구 중복 기억

                ↓

    [정리된 통합 데이터 저장소]
   ├─ data_index/normalized/docs.jsonl        ← 통과 문서 (JSONL)
   ├─ data_index/normalized/seen_hashes.jsonl ← content_hash 중복 방지
   ├─ data_index/quality/failures.jsonl       ← 누적 품질 실패 (report 연동)
   ├─ runs/<run_id>/events.jsonl
   ├─ runs/<run_id>/quality_failures.jsonl
   └─ runs/<run_id>/quality_report.md

                ↓

      [검증용 검색(app.py) / 이후 RAG 연결 가능]
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

### 입법 프로세스와 `source_type` 매핑

본 파이프라인은 양국의 입법 프로세스를 데이터 모델로 추상화합니다.

| 단계 | 한국어 | 영어 | source_type | 수집 소스 |
|---|---|---|---|---|
| 1. 발의 | 법률안 발의 | Bill Introduction | `bill` | 열린국회 ALLBILLV2, Congress.gov |
| 2. 심사 | 상임위원회 심사 | Committee Review | `minutes` | 국회 회의록 API (Week 3+) |
| 3. 의결 | 본회의 의결 | Floor Vote | — | (상태값으로 반영) |
| 4. 공포 | 공포·시행 | Promulgation / Enforcement | `law` | 국가법령정보 API |
| 5. 하위법령 | 시행령·시행규칙 | Decree, Rule | `decree`, `rule` | 국가법령정보 API (Week 3+) |

**현재 MVP는 1·4단계를 수집 완료**, 2·5단계는 Week 3+ 확장 범위입니다.  
3단계(의결)는 별도 타입이 아니라 `metadata.status`(예: "계류"/"가결")로 추적합니다.

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

| 국가 | 소스 | 접근 방식 | 파이프라인 연결 |
|---|---|---|---|
| KR | 국가법령정보 Open API | REST (OC 키) | 연결됨 (`kr_law.py`, 다중 쿼리 `fetch_laws_bulk`) |
| KR | 열린국회정보 Open API | REST (API 키) | 연결됨 (`assembly_bills.py`, 제21·22대) |
| US | Congress.gov API v3 | REST (API 키) | 연결됨 (`us_congress.py`) |

상세·건수·제한 사항은 `docs/source_catalog.md` 참고.

### 왜 이 3개 소스로 증명하나?

- **2개국·3개 소스**만으로도 스키마 통일·QA·실행 추적을 끝까지 보여줄 수 있음
- API 기반이라 재현·문서화가 쉬움
- 한국은 `law`(통과된 법령) + `bill`(발의 법안)을 동시에 다뤄 **입법 프로세스 추적**이 가능
- 국회 회의록 PDF 등은 동일 카탈로그에 **추가 예정**으로 두고, Week 3+에서 어댑터만 붙이면 확장 가능

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
| `content_hash` | 정규화된 식별 메타데이터(제목·발행일·식별자)의 SHA-256 해시 — **본문 해시 아님** ([docs/schema_v1.md §6](docs/schema_v1.md#6-content_hash-생성-규칙)) |
| `ingested_at` | 수집 시각 |

> ⚠️ **`content_hash` 정의 주의** — 이 해시는 본문 텍스트가 아니라 `(제목, 발행일, 소스 식별자)`를 정규화·결합해 SHA-256으로 계산합니다.
> 공개 API의 본문 제공 일관성 문제로 현재는 메타데이터 ID 해시 방식을 채택했습니다. 본문 기반 해시 승격은 Phase 3+ 고도화 항목으로 유지합니다 ([pipline_upgrade.md](pipline_upgrade.md), [schema_v1.md §6](docs/schema_v1.md#6-content_hash-생성-규칙)).

### `metadata`에 들어가는 보조 정보

공통 필드에 다 넣기 어려운 값은 `metadata`에 넣습니다.

- **KR 예시**: 위원회명, 회차, 차수, 발의자, 의안 진행 상태
- **US 예시**: congress, billType, sponsor, latestAction

### 왜 필드를 최소로 잡았나?

필드가 너무 많으면 국가마다 결측이 늘어나고, 스키마 유지가 어려워집니다.  
그래서 **공통 필드는 최소화**하고, 국가별 특수 정보는 `metadata`로 분리합니다.

### `source_type` 분류 근거

법률 문서는 **효력 위계**와 **생산 단계**에 따라 분류됩니다.  
본 파이프라인의 `source_type` 5개는 한국·미국 법제의 공통 분모에서 도출했습니다.

**한국 법제 위계 (Korean Legal Hierarchy)**:
```
법률 (Act)                          ── 국회 통과, 최상위
  └ 시행령 (Presidential Decree)     ── 대통령령
      └ 시행규칙 (Enforcement Rule)  ── 부령·총리령
          └ 행정규칙 (Administrative Rule) ── 훈령·예규·고시
```

**미국 법제 위계 (U.S. Legal Hierarchy)**:
```
Public Law                               ── 의회 통과 법률
  └ CFR (Code of Federal Regulations)    ── 연방 규정집
      └ Agency Rule                      ── 각 기관 내부 규칙
```

**공통 분모 → `source_type` 5개**:

| source_type | 한국어 | 영어 | 비고 |
|---|---|---|---|
| `law` | 법률 | Act / Public Law | 최상위 효력 |
| `decree` | 시행령 | Presidential Decree | 법률의 시행 세부 |
| `rule` | 시행규칙·행정규칙 | Enforcement Rule / Agency Rule | 행정 집행 |
| `bill` | 법안 (미통과) | Bill (Pending) | HR, S, 법률안 |
| `minutes` | 회의록 | Minutes / Hearing | 심사 과정 기록 |

이 분류는 향후 `treaty`(조약), `precedent`(판례)로 확장될 수 있습니다.

### `metadata` 자유도에 대한 방어

`metadata`는 현재 `dict[str, Any]`로 **의도적으로 자유도를 열어둔** 영역입니다.  
이유는 다음과 같습니다.

- 국가/소스별로 필드 구조가 불안정해서 초반에 강제 스키마를 고정하면 수집이 막힘
- MVP 단계에서는 "어떤 필드가 실제로 필요한지"를 먼저 수집해서 관찰해야 함

단, 자유도는 방치하지 않습니다. 다음 원칙으로 관리합니다.

1. **네이밍 규약 고정**  
   - KR: `committee`, `session`, `sub_session`, `proposer_type`, `bill_status`, …  
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
| R07 | 비정상/파싱실패 발행일 | 격리 + 실패 기록 |
| R05 | 같은 내용인데 날짜만 다름 | 병합 또는 검토 대상으로 표시 |

> R07 도입 배경 ([pipline_upgrade 0-4](pipline_upgrade.md)): 이전엔 수집기가 발행일 파싱에 실패하면 `date(2000, 1, 1)`을 박고 silently 통과시켰다. 이제는 sentinel `date(1900, 1, 1)` + `metadata.date_parse_failed=True`를 남기고 R07이 명시적으로 격리한다. 어떤 문서가 왜 빠졌는지 quality_report.md에 그대로 드러난다.

### 예약된 룰 (다음 단계)
| 룰 ID | 검사 내용 | 도입 시점 | 처리 방식(예정) |
|---|---|---|---|
| R03 | 본문 언어와 `language` 필드 불일치 | Week 3+ | 경고 + 언어 자동 판별 재태깅 |
| R04 | `source_url`이 유효하지 않거나 접근 불가 | Week 3+ | 실패 기록 + 재시도 큐로 격리 |

### 품질 산출물

- `quality_failures.jsonl` : 문제 건 상세 기록
- `quality_report.md` : 이번 실행 요약 보고서
- `data_index/quality/failures.jsonl` : **전체 실행 누적 실패 로그** (운영 대시보드/통계용)

즉, GovLex-Ops는 "수집 성공"만 기록하는 게 아니라  
**"무엇이 왜 실패했는지도 기록"**합니다.

---

## 11. 폴더 구조

```text
Gov_Lex/
├── Readme.md
├── docs/
│   ├── adr/
│   │   ├── ADR-001.md
│   │   ├── ...
│   │   └── ADR-007.md
│   ├── dashboard.md
│   ├── failure_patterns.md
│   ├── ontology/
│   │   ├── concepts.md
│   │   ├── relations.md
│   │   └── kr_us_mapping.md
│   ├── schema_v1.md
│   ├── source_catalog.md
│   └── design_decisions.md
├── configs/
│   ├── pipeline.yaml
│   ├── dev.yaml
│   └── prod.yaml
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── schemas/
│   ├── legal_document.schema.json
│   └── quality_failure.schema.json
├── src/govlexops/
│   ├── core/
│   │   ├── config.py
│   │   ├── event_log.py
│   │   ├── raw_store.py
│   │   ├── replay.py
│   │   ├── run_context.py
│   │   ├── storage.py
│   │   └── seen_store.py
│   ├── integrations/store/
│   │   ├── base.py
│   │   ├── factory.py
│   │   ├── jsonl_store.py
│   │   └── sqlite_store.py
│   ├── schemas/
│   │   └── legal_document.py
│   ├── etl/
│   │   ├── ingest/
│   │   │   ├── kr_law.py
│   │   │   ├── assembly_bills.py
│   │   │   └── us_congress.py
│   │   └── pipeline.py
│   ├── qa/
│   │   ├── failure_catalog.py
│   │   ├── rules.py
│   │   └── report.py
│   └── search/
│       └── indexer.py
├── data_index/
│   ├── raw/
│   │   └── <source>/<date>/*.json.gz
│   ├── quality/
│   │   ├── failures.jsonl
│   │   └── failure_catalog.jsonl
│   ├── extracted/
│   ├── chunks/
│   ├── embeddings/
│   └── normalized/
│       ├── docs.jsonl
│       ├── docs.sqlite
│       └── seen_hashes.jsonl
├── runs/
│   └── run_YYYYMMDD_HHMMSS_xxxxxx/
│       ├── events.jsonl
│       ├── metrics.json
│       ├── quality_failures.jsonl
│       └── quality_report.md
├── tests/
│   ├── test_config.py
│   ├── test_failure_catalog.py
│   ├── test_metrics_dashboard.py
│   ├── test_raw_store.py
│   ├── test_replay.py
│   ├── test_store_adapters.py
│   └── ...
├── scripts/
│   ├── analyze_failures.py
│   ├── build_dashboard.py
│   ├── build_docker.sh
│   ├── run_pipeline.sh
│   ├── replay_run.sh
│   └── smoke_test.sh
├── app.py
├── requirements.txt
├── pyproject.toml
├── .pre-commit-config.yaml
└── .env (또는 .env.example 참고)
```

---

## 12. 기술 스택

| 계층 | 선택 | 이유 |
|---|---|---|
| 언어 | Python 3.11+ | 기존 자산 활용 가능 |
| 데이터 검증 | pydantic v2 | 스키마 검증 자동화 |
| 저장 | JSONL + SQLite Adapter | 초기 단순성 + 확장성 |
| 검색 | BM25 또는 가벼운 인덱스 | MVP 범위에 적합 |
| UI | Streamlit (선택) | 검증용 검색 화면 |
| 테스트 | pytest | 파이프라인 안정성 확인 |
| 코드 품질 | ruff + pre-commit | 커밋 전 자동 검사/포맷 |
| 재현성 | Docker / docker-compose | 신규 머신에서 동일 실행 |

### 왜 무거운 인프라를 안 쓰나?

이번 MVP의 목적은 **데이터 파이프라인 구조를 증명하는 것**입니다.  
그래서 처음부터 pgvector, Neo4j, Docker, GPU까지 넣기보다,
**로컬 한 줄 실행으로도 돌아가는 구조**를 우선합니다.

---

## 13. 실행 방법

### 환경 준비

```bash
git clone <저장소 URL>
cd Gov_Lex

python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -e .
pip install -r requirements.txt
pip install pytest             # 테스트 실행 시

# 프로젝트 루트에 .env 생성 후 다음 키 입력:
# LAW_GO_KR_OC=...
# CONGRESS_GOV_API_KEY=...
# OPEN_ASSEMBLY_API_KEY=...
```

실행 시 패키지를 찾지 못하면 **저장소 루트에서** `PYTHONPATH`에 `src`를 넣습니다 (PowerShell 예: `$env:PYTHONPATH="src"`).

### 파이프라인 실행

```bash
python -m govlexops.etl.pipeline
# 또는 프로파일 분기
python -m govlexops.etl.pipeline --config configs/dev.yaml
python -m govlexops.etl.pipeline --config configs/prod.yaml
```

저장소 백엔드는 `configs/*.yaml`의 `store_backend`로 선택합니다.

- `store_backend: jsonl` (기본)
- `store_backend: sqlite` (`sqlite_path` 경로 사용)
- `store_backend: pgvector` (예약됨, Phase 4 예정)

### Docker 재현 실행 (Phase 2-1)

```bash
# 이미지 빌드
docker build -t govlexops:latest -f docker/Dockerfile .

# 컨테이너 실행 (runs/data_index 볼륨 마운트)
docker run --rm -v $(pwd)/runs:/app/runs -v $(pwd)/data_index:/app/data_index --env-file .env govlexops:latest --config configs/pipeline.yaml

# compose 실행 (옵션: db/graph 프로파일)
docker compose -f docker/docker-compose.yml up --build pipeline
```

> Windows PowerShell에서는 `$(pwd)` 대신 `${PWD}` 또는 절대 경로를 사용하세요.

실행이 끝나면 `runs/<run_id>/` 아래에 다음 파일이 생성됩니다:
- `events.jsonl` — 실행 이력
- `metrics.json` — 실행 메트릭(수집/통과/룰별 실패/소스별 건수)
- `quality_failures.jsonl` — 품질 실패 건
- `quality_report.md` — 품질 요약 리포트

운영 대시보드 갱신:

```bash
python scripts/build_dashboard.py
```

## 운영 스크립트 (Phase 2-1)

- `scripts/build_docker.sh` — Docker 이미지 빌드
- `scripts/run_pipeline.sh` — 파이프라인 실행 + 대시보드 갱신
- `scripts/smoke_test.sh` — lint/type/test + dev 실행 스모크 테스트
- `scripts/replay_run.sh` — Replay 실행 래퍼
- `scripts/analyze_failures.py` — Failure Catalog 패턴 리포트 생성

Replay 예시:

```bash
python -m govlexops.services.cli replay --run-path runs/run_20260501_123456_abcd12
python -m govlexops.services.cli replay --run-path runs/run_20260501_123456_abcd12 --only-failures
python -m govlexops.services.cli replay --run-path runs/run_20260501_123456_abcd12 --regenerate-report
```

### 검증용 검색 UI (선택)

```bash
streamlit run app.py
```

검색 모드:
- `하이브리드` (기본): BM25 + 벡터 유사도(해시 벡터 코사인) 결합
- `BM25`: 기존 키워드 검색

동의어 확장 예시:
- `AI` ↔ `인공지능`
- `privacy` ↔ `개인정보`

### 테스트

```bash
pytest tests/ -v
```

(현재 **96개** 테스트 PASS — 수집기 mock/HTTP/atomic/logging/config/replay/raw/failure_catalog/adapter 포함.)

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
- `data_index/raw/<source>/<date>/*.json.gz` — 원본 API 응답 보관 (ETL raw 레이어)
- `data_index/normalized/docs.jsonl` — 통과 문서 (줄 단위 JSON)
- `data_index/normalized/docs.sqlite` — SQLite adapter 백엔드(선택)
- `data_index/normalized/seen_hashes.jsonl` — `content_hash` 영구 중복 기억 (QA R01)
- `data_index/quality/failures.jsonl` — 품질 실패 누적 로그
- `data_index/quality/failure_catalog.jsonl` — 실패 카탈로그 누적

### 실행 기록
- `runs/<run_id>/events.jsonl`
- `runs/<run_id>/metrics.json`

### 품질 관리 결과
- `runs/<run_id>/quality_failures.jsonl`
- `runs/<run_id>/quality_report.md`
- `docs/failure_patterns.md` (카탈로그 집계)

### 관계 추출 결과 (Phase 3-3)
- `data_index/extracted/entities.jsonl` — 의원/위원회 엔티티
- `data_index/extracted/relations.jsonl` — `PROPOSED_BY`, `REVIEWED_BY` 관계

### 검증
- `pytest tests/ -v` → **96개 PASS**
- 주요 추가 영역: replay, raw_store, failure_catalog, store_adapters, config

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
간단 검색 확인 (`streamlit run app.py`)  
→ 키워드 검색 시 문서 제목, 국가, 날짜, 원문 링크가 나오는지 보여주기

---

## 17. Before / After (수치 증명)

| 항목 | Before | After | 확인 방법 |
|---|---|---|---|
| 중복 적재율 | 측정 불가 (기억 없음) | **0%** | 파이프라인 2회 실행 → 2회차 전량 거부 |
| 수집 소스 | 1개국 1개 소스 | **2개국 3개 소스** | `docs/source_catalog.md` |
| 표준화 커버리지 | 단일 포맷 | **전체 문서 동일 9필드** | `data_index/normalized/docs.jsonl` |
| 품질 리포트 | 없음 | **매 실행 자동 생성** | `runs/<run_id>/quality_report.md` |
| 실행 추적 | 없음 | **100% run_id 보존** | `runs/` 폴더 누적 확인 |
| 테스트 | 0개 | **96개 전부 PASS** | `pytest tests/ -v` |
| 재현 실행 | 없음 | **Docker/Compose로 재현 가능** | `docker compose -f docker/docker-compose.yml up --build pipeline` |
| 실패 분석 | 단순 로그 | **Failure Catalog + 패턴 문서** | `python scripts/analyze_failures.py` |
| 저장 백엔드 | JSONL 고정 | **JSONL/SQLite 전환 가능** | `configs/*.yaml`의 `store_backend` |
| **도메인 매핑** | **없음** | **입법 프로세스 5단계 ↔ source_type 5개 매핑** | **`Readme.md` §6, §9** |

---

## 18. CODIT Legal Data Specialist 직무 매핑

| CODIT JD 요구사항 | 증명 | 코드 링크 |
|---|---|---|
| 글로벌 법률·규제 공개 데이터 리서치·확보 | KR/US 3개 공개 소스를 수집 카탈로그로 문서화 | [`docs/source_catalog.md`](docs/source_catalog.md), [`kr_law.py`](src/govlexops/etl/ingest/kr_law.py), [`assembly_bills.py`](src/govlexops/etl/ingest/assembly_bills.py), [`us_congress.py`](src/govlexops/etl/ingest/us_congress.py) |
| 내부 데이터 표준에 맞춘 구조화·정제 | 9필드 canonical schema + metadata 정책 + source_type 매핑 | [`legal_document.py`](src/govlexops/schemas/legal_document.py), [`docs/schema_v1.md`](docs/schema_v1.md), [`docs/ontology/kr_us_mapping.md`](docs/ontology/kr_us_mapping.md) |
| 백엔드 협업 가능한 파이프라인 설계 | ingest/core/qa/integrations 모듈 분리 + 저장소 어댑터 | [`pipeline.py`](src/govlexops/etl/pipeline.py), [`integrations/store/base.py`](src/govlexops/integrations/store/base.py), [`integrations/store/factory.py`](src/govlexops/integrations/store/factory.py) |
| 가공 데이터 품질 검증(정확도/일관성) | QA 룰 + 품질 리포트 + 실패 카탈로그/패턴 분석 | [`qa/rules.py`](src/govlexops/qa/rules.py), [`qa/report.py`](src/govlexops/qa/report.py), [`qa/failure_catalog.py`](src/govlexops/qa/failure_catalog.py), [`docs/failure_patterns.md`](docs/failure_patterns.md) |
| 데이터 관리 프로세스 개선·자동화 | CI/정적검사/테스트 게이트 + run metrics/dashboard 자동 생성 | [`.github/workflows/ci.yml`](.github/workflows/ci.yml), [`.pre-commit-config.yaml`](.pre-commit-config.yaml), [`pipeline.py`](src/govlexops/etl/pipeline.py), [`scripts/build_dashboard.py`](scripts/build_dashboard.py), [`docs/dashboard.md`](docs/dashboard.md) |
| 재현성/운영 안정성 | Docker/Compose 실행 + Replay 재검증 + run 단위 산출물 격리 | [`docker/Dockerfile`](docker/Dockerfile), [`docker/docker-compose.yml`](docker/docker-compose.yml), [`core/replay.py`](src/govlexops/core/replay.py), [`services/cli.py`](src/govlexops/services/cli.py) |
| 의사결정 문서화 | ADR 7개로 설계 근거와 트레이드오프를 명시 | [`docs/adr/`](docs/adr/), [`ADR-005.md`](docs/adr/ADR-005.md), [`ADR-007.md`](docs/adr/ADR-007.md) |
| 정형/비정형 표준화 | BPMBILLSUMMARY 자유 텍스트를 `metadata.summary`로 표준 객체에 흡수 | [`assembly_bills.py`](src/govlexops/etl/ingest/assembly_bills.py), [`legal_document.py`](src/govlexops/schemas/legal_document.py) |
| 관계형 확장성(KG 기초) | 의원/위원회 엔티티 + PROPOSED_BY/REVIEWED_BY 관계 추출 | [`etl/extract.py`](src/govlexops/etl/extract.py), [`data_index/extracted/entities.jsonl`](data_index/extracted/entities.jsonl), [`data_index/extracted/relations.jsonl`](data_index/extracted/relations.jsonl) |

상세 매핑표(면접용 풀버전): [`docs/scoring_mapping.md`](docs/scoring_mapping.md)

---

## 19. 로드맵

### Phase 0~2 (완료)
- Phase 0: 무결성/안정성 복구 (R01 타이밍, HTTP 통일, R07, atomic write)
- Phase 1: 운영 인프라 (mock tests, CI, metrics/dashboard, config 분리, pre-commit)
- Phase 2: 운영 패턴 이식 (Docker/scripts, Replay, raw 레이어, ontology 초안, failure catalog, store adapter)

### Phase 3 (진행 예정)
- ADR 7개 작성 ✅ (완료)
- entities/relations 추출 파이프라인 ✅ (완료)
- (옵션) 하이브리드 검색(BM25+벡터) ✅ (완료)
- decree/minutes 1종 추가
- CODIT 매핑표 + `docs/scoring_mapping.md` ✅ (완료)

### Phase 4 (진행 예정)
- 챗봇 프로젝트 부트스트랩
- RAG 백엔드 + 출처 인용 강제
- eval 셋 + LLM-as-Judge
- Streamlit 챗 UI + 통합 데모

---

## 20. 한 줄 요약

> **GovLex-Ops는 법률 문서를 해석하는 AI가 아니라, Legal Corpus를 Jurisdiction·입법 프로세스별로 수집·표준화하는 데이터 파이프라인입니다.**

---

<!-- AUTO_PHASE_SYNC:START -->
### 자동 동기화 상태
- 마지막 완료 페이즈: **3-5**
- 다음 권장 페이즈: **3-6**
- 동기화 시각: 2026-05-01 21:58

#### 최근 완료 페이즈 (최신순)
| Phase | 요약 |
|---|---|
| 3-5 | `Readme.md` §18을 '증거 링크' 중심 매핑표로 개편하고 `docs/scoring_mapping.md`를 신설해 CODIT JD 항목별 코드/문서 경로를 고정. 면접에서 '어디 코드냐' 질문에 5초 내 답할 수 있는 링크형 증거 맵을 완성. |
| 3-4 | `search/indexer.py`에 BM25+벡터 하이브리드 점수 결합(0.6/0.4)과 KR/EN 동의어 확장을 적용. `app.py`에서 모드 토글로 비교 검색이 가능해졌고, 'AI' 질의가 '인공지능' 문서를 찾는 회귀 테스트를 추가. |
| 3-3 | `src/govlexops/etl/extract.py`를 추가해 국회 법안 metadata(`ppsr_nm`, `jrcmit_nm`)에서 엔티티/관계를 추출하고 `data_index/extracted/entities.jsonl`, `relations.jsonl`로 누적 저장. 파이프라인에 `extract_done` 이벤트를 연결해 run 단위 관측이 가능해졌습니다. |
| 3-1 | `docs/adr/ADR-001~007` 작성으로 JSONL 선택, content_hash 정의, metadata 승격 정책, QA 분리, run_id 격리, config 외부화, 검색 마이그레이션 트리거를 의사결정 문서로 고정. README에 Architecture Decisions 링크를 연결. |
| 2-6 | `integrations/store/`에 `DocumentStore` 인터페이스 + `jsonl_store.py`/`sqlite_store.py` 추가. `create_document_store()` 팩토리로 `store_backend`를 주입해 같은 파이프라인 코드로 JSONL/SQLite 전환 가능. 어댑터 테스트 2건 추가 후 전체 96 passed. |
| 2-5 | `qa/failure_catalog.py`로 실패 카탈로그(`data_index/quality/failure_catalog.jsonl`) 누적 기록. `scripts/analyze_failures.py`로 rule/source_type/jurisdiction 패턴을 `docs/failure_patterns.md` 생성. 파이프라인 시작 시 카탈로그 요약 로그 출력. |
| 2-4 | `docs/ontology/concepts.md`, `relations.md`, `kr_us_mapping.md`로 온톨로지 초안 작성. active/pending 구분, relation별 근거 필드와 confidence를 명시해 Phase 3-3의 entities/relations 추출 기준을 고정. |
| 2-3 | `core/raw_store.py`로 API 원본 응답 gzip 보관(`data_index/raw/<source>/<date>/...`) 추가. 파이프라인 시작 시 `raw/normalized/extracted/chunks/embeddings/quality` 6개 디렉터리 자동 생성. 수집기 3종에 raw 저장 플래그 주입 후 전체 92 passed. |
| 2-2 | `src/govlexops/services/cli.py`(Typer)로 `run`/`replay` 커맨드 추가. `src/govlexops/core/replay.py`에서 run 경로 기준 재검증(`--only-failures`, `--regenerate-report`) 구현 후 `replay_report.md` 생성. replay 테스트 3건 포함 전체 90 passed. |
| 2-1 | `docker/Dockerfile`, `docker/docker-compose.yml` 추가로 컨테이너 재현 실행 경로 확보. `scripts/build_docker.sh`, `run_pipeline.sh`, `smoke_test.sh`, `replay_run.sh` 풀세트 구성. `docker build`와 `docker compose config` 검증 통과. |
<!-- AUTO_PHASE_SYNC:END -->
