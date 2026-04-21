# 법률 도메인 이해 (Legal Domain Primer)

> 본 문서는 법학 비전공자가 법률 데이터 파이프라인 설계를 위해
> 학습하고 정리한 내용입니다. 법학적 엄밀성보다
> **데이터 모델링 관점의 일관성**을 우선합니다.

---

## 0. 이 문서의 목적

GovLex-Ops는 법률 문서를 다루는 파이프라인입니다.  
그런데 "법률 문서"라는 말 안에는 다음과 같이 서로 다른 것들이 섞여 있습니다.

- 통과된 법률
- 심사 중인 법안
- 대통령령·부령
- 위원회 회의록
- 판례
- 조약

각각 **생산 주체, 효력, 수집 경로**가 다릅니다.  
이 차이를 모른 채 `source_type = "legal"` 같이 하나로 묶으면,
나중에 검색·비교·RAG 모두 망가집니다.

본 문서는 **GovLex-Ops의 `source_type` 5개가 왜 이렇게 나뉘었는지**를
한국·미국 법제 구조 기준으로 정리합니다.

---

## 1. 한국 법제 구조 (Korean Legal System)

### 1-1. 법령 위계 (Hierarchy)

한국 법제는 **효력의 상하 관계**로 층을 이룹니다.

```
헌법 (Constitution)
  └ 법률 (Act)                         ── 국회 통과, 대통령 공포
     └ 시행령 (Presidential Decree)    ── 대통령령
        └ 시행규칙 (Enforcement Rule)  ── 부령·총리령
           └ 행정규칙 (Administrative Rule)
                                       ── 훈령·예규·고시 (각 부처 내부)
```

**핵심 규칙**: 하위 법령은 상위 법령에 위반될 수 없습니다.  
예를 들어 시행령은 법률이 위임한 범위 안에서만 만들 수 있습니다.

### 1-2. 입법 프로세스 (Legislative Process)

법률이 만들어지는 전 과정을 6단계로 정리하면:

| 단계 | 이름 | 영어 | 설명 |
|---|---|---|---|
| 1 | 발의 | Bill Introduction | 의원 10인 이상 또는 정부가 제출 |
| 2 | 상임위 심사 | Committee Review | 17개 상임위 중 소관 위원회 |
| 3 | 법사위 심사 | Judiciary Review | 체계·자구 심사 |
| 4 | 본회의 의결 | Floor Vote | 재적 과반 출석 + 과반 찬성 |
| 5 | 공포 | Promulgation | 대통령 공포 (15일 이내) |
| 6 | 시행 | Enforcement | 부칙 규정 시행일 |

**데이터 관점 중요 포인트**: 1~4단계에서는 `bill`, 5~6단계 이후는 `law`로 분류.  
같은 법안이라도 **시점에 따라 `source_type`이 달라집니다.**

### 1-3. 본 파이프라인에서의 매핑

| 입법 단계 | 수집 소스 | source_type | 현재 상태 |
|---|---|---|---|
| 1. 발의 | 열린국회정보 ALLBILLV2 | `bill` | ✅ 연결 완료 |
| 2. 심사 | 국회 위원회 회의록 API | `minutes` | Week 3+ 예정 |
| 3. 법사위 | 국회 법사위 회의록 | `minutes` | Week 3+ 예정 |
| 4. 본회의 | `metadata.status` 필드 | — | 상태값으로 반영 |
| 5. 공포 | 국가법령정보 API | `law` | ✅ 연결 완료 |
| 6. 시행 | `metadata.enforcement_date` | — | 메타데이터 |

### 1-4. 한국 특유의 용어

| 용어 | 뜻 |
|---|---|
| **의안** | 국회에 제출된 안건 전체 (법안 + 예산안 + 결의안 등) |
| **법률안** | 의안 중 "법을 만들거나 바꾸는 것" |
| **의원발의** | 의원이 발의한 법안 |
| **정부제출** | 정부가 제출한 법안 |
| **계류의안** | 심사 중인 법안 |
| **폐기의안** | 임기 만료로 사라진 법안 |
| **원안가결** | 원안 그대로 통과 |
| **수정가결** | 수정되어 통과 |
| **대안반영폐기** | 다른 법안으로 대체되어 폐기 |
| **제N대 국회** | 현재는 제22대 (2024~2028) |

---

## 2. 미국 법제 구조 (U.S. Legal System)

### 2-1. 연방법 위계

