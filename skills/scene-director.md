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

> **에셋 설계는 Asset Designer가 담당** (Scene Director 완료 후 순차 실행)

### Scene Director가 하지 않는 것

❌ 구체적인 좌표/위치 지정, 애니메이션 타입 결정, 색상 배치, 타이밍 세부 설계 → Visual Prompter 담당

---

## 입출력

### 입력
- `1_script/reading_script.json` (읽기용 대본)
- `state.json` (프로젝트 설정: style, duration, aspect_ratio)

### 출력 (Sub-agents 체계)

> **3개 에이전트가 섹션별로 분담 처리**

| 에이전트 | 담당 섹션 | 출력 파일 |
|----------|----------|-----------|
| `scene-director-hook` | Hook + 분석 | `scenes_part1.json` |
| `scene-director-core` | 핵심수학 | `scenes_part2.json` |
| `scene-director-outro` | 적용 + 아웃트로 | `scenes_part3.json` |

병합 후 최종 출력:
- `output/{project_id}/2_scenes/scenes.json` (전체)
- `output/{project_id}/2_scenes/s1.json`, `s2.json`, ... (개별)

---

## JSON 출력 형식 (나레이션 3종 통합)

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
    "camera_settings": null
  }
]
```

> **참고**: `required_assets`는 Asset Designer가 후속 작성

---

## 필수 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `scene_id` | string | s1, s2, s3... |
| `section` | string | Hook/분석/핵심수학/적용/아웃트로 |
| `duration` | number | 예상 길이 (초) |
| `narration_display` | string | 대본 원문 그대로 복사 |
| `subtitle_display` | string | 자막용 (`;; `로 분할) |
| `narration_tts` | string | TTS 발음용 (한글 발음) |
| `semantic_goal` | string | 씬의 목적 |
| `required_elements` | array | 필요한 요소 목록 |
| `wow_moment` | string/null | 강조 포인트 |
| `emotion_flow` | string | 감정 흐름 |
| `style` | string | 프로젝트 스타일 |
| `is_3d` | boolean | 3D 씬 여부 |
| `scene_class` | string | Scene / ThreeDScene |
| `camera_settings` | object/null | 3D 씬 카메라 설정 (is_3d: true일 때 필수) |

---

## 나레이션 3종 (TTS는 대본에서 추출)

> **Scene Director는 TTS를 직접 생성하지 않습니다!**
> Script Writer가 대본 작성 시 `tts` 필드를 함께 작성합니다.
> Scene Director는 씬 분할에 맞게 배치만 합니다.

| 필드 | 용도 | 출처 |
|------|------|------|
| `narration_display` | 대본 원문 | 대본 `content`에서 해당 구간 추출 |
| `subtitle_display` | 자막 (30자 초과 시 `;;` 삽입) | narration_display를 분할 |
| `narration_tts` | TTS 발음 (마침표 금지) | **대본 `tts`에서 해당 구간 추출** |

### narration_display

> **대본 `content`에서 해당 구간을 그대로 복사합니다.**

### narration_tts

> ⚠️ **직접 생성 금지!** 대본의 `tts` 필드에서 해당 구간을 추출하여 배치합니다.
> Script Writer가 이미 숫자/기호를 한글 발음으로 변환해 두었습니다.

### ⚠️ 씬 경계 Pause 규칙 (Script Writer가 이미 삽입)

> **`...` (줄임표)는 Script Writer가 `reading_script.json`의 `tts` 필드에 이미 삽입해 두었습니다.**
> **Scene Director는 줄임표를 추가하거나 수정하지 않고, 그대로 추출하여 배치만 합니다.**

**예시 (reading_script.json의 tts):**
```
"여러분, 루트 구가 뭔지 아시나요... 사실 이건, 숫자가 아니라 질문입니다..."
```

**Scene Director가 씬 분할 시:**
```json
// s1
{"narration_tts": "여러분, 루트 구가 뭔지 아시나요..."}

