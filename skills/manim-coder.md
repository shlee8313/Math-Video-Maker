# Manim Coder Skill

## 역할

Manim Community Edition 코드 구현 전문가. 연출 계획을 Python 코드로 변환.

> 📚 상세 패턴은 `manim-coder-reference.md` 참조

---

## 절대 규칙 (CRITICAL)

1. 모든 수식은 `MathTex(r"...")` 형식
2. 수식 변화는 `TransformMatchingTex` 우선
3. 모든 `wait()`에 주석: `# wait_tag_s[씬번호]_[순서]`
4. Text는 `font="Noto Sans KR"` 필수
5. 중괄호 `{}` 짝 맞추기
6. `always_redraw`는 반드시 `lambda` 사용
7. 캐릭터/물체는 `ImageMobject` 사용 (직접 그리기 금지!)
8. 에셋 경로는 `"assets/..."` 형식
9. 3D 객체 → `ThreeDScene` + `set_camera_orientation()` 필수
10. 자막은 Manim에서 처리하지 않음 (FFmpeg/SRT)

---

## 📐 에셋 크기 기준 시스템 (CRITICAL)

**핵심: 졸라맨을 기준으로 모든 에셋 크기 설정**

```python
STICKMAN_HEIGHT = 4  # 화면 높이(8)의 50% = 기준!

# ❌ scale() - 예측 불가능
stickman.scale(0.5)

# ✅ set_height() - 예측 가능
stickman.set_height(STICKMAN_HEIGHT)
snack_bag.set_height(STICKMAN_HEIGHT * 0.30)
```

### 크기 비율표

| 유형            | 비율    | set_height               |
| --------------- | ------- | ------------------------ |
| 캐릭터 (주인공) | 100%    | `STICKMAN_HEIGHT`        |
| 캐릭터 (서브)   | 80%     | `STICKMAN_HEIGHT * 0.80` |
| 손에 드는 물건  | 25~35%  | `STICKMAN_HEIGHT * 0.30` |
| 중간 물체       | 40~60%  | `STICKMAN_HEIGHT * 0.50` |
| 큰 물체         | 70~100% | `STICKMAN_HEIGHT * 0.80` |
| 머리 위 아이콘  | 15~25%  | `STICKMAN_HEIGHT * 0.20` |
| 강조 아이콘     | 30~50%  | `STICKMAN_HEIGHT * 0.40` |

### 📍 단독 물체 크기 및 위치 (캐릭터 없이 등장할 때)

**문제:** 캐릭터와 함께 나올 때 기준(30~50%)으로 물체를 단독 배치하면 너무 작음

```python
# ========== 단독 물체 크기 ==========
SOLO_MAIN = 3.0      # 화면의 37% - 주인공급 물체
SOLO_LARGE = 4.0     # 화면의 50% - 강조할 때
SOLO_WITH_LABEL = 2.5  # 라벨과 함께 나올 때
SOLO_ICON = 2.0      # 아이콘 강조

# 예시
snack = ImageMobject("assets/objects/snack_bag.png")
snack.set_height(SOLO_MAIN)  # 3.0 (단독)
# vs
snack.set_height(STICKMAN_HEIGHT * 0.30)  # 1.2 (캐릭터와 함께)
```

**크기 비교표:**

| 상황 | 크기 | 화면 비율 |
|------|------|----------|
| 캐릭터 + 물체 | 1.2~2.0 | 15~25% |
| **물체 단독** | **3.0** | **37%** |
| **물체 강조** | **4.0** | **50%** |
| **아이콘 단독** | **2.0~2.5** | **25~31%** |

**단독 물체 위치:**

```python
# 1. 화면 중앙 (기본)
object.move_to(ORIGIN)

# 2. 약간 위 (하단에 수식/텍스트 공간 확보)
object.move_to(UP * 0.5)

# 3. 좌측 물체 + 우측 설명
object.shift(LEFT * 2.5)
label.next_to(object, RIGHT, buff=1.0)

# 4. 상단 물체 + 하단 수식
object.shift(UP * 1)
equation.shift(DOWN * 2)
```

**레이아웃 패턴:**

```
┌─────────────────────────────────┐
│         [제목 영역]              │  UP * 3.5
│                                 │
│         ┌───────┐               │
│         │ 물체  │  ← ORIGIN     │  중앙
│         └───────┘   또는 UP*0.5 │
│                                 │
│       수식 또는 설명             │  DOWN * 2
└─────────────────────────────────┘
```

| 상황 | 물체 위치 | 보조 요소 위치 |
|------|----------|---------------|
| 물체만 강조 | `ORIGIN` | - |
| 물체 + 수식 | `UP * 1` | 수식: `DOWN * 2` |
| 물체 + 라벨 | `LEFT * 2` | 라벨: `RIGHT * 2` |
| 물체 비교 (2개) | `LEFT * 2.5` | 두번째: `RIGHT * 2.5` |
| 물체 나열 (3개) | `LEFT * 3.5` | 중앙 `ORIGIN`, `RIGHT * 3.5` |

---

## 📝 텍스트/수식 크기 기준

### font_size 기준 (생성 시)

```python
# ========== 텍스트/수식 font_size ==========
TITLE_SIZE = 72          # 제목, 섹션명
EQUATION_MAIN = 64       # 주요 수식
EQUATION_SUB = 48        # 보조 수식, 설명
TEXT_NORMAL = 48         # 일반 텍스트
TEXT_LABEL = 36          # 라벨, 축 레이블

# 예시
title = Text("피타고라스 정리", font="Noto Sans KR", font_size=72)
equation = MathTex(r"a^2 + b^2 = c^2", font_size=64)
label = Text("빗변", font="Noto Sans KR", font_size=36)
```

### scale() 기준 (상황별 조정)

**원칙:** `font_size`로 기본 크기 설정 → `scale()`로 상황별 조정

```python
# ========== scale 상황별 ==========
SCALE_SOLO = 1.5         # 단독 등장 (강조)
SCALE_EMPHASIS = 1.8     # 특별 강조
SCALE_WITH_OBJECTS = 1.0 # 다른 요소와 함께
SCALE_SMALL = 0.8        # 공간 부족 시

# 예시: 수식 단독 등장
equation = MathTex(r"E = mc^2", font_size=64)
equation.scale(1.5)  # 단독이라 크게

# 예시: 물체와 함께
equation = MathTex(r"V = lwh", font_size=64)
equation.scale(1.0)  # 물체랑 같이 있어서 기본
```

### 상황별 크기표

| 상황 | font_size | scale | 결과 |
|------|-----------|-------|------|
| **제목 단독** | 72 | 1.3 | 매우 큼 |
| **수식 단독** | 64 | **1.5** | 큼 (강조) |
| 수식 + 물체/캐릭터 | 64 | 1.0 | 보통 |
| 보조 수식 | 48 | 1.0 | 작음 |
| 라벨/축 | 36 | 1.0 | 작음 |
| **결과 강조** | 64 | **1.8** | 매우 큼 |

### 📍 텍스트/수식 위치

```python
# 제목: 상단
title.to_edge(UP, buff=0.5)

# 수식 단독: 중앙 또는 약간 위
equation.move_to(ORIGIN)
equation.move_to(UP * 0.5)  # 설명 공간 확보

# 수식 + 물체: 물체 옆 또는 아래
equation.next_to(object, RIGHT, buff=1.0)
equation.next_to(object, DOWN, buff=0.8)

# 수식 여러 줄: VGroup으로 정렬
equations = VGroup(eq1, eq2, eq3).arrange(DOWN, buff=0.5)
equations.move_to(ORIGIN)
```

| 상황 | 위치 |
|------|------|
| 제목 | `to_edge(UP, buff=0.5)` |
| 수식 단독 | `ORIGIN` 또는 `UP * 0.5` |
| 수식 + 물체 | `next_to(물체, RIGHT/DOWN)` |
| 수식 여러 개 | `VGroup(...).arrange(DOWN)` |
| 결과 강조 | `ORIGIN` + `scale(1.8)` |

### 가독성 향상

```python
# 배경과 대비 (어두운 배경)
equation.set_stroke(width=8, background=True)  # 그림자

# 배경 박스 추가
equation.add_background_rectangle(color=BLACK, opacity=0.7, buff=0.2)

# 수식 부분 색상
eq = MathTex("x", "^2", "+", "2x", "=", "0")
eq[0].set_color(YELLOW)   # x
eq[3].set_color(YELLOW)   # 2x
eq[5].set_color(GREEN)    # 결과
```

---

## 🧊 3D 씬 규칙

