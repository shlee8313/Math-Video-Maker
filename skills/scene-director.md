# Scene Director Skill

## 역할 정의

수학 교육 영상의 씬 분할과 의미적 구조를 설계하는 연출가입니다.

| 역할 | 담당 |
|------|------|
| **"무엇을(What)"** 보여줄지 | Scene Director (이 문서) |
| **"어떻게(How)"** 보여줄지 | Visual Prompter |
| **"코드로(Code)"** 구현 | Manim Coder |

### Scene Director의 책임

- 대본을 씬으로 분할
- 각 씬의 목적(semantic_goal) 정의
- 필요한 요소(required_elements) 목록화
- 강조 포인트(wow_moment) 지정
- 3D 씬 여부 판단
- 필요한 에셋 목록 작성

### Scene Director가 하지 않는 것

❌ 구체적인 좌표/위치 지정, 애니메이션 타입 결정, 색상 배치, 타이밍 세부 설계 → Visual Prompter 담당

---

## 입출력

### 입력
- `1_script/reading_script.json` (읽기용 대본)
- `1_script/tts_script.json` (TTS용 대본)
- `state.json` (프로젝트 설정: style, duration, aspect_ratio)

### 출력
- `output/{project_id}/2_scenes/scenes.json`

---

## JSON 출력 형식

```json
[
  {
    "scene_id": "s1",
    "section": "Hook",
    "duration": 12,
    "narration_display": "여러분, √9가 뭔지 아시나요?",
    "subtitle_display": "여러분, √9가 뭔지 아시나요?",
    "narration_tts": "여러분, 루트 구가 뭔지 아시나요?",
    "semantic_goal": "호기심 유발 - 제곱근을 질문으로 재정의",
    "required_elements": [
      {"type": "text", "content": "?", "role": "호기심 상징"},
      {"type": "math", "content": "\\sqrt{9}", "role": "주제 수식"}
    ],
    "wow_moment": "물음표가 제곱근 기호로 변하는 순간",
    "emotion_flow": "호기심 → 흥미",
    "style": "minimal",
    "is_3d": false,
    "scene_class": "Scene",
    "required_assets": []
  }
]
```

---

## 필수 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `scene_id` | string | s1, s2, s3... |
| `section` | string | Hook/분석/핵심수학/적용/아웃트로 |
| `duration` | number | 예상 길이 (초) |
| `narration_display` | string | 화면 자막용 (숫자/기호 형식) |
| `subtitle_display` | string | 자막 분할용 (`;;`로 분할 위치 표시) |
| `narration_tts` | string | TTS 음성용 (한글 발음) |
| `semantic_goal` | string | 씬의 목적 |
| `required_elements` | array | 필요한 요소 목록 |
| `wow_moment` | string/null | 강조 포인트 |
| `emotion_flow` | string | 감정 흐름 |
| `style` | string | 프로젝트 스타일 |
| `is_3d` | boolean | 3D 씬 여부 |
| `scene_class` | string | Scene / ThreeDScene |
| `required_assets` | array | 필요한 PNG 에셋 |

---

## 나레이션 3종 필드

| 필드 | 용도 | 작성 방식 |
|------|------|-----------|
| `narration_display` | 화면 표시 원문 | 자연스러운 문장 |
| `subtitle_display` | 자막 분할용 | `;;`로 분할 위치 표시 |
| `narration_tts` | TTS 음성용 | `,` 쉼표 = 짧은 쉼, `...` = 긴 쉼, **`.` 마침표 금지** |

---

## subtitle_display 규칙 (자막 분할)

> **핵심**: `narration_display`를 의미 단위로 분할하여 `;;` 삽입. Python은 `;;` 기준으로 SRT 생성.

### 분할 금지 패턴

| 금지 | 예시 |
|------|------|
| 수식 내부 | `V(s, t)` 내부 쉼표에서 분할 ❌ |
| 따옴표+조사 | `"말"` / `는 사실` ❌ |
| 콜론+10자미만 | `시간:` / `2시` ❌ |
| 5자 미만 자막 | `자,` 혼자 ❌ |

### 분할 허용 조건

> **분할점 앞뒤 모두 10자 이상 + 의미 완결 시에만**

