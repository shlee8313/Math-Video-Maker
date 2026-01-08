# Manim Coder Reference

> **참고**: 이 파일은 `manim-coder.md`의 상세 참조 문서입니다.
> 핵심 규칙과 체크리스트는 `manim-coder.md`를 참조하세요.

---

## 객체 타입별 변환

### 1. ImageMobject (PNG 이미지)

**Visual Prompter JSON:**

```json
{
  "id": "stickman",
  "type": "ImageMobject",
  "source": "assets/characters/stickman_confused.png",
  "size": { "height": 4.0, "note": "STICKMAN_HEIGHT" },
  "position": { "method": "shift", "x": -3, "y": 0 }
}
```

**Manim 코드:**

```python
stickman = ImageMobject("assets/characters/stickman_confused.png")
stickman.set_height(4.0)
stickman.shift(LEFT * 3)
```

**변환 규칙:**

- `source` → ImageMobject 생성자 인자
- `size.height` → `set_height()` 메서드
- `position` → 위치 변환 규칙 적용 (아래 참조)

---

### 1.5. SVGMobject (SVG 이미지)

> **중요:** 아이콘은 SVG 또는 PNG일 수 있음. 확장자에 따라 다른 클래스 사용!

**Visual Prompter JSON:**

```json
{
  "id": "lightbulb",
  "type": "SVGMobject",
  "source": "assets/icons/lightbulb.svg",
  "size": { "height": 1.0, "note": "ICON_SIZE" },
  "position": { "method": "next_to", "anchor": "stickman", "direction": "UR", "buff": 0.2 }
}
```

**Manim 코드:**

```python
lightbulb = SVGMobject("assets/icons/lightbulb.svg")
lightbulb.set_height(1.0)
lightbulb.next_to(stickman, UR, buff=0.2)
```

**PNG vs SVG 분기 처리:**

| 확장자 | Manim 클래스   | 특징                        |
| ------ | -------------- | --------------------------- |
| `.png` | `ImageMobject` | 래스터 이미지, 색상 변경 X  |
| `.svg` | `SVGMobject`   | 벡터 이미지, 색상 변경 가능 |

**SVG 색상 변경 (옵션):**

```python
# SVG는 색상 변경 가능
icon = SVGMobject("assets/icons/lightbulb.svg")
icon.set_color(YELLOW)  # 전체 색상 변경
icon.set_fill(YELLOW, opacity=1)  # 채우기 색상
icon.set_stroke(WHITE, width=2)  # 외곽선
```

**🔴 스타일별 SVG 색상 (중요!):**

> SVG 파일은 기본 `#FFFFFF` (흰색). 밝은 배경에서는 반드시 변경!

| 스타일 | 배경 타입 | SVG 색상 |
|--------|-----------|----------|
| minimal | 어두움 | WHITE (기본값) |
| cyberpunk | 어두움 | WHITE, "#00FFFF" |
| space | 어두움 | WHITE |
| geometric | 어두움 | WHITE, GOLD |
| stickman | 어두움 | WHITE |
| **paper** | **밝음** | BLACK, "#00008B" ← 반드시 변경! |

```python
# paper 스타일에서 SVG 색상 변경 예시
arrow = SVGMobject("assets/icons/arrow_right.svg")
arrow.set_color(BLACK)  # 밝은 배경에서 보이도록 변경
```

**주의사항:**

```python
# ❌ 틀림 - PNG에 SVGMobject 사용
icon = SVGMobject("assets/icons/lightbulb.png")

# ❌ 틀림 - SVG에 ImageMobject 사용 (작동은 하지만 색상 변경 불가)
icon = ImageMobject("assets/icons/lightbulb.svg")

# ✅ 맞음 - 확장자에 맞는 클래스 사용
icon_png = ImageMobject("assets/icons/star.png")
icon_svg = SVGMobject("assets/icons/lightbulb.svg")
```

---

### 2. Text

**Visual Prompter JSON:**

```json
{
  "id": "title",
  "type": "Text",
  "content": "피타고라스 정리",
  "font": "Noto Sans KR",
  "font_size": 72,
  "color": "WHITE",
  "position": { "method": "to_edge", "edge": "UP", "buff": 0.5 },
  "background": { "color": "#000000", "opacity": 0.7, "buff": 0.2 }
}
```

**Manim 코드:**

```python
title = Text("피타고라스 정리", font="Noto Sans KR", font_size=72, color=WHITE)
title.to_edge(UP, buff=0.5)
title.add_background_rectangle(color=BLACK, opacity=0.7, buff=0.2)
```

**변환 규칙:**

- `content` → Text 첫 번째 인자
- `font` → 항상 `font="Noto Sans KR"` (필수!)
- `font_size` → `font_size=` 인자
- `color` → `color=` 인자 (색상 변환 규칙 적용)
- `background` → `add_background_rectangle()` 메서드

