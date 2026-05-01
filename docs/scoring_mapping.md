# CODIT JD ↔ GovLex-Ops Scoring Mapping

GovLex-Ops 결과물을 CODIT Legal Data Specialist JD 항목에 1:1로 매핑한 문서입니다.  
면접 중 "이 항목을 어디서 증명하나요?" 질문에 바로 파일 경로로 답하기 위한 증거 맵입니다.

## 1) JD 매핑 표

| CODIT JD 요구사항 | GovLex-Ops 증명 | 코드/문서 링크 |
|---|---|---|
| 글로벌 법률·규제 공개 데이터 리서치·확보 | KR 법제처 / KR 국회 / US Congress 3개 소스 카탈로그화 | [`docs/source_catalog.md`](source_catalog.md), [`src/govlexops/etl/ingest/kr_law.py`](../src/govlexops/etl/ingest/kr_law.py), [`src/govlexops/etl/ingest/assembly_bills.py`](../src/govlexops/etl/ingest/assembly_bills.py), [`src/govlexops/etl/ingest/us_congress.py`](../src/govlexops/etl/ingest/us_congress.py) |
| 내부 데이터 표준에 맞춘 구조화·정제 | 9필드 canonical schema + metadata 정책 + source_type 체계 | [`src/govlexops/schemas/legal_document.py`](../src/govlexops/schemas/legal_document.py), [`docs/schema_v1.md`](schema_v1.md), [`docs/ontology/kr_us_mapping.md`](ontology/kr_us_mapping.md) |
| 백엔드 개발자와 협업한 파이프라인 설계 | ingest/core/qa/integrations 모듈 분리 + 저장소 어댑터 패턴 | [`src/govlexops/etl/pipeline.py`](../src/govlexops/etl/pipeline.py), [`src/govlexops/integrations/store/base.py`](../src/govlexops/integrations/store/base.py), [`src/govlexops/integrations/store/factory.py`](../src/govlexops/integrations/store/factory.py) |
| 가공 데이터 품질 검증(정확도/일관성) | QA 룰(R01/R02/R05/R07) + 품질 리포트 + 실패 카탈로그 | [`src/govlexops/qa/rules.py`](../src/govlexops/qa/rules.py), [`src/govlexops/qa/report.py`](../src/govlexops/qa/report.py), [`src/govlexops/qa/failure_catalog.py`](../src/govlexops/qa/failure_catalog.py), [`docs/failure_patterns.md`](failure_patterns.md) |
| 데이터 관리 프로세스 개선·자동화 | CI/정적검사/테스트 게이트 + run metrics + dashboard 자동 생성 | [`.github/workflows/ci.yml`](../.github/workflows/ci.yml), [`.pre-commit-config.yaml`](../.pre-commit-config.yaml), [`src/govlexops/etl/pipeline.py`](../src/govlexops/etl/pipeline.py), [`scripts/build_dashboard.py`](../scripts/build_dashboard.py), [`docs/dashboard.md`](dashboard.md) |
| 재현 가능 운영(운영 안정성) | Docker/Compose 실행 경로 + Replay 재검증 + run 단위 로그 | [`docker/Dockerfile`](../docker/Dockerfile), [`docker/docker-compose.yml`](../docker/docker-compose.yml), [`src/govlexops/core/replay.py`](../src/govlexops/core/replay.py), [`src/govlexops/services/cli.py`](../src/govlexops/services/cli.py) |
| 의사결정 문서화(설계 근거) | ADR 7개로 주요 결정의 Context/Decision/Trade-off 고정 | [`docs/adr/`](adr/), [`docs/adr/ADR-005.md`](adr/ADR-005.md), [`docs/adr/ADR-007.md`](adr/ADR-007.md) |
| 정형/비정형 혼합 데이터 표준화 | 법안 summary 자유 텍스트를 `metadata.summary`에 흡수해 공통 객체 유지 | [`src/govlexops/etl/ingest/assembly_bills.py`](../src/govlexops/etl/ingest/assembly_bills.py), [`src/govlexops/schemas/legal_document.py`](../src/govlexops/schemas/legal_document.py) |
| 관계형 인사이트 기반 확장성 | 의원/위원회 엔티티 + 관계(`PROPOSED_BY`, `REVIEWED_BY`) 추출 | [`src/govlexops/etl/extract.py`](../src/govlexops/etl/extract.py), [`data_index/extracted/entities.jsonl`](../data_index/extracted/entities.jsonl), [`data_index/extracted/relations.jsonl`](../data_index/extracted/relations.jsonl) |

## 2) 면접 30초 답변 템플릿

- **요구사항**: "품질 검증 자동화 했나요?"
- **답변**: "네. `qa/rules.py`에서 룰 기반 검증, `qa/report.py`에서 run별 리포트 생성, `qa/failure_catalog.py`로 누적 패턴 분석까지 연결했습니다. 결과는 `docs/dashboard.md`와 `docs/failure_patterns.md`에서 추적 가능합니다."

- **요구사항**: "재현 가능한 파이프라인인가요?"
- **답변**: "Docker/Compose로 동일 실행이 가능하고, `replay --run-path`로 과거 실행을 재검증할 수 있습니다. run 산출물은 `runs/<run_id>/`에 격리됩니다."

## 3) 사용법

1. README §18의 요약 표에서 항목 확인
2. 이 문서의 링크를 열어 실제 코드/문서를 즉시 제시
3. 필요 시 `masterplan.md` §13(점수 추적)와 함께 성장 흐름까지 설명