// s2
{"narration_tts": "사실 이건, 숫자가 아니라 질문입니다..."}
```

> `...`는 문장 끝에 이미 있으므로, 씬의 `narration_tts`도 자연스럽게 `...`로 끝납니다.

> ⚠️ **[pause] 태그 사용 금지** - OpenAI TTS가 지원하지 않아 텍스트로 읽어버림

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
| **highlight** | `{"type": "highlight", "target": "좌변", "role": "강조"}` | **수식 부분 강조** |

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

### 🔴 핵심 등식 연속성 유지 (매우 중요!)

> **한번 등장한 핵심 등식은 이후 씬에서도 계속 화면에 유지해야 함**
> 좌변/우변을 설명할 때 식을 분리하지 말고, 전체 등식을 유지하면서 부분 강조

#### ❌ 잘못된 예 (식 분리)

나레이션: "왼쪽을 볼까요? ... 오른쪽은?"

```json
// s55: 등식 완성
{"type": "math", "content": "\\frac{p-MC}{p} = \\frac{1}{E_d}", "role": "러너 지수"}

// s57: ❌ 좌변만 표시 (등식이 사라짐!)
{"type": "math", "content": "\\frac{p-MC}{p}", "role": "마크업 비율"}

// s58: ❌ 우변만 표시 (등식이 사라짐!)
{"type": "math", "content": "\\frac{1}{E_d}", "role": "탄력성 역수"}
```

**문제점**: 시청자가 전체 등식을 잊어버림, 좌우 관계가 끊어짐

#### ✅ 올바른 예 (등식 유지 + 부분 강조)

```json
// s55: 등식 완성
{
  "required_elements": [
    {"type": "math", "content": "\\frac{p-MC}{p} = \\frac{1}{E_d}", "role": "러너 지수"}
  ],
  "wow_moment": "러너 지수가 완성되는 순간"
}

// s56: 등식 위에 이름 표시
{
  "required_elements": [
    {"type": "math", "content": "\\frac{p-MC}{p} = \\frac{1}{E_d}", "role": "러너 지수"},
    {"type": "text", "content": "Lerner Index", "role": "식 이름 (등식 위에)"}
  ]
}

// s57: 전체 등식 유지 + 좌변 강조
{
  "required_elements": [
    {"type": "math", "content": "\\frac{p-MC}{p} = \\frac{1}{E_d}", "role": "러너 지수 전체"},
    {"type": "highlight", "target": "좌변", "role": "마크업 비율 강조"},
    {"type": "text", "content": "기업의 배짱", "role": "좌변 해석 (좌변 아래)"}
  ]
}

// s58: 전체 등식 유지 + 우변 강조
{
  "required_elements": [
    {"type": "math", "content": "\\frac{p-MC}{p} = \\frac{1}{E_d}", "role": "러너 지수 전체"},
    {"type": "highlight", "target": "우변", "role": "탄력성 역수 강조"},
    {"type": "text", "content": "고객의 고집", "role": "우변 해석 (우변 아래)"}
  ]
}
```

**핵심 원칙**:
1. 등식이 완성되면 **이후 씬에서도 전체 등식 유지**
2. "왼쪽", "오른쪽" 설명 시 **highlight로 부분 강조** (식 분리 X)
3. 해석 텍스트는 **해당 부분 아래에 배치** (식 대체 X)

#### 식 유지가 필요한 상황

| 나레이션 패턴 | 식 유지? | 처리 방법 |
|--------------|----------|----------|
| "왼쪽/오른쪽을 볼까요" | ✅ 필수 | highlight로 부분 강조 |
| "예를 들어볼까요" | ✅ 필수 | 식은 상단 유지, 예시는 하단 |
| "이런 고객은 ~합니다" | ✅ 필수 | 식 + 개념 텍스트 함께 |
| "정리하면" | ✅ 필수 | 식 + 요약 텍스트 |
| (완전히 새 주제/새 식 도입) | ❌ | 새 식으로 전환 |

#### 예시 설명 패턴 (식 유지 필수)

```json
// s13: 탄력성 식 정의
{
  "required_elements": [
    {"type": "math", "content": "E_d = \\frac{|\\%\\Delta Q|}{|\\%\\Delta P|}", "role": "탄력성 식"}
  ]
}

// s14: "예를 들어볼까요?" - 식 유지!
{
  "required_elements": [
    {"type": "math", "content": "E_d = \\frac{|\\%\\Delta Q|}{|\\%\\Delta P|}", "role": "탄력성 식 (상단 유지)"},
    {"type": "text", "content": "예시", "role": "섹션 전환"}
  ]
}

// s15: 출장객 예시 - 식 유지!
{
  "required_elements": [
    {"type": "math", "content": "E_d = \\frac{|\\%\\Delta Q|}{|\\%\\Delta P|}", "role": "탄력성 식 (상단 유지)"},
    {"type": "text", "content": "출장객", "role": "예시 캐릭터"},
    {"type": "text", "content": "+10% → 구매", "role": "행동 패턴"}
  ]
}