---

### 3. MathTex (단일 색상)

**Visual Prompter JSON:**

```json
{
  "id": "equation",
  "type": "MathTex",
  "content": "a^2 + b^2 = c^2",
  "font_size": 64,
  "color": "YELLOW",
  "position": { "method": "shift", "x": 0, "y": 0 },
  "scale": 1.5,
  "stroke": { "width": 8, "background": true }
}
```

**Manim 코드:**

```python
equation = MathTex(r"a^2 + b^2 = c^2", font_size=64, color=YELLOW)
equation.shift(ORIGIN)  # 또는 생략
equation.scale(1.5)
equation.set_stroke(width=8, background=True)
```

---

### 4. MathTex (tex_parts - 부분 색상)

**Visual Prompter JSON:**

```json
{
  "id": "eq_factored",
  "type": "MathTex",
  "tex_parts": [
    { "tex": "(x-1)", "color": "ORANGE" },
    { "tex": "(x-2)", "color": "ORANGE" },
    { "tex": "=", "color": "WHITE" },
    { "tex": "0", "color": "WHITE" }
  ],
  "font_size": 56,
  "position": { "method": "shift", "x": -1, "y": -1.4 }
}
```

**Manim 코드:**

```python
eq_factored = MathTex(
    r"(x-1)", r"(x-2)", r"=", r"0",
    font_size=56
)
eq_factored[0].set_color(ORANGE)  # (x-1)
eq_factored[1].set_color(ORANGE)  # (x-2)
eq_factored[2].set_color(WHITE)   # =
eq_factored[3].set_color(WHITE)   # 0
eq_factored.shift(LEFT * 1 + DOWN * 1.4)
```

**변환 규칙:**

- `tex_parts` 배열 → MathTex에 각각 `r"..."` 인자로 전달
- 각 part의 `color` → `[index].set_color()` 메서드
- 인덱스는 tex_parts 배열 순서와 동일 (0, 1, 2, ...)

---

### 4-1. MathTex (subparts - 인덱스 기반 부분 색상)

> ⚠️ `subparts`는 단일 수식 문자열에서 특정 부분만 색칠할 때 사용

**Visual Prompter JSON:**

```json
{
  "id": "lerner_formula",
  "type": "MathTex",
  "content": "\\frac{p - MC}{p} = \\frac{1}{E_d}",
  "font_size": 80,
  "color": "WHITE",
  "subparts": [
    {"index": 0, "meaning": "p - MC", "color": "#58C4DD"},
    {"index": 1, "meaning": "p (분모)", "color": "#58C4DD"},
    {"index": 2, "meaning": "=", "color": "WHITE"},
    {"index": 3, "meaning": "1", "color": "WHITE"},
    {"index": 4, "meaning": "E_d", "color": "#FC6255"}
  ],
  "position": { "method": "shift", "x": 0, "y": 0.5 }
}
```

**Manim 코드:**

```python
lerner_formula = MathTex(
    r"\frac{p - MC}{p} = \frac{1}{E_d}",
    font_size=80,
    color=WHITE
)
# subparts 인덱스로 부분 색상 적용
lerner_formula[0][0:6].set_color("#58C4DD")   # p - MC (분자)
lerner_formula[0][7].set_color("#58C4DD")     # p (분모)
lerner_formula[0][8].set_color(WHITE)         # =
lerner_formula[0][9].set_color(WHITE)         # 1
lerner_formula[0][10:].set_color("#FC6255")   # E_d
lerner_formula.shift(UP * 0.5)
```

**⚠️ subparts 인덱스 주의사항:**

1. **MathTex 내부 인덱싱 복잡성**: LaTeX 수식은 내부적으로 여러 submobject로 분해됨
2. **권장 방법**: `substrings_to_isolate` 사용하여 명시적 분리

**더 안전한 방법 (substrings_to_isolate):**

```python
lerner_formula = MathTex(
    r"\frac{p - MC}{p}", r"=", r"\frac{1}{E_d}",
    substrings_to_isolate=["p", "MC", "E_d"],
    font_size=80
)
lerner_formula.set_color_by_tex("p", "#58C4DD")
lerner_formula.set_color_by_tex("MC", "#58C4DD")
lerner_formula.set_color_by_tex("E_d", "#FC6255")
lerner_formula.shift(UP * 0.5)
```

**변환 규칙:**

| JSON 방식 | Manim 방식 | 권장도 |
|-----------|-----------|--------|
| `tex_parts` 배열 | MathTex에 여러 인자 전달 후 `[i].set_color()` | ⭐⭐⭐ 권장 |
| `subparts` + index | `substrings_to_isolate` + `set_color_by_tex()` | ⭐⭐⭐ 권장 |
| `subparts` + index | `[0][start:end].set_color()` 슬라이싱 | ⚠️ 복잡, 비권장 |

