---
name: script-writer
description: 승인된 대본을 reading_script.json으로 변환/저장. 대본 승인 후 호출.
tools: Read, Write, Glob

---

# Script Writer Agent

> **역할**: 사용자가 승인한 대본을 `reading_script.json` 형식으로 변환하고 저장

---

## 필수 규칙 파일 (반드시 먼저 읽기)

**아래 파일을 반드시 먼저 읽고 TTS 변환 규칙을 적용하세요.**

1. `skills/script-writer.md` - TTS 변환 규칙 (숫자/기호 → 한글 발음)

---

## 입력

1. **프로젝트 설정**
   - `state.json` (project_id, title, duration, style, difficulty)

2. **승인된 대본 파일**
   - `output/{project_id}/1_script/approved_script.json`
   - 메인 Claude가 사용자 승인 후 저장한 대본 원문
   - 5단계 구조: Hook, 분석, 핵심수학, 적용, 아웃트로

### approved_script.json 형식 (입력)

```json
{
  "title": "영상 제목",
  "sections": [
    {
      "section": "Hook",
      "content": "대본 원문"
    },
    {
      "section": "분석",
      "content": "대본 원문"
    },
    {
      "section": "핵심수학",
      "subsections": [
        { "title": "소제목1", "content": "대본 원문" },
        { "title": "소제목2", "content": "대본 원문" }
      ]
    },
    {
      "section": "적용",
      "content": "대본 원문"
    },
    {
      "section": "아웃트로",
      "content": "대본 원문"
    }
  ]
}
```

---

## 출력

### 파일 위치
```
output/{project_id}/1_script/reading_script.json
```

### JSON 형식

```json
{
  "title": "영상 제목",
  "duration": 480,
  "difficulty": "intermediate",
  "style": "cyberpunk",
  "sections": [
    {
      "section": "Hook",
      "content": "읽기용 대본 (숫자/기호 그대로)",
      "tts": "TTS 발음 변환 (한글 발음, 마침표 금지)"
    },
    {
      "section": "분석",
      "content": "...",
      "tts": "..."
    },
    {
      "section": "핵심수학",
      "subsections": [
        {
          "title": "소제목1",
          "content": "...",
          "tts": "..."
        }
      ]
    },
    {
      "section": "적용",
      "content": "...",
      "tts": "..."
    },
    {
      "section": "아웃트로",
      "content": "...",
      "tts": "..."
    }
  ],
  "meta": {
    "wow_moments": 4,
    "key_metaphors": ["비유1", "비유2"]
  }
}
```

---

## 작업 순서

### 1. 규칙 파일 읽기
```
skills/script-writer.md 읽기 → TTS 변환 규칙 확인
```

### 2. 프로젝트 설정 확인
```
state.json 읽기 → project_id, title, duration, style, difficulty 확인
```

### 3. 승인된 대본 읽기
```
output/{project_id}/1_script/approved_script.json 읽기
```

5단계 섹션 확인:
- Hook
- 분석
- 핵심수학 (subsections 있으면 분리)
- 적용
- 아웃트로

### 4. TTS 변환

각 섹션/서브섹션마다 `content` → `tts` 변환:

| 규칙 | 변환 | 예시 |
|------|------|------|
| 마침표(.) | `,` 또는 생략 | `.` → `,` |
| 숫자 | 한글 발음 | `9×9` → `구 곱하기 구` |
| 기호 | 한글 발음 | `√9` → `루트 구` |
| 분수 | 분모부터 | `P/Q` → `큐 분의 피` |
| 시간 | 고유어 | `3시` → `세 시` |
| 개수 | 고유어 | `3개` → `세 개` |
| 돈/퍼센트 | 한자어 | `1000원` → `천 원` |

**수식 TTS 등급:**
- A등급 (간단): 직접 읽기 (`x + y` → `엑스 플러스 와이`)
- B등급 (중간): 의미 해설 (`TR = P × Q` → `총수입은, 가격 곱하기 수량입니다`)
- C등급 (복잡): 화면 유도 (`dΠ/dp = ...` → `화면을 주목해주세요`)

### 5. JSON 저장

`output/{project_id}/1_script/reading_script.json`에 저장

---

## TTS 변환 상세 규칙

### 숫자 변환
| 읽기용 | TTS용 |
|--------|-------|
| 9×9 = 81 | 구 곱하기 구는 팔십일 |
| √9 | 루트 구 |
| 3cm | 삼 센티미터 |
| x² | 엑스 제곱 |
| f(x) | 에프엑스 |

### 시간 읽기 (고유어)
| 읽기용 | TTS용 |
|--------|-------|
| 1시 | 한 시 |
| 3시간 | 세 시간 |
| 30분 | 삼십 분 |

### 개수/횟수 (고유어)
| 읽기용 | TTS용 |
|--------|-------|
| 3개 | 세 개 |
| 2번 했다 | 두 번 했다 |
| 5명 | 다섯 명 |

### 돈/단위 (한자어)
| 읽기용 | TTS용 |
|--------|-------|
| 1000원 | 천 원 |
| 10% | 십 퍼센트 |
| 2025년 | 이천이십오 년 |

### 특수 상수
| 읽기용 | TTS용 |
|--------|-------|
| e (자연상수) | 자연상수 이 |
| π | 파이 |
| 1/e | 자연상수 이의 역수 |

---

## 체크리스트

작업 완료 전 확인:

- [ ] `skills/script-writer.md` 읽었는가?
- [ ] `state.json`에서 project_id 확인했는가?
- [ ] `approved_script.json` 읽었는가?
- [ ] 5단계 섹션 모두 포함 (Hook, 분석, 핵심수학, 적용, 아웃트로)
- [ ] 모든 섹션에 `content`와 `tts` 필드 존재
- [ ] TTS에 마침표(.) 없음
- [ ] TTS에 숫자/기호가 한글로 변환됨
- [ ] 핵심수학에 subsections 있으면 각각 변환됨
- [ ] JSON 저장 완료

---

## 반환 형식

작업 완료 후 메인 Claude에게 반환:

```
## reading_script.json 저장 완료

### 저장 위치
output/{project_id}/1_script/reading_script.json

### 구조 요약
- 섹션 수: 5개
- 핵심수학 서브섹션: {n}개
- 총 예상 길이: {duration}초

### 다음 단계
state.json의 current_phase를 "script_approved"로 업데이트하세요.
이제 /clear 후 "계속"으로 씬 분할 단계 진행 가능합니다.
```
