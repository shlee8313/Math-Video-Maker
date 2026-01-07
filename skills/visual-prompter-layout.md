# Visual Prompter - Layout Stage

> **역할**: Scene Director의 semantic_goal을 구체적인 객체 배치로 변환
> **입력**: scenes.json, required_elements
> **출력**: s{n}_layout.json (objects 정의만)

---

## 1. 화면 세이프존

```
화면 전체: 14.2 x 8 units (16:9 기준)
Manim 좌표: 중앙 = (0,0)
            좌상단 ≈ (-7.1, 4)
            우하단 ≈ (7.1, -4)

세이프존 (safe_margin: 0.5):
    실제 사용 영역: x: -6.6 ~ 6.6, y: -3.5 ~ 3.5

화면 분할:
    상단 (UP): y = 2.5 ~ 3.5 (타이틀, 섹션명)
    중앙 (CENTER): y = -1.5 ~ 1.5 (메인 콘텐츠)
    하단 (DOWN): y = -2.5 ~ -3.5 (자막 영역 - 비워둘 것)
```

### 세이프존 경고

```
❌ y > 3.5 또는 y < -3.5 → 화면 밖 잘림
❌ x > 6.6 또는 x < -6.6 → 화면 밖 잘림
❌ y < -2.5 → 자막과 겹침
```

---

## 2. 객체 타입별 명세

### 2.1 ImageMobject (PNG 에셋)

```json
{
  "id": "stickman",
  "type": "ImageMobject",
  "source": "assets/characters/stickman_confused.png",
  "size": {
    "height": 4.0,
    "note": "STICKMAN_HEIGHT 기준"
  },
  "position": {
    "method": "shift",
    "x": -3,
    "y": 0,
    "note": "왼쪽 중앙"
  },
  "z_index": 1
}
```

**필수 필드**: id, type, source, size, position

### 2.2 SVGMobject (아이콘)

```json
{
  "id": "algorithm_icon",
  "type": "SVGMobject",
  "source": "assets/icons/algorithm_icon.svg",
  "size": {
    "height": 1.5,
    "note": "아이콘 크기"
  },
  "color": "YELLOW",
  "position": {
    "method": "shift",
    "x": 0,
    "y": 0
  },
  "z_index": 2
}
```

#### 🔴 화살표/물음표는 반드시 SVG 사용 (텍스트 금지!)

화살표(→←↑↓↗↘↔)와 물음표(?)는 Text/MathTex로 사용하면 예쁘지 않습니다.
반드시 SVG 에셋을 사용하세요.

**❌ 잘못된 정의:**
```json
{
  "id": "arrow",
  "type": "MathTex",
  "content": "\\rightarrow"
}
```

**✅ 올바른 정의:**
```json
{
  "id": "arrow_right",
  "type": "SVGMobject",
  "source": "assets/icons/arrow_right.svg",
  "size": {"height": 0.8},
  "color": "WHITE",
  "position": {"method": "shift", "x": 0, "y": 0}
}
```

**사용 가능한 화살표 SVG:**

| 파일명 | 용도 |
|--------|------|
| `arrow_right.svg` | 오른쪽 화살표 → |
| `arrow_left.svg` | 왼쪽 화살표 ← |
| `arrow_up.svg` | 위쪽 화살표 ↑ |
| `arrow_down.svg` | 아래쪽 화살표 ↓ |
| `arrow_diagonal_down.svg` | 좌→우 하향 대각선 ↘ |
| `arrow_diagonal_up.svg` | 좌→우 상향 대각선 ↗ |
| `arrow_bidirectional.svg` | 양방향 화살표 ↔ |
| `arrow_vertical_bidirectional.svg` | 수직 양방향 화살표 ↕ |

**기호 SVG:**

| 파일명 | 용도 |
|--------|------|
| `question_mark.svg` | 물음표 ? |
| `exclamation_mark.svg` | 느낌표 ! |

**체크/상태 SVG:**