---

### 5. TextMathGroup (한글 + 수식 혼합)

**Visual Prompter JSON:**

```json
{
  "id": "probability_label",
  "type": "TextMathGroup",
  "components": [
    { "type": "Text", "content": "성공 확률", "font": "Noto Sans KR", "font_size": 48, "color": "WHITE" },
    { "type": "MathTex", "content": "= p", "font_size": 48, "color": "YELLOW" }
  ],
  "arrange": "RIGHT",
  "buff": 0.3,
  "position": { "method": "shift", "x": 0, "y": 2 }
}
```

**Manim 코드:**

```python
probability_label_text = Text("성공 확률", font="Noto Sans KR", font_size=48, color=WHITE)
probability_label_math = MathTex(r"= p", font_size=48, color=YELLOW)
probability_label = VGroup(probability_label_text, probability_label_math).arrange(RIGHT, buff=0.3)
probability_label.shift(UP * 2)
```

---

### 6. Arrow

**Visual Prompter JSON:**

```json
{
  "id": "arrow_1",
  "type": "Arrow",
  "start": { "ref": "eq_original", "anchor": "bottom" },
  "end": { "ref": "eq_step1", "anchor": "top" },
  "color": "GRAY",
  "stroke_width": 2,
  "buff": 0.3
}
```

**Manim 코드:**

```python
arrow_1 = Arrow(
    eq_original.get_bottom(),
    eq_step1.get_top(),
    color=GRAY,
    stroke_width=2,
    buff=0.3
)
```

**anchor 매핑:**
| JSON anchor | Manim 메서드 |
|-------------|-------------|
| `bottom` | `get_bottom()` |
| `top` | `get_top()` |
| `left` | `get_left()` |
| `right` | `get_right()` |
| `center` | `get_center()` |

---

### 6-1. CurvedArrow (곡선 화살표)

**Visual Prompter JSON:**

```json
{
  "id": "reverse_arrow",
  "type": "CurvedArrow",
  "start": {"x": 2, "y": -0.3},
  "end": {"x": -2, "y": -0.3},
  "color": "MAGENTA",
  "stroke_width": 4,
  "angle": -1.5,
  "z_index": 1
}
```

**Manim 코드:**

```python
reverse_arrow = CurvedArrow(
    start_point=RIGHT * 2 + DOWN * 0.3,
    end_point=LEFT * 2 + DOWN * 0.3,
    color=MAGENTA,
    stroke_width=4,
    angle=-1.5  # 음수: 시계방향, 양수: 반시계방향
)
reverse_arrow.set_z_index(1)
```

**angle 값 가이드:**

| angle 값 | 효과 | 사용 예 |
|----------|------|---------|
| `TAU/4` (≈1.57) | 반시계방향 완만한 곡선 | 순방향 흐름 |
| `-TAU/4` (≈-1.57) | 시계방향 완만한 곡선 | 역방향 흐름 |
| `TAU/2` (≈3.14) | 반원 곡선 | 큰 전환 강조 |
| `-1.5` | 시계방향 곡선 (예제) | 역이용 표현 |

**참조 객체 기반 CurvedArrow:**

```json
{
  "id": "curved_arrow",
  "type": "CurvedArrow",
  "start": {"ref": "box1", "anchor": "right"},
  "end": {"ref": "box2", "anchor": "left"},
  "color": "CYAN",
  "angle": 0.8
}
```

```python
curved_arrow = CurvedArrow(
    start_point=box1.get_right(),
    end_point=box2.get_left(),
    color=CYAN,
    angle=0.8
)
```

---

### 7. SurroundingRectangle

**Visual Prompter JSON:**

```json
{
  "id": "result_box",
  "type": "SurroundingRectangle",
  "target": "eq_result",
  "color": "#00ff00",
  "stroke_width": 3,
  "buff": 0.2,
  "corner_radius": 0.1
}
```

**Manim 코드:**

```python
result_box = SurroundingRectangle(
    eq_result,
    color="#00ff00",
    stroke_width=3,
    buff=0.2,
    corner_radius=0.1
)
```

---

### 8. 기본 도형 (Circle, Rectangle, Triangle)

**Visual Prompter JSON:**

```json
{
  "id": "circle",
  "type": "Circle",
  "radius": 1.5,
  "color": "YELLOW",
  "fill_opacity": 0.3,
  "stroke_width": 3,
  "position": { "method": "shift", "x": 0, "y": 0 }
}
```

**Manim 코드:**

```python
circle = Circle(radius=1.5, color=YELLOW, fill_opacity=0.3, stroke_width=3)
circle.shift(ORIGIN)  # 또는 생략
```