// s16: 개념 정리 - 식 유지!
{
  "required_elements": [
    {"type": "math", "content": "E_d = \\frac{|\\%\\Delta Q|}{|\\%\\Delta P|}", "role": "탄력성 식 (상단 유지)"},
    {"type": "text", "content": "탄력성 낮음 = 가격 둔감", "role": "개념 정리"}
  ]
}
```

> **Visual Prompter 처리**: role에 "(상단 유지)"가 있으면 식을 화면 상단에 고정 배치

#### highlight 타입 사용법

```json
{"type": "highlight", "target": "좌변", "role": "강조할 부분"}
{"type": "highlight", "target": "우변", "role": "강조할 부분"}
{"type": "highlight", "target": "등호", "role": "등호 강조"}
```

> Visual Prompter가 highlight를 박스/색상 변경/글로우 등으로 구현

### 긴 수식 씬 분할 규칙

| 씬 길이 | 조치 |
|---------|------|
| 20초 이하 | 유지 |
| 35초 이상 | 분할 권장 |
| 40초 이상 | 분할 필수 |

### 섹션 전환 브릿지

주제 급변 시 연결 문구 삽입:
- "이론은 알겠는데, 현실에선 어떨까요?"
- "하지만 현실은 이렇게 단순하지 않습니다."
- "여기서 한 가지 의문이 생깁니다."

---



### 🔴 영상 길이별 총 씬 수 가이드

> **이 가이드를 반드시 준수하세요!** 씬이 너무 많으면 영상이 산만해집니다.

| 영상 길이 | 권장 씬 수 | 평균 씬 길이 |
|-----------|-----------|-------------|
| 2분 (120초) | **8~10개** | 12~15초 |
| 5분 (300초) | **20~25개** | 12~15초 |
| 8분 (480초) | **30~35개** | 13~16초 |
| 10분 (600초) | **40~50개** | 12~15초 |
| 15분 (900초) | **55~70개** | 13~16초 |
| 20분 (1200초) | **75~90개** | 13~16초 |

### 섹션별 비율 가이드

| 섹션 | 비율 | 10분 영상 기준 |
|------|------|---------------|
| Hook | 5% | 2~3개 |
| 분석 | 20% | 8~10개 |
| 핵심수학 | 45% | 18~22개 |
| 적용 | 25% | 10~12개 |
| 아웃트로 | 5% | 2~3개 |

---

## 3D 씬 판단

### 3D 키워드표

| 키워드 | is_3d | scene_class |
|--------|-------|-------------|
| 정육면체, 큐브, 상자 | true | ThreeDScene |
| 원기둥, 캔, 병 | true | ThreeDScene |
| 구, 공, 지구본 | true | ThreeDScene |
| 원뿔, 고깔 | true | ThreeDScene |
| 부피, cm³, 세제곱 | true | ThreeDScene |
| **3D, 입체, 회전** | true | ThreeDScene |
| **표면적, 전개도** | true | ThreeDScene |
| 사각형, 원, 삼각형 | false | Scene |
| 그래프, 좌표 | false | Scene |

### 판단 흐름도

```
대본 키워드 분석
    ↓
"정육면체/큐브/상자" → is_3d: true, shape: "cube"
"원기둥/캔/병" → is_3d: true, shape: "cylinder"
"구/공" → is_3d: true, shape: "sphere"
"3D/입체/회전" → is_3d: true
"표면적/전개도" → is_3d: true
"부피/cm³" → 맥락상 3D 여부 확인
    ↓ (3D 키워드 없으면)