| 파일명 | 용도 |
|--------|------|
| `checkmark.svg` | 체크마크 ✓ (정답, 완료) |
| `crossmark.svg` | 엑스마크 ✗ (오답, 금지) |
| `circle_empty.svg` | 빈 원 ○ (미선택) |
| `circle_filled.svg` | 채워진 원 ● (선택됨) |

**수학기호(강조용) SVG:**

| 파일명 | 용도 |
|--------|------|
| `infinity_emphasis.svg` | 무한대 ∞ |
| `approximately_emphasis.svg` | 근사 ≈ |
| `not_equal_emphasis.svg` | 같지 않음 ≠ |
| `less_equal_emphasis.svg` | 작거나 같음 ≤ |
| `greater_equal_emphasis.svg` | 크거나 같음 ≥ |

**강조 SVG:**

| 파일명 | 용도 |
|--------|------|
| `star_filled.svg` | 채워진 별 ★ (중요) |
| `star_empty.svg` | 빈 별 ☆ |
| `heart_filled.svg` | 채워진 하트 ♥ |
| `diamond_filled.svg` | 채워진 다이아몬드 ♦ |
| `lightning.svg` | 번개 ⚡ (빠름, 에너지) |
| `warning_triangle.svg` | 경고 삼각형 ⚠ (주의) |

> **예외**: Manim `Arrow` 클래스(두 점 연결용)는 사용 가능.
> 텍스트/수식 내 기호만 SVG 사용.

### 2.3 Text (한글 텍스트)

```json
{
  "id": "title_text",
  "type": "Text",
  "content": "동적 가격이란?",
  "font": "Noto Sans KR",
  "font_size": 56,
  "color": "WHITE",
  "position": {
    "method": "to_edge",
    "edge": "UP",
    "buff": 0.5
  },
  "z_index": 2
}
```

**주의**: 한글은 반드시 `font: "Noto Sans KR"` 필요

### 2.4 MathTex (수식)

```json
{
  "id": "elasticity_formula",
  "type": "MathTex",
  "content": "E_d = \\frac{\\%\\Delta Q}{\\%\\Delta P}",
  "font_size": 72,
  "color": "YELLOW",
  "position": {
    "method": "shift",
    "x": 0,
    "y": 0
  },
  "scale": 1.0,
  "z_index": 3
}
```

**주의**: LaTeX 백슬래시는 이중 이스케이프 (`\\frac` 등)

### 2.5 TextMathGroup (혼합 텍스트+수식)

```json
{
  "id": "mixed_group",
  "type": "TextMathGroup",
  "parts": [
    {"type": "Text", "content": "탄력성 ", "color": "WHITE"},
    {"type": "MathTex", "content": "E_d", "color": "YELLOW"},
    {"type": "Text", "content": " 는 다음과 같다", "color": "WHITE"}
  ],
  "arrangement": "horizontal",
  "position": {
    "method": "shift",
    "x": 0,
    "y": 1.5
  }
}
```

### 2.6 기본 도형

**Rectangle**
```json
{
  "id": "highlight_box",
  "type": "Rectangle",
  "width": 4,
  "height": 1.5,
  "color": "YELLOW",
  "fill_opacity": 0.2,
  "stroke_width": 2,
  "position": {"method": "shift", "x": 0, "y": 0}
}
```

**Circle**
```json
{
  "id": "focus_circle",
  "type": "Circle",
  "radius": 0.8,
  "color": "RED",
  "fill_opacity": 0,
  "stroke_width": 3
}
```

**Arrow**
```json
{
  "id": "direction_arrow",
  "type": "Arrow",
  "start": {"x": -2, "y": 0},
  "end": {"x": 2, "y": 0},
  "color": "GREEN",
  "stroke_width": 4
}
```

**Line**
```json
{
  "id": "separator",
  "type": "Line",
  "start": {"x": -3, "y": 0},
  "end": {"x": 3, "y": 0},
  "color": "GRAY_B",
  "stroke_width": 2
}
```

### 2.7 Axes (그래프) - 🔴 필수 요소 주의!

