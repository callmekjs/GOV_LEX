# GovLex-Ops 마스터 플랜 — 5.8 → 9.0+ → CODIT 합격

> **이 문서 하나만 보면서 작업합니다.**
> 가고 싶은 회사(CODIT) → 두 프로젝트(파이프라인 + 챗봇) → 5~8주 로드맵 → 면접 준비물까지 전부.
>
> *(원래 이름: `pipline_upgrade.md`. 마스터 플랜으로 승격하면서 `masterplan.md`로 변경.)*

---

## 0. 한눈에

### 0-1. 목표 한 줄
> **"CODIT Legal Data Specialist 합격을 위한, GovLex-Ops 데이터 파이프라인 + LLM 챗봇 풀스택 포트폴리오 마스터 플랜."**

### 0-2. 두 프로젝트 페어링 그림

```
┌──────────────────────────┐         ┌──────────────────────────┐
│  프로젝트 A : Gov_Lex    │ ──────> │  프로젝트 B : LLM 챗봇    │
│  (데이터 파이프라인)      │ docs   │  (Chat CODIT 미니 클론)   │
│                          │ .jsonl │                          │
│  • KR 법령 + 국회 + US   │         │  • RAG (BM25+벡터)       │
│  • 9필드 canonical       │         │  • 출처 인용 강제         │
│  • QA R01·R02·R05·R07    │         │  • eval 셋 100개         │
│  • atomic write          │         │  • Streamlit UI          │
└──────────────────────────┘         └──────────────────────────┘
            │                                       │
            └────────── 같은 데이터·같은 DB ─────────┘
                              │
                              ▼
                  ┌─────────────────────────┐
                  │  CODIT JD ~93/100 매칭   │
                  │  Legal Data Specialist  │
                  └─────────────────────────┘
```

### 0-3. 진행 현황 (이 표가 마스터 진행 추적)

| Phase | 기간 | 점수 | 상태 |
|-------|------|------|------|
| **Phase 0** — 결함 복구 | 1주 | 5.8 → **7.0** | ✅ 완료 (2026-04-30) |
| Phase 1 — 운영 인프라 | 1주 | 7.0 → 7.5 | ✅ 완료 (2026-05-01) |
| Phase 2 — 운영 패턴 이식 (Helixops 선별) | 2주 | 7.5 → 8.5 | ✅ 완료 (2026-05-01) |
| Phase 3 — 차별화 마무리 | 1주 | 8.5 → 9.0+ | 진행 예정 |
| **Phase 4** — 챗봇 프로젝트 | 2~3주 | → 9.5+ | 진행 예정 (Phase 3 후) |
| 폴리싱·면접 준비 | 1주 | 9.5+ | 진행 예정 |

→ **총 7~8주.** 하루 2~3시간 기준.

### 0-4. 점수 정량 추적 (자세한 건 §13)

```
2026-04-30 ┃ 5.8 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Baseline (CTO 평가)
           ┃    ↓ 0-1 R01 mark_seen 버그 수정
           ┃ 6.0
           ┃    ↓ 0-2 content_hash 정의 일치
           ┃ 6.2
           ┃    ↓ 0-3 공통 HTTP 클라이언트
           ┃ 6.5
           ┃    ↓ 0-4 R07 격리
           ┃ 6.7
           ┃    ↓ 0-5 logging
           ┃ 6.8
           ┃    ↓ 0-6 atomic write
2026-04-30 ┃ 7.0 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ★ Phase 0 완료 (현재)
                    ↓
                  목표: 9.0+
```

---

## 1. 목표 회사 — CODIT Legal Data Specialist

### 1-1. 회사·포지션 요약

| 항목 | 내용 |
|------|------|
| 회사 | **CODIT** (글로벌 리걸테크) |
| 포지션 | **Legal Data Specialist** |
| 핵심 책임 | **Chat CODIT** (생성형 AI 기반 규제·정책 모니터링) 활용 데이터 총괄 |
| 데이터 범위 | 한국 + 미국 + 글로벌 법률·규제·정책 공개 데이터 |

### 1-2. 왜 이 회사인가

1. **한·미 법률 데이터 글로벌 스케일** — 내가 만들고 있는 GovLex-Ops가 정확히 그 도메인
2. **Chat CODIT 운영 중** — 데이터 인프라 + AI 응용 두 역량 다 필요
3. **두 포트폴리오 페어링이 JD에 정확 매칭** — 매칭률 ~93/100

### 1-3. JD 항목 ↔ 내 포트폴리오 매핑

#### 담당 업무 (5개 모두 매칭)

| JD 담당 업무 | Gov_Lex 매칭 증거 | 챗봇 매칭 |
|---|---|---|
| 글로벌 법률·규제·정책 공개 데이터 리서치·확보 | KR(법제처) + US(Congress.gov) + 국회(열린국회정보) 3개 소스 직접 통합 | — |
| 내부 데이터 표준에 맞춘 구조화·정제 | `LegalDocument` 9필드 canonical schema, `schema_v1.md` 박제 | RAG 청크 표준화 |
| 백엔드 개발자와 협업한 파이프라인 설계 | ETL 파이프라인 + ADR 7개 + Replay 모드 | RAG API 인터페이스 |
| 가공된 데이터 품질 검증(QA)·정확도/일관성 | R01·R02·R05·R07 4개 룰 + `quality_report.md` | eval 셋 100개 + 정량 측정 |
| 데이터 관리 프로세스 개선·자동화 | **5.8 → 9.0+ 자체 6단계 개선 기록 + 24단계 로드맵** | LLM-as-Judge 자동 측정 |

#### 자격 조건 (4개 매칭, 학력 1개 본인 답변)

| JD 자격 | 매칭 증거 |
|---|---|
| 4년제 대학 졸업 (법학·정치학·국제학·데이터 우대) | (본인) |
| 해외 정부·의회 웹사이트 (영어 필수) | Congress.gov API 영어 응답 직접 파싱, KNOWN_AI_BILLS 등 |
| 리서치·크롤링·DB 관리 + QA 경험 | 3개 API 직접 통합 + atomic write + R01~R07 룰 엔진 |
| 세부 사항을 꼼꼼하게 + 데이터 정확성 높은 기준 | **직접 발견·해결한 3대 무결성 이슈** (R01 / content_hash / 2000-01-01) |
| Jira·Notion·Slack 협업 툴 | GitHub Issue/PR 패턴으로 대체 |

#### 우대 조건 (4개 모두 매칭)

| JD 우대 | 매칭 증거 |
|---|---|
| 법률·정책·컴플라이언스 도메인 지식 | `docs/legal_domain.md` (확장 예정) |
| Python·SQL 데이터 처리 | Python 전체 ETL + Phase 2-6 SQLite Adapter |
| **정형/비정형 데이터 표준화** | 정형: API JSON → 9필드 / 비정형: BPMBILLSUMMARY 자유 텍스트 → `metadata.summary` |
| **글로벌·멀티링구얼 데이터** | **한국어(KR) + 영어(US) 동일 스키마 통일** — CODIT 정체성 그 자체 |

### 1-4. Chat CODIT 발견 — 챗봇 포트폴리오의 정당성

JD 본문 인용:
> "**생성형 AI 기반 질의응답형 규제·정책 모니터링 서비스 'Chat CODIT'에 활용되는 기반 데이터를 총괄**"

→ **CODIT은 이미 LLM 챗봇을 운영 중**.
→ 내가 만드는 두 번째 포트폴리오(LLM 챗봇) = **Chat CODIT의 미니 클론**.
→ 면접관에게 **"우리 회사 알고 지원했다"** 인상.

---

## 2. 두 프로젝트 페어링 전략

### 2-1. 프로젝트 A — Gov_Lex (데이터 파이프라인)

**상태**: Phase 0 완료, 7.0/10
**목표**: 9.0+/10
**소요**: 5주 (Phase 1~3)

**핵심 가치**:
- 한·미 법률·법안을 같은 스키마로 정리
- ETL · QA · 운영 인프라 역량 증명
- "데이터를 관리할 줄 아는 사람"

### 2-2. 프로젝트 B — LLM 챗봇 (Chat CODIT 미니 클론)

**상태**: 미시작 (Phase 4)
**시작 시점**: Gov_Lex 8.5점 도달 후 (= Phase 3 완료 후)
**소요**: 2~3주

**핵심 가치**:
- Gov_Lex 데이터 위에서 RAG 챗봇
- BM25 + 벡터 하이브리드 검색
- 출처 인용 강제 (환각 방지)
- eval 셋 100개 + 정량 측정
- "데이터로 가치를 만들 줄 아는 사람"

### 2-3. 두 프로젝트 연결 방식 — 같은 데이터·같은 DB

```
[Gov_Lex 데이터 파이프라인]
        ├─ KR 법령 (40만+ 건)
        ├─ US 법안 (10만+ 건)
        └─ 국회 의안 (5만+ 건)
              │
              │ 같은 LegalDocument 9필드 스키마
              ▼
[공유 데이터 레이어]  data_index/normalized/docs.jsonl
              │
              │ Phase 2-6 Adapter (SQLite/pgvector)
              ▼
[챗봇 RAG 백엔드]
        ├─ pgvector / FAISS 벡터 검색
        ├─ BM25 키워드 검색
        └─ 하이브리드 가중 합산
              │
              ▼
[Streamlit 챗봇 UI]
        "GDPR과 한국 개인정보보호법 차이는?"
        └─ 답변 + [§15(2) 인용] + 원문 링크
```

**연결의 강력함**:
- 두 프로젝트가 **같은 DB·같은 스키마** 공유 → 통합 데모 가능
- 면접에서 **하나의 demo로 두 포트폴리오 다 보여줌**
- "데이터 → 검색 → LLM 답변" 풀스택 흐름

### 2-4. 면접 한 줄 어필

> **"직접 ETL해서 정리한 한미 법률 데이터 50만 건 위에 RAG 챗봇을 띄웠고, 검색은 BM25+벡터 하이브리드, 답변엔 출처 인용까지 강제. eval 셋 100개에서 정답률 87% / 인용 정확도 93%."**

---

## 3. 이 문서 사용법

1. **위에서부터 차례대로** 진행합니다. 단계를 건너뛰면 다음 단계에서 막힙니다.
2. 각 단계는 다음 4 블록으로 구성됩니다.
   - 🎯 **무엇을** : 이 단계에서 할 작업
   - 💡 **왜** : 이게 왜 점수에 중요한가
   - 🔧 **어떻게** : 구체적인 코드/명령
   - ✅ **확인** : "다 됐다"고 판단하는 기준
3. 막히면 Cursor Agent에게 **"@masterplan.md 의 N-N 단계 진행해줘"** 라고 말하면 됩니다.
4. 한 단계 끝낼 때마다 아래 **§11 진행 체크리스트** 의 박스를 `[ ]` → `[x]` 로 바꾸세요. 진척도가 눈에 보입니다.
5. **Phase 단위 완료 시 자동 동기화 규칙**: 이 파일(`masterplan.md`)의 체크리스트·점수추적·다음단계를 갱신한 직후, 작업 회고 파일 `내가한거.md`에도 같은 완료 사실(날짜/핵심변경/검증결과/다음단계)을 즉시 반영합니다.
5. **절대 한 번에 다 하려고 하지 마세요.** 하루에 한두 단계만 해도 충분합니다.

