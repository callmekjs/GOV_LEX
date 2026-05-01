# KR-US Concept Mapping (Draft v0.1)

> 목적: 한미 법/입법 개념의 대응표를 고정해 추출 규칙 충돌을 줄인다.

## 1) 개념 대응표

| 한국(KR) | 미국(US) | GovLex 공통 개념 | 비고 |
|---|---|---|---|
| 법률 | Public Law (통과 후 법) | Statute | 현재 US 소스는 bill 중심이라 pending |
| 법안 | Bill | Bill | 양국 공통 |
| 시행령/시행규칙 | CFR/agency regulation | Decree/Regulation | 소스 연동 전 pending |
| 상임위/소관위 | Committee | Committee | KR은 `jrcmit_nm`, US는 committee API 확장 필요 |
| 소관부처 | Executive agency/department | Ministry/Agency | KR은 `ministry` 추출 가능 |
| 의사록 | Hearing transcript | Minutes | 현재 미연결 |

## 2) 필드 매핑 힌트 (현재 소스 기준)

### KR law (`kr_law.py`)

- 문서 타입: `source_type="law"`
- 부처: `metadata.ministry`
- 법령 분류: `metadata.law_type`

### KR assembly (`assembly_bills.py`)

- 문서 타입: `source_type="bill"`
- 위원회: `metadata.jrcmit_nm`
- 발의자: `metadata.ppsr_nm`
- 요약 텍스트: `metadata.summary`

### US congress (`us_congress.py`)

- 문서 타입: `source_type="bill"`
- 정책영역: `metadata.policy_area`
- 최신행동: `metadata.latest_action`, `metadata.latest_action_date`
- 챔버/유형: `metadata.origin_chamber`, `metadata.bill_type`

## 3) 운영 규칙

- 대응표는 “실데이터 필드 존재 여부”가 기준
- 개념 동형이 애매하면 공통 추상 개념에 먼저 매핑
- `pending` 항목은 Phase 3-2/3-3에서 승격 여부 재평가