```
Constitution
  └ Public Law                          ── 의회 통과, 대통령 서명
     └ U.S. Code (USC)                  ── 주제별 법전화
        └ CFR (Code of Federal Regulations)  ── 연방 규정집
           └ Agency Rule                ── 각 기관 내부 규칙
```

### 2-2. 입법 프로세스

| 단계 | 이름 | 설명 |
|---|---|---|
| 1 | Bill Introduction | HR (House Bill) 또는 S (Senate Bill) |
| 2 | Committee Review | Markup, Hearing |
| 3 | Floor Vote | Roll Call Vote |
| 4 | Conference Committee | 양원 조정 (버전이 다를 때) |
| 5 | Presidential Action | 서명 / 거부권 |
| 6 | Public Law | PL 117-xxx 번호 부여 |

### 2-3. 본 파이프라인에서의 매핑

| 단계 | 수집 소스 | source_type | 현재 상태 |
|---|---|---|---|
| 1 | Congress.gov `/bill` | `bill` | ✅ 연결 완료 |
| 2 | Congress.gov Hearing API | `minutes` | Week 3+ 예정 |
| 3 | `metadata.latest_action` | — | 상태값으로 반영 |
| 6 | Congress.gov (enacted) | `law` | Week 3+ 예정 |
| 행정규제 | Federal Register API | `rule` | Week 3+ 예정 |

### 2-4. 미국 특유의 용어

| 용어 | 뜻 |
|---|---|
| **Bill** | 법안 (통과 전) |
| **Congress** | 의회 회기 단위 (2년, 현재 119th) |
| **Sponsor** | 법안 발의자 |
| **Cosponsor** | 공동 발의자 |
| **Committee** | 위원회 |
| **Hearing** | 청문회 |
| **Markup** | 위원회가 법안 수정하는 과정 |
| **Floor Vote** | 본회의 표결 |
| **Roll Call Vote** | 기명 표결 |
| **Enacted** | 법으로 제정됨 |
| **Public Law** | 통과된 법률 (PL 117-xxx 형식) |
| **Federal Register** | 연방 관보 (행정규제 공고) |
| **CFR** | Code of Federal Regulations, 규정집 |
| **USC** | U.S. Code, 법전 |

---

## 3. 한국·미국 공통 분모

양국 법제를 추상화하면 다음과 같이 매칭됩니다.

| 추상 개념 | 한국 | 미국 |
|---|---|---|
| 최상위 규범 | 헌법 | Constitution |
| **Primary Legislation** | **법률** | **Public Law** |
| **Secondary Legislation** | **시행령·시행규칙** | **CFR, Agency Rule** |
| Administrative Rule | 훈령·예규·고시 | Agency Internal Rule |
| **Pending Bill** | **법률안 (계류 중)** | **HR / S Bill** |
| **Legislative Record** | **회의록** | **Congressional Record / Hearing** |
| Judicial Decision | 판례 | Court Opinion |
| Treaty | 조약 | Treaty |

**본 파이프라인의 `source_type` 5개**(`law`, `decree`, `rule`, `bill`, `minutes`)는
이 공통 분모에서 **"양국 모두에 존재하고, 데이터 소스가 확보 가능한 것"** 만 추린 결과입니다.

---

## 4. source_type 분류 원칙

### 4-1. 왜 5개인가?

**조건 1: 데이터 소스가 실재할 것**
- `precedent`(판례)는 중요하지만 MVP에서 제외 → 추후 확장

**조건 2: 양국에서 의미가 통할 것**
- 한국의 `의안`은 예산안·결의안까지 포함 → 법률에만 한정하려면 `bill`로 축소

**조건 3: 효력 위계가 명확할 것**
- `law > decree > rule` 순서가 명확해야 검색·필터링이 가능

### 4-2. 분류 기준 플로우차트

```
문서가 들어왔을 때:

이 문서는 국회/의회를 통과했는가?
├─ 아니오 (심사 중 / 발의 상태)
│    └─ source_type: bill
│
└─ 예 (통과 완료)
     │
     이 문서는 국회가 직접 만든 것인가?
     ├─ 예 (국회 통과 법률)
     │    └─ source_type: law
     │
     └─ 아니오 (행정부가 만든 하위 규범)
          │
          이 문서는 대통령령인가?
          ├─ 예 → source_type: decree
          └─ 아니오 (부령/총리령/훈령 등)
               └─ source_type: rule


심사 과정의 기록인가? (회의록)
└─ 예 → source_type: minutes
```