그래프를 정의할 때 **반드시** 아래 모든 요소를 포함해야 합니다:

```json
{
  "id": "axes",
  "type": "Axes",
  "x_range": [0, 10, 1],
  "y_range": [0, 5, 1],
  "x_length": 6,
  "y_length": 4,
  "position": {"method": "shift", "x": 0, "y": -0.5},
  "axis_config": {
    "color": "GRAY_B",
    "include_tip": true
  },
  "axis_labels": {
    "x": "Q",
    "y": "P",
    "font_size": 24
  }
}
```

#### 🔴 그래프 필수 체크리스트

| 항목 | 필수 | 설명 |
|------|------|------|
| **axis_labels** | ✅ | X축, Y축 레이블 (예: P, Q, x, y) |
| **curve_labels** | ✅ | 각 곡선 옆에 이름 (예: MR, MC, D, S) |
| **intersection_point** | ✅ | 곡선 교차점에 Dot 표시 |
| font_size | ✅ | 축/곡선 레이블은 20~24 (작게) |

#### 축 레이블 정의

```json
{
  "id": "y_axis_label",
  "type": "Text",
  "content": "P",
  "font": "Noto Sans KR",
  "font_size": 24,
  "color": "WHITE",
  "position": {
    "method": "next_to",
    "ref": "axes",
    "anchor": "y_axis_top",
    "direction": "UP",
    "buff": 0.1
  }
},
{
  "id": "x_axis_label",
  "type": "Text",
  "content": "Q",
  "font": "Noto Sans KR",
  "font_size": 24,
  "color": "WHITE",
  "position": {
    "method": "next_to",
    "ref": "axes",
    "anchor": "x_axis_right",
    "direction": "RIGHT",
    "buff": 0.1
  }
}
```

### 2.8 ParametricFunction (곡선) - 🔴 레이블 필수!

곡선을 정의할 때 **반드시 곡선 레이블도 함께** 정의:

```json
{
  "id": "mr_curve",
  "type": "ParametricFunction",
  "function": "mr_curve",
  "function_def": "-0.5*x + 8",
  "x_range": [0, 9],
  "axes_ref": "axes",
  "color": "GREEN",
  "stroke_width": 3,
  "note": "axes.plot() 사용"
},
{
  "id": "mr_label",
  "type": "Text",
  "content": "MR",
  "font": "Noto Sans KR",
  "font_size": 20,
  "color": "GREEN",
  "position": {
    "method": "next_to",
    "ref": "mr_curve",
    "anchor": "end",
    "direction": "UR",
    "buff": 0.1
  },
  "note": "곡선 끝점 근처에 배치"
}
```

### 2.9 Intersection Point (교차점) - 🔴 실제 좌표 계산 필수!

두 곡선이 만나는 점은 **반드시 실제 교차 좌표를 계산**해서 정의:

```json
{
  "id": "equilibrium_point",
  "type": "Dot",
  "position": {
    "method": "axes_coord",
    "axes_ref": "axes",
    "x": 5.6,
    "y": 5.2,
    "note": "MR=MC 교차점: -0.5*5.6+8 = 5.2"
  },
  "color": "YELLOW",
  "radius": 0.12
}
```

**❌ 잘못된 예시:**
```json
{
  "position": {"x": 3, "y": 2, "note": "대충 중간쯤"}
}
```

**✅ 올바른 예시:**
```json
{
  "position": {
    "x": 5.6,
    "y": 5.2,
    "note": "MR: -0.5x+8, MC: 0.1x²+2, 교차점 x=5.6"
  }
}
```

### 2.10 VGroup (객체 그룹)

```json
{
  "id": "example_group",
  "type": "VGroup",
  "children": ["icon1", "icon2", "icon3"],
  "arrangement": "horizontal",
  "spacing": 1.5,
  "position": {"method": "shift", "x": 0, "y": -1}
}
```

---

## 3. 3D 객체 (ThreeDScene 전용)

### 3D 씬 필수 설정