---

### 9. 3D 객체 (Cube, Sphere, Cylinder, Cone)

**Visual Prompter JSON:**

```json
{
  "id": "cube",
  "type": "Cube",
  "side_length": 3.0,
  "fill_color": "ORANGE",
  "fill_opacity": 0.7,
  "stroke_color": "WHITE",
  "stroke_width": 2
}
```

**Manim 코드:**

```python
cube = Cube(side_length=3.0, fill_opacity=0.7, fill_color=ORANGE)
cube.set_stroke(color=WHITE, width=2)
cube.move_to(ORIGIN)
```

**3D 객체별 고유 인자:**

| 타입       | 고유 인자               |
| ---------- | ----------------------- |
| `Cube`     | `side_length`           |
| `Sphere`   | `radius`                |
| `Cylinder` | `radius`, `height`      |
| `Cone`     | `base_radius`, `height` |

---

### 10. Axes (좌표계)

**Visual Prompter JSON:**

```json
{
  "id": "axes",
  "type": "Axes",
  "x_range": [-3, 3, 1],
  "y_range": [-1, 9, 1],
  "x_length": 6,
  "y_length": 5,
  "axis_config": { "color": "GRAY_B" },
  "position": { "method": "shift", "x": -2, "y": 0 }
}
```

**Manim 코드:**

```python
axes = Axes(
    x_range=[-3, 3, 1],
    y_range=[-1, 9, 1],
    x_length=6,
    y_length=5,
    axis_config={"color": GRAY_B}
)
axes.shift(LEFT * 2)
```

---

### 그래프 필수 체크리스트 (Axes 사용 시)

#### 1. 축 레이블 (필수)

```python
y_label = Text("P", font="Noto Sans KR", font_size=24, color=WHITE)
y_label.next_to(axes.y_axis, UP, buff=0.1)

x_label = Text("Q", font="Noto Sans KR", font_size=24, color=WHITE)
x_label.next_to(axes.x_axis, RIGHT, buff=0.1)
```

#### 2. 곡선 레이블 (필수)

```python
mr_curve = axes.plot(lambda x: -0.5*x + 5, color=GREEN)
mr_label = Text("MR", font="Noto Sans KR", font_size=20, color=GREEN)
mr_label.next_to(mr_curve.get_end(), RIGHT, buff=0.1)
```

#### 3. 교차점 계산 (필수)

```python
# ❌ 잘못된 방법: 임의의 좌표
intersection = Dot(axes.c2p(3, 2), color=YELLOW)

# ✅ 올바른 방법: 실제 교차점 계산
x_star = 5.6  # MR=MC 계산 결과
y_star = mr_func(x_star)
intersection_dot = Dot(axes.c2p(x_star, y_star), color=YELLOW, radius=0.12)
```

---

### 11. Dot (점)

```json
{ "id": "point", "type": "Dot", "position": { "method": "shift", "x": 2, "y": 4 }, "color": "RED", "radius": 0.1 }
```

```python
point = Dot(color=RED, radius=0.1)
point.shift(RIGHT * 2 + UP * 4)
```

---

### 12. RoundedRectangle (둥근 모서리 사각형)

```json
{
  "id": "thought_box",
  "type": "RoundedRectangle",
  "width": 11,
  "height": 2.5,
  "corner_radius": 0.2,
  "fill_color": "#2a1a2e",
  "fill_opacity": 0.8,
  "stroke_color": "#FF00FF",
  "stroke_width": 2,
  "position": { "method": "shift", "x": 0, "y": 0.5 }
}
```

```python
thought_box = RoundedRectangle(
    width=11, height=2.5, corner_radius=0.2,
    fill_color="#2a1a2e", fill_opacity=0.8,
    stroke_color="#FF00FF", stroke_width=2
)
thought_box.shift(UP * 0.5)
```

---

### 13. Line (직선)

```json
{ "id": "tangent", "type": "Line", "start": {"x": 5, "y": 1.5}, "end": {"x": 7, "y": 1.5}, "color": "#FF6B6B", "stroke_width": 2 }
```

```python
tangent = Line(
    start=RIGHT * 5 + UP * 1.5,
    end=RIGHT * 7 + UP * 1.5,
    color="#FF6B6B", stroke_width=2
)
```

---

### 14. DashedLine (점선)

```json
{ "id": "divider", "type": "DashedLine", "start": {"x": -6, "y": 0}, "end": {"x": 6, "y": 0}, "color": "GRAY_B", "stroke_width": 2 }
```

```python
divider = DashedLine(start=LEFT * 6, end=RIGHT * 6, color=GRAY_B, stroke_width=2)
```

---

### 15. Cross (X 표시)