### 4-3. `source_type`별 대표 예시

| source_type | KR 예시 | US 예시 |
|---|---|---|
| `law` | 인공지능 기본법 | Public Law 117-xxx |
| `decree` | 인공지능 기본법 시행령 | (정식 대응 없음, CFR로 대체) |
| `rule` | 개인정보 보호 고시 | CFR Title X, Section Y |
| `bill` | 의원 OO 발의 AI법률안 | HR 4763 |
| `minutes` | 외교통일위 회의록 | Committee Hearing Transcript |

---

## 5. 코딧(CODIT) 서비스와의 연결

### 5-1. 코딧이 제공하는 주요 서비스 (공개 정보 기반)

- **Chat CODIT** — 규제 질의응답
- **Regulatory Intelligence** — 규제 동향 추적
- **Compliance Monitoring** — 기업 준수 지원
- **Policy Monitoring** — 정책 실시간 추적

### 5-2. 이 서비스들이 필요로 하는 데이터

| 서비스 기능 | 필요한 source_type |
|---|---|
| "현재 이 법이 뭐라고 하나?" | `law`, `decree`, `rule` |
| "이런 규제가 새로 생기나?" | `bill` (Pending) |
| "이 법안이 왜 이렇게 바뀌었나?" | `minutes` |
| "이 법이 언제부터 시행되나?" | `law` + `metadata.enforcement_date` |
| "누가 이 법안을 발의했나?" | `bill` + `metadata.sponsor` |

### 5-3. GovLex-Ops가 기여하는 영역

**현재 MVP(Week 1–2)에서 커버**:
- ✅ 한국 `law` (국가법령정보 API)
- ✅ 한국 `bill` (열린국회정보 API)
- ✅ 미국 `bill` (Congress.gov API)

**Week 3+ 확장**:
- 한국 `minutes` (위원회 회의록)
- 한국 `decree`, `rule` (시행령·행정규칙)
- 미국 `rule` (Federal Register)
- 미국 `law` (Public Law)

이 구조로 **코딧 핵심 서비스의 데이터 백엔드** 역할을 가정합니다.

---

## 6. 비전공자로서 학습 자료

본 문서를 작성하면서 참고한 자료:

### 공식 문서
- 법제처 국가법령정보센터 서비스 설명
- 국회 입법과정 안내 (assembly.go.kr)
- Congress.gov Legislative Process Guide
- Federal Register API Documentation

### 학습 정리 순서
1. 한국 입법 프로세스 6단계 암기
2. 법령 위계 4층 구조 이해
3. 미국 입법 프로세스 6단계 암기
4. 양국 공통 분모 도출
5. `source_type` 5개 확정

### 데이터 엔지니어 관점에서 배운 점
- 법률 용어는 **"생산 주체 + 생산 단계"** 두 축으로 이해하면 깔끔함
- 한국 "시행령"과 미국 "CFR"은 정확히 대응되지 않음 → 공통 분모로 `decree`/`rule` 분리
- `bill` vs `law` 구분은 **"통과 여부"** 하나로 결정됨
- 회의록(`minutes`)은 **심사 과정의 근거**로 Regulatory Intelligence에 중요

---

## 7. 한계와 개선 여지

### 7-1. 본 문서의 한계

- 법학 비전공자의 정리이므로 **법학적 엄밀성**에는 부족할 수 있음
- 특히 **하위 법령 간 위계**(훈령 vs 예규 vs 고시)의 세부 구분은 단순화됨
- 판례·조약은 MVP에서 제외

### 7-2. 향후 보완 계획

| 항목 | 계획 |
|---|---|
| 판례 데이터 | `source_type: precedent` 추가 (Week 4+) |
| 조약 데이터 | `source_type: treaty` 추가 (Week 4+) |
| EU 법제 | `jurisdiction: EU` 확장 |
| 법령 개정 추적 | `metadata.amendment_history` 필드 |
| 법령 간 인용 관계 | 별도 그래프 DB 고려 |

---

## 8. 한 줄 요약

> **법률 문서는 "누가 만들었는가(생산 주체)"와 "어느 단계에 있는가(입법 단계)"
> 두 축으로 분류할 수 있으며, GovLex-Ops의 `source_type` 5개는
> 이 두 축의 공통 분모에서 도출되었다.**