```json
{
  "scene_id": "s15",
  "is_3d": true,
  "scene_class": "ThreeDScene",
  "camera": {
    "phi": 60,
    "theta": -45,
    "frame_center": [0, 0, 0]
  }
}
```

### 3D 기본 객체

**Cube**
```json
{
  "id": "cube1",
  "type": "Cube",
  "side_length": 2,
  "fill_color": "BLUE",
  "fill_opacity": 0.7,
  "stroke_width": 2
}
```

**Sphere**
```json
{
  "id": "sphere1",
  "type": "Sphere",
  "radius": 1,
  "color": "GREEN"
}
```

**Cylinder**
```json
{
  "id": "cylinder1",
  "type": "Cylinder",
  "radius": 0.5,
  "height": 2,
  "color": "RED"
}
```

### 3D 씬 텍스트 처리

```json
{
  "id": "volume_formula",
  "type": "MathTex",
  "content": "V = a^3",
  "fixed_in_frame": true,
  "position": {
    "method": "to_corner",
    "corner": "UL",
    "buff": 0.5
  },
  "note": "3D 씬에서 텍스트는 fixed_in_frame 필수"
}
```

---

## 4. 위치 지정 규칙

### 4.1 절대 좌표 (shift)

```json
"position": {
  "method": "shift",
  "x": -3,
  "y": 1.5,
  "note": "왼쪽 상단"
}
```

**주요 좌표값**
| 위치 | x | y |
|------|---|---|
| 중앙 | 0 | 0 |
| 왼쪽 | -3 ~ -5 | 0 |
| 오른쪽 | 3 ~ 5 | 0 |
| 상단 | 0 | 2 ~ 3 |
| 하단 | 0 | -1 ~ -2 |

### 4.2 화면 가장자리 (to_edge)

```json
"position": {
  "method": "to_edge",
  "edge": "UP",
  "buff": 0.5
}
```

**edge 옵션**: UP, DOWN, LEFT, RIGHT

### 4.3 모서리 (to_corner)

```json
"position": {
  "method": "to_corner",
  "corner": "UL",
  "buff": 0.5
}
```

**corner 옵션**: UL, UR, DL, DR

### 4.4 상대 위치 (next_to)

```json
"position": {
  "method": "next_to",
  "reference": "stickman",
  "direction": "RIGHT",
  "buff": 0.5
}
```

**direction 옵션**: UP, DOWN, LEFT, RIGHT

### 4.5 다른 객체 위치 복사 (move_to)

```json
"position": {
  "method": "move_to",
  "reference": "target_object"
}
```

---

## 5. 크기 기준

### 캐릭터 크기

```
STICKMAN_HEIGHT = 4.0 (기준값)

캐릭터가 들고 있는 물체: STICKMAN_HEIGHT * 0.25~0.35
캐릭터 옆 물체: STICKMAN_HEIGHT * 0.40~0.60
독립 물체: STICKMAN_HEIGHT * 0.50~0.70
```

### 아이콘 크기

```
큰 아이콘: 1.5~2.0
중간 아이콘: 1.0~1.5
작은 아이콘: 0.5~1.0
```

### 텍스트 크기

```
타이틀: font_size 56~72
본문: font_size 40~48
라벨: font_size 28~36
주석: font_size 20~24
```

### 수식 크기

```
메인 수식: font_size 72, scale 1.0~1.2
보조 수식: font_size 48~56
인라인 수식: font_size 36~40
```

---

## 6. 색상 팔레트

### 기본 색상

| 용도 | 색상 | 코드 |
|------|------|------|
| 변수 | YELLOW | 변수, 강조 |
| 상수 | ORANGE | 숫자 상수 |
| 결과 | GREEN | 정답, 성공 |
| 경고 | RED | 오류, 강조 |
| 보조 | GRAY_B | 축, 보조선 |
| 기본 | WHITE | 일반 텍스트 |

### 스타일별 팔레트