| 객체                                 | Scene 클래스       |
| ------------------------------------ | ------------------ |
| `Cube`, `Cylinder`, `Sphere`, `Cone` | `ThreeDScene` 필수 |
| `Square`, `Circle`, `MathTex`        | `Scene`            |

### 📐 3D 객체 크기 기준

**주의:** 3D는 원근법으로 작아 보이므로 2D보다 크게 설정!

```python
# ========== 3D 크기 기준 ==========
# 캐릭터와 함께
CUBE_WITH_CHAR = 2.0       # side_length
SPHERE_WITH_CHAR = 1.2     # radius
CYLINDER_WITH_CHAR = (0.8, 2.0)  # (radius, height)

# 단독 등장 (더 크게!)
CUBE_SOLO = 3.0            # side_length
SPHERE_SOLO = 2.0          # radius
CYLINDER_SOLO = (1.2, 3.0) # (radius, height)

# 강조/클로즈업
CUBE_EMPHASIS = 4.0        # side_length
```

**크기 비교표:**

| 상황 | Cube side | Sphere radius | Cylinder (r, h) |
|------|-----------|---------------|-----------------|
| 캐릭터와 함께 | 2.0 | 1.2 | (0.8, 2.0) |
| **단독 등장** | **3.0** | **2.0** | **(1.2, 3.0)** |
| **강조** | **4.0** | **2.5** | **(1.5, 4.0)** |

### 📍 3D 객체 위치

```python
# 기본: 중앙 (카메라가 비스듬히 보므로 ORIGIN이 적절)
cube.move_to(ORIGIN)

# 약간 아래로 (수식 공간 확보)
cube.shift(DOWN * 0.5)

# 2개 비교
cube1.shift(LEFT * 2.5)
cube2.shift(RIGHT * 2.5)

# 3개 나열
obj1.shift(LEFT * 3.5)
obj2.move_to(ORIGIN)
obj3.shift(RIGHT * 3.5)
```

**3D 위치 주의사항:**
- 3D에서는 `UP/DOWN` 이동 시 깊이감이 달라 보임
- 비교 시 `LEFT/RIGHT`만 사용 권장
- 수직 배치보다 **수평 배치** 선호

### 🎥 카메라 각도 용도

```python
# 기본 등각뷰 (권장) - 3면이 균형있게 보임
self.set_camera_orientation(phi=60*DEGREES, theta=-45*DEGREES)

# 위에서 내려다봄 - 윗면/단면 강조
self.set_camera_orientation(phi=75*DEGREES, theta=-45*DEGREES)

# 옆에서 봄 - 높이/측면 강조
self.set_camera_orientation(phi=30*DEGREES, theta=-45*DEGREES)

# 정면 - 2D처럼 보임 (비권장)
self.set_camera_orientation(phi=0*DEGREES, theta=-90*DEGREES)
```

| 용도 | phi | theta | 설명 |
|------|-----|-------|------|
| **기본 (권장)** | 60° | -45° | 3면 균형, 입체감 |
| 윗면 강조 | 75° | -45° | 단면적, 전개도 |
| 측면 강조 | 30° | -45° | 높이, 부피 비교 |
| 회전 시작점 | 60° | 0° | 정면에서 회전 |

### 3D 코드 템플릿

```python
class Scene7(ThreeDScene):
    def construct(self):
        # ========== 카메라 설정 (필수!) ==========
        self.set_camera_orientation(phi=60*DEGREES, theta=-45*DEGREES)

        # ========== 3D 크기 기준 ==========
        CUBE_SOLO = 3.0

        # ========== 3D 객체 생성 ==========
        cube = Cube(side_length=CUBE_SOLO, fill_opacity=0.7, fill_color=ORANGE)
        cube.set_stroke(color=WHITE, width=2)
        cube.move_to(ORIGIN)

        # ========== 라벨 (3D에서 텍스트) ==========
        label = MathTex(r"V = a^3", color=YELLOW)
        label.scale(1.2)
        label.next_to(cube, DOWN, buff=0.8)
        self.add_fixed_in_frame_mobjects(label)  # 텍스트 고정!

        # ========== 애니메이션 ==========
        self.play(Create(cube))  # wait_tag_s7_1
        self.play(Write(label))  # wait_tag_s7_2
        self.play(Rotate(cube, angle=PI/2, axis=UP), run_time=2)  # wait_tag_s7_3
        self.wait(1)  # wait_tag_s7_final
```