---

## 4. 전체 일정 한눈에

```
[Phase 0]  결함 복구            1주    5.8 → 7.0   ✅ 완료
[Phase 1]  운영 인프라          1주    7.0 → 7.5
[Phase 2]  운영 패턴 이식       2주    7.5 → 8.5  (Helixops 선별 이식)
[Phase 3]  차별화 마무리        1주    8.5 → 9.0+
─────────────────────────────────────────────────  Gov_Lex 완성
[Phase 4]  LLM 챗봇             2~3주  → 9.5+
[폴리싱]   README·면접 준비     1주    9.5+
                                ────
                                총 7~8주
```

**하루 2~3시간 작업 기준 7~8주.** 시간이 더 있으면 빠르고, 적으면 늦어집니다. 그래도 **순서는 절대 바꾸지 마세요.**

---

## 5. 지금 상태 vs 목표

| 영역 | 시작 (5.8) | 현재 (7.0) | 목표 (9.0+) |
|---|---|---|---|
| 데이터 무결성 | R01 버그·content_hash 정의 불일치 | ✅ 둘 다 해결 | 버그 0, 정의 일치 |
| 테스트 | 19개 (수집기 0) | **87개** (+ 설정 외부화 테스트) | 70%+ 커버리지, 수집기 mock 테스트 |
| 운영 흔적 | print 문, run 폴더만 | ✅ logging + run별 pipeline.log | logging + metrics.json + dashboard.md |
| 데이터 안전성 | open(append) 직접 쓰기 | ✅ atomic write | atomic write + Adapter |
| HTTP 안정성 | 수집기별 제각각 | ✅ 통일 클라이언트 | (변동 없음) |
| 재실행 가능성 | 안 됨 | 안 됨 | Replay 모드 (`--replay`, `--only-failures`) |
| 저장소 | JSONL append만 | JSONL atomic | Adapter 패턴 (JSONL → SQLite → pgvector) |
| 도메인 깊이 | law + bill 2종 | (변동 없음) | + decree/minutes 추가, KG 기반 관계 |
| 자동화 | 없음 | 없음 | GitHub Actions CI + 일일 cron + Slack 알림 |
| 의사결정 흔적 | 없음 | 없음 | ADR 7개 |
| Docker | 없음 | 없음 | Dockerfile + scripts/ 풀세트 |
| 챗봇 | 없음 | 없음 | RAG + 인용 + eval 셋 |

---

## 6. 용어 사전 (모르면 막힙니다)

| 용어 | 쉬운 설명 |
|---|---|
| **content_hash** | 문서 본문을 짧은 코드로 줄인 "지문". 같은 문서면 같은 지문. 중복 방지용. |
| **idempotent (멱등)** | 같은 작업을 100번 해도 결과가 똑같음. 파이프라인을 두 번 돌려도 데이터가 두 배가 안 됨. |
| **atomic write (원자적 쓰기)** | 파일을 쓸 때 "전부 쓰거나, 아예 안 쓰거나" 둘 중 하나. 중간에 죽어도 반쪽 파일이 안 생김. |
| **mock (목)** | 진짜 API를 안 부르고 가짜 응답을 만들어서 테스트하는 것. |
| **CI (Continuous Integration)** | GitHub에 코드를 올리면 자동으로 테스트/문법검사를 돌려주는 시스템. |
| **adapter pattern (어댑터 패턴)** | "어디에 저장할지"를 인터페이스로 분리. 나중에 JSONL → DB로 바꿔도 코드 수정 최소. |
| **replay (재연)** | 옛날 실행 결과를 다시 돌려서 같은 결과가 나오는지 확인. 재현성 증명. |
| **ADR (Architecture Decision Record)** | "왜 이렇게 만들었는지" 짧은 문서. 면접관이 "왜?" 물으면 여기 보여주면 됨. |
| **provenance (출처 기록)** | 이 데이터가 언제, 어디서, 어떤 API 버전으로 왔는지 메타정보. |
| **knowledge graph (KG)** | 법령↔법안↔의원↔위원회처럼 "관계로 연결된 데이터". |
| **ontology (온톨로지)** | "이 도메인엔 어떤 개념이 있고 어떻게 연결되나"를 정리한 사전. KG의 설계 도면. 예: `Bill -PROPOSED_BY-> Member`. |
| **failure catalog** | QA 실패를 누적해서 "어떤 패턴이 자주 깨지나" 보는 카탈로그. (Reflexion처럼 학습 시스템이 아님 — 단순 기록·집계.) |
| **RAG (Retrieval-Augmented Generation)** | 챗봇이 답하기 전에 먼저 DB에서 관련 문서를 찾아오고, 그 문서 기반으로 답변. 환각 방지. |
| **eval 셋 (evaluation set)** | "이 질문엔 이게 정답" 쌍을 100개 미리 만들어 두고, 챗봇 정답률을 측정. |
| **hallucination (환각)** | LLM이 그럴듯하지만 틀린 답변을 만들어내는 현상. RAG + 인용 강제로 방지. |
| **embedding (임베딩)** | 문장을 의미 비슷한 정도로 비교 가능한 숫자 벡터로 변환. 의미 검색 가능. |

---

# Phase 0 — 결함 복구 (1주차, 5.8 → 7.0) ✅ 완료

> 면접관이 코드 열었을 때 5초 안에 잡힐 결함을 0으로 만드는 단계.
> 화려한 기능 추가 전에 **신뢰성부터** 잡습니다.

---

## 0-1. R01 mark_seen 버그 수정 ⭐최우선

### 🎯 무엇을
`src/govlexops/qa/rules.py` 의 R01 룰에서 `mark_seen()`을 호출하는 위치를 옮깁니다.
지금은 **R02·R05 검증도 안 끝났는데** 영구 저장소에 이미 "본 적 있음"으로 기록 중입니다.

### 💡 왜
이 버그가 살아 있으면, R02에서 거부된 문서는 다음 실행 때도 영원히 못 들어옵니다. **데이터 영구 손실 버그.** 면접관이 5초 안에 잡습니다.

### 🔧 어떻게
1. `qa/rules.py` 의 `check_r01_duplicate()` 마지막에 있는 `mark_seen()` 호출을 **삭제**합니다.
2. 새 메서드 `commit_seen(self, doc)` 을 만들어 `self._seen_this_run` 에만 추가합니다.
3. `pipeline.py` 에서 `save_documents(passed_docs)` **성공 후에** `for doc in passed_docs: mark_seen(doc.content_hash, ...)` 를 일괄 호출합니다.

### ✅ 확인
- `tests/test_qa_rules.py` 에 새 테스트 추가:
  ```python
  def test_r02_failure_does_not_mark_seen():
      """R02에서 거부된 문서는 영구 저장소에 안 남아야 한다."""
  ```
  이 테스트가 PASS.
- `pytest tests/ -v` → 20개 모두 PASS.

---

## 0-2. content_hash 정의를 README와 일치시키기

### 🎯 무엇을
README §9에는 "본문 기반 SHA-256 해시"라고 써 있는데, 실제 코드는 `f"{title}_{raw_date}"` 즉 **메타데이터 해시**입니다.
둘 중 하나로 통일합니다.

### 💡 왜
README와 코드가 다르면 포트폴리오 신뢰도 즉시 0. CTO/면접관 입장에서 "거짓말한 사람"으로 분류됩니다.

### 🔧 어떻게
**옵션 A(추천, 솔직 노선):** README 표현을 정정합니다.
- `Readme.md` §9 의 `content_hash` 행을 다음처럼 변경:
  ```
  | content_hash | 제목·발행일·식별자를 정규화한 SHA-256 해시 (메타데이터 기반 ID 해시) |
  ```
- `docs/schema_v1.md` 에 정의를 박제하고, "본문 해시가 아닌 이유"를 한 줄 적습니다.

**옵션 B(어려운 노선, +0.3점):** 코드를 진짜 본문 기반으로 바꿉니다.
- KR 법령: 시행일·소관부처·조문 일부까지 포함
- US: bill text API로 본문 받아와서 해시
- 국회: 요약(`SUMMARY`)을 해시 입력에 포함

→ **처음엔 옵션 A로 가시고, Phase 2에서 옵션 B로 업그레이드** 하시면 됩니다.

### ✅ 확인
- `Readme.md` 와 `src/govlexops/schemas/legal_document.py` 의 `content_hash` 설명이 같은 의미.
- 새 파일 `docs/schema_v1.md` 가 존재하고, 거기에 정의·이유·예시 3가지가 적혀 있음.

---

## 0-3. 공통 HTTP 클라이언트 만들기

### 🎯 무엇을
세 개 수집기(`kr_law.py`, `us_congress.py`, `assembly_bills.py`)가 각자 다르게 `requests.get()` 을 부르고 있습니다.
하나의 공통 모듈로 통일합니다.

### 💡 왜
- `kr_law.py` 에는 timeout이 없음 → API가 느려지면 영원히 안 끝남
- 재시도 로직이 `assembly_bills.py` 에만 있음 → 다른 둘은 한 번 끊기면 끝
- 같은 사람이 짠 코드인데 일관성이 없으면 "추상화 사고가 약하다"는 평가

### 🔧 어떻게
1. 새 파일 `src/govlexops/core/http.py` 생성:
   ```python
   import requests, time, logging
   log = logging.getLogger("govlex.http")

   def get_json(url, params=None, *, timeout=30, max_retries=3, backoff=1.5):
       """공통 GET. 재시도 + 타임아웃 + 429 분기 + 구조화 로그."""
       last_err = None
       for attempt in range(1, max_retries + 1):
           try:
               r = requests.get(url, params=params, timeout=timeout,
                                headers={"User-Agent": "govlex-ops/0.1"})
               if r.status_code == 429:  # rate limit
                   wait = backoff ** attempt * 2
                   log.warning("rate_limited", extra={"wait": wait, "url": url})
                   time.sleep(wait)
                   continue
               r.raise_for_status()
               return r.json()
           except Exception as e:
               last_err = e
               log.warning("http_retry", extra={"attempt": attempt, "err": str(e)})
               time.sleep(backoff ** attempt)
       raise last_err
   ```
2. 세 수집기에서 `requests.get(...)` 직접 호출 → `from govlexops.core.http import get_json` 으로 교체.

### ✅ 확인
- `rg "requests.get\("  src/govlexops/etl/ingest/` 결과 0건.
- 한 수집기에서 인터넷 끄고 실행 → 3번 재시도 후 깔끔하게 실패.

---

## 0-4. 폴백 날짜 제거 → 격리(quarantine)로

### 🎯 무엇을
`kr_law.py` 와 `us_congress.py` 는 날짜 파싱 실패 시 `date(2000, 1, 1)` 을 박아 넣고 그대로 통과시킵니다.
이런 문서는 **저장하지 말고 quality_failures 로** 보냅니다.

### 💡 왜
2000-01-01 가짜 날짜가 박힌 문서가 docs.jsonl에 쌓이면 R05(날짜 충돌) 룰도 잘못 작동하고 검색 결과도 오염됩니다.

