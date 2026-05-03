# LEGAL OVERCLAIM COPY AUDIT

## Scope audited
- `index.html`
- `ai.html`
- `README.md`
- Public-facing docs likely to influence messaging decisions (`docs/GEMINI_CONTEST_REVIEW_ACTION_PLAN.md`)

## Audit framework
This audit flags user-facing copy that may create legal overclaim risk in five categories:
1. Implied official legal authority
2. Implied visa eligibility determination
3. Implied administrative representation or application handling
4. Implied guaranteed accuracy or official decision-making
5. Safer replacement wording

Priority levels:
- **P0**: must fix before contest submission
- **P1**: should fix soon
- **P2**: nice to improve

---

## Findings

| ID | File | Risky phrase (current) | Risk type | Why risky | Safer replacement wording | Priority |
|---|---|---|---|---|---|---|
| F-01 | `ai.html` | "맞춤형 행정 절차와 구비 서류를 **검증해 드립니다**" | 1, 2, 4 | "검증" implies authoritative adjudication and can be interpreted as official correctness determination. | "공개 법령·매뉴얼을 바탕으로 **참고용 절차/서류 정보를 안내합니다**" | P0 |
| F-02 | `index.html` | "AI가 ... 기반한 **완벽한 솔루션을 제공합니다**" | 2, 4 | "완벽한" + "솔루션" implies guaranteed outcomes and problem resolution authority. | "AI가 공개 자료를 근거로 **참고용 설명을 제공합니다**" | P0 |
| F-03 | `index.html` | "자의적 해석 없이 **철저한 법적 판단 및 구제 절차**를 검증" | 1, 2, 4 | "법적 판단" and "구제 절차 검증" implies legal judgment and near-consultation/service authority. | "관련 법령·매뉴얼의 **근거 조항과 일반 절차를 참고용으로 정리**" | P0 |
| F-04 | `index.html` | "해당 체류자격을 발급, 연장 또는 변경할 가능성을 **객관적으로 평가**" | 2, 4 | Eligibility/approval likelihood assessment can be interpreted as legal determination. | "요건 항목을 기준으로 **확인 포인트를 안내**" | P0 |
| F-05 | `index.html` | "가장 정확한 비자 정보" | 4 | "가장 정확한" is a superlative guarantee claim. | "공개 자료 기반의 비자 정보" | P1 |
| F-06 | `index.html` | "공식 인프라로의 도약", "플랫폼의 공식적 지향점" | 1 | "공식" can imply government endorsement or authority. | "공공 정보 접근 인프라 지향" | P1 |
| F-07 | `index.html` | "AI 자연어 분석으로 **공식 직종 및 업종 찾기**" | 1, 4 | "공식 ... 찾기" can imply formal classification authority rather than reference lookup. | "AI 분석으로 **직종·업종 코드 후보 안내**" | P1 |
| F-08 | `index.html` | "실질적인 행정 처리 시간을 단축" | 3, 4 | Can imply procedural handling capability rather than information support only. | "정보 탐색 및 준비 시간을 줄이는 데 도움" | P1 |
| F-09 | `index.html` | "AI 심층 법률 검증 시작", "법령 팩트체크 및 사례 심층 검증" | 1, 4 | "법률 검증" wording can be read as legal review service. | "법령·매뉴얼 **근거 확인 시작**" | P1 |
| F-10 | `ai.html` | `DISLCAIMER` 문구 중 "정확한 행정 처리는 ... 확인" | 3 | "행정 처리" could still imply processing workflow support rather than reference-only role. | "최종 요건과 접수 가능 여부는 관할 기관에 확인" | P2 |
| F-11 | `README.md` | "공식 시드 URL 등록 SQL", "공식 사이트 HTML/PDF 수집기" | 1 | Internal/dev doc but publicly visible; "공식" may be misread as institutional affiliation. | "원천/기관 공개 URL" 또는 "기관 공개 사이트" | P2 |

---

## Category coverage mapping

### 1) Phrases that imply official legal authority
- F-01, F-03, F-06, F-07, F-09, F-11

### 2) Phrases that imply visa eligibility determination
- F-02, F-03, F-04

### 3) Phrases that imply administrative representation or application handling
- F-08, F-10

### 4) Phrases that imply guaranteed accuracy or official decision-making
- F-01, F-02, F-03, F-04, F-05, F-07, F-08, F-09

### 5) Safer replacement wording themes to standardize
Use these consistently across UI and prompts:
- "참고용 정보"
- "공개 법령·매뉴얼 기반 안내"
- "근거 조항/출처 기반 설명"
- "최종 확인은 출입국·외국인청, 하이코리아, 또는 자격 있는 전문가"
- "법적 자문/행정 대행/신청 접수 서비스가 아님"

---

## Priority remediation order

### P0 (must fix before contest submission)
- F-01, F-02, F-03, F-04

### P1 (should fix soon)
- F-05, F-06, F-07, F-08, F-09

### P2 (nice to improve)
- F-10, F-11

---

## Notes
- Existing disclaimers already reduce risk, but high-risk overclaim phrases still coexist nearby and can override user perception.
- The next copy revision should prioritize replacing action/authority verbs (검증, 판단, 평가, 완벽한 솔루션) with reference-oriented guidance language.