is_3d: false, scene_class: "Scene"
```

### camera_settings (Visual Prompter 담당)

> ⚠️ **역할 분리**: Scene Director는 `is_3d` 판단만, `camera_settings`는 **Visual Prompter가 채웁니다.**

**Scene Director 출력:**
```json
{
  "is_3d": true,
  "scene_class": "ThreeDScene",
  "camera_settings": null
}
```

**Visual Prompter가 채운 후:**
```json
{
  "is_3d": true,
  "scene_class": "ThreeDScene",
  "camera_settings": {
    "phi": 75,
    "theta": -30,
    "zoom": 0.8,
    "movement": "rotate"
  }
}
```

> 참고: camera_settings 상세 규칙은 `skills/visual-prompter-layout.md` 참조

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

## 금지 사항 요약

| 항목 | 금지 | 올바름 |
|------|------|--------|
| semantic_goal | "수식 보여주기" | "인수분해 과정 단계별 시각화" |
| required_elements | 빈 배열 `[]` | 최소 1개 요소 |
| role | 누락 | 반드시 포함 |
| 3D 객체 | `is_3d: false` | `is_3d: true, scene_class: ThreeDScene` |
| 좌표 지정 | `"x": -2.5` | Visual Prompter 담당 |
| 애니메이션 | `"type": "FadeIn"` | Visual Prompter 담당 |

---

## 체크리스트

### 기본
- [ ] 모든 씬에 고유한 scene_id (s1, s2...)
- [ ] duration이 5~30초 범위
- [ ] narration_display가 대본 원문과 일치

### 의미 구조
- [ ] semantic_goal이 "왜 이 씬이 필요한가"에 답함
- [ ] required_elements가 최소 1개, role 포함
- [ ] 30초당 최소 1개 wow_moment

### 3D/에셋
- [ ] 3D 키워드 씬에 is_3d: true, scene_class: ThreeDScene
- [ ] **3D 씬에 camera_settings 포함** (없으면 평면처럼 보임!)

---

## 전체 예시

### 예시 1: 순수 수학 씬 (에셋 불필요)

```json
{
  "scene_id": "s4",
  "section": "핵심수학",
  "duration": 18,
  "narration_display": "x² + 2x + 1을 인수분해하면 (x+1)²이 됩니다.",
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
  "camera_settings": null
}
```

> **참고**: `required_assets`는 Asset Designer가 후속 작성

### 예시 2: 캐릭터 + 수식 혼합 씬

```json
{
  "scene_id": "s2",
  "section": "분석",
  "duration": 15,
  "narration_display": "마트에서 익숙한 과자를 집어들었는데, 뭔가 이상합니다.",
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
  "camera_settings": null
}
```

### 예시 3: Before-After 비교 씬

```json
{
  "scene_id": "s3",
  "section": "핵심수학",
  "duration": 20,
  "narration_display": "가격은 그대로인데, 용량이 줄었습니다. 100g → 80g",
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
  "camera_settings": null
}
```

### 예시 4: 3D 씬

```json
{
  "scene_id": "s7",
  "section": "핵심수학",
  "duration": 22,
  "narration_display": "정육면체의 부피는 한 변의 길이를 세 번 곱한 것입니다. V = a³",
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
  "camera_settings": {
    "phi": 75,
    "theta": -45,
    "zoom": 0.8,
    "movement": "rotate"
  }
}
```

> ⚠️ **3D 씬 필수**: `camera_settings`가 없으면 평면처럼 보입니다!

### 예시 5: 깨달음/결론 씬

```json
{
  "scene_id": "s8",
  "section": "적용",
  "duration": 12,
  "narration_display": "바로 이거야! 슈링크플레이션의 수학적 본질입니다.",
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
  "camera_settings": null
}
```

### 예시 6: 그래프 씬

```json
{
  "scene_id": "s5",
  "section": "핵심수학",
  "duration": 25,
  "narration_display": "이차함수 y = x²의 그래프를 그려봅시다.",
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
  "camera_settings": null
}
```

---

## 작업 흐름 요약 (Sub-agents 체계)

```
1. 입력 확인
   ├── 읽기용 대본 (reading_script.json)
   │   ├── content: 읽기용 원문
   │   └── tts: TTS 발음 (Script Writer가 작성)
   └── 프로젝트 설정 (style, duration)

2. 씬 분할 작업 (3개 에이전트가 섹션별 분담)
   ├── 대본을 씬으로 분할
   ├── 나레이션 3종 배치:
   │   ├── narration_display (대본 content에서 추출)
   │   ├── subtitle_display (;; 삽입)
   │   └── narration_tts (대본 tts에서 추출 - 직접 생성 X!)
   ├── semantic_goal 정의
   ├── required_elements 목록화
   ├── wow_moment 배치
   └── is_3d 판단

3. 출력
   ├── scenes_part1.json (Hook + 분석)
   ├── scenes_part2.json (핵심수학)
   └── scenes_part3.json (적용 + 아웃트로)

4. 병합 (python math_video_pipeline.py merge-scenes)
   ├── scenes.json (전체)
   └── s1.json, s2.json, ... (개별)
```

> ⚠️ **TTS 직접 생성 금지!** Script Writer가 작성한 `tts` 필드를 씬 분할에 맞게 배치만 함