### 🔧 어떻게
1. 새 룰 `R07: invalid_date` 를 `qa/rules.py` 에 추가:
   ```python
   def check_r07_invalid_date(self, doc):
       y = doc.issued_date.year
       if y < 1948 or y > date.today().year + 1:
           # 격리
           return False
       return True
   ```
2. 수집기에서 폴백 `date(2000,1,1)` 을 그대로 두되, R07이 잡아내도록 함. (또는 수집기 자체에서 None 반환하고 pipeline에서 격리)

### ✅ 확인
- `docs.jsonl` 에 `issued_date: "2000-01-01"` 인 줄이 0개.
- `quality_report.md` 에 R07 통계가 보임.

---

## 0-5. print 전면 제거 → logging 도입 ✅ 완료 (2026-04-30)

### 🎯 무엇을
모든 `print(...)` 문을 `logging` 모듈로 교체합니다.

### 💡 왜
운영 환경에선 print 문은 추적이 안 됩니다. 로그 레벨(INFO/WARNING/ERROR)도 못 나누고, 파일로 저장도 안 됩니다.

### 🔧 어떻게
1. 새 파일 `src/govlexops/core/logging.py`:
   ```python
   import logging, sys
   from pathlib import Path

   def setup_logging(run_dir: Path | None = None, level=logging.INFO):
       fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
       handlers = [logging.StreamHandler(sys.stdout)]
       if run_dir:
           handlers.append(logging.FileHandler(run_dir / "pipeline.log", encoding="utf-8"))
       logging.basicConfig(level=level, format=fmt, handlers=handlers)
   ```
2. `pipeline.py` 맨 위에서 `setup_logging(run_dir)` 호출.
3. `print(...)` → `log.info(...)`, `print("❌ ...")` → `log.error(...)` 식으로 변환.

### ✅ 확인
- `rg "print\(" src/govlexops/` 결과 0건. (앱 `app.py`는 Streamlit이라 OK)
- `runs/<run_id>/pipeline.log` 파일이 생성됨.

### 📝 실제 작업 결과
- **신규 모듈**: `src/govlexops/core/logging.py` — `setup_logging(run_dir, level)`
  - 매 호출 시 기존 핸들러를 정리 후 재부착해 **run마다 깨끗한 pipeline.log** 생성.
  - `urllib3`, `requests` 등 noisy 외부 로거는 WARNING으로 다운그레이드.
- **변환 규모**: 4개 모듈에서 print 33건 → log 호출로 전부 교체.
  - `pipeline.py` 14건, `kr_law.py` 5건, `us_congress.py` 6건, `assembly_bills.py` 8건
  - `print("❌ ...")` → `log.error(...)`, `print("⚠️ ...")` → `log.warning(...)`, 그 외 → `log.info(...)`
  - 모듈별 logger 트리(`govlexops.etl.ingest.kr_law` 등)로 grep 가능.
- **신규 테스트**: `tests/test_logging.py` 5건 추가
  - `test_setup_logging_creates_pipeline_log` — 파일이 실제로 생성되고 메시지가 들어가는지
  - `test_setup_logging_idempotent` — 두 번 호출해도 핸들러 누적 안 됨
  - `test_setup_logging_switches_log_file_per_run` — run마다 새 파일에 기록 (이전 run에 안 섞임)
  - `test_setup_logging_without_run_dir_attaches_only_console` — 콘솔만 부착 검증
  - `test_setup_logging_downgrades_noisy_loggers` — urllib3/requests 다운그레이드 검증
- **검증**:
  - `rg "print\(" src/govlexops/` → 0건 (docstring 1건만 잔존)
  - `pytest tests/ -v` → **47 passed** (logging 5건 신규)

---

## 0-6. docs.jsonl 원자적 쓰기 (atomic write) ✅ 완료 (2026-04-30)

### 🎯 무엇을
저장 도중 파이프라인이 죽어도 `docs.jsonl` 이 반쪽이 안 되도록 **staging → rename** 패턴을 적용합니다.

### 💡 왜
지금은 `open(..., "a")` 로 바로 append합니다. 100건 중 50건째에서 죽으면 반쪽 데이터가 영구히 남습니다. 다음 실행 때 섞이면서 디버깅 불가.

### 🔧 어떻게
1. `core/storage.py` 의 `save_documents()` 를 다음처럼:
   ```python
   def save_documents(docs):
       DOCS_PATH.parent.mkdir(parents=True, exist_ok=True)
       staging = DOCS_PATH.with_suffix(".jsonl.staging")
       # 기존 docs.jsonl을 먼저 staging으로 복사
       if DOCS_PATH.exists():
           shutil.copy(DOCS_PATH, staging)
       with open(staging, "a", encoding="utf-8") as f:
           for d in docs:
               f.write(json.dumps(d.model_dump(mode="json"), ensure_ascii=False) + "\n")
       os.replace(staging, DOCS_PATH)  # atomic rename
       return len(docs)
   ```
2. `seen_store.py` 의 `mark_seen()` 도 같은 패턴 적용.

### ✅ 확인
- 일부러 `Ctrl+C` 로 파이프라인 중간에 죽임 → `docs.jsonl` 은 직전 정상 상태 유지.
- `docs.jsonl.staging` 파일이 실행 후에 안 남아 있음.

### 📝 실제 작업 결과
- **신규 헬퍼**: `src/govlexops/core/atomic.py` — `atomic_append_jsonl(target, lines)`
  - 매 호출 시 `target.suffix.staging.<pid>` 임시 파일 생성 → 기존 내용 복사 → 새 줄 append → `os.replace()`로 atomic rename.
  - 실패 경로: `os.replace` 직전까지 어디서 죽어도 target은 호출 전 상태 그대로. staging만 정리.
  - 줄 끝 개행 자동 보정, 빈 입력은 no-op (mtime도 안 건드림).
- **storage.py 마이그레이션**: `save_documents`가 한 번의 atomic write로 N건을 묶어 처리.
- **seen_store.py 확장**:
  - `mark_seen_many(records)` 신규 — 배치 atomic write로 N건 한 번에. 기존 호출 시 N번 staging+rename이 발생하던 비효율을 1번으로 압축.
  - 같은 배치 내 중복 해시 자동 dedup, 이미 본 해시 자동 스킵.
  - **메모리 캐시(_seen) 갱신은 atomic write 성공 후에만** 수행 → 실패 시 캐시 일관성 보존.
  - `mark_seen(...)` 단건 wrapper는 호환을 위해 남기고 내부적으로 `mark_seen_many` 호출.
- **rules.py 수정**: `commit_seen_for_passed`가 `mark_seen_many` 한 번 호출로 일괄 기록.
- **신규 테스트**: 3개 파일 22건 추가 (총 69 passed)
  - `tests/test_atomic.py` (9): 신규 생성/append/빈입력/개행보정/staging정리/실패시 target보존/유니코드/카운트
  - `tests/test_storage.py` (5): save_documents 정상/append/빈입력/실패보존/staging정리
  - `tests/test_seen_store.py` (8): mark_seen_many 정상/이미본해시스킵/배치내dedup/빈입력/필수키누락/단건호환/실패시 캐시·파일보존/모두중복인 경우
- **검증**:
  - `pytest tests/ -v` → **69 passed** (기존 47 + atomic 22)
  - `os.replace`를 강제 실패시키는 mock으로 atomicity 직접 검증 (test_target_unchanged_on_failure / test_save_documents_failure_preserves_existing / test_mark_seen_failure_preserves_file_and_cache)

---

# Phase 1 — 운영 인프라 (2주차, 7.0 → 7.5)

> "동작은 되는 스크립트"에서 "운영 가능한 데이터 파이프라인"으로 격을 올리는 단계.

---

## 1-1. 수집기 mock 테스트 추가

### 🎯 무엇을
`kr_law`, `us_congress`, `assembly_bills` 수집기에 가짜 API 응답으로 돌리는 테스트를 추가합니다.

### 💡 왜
지금 19개 테스트는 schema와 QA만 검증하고, **가장 위험한 수집 코드는 0개 테스트**입니다. 수집기가 실제로 깨졌는지 알 방법이 없음.

### 🔧 어떻게
1. `pip install responses pytest-cov` (의존성 추가)
2. `tests/ingest/` 폴더 신설.
3. `tests/ingest/test_kr_law.py` 예시:
   ```python
   import responses
   from govlexops.etl.ingest.kr_law import fetch_laws

   @responses.activate
   def test_fetch_laws_normal():
       responses.add(responses.GET, "http://www.law.go.kr/DRF/lawSearch.do",
                     json={"LawSearch": {"law": [{"법령ID": "1", "법령명한글": "AI기본법",
                                                   "공포일자": "20240315", "법령일련번호": "999"}]}})
       docs = fetch_laws(query="인공지능", max_count=10)
       assert len(docs) == 1
       assert docs[0].title == "AI기본법"
   ```
4. 같은 패턴으로 `test_us_congress.py`, `test_assembly_bills.py` 작성. 케이스: ① 정상 ② 빈 결과 ③ 429 ④ 잘못된 JSON.

### ✅ 확인
- `pytest tests/ -v` → **83개** PASS (기준 예시는 30개 이상).
- `pytest tests/ --cov=govlexops --cov-report=term --cov-fail-under=70` → **coverage 70% 이상** (현재 약 74%).

---

## 1-2. GitHub Actions CI 셋업

### 🎯 무엇을
GitHub에 코드를 push 할 때마다 자동으로 pytest + ruff + mypy 가 돌게 합니다.

### 💡 왜
README에 "Tests: 19 PASS" 라고만 쓰면 누구도 안 믿습니다. **녹색 배지가 박혀 있어야** 신뢰가 생깁니다. 이거 하나로 점수 +0.3.

### 🔧 어떻게
1. 새 폴더 `.github/workflows/` 생성.
2. `.github/workflows/ci.yml`:
   ```yaml
   name: CI
   on: [push, pull_request]
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
           with: { python-version: "3.11" }
         - run: pip install -e . pytest pytest-cov responses ruff mypy
         - run: ruff check src/
         - run: mypy src/govlexops --ignore-missing-imports
         - run: pytest tests/ --cov=govlexops --cov-fail-under=70
   ```
3. `Readme.md` 맨 위에 배지 추가:
   ```
   ![CI](https://github.com/<USER>/Gov_Lex/actions/workflows/ci.yml/badge.svg)
   ![Coverage](https://img.shields.io/badge/coverage-72%25-brightgreen)
   ```

### ✅ 확인
- GitHub 저장소의 Actions 탭에서 ✅ 초록 체크가 보임.
- README에 배지가 렌더링됨.

---

## 1-3. metrics.json + dashboard.md 자동 생성

### 🎯 무엇을
실행 때마다 `runs/<run_id>/metrics.json` 을 만들고, 누적 metrics를 모아 `docs/dashboard.md` 를 자동 갱신합니다.

### 💡 왜
README §17의 "통과율 0%" 같은 정적 표는 약합니다. **"지난 30일간 통과율 92.4%, 일평균 수집 4,821건"** 같은 동적 그래프가 박히면 점수 격이 다릅니다.