| 우선순위 | 위치 | 예시 |
|----------|------|------|
| 1 | 마침표(.) 뒤 | `사실일까요?;;항공사는...` |
| 2 | "첫 번째/두 번째" 앞 | 나열 구조 |
| 3 | 콜론(:) 뒤 (15자 이상) | `합치면:;;dΠ/dp = ...` |
| 4 | 완전한 절 경계 | 주어+서술 완결 후 |
| 5 | 목적어 조사 앞 | `시나리오의;;기대값을...` |

### 길이 가이드

| 구분 | 길이 |
|------|------|
| 최대 | 35자 (초과 시 분할 검토) |
| 목표 | 15~30자 |
| 최소 | 10자 |

### 예시

```json
{
  "narration_display": "\"쿠키 삭제하면 싸진다\"는 말, 사실일까요? 항공사는 당신의 지갑 속을 들여다보고 있습니다.",
  "subtitle_display": "\"쿠키 삭제하면 싸진다\"는 말, 사실일까요?;;항공사는 당신의 지갑 속을 들여다보고 있습니다."
}
```

---

## semantic_goal 작성법

**핵심 질문:** "이 씬이 왜 필요한가?"

| ✅ 좋은 예 | ❌ 나쁜 예 |
|-----------|-----------|
| 호기심 유발 - 제곱근을 질문으로 재정의 | 수식 보여주기 |
| 용량 감소를 시각적으로 대비시켜 충격 주기 | 다음 씬으로 넘어가기 |
| 인수분해 과정을 단계별로 보여주기 | 애니메이션 |

---

## required_elements 타입별 형식

| type | 형식 | 비고 |
|------|------|------|
| math | `{"type": "math", "content": "x^2", "role": "수식"}` | LaTeX |
| text | `{"type": "text", "content": "제목", "role": "역할"}` | |
| image | `{"type": "image", "asset": "stickman_thinking", "role": "역할"}` | 확장자 없이 |
| graph | `{"type": "graph", "function": "x^2", "role": "역할"}` | |
| shape | `{"type": "shape", "shape": "circle", "role": "역할"}` | |
| arrow | `{"type": "arrow", "role": "연결선"}` | Manim Arrow |
| icon | `{"type": "icon", "asset": "arrow_right", "role": "역할"}` | SVG 에셋 |
| 3d_object | `{"type": "3d_object", "shape": "cube", "role": "역할"}` | |

### 🔴 아이콘은 반드시 별도 요소로 분리

```json
// ✅ 올바름 - 화살표 별도
{"type": "text", "content": "30만원", "role": "이전"},
{"type": "icon", "asset": "arrow_right", "role": "변화"},
{"type": "text", "content": "35만원", "role": "현재"}

// ❌ 잘못됨 - 텍스트에 포함
{"type": "text", "content": "30만원 → 35만원", "role": "변동"}
```

### 사용 가능한 아이콘 에셋

| asset | 용도 |
|-------|------|
| `arrow_right/left/up/down` | 방향 화살표 |
| `arrow_diagonal_up/down` | 대각선 화살표 |
| `arrow_bidirectional` | 양방향 화살표 |
| `question_mark` | 물음표 |
| `exclamation_mark` | 느낌표 |
| `checkmark` / `crossmark` | 체크/X 표시 |

---

## wow_moment & emotion_flow

### wow_moment

```json
"wow_moment": "복잡한 수식이 깔끔하게 정리되는 순간"
"wow_moment": null  // 없으면 null
```

**배치 원칙**: 30초당 최소 1개, Hook에 반드시 1개

### emotion_flow

```json
"emotion_flow": "호기심 → 흥미"
"emotion_flow": "복잡함 → 실마리 → 해결"
"emotion_flow": "집중"  // 변화 없이 유지
```

---

## required_assets 작성법

```json
"required_assets": [
  {
    "category": "characters",
    "filename": "stickman_confused",
    "description": "혼란스러운 표정의 졸라맨",
    "usage": "화면 왼쪽에 배치"
  }
]
```

| 필드 | 설명 |
|------|------|
| category | characters / objects / icons |
| filename | 파일명 (**확장자 제외**) |
| description | 에셋 설명 |
| usage | 사용 용도 |

---

## 씬 분할 원칙

### 분할 기준 (우선순위)

| 순위 | 기준 | 예시 |
|------|------|------|
| 1 | 주제/개념 전환 | "이제 그래프를 그려보겠습니다" |
| 2 | 새 수학 객체 등장 | 수식 첫 등장, 그래프 생성 |
| 3 | 음성 호흡 (20단어+) | 명확한 단락 전환 |
| 4 | Wow 모멘트 배치 | 충분한 시간 확보 |

### 분할 금지

| 금지 | 이유 |
|------|------|
| 수식 변환 과정 쪼개기 | 연속성 깨짐 |
| 캐릭터 감정만으로 분리 | Visual Prompter가 처리 |
| 단순 설명 구간 분리 | 하나로 유지 |

### 🔴 씬 간 나레이션 중복 금지

> 한 문장은 하나의 씬에만 포함. 연속된 두 씬이 같은 문장으로 끝/시작하면 TTS 중복.

```json
// ❌ s40 끝: "러너 지수입니다" / s41 시작: "러너 지수입니다" → 중복!
// ✅ s41은 새로운 내용으로 시작
```

### 🔴 등식 좌변/우변 분할 금지

> `A = B` 등식을 "왼쪽 설명" / "오른쪽 설명"으로 별도 씬 분리 금지

**올바른 방법**: 하나의 씬에서 부분 강조 (highlight 타입 사용)

```json
{
  "required_elements": [
    {"type": "math", "content": "\\frac{p-MC}{p} = \\frac{1}{E_d}", "role": "전체 공식"},
    {"type": "highlight", "target": "좌변", "timing": "first_half"},
    {"type": "highlight", "target": "우변", "timing": "second_half"}
  ]
}
```

### 긴 수식 씬 분할 규칙

| 씬 길이 | 조치 |
|---------|------|
| 20초 이하 | 유지 |
| 25초 이상 | 분할 권장 |
| 35초 이상 | 분할 필수 |

### 섹션 전환 브릿지

주제 급변 시 연결 문구 삽입:
- "이론은 알겠는데, 현실에선 어떨까요?"
- "하지만 현실은 이렇게 단순하지 않습니다."
- "여기서 한 가지 의문이 생깁니다."

---

## 수학 표기 명확화

절댓값, 부호 등 혼란 가능한 표기는 TTS에 설명 포함:

| 표기 | TTS 설명 |
|------|----------|
| `\|E_d\|` | "수요곡선 우하향 → 음수 → 절댓값으로 양수화" |
| `dP/dQ < 0` | "가격 올리면 수요 줄어드니까 음수" |
| `λ (람다)` | "제약 완화 시 추가 이윤, 그림자 가격" |

---

## 씬 길이 가이드

| 구분 | 시간 |
|------|------|
| 최소 | 5초 |
| 최적 | 10~20초 |
| 최대 | 30초 |

### 섹션별 가이드

| 섹션 | 권장 씬 수 | 평균 길이 |
|------|-----------|----------|
| Hook | 1~2개 | 5~10초 |
| 분석 | 2~4개 | 10~15초 |
| 핵심수학 | 3~6개 | 15~20초 |
| 적용 | 1~3개 | 10~15초 |
| 아웃트로 | 1개 | 5~10초 |

---

## 3D 씬 판단

| 키워드 | is_3d | scene_class |
|--------|-------|-------------|
| 정육면체, 큐브, 상자 | true | ThreeDScene |
| 원기둥, 캔, 병 | true | ThreeDScene |
| 구, 공, 지구본 | true | ThreeDScene |
| 원뿔, 고깔 | true | ThreeDScene |
| 부피, cm³, 세제곱 | true | ThreeDScene |
| 사각형, 원, 삼각형 | false | Scene |
| 그래프, 좌표 | false | Scene |

---

## PNG vs Manim 판단

| 구분 | Manim | PNG 에셋 |
|------|-------|----------|
| 수식, 그래프, 기본도형 | ✅ | - |
| 화살표, 선, 점 | ✅ | - |
| **캐릭터 (사람)** | ❌ | `stickman_*.png` |
| **실물 물체** | ❌ | `snack_bag.png` |
| **복잡한 아이콘** | ❌ | `question_mark.png` |
| **동물, 건물, 음식** | ❌ | PNG 사용 |

---

## 에셋 카탈로그

### 캐릭터 (assets/characters/)

| 파일명 | 설명 | 키워드 |
|--------|------|--------|
| `stickman_neutral` | 기본 자세 | 일반, 설명 |
| `stickman_thinking` | 생각하는 포즈 | 고민, 왜 |
| `stickman_surprised` | 놀란 표정 | 충격, 반전 |
| `stickman_happy` | 기쁜 표정 | 정답, 성공 |
| `stickman_confused` | 혼란 표정 | 의문, 이상함 |
| `stickman_pointing` | 가리키는 포즈 | 주목, 강조 |
| `stickman_sad` | 슬픈 표정 | 손해, 실패 |

### 물체 (assets/objects/)

| 파일명 | 설명 |
|--------|------|
| `snack_bag_normal` | 일반 과자봉지 |
| `snack_bag_shrunk` | 줄어든 과자봉지 |
| `money` | 돈/지폐 |
| `cart` | 쇼핑카트 |
| `calculator` | 계산기 |

### 아이콘 (assets/icons/)

| 파일명 | 설명 |
|--------|------|
| `question_mark` | 물음표 |
| `exclamation` | 느낌표 |
| `lightbulb` | 전구 (아이디어) |
| `arrow_right` | 오른쪽 화살표 |
| `checkmark` | 체크마크 |
| `clock` | 시계 |

---

## 스타일 설정

| 스타일 | 배경 | text_color_mode |
|--------|------|-----------------|
| minimal | #000000 (어두운) | light |
| cyberpunk | #0a0a1a (어두운) | light |
| space | #000011 (어두운) | light |
| geometric | #1a1a1a (어두운) | light |
| stickman | #1a2a3a (어두운) | light |
| **paper** | #f5f5dc (밝은) | **dark** |

---

## 복잡한 수식 TTS 처리

| 등급 | 기준 | TTS 처리 |
|------|------|----------|
| A (간단) | 변수 2개, 연산 1개 | 음성으로 읽기 |
| B (중간) | 변수 3-4개, 연산 2-3개 | 의미 해설로 대체 |
| C (복잡) | 분수/미분/다단계 | 화면 집중 + 해설 |

### A등급 예시
```json
"narration_tts": "총수입 티알은, 가격 피 곱하기 판매량 큐입니다."
```

### B등급 예시 (의미 해설)
```json
"narration_tts": "탄력성 이디는, 가격 변화율 대비 판매량 변화율의 비율입니다."
```

### C등급 예시 (화면 집중)
```json
"narration_tts": "오른쪽 항에서 피를 묶어내면, 괄호 안에 흥미로운 구조가 나타납니다. 보이시나요?"
```

### 화면 집중 유도 문장 템플릿

| 용도 | 문장 |
|------|------|
| 집중 | "화면을 주목해주세요." |
| 전환 | "자, 여기서 흥미로운 일이 벌어집니다." |
| 발견 | "보이시나요? 숨어있던 패턴이 드러납니다." |
| 감탄 | "놀랍죠?" / "바로 이겁니다." |

---

## 금지 사항 요약

| 항목 | ❌ 금지 | ✅ 올바름 |
|------|--------|----------|
| semantic_goal | "수식 보여주기" | "인수분해 과정 단계별 시각화" |
| required_elements | 빈 배열 `[]` | 최소 1개 요소 |
| role | 누락 | 반드시 포함 |
| 3D 객체 | `is_3d: false` | `is_3d: true, scene_class: ThreeDScene` |
| narration_display | 한글 발음 | 숫자/기호 형식 |
| narration_tts | 숫자/기호 | 한글 발음 |
| narration_tts | 마침표(.) | 줄임표(...) |
| 좌표 지정 | `"x": -2.5` | Visual Prompter 담당 |
| 애니메이션 | `"type": "FadeIn"` | Visual Prompter 담당 |

---

## 체크리스트

### 기본
- [ ] 모든 씬에 고유한 scene_id (s1, s2...)
- [ ] duration이 5~30초 범위
- [ ] narration_display는 숫자/기호, narration_tts는 한글 발음

### 의미 구조
- [ ] semantic_goal이 "왜 이 씬이 필요한가"에 답함
- [ ] required_elements가 최소 1개, role 포함
- [ ] 30초당 최소 1개 wow_moment

