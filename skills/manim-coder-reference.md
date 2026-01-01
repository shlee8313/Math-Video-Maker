# Manim Coder Reference

> 📌 핵심 규칙은 `manim-coder.md` 참조. 이 문서는 상세 패턴 참조용.

---

## 입력 정보 (Scene Director로부터)

```json
{
  "scene_id": "s2",
  "main_objects": ["ImageMobject('assets/characters/stickman_confused.png')"],
  "actions": [{ "step": 1, "action": "FadeIn(stickman)", "duration": 0.8 }],
  "required_assets": [
    {
      "category": "characters",
      "filename": "stickman_confused.png",
      "description": "혼란스러운 표정"
    }
  ]
}
```

---

## ImageMobject 상세 패턴

### 위치 조정

```python
img.shift(LEFT * 3)                    # 상대 이동
img.move_to(ORIGIN)                    # 절대 위치
img.to_edge(LEFT, buff=0.5)            # 화면 가장자리
img.to_corner(UL)                      # 모서리 (UL, UR, DL, DR)
img.next_to(other, RIGHT, buff=1.0)    # 다른 객체 옆
```

### 애니메이션

```python
# 등장
self.play(FadeIn(img))
self.play(FadeIn(img, shift=UP * 0.5))
self.play(FadeIn(img, scale=1.5))
self.play(GrowFromCenter(img))

# 이동/변환
self.play(img.animate.shift(RIGHT * 2))
self.play(img.animate.move_to(UP * 2))
self.play(img.animate.scale(1.5))      # 애니메이션 중에만 scale 허용
self.play(img.animate.rotate(PI / 4))

# 퇴장
self.play(FadeOut(img))
self.play(FadeOut(img, shift=DOWN * 0.5))
self.play(ShrinkToCenter(img))
```

### 이미지 교체 (감정 변화)

```python
STICKMAN_HEIGHT = 4

stickman_confused = ImageMobject("assets/characters/stickman_confused.png")
stickman_confused.set_height(STICKMAN_HEIGHT).shift(LEFT * 3)

stickman_happy = ImageMobject("assets/characters/stickman_happy.png")
stickman_happy.set_height(STICKMAN_HEIGHT).shift(LEFT * 3)

self.play(FadeIn(stickman_confused))  # wait_tag_s3_1
self.wait(2)  # wait_tag_s3_2
self.play(FadeOut(stickman_confused), FadeIn(stickman_happy), run_time=0.5)  # wait_tag_s3_3

# 또는 ReplacementTransform
self.play(ReplacementTransform(stickman_confused, stickman_happy))
```

### 이미지 그룹화

```python
STICKMAN_HEIGHT = 4

stickman = ImageMobject("assets/characters/stickman_holding.png")
stickman.set_height(STICKMAN_HEIGHT)

snack = ImageMobject("assets/objects/snack_bag_normal.png")
snack.set_height(STICKMAN_HEIGHT * 0.30)
snack.next_to(stickman, RIGHT, buff=0.2)

character_group = Group(stickman, snack)
character_group.shift(LEFT * 2)

self.play(FadeIn(character_group))
self.play(character_group.animate.shift(RIGHT * 4))
```

---

## 텍스트 & 수식

### 일반 텍스트

```python
text = Text("안녕하세요", font="Noto Sans KR", font_size=48)
text.add_background_rectangle(color=BLACK, opacity=0.8, buff=0.2)
text.to_edge(UP)
```

### 수식

```python
eq = MathTex(r"f(x) = x^2", font_size=64, color=YELLOW)
eq.set_stroke(width=8, background=True)  # 그림자

# 부분 색상
eq = MathTex("x", "^2", "+", "2x")
eq[0].set_color(YELLOW)
eq[1].set_color(ORANGE)
```

### 수식 변환

```python
eq1 = MathTex("x", "+", "2", "=", "5")
eq2 = MathTex("x", "=", "5", "-", "2")
eq3 = MathTex("x", "=", "3")

self.play(Write(eq1))  # wait_tag_s1_1
self.wait(1)  # wait_tag_s1_2
self.play(TransformMatchingTex(eq1, eq2))  # wait_tag_s1_3
self.wait(1)  # wait_tag_s1_4
self.play(TransformMatchingTex(eq2, eq3))  # wait_tag_s1_5
```

---

## 그래프

### 2D 그래프

```python
axes = Axes(
    x_range=[-3, 3, 1],
    y_range=[-1, 9, 1],
    x_length=10,
    y_length=6,
    axis_config={"color": GRAY_B, "include_tip": True}
)
labels = axes.get_axis_labels(x_label="x", y_label="y")
graph = axes.plot(lambda x: x**2, color=YELLOW, x_range=[-3, 3])

self.play(Create(axes), Write(labels))  # wait_tag_s1_1
self.play(Create(graph), run_time=3)  # wait_tag_s1_2
```

### ValueTracker + always_redraw

```python
x_tracker = ValueTracker(-3)

axes = Axes(x_range=[-3, 3], y_range=[-1, 9])
graph = axes.plot(lambda x: x**2, color=YELLOW)

dot = always_redraw(lambda:
    Dot(color=RED).move_to(
        axes.c2p(x_tracker.get_value(), x_tracker.get_value()**2)
    )
)

coords = always_redraw(lambda:
    MathTex(f"({x_tracker.get_value():.1f}, {x_tracker.get_value()**2:.1f})")
    .next_to(dot, UR)
    .add_background_rectangle()
)

self.add(axes, graph, dot, coords)
self.play(x_tracker.animate.set_value(3), run_time=5)  # wait_tag_s1_1
```

---

## 강조 애니메이션

```python
self.play(Indicate(obj, scale_factor=1.3, color=RED))
self.play(Circumscribe(obj, color=YELLOW, run_time=1.5))
self.play(Flash(obj, color=GOLD, flash_radius=1.5, num_lines=12))
self.play(ApplyWave(obj))
self.play(Wiggle(obj))
```

---

## 3D 씬 상세

### 카메라 설정

```python
# 기본 등각 뷰 (권장)
self.set_camera_orientation(phi=60*DEGREES, theta=-45*DEGREES)

# 동적 회전
self.begin_ambient_camera_rotation(rate=0.2)
self.wait(3)
self.stop_ambient_camera_rotation()

# 카메라 이동
self.move_camera(phi=75*DEGREES, theta=-30*DEGREES, run_time=2)
```

### 3D 객체

```python
# 크기 기준: 단독=3.0, 캐릭터와 함께=2.0, 강조=4.0
CUBE_SOLO = 3.0

cube = Cube(side_length=CUBE_SOLO, fill_opacity=0.7, fill_color=ORANGE)
cube.set_stroke(color=WHITE, width=2)

# 단독: radius=2.0, 함께: radius=1.2
cylinder = Cylinder(radius=1.2, height=3, fill_opacity=0.7, fill_color=BLUE)
sphere = Sphere(radius=2.0, fill_opacity=0.7, fill_color=GREEN)
cone = Cone(base_radius=1.2, height=2, fill_opacity=0.7, fill_color=RED)
```

---

## Scene 클래스별 템플릿

### MovingCameraScene (줌)

```python
class Scene3(MovingCameraScene):
    def construct(self):
        STICKMAN_HEIGHT = 4
        equation = MathTex(r"...")

        self.play(
            self.camera.frame.animate.scale(0.5).move_to(equation)
        )  # wait_tag_s3_1
```

### ThreeDScene

```python
class Scene7(ThreeDScene):
    def construct(self):
        # ========== 크기 기준 ==========
        CUBE_SOLO = 3.0  # 단독 등장

        self.set_camera_orientation(phi=60*DEGREES, theta=-45*DEGREES)

        cube = Cube(side_length=CUBE_SOLO, fill_opacity=0.7, fill_color=ORANGE)
        cube.set_stroke(color=WHITE, width=2)
        cube.move_to(ORIGIN)

        # 3D 텍스트는 고정 필수!
        label = MathTex(r"V = a^3", color=YELLOW, font_size=64)
        label.scale(1.5)  # 단독이라 크게
        label.next_to(cube, DOWN, buff=0.8)
        self.add_fixed_in_frame_mobjects(label)

        self.play(Create(cube))  # wait_tag_s7_1
        self.play(Write(label))  # wait_tag_s7_2
        self.play(Rotate(cube, angle=PI/2, axis=UP), run_time=2)  # wait_tag_s7_3
        self.wait(1)  # wait_tag_s7_final
```

---

## 스타일별 설정

### 어두운 배경 (minimal, cyberpunk, space, geometric, stickman)

```python
DARK_BG_PALETTE = {
    "primary": WHITE,
    "variable": YELLOW,
    "constant": ORANGE,
    "result": GREEN,
    "auxiliary": GRAY_B,
    "emphasis": RED
}
```

### 밝은 배경 (paper)

```python
LIGHT_BG_PALETTE = {
    "primary": BLACK,
    "variable": "#1a237e",     # 진한 파랑
    "constant": "#bf360c",      # 진한 주황
    "result": "#1b5e20",        # 진한 초록
    "auxiliary": GRAY_D,
    "emphasis": "#b71c1c"       # 진한 빨강
}
```

### 스타일별 배경색

| 스타일    | 배경 색상 |
| --------- | --------- |
| minimal   | #000000   |
| cyberpunk | #0a0a1a   |
| space     | #000011   |
| geometric | #1a1a1a   |
| stickman  | #1a2a3a   |
| paper     | #f5f5dc   |

---

## 일반적인 실수 & 해결

### MathTex 중괄호 에러

```python
# ❌
MathTex("\frac{1}{2}")

# ✅
MathTex(r"\frac{1}{2}")
```

### always_redraw 문법

```python
# ❌
number = always_redraw(DecimalNumber(tracker.get_value()))

# ✅
number = always_redraw(lambda: DecimalNumber(tracker.get_value()))
```

### 한글 폰트 누락

```python
# ❌
text = Text("안녕하세요")

# ✅
text = Text("안녕하세요", font="Noto Sans KR")
```

### 이미지 경로 오류

```python
# ❌
ImageMobject("stickman.png")
ImageMobject("./assets/stickman.png")

# ✅
ImageMobject("assets/characters/stickman_neutral.png")
```

### 3D 객체가 2D로 보임

```python
# ❌ 일반 Scene 사용
class Scene7(Scene):
    def construct(self):
        cube = Cube()

# ❌ 카메라 설정 없음
class Scene7(ThreeDScene):
    def construct(self):
        cube = Cube()
        self.add(cube)

# ✅ ThreeDScene + 카메라 설정
class Scene7(ThreeDScene):
    def construct(self):
        self.set_camera_orientation(phi=60*DEGREES, theta=-45*DEGREES)
        cube = Cube()
        self.play(Create(cube))
```

---

## 에셋 경로 규칙

```python
# ✅ 올바른 경로
ImageMobject("assets/characters/stickman_happy.png")
ImageMobject("assets/objects/money.png")
ImageMobject("assets/icons/lightbulb.png")

# ❌ 틀린 경로
ImageMobject("stickman_happy.png")           # 폴더 없음
ImageMobject("./assets/characters/...")      # ./ 불필요
ImageMobject("C:/PROJECT/assets/...")        # 절대 경로 금지
ImageMobject("output/P001/assets/...")       # 프로젝트별 경로 아님
```

---

## 에셋 폴더 구조

```
Math-Video-Maker/
├── assets/                    ← 모든 프로젝트 공용
│   ├── characters/
│   │   ├── stickman_neutral.png
│   │   ├── stickman_thinking.png
│   │   ├── stickman_surprised.png
│   │   ├── stickman_happy.png
│   │   ├── stickman_confused.png
│   │   ├── stickman_pointing.png
│   │   ├── stickman_holding.png
│   │   └── stickman_sad.png
│   ├── objects/
│   │   ├── snack_bag_normal.png
│   │   ├── snack_bag_shrunk.png
│   │   ├── money.png
│   │   └── cart.png
│   └── icons/
│       ├── question_mark.png
│       ├── exclamation.png
│       └── lightbulb.png
```

---

## 출력 형식 예시

### 에셋 + 수식 혼합 씬

```python
from manim import *

class Scene5(Scene):
    def construct(self):
        STICKMAN_HEIGHT = 4

        COLOR_PALETTE = {
            "variable": YELLOW,
            "result": GREEN,
            "emphasis": RED
        }

        stickman = ImageMobject("assets/characters/stickman_happy.png")
        stickman.set_height(STICKMAN_HEIGHT)
        stickman.to_edge(LEFT, buff=1)

        lightbulb = ImageMobject("assets/icons/lightbulb.png")
        lightbulb.set_height(STICKMAN_HEIGHT * 0.25)
        lightbulb.next_to(stickman, UP, buff=0.3)

        # 수식: 캐릭터와 함께 → scale(1.0)
        equation = MathTex(
            r"\frac{100}{80} - 1 = 0.25 = 25\%",
            font_size=64,
            color=COLOR_PALETTE["result"]
        )
        equation.scale(1.0).shift(RIGHT * 1)  # 캐릭터와 함께
        equation.add_background_rectangle(color=BLACK, opacity=0.7)

        # 제목: 단독 → scale(1.3)
        title = Text("슈링크플레이션", font="Noto Sans KR", font_size=72, color=CYAN)
        title.scale(1.0).to_edge(UP, buff=0.5)  # 상단 고정은 scale 1.0

        self.play(FadeIn(stickman))  # wait_tag_s5_1
        self.wait(0.5)  # wait_tag_s5_2
        self.play(FadeIn(lightbulb, scale=1.5))  # wait_tag_s5_3
        self.play(Flash(lightbulb, color=YELLOW, num_lines=8))  # wait_tag_s5_4
        self.play(Write(equation))  # wait_tag_s5_5
        self.wait(1)  # wait_tag_s5_6
        self.play(Write(title))  # wait_tag_s5_7
        self.wait(2)  # wait_tag_s5_final
```
