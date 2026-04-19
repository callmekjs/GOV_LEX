# Source Catalog v1

> GovLex-Ops가 수집하는 공개 데이터 소스 목록.
> 소스별 접근 방식·제한·라이선스를 명시합니다.

---

## 한국 (KR)

### 1. 국가법령정보 Open API
- **운영기관**: 법제처
- **사이트**: https://open.law.go.kr
- **수집 데이터**: 현행 법령 전문 (법률·시행령·시행규칙·행정규칙)
- **접근 방식**: REST API (OC 인증키, 공공데이터포털 자동승인)
- **응답 형식**: JSON
- **수집 주기**: 수동 실행 (Week 3+에서 자동화 예정)
- **일일 제한**: 10,000건
- **라이선스**: 공공저작물 자유이용 허락
- **수집 쿼리**: 인공지능, 데이터, 개인정보, 정보통신, 디지털
- **코드 위치**: `src/govlexops/etl/ingest/kr_law.py`

**수집 필드 매핑**:

| API 필드 | canonical 필드 | 비고 |
|---|---|---|
| 법령명한글 | title | - |
| 공포일자 | issued_date | YYYYMMDD → date |
| 법령일련번호 | source_url 생성 | lsInfoP.do?lsiSeq= |
| 법령ID | source_id 생성 | kr_law_{ID} |
| 법령구분명 | metadata.law_type | 법률/시행령/시행규칙 |
| 소관부처명 | metadata.ministry | - |

---

## 미국 (US)

### 2. Congress.gov API v3
- **운영기관**: 미국 의회도서관 (Library of Congress)
- **사이트**: https://api.congress.gov
- **수집 데이터**: AI·데이터·규제 관련 법안 (bill) 메타데이터
- **접근 방식**: REST API (API 키 무료 발급)
- **응답 형식**: JSON
- **수집 주기**: 수동 실행
- **시간당 제한**: 5,000건
- **라이선스**: Public Domain
- **수집 방식**: AI 관련 주요 법안 번호 직접 지정
- **코드 위치**: `src/govlexops/etl/ingest/us_congress.py`

**수집 필드 매핑**:

| API 필드 | canonical 필드 | 비고 |
|---|---|---|
| title | title | - |
| introducedDate | issued_date | YYYY-MM-DD → date |
| congress + type + number | source_id | us_congress_{c}_{t}{n} |
| congress + type + number | source_url | congress.gov URL 조합 |
| type | metadata.bill_type | HR/S/HJRES 등 |
| latestAction.text | metadata.latest_action | 최신 진행 상태 |
| policyArea.name | metadata.policy_area | 정책 분야 |

---

## 소스별 현황

| 국가 | 소스 | 수집 건수 | 마지막 수집 |
|---|---|---|---|
| KR | 국가법령정보 API | 51건 | 2026-04-19 |
| US | Congress.gov API | 10건 | 2026-04-19 |
| **합계** | | **61건** | |

---

## Week 3+ 추가 예정 소스

| 국가 | 소스 | 데이터 |
|---|---|---|
| KR | 열린국회정보 API | 국회 발의 법안 |
| KR | 국회 회의록 시스템 | 위원회 회의록 (PDF) |
| US | Federal Register API | 행정 규제 공고 |