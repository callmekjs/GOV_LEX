# GovLex Ontology Relations (Draft v0.1)

> 목적: 관계 추출 파이프라인(Phase 3-3)에서 사용할 관계 카탈로그.
> 포맷: `subject -RELATION-> object` + 근거 필드 + confidence.

## 1) Active Relations

| Subject | Relation | Object | Source | Evidence field | Confidence | Notes |
|---|---|---|---|---|---|---|
| LegalDocument | BELONGS_TO | Jurisdiction | KR/US 공통 | `jurisdiction` | high | KR/US 분류 기본 축 |
| Bill | HAS_POLICY_AREA | PolicyArea | us_congress | `metadata.policy_area` | medium | policyArea 누락 가능 |
| Bill | HAS_LATEST_ACTION | Action | us_congress | `metadata.latest_action`, `metadata.latest_action_date` | medium | action text 정규화 필요 |
| KRAssemblyBill | REVIEWED_BY | Committee | kr_assembly | `metadata.jrcmit_nm` | medium | 비어있는 경우 존재 |
| KRAssemblyBill | PROPOSED_BY | Member | kr_assembly | `metadata.ppsr_nm` | medium | 공동발의 분해는 추후 |
| Statute | ISSUED_BY | Ministry | kr_law | `metadata.ministry` | medium | 부처명 표준화 필요 |
| LegalDocument | HAS_SOURCE_TYPE | SourceType | KR/US 공통 | `source_type` | high | `law`/`bill` 중심 |

## 2) Pending Relations

| Subject | Relation | Object | Activation condition |
|---|---|---|---|
| Bill | BECAME | Statute | bill↔law 연결 키 확보 시 |
| Statute | ENFORCED_BY | Decree | 시행령 소스 연동 후 |
| Minutes | DISCUSSES | Bill | 회의록 소스 연동 후 |
| Bill | CO_SPONSORED_BY | Member | 공동발의자 구조 파싱 후 |

## 3) Triple Notation (참고)

```text
KRAssemblyBill -PROPOSED_BY-> Member
KRAssemblyBill -REVIEWED_BY-> Committee
Statute -ISSUED_BY-> Ministry
USCongressBill -HAS_POLICY_AREA-> PolicyArea
Bill -HAS_LATEST_ACTION-> Action
```

## 4) 설계 원칙

- 근거 필드가 명확하지 않은 관계는 `pending`으로 유지
- `confidence=high`만 자동 그래프 적재, `medium`은 검증 큐를 거쳐 승격
- relation 이름은 대문자 스네이크(`HAS_POLICY_AREA`)로 통일