```json
{ "id": "cross_mark", "type": "Cross", "scale": 0.8, "color": "#FF0000", "stroke_width": 8, "position": { "method": "shift", "x": -4, "y": 0.5 } }
```

```python
cross_mark = Cross(scale_factor=0.8, color="#FF0000", stroke_width=8)
cross_mark.shift(LEFT * 4 + UP * 0.5)
```

**주의:** Manim의 Cross는 `scale`이 아니라 `scale_factor` 인자 사용

---

### 16. FunctionGraph (함수 그래프)

```json
{ "id": "curve", "type": "FunctionGraph", "function": "-0.5*(x-2)^2 + 2", "x_range": [0, 4], "color": "#83C167" }
```

```python
curve = FunctionGraph(
    lambda x: -0.5 * (x - 2) ** 2 + 2,
    x_range=[0, 4],
    color="#83C167"
)
```

**변환:** `^` → `**`, 수학 함수는 `np.sin`, `np.cos`, `np.sqrt` 사용

---

## 위치 변환 규칙

### 1. shift (절대 위치)

```json
{ "position": { "method": "shift", "x": -2.5, "y": 1 } }
```

```python
obj.shift(LEFT * 2.5 + UP * 1)
```

**변환:** x 양수=RIGHT, x 음수=LEFT, y 양수=UP, y 음수=DOWN, z=OUT/IN

---

### 2. next_to (상대 위치)

```json
{ "position": { "method": "next_to", "anchor": "stickman", "direction": "RIGHT", "buff": 1.0 } }
```

```python
obj.next_to(stickman, RIGHT, buff=1.0)
```

---

### 3. to_edge (화면 가장자리)

```json
{ "position": { "method": "to_edge", "edge": "UP", "buff": 0.5 } }
```

```python
obj.to_edge(UP, buff=0.5)
```

---

### 4. to_corner (화면 모서리)

```json
{ "position": { "method": "to_corner", "corner": "UL", "buff": 0.5 } }
```

```python
obj.to_corner(UL, buff=0.5)
```

---

### 5. 복합 위치 (shift + align_to)

```json
{ "position": { "method": "shift", "x": 4.5, "y": 0, "align_to": { "target": "eq_original", "direction": "UP" } } }
```

```python
obj.shift(RIGHT * 4.5)
obj.align_to(eq_original, UP)
```

---

## 색상 변환 규칙

### Manim 기본 상수

| JSON 값  | Manim 코드 |
| -------- | ---------- |
| `WHITE`  | `WHITE`    |
| `BLACK`  | `BLACK`    |
| `RED`    | `RED`      |
| `GREEN`  | `GREEN`    |
| `BLUE`   | `BLUE`     |
| `YELLOW` | `YELLOW`   |
| `ORANGE` | `ORANGE`   |
| `GRAY_B` | `GRAY_B`   |

### Hex 색상

```python
color="#00ffff"  # 문자열 그대로 사용
```

### ❌ Manim에 없는 상수

- `CYAN` → `"#00ffff"` 사용
- `MAGENTA` → `"#ff00ff"` 사용

---

## 추가 속성 변환 규칙

### 1. z_index (레이어 순서)

```json
{ "id": "background_box", "type": "Rectangle", "z_index": 1 }
```

```python
background_box = Rectangle(...)
background_box.set_z_index(1)
```

---

### 2. glow (발광 효과)

```json
{ "id": "neon_text", "type": "Text", "color": "#00FFFF", "glow": { "stroke_width": 15, "stroke_opacity": 0.3, "stroke_color": "#00FFFF" } }
```

```python
neon_text = Text("Dynamic", font="Noto Sans KR", color="#00FFFF")
neon_text_glow = neon_text.copy()
neon_text_glow.set_stroke(color="#00FFFF", width=15, opacity=0.3)
neon_text_glow.set_z_index(neon_text.z_index - 1)
self.add(neon_text_glow)  # 글로우 먼저 추가 (뒤에 배치)
self.play(FadeIn(neon_text))  # 원본 애니메이션
```

---

### 3. weight (텍스트 굵기)

```json
{ "id": "bold_title", "type": "Text", "weight": "BOLD" }
```

```python
bold_title = Text("중요한 제목", font="Noto Sans KR", weight=BOLD)
```

---

## 시퀀스 변환 규칙

### 등장 애니메이션

| JSON type            | Manim 코드                    |
| -------------------- | ----------------------------- |
| `FadeIn`             | `FadeIn(obj)`                 |
| `FadeIn` + shift     | `FadeIn(obj, shift=UP * 0.5)` |
| `Write`              | `Write(obj)`                  |
| `Create`             | `Create(obj)`                 |
| `GrowFromCenter`     | `GrowFromCenter(obj)`         |
| `SpinInFromNothing`  | `SpinInFromNothing(obj)`      |
| `GrowArrow`          | `GrowArrow(arrow)`            |

---

### 퇴장 애니메이션

| JSON type        | Manim 코드                       |
| ---------------- | -------------------------------- |
| `FadeOut`        | `FadeOut(obj)`                   |
| `FadeOut`+shift  | `FadeOut(obj, shift=DOWN * 0.5)` |
| `Uncreate`       | `Uncreate(obj)`                  |
| `ShrinkToCenter` | `ShrinkToCenter(obj)`            |

---

### 변환 애니메이션

| JSON type              | Manim 코드                             |
| ---------------------- | -------------------------------------- |
| `Transform`            | `Transform(source, target)`            |
| `TransformMatchingTex` | `TransformMatchingTex(source, target)` |
| `ReplacementTransform` | `ReplacementTransform(source, target)` |

---

### 강조 애니메이션

| JSON type      | Manim 코드                                 |
| -------------- | ------------------------------------------ |
| `Indicate`     | `Indicate(obj, scale_factor=1.2, color=Y)` |
| `Circumscribe` | `Circumscribe(obj, color=YELLOW)`          |
| `Flash`        | `Flash(obj, color=GOLD, flash_radius=1.5)` |
| `Wiggle`       | `Wiggle(obj)`                              |

---

### 이동/스케일 애니메이션

| JSON type | Manim 코드                         |
| --------- | ---------------------------------- |
| `shift`   | `obj.animate.shift(...)`           |
| `scale`   | `obj.animate.scale(...)`           |
| `Rotate`  | `Rotate(obj, angle=PI/2, axis=UP)` |

---

### 대기

```json
{ "type": "wait", "duration": 1.5 }
```

```python
self.wait(1.5)  # wait_tag_s#_#
```

---

### 남은 시간 대기 (wait remaining)

```json
{
  "step": 4,
  "time_range": [5.84, 6.72],
  "actions": [{"type": "Indicate", "target": "label", "run_time": 0.6}],
  "wait": { "duration": "remaining", "tag": "wait_tag_s1_1" }
}
```

```python
self.play(Indicate(label, color=YELLOW), run_time=0.6)  # wait_tag_s1_1
# remaining = (6.72 - 5.84) - 0.6 = 0.28초
remaining_time = 0.28
if remaining_time > 0:
    self.wait(remaining_time)  # wait_tag_s1_final
```

**공식:** `remaining = time_range[1] - time_range[0] - sum(run_times)`

---

### 동시 실행 (simultaneous)

```json
{ "actions": [
    { "type": "FadeIn", "target": "obj_a", "run_time": 1.0 },
    { "type": "FadeIn", "target": "obj_b", "run_time": 1.0, "simultaneous": true }
]}
```

```python
self.play(FadeIn(obj_a), FadeIn(obj_b), run_time=1.0)  # wait_tag_s#_#
```

---

### AnimationGroup (고급 동시 실행)

```json
{
  "type": "AnimationGroup",
  "animations": [
    {"type": "FadeIn", "target": "sparkle1", "run_time": 0.3},
    {"type": "FadeIn", "target": "sparkle2", "run_time": 0.3}
  ],
  "lag_ratio": 0.15
}
```

```python
self.play(
    AnimationGroup(
        FadeIn(sparkle1),
        FadeIn(sparkle2),
        lag_ratio=0.15
    ),
    run_time=0.3
)  # wait_tag_s#_#
```

**lag_ratio:** 0=동시, 0.1~0.3=웨이브, 1.0=순차

---

### 3D 카메라 액션

**move_camera:**

```python
self.move_camera(phi=75*DEGREES, theta=-30*DEGREES, run_time=2.0)
```

**ambient_rotation:**

```python
self.begin_ambient_camera_rotation(rate=0.2)
self.wait(3.0)  # wait_tag_s7_#
self.stop_ambient_camera_rotation()
```

---

## 코드 템플릿

### 기본 씬 템플릿 (2D)

```python
from manim import *

class Scene3(Scene):
    def construct(self):
        STICKMAN_HEIGHT = 4.0
        SOLO_MAIN = 3.0

        snack = ImageMobject("assets/objects/snack_bag.png")
        snack.set_height(3.0).shift(LEFT * 2.5)

        equation = MathTex(r"100g", r"\rightarrow", r"80g", font_size=64)
        equation[0].set_color(YELLOW)
        equation[2].set_color(GREEN)
        equation.shift(DOWN * 2)

        self.play(FadeIn(snack), run_time=1.0)  # wait_tag_s3_1
        self.play(Write(equation), run_time=1.5)  # wait_tag_s3_2
        self.wait(2.0)  # wait_tag_s3_final
```

---

### 3D 씬 템플릿

```python
from manim import *

class Scene7(ThreeDScene):
    def construct(self):
        self.set_camera_orientation(phi=60*DEGREES, theta=-45*DEGREES)

        cube = Cube(side_length=3.0, fill_opacity=0.7, fill_color=ORANGE)
        cube.set_stroke(color=WHITE, width=2)

        title = Text("정육면체", font="Noto Sans KR", font_size=56)
        title.to_edge(UP, buff=0.5)
        self.add_fixed_in_frame_mobjects(title)

        formula = MathTex(r"V = a^3", font_size=56)
        formula.next_to(cube, DOWN, buff=1.2)
        self.add_fixed_in_frame_mobjects(formula)

        self.play(Write(title), run_time=1.0)  # wait_tag_s7_1
        self.play(Create(cube), run_time=1.0)  # wait_tag_s7_2
        self.play(Rotate(cube, angle=PI/4, axis=UP), run_time=2.0)  # wait_tag_s7_3
        self.play(Write(formula), run_time=1.5)  # wait_tag_s7_4
        self.wait(2.0)  # wait_tag_s7_final
```

---

### TextMathGroup 포함 템플릿

```python
from manim import *

class Scene5(Scene):
    def construct(self):
        stickman = ImageMobject("assets/characters/stickman_happy.png")
        stickman.set_height(4.0).shift(LEFT * 3)

        prob_text = Text("성공 확률", font="Noto Sans KR", font_size=48, color=WHITE)
        prob_math = MathTex(r"= 0.75", font_size=48, color=YELLOW)
        probability_label = VGroup(prob_text, prob_math).arrange(RIGHT, buff=0.3)
        probability_label.shift(RIGHT * 2 + UP * 1)

        self.play(FadeIn(stickman), run_time=1.0)  # wait_tag_s5_1
        self.play(Write(probability_label), run_time=1.5)  # wait_tag_s5_2
        self.wait(2.0)  # wait_tag_s5_final
```

---

### 캐릭터 감정 변화 템플릿

```python
from manim import *

class Scene4(Scene):
    def construct(self):
        STICKMAN_HEIGHT = 4.0

        stickman_confused = ImageMobject("assets/characters/stickman_confused.png")
        stickman_confused.set_height(STICKMAN_HEIGHT).shift(LEFT * 3)

        stickman_happy = ImageMobject("assets/characters/stickman_happy.png")
        stickman_happy.set_height(STICKMAN_HEIGHT).shift(LEFT * 3)

        question = ImageMobject("assets/icons/question_mark.png")
        question.set_height(STICKMAN_HEIGHT * 0.20).next_to(stickman_confused, UR, buff=0.2)

        lightbulb = ImageMobject("assets/icons/lightbulb.png")
        lightbulb.set_height(STICKMAN_HEIGHT * 0.20).next_to(stickman_happy, UR, buff=0.2)

        self.play(FadeIn(stickman_confused), run_time=1.0)  # wait_tag_s4_1
        self.play(FadeIn(question, scale=1.5), run_time=0.5)  # wait_tag_s4_2
        self.wait(1.0)  # wait_tag_s4_3

        self.play(
            FadeOut(stickman_confused), FadeOut(question),
            FadeIn(stickman_happy), FadeIn(lightbulb, scale=1.5),
            run_time=0.5
        )  # wait_tag_s4_4
        self.play(Flash(lightbulb, color=YELLOW), run_time=0.5)  # wait_tag_s4_5
        self.wait(2.0)  # wait_tag_s4_final
```

---

### 수식 단계적 전개 템플릿

```python
from manim import *

class Scene6(Scene):
    def construct(self):
        eq1 = MathTex(r"x^3 - 6x^2 + 11x - 6 = 0", font_size=56)
        eq1.shift(UP * 2)

        eq2 = MathTex(r"(x-1)", r"(x^2-5x+6)", r"=", r"0", font_size=56)
        eq2[0].set_color(ORANGE)
        eq2[1].set_color(YELLOW)

        eq3 = MathTex(r"(x-1)", r"(x-2)", r"(x-3)", r"=", r"0", font_size=56)
        eq3[0:3].set_color(ORANGE)
        eq3.shift(DOWN * 2)

        arrow1 = Arrow(eq1.get_bottom(), eq2.get_top(), color=GRAY, buff=0.3)
        arrow2 = Arrow(eq2.get_bottom(), eq3.get_top(), color=GRAY, buff=0.3)
        result_box = SurroundingRectangle(eq3, color=GREEN, stroke_width=3, buff=0.2)

        self.play(Write(eq1), run_time=1.5)  # wait_tag_s6_1
        self.play(Create(arrow1), run_time=0.5)  # wait_tag_s6_2
        self.play(Write(eq2), run_time=1.5)  # wait_tag_s6_3
        self.play(Create(arrow2), run_time=0.5)  # wait_tag_s6_4
        self.play(Write(eq3), run_time=1.5)  # wait_tag_s6_5
        self.play(Create(result_box), Flash(eq3, color=GREEN), run_time=0.5)  # wait_tag_s6_6
        self.wait(2.0)  # wait_tag_s6_final
```