### 3D/에셋
- [ ] 3D 키워드 씬에 is_3d: true, scene_class: ThreeDScene
- [ ] 캐릭터/물체 씬에 required_assets 포함

---

## 전체 예시

### 예시 1: 순수 수학 씬 (에셋 불필요)

```json
{
  "scene_id": "s4",
  "section": "핵심수학",
  "duration": 18,
  "narration_display": "x² + 2x + 1을 인수분해하면 (x+1)²이 됩니다.",
  "subtitle_display": "x² + 2x + 1을 인수분해하면;;(x+1)²이 됩니다.",
  "narration_tts": "엑스 제곱 더하기 이 엑스 더하기 일을, 인수분해하면, 엑스 더하기 일의 제곱이 됩니다.",

  "semantic_goal": "완전제곱식 인수분해 과정 시각화",
  "required_elements": [
    { "type": "math", "content": "x^2 + 2x + 1", "role": "원본 수식" },
    { "type": "math", "content": "(x+1)^2", "role": "인수분해 결과" }
  ],
  "wow_moment": "복잡한 식이 깔끔하게 정리되는 순간",
  "emotion_flow": "복잡함 → 깔끔함",

  "style": "minimal",
  "is_3d": false,
  "scene_class": "Scene",
  "required_assets": []
}
```

### 예시 2: 캐릭터 + 수식 혼합 씬

```json
{
  "scene_id": "s2",
  "section": "분석",
  "duration": 15,
  "narration_display": "마트에서 익숙한 과자를 집어들었는데, 뭔가 이상합니다.",
  "subtitle_display": "마트에서 익숙한 과자를 집어들었는데,;;뭔가 이상합니다.",
  "narration_tts": "마트에서, 익숙한 과자를 집어들었는데, 뭔가 이상합니다...",

  "semantic_goal": "일상에서 발견한 이상함으로 호기심 유발",
  "required_elements": [
    { "type": "image", "asset": "stickman_confused", "role": "혼란스러운 소비자" },
    { "type": "image", "asset": "snack_bag_normal", "role": "과자봉지" }
  ],
  "wow_moment": null,
  "emotion_flow": "평범 → 의아함",

  "style": "stickman",
  "is_3d": false,
  "scene_class": "Scene",
  "required_assets": [
    {
      "category": "characters",
      "filename": "stickman_confused",
      "description": "혼란스러운 표정의 졸라맨",
      "usage": "화면 왼쪽에 배치"
    },
    {
      "category": "objects",
      "filename": "snack_bag_normal",
      "description": "일반 크기 과자봉지",
      "usage": "캐릭터 오른쪽에 배치"
    }
  ]
}
```

### 예시 3: Before-After 비교 씬

```json
{
  "scene_id": "s3",
  "section": "핵심수학",
  "duration": 20,
  "narration_display": "가격은 그대로인데, 용량이 줄었습니다. 100g → 80g",
  "subtitle_display": "가격은 그대로인데, 용량이 줄었습니다.;;100g → 80g",
  "narration_tts": "가격은 그대로인데, 용량이 줄었습니다. 백 그램에서, 팔십 그램으로.",

  "semantic_goal": "용량 감소를 시각적으로 대비시켜 충격 주기",
  "required_elements": [
    { "type": "image", "asset": "snack_bag_normal", "role": "비교 대상 A (Before)" },
    { "type": "image", "asset": "snack_bag_shrunk", "role": "비교 대상 B (After)" },
    { "type": "math", "content": "100g \\rightarrow 80g", "role": "수치 변화" },
    { "type": "math", "content": "\\frac{80}{100} = 80\\%", "role": "비율 계산" }
  ],
  "wow_moment": "20% 감소가 수치로 드러나는 순간",
  "emotion_flow": "의아함 → 충격",

  "style": "stickman",
  "is_3d": false,
  "scene_class": "Scene",
  "required_assets": [
    {
      "category": "objects",
      "filename": "snack_bag_normal",
      "description": "일반 크기 과자봉지",
      "usage": "화면 왼쪽 (Before)"
    },
    {
      "category": "objects",
      "filename": "snack_bag_shrunk",
      "description": "줄어든 과자봉지",
      "usage": "화면 오른쪽 (After)"
    }
  ]
}
```

### 예시 4: 3D 씬

```json
{
  "scene_id": "s7",
  "section": "핵심수학",
  "duration": 22,
  "narration_display": "정육면체의 부피는 한 변의 길이를 세 번 곱한 것입니다. V = a³",
  "subtitle_display": "정육면체의 부피는;;한 변의 길이를 세 번 곱한 것입니다.;;V = a³",
  "narration_tts": "정육면체의 부피는, 한 변의 길이를 세 번 곱한 것입니다. 브이는, 에이의 세제곱.",

  "semantic_goal": "정육면체 부피 공식의 직관적 이해",
  "required_elements": [
    { "type": "text", "content": "정육면체의 부피", "role": "제목" },
    { "type": "3d_object", "shape": "cube", "role": "부피 계산 대상" },
    { "type": "math", "content": "V = a^3", "role": "부피 공식" },
    { "type": "math", "content": "V = 10^3 = 1000cm^3", "role": "계산 예시" }
  ],
  "wow_moment": "정육면체가 회전하며 부피 공식이 도출되는 순간",
  "emotion_flow": "호기심 → 이해 → 만족",

  "style": "minimal",
  "is_3d": true,
  "scene_class": "ThreeDScene",
  "required_assets": []
}
```

### 예시 5: 깨달음/결론 씬

```json
{
  "scene_id": "s8",
  "section": "적용",
  "duration": 12,
  "narration_display": "바로 이거야! 슈링크플레이션의 수학적 본질입니다.",
  "subtitle_display": "바로 이거야!;;슈링크플레이션의 수학적 본질입니다.",
  "narration_tts": "바로 이거야! 슈링크플레이션의, 수학적 본질입니다.",

  "semantic_goal": "핵심 개념 정리 및 깨달음 표현",
  "required_elements": [
    { "type": "image", "asset": "stickman_happy", "role": "깨달은 캐릭터" },
    { "type": "image", "asset": "lightbulb", "role": "아이디어 아이콘" },
    { "type": "text", "content": "슈링크플레이션", "role": "핵심 용어" }
  ],
  "wow_moment": "전구 아이콘이 빛나며 깨달음 표현",
  "emotion_flow": "이해 → 만족",

  "style": "stickman",
  "is_3d": false,
  "scene_class": "Scene",
  "required_assets": [
    {
      "category": "characters",
      "filename": "stickman_happy",
      "description": "기쁜 표정의 졸라맨",
      "usage": "화면 중앙"
    },
    {
      "category": "icons",
      "filename": "lightbulb",
      "description": "전구 아이콘",
      "usage": "캐릭터 머리 위"
    }
  ]
}
```

### 예시 6: 그래프 씬

```json
{
  "scene_id": "s5",
  "section": "핵심수학",
  "duration": 25,
  "narration_display": "이차함수 y = x²의 그래프를 그려봅시다.",
  "subtitle_display": "이차함수 y = x²의;;그래프를 그려봅시다.",
  "narration_tts": "이차함수, 와이는 엑스 제곱의, 그래프를 그려봅시다.",

  "semantic_goal": "이차함수 그래프의 형태와 특성 시각화",
  "required_elements": [
    { "type": "graph", "function": "x^2", "role": "이차함수 그래프" },
    { "type": "math", "content": "y = x^2", "role": "함수식" },
    { "type": "shape", "shape": "dot", "role": "특정 점 표시" },
    { "type": "math", "content": "(2, 4)", "role": "좌표 라벨" }
  ],
  "wow_moment": "그래프가 부드럽게 그려지는 순간",
  "emotion_flow": "집중 → 이해",

  "style": "minimal",
  "is_3d": false,
  "scene_class": "Scene",
  "required_assets": []
}
```

---

## 작업 흐름 요약

```
1. 입력 확인
   ├── 읽기용 대본
   ├── TTS용 대본
   └── 프로젝트 설정 (style, duration)

2. 씬 분할 작업
   ├── 대본을 씬으로 분할
   ├── semantic_goal 정의
   ├── required_elements 목록화
   ├── wow_moment 배치
   ├── is_3d 판단
   └── required_assets 생성

3. 출력
   └── output/{project_id}/2_scenes/scenes.json
```