### 🔧 어떻게
1. `pipeline.py` 끝부분에 metrics 수집:
   ```python
   metrics = {
       "run_id": run_dir.name,
       "duration_seconds": (datetime.now() - start).total_seconds(),
       "ingested": len(all_docs),
       "passed": len(passed_docs),
       "rejected": {"R01": s["R01"], "R02": s["R02"], "R05": s["R05"]},
       "by_source": {"kr_law": len(kr_docs), "us": len(us_docs), "assembly": len(assembly_docs)},
       "pass_rate": round(len(passed_docs) / max(len(all_docs), 1), 4),
   }
   (run_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2))
   ```
2. 새 스크립트 `scripts/build_dashboard.py`: `runs/*/metrics.json` 전부 읽어서 `docs/dashboard.md` 작성 (지난 30일 표 + 통과율 추이).

### ✅ 확인
- 파이프라인 한 번 실행 후 `runs/<run_id>/metrics.json` 존재.
- `python scripts/build_dashboard.py` → `docs/dashboard.md` 생성.
- README에 "[운영 대시보드 보기](docs/dashboard.md)" 링크 추가.

---

## 1-4. 설정 외부화 (configs/pipeline.yaml)

### 🎯 무엇을
지금 코드에 하드코딩된 정책값(쿼리 36개, TEST_LIMIT=5000, 연도 필터 등)을 YAML 설정 파일로 빼냅니다.

### 💡 왜
현재 운영 정책을 바꾸려면 코드를 수정해야 함. **운영 데이터 엔지니어는 코드 수정 없이 설정만 바꿀 줄 알아야** 합니다.

### 🔧 어떻게
1. `configs/pipeline.yaml`:
   ```yaml
   kr_law:
     queries: [인공지능, 데이터, 개인정보, 정보통신, 디지털, ...]
     max_per_query: 80
     issued_since_year_offset: -3
   us_congress:
     congress: 118
     max_count: 250
     min_intro_year_offset: -3
   kr_assembly:
     assemblies: [제21대, 제22대]
     test_limit: 5000
     page_size: 100
   ```
2. `pip install pydantic-settings`
3. `src/govlexops/core/config.py` 에 pydantic 모델로 로드.
4. 수집기들이 모듈 상수 대신 이 config를 사용하도록 수정.

### ✅ 확인
- `configs/dev.yaml`, `configs/prod.yaml` 두 개로 분기 가능.
- 코드 수정 없이 `--config configs/dev.yaml` 만 바꿔서 다른 정책으로 실행됨.

---

## 1-5. ruff + pre-commit 도입

### 🎯 무엇을
코드 스타일을 자동으로 통일하는 ruff와, 커밋 직전에 검사하는 pre-commit을 도입합니다.

### 💡 왜
코드 스타일이 들쭉날쭉하면 "협업 경험 없다"는 신호입니다. **ruff 한 번이면 90% 해결**됩니다.

### 🔧 어떻게
```bash
pip install ruff pre-commit
ruff check src/ --fix
ruff format src/
```

`.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.0
    hooks:
      - id: ruff
      - id: ruff-format
```
실행:
```bash
pre-commit install
```

### ✅ 확인
- `git commit` 할 때 ruff가 자동으로 돌아감.
- CI(1-2)에서 `ruff check` 가 PASS.

---

# Phase 2 — 운영 패턴 이식 (3~4주차, 7.5 → 8.5)

> 이전 공모전 자산(HelixOps)에서 검증된 패턴 중 **GovLex 도메인에 맞는 것만** 선별 이식하는 단계.
> **이 Phase가 9점대 진입의 핵심**입니다.

### ⚠️ 도메인 차이 — 패턴을 무조건 옮기지 않는다

Helixops는 **AI 기반 단백질 설계 멀티 에이전트 시스템**입니다.
GovLex는 **법률 데이터 ETL 파이프라인**입니다.
시스템 형태가 다르므로 **에이전트 패턴은 의도적으로 빼고**, ETL/운영 인프라 패턴만 가져옵니다.

| 가져오는 것 (도메인 무관 인프라) | 빼는 것 (에이전트용 과잉) |
|---|---|
| ✅ scripts/Docker (2-1) | ❌ State + StateDelta (LangGraph 머지 패턴) |
| ✅ Replay 모드 (2-2) | ❌ Reflexion 기반 실패 학습 |
| ✅ ETL 5단계 디렉터리 (2-3) | |
| ✅ Failure **Catalog** (Knowledge 아님, 단순 카탈로그로 축소, 2-5) | |
| ✅ Adapter 패턴 (2-6) | |
| ✅ **법률 도메인 온톨로지** (Helixops `ontology/` 패턴 차용, 2-4 신규) | |

**면접 어필**:
> "Helixops에서 ETL/인프라 패턴은 가져오고 에이전트 패턴은 의도적으로 뺐습니다.
> GovLex는 ETL이지 에이전트 시스템이 아니거든요. 대신 Researcher 에이전트의
> RAG 패턴은 Phase 4 챗봇에 그대로 적용합니다."

→ **"패턴 외워 박는 사람"이 아니라 "패턴이 도메인에 맞는지 판단하는 사람"** 으로 보임.

---

## 2-1. scripts/ + Docker 풀세트

### 🎯 무엇을
HelixOps의 `scripts/` 와 `docker/` 폴더를 GovLex 컨텍스트로 옮깁니다.

### 💡 왜
면접관이 README 보고 `git clone` → `docker compose up` 한 번으로 재현되면 점수 +0.5.
"누구나 5초 만에 재현"이 운영 데이터 엔지니어의 자격증입니다.

### 🔧 어떻게
1. `docker/Dockerfile`:
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY pyproject.toml requirements.txt ./
   RUN pip install --no-cache-dir -e . -r requirements.txt
   COPY src ./src
   COPY configs ./configs
   COPY scripts ./scripts
   ENV PYTHONPATH=/app/src
   ENV RUNS_DIR=/data/runs
   ENTRYPOINT ["python", "-m", "govlexops.etl.pipeline"]
   ```
2. `docker/docker-compose.yml`: pipeline 컨테이너 + (옵션) pgvector + (옵션) neo4j.
3. `scripts/run_pipeline.sh`, `scripts/replay_run.sh`, `scripts/smoke_test.sh`, `scripts/build_docker.sh`.

### ✅ 확인
```bash
docker build -t govlex -f docker/Dockerfile .
docker run --rm -v $(pwd)/runs:/data/runs --env-file .env govlex
```
이 한 줄로 새 머신에서도 파이프라인이 돌아감.

---

## 2-2. Replay 모드 ⭐핵심

### 🎯 무엇을
`python -m govlexops.etl.pipeline replay --run-path runs/<run_id>` 명령으로 옛날 실행을 다시 검증할 수 있게 합니다.

### 💡 왜
**재현성**은 9점대 진입의 통과의례입니다. HelixOps에 이미 패턴이 있으니 그대로 가져옵니다.
이거 하나로 **"실패한 67건만 다시 검증"** 같은 운영 시나리오가 가능해짐. 점수 +0.6.

### 🔧 어떻게
1. CLI를 Typer로 재구성:
   ```bash
   pip install typer
   ```
   `src/govlexops/services/cli.py`:
   ```python
   import typer
   app = typer.Typer()

   @app.command()
   def run(config: str = "configs/pipeline.yaml"):
       from govlexops.etl.pipeline import run as pipeline_run
       pipeline_run(config_path=config)

   @app.command()
   def replay(run_path: str, only_failures: bool = False, regenerate_report: bool = False):
       from govlexops.core.replay import replay_run
       replay_run(run_path, only_failures=only_failures,
                  regenerate_report=regenerate_report)
   ```
2. `src/govlexops/core/replay.py` 신설:
   - `runs/<run_id>/quality_failures.jsonl` 을 읽어 `source_id` 목록 추출
   - 각 source에서 그 문서만 재수집 (수집기에 `--by-source-id` 옵션 추가)
   - 다시 QA → 새 quality_report 생성

### ✅ 확인
```bash
# 옛날 run 재검증
python -m govlexops.services.cli replay --run-path runs/run_20260430_191000_a1b2c3
# 실패한 것만
python -m govlexops.services.cli replay --run-path ... --only-failures
```
`runs/<run_id>/replay_report.md` 가 생성됨.

---

## 2-3. ETL 5단계 디렉터리 분리

### 🎯 무엇을
HelixOps의 `data_index/` 5단계 구조를 GovLex에 적용합니다.

### 💡 왜
지금은 `raw/` 가 비어 있고 `normalized/` 만 씁니다. **"raw 응답 보관"** 자체가 운영 데이터 엔지니어의 기본기.

### 🔧 어떻게
새 디렉터리 구조:
```
data_index/
├── raw/                    # ⭐ 신규: 원본 API 응답을 gzip으로 보관
│   ├── kr_law/<date>/<query>.json.gz
│   ├── us_congress/<date>/<congress>.json.gz
│   └── kr_assembly/<date>/<eraco>_<year>.json.gz
├── normalized/             # 현재 docs.jsonl
├── extracted/              # ⭐ 신규: 엔티티/관계 추출
│   ├── entities.jsonl      # 의원, 위원회, 정책영역
│   └── relations.jsonl     # bill -PROPOSED_BY-> member 등
├── chunks/                 # ⭐ Phase 3에서 추가
├── embeddings/             # ⭐ Phase 3에서 추가
└── quality/
    ├── failures.jsonl
    └── failure_notes.jsonl  # ⭐ 2-5에서 추가
