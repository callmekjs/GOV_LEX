# GovLex Ontology Concepts (Draft v0.1)

> 목적: Phase 3-3의 entities/relations 추출에 쓰일 최소 개념 트리 초안.
> 원칙: 데이터 근거가 있는 개념만 `active`, 아직 근거가 약한 개념은 `pending`.

## 1) 최상위 개념

```text
LegalDocument
├── Statute (법률)
│   ├── Act (법)
│   └── Decree (시행령/시행규칙) [pending]
├── Bill (법안)
│   ├── KRAssemblyBill (열린국회 법률안)
│   └── USCongressBill (Congress.gov bill)
├── Regulation (행정규칙/고시) [pending]
└── Minutes (의사록) [pending]
```

## 2) 행위자(Actor) 개념

```text
Actor
├── Member (국회의원/US sponsor)
├── Committee (위원회)
└── Ministry (소관부처)
```

## 3) 정책 영역 개념

```text
PolicyArea
├── AI/Data
├── Privacy
├── Fintech/Compliance
└── ICT/Cyber
```

## 4) 상태 정의

- `active`: 현재 파이프라인 필드에서 직접 근거 추출 가능
- `pending`: 현재 데이터셋에서는 근거가 부족하거나 미연결 소스 필요

## 5) 구현 메모

- 현재 `source_type` 실데이터 기준 핵심은 `law`, `bill`
- `Minutes`, `Decree`, `Regulation`은 3-2/3-3 확장 타이밍에 `active` 전환