**3D 텍스트 주의:** `add_fixed_in_frame_mobjects()`로 텍스트 고정 필수!

---

## 코드 템플릿

```python
from manim import *

class Scene2(Scene):
    def construct(self):
        # ========== 📏 크기 기준 ==========
        STICKMAN_HEIGHT = 4

        # ========== 컬러 팔레트 ==========
        COLOR = {"variable": YELLOW, "result": GREEN, "emphasis": RED}

        # ========== 에셋 로드 ==========
        stickman = ImageMobject("assets/characters/stickman_confused.png")
        stickman.set_height(STICKMAN_HEIGHT)
        stickman.shift(LEFT * 3)

        snack_bag = ImageMobject("assets/objects/snack_bag_normal.png")
        snack_bag.set_height(STICKMAN_HEIGHT * 0.30)
        snack_bag.next_to(stickman, RIGHT, buff=1.0)

        question = ImageMobject("assets/icons/question_mark.png")
        question.set_height(STICKMAN_HEIGHT * 0.20)
        question.next_to(stickman, UP, buff=0.3)

        # ========== 애니메이션 ==========
        self.play(FadeIn(stickman))  # wait_tag_s2_1
        self.wait(0.5)  # wait_tag_s2_2
        self.play(FadeIn(snack_bag))  # wait_tag_s2_3
        self.wait(1)  # wait_tag_s2_final
```

---

## 컬러 팔레트

| 배경                                     | 팔레트                              |
| ---------------------------------------- | ----------------------------------- |
| 어두운 (minimal, cyberpunk, stickman 등) | `WHITE, YELLOW, ORANGE, GREEN, RED` |
| 밝은 (paper)                             | `BLACK, #1a237e, #bf360c, #1b5e20`  |

---

## 🚫 금지 패턴

```python
# ❌ 캐릭터 직접 그리기
head = Circle(radius=0.3)
body = Line(ORIGIN, DOWN)

# ❌ 에셋(ImageMobject)에 scale() 사용
stickman.scale(0.5)  # 예측 불가능!
snack.scale(2.0)     # ❌

# ✅ 에셋은 set_height() 사용
stickman.set_height(STICKMAN_HEIGHT)
snack.set_height(SOLO_MAIN)

# ✅ 텍스트/수식에는 scale() 허용
equation.scale(1.5)  # OK - 텍스트는 scale 가능
title.scale(1.3)     # OK

# ❌ 일반 Scene에서 3D 객체
class Scene7(Scene):
    cube = Cube()  # 에러!

# ✅ 올바른 방법
stickman = ImageMobject("assets/characters/stickman_neutral.png")
stickman.set_height(STICKMAN_HEIGHT)
```

---

## 체크리스트

### 기본 규칙
- [ ] `STICKMAN_HEIGHT = 4` 정의
- [ ] 모든 에셋 `set_height()` 사용 (scale 금지)
- [ ] 모든 `MathTex`에 `r"..."` 사용
- [ ] 모든 `Text`에 `font="Noto Sans KR"`
- [ ] 모든 `wait()`에 태그 주석
- [ ] 캐릭터/물체 → `ImageMobject`

### 크기 확인
- [ ] 캐릭터와 함께 → 물체 `STICKMAN_HEIGHT * 0.30~0.50`
- [ ] 물체 단독 → `SOLO_MAIN = 3.0` 이상
- [ ] 수식 단독 → `font_size=64` + `scale(1.5)`
- [ ] 수식 + 물체 → `font_size=64` + `scale(1.0)`

### 3D 씬
- [ ] 3D 객체 → `ThreeDScene` 클래스
- [ ] `set_camera_orientation(phi=60*DEGREES, theta=-45*DEGREES)`
- [ ] 3D 단독 → `CUBE_SOLO = 3.0` 이상
- [ ] 3D 텍스트 → `add_fixed_in_frame_mobjects()` 사용

### 위치 확인
- [ ] 단독 물체/수식 → `ORIGIN` 또는 `UP * 0.5`
- [ ] 물체 + 수식 → 물체 `UP * 1`, 수식 `DOWN * 2`
- [ ] 2개 비교 → `LEFT * 2.5`, `RIGHT * 2.5`
- [ ] 3개 나열 → `LEFT * 3.5`, `ORIGIN`, `RIGHT * 3.5`