```

각 수집기에서 `_save_raw_response(data, source, query)` 호출 추가.

### ✅ 확인
- 한 번 파이프라인 실행 → `data_index/raw/<source>/<date>/...` 에 압축 파일이 쌓임.
- 같은 날 두 번 실행해도 파일이 덮어쓰여지거나 이름이 분기됨.

---

## 2-4. 법률 도메인 온톨로지 정리 (Helixops `ontology/` 패턴 차용)

> ⚠️ **이 항목은 원래 "State + StateDelta"였습니다.**
> Helixops의 멀티 에이전트 머지 패턴인데, GovLex는 단순 ETL이라 **과잉 추상화** 함정.
> "왜 ETL에 LangGraph 쓰지?" 의문을 부르므로 **삭제**하고, 같은 Helixops에서
> 더 잘 맞는 `ontology/` 패턴을 가져와 **법률 도메인 온톨로지 정리**로 교체했습니다.
> (변경 이유는 이 문서 §2 Phase 2 서두 표 참조)

### 🎯 무엇을
법률·법안 데이터에서 등장하는 개념들의 위계와 관계를 `docs/ontology/`로 정리합니다.

### 💡 왜
- **CODIT 우대 조건** "법률·정책·컴플라이언스 도메인 지식" 직접 어필
- Phase 3-3 (entities/relations 추출)의 **개념 정의 근거**가 되는 선행 작업
- 면접관에게 "법률 도메인을 진짜 안다"는 가장 강력한 증거
- Helixops `src/helixops/ontology/`의 단백질 개념 트리 → 법률 개념 트리로 변환

### 🔧 어떻게
1. `docs/ontology/` 폴더 신설.
2. `docs/ontology/concepts.md` — 핵심 개념 트리:
   ```
   LegalDocument
   ├── Statute (법률)
   │   ├── Act (법)
   │   └── Decree (시행령·시행규칙)
   ├── Bill (법안)
   │   ├── Government Bill (정부 발의)
   │   └── Member Bill (의원 발의)
   ├── Regulation (행정규칙·고시)
   └── Minutes (의사록)

   Actor
   ├── Member (국회의원)
   ├── Committee (위원회)
   ├── Ministry (소관부처)
   └── Sponsor (US: representative/senator)

   PolicyArea
   ├── AI / 데이터
   ├── 핀테크 / 컴플라이언스
   └── 개인정보 / 프라이버시
   ```
3. `docs/ontology/relations.md` — 관계 정의:
   ```
   Bill -PROPOSED_BY-> Member
   Bill -REVIEWED_BY-> Committee
   Bill -BECAME-> Statute
   Statute -ENFORCED_BY-> Decree
   Statute -RELATED_TO-> PolicyArea
   ```
4. `docs/ontology/kr_us_mapping.md` — 한·미 개념 대응표:
   ```
   | 한국 | 미국 | 비고 |
   |---|---|---|
   | 법률 (Act) | Public Law | 통과 후 |
   | 법안 (Bill) | Bill | 발의 단계 |
   | 시행령 | Regulation (CFR) | 행정부 입법 |
   | 의사록 | Hearing transcript | 위원회 기록 |
   ```

### ✅ 확인
- `docs/ontology/` 에 3개 마크다운 파일.
- Phase 3-3 (entities/relations 추출)이 이 정의를 그대로 참조하도록 코드 작성 가능.
- README §6 "도메인 깊이" 섹션에서 이 폴더로 링크.

---

## 2-5. Failure Catalog — QA 실패 패턴 카탈로그

> ⚠️ **이 항목의 원본은 "Failure Knowledge — 실패를 RAG로 자산화"였습니다.**
> Reflexion 에이전트가 실패에서 학습하는 컨셉인데, GovLex엔 에이전트가 없으므로
> **단순 "데이터 품질 카탈로그"로 축소**했습니다.
> (Reflexion 컨셉 자체는 Phase 4 챗봇 eval 셋 개선 루프에서 활용 가능)

### 🎯 무엇을
QA에서 실패한 건을 누적해서 **"어떤 쿼리·위원회·출처가 자주 실패하는지" 카탈로그**를 만듭니다.

### 💡 왜
- "이 쿼리는 70% 결측", "이 위원회는 RGS_CONF_RSLT 자주 비어있음" 같은 **정량 패턴**을 발견.
- 다음 run 시작 시 "이 쿼리는 위험 ⚠️" **사전 경고** 가능.
- CODIT JD "데이터 정확도/일관성 관리" 직접 어필.
- 단순 jsonl 로그 < 카탈로그 = **사후 분석 가능 > 학습 시스템(과잉)**.

### 🔧 어떻게
1. `src/govlexops/qa/failure_catalog.py` 신설:
   ```python
   def append_to_catalog(failure: dict) -> None:
       """실패를 누적 카탈로그에 한 줄로 기록.
       Helixops Reflexion과 달리 학습은 안 함 — 단순 패턴 추적.
       """
       record = {
           "failure_id": failure["failure_id"],
           "rule_id": failure["rule_id"],          # R01/R02/R05/R07
           "source_id": failure["source_id"],
           "source_type": failure.get("source_type"),
           "jurisdiction": failure["jurisdiction"],
           "observed_at": datetime.now().isoformat(),
           "context_brief": failure.get("observed", "")[:200],
       }
       atomic_append_jsonl(
           Path("data_index/quality/failure_catalog.jsonl"),
           [json.dumps(record, ensure_ascii=False)],
       )
   ```
2. `qa/report.py`의 매 failure마다 `append_to_catalog()` 호출.
3. 새 스크립트 `scripts/analyze_failures.py`:
   - `failure_catalog.jsonl` 읽고 패턴 집계
   - "rule_id별 빈도", "source_type별 실패율", "쿼리별 결측 비율" 출력
   - `docs/failure_patterns.md`로 저장
4. `pipeline.py` 시작 시 `failure_patterns.md`를 읽어 위험 쿼리 목록 출력 (사전 경고).

### ✅ 확인
- `data_index/quality/failure_catalog.jsonl` 누적.
- `python scripts/analyze_failures.py` → `docs/failure_patterns.md` 생성.
- 파이프라인 시작 시 `[CATALOG] 위험 쿼리: ['핀테크 컴플라이언스 (실패율 65%)']` 같은 경고 표시.

---

## 2-6. Adapter 패턴 (integrations/store/)

### 🎯 무엇을
지금 `core/storage.py` 는 JSONL 한 가지뿐입니다. 인터페이스로 추상화하고 SQLite 어댑터를 추가합니다.

### 💡 왜
"JSONL이 1만 건 넘으면 어떡할 거야?" 라는 면접 질문에 **코드로 답할 수 있게** 됩니다. +0.4.
또한 **챗봇(Phase 4)이 pgvector를 통해 검색**하려면 이 Adapter가 먼저 깔려야 합니다.

### 🔧 어떻게
1. `src/govlexops/integrations/store/base.py`:
   ```python
   from typing import Protocol
   class DocumentStore(Protocol):
       def append(self, docs) -> int: ...
       def query(self, **filters) -> list: ...
       def count(self) -> dict: ...
   ```
2. `jsonl_store.py` (현재 코드 이전), `sqlite_store.py` (신규).
3. `configs/pipeline.yaml` 에 `store_backend: jsonl | sqlite | pgvector`.

### ✅ 확인
- 같은 파이프라인 코드로 `store_backend: sqlite` 로 바꿔서 실행 → 정상 동작.
- 1만 건 들어 있는 SQLite에서 `WHERE jurisdiction='KR'` 쿼리 100ms 이내.

---

# Phase 3 — 차별화 마무리 (5주차, 8.5 → 9.0+)

> 9점대를 가르는 것은 "**의사결정의 흔적**" 과 "**도메인 깊이**" 입니다.

---

## 3-1. ADR 7개 작성 ⭐

### 🎯 무엇을
`docs/adr/` 폴더에 의사결정 기록 7개를 작성합니다.

### 💡 왜
**이게 9점대 진입의 결정타.** "왜 그렇게 했어요?" 라는 면접 질문 100%에 자동 응답.
HelixOps에도 ADR-0001~0004가 있었으니 패턴은 이미 알고 계심.

### 🔧 어떻게
각 ADR은 다음 4 섹션으로 구성:
- **Context** : 어떤 상황이었나
- **Decision** : 무엇을 결정했나
- **Consequences** : 결과 (좋은 점 + 나쁜 점)
- **Alternatives Considered** : 안 고른 옵션과 그 이유

작성할 ADR 목록:
| 번호 | 주제 |
|---|---|
| ADR-001 | 왜 RDB 대신 JSONL로 시작했는가 |
| ADR-002 | content_hash를 본문이 아닌 ID 해시로 정의한 이유 |
| ADR-003 | metadata를 자유 dict로 두고 점진 승격하는 정책 |
| ADR-004 | QA를 ETL 외부 단계로 분리한 이유 (Great Expectations 안 쓴 이유) |
| ADR-005 | run_id 격리와 normalized 누적의 분리 |
| ADR-006 | 수집 상한을 코드 주석이 아닌 config로 둔 이유 |
| ADR-007 | BM25 → 벡터 검색 마이그레이션 시점과 트리거 |

### ✅ 확인
- `docs/adr/` 에 7개 마크다운 파일.
- README에 "[Architecture Decisions](docs/adr/)" 링크 추가.

---

## 3-2. 도메인 깊이 — decree 또는 minutes 1개 추가

### 🎯 무엇을
README §6에는 "5단계 매핑"이라 광고했지만 실제론 1·4단계만 수집 중입니다.
**최소 한 단계 더** 실제 수집되도록 합니다.

### 💡 왜
README 광고와 코드가 일치해야 9점대. **"법률 도메인을 진짜 안다"** 는 가장 강력한 증거입니다.
**다양성이 점수, 사이즈는 보너스** — 같은 종류 100만 건보다 4종류 1만 건씩이 훨씬 인상적.

### 🔧 어떻게
**옵션 A (쉬움, 추천):** 국가법령정보 API의 `target=admrul` 또는 `target=ordin` 추가 → `source_type=decree`
- 새 파일 `src/govlexops/etl/ingest/kr_decree.py`
- `kr_law.py` 와 거의 같은 패턴

**옵션 B (보너스):** 국회 회의록 API 추가 → `source_type=minutes`
- National_Assembly 프로젝트의 PDF 파싱 자산 재활용 가능

### ✅ 확인
- `docs.jsonl` 에 `source_type: "decree"` 또는 `"minutes"` 인 줄이 100건 이상.
- README §17 Before/After 표 업데이트: "수집 source_type: 2종 → 3종".

---

## 3-3. Knowledge Graph 기초 — entities/relations 추출

### 🎯 무엇을
법안에서 의원·위원회·정책영역을 추출해서 `entities.jsonl` + `relations.jsonl` 로 저장합니다.

### 💡 왜
법령·법안 데이터의 진짜 가치는 **관계**에 있습니다. "이 법안을 발의한 의원이 같은 위원회에서 다음에 어떤 법안을 냈나" 같은 분석이 가능해짐.
HelixOps의 ontology event 패턴을 그대로 적용. +0.4.
**또한 Phase 4 챗봇이 "법령 A를 인용한 법안 B" 같은 KG 답변을 할 수 있게 함.**

### 🔧 어떻게
1. `src/govlexops/etl/extract.py` 신설:
   ```python
   def extract_entities_from_assembly_bill(doc):
       md = doc.metadata
       entities = []
       if md.get("ppsr_nm"):
           entities.append({"type": "Member", "name": md["ppsr_nm"]})
       if md.get("jrcmit_nm"):
           entities.append({"type": "Committee", "name": md["jrcmit_nm"]})
       relations = [
           {"from": doc.source_id, "to": md.get("ppsr_nm"), "type": "PROPOSED_BY"},
           {"from": doc.source_id, "to": md.get("jrcmit_nm"), "type": "REVIEWED_BY"},
       ]
       return entities, relations
   ```
2. 파이프라인 끝에서 `data_index/extracted/entities.jsonl`, `relations.jsonl` 생성.

### ✅ 확인
- `entities.jsonl` 에 의원/위원회 이름 unique 100개 이상.
- `relations.jsonl` 에 PROPOSED_BY 관계 1000건 이상.

---

## 3-4. Hybrid Retrieval — pgvector 추가 (옵션, +0.4)

### 🎯 무엇을
지금 BM25 단일 검색을 BM25 + 벡터 검색 하이브리드로 확장합니다.

### 💡 왜
HelixOps README §1.6.1의 BRCA1 예시를 그대로 법률에 적용:
- BM25: "AI 책임성" 정확 매칭
- 벡터: "인공지능 윤리" 같은 의미 유사 조문
이거까지 해야 진짜 9.5점 영역.
**또한 Phase 4 챗봇의 RAG 검색 엔진이 정확히 이것**.

### 🔧 어떻게
1. `pip install sentence-transformers` (한국어는 `BM-K/KoSimCSE-roberta-multitask`)
2. `data_index/embeddings/chunk_vec.parquet` 생성
3. `src/govlexops/integrations/retriever/hybrid.py` 에서 BM25 점수 + 벡터 점수 가중 합산.

### ✅ 확인
- `app.py` 검색 UI에서 동의어 검색이 됨 (예: "AI" 검색 → "인공지능" 문서도 나옴).

---

## 3-5. CODIT 매핑 표 업그레이드 + scoring_mapping.md ⭐

### 🎯 무엇을
README §18 표를 "증거 링크" 형태로 업그레이드하고, 별도 `docs/scoring_mapping.md` 를 만듭니다.

### 💡 왜
**CODIT 면접 결정타.** 면접관이 "이 코드 어디에 있어요?" 물으면 5초 안에 줄 번호로 답해야 9점대.

### 🔧 어떻게
README §18 표를 다음처럼:
```
| CODIT 요구사항 | 증명 | 코드 링크 |
|---|---|---|
| 표준 스키마 정제 | 9필드 + KRMetadata/USMetadata | src/.../legal_document.py#L13 |
| QA 정확도/일관성 | 7개 룰 + 통과율 92.4% | docs/dashboard.md |
| 자동화 | GitHub Actions cron | .github/workflows/daily.yml |
| 재현성 | Replay 모드 + ADR-005 | src/.../replay.py, docs/adr/ADR-005.md |
| 멀티링구얼 | KR(ko) + US(en) 동일 스키마 | src/.../legal_document.py |
| 정형/비정형 표준화 | BPMBILLSUMMARY 자유 텍스트 → metadata.summary | src/.../assembly_bills.py#L260 |
```

### ✅ 확인
- 모든 링크가 실제로 존재하는 파일/줄을 가리킴.
- `docs/scoring_mapping.md` 에 CODIT JD 모든 항목이 있음.

---

# Phase 4 — LLM 챗봇 프로젝트 (6~8주차, 8.5 → 9.5+)

> Gov_Lex가 8.5점 도달한 후에 시작. 절대 동시 진행 금지.
> **Chat CODIT 미니 클론** 컨셉으로 한미 법률 RAG 챗봇 구현.
> 이 Phase가 끝나면 두 포트폴리오 페어링이 완성되고, JD 매칭률이 ~93/100에서 ~98/100으로 올라갑니다.

---

## 4-1. 챗봇 프로젝트 부트스트랩

### 🎯 무엇을
GovLex-Chat 별도 폴더(또는 같은 repo의 `chatbot/` 서브폴더)를 만들고, RAG 백엔드 뼈대를 깝니다.

### 💡 왜
시작 전에 Gov_Lex 자산을 어떻게 재사용할지 결정해야 합니다.
**같은 repo 권장**: 두 프로젝트가 같은 데이터·같은 스키마 공유. 면접 데모도 한 번에.

### 🔧 어떻게
1. 폴더 구조:
   ```
   Gov_Lex/
   ├── src/govlexops/                # 기존 파이프라인
   ├── src/govlexchat/               # ⭐ 신규
   │   ├── retrieval/                # BM25 + 벡터 + 하이브리드
   │   ├── llm/                      # OpenAI/Anthropic/Local 어댑터
   │   ├── prompts/                  # 시스템 프롬프트 + few-shot
   │   ├── eval/                     # eval 셋 + 채점기
   │   └── api.py                    # FastAPI 또는 직접 호출
   ├── ui/
   │   └── chatbot.py                # ⭐ Streamlit 챗 UI
   └── tests/chatbot/
   ```
2. 의존성 추가: `openai` 또는 `anthropic`, `sentence-transformers`, `streamlit-chat`.
3. ADR-008 작성: "왜 같은 repo로 통합했는가"
4. **Helixops 자산 재활용**:
   - `c:\Helixops-agentic\helixops-agentic\src\helixops\agents\researcher\` 구조를
     `src/govlexchat/`에 모방. **PubMed RAG 답변 패턴 = GovLex 법률 RAG 답변 패턴**.
   - `helixops/etl/chunk/`의 청크 분할 정책 → 4-1 청크 사이즈·overlap 결정에 참고
   - `helixops/etl/embed/protocols/`의 임베딩 모델 protocol → 한국어 모델 결정에 참고
   - **단**, Reflexion/Designer/Simulator 에이전트는 가져오지 않음 (도메인 다름).

### ✅ 확인
- `python -m govlexchat.api --help` 가 동작.
- Phase 3-4 pgvector 인덱스를 `govlexchat.retrieval`에서 정상 로드.
- ADR-008에 "Helixops에서 가져온 것 vs 안 가져온 것" 명시.

---

## 4-2. RAG 백엔드 — 검색 + LLM + 인용 강제

### 🎯 무엇을
질문 → 검색 → LLM 답변 + 출처 인용 강제 파이프라인을 만듭니다.

### 💡 왜
**환각 방지 + 변호사가 신뢰할 수 있는 답변.** 출처 없는 답변은 거부하는 시스템.
이게 일반 챗봇과 LegalTech 챗봇을 가르는 핵심 차이.

### 🔧 어떻게
1. **하이브리드 검색** (`govlexchat/retrieval/hybrid.py`):
   ```python
   def retrieve(query: str, top_k: int = 10) -> list[Chunk]:
       bm25_hits = bm25.search(query, k=top_k)
       vec_hits = pgvector.similarity_search(query, k=top_k)
       # 가중 합산 (BM25 0.4 + 벡터 0.6)
       return rerank_and_merge(bm25_hits, vec_hits)
   ```
2. **인용 강제 프롬프트** (`govlexchat/prompts/system.txt`):
   ```
   너는 한미 법률 전문 어시스턴트다.
   답변 규칙:
   1. 반드시 검색된 문서에서 근거를 찾아서 답한다.
   2. 답변에 [§N] 형식으로 인용 태그를 넣는다.
   3. 검색 결과에 근거가 없으면 "관련 법령 없음"이라 답한다.
   4. 절대 추측·일반 상식으로 답하지 않는다.
   ```
3. **답변 후처리** (`govlexchat/llm/cite_validator.py`):
   - 답변에 `[§N]` 태그 없으면 거부 → 재시도
   - 인용된 청크가 실제 검색 결과에 있는지 검증

### ✅ 확인
- "GDPR과 한국 개인정보보호법 차이는?" 질문 → 답변에 인용 태그 + 원문 미리보기.
- "오늘 점심 뭐 먹지?" 같은 비법률 질문 → "관련 법령 없음" 거부.

---

## 4-3. eval 셋 + LLM-as-Judge 자동 측정

### 🎯 무엇을
법률 질문 100개 + 정답 + 근거 출처 쌍을 미리 만들고, GPT-4를 채점기로 써서 정답률·인용 정확도를 자동 측정합니다.

### 💡 왜
**"잘 동작해요"는 증명 못 함. "정답률 87%, 인용 정확도 93%"는 정량 증명.**
이거 하나로 챗봇 점수 1점 점프. 면접에서 결정타.

### 🔧 어떻게
1. eval 셋 작성 (`tests/chatbot/eval/legal_qa.jsonl`):
   ```json
   {"q": "AI 기본법은 언제 통과됐나?", "a_must_include": ["2024", "통과"], "must_cite": ["AI기본법"]}
   {"q": "GDPR과 한국 개인정보보호법 차이?", "a_must_include": ["EU", "한국"], "must_cite": ["GDPR", "개인정보보호법"]}
   ```
   100개 작성. (50개부터 시작해도 OK)
2. 채점기 (`govlexchat/eval/judge.py`):
   ```python
   def score_answer(question, gold, answer, cited_docs):
       # 1. 답변 정확도 (LLM-as-Judge)
       accuracy = llm_judge(question, gold, answer)
       # 2. 인용 정확도 (must_cite vs cited_docs 매칭)
       citation = compute_citation_match(gold["must_cite"], cited_docs)
       return {"accuracy": accuracy, "citation": citation}
   ```
3. CI에서 매주 실행 → `docs/chatbot_eval.md` 자동 갱신.

### ✅ 확인
- `python -m govlexchat.eval.run` → 전체 셋 점수 출력.
- 정답률 80%+ / 인용 정확도 90%+ 도달.

---

## 4-4. Streamlit 챗 UI + 면접용 데모

### 🎯 무엇을
면접관 앞에서 5분 데모할 수 있는 챗 UI를 만듭니다.

### 💡 왜
**백엔드만 있으면 임팩트 절반.** 면접관이 직접 입력해보는 순간이 가장 강력.
UI는 단순하게 — 기능에 집중. Streamlit이면 충분.

### 🔧 어떻게
1. `ui/chatbot.py`:
   ```python
   import streamlit as st
   from govlexchat.api import ask

   st.title("GovLex Chat — 한미 법률 어시스턴트")
   query = st.chat_input("법률에 대해 물어보세요")
   if query:
       result = ask(query)  # {"answer": ..., "citations": [...]}
       st.write(result["answer"])
       for cite in result["citations"]:
           with st.expander(f"📜 {cite['title']}"):
               st.markdown(cite["snippet"])
               st.link_button("원문 보기", cite["source_url"])
   ```
2. 데모 시나리오 5개 미리 준비 (`docs/chatbot_demo_scenarios.md`):
   - "AI 기본법 핵심 내용은?"
   - "한국 개인정보보호법과 GDPR 차이는?"
   - "최근 발의된 핀테크 관련 법안은?"
   - "이 의원이 발의한 법안 목록은?" (KG 활용)
   - "오늘 날씨 어때?" (거부 시연)

### ✅ 확인
- `streamlit run ui/chatbot.py` → 브라우저에서 정상 동작.
- 5개 시나리오 모두 답변 + 인용 정상.

---

## 4-5. (옵션) 챗봇 + Gov_Lex 통합 데모

### 🎯 무엇을
파이프라인 실행 → 챗봇 답변까지 한 화면에서 보여주는 통합 대시보드.

### 💡 왜
**"데이터 → 검색 → LLM 답변" 풀스택을 한 번에 시연.** 면접 마지막 5분에 결정타.

### 🔧 어떻게
- `ui/dashboard.py`: 좌측 = Gov_Lex run 통계, 우측 = 챗봇 인터페이스.
- 새 데이터 들어오면 챗봇이 즉시 답변에 반영되는 모습 시연.

### ✅ 확인
- 면접관 앞에서 한 화면 5분 데모로 두 포트폴리오 다 전달 가능.

---

# 11. 진행 체크리스트

> 한 단계 끝낼 때마다 `[ ]` → `[x]` 로 바꾸세요.

## Phase 0 — 결함 복구 (목표 7.0) ✅ 완료
- [x] 0-1. R01 mark_seen 버그 수정 ✅ 2026-04-30
- [x] 0-2. content_hash 정의 일치 ✅ 2026-04-30
- [x] 0-3. 공통 HTTP 클라이언트 (`core/http.py`) ✅ 2026-04-30
- [x] 0-4. 폴백 날짜 제거 → R07 격리 ✅ 2026-04-30
- [x] 0-5. print 제거 → logging ✅ 2026-04-30
- [x] 0-6. docs.jsonl 원자적 쓰기 ✅ 2026-04-30

## Phase 1 — 운영 인프라 (목표 7.5)
- [x] 1-1. 수집기 mock 테스트 + coverage 70% ✅ 2026-05-01
- [x] 1-2. GitHub Actions CI ✅ 2026-05-01
- [x] 1-3. metrics.json + dashboard.md ✅ 2026-05-01
- [x] 1-4. configs/pipeline.yaml 외부화 ✅ 2026-05-01
- [x] 1-5. ruff + pre-commit ✅ 2026-05-01

## Phase 2 — 운영 패턴 이식 (목표 8.5)
- [x] 2-1. scripts/ + Docker ✅ 2026-05-01
- [x] 2-2. Replay 모드 (`replay --run-path`) ✅ 2026-05-01
- [x] 2-3. ETL 5단계 디렉터리 ✅ 2026-05-01
- [x] 2-4. **법률 도메인 온톨로지 정리** (← State+Delta 대체, Helixops `ontology/` 차용) ✅ 2026-05-01 (draft)
- [x] 2-5. **Failure Catalog** (← Failure Knowledge 축소, Reflexion 빼고 카탈로그만) ✅ 2026-05-01
- [x] 2-6. Adapter 패턴 (integrations/store/) ✅ 2026-05-01

## Phase 3 — 차별화 (목표 9.0+)
- [x] 3-1. ADR 7개 작성 ✅ 2026-05-01
- [ ] 3-2. decree 또는 minutes 1종 추가
- [x] 3-3. entities/relations 추출 ✅ 2026-05-01
- [x] 3-4. (옵션) 하이브리드 검색(BM25+벡터) ✅ 2026-05-01
- [x] 3-5. CODIT 매핑표 + scoring_mapping.md ✅ 2026-05-01

## Phase 4 — LLM 챗봇 (목표 9.5+)
- [ ] 4-1. 챗봇 프로젝트 부트스트랩
- [ ] 4-2. RAG 백엔드 + 인용 강제
- [ ] 4-3. eval 셋 + LLM-as-Judge
- [ ] 4-4. Streamlit 챗 UI
- [ ] 4-5. (옵션) 통합 데모

---

# 12. 자주 막히는 점 FAQ

**Q1. ImportError가 자꾸 나요.**
→ 저장소 루트에서 `$env:PYTHONPATH = "src"` (PowerShell) 한 줄을 매번 실행했는지 확인. 영구 설정은 `pyproject.toml` 의 `[tool.pytest.ini_options]` 에 `pythonpath = ["src"]` 추가.

**Q2. mock 테스트가 실제 인터넷을 타고 나가요.**
→ `responses` 라이브러리는 `@responses.activate` 데코레이터를 안 붙이면 무시됩니다. 매 테스트 함수마다 데코레이터 확인.

**Q3. Docker 빌드가 너무 느려요.**
→ `.dockerignore` 파일에 `runs/`, `data_index/`, `.venv/`, `__pycache__/` 추가. 첫 빌드는 5분 걸려도 두 번째부터 캐시로 30초.

**Q4. CI가 자꾸 빨갛게 떠요.**
→ 로컬에서 `pytest --cov=govlexops --cov-fail-under=70` 을 먼저 통과시키세요. coverage가 70% 안 나오면 fail되도록 위에서 설정했습니다.

**Q5. ADR 어떻게 쓰는지 모르겠어요.**
→ `c:\Helixops-agentic\helixops-agentic\docs\architecture\adr\` 의 ADR-0001 파일 그대로 복사해서 내용만 GovLex 컨텍스트로 바꾸세요.

**Q6. Replay가 너무 어려워 보여요.**
→ Phase 2-2는 어려우면 Phase 3 끝나고 마지막에 해도 됩니다. 단, 하나라도 빠지면 9점대 진입 어렵습니다.

**Q7. 일주일 안에 다 못 하겠어요.**
→ Phase 0(1주) + Phase 1(1주) + Phase 2(2주) + Phase 3(1주) + Phase 4(2주) + 폴리싱(1주) = **8주가 최소**. 시간을 늘리되 순서는 절대 바꾸지 마세요.

**Q8. 챗봇을 먼저 만들고 싶어요.**
→ 절대 안 됩니다. Gov_Lex 8.5점 안 되면 챗봇 데이터 품질이 깨져서 RAG 답변이 엉망이 됩니다. **순서 = 점수**.

**Q9. 데이터를 더 많이 모으고 싶어요. (예: 한국 시행령 추가)**
→ Phase 3-2 (decree/minutes 1종 추가)에 정확히 그 작업이 있습니다. 그 전에는 오히려 인프라가 못 버틉니다. **다양성이 점수, 사이즈는 보너스.**

---

# 13. 단계별 점수 추적

진행하면서 여기에 날짜와 함께 기록하세요. 면접 때 "5월 1일 5.8 → 6월 5일 9.5" 같은 흐름이 그 자체로 어필 포인트입니다.

| 날짜 | 완료 단계 | 추정 점수 | 메모 |
|---|---|---|---|
| 2026-04-30 | 베이스라인 | 5.8 | CTO 1차 평가 |
| 2026-04-30 | 0-1. R01 mark_seen 버그 수정 | 6.0 | 영구저장 시점을 save 성공 후로 분리. 회귀 방지 테스트 3개 추가 (총 22개 PASS) |
| 2026-04-30 | 0-2. content_hash 정의 일치 | 6.2 | README ↔ 코드 ↔ schema_v1.md §6 정직 노선으로 정정. 정의 잠금 테스트 2개 추가 (총 24개 PASS). schema v1.4 박제 |
| 2026-04-30 | 0-3. 공통 HTTP 클라이언트 | 6.5 | core/http.py 신설 (timeout/재시도/429×2 backoff/4xx 즉시실패/UA 통일). 3개 수집기 마이그레이션 완료, 직접 requests 참조 0건. HTTP 동작 잠금 테스트 14개 추가 (총 38개 PASS) |
| 2026-04-30 | 0-4. 폴백 날짜 제거 → R07 격리 | 6.7 | sentinel date(1900,1,1) + metadata.date_parse_failed 표지. R07 룰 추가(연도<1948 / 미래 / 표지) + report.py·README·schema_v1.md 일관 갱신. 3개 수집기 마이그레이션. 격리 잠금 테스트 4개 추가 (총 42개 PASS) |
| 2026-04-30 | 0-5. print 제거 → logging | 6.8 | core/logging.py 신설(setup_logging idempotent + 외부로거 다운그레이드). 4개 모듈 33건 print → 레벨별 log 호출(error/warning/info). pipeline.py가 매 run마다 runs/&lt;run_id&gt;/pipeline.log를 자동 생성. logging 잠금 테스트 5개 추가 (총 47개 PASS) |
| 2026-04-30 | 0-6. docs.jsonl 원자적 쓰기 | **7.0** | **Phase 0 완료.** core/atomic.py 신설(staging→os.replace 패턴, PID suffix로 충돌회피). storage.save_documents·seen_store.mark_seen 모두 atomic 전환. 배치 API mark_seen_many 추가로 commit_seen_for_passed 비용 1/N. atomic·storage·seen_store 잠금 테스트 22개 추가, mock으로 os.replace 실패 시 target 보존 직접 검증 (총 69개 PASS) |
| 2026-05-01 | 1-1. 수집기 mock 테스트 + coverage 70% | 7.2 | `tests/ingest/` 3파일(14개) 추가. 정상·빈결과·429·비정상 JSON 검증. 전체 83 passed, coverage 약 74%. |
| 2026-05-01 | 1-2. GitHub Actions CI | **7.5** | `.github/workflows/ci.yml` 추가, ruff+mypy+pytest(coverage gate 70%) 자동 실행. `Readme.md` 상단 CI/Coverage 배지 연결, 로컬 선검증 통과. |
| 2026-05-01 | 1-3. metrics.json + dashboard.md | **7.5** | `pipeline.py`에 `metrics.json` 자동 기록 추가, `scripts/build_dashboard.py`로 `docs/dashboard.md` 자동 생성. 메트릭/대시보드 잠금 테스트 2건 추가 (총 85 passed). |
| 2026-05-01 | 1-4. configs/pipeline.yaml 외부화 | **7.5** | `core/config.py`(pydantic+pydantic-settings) 추가, `configs/pipeline.yaml`/`dev.yaml`/`prod.yaml` 작성. `pipeline.py --config`로 정책 주입, 수집기 파라미터 하드코딩 제거. 설정 로더 테스트 2건 추가 (총 87 passed). |
| 2026-05-01 | 1-5. ruff + pre-commit | **7.5** | `.pre-commit-config.yaml` 추가(ruff/ruff-format, `src/` 대상). `pre-commit install` 및 `run --all-files`로 코드 포맷 정리 후 `ruff check src/`, `mypy`, `pytest` 재검증 통과 (총 87 passed). |
| 2026-05-01 | 2-1. scripts/ + Docker | **7.8** | `docker/Dockerfile`, `docker/docker-compose.yml`, `.dockerignore` 추가. `scripts/`에 build/run/smoke/replay 셸 스크립트 구성. `docker compose config` 및 `docker build -f docker/Dockerfile .` 검증 통과. |
| 2026-05-01 | 2-2. Replay 모드 (`replay --run-path`) | **8.0** | `core/replay.py` + `services/cli.py`로 replay 구현. `python -m govlexops.services.cli replay --run-path ... --only-failures --regenerate-report` 지원, `replay_report.md` 생성. replay 테스트 3건 추가 (총 90 passed). |
| 2026-05-01 | 2-3. ETL 5단계 디렉터리 | **8.1** | `core/raw_store.py` 추가로 원본 응답 gzip 보관(`data_index/raw`). 파이프라인이 `raw/normalized/extracted/chunks/embeddings/quality` 자동 생성. 수집기 3종 raw 저장 연결, raw_store 테스트 2건 추가 (총 92 passed). |
| 2026-05-01 | 2-4. 법률 도메인 온톨로지 정리 (draft) | **8.2** | `docs/ontology/`에 `concepts.md`, `relations.md`, `kr_us_mapping.md` 추가. 개념/관계를 active·pending으로 분리하고 relation별 근거 필드/신뢰도 명시. README에 온톨로지 링크 연결. |
| 2026-05-01 | 2-5. Failure Catalog | **8.3** | `qa/failure_catalog.py` 추가, `qa/report.py`가 실패 건을 카탈로그에 누적 적재. `scripts/analyze_failures.py`로 `docs/failure_patterns.md` 자동 생성. failure_catalog 테스트 2건 추가 후 총 94 passed. |
| 2026-05-01 | 2-6. Adapter 패턴 | **8.5** | `integrations/store/base.py` 인터페이스와 `jsonl_store.py`/`sqlite_store.py` 구현, `factory.py` 추가. `configs/*.yaml`에 `store_backend`, `sqlite_path` 도입 후 파이프라인이 백엔드 선택 주입. adapter 테스트 2건 추가, 총 96 passed. |
| 2026-05-01 | 3-1. ADR 7개 작성 | **8.7** | `docs/adr/ADR-001.md`~`ADR-007.md` 작성. 의사결정 7건을 Context/Decision/Consequences/Alternatives 형식으로 고정해 "왜 이렇게 설계했는가"를 문서 증거로 정리. `Readme.md`에 `docs/adr/` 링크 추가. |
| 2026-05-01 | 3-3. entities/relations 추출 | **8.9** | `src/govlexops/etl/extract.py` 신설. KR 국회 법안(`kr_assembly_*`)의 `ppsr_nm`, `jrcmit_nm`에서 `Member/Committee` 엔티티와 `PROPOSED_BY/REVIEWED_BY` 관계 추출. 파이프라인이 `data_index/extracted/entities.jsonl`, `relations.jsonl`을 자동 생성/누적. 추출 테스트 3건 추가. |
| 2026-05-01 | 3-4. 하이브리드 검색(BM25+벡터) | **9.0** | `src/govlexops/search/indexer.py`를 BM25+해시 벡터 코사인 하이브리드로 확장. `AI↔인공지능`, `privacy↔개인정보` 동의어 확장 추가. `app.py`에 검색 모드(하이브리드/BM25) 토글 추가. 검색 회귀 테스트 2건(`tests/test_search_hybrid.py`) 추가. |
| 2026-05-01 | 3-5. CODIT 매핑표 + scoring_mapping | **9.1** | `Readme.md` §18을 `요구사항/증명/코드 링크` 3열 표로 업그레이드. `docs/scoring_mapping.md` 신설해 JD 항목별 증거 경로를 상세 매핑하고 면접용 30초 답변 템플릿 추가. |
| | | | |

---

# 14. CODIT 면접 준비물

> Phase 4까지 끝낸 후, 채용 지원 직전에 이 섹션을 채워나갑니다.
> 지금은 뼈대만. 진행하면서 살을 붙이세요.

## 14-1. JD ↔ 포트폴리오 매핑 표 (위 §1-3 그대로 활용)

면접 시 화면 공유용. 이 표 한 장이 면접관 손에 들리는 순간 게임 끝.

## 14-2. 면접 어필 한 줄 모음 (Phase별)

각 Phase 끝낼 때마다 추가:

### Phase 0 (✅ 완료)
- **0-1**: "도장 찍는 순서가 잘못돼서 멀쩡한 책이 영원히 차단되는 데이터 손실 버그를 발견하고 `commit_seen_for_passed` 분리로 해결. 회귀 방지 테스트 3건도 같이 박았습니다."
- **0-2**: "안내문(README)과 코드가 다른 거짓말 상태였는데, 정직하게 정정하고 한계·미래 계획까지 schema v1.4로 박제했습니다."
- **0-3**: "수집기 3종이 제각각 `requests.get`을 쓰던 것을 `core/http.py` 단일 진입점으로 통일. 429에는 ×2 가중 backoff, 4xx는 즉시 실패, User-Agent까지 잠그고 14개 테스트로 동작을 박았습니다."
- **0-4**: "날짜 파싱 실패 시 `2000-01-01`로 silent fallback하던 무결성 거짓말을 sentinel + R07 격리로 바꿨습니다. 이전엔 진짜 2000년 데이터와 구별 불가능했지만, 이제 quality_report.md에서 추적됩니다."
- **0-5**: "외치기만 하던 print를 logging으로 일원화하고, 매 run마다 `runs/<run_id>/pipeline.log` 자동 생성. 이전 run에 다음 run 메시지 안 섞이는 것까지 테스트로 박았습니다."
- **0-6**: "JSONL 저장과 영구 dedup 모두 staging→`os.replace` 패턴으로 atomic write 전환. `os.replace`를 강제 실패시키는 mock으로 'rename 직전 죽어도 target이 보존되는가'를 직접 검증. 메모리 캐시 갱신도 atomic write 성공 후에만 일어나도록 설계해 부분 일관성 깨짐을 막았습니다."

### Phase 1~4 (진행 후 작성)
- **1-1**: "`responses`로 KR/US/국회 수집기 HTTP 스텁. 정상·빈 목록·429·비정상 JSON을 각 소스에 맞게 검증(`tests/ingest/`). 국회는 상위 루프가 예외를 삼키는 구간은 `request_json` 단위로 분리 검증. `pytest --cov=govlexops` 약 74%."
- **1-2**: "`.github/workflows/ci.yml` 신설. push/PR마다 `ruff check src/` + `mypy src/govlexops --ignore-missing-imports` + `pytest tests/ --cov=govlexops --cov-fail-under=70` 자동 실행. `Readme.md` 상단에 CI/Coverage 배지 연결."
- **1-3**: "`pipeline.py`에 run 메트릭 기록(`runs/<run_id>/metrics.json`) 추가. `scripts/build_dashboard.py`로 누적 run 집계 후 `docs/dashboard.md` 자동 생성. `tests/test_metrics_dashboard.py` 2건으로 metrics/dashboard 동작 잠금."
- **1-4**: "`src/govlexops/core/config.py`에 pydantic 설정 로더 추가 + `configs/pipeline.yaml`, `configs/dev.yaml`, `configs/prod.yaml` 분기. 파이프라인은 `--config` 인자로 정책 로드해 수집기 파라미터(쿼리/건수/연도오프셋/국회 옵션)를 주입."
- **1-5**: "`.pre-commit-config.yaml`에 ruff/ruff-format 훅 도입(대상: `src/`). `pre-commit install`로 커밋 훅 설치, `pre-commit run --all-files`로 포맷 일괄 정리. 이후 `ruff check src/` + `mypy` + `pytest` 재검증 통과."
- **2-1**: "`docker/Dockerfile`, `docker/docker-compose.yml` 추가로 컨테이너 재현 실행 경로 확보. `scripts/build_docker.sh`, `run_pipeline.sh`, `smoke_test.sh`, `replay_run.sh` 풀세트 구성. `docker build`와 `docker compose config` 검증 통과."
- **2-2**: "`src/govlexops/services/cli.py`(Typer)로 `run`/`replay` 커맨드 추가. `src/govlexops/core/replay.py`에서 run 경로 기준 재검증(`--only-failures`, `--regenerate-report`) 구현 후 `replay_report.md` 생성. replay 테스트 3건 포함 전체 90 passed."
- **2-3**: "`core/raw_store.py`로 API 원본 응답 gzip 보관(`data_index/raw/<source>/<date>/...`) 추가. 파이프라인 시작 시 `raw/normalized/extracted/chunks/embeddings/quality` 6개 디렉터리 자동 생성. 수집기 3종에 raw 저장 플래그 주입 후 전체 92 passed."
- **2-4**: "`docs/ontology/concepts.md`, `relations.md`, `kr_us_mapping.md`로 온톨로지 초안 작성. active/pending 구분, relation별 근거 필드와 confidence를 명시해 Phase 3-3의 entities/relations 추출 기준을 고정."
- **2-5**: "`qa/failure_catalog.py`로 실패 카탈로그(`data_index/quality/failure_catalog.jsonl`) 누적 기록. `scripts/analyze_failures.py`로 rule/source_type/jurisdiction 패턴을 `docs/failure_patterns.md` 생성. 파이프라인 시작 시 카탈로그 요약 로그 출력."
- **2-6**: "`integrations/store/`에 `DocumentStore` 인터페이스 + `jsonl_store.py`/`sqlite_store.py` 추가. `create_document_store()` 팩토리로 `store_backend`를 주입해 같은 파이프라인 코드로 JSONL/SQLite 전환 가능. 어댑터 테스트 2건 추가 후 전체 96 passed."
- **3-1**: "`docs/adr/ADR-001~007` 작성으로 JSONL 선택, content_hash 정의, metadata 승격 정책, QA 분리, run_id 격리, config 외부화, 검색 마이그레이션 트리거를 의사결정 문서로 고정. README에 Architecture Decisions 링크를 연결."
- **3-3**: "`src/govlexops/etl/extract.py`를 추가해 국회 법안 metadata(`ppsr_nm`, `jrcmit_nm`)에서 엔티티/관계를 추출하고 `data_index/extracted/entities.jsonl`, `relations.jsonl`로 누적 저장. 파이프라인에 `extract_done` 이벤트를 연결해 run 단위 관측이 가능해졌습니다."
- **3-4**: "`search/indexer.py`에 BM25+벡터 하이브리드 점수 결합(0.6/0.4)과 KR/EN 동의어 확장을 적용. `app.py`에서 모드 토글로 비교 검색이 가능해졌고, 'AI' 질의가 '인공지능' 문서를 찾는 회귀 테스트를 추가."
- **3-5**: "`Readme.md` §18을 '증거 링크' 중심 매핑표로 개편하고 `docs/scoring_mapping.md`를 신설해 CODIT JD 항목별 코드/문서 경로를 고정. 면접에서 '어디 코드냐' 질문에 5초 내 답할 수 있는 링크형 증거 맵을 완성."
- ...

## 14-3. 화면 공유용 자산

면접 시 미리 띄워둘 화면:

1. **§13 점수 추적 표** — 5.8 → 9.5 흐름 정량 보여주기
2. **`pytest tests/ -v` 결과 스크린샷** — XX passed 시각화
3. **`runs/<id>/quality_report.md` 예시** — QA 룰 통과율
4. **`runs/<id>/pipeline.log` 예시** — logging 작동 시연
5. **`docs/dashboard.md`** — Phase 1-3 후 운영 메트릭
6. **챗봇 데모 영상 60초** — Phase 4-4 후 통합 시연

## 14-4. 예상 면접 질문 답변

| 질문 | 답변 핵심 |
|------|---------|
| 왜 우리 회사? | "Chat CODIT을 알고 지원했습니다. 한미 법률 데이터 글로벌 표준화 + LLM 챗봇 두 역량이 정확히 제 두 포트폴리오와 매칭됩니다." |
| 어려웠던 점? | "0-1 R01 mark_seen 버그 발견 스토리 — 통과한 줄 알았던 데이터가 R02에서 거부되면 영원히 차단되는 패턴." |
| 협업 경험? | "Helixops에서 ADR 패턴으로 의사결정 흔적을 남겨봤고, GovLex에도 ADR-001~007을 작성했습니다. 백엔드 개발자가 의사결정 맥락을 5분에 따라잡을 수 있게." |
| 데이터 정확성? | "직접 발견·해결한 3대 무결성 이슈 (R01 / content_hash / 2000-01-01) — 모두 회귀 방지 테스트로 박았습니다." |
| 프로세스 개선? | "5.8 → 9.5+로 6+개월간 자체 개선한 24단계 마스터 플랜이 있습니다 (`masterplan.md`)." |
| 챗봇 환각 방지? | "RAG + 인용 강제. 검색 결과에 근거 없으면 답변 거부. eval 셋 100개로 정답률·인용 정확도 정량 측정." |
| 영어로 미국 데이터 다룰 수 있나? | "Congress.gov API 영어 응답 직접 파싱하고 KNOWN_AI_BILLS 같은 영어 법안명 처리 코드를 짰습니다." |

## 14-5. 이력서 한 줄 (스킬 어필)

> "한·미 법률·법안 50만 건을 ETL하는 GovLex-Ops 데이터 파이프라인을 5.8/10 → 9.5/10으로 자체 개선(24단계 로드맵·테스트 19→100+개)하고, 그 위에 Chat CODIT 미니 클론 RAG 챗봇(eval 정답률 87%, 인용 정확도 93%)까지 직접 구현."

---

*마스터 플랜 — 마지막 갱신: 2026-05-01*
*다음 단계: Phase 3 종료 점검 (3-2 실데이터 수집 재시도) 후 Phase 4-1.*

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