---

## 3D 씬 처리

### 필수 설정

```python
class Scene7(ThreeDScene):  # 반드시 ThreeDScene 상속
    def construct(self):
        self.set_camera_orientation(phi=60*DEGREES, theta=-45*DEGREES)  # DEGREES 필수!
```

### fixed_in_frame 처리

```python
title = Text("3D 제목", font="Noto Sans KR")
self.add_fixed_in_frame_mobjects(title)  # 반드시 추가!
```

**적용 대상:** Text, MathTex, TextMathGroup
**적용 안 함:** Cube, Sphere, Cylinder, Cone

**⚠️ 호출 시점 (Critical):**

```python
class Scene7(ThreeDScene):
    def construct(self):
        self.set_camera_orientation(phi=60*DEGREES, theta=-45*DEGREES)

        # 1. 3D 객체 생성
        cube = Cube(side_length=3.0)

        # 2. 2D 객체 생성 (Text, MathTex)
        title = Text("정육면체", font="Noto Sans KR", font_size=56)
        title.to_edge(UP, buff=0.5)

        # 3. ⚠️ 반드시 애니메이션 전에 fixed_in_frame 호출!
        self.add_fixed_in_frame_mobjects(title)

        # 4. 이제 애니메이션 실행
        self.play(Write(title), run_time=1.0)  # ✅ 정상 동작
        self.play(Create(cube), run_time=1.0)
```

**❌ 잘못된 순서 (오류 발생):**

```python
# 틀린 예시 - 애니메이션 후에 fixed_in_frame 호출
self.play(Write(title))  # ❌ 텍스트가 3D 공간에서 왜곡됨
self.add_fixed_in_frame_mobjects(title)  # 이미 늦음
```

**규칙 요약:**

1. 2D 객체(Text, MathTex) 생성
2. 위치 설정 (to_edge, shift 등)
3. `add_fixed_in_frame_mobjects()` 호출 ← **애니메이션 전!**
4. 애니메이션 실행 (Write, FadeIn 등)

### 3D 회전

```python
self.play(Rotate(cube, angle=PI/2, axis=UP), run_time=2.0)
```

**axis:** UP, DOWN, RIGHT, LEFT, OUT, IN
**angle:** PI, PI/2, PI/4, TAU

---

## 금지 사항

### MathTex

```python
# ❌ r-string 누락
MathTex("\frac{1}{2}")

# ✅
MathTex(r"\frac{1}{2}")
```

### Text

```python
# ❌ 폰트 누락
Text("안녕하세요")

# ✅
Text("안녕하세요", font="Noto Sans KR")
```

### ImageMobject

```python
# ❌ scale 사용
img.scale(0.5)

# ✅ set_height 사용
img.set_height(2.0)
```

```python
# ❌ 잘못된 경로
ImageMobject("stickman.png")

# ✅ 올바른 경로
ImageMobject("assets/characters/stickman.png")
```

### wait_tag

```python
# ❌ 태그 누락
self.play(FadeIn(obj))

# ✅ 태그 필수
self.play(FadeIn(obj))  # wait_tag_s3_1
```

### 3D

```python
# ❌ DEGREES 누락
self.set_camera_orientation(phi=60, theta=-45)

# ✅
self.set_camera_orientation(phi=60*DEGREES, theta=-45*DEGREES)
```

---

## 에러 처리

### 1. 화면 밖 좌표

```python
# Visual Prompter: {"x": -8} → 조정
obj.shift(LEFT * 6)  # 조정됨: x=-8 → x=-6 (안전 영역)
```

### 2. 시간 초과

```python
# time_range [0, 2]인데 actions 총 3초 → run_time 비율 축소
self.play(FadeIn(a), run_time=0.7)  # 조정됨: 1.0 → 0.7
```

### 3. 존재하지 않는 객체 참조

```python
# self.play(FadeIn(undefined_obj))  # 스킵: 객체 미정의
```

### 에러 보고 형식

```
⚠️ Manim Coder 오류 보고

씬: s3
문제: [문제 설명]
위치: [objects/sequence 위치]

권장 조치:
1. Visual Prompter 수정: [구체적 수정 내용]
```

---

## 출력 파일

```
output/{project_id}/4_manim_code/
├── s1_manim.py
├── s2_manim.py
└── ...
```

파일명 규칙: `{scene_id}_manim.py` (예: s1_manim.py, s12_manim.py)