**minimal (어두운 배경)**
```
배경: #000000
텍스트: WHITE, YELLOW
강조: GREEN, RED
```

**paper (밝은 배경)**
```
배경: #f5f5dc
텍스트: BLACK, DARK_BLUE
강조: DARK_GREEN, MAROON
```

---

## 7. z_index 가이드

```
z_index 1: 배경 요소, 보조 그래픽
z_index 2: 메인 콘텐츠 (텍스트, 이미지)
z_index 3: 강조 요소 (수식, 하이라이트)
z_index 4: 오버레이 (팝업, 전환 효과)
```

---

## 8. 레이아웃 패턴

### 패턴 1: 좌우 대비

```
왼쪽 (-3, 0): Before/문제/질문
오른쪽 (3, 0): After/해결/답
중앙 (0, 2): 타이틀
```

### 패턴 2: 중앙 집중

```
중앙 (0, 0): 메인 수식/핵심
상단 (0, 2.5): 제목
하단 (0, -1.5): 설명
```

### 패턴 3: 수직 흐름

```
상단 (0, 2): Step 1
중앙 (0, 0): Step 2
하단 (0, -2): Step 3
화살표로 연결
```

### 패턴 4: 그래프 중심

```
그래프 (0, -0.5): 중앙~약간 아래
y축 라벨 (LEFT): axes 옆
x축 라벨 (DOWN): axes 아래
결론 (0, 2.5): 상단
```

### 패턴 5: 캐릭터 + 말풍선

```
캐릭터 (-4, -1): 왼쪽 하단
말풍선 (-1, 1): 캐릭터 우상단
말풍선 꼬리: 캐릭터 방향
```

### 패턴 6: 3개 나열

```
왼쪽 (-4, 0): 항목 1
중앙 (0, 0): 항목 2
오른쪽 (4, 0): 항목 3
VGroup으로 묶어서 spacing 조절
```

---

## 9. 레이아웃 체크리스트

### 필수 확인

- [ ] 모든 객체에 고유한 id 있음
- [ ] 모든 객체에 type 지정됨
- [ ] 모든 객체에 position 있음
- [ ] 에셋 source 경로 올바름 (assets/...)
- [ ] 한글 Text에 font 지정됨
- [ ] 3D 씬에 camera 설정 있음
- [ ] 3D 텍스트에 fixed_in_frame 있음
- [ ] 화살표(→←↑↓↗↘↔)/물음표(?)는 SVGMobject 사용 (Text/MathTex 금지)

### 세이프존 확인

- [ ] x 좌표가 -6.6 ~ 6.6 범위
- [ ] y 좌표가 -2.5 ~ 3.5 범위 (자막 영역 제외)
- [ ] 큰 객체가 화면 밖으로 안 나감

### 크기 확인

- [ ] 캐릭터 높이 STICKMAN_HEIGHT (4.0) 사용
- [ ] 물체 크기가 캐릭터 대비 적절함
- [ ] 텍스트 크기가 가독성 있음

---

## 10. 출력 형식

### 파일 위치

```
output/{project_id}/3_visual_prompts/s{n}_layout.json
```

### 파일 구조

```json
{
  "scene_id": "s1",
  "is_3d": false,
  "scene_class": "Scene",
  "style": "minimal",
  "total_duration": 12.5,

  "canvas": {
    "background": "#000000",
    "safe_margin": 0.5
  },

  "objects": [
    {
      "id": "...",
      "type": "...",
      "...": "..."
    }
  ],

  "layout_notes": {
    "pattern": "좌우 대비",
    "focal_point": "result_text"
  }
}
```

**주의**: sequence는 Animation 단계에서 추가

---

## 작업 흐름

```
1. scenes.json에서 해당 씬 읽기
   - semantic_goal, required_elements, wow_moment

2. timing.json에서 total_duration 확인

3. 레이아웃 패턴 선택

4. objects 배열 작성
   - 모든 필요한 객체 정의
   - 위치, 크기, 색상 지정

5. s{n}_layout.json 저장

6. 다음 씬 처리
```
