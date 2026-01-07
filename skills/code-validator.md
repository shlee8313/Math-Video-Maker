# Code Validator Skill

## Manim 코드 검증 및 파이프라인 일관성 전문가

### 역할 정의

당신은 Manim 코드의 품질 보증 및 **파이프라인 일관성 검증** 전문가입니다.

**핵심 책임:**

1. **파이프라인 일관성 검증**: Scene Director → Visual Prompter → Manim Coder 간 데이터 흐름 검증
2. **코드 품질 검증**: 생성된 Manim 코드의 문법, 로직, 타이밍, 스타일 검증
3. **자동 수정**: 발견된 오류를 자동으로 수정

---

## 입력 정보

Code Validator는 다음 4개 파일을 입력으로 받습니다:

### 1. Scene Director 데이터 (`scenes.json`의 해당 씬)

```json
{
  "scene_id": "s3",
  "section": "핵심수학",
  "duration": 15,
  "narration_display": "가격은 그대로인데, 용량이 줄었습니다. 100g → 80g",
  "narration_tts": "가격은 그대로인데, 용량이 줄었습니다...",
  "semantic_goal": "용량 감소를 시각적으로 대비시켜 충격 주기",
  "required_elements": [
    { "type": "image", "asset": "snack_bag_normal.png", "role": "비교 대상 A" },
    { "type": "image", "asset": "snack_bag_shrunk.png", "role": "비교 대상 B" },
    { "type": "math", "content": "100g \\rightarrow 80g", "role": "수치 표현" }
  ],
  "wow_moment": "줄어든 과자가 등장하는 순간",
  "emotion_flow": "평범 → 의아함 → 충격",
  "style": "minimal",
  "is_3d": false,
  "scene_class": "Scene",
  "required_assets": [
    { "category": "objects", "filename": "snack_bag_normal.png" },
    { "category": "objects", "filename": "snack_bag_shrunk.png" }
  ]
}
```

### 2. Visual Prompter 데이터 (`s#_visual.json`)

```json
{
  "scene_id": "s3",
  "is_3d": false,
  "scene_class": "Scene",
  "style": "minimal",
  "total_duration": 14.2,
  "canvas": {
    "background": "#000000",
    "safe_margin": 0.5
  },
  "objects": [
    {
      "id": "snack_normal",
      "type": "ImageMobject",
      "source": "assets/objects/snack_bag_normal.png",
      "size": { "height": 3.0 },
      "position": { "method": "shift", "x": -2.5, "y": 0 }
    },
    {
      "id": "snack_shrunk",
      "type": "ImageMobject",
      "source": "assets/objects/snack_bag_shrunk.png",
      "size": { "height": 2.4 },
      "position": { "method": "shift", "x": 2.5, "y": 0 }
    },
    {
      "id": "equation",
      "type": "MathTex",
      "tex_parts": [
        { "tex": "100g", "color": "YELLOW" },
        { "tex": "\\rightarrow", "color": "WHITE" },
        { "tex": "80g", "color": "GREEN" }
      ],
      "font_size": 64,
      "position": { "method": "shift", "x": 0, "y": -2 }
    }
  ],
  "sequence": [
    {
      "step": 1,
      "time_range": [0, 1.8],
      "actions": [{ "type": "FadeIn", "target": "snack_normal", "run_time": 1.0 }]
    },
    {
      "step": 2,
      "time_range": [1.8, 3.5],
      "actions": [
        { "type": "FadeIn", "target": "snack_shrunk", "run_time": 1.0 },
        { "type": "Indicate", "target": "snack_shrunk", "run_time": 0.7 }
      ]
    },
    {
      "step": 3,
      "time_range": [3.5, 6.2],
      "actions": [{ "type": "Write", "target": "equation", "run_time": 1.5 }]
    },
    {
      "step": 4,
      "time_range": [6.2, 14.2],
      "actions": [{ "type": "wait", "duration": 8.0 }]
    }
  ]
}
```

### 3. Manim 코드 (`s#_manim.py`)

```python
from manim import *

class Scene3(Scene):
    def construct(self):
        # 객체 생성
        snack_normal = ImageMobject("assets/objects/snack_bag_normal.png")
        snack_normal.set_height(3.0)
        snack_normal.shift(LEFT * 2.5)

        # ... 애니메이션
        self.play(FadeIn(snack_normal))  # wait_tag_s3_1
```

### 4. Timing 데이터 (`s#_timing.json`)

```json
{
  "scene_id": "s3",
  "total_duration": 14.2,
  "segments": [
    { "text": "가격은 그대로인데", "start": 0, "end": 1.8 },
    { "text": "용량이 줄었습니다", "start": 1.8, "end": 3.5 }
  ]
}
```

---

## 검증 프로세스 개요

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Code Validator 검증 순서                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Phase 0: 파이프라인 일관성 검증 ← NEW!                              │
│  ├── A. Scene Director → Visual Prompter 일치                       │
│  ├── B. Visual Prompter → Manim Coder 일치                          │
│  └── C. timing.json ↔ 코드 동기화                                   │
│                                                                     │
│  Phase 1: 문법 검증                                                  │
│  ├── MathTex r-string, 중괄호                                       │
│  ├── Text 한글 폰트                                                 │
│  └── always_redraw lambda                                           │
│                                                                     │
│  Phase 2: 로직 검증                                                  │
│  ├── Transform 타겟 존재                                            │
│  ├── 3D Scene 클래스 일치                                           │
│  └── 카메라 설정                                                    │
│                                                                     │
│  Phase 3: 타이밍 검증                                                │
│  ├── wait_tag 주석                                                  │
│  └── 총 시간 일치                                                   │
│                                                                     │
│  Phase 4: 스타일 검증                                                │
│  ├── 컬러 팔레트 준수                                               │
│  └── 스타일/난이도별 제약                                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Phase 0: 파이프라인 일관성 검증 (NEW!)

### 목적

Scene Director → Visual Prompter → Manim Coder 간 데이터가 **누락이나 불일치 없이** 전달되었는지 검증합니다.

---

### A. Scene Director → Visual Prompter 검증

#### 체크 항목 1: required_elements 커버리지

Scene Director의 `required_elements`가 Visual Prompter의 `objects`에 모두 있는지 확인합니다.

```python
def check_required_elements_coverage(sd, vp):
    """
    Scene Director의 required_elements가 Visual Prompter objects에 모두 있는지
    """
    errors = []

    for elem in sd["required_elements"]:
        elem_type = elem["type"]

        if elem_type == "image":
            # 이미지: asset 파일명으로 확인
            asset_name = elem["asset"]
            found = any(
                asset_name in obj.get("source", "")
                for obj in vp["objects"]
            )
            if not found:
                errors.append({
                    "type": "ELEMENT_NOT_FOUND",
                    "phase": "SD→VP",
                    "message": f"required_elements의 이미지 '{asset_name}'이 Visual Prompter objects에 없음",
                    "severity": "ERROR"
                })

        elif elem_type == "math":
            # 수식: content로 확인 (일부 일치)
            content = elem["content"]
            found = any(
                obj.get("type") == "MathTex" and (
                    content in obj.get("content", "") or
                    any(content in p.get("tex", "") for p in obj.get("tex_parts", []))
                )
                for obj in vp["objects"]
            )
            if not found:
                errors.append({
                    "type": "ELEMENT_NOT_FOUND",
                    "phase": "SD→VP",
                    "message": f"required_elements의 수식 '{content}'이 Visual Prompter objects에 없음",
                    "severity": "WARNING"  # 수식은 변형될 수 있어 WARNING
                })

        elif elem_type == "text":
            # 텍스트: content로 확인
            content = elem["content"]
            found = any(
                obj.get("type") == "Text" and content in obj.get("content", "")
                for obj in vp["objects"]
            )
            if not found:
                errors.append({
                    "type": "ELEMENT_NOT_FOUND",
                    "phase": "SD→VP",
                    "message": f"required_elements의 텍스트 '{content}'이 Visual Prompter objects에 없음",
                    "severity": "WARNING"
                })

        elif elem_type == "3d_object":
            # 3D 객체: shape으로 확인
            shape = elem["shape"]
            shape_map = {
                "cube": "Cube",
                "cylinder": "Cylinder",
                "sphere": "Sphere",
                "cone": "Cone"
            }
            manim_type = shape_map.get(shape.lower(), shape)
            found = any(
                obj.get("type") == manim_type
                for obj in vp["objects"]
            )
            if not found:
                errors.append({
                    "type": "ELEMENT_NOT_FOUND",
                    "phase": "SD→VP",
                    "message": f"required_elements의 3D 객체 '{shape}'이 Visual Prompter objects에 없음",
                    "severity": "ERROR"
                })

    return errors
```

#### 체크 항목 2: wow_moment 구현 확인

Scene Director의 `wow_moment`가 Visual Prompter `sequence`에 강조 애니메이션으로 구현되었는지 확인합니다.

```python
def check_wow_moment_implementation(sd, vp):
    """
    wow_moment에 대응하는 강조 애니메이션(Indicate/Flash/Circumscribe)이 있는지
    """
    warnings = []

    wow_moment = sd.get("wow_moment")
    if not wow_moment:
        return warnings  # wow_moment가 없으면 통과

    emphasis_animations = ["Indicate", "Flash", "Circumscribe", "Wiggle", "ApplyWave"]

    has_emphasis = any(
        action.get("type") in emphasis_animations
        for step in vp.get("sequence", [])
        for action in step.get("actions", [])
    )

    if not has_emphasis:
        warnings.append({
            "type": "WOW_MOMENT_NOT_IMPLEMENTED",
            "phase": "SD→VP",
            "message": f"wow_moment '{wow_moment}'에 대한 강조 애니메이션 없음 (Indicate/Flash 권장)",
            "severity": "WARNING"
        })

    return warnings
```

#### 체크 항목 3: is_3d / scene_class 일치

```python
def check_3d_consistency_sd_vp(sd, vp):
    """
    Scene Director와 Visual Prompter의 is_3d, scene_class 일치 확인
    """
    errors = []

    if sd["is_3d"] != vp["is_3d"]:
        errors.append({
            "type": "3D_FLAG_MISMATCH",
            "phase": "SD→VP",
            "message": f"is_3d 불일치: Scene Director={sd['is_3d']}, Visual Prompter={vp['is_3d']}",
            "severity": "ERROR"
        })

    if sd["scene_class"] != vp["scene_class"]:
        errors.append({
            "type": "SCENE_CLASS_MISMATCH",
            "phase": "SD→VP",
            "message": f"scene_class 불일치: Scene Director={sd['scene_class']}, Visual Prompter={vp['scene_class']}",
            "severity": "ERROR"
        })

    return errors
```

#### 체크 항목 4: required_assets → objects[].source

```python
def check_assets_in_objects(sd, vp):
    """
    required_assets의 파일들이 objects[].source에 있는지
    """
    errors = []

    for asset in sd.get("required_assets", []):
        filename = asset["filename"]
        category = asset["category"]
        expected_path_part = f"assets/{category}/{filename}"

        found = any(
            expected_path_part in obj.get("source", "")
            for obj in vp["objects"]
            if obj.get("type") == "ImageMobject"
        )

        if not found:
            errors.append({
                "type": "ASSET_NOT_USED",
                "phase": "SD→VP",
                "message": f"required_assets '{filename}'이 Visual Prompter에서 사용되지 않음",
                "severity": "ERROR"
            })

    return errors
```

#### 체크 항목 5: style → canvas.background 일치

```python
def check_style_background(sd, vp):
    """
    style에 맞는 canvas.background가 설정되었는지
    """
    errors = []

    style_backgrounds = {
        "minimal": "#000000",
        "cyberpunk": "#0a0a1a",
        "space": "#000011",
        "geometric": "#1a1a1a",
        "stickman": "#1a2a3a",
        "paper": "#f5f5dc"
    }

    style = sd.get("style", "minimal")
    expected_bg = style_backgrounds.get(style)
    actual_bg = vp.get("canvas", {}).get("background")

    if expected_bg and actual_bg and expected_bg.lower() != actual_bg.lower():
        errors.append({
            "type": "BACKGROUND_MISMATCH",
            "phase": "SD→VP",
            "message": f"style '{style}'의 배경색은 {expected_bg}이어야 하나, {actual_bg}로 설정됨",
            "severity": "WARNING"
        })

    return errors
```

---

### B. Visual Prompter → Manim Coder 검증

#### 체크 항목 1: objects[] 모두 코드에 생성되었는지

```python
def check_objects_implemented(vp, code):
    """
    Visual Prompter의 모든 objects가 코드에서 변수로 생성되었는지
    """
    errors = []

    for obj in vp["objects"]:
        obj_id = obj["id"]

        # 변수 할당 패턴: obj_id = ... 또는 obj_id= ...
        pattern = rf'\b{obj_id}\s*='
        if not re.search(pattern, code):
            errors.append({
                "type": "OBJECT_NOT_IMPLEMENTED",
                "phase": "VP→Code",
                "message": f"Visual Prompter의 객체 '{obj_id}'가 코드에서 생성되지 않음",
                "severity": "ERROR"
            })

    return errors
```

#### 체크 항목 2: objects[].type에 맞는 Manim 클래스 사용

```python
def check_object_types(vp, code):
    """
    objects[].type에 맞는 Manim 클래스가 사용되었는지
    """
    errors = []

    type_class_map = {
        "ImageMobject": "ImageMobject",
        "Text": "Text",
        "MathTex": "MathTex",
        "Cube": "Cube",
        "Cylinder": "Cylinder",
        "Sphere": "Sphere",
        "Cone": "Cone",
        "Axes": "Axes",
        "NumberPlane": "NumberPlane"
    }

    for obj in vp["objects"]:
        obj_id = obj["id"]
        obj_type = obj["type"]
        expected_class = type_class_map.get(obj_type, obj_type)

        # 패턴: obj_id = ExpectedClass(
        pattern = rf'{obj_id}\s*=\s*{expected_class}\s*\('
        if not re.search(pattern, code):
            # 좀 더 유연한 검색 (VGroup 등으로 감싸진 경우)
            pattern_loose = rf'{expected_class}\s*\('
            if expected_class not in code:
                errors.append({
                    "type": "WRONG_CLASS_USED",
                    "phase": "VP→Code",
                    "message": f"객체 '{obj_id}'가 {expected_class}로 생성되지 않았을 수 있음",
                    "severity": "WARNING"
                })

    return errors
```

#### 체크 항목 3: sequence[].actions 모두 구현되었는지

```python
def check_sequence_implemented(vp, code):
    """
    Visual Prompter의 sequence actions가 코드에 구현되었는지
    """
    warnings = []

    for step in vp.get("sequence", []):
        step_num = step["step"]

        for action in step.get("actions", []):
            action_type = action.get("type")
            target = action.get("target", "")

            if action_type == "wait":
                # self.wait( 확인
                if "self.wait(" not in code:
                    warnings.append({
                        "type": "WAIT_MISSING",
                        "phase": "VP→Code",
                        "message": f"Step {step_num}의 wait 액션이 코드에 없을 수 있음",
                        "severity": "WARNING"
                    })
            else:
                # self.play(...ActionType...) 확인
                if action_type not in code:
                    warnings.append({
                        "type": "ACTION_POSSIBLY_MISSING",
                        "phase": "VP→Code",
                        "message": f"Step {step_num}의 {action_type}({target}) 애니메이션 확인 필요",
                        "severity": "WARNING"
                    })

    return warnings
```

#### 체크 항목 4: tex_parts 색상이 set_color()로 구현되었는지

```python
def check_tex_parts_colors(vp, code):
    """
    tex_parts의 색상이 [index].set_color()로 구현되었는지
    """
    warnings = []

    for obj in vp["objects"]:
        if "tex_parts" not in obj:
            continue

        obj_id = obj["id"]
        tex_parts = obj["tex_parts"]

        # tex_parts가 있으면 인덱스별 set_color 확인
        for i, part in enumerate(tex_parts):
            color = part.get("color")
            if color:
                # 패턴: obj_id[i].set_color(
                pattern = rf'{obj_id}\[{i}\]\.set_color\('
                if not re.search(pattern, code):
                    warnings.append({
                        "type": "TEX_COLOR_NOT_SET",
                        "phase": "VP→Code",
                        "message": f"{obj_id}[{i}]의 색상 {color}이 set_color()로 설정되지 않았을 수 있음",
                        "severity": "WARNING"
                    })

    return warnings
```

#### 체크 항목 5: fixed_in_frame 처리 확인 (3D 씬)

```python
def check_fixed_in_frame(vp, code):
    """
    3D 씬에서 fixed_in_frame: true인 객체가 add_fixed_in_frame_mobjects()로 처리되었는지
    """
    errors = []

    if not vp.get("is_3d"):
        return errors  # 2D 씬이면 통과

    for obj in vp["objects"]:
        if obj.get("fixed_in_frame"):
            obj_id = obj["id"]

            # add_fixed_in_frame_mobjects(obj_id) 또는 self.add_fixed_in_frame_mobjects(obj_id)
            pattern = rf'add_fixed_in_frame_mobjects\s*\([^)]*{obj_id}'
            if not re.search(pattern, code):
                errors.append({
                    "type": "FIXED_IN_FRAME_MISSING",
                    "phase": "VP→Code",
                    "message": f"3D 씬의 '{obj_id}'에 add_fixed_in_frame_mobjects() 누락",
                    "severity": "ERROR"
                })

    return errors
```

#### 체크 항목 6: position 변환 확인

```python
def check_position_conversion(vp, code):
    """
    position의 method(shift/to_edge/next_to)가 올바르게 변환되었는지
    """
    warnings = []

    for obj in vp["objects"]:
        obj_id = obj["id"]
        position = obj.get("position", {})
        method = position.get("method")

        if method == "shift":
            # shift, move_to, LEFT, RIGHT 등 확인
            if not re.search(rf'{obj_id}[^=]*\.(shift|move_to)\s*\(', code):
                # 직접 좌표 할당도 가능하므로 WARNING
                pass  # 너무 엄격하면 많은 false positive

        elif method == "to_edge":
            edge = position.get("edge", "").upper()
            if edge and f".to_edge({edge}" not in code and f".to_edge( {edge}" not in code:
                warnings.append({
                    "type": "POSITION_METHOD_MISMATCH",
                    "phase": "VP→Code",
                    "message": f"'{obj_id}'의 to_edge({edge}) 변환 확인 필요",
                    "severity": "WARNING"
                })

        elif method == "next_to":
            anchor = position.get("anchor", "")
            if anchor and f".next_to({anchor}" not in code and f".next_to( {anchor}" not in code:
                warnings.append({
                    "type": "POSITION_METHOD_MISMATCH",
                    "phase": "VP→Code",
                    "message": f"'{obj_id}'의 next_to({anchor}) 변환 확인 필요",
                    "severity": "WARNING"
                })

    return warnings
```

---

### C. timing.json ↔ 코드 검증

#### 체크 항목 1: total_duration vs 코드 총 시간

```python
def check_total_duration_match(timing, code, tolerance=0.1):
    """
    timing.json의 total_duration과 코드의 총 애니메이션 시간 비교
    허용 오차: ±10%
    """
    errors = []

    target_time = timing["total_duration"]
    code_time = calculate_total_time(code)

    diff = abs(code_time - target_time)
    max_diff = target_time * tolerance

    if diff > max_diff:
        diff_percent = (diff / target_time) * 100
        errors.append({
            "type": "DURATION_MISMATCH",
            "phase": "Timing",
            "message": f"시간 불일치: timing.json={target_time:.1f}s, 코드={code_time:.1f}s (차이: {diff_percent:.1f}%)",
            "severity": "ERROR" if diff_percent > 20 else "WARNING",
            "suggestion": f"self.wait({target_time - code_time:.2f}) 추가 필요" if code_time < target_time else "run_time 조정 필요"
        })

    return errors


def calculate_total_time(code):
    """
    코드에서 총 애니메이션 시간 추출
    """
    import re
    total = 0.0

    # run_time 추출
    run_times = re.findall(r'run_time\s*=\s*([0-9.]+)', code)
    total += sum(float(t) for t in run_times)

    # wait() 추출
    waits = re.findall(r'self\.wait\s*\(\s*([0-9.]+)\s*\)', code)
    total += sum(float(w) for w in waits)

    # run_time 없는 play() (기본 1초)
    # self.play(...)가 있고, 같은 줄에 run_time이 없는 경우
    plays = re.findall(r'self\.play\s*\([^)]+\)', code)
    for play in plays:
        if 'run_time' not in play:
            total += 1.0

    return total
```

#### 체크 항목 2: sequence time_range와 코드 동기화

```python
def check_sequence_timing(vp, code):
    """
    Visual Prompter sequence의 time_range 합계와 코드 시간 비교
    """
    warnings = []

    sequence = vp.get("sequence", [])
    if not sequence:
        return warnings

    # sequence의 총 시간 (마지막 step의 time_range[1])
    last_step = sequence[-1]
    vp_total = last_step.get("time_range", [0, 0])[1]

    # 코드의 총 시간
    code_total = calculate_total_time(code)

    diff = abs(code_total - vp_total)
    if diff > vp_total * 0.15:  # 15% 이상 차이
        warnings.append({
            "type": "SEQUENCE_TIMING_DRIFT",
            "phase": "Timing",
            "message": f"Visual Prompter sequence 총 시간({vp_total:.1f}s)과 코드 시간({code_total:.1f}s) 불일치",
            "severity": "WARNING"
        })

    return warnings
```

---

## Phase 1: 문법 검증

### A. MathTex 검증

#### 체크 항목 1: r-string 사용

```python
def check_mathtex_r_string(code):
    """
    MathTex에서 r-string 사용 확인
    """
    errors = []

    # MathTex("...") 패턴 (r이 없는 경우)
    pattern = r'MathTex\s*\(\s*"(?!r)'
    matches = re.finditer(pattern, code)

    for match in matches:
        errors.append({
            "type": "MISSING_R_STRING",
            "phase": "Syntax",
            "message": "MathTex에 r-string 누락",
            "line": code[:match.start()].count('\n') + 1,
            "suggestion": 'MathTex("...") → MathTex(r"...")',
            "severity": "ERROR",
            "auto_fixable": True
        })

    return errors
```

#### 체크 항목 2: 중괄호 짝 맞추기

```python
def check_mathtex_braces(code):
    """
    MathTex 내 LaTeX 중괄호 짝 확인
    """
    errors = []

    # MathTex 내용 추출
    pattern = r'MathTex\s*\(\s*r?"([^"]+)"'
    matches = re.finditer(pattern, code)

    for match in matches:
        latex_content = match.group(1)
        open_count = latex_content.count('{')
        close_count = latex_content.count('}')

        if open_count != close_count:
            errors.append({
                "type": "BRACE_MISMATCH",
                "phase": "Syntax",
                "message": f"LaTeX 중괄호 불일치: {{ {open_count}개, }} {close_count}개",
                "line": code[:match.start()].count('\n') + 1,
                "severity": "ERROR",
                "auto_fixable": False
            })

    return errors
```

### B. Text 검증

#### 체크 항목: 한글 폰트

```python
def check_text_korean_font(code):
    """
    한글 포함 Text에 font="Noto Sans KR" 확인
    """
    errors = []

    # Text("한글이 포함된 내용") 패턴
    pattern = r'Text\s*\(\s*["\']([^"\']*[가-힣]+[^"\']*)["\']'
    matches = re.finditer(pattern, code)

    for match in matches:
        # 같은 Text() 호출에 font= 가 있는지 확인
        # match 위치부터 다음 ) 까지 확인
        start = match.start()
        # 간단히: 해당 줄에 font= 가 있는지
        line_start = code.rfind('\n', 0, start) + 1
        line_end = code.find('\n', start)
        line = code[line_start:line_end]

        if 'font=' not in line and 'font =' not in line:
            errors.append({
                "type": "MISSING_KOREAN_FONT",
                "phase": "Syntax",
                "message": f"한글 Text에 font 누락: '{match.group(1)[:20]}...'",
                "line": code[:start].count('\n') + 1,
                "suggestion": 'Text("한글", font="Noto Sans KR")',
                "severity": "ERROR",
                "auto_fixable": True
            })

    return errors
```

### C. always_redraw 검증

```python
def check_always_redraw_lambda(code):
    """
    always_redraw에 lambda 함수 사용 확인
    """
    errors = []

    # always_redraw( 다음에 lambda가 아닌 경우
    pattern = r'always_redraw\s*\(\s*(?!lambda)'
    matches = re.finditer(pattern, code)

    for match in matches:
        # lambda가 아닌 경우 (주석이나 다른 패턴 제외)
        after_paren = code[match.end():match.end()+20]
        if not after_paren.strip().startswith('lambda') and not after_paren.strip().startswith('#'):
            errors.append({
                "type": "MISSING_LAMBDA",
                "phase": "Syntax",
                "message": "always_redraw에 lambda 함수 누락",
                "line": code[:match.start()].count('\n') + 1,
                "suggestion": "always_redraw(lambda: ...)",
                "severity": "ERROR",
                "auto_fixable": False
            })

    return errors
```

---

## Phase 2: 로직 검증

### A. Transform 타겟 존재 확인

```python
def check_transform_targets(code):
    """
    Transform/ReplacementTransform의 타겟 객체가 존재하는지
    """
    errors = []

    # 정의된 변수들 추출
    defined_vars = set(re.findall(r'(\w+)\s*=\s*(?:MathTex|Text|ImageMobject|VGroup|Cube)', code))

    # Transform(a, b) 패턴에서 b가 정의되었는지
    transform_pattern = r'(?:Transform|ReplacementTransform)\s*\(\s*(\w+)\s*,\s*(\w+)'
    matches = re.finditer(transform_pattern, code)

    for match in matches:
        source, target = match.group(1), match.group(2)
        if target not in defined_vars:
            errors.append({
                "type": "UNDEFINED_TRANSFORM_TARGET",
                "phase": "Logic",
                "message": f"Transform 타겟 '{target}'이 정의되지 않음",
                "line": code[:match.start()].count('\n') + 1,
                "severity": "ERROR"
            })

    return errors
```

### B. 3D Scene 클래스 일치

```python
def check_3d_scene_class(code, vp):
    """
    3D 객체 사용 시 ThreeDScene 클래스 사용 확인
    """
    errors = []

    three_d_objects = ['Cube(', 'Cylinder(', 'Sphere(', 'Cone(', 'Surface(', 'ThreeDAxes(']
    has_3d_objects = any(obj in code for obj in three_d_objects)
    uses_3d_scene = 'ThreeDScene' in code

    # Visual Prompter의 is_3d 확인
    vp_is_3d = vp.get("is_3d", False)

    if has_3d_objects and not uses_3d_scene:
        errors.append({
            "type": "3D_SCENE_CLASS_MISSING",
            "phase": "Logic",
            "message": "3D 객체 사용 시 ThreeDScene 클래스 필수",
            "suggestion": "class SceneX(Scene): → class SceneX(ThreeDScene):",
            "severity": "ERROR",
            "auto_fixable": True
        })

    if vp_is_3d and not uses_3d_scene:
        errors.append({
            "type": "VP_3D_MISMATCH",
            "phase": "Logic",
            "message": "Visual Prompter는 3D 씬인데 코드는 일반 Scene 사용",
            "severity": "ERROR",
            "auto_fixable": True
        })

    return errors
```

### C. 카메라 설정 확인

```python
def check_camera_orientation(code):
    """
    ThreeDScene에서 카메라 설정 확인
    """
    errors = []

    if 'ThreeDScene' in code:
        if 'set_camera_orientation' not in code:
            errors.append({
                "type": "CAMERA_SETUP_MISSING",
                "phase": "Logic",
                "message": "ThreeDScene에서 카메라 설정 누락 (정면 뷰는 2D처럼 보임)",
                "suggestion": "self.set_camera_orientation(phi=60*DEGREES, theta=-45*DEGREES)",
                "severity": "WARNING",
                "auto_fixable": True
            })

        # DEGREES 사용 확인
        if 'set_camera_orientation' in code and 'DEGREES' not in code:
            errors.append({
                "type": "DEGREES_MISSING",
                "phase": "Logic",
                "message": "카메라 각도에 DEGREES 누락",
                "suggestion": "phi=60*DEGREES, theta=-45*DEGREES",
                "severity": "ERROR"
            })

    return errors
```

### D. Cube vs Square 혼동

```python
def check_cube_vs_square(code, vp):
    """
    is_3d: true인 씬에서 Square 대신 Cube 사용 확인
    """
    errors = []

    if vp.get("is_3d") and 'Square(' in code:
        errors.append({
            "type": "WRONG_2D_OBJECT_IN_3D",
            "phase": "Logic",
            "message": "3D 씬에서 Square() 사용됨 - Cube() 사용 권장",
            "suggestion": "Square(side_length=2) → Cube(side_length=2)",
            "severity": "WARNING",
            "auto_fixable": True
        })

    return errors
```

---

## Phase 3: 타이밍 검증

### A. wait_tag 검증

#### 체크 항목 1: 모든 wait()에 주석

```python
def check_wait_tags(code, scene_id):
    """
    모든 self.wait()와 self.play()에 wait_tag 주석 확인
    """
    errors = []

    # self.wait(...) 뒤에 # wait_tag 없는 경우
    wait_pattern = r'self\.wait\s*\([^)]+\)(?!\s*#\s*wait_tag)'
    matches = re.finditer(wait_pattern, code)

    for match in matches:
        errors.append({
            "type": "MISSING_WAIT_TAG",
            "phase": "Timing",
            "message": "wait()에 wait_tag 주석 누락",
            "line": code[:match.start()].count('\n') + 1,
            "suggestion": f"self.wait(...)  # wait_tag_{scene_id}_N",
            "severity": "ERROR",
            "auto_fixable": True
        })

    # self.play(...) 뒤에 # wait_tag 없는 경우
    play_pattern = r'self\.play\s*\([^)]+\)(?!\s*#\s*wait_tag)'
    matches = re.finditer(play_pattern, code)

    for match in matches:
        errors.append({
            "type": "MISSING_WAIT_TAG",
            "phase": "Timing",
            "message": "play()에 wait_tag 주석 누락",
            "line": code[:match.start()].count('\n') + 1,
            "suggestion": f"self.play(...)  # wait_tag_{scene_id}_N",
            "severity": "ERROR",
            "auto_fixable": True
        })

    return errors
```

#### 체크 항목 2: 태그 중복 확인

```python
def check_duplicate_tags(code):
    """
    wait_tag 중복 확인
    """
    errors = []

    # wait_tag_sX_Y 패턴 추출
    tags = re.findall(r'wait_tag_s\d+_\d+', code)

    seen = set()
    for tag in tags:
        if tag in seen:
            errors.append({
                "type": "DUPLICATE_WAIT_TAG",
                "phase": "Timing",
                "message": f"wait_tag 중복: {tag}",
                "severity": "ERROR"
            })
        seen.add(tag)

    return errors
```

---

## Phase 4: 스타일 검증

### A. 컬러 팔레트 준수

```python
def check_color_palette(code, style):
    """
    스타일에 맞는 컬러 팔레트 사용 확인
    """
    warnings = []

    # 어두운 배경 스타일
    dark_styles = ["minimal", "cyberpunk", "space", "geometric", "stickman"]
    # 밝은 배경 스타일
    light_styles = ["paper"]

    # 권장 색상
    dark_palette = ["WHITE", "YELLOW", "ORANGE", "GREEN", "RED", "GRAY_B", "CYAN", "BLUE"]
    light_palette = ["BLACK", "DARK_BLUE", "DARK_BROWN", "DARK_GREEN"]

    if style in light_styles:
        # 밝은 배경에서 WHITE 사용은 비권장
        if 'color=WHITE' in code or 'color = WHITE' in code:
            warnings.append({
                "type": "COLOR_VISIBILITY",
                "phase": "Style",
                "message": f"밝은 배경 스타일 '{style}'에서 WHITE 색상 사용 - 가시성 문제",
                "severity": "WARNING"
            })

    return warnings
```

### B. 스타일별 효과 확인

```python
def check_style_effects(code, style):
    """
    스타일별 필수/권장 효과 확인
    """
    warnings = []

    if style == "cyberpunk":
        # 글로우 효과 권장
        if 'set_stroke' not in code and 'glow' not in code.lower():
            warnings.append({
                "type": "STYLE_EFFECT_MISSING",
                "phase": "Style",
                "message": "cyberpunk 스타일에서 글로우 효과(set_stroke) 권장",
                "severity": "WARNING"
            })

    return warnings
```

---

## 자동 수정 패턴

### 패턴 1: r-string 추가

```python
def fix_mathtex_r_string(code):
    """
    MathTex("...") → MathTex(r"...")
    """
    # MathTex(" 를 MathTex(r" 로 변환 (이미 r이 있는 경우 제외)
    pattern = r'MathTex\s*\(\s*"(?!r)'

    def replace(match):
        return match.group(0).replace('MathTex("', 'MathTex(r"').replace("MathTex('", "MathTex(r'")

    return re.sub(pattern, lambda m: m.group(0).replace('"', 'r"', 1), code)
```

### 패턴 2: 한글 폰트 추가

```python
def fix_korean_font(code):
    """
    Text("한글") → Text("한글", font="Noto Sans KR")
    """
    # 한글 포함 Text에 font가 없는 경우
    pattern = r'Text\s*\(\s*(["\'])([^"\']*[가-힣]+[^"\']*)\1\s*\)'

    def replace(match):
        quote = match.group(1)
        content = match.group(2)
        return f'Text({quote}{content}{quote}, font="Noto Sans KR")'

    return re.sub(pattern, replace, code)
```

### 패턴 3: wait_tag 추가

```python
def fix_wait_tags(code, scene_id):
    """
    wait_tag 주석 자동 추가
    """
    lines = code.split('\n')
    tag_count = 0

    for i, line in enumerate(lines):
        # self.wait() 또는 self.play()가 있고 wait_tag가 없는 경우
        if ('self.wait(' in line or 'self.play(' in line) and 'wait_tag' not in line:
            tag_count += 1
            lines[i] = line.rstrip() + f"  # wait_tag_{scene_id}_{tag_count}"

    return '\n'.join(lines)
```

### 패턴 4: 3D Scene 클래스 수정

```python
def fix_3d_scene_class(code):
    """
    3D 객체 사용 시 Scene → ThreeDScene 변환
    """
    three_d_objects = ['Cube(', 'Cylinder(', 'Sphere(', 'Cone(', 'Surface(']
    has_3d = any(obj in code for obj in three_d_objects)

    if has_3d and 'ThreeDScene' not in code:
        # class SceneX(Scene): → class SceneX(ThreeDScene):
        code = re.sub(
            r'class\s+(\w+)\s*\(\s*Scene\s*\)\s*:',
            r'class \1(ThreeDScene):',
            code
        )

        # 카메라 설정 추가
        if 'set_camera_orientation' not in code:
            code = re.sub(
                r'(def construct\s*\(\s*self\s*\)\s*:)',
                r'\1\n        self.set_camera_orientation(phi=60*DEGREES, theta=-45*DEGREES)',
                code
            )

    return code
```

### 패턴 5: 타이밍 보정

```python
def fix_timing(code, target_duration):
    """
    총 시간이 부족하면 마지막에 wait 추가
    """
    current_time = calculate_total_time(code)

    if current_time < target_duration:
        diff = target_duration - current_time

        # construct() 끝에 wait 추가
        # 마지막 self.wait 또는 self.play 찾기
        last_action = max(
            code.rfind('self.wait'),
            code.rfind('self.play')
        )

        if last_action > 0:
            # 해당 줄 끝에 추가하지 않고, 다음 줄에 추가
            line_end = code.find('\n', last_action)
            if line_end > 0:
                scene_id = re.search(r'wait_tag_(s\d+)', code)
                scene_id = scene_id.group(1) if scene_id else "s1"

                # 기존 태그 개수 확인
                existing_tags = len(re.findall(rf'wait_tag_{scene_id}_\d+', code))

                correction = f"\n        self.wait({diff:.2f})  # wait_tag_{scene_id}_{existing_tags + 1}_sync"
                code = code[:line_end] + correction + code[line_end:]

    return code
```

---

## 통합 검증 클래스

```python
import re

class CodeValidator:
    """
    Manim 코드 검증 및 파이프라인 일관성 검증 통합 클래스
    """

    def __init__(self, scene_director, visual_prompter, manim_code, timing):
        """
        Args:
            scene_director: scenes.json의 해당 씬 데이터
            visual_prompter: s#_visual.json 데이터
            manim_code: s#_manim.py 코드 문자열
            timing: s#_timing.json 데이터
        """
        self.sd = scene_director
        self.vp = visual_prompter
        self.code = manim_code
        self.timing = timing

        self.scene_id = self.sd.get("scene_id", "s1")
        self.style = self.sd.get("style", "minimal")

        self.errors = []
        self.warnings = []

    def validate_all(self):
        """전체 검증 실행"""

        # Phase 0: 파이프라인 일관성
        self._phase0_pipeline_consistency()

        # Phase 1: 문법
        self._phase1_syntax()

        # Phase 2: 로직
        self._phase2_logic()

        # Phase 3: 타이밍
        self._phase3_timing()

        # Phase 4: 스타일
        self._phase4_style()

        return {
            "status": "OK" if not self.errors else "FAILED",
            "errors": self.errors,
            "warnings": self.warnings,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings)
        }

    def _phase0_pipeline_consistency(self):
        """Phase 0: 파이프라인 일관성 검증"""
        # A. Scene Director → Visual Prompter
        self.errors.extend(check_required_elements_coverage(self.sd, self.vp))
        self.warnings.extend(check_wow_moment_implementation(self.sd, self.vp))
        self.errors.extend(check_3d_consistency_sd_vp(self.sd, self.vp))
        self.errors.extend(check_assets_in_objects(self.sd, self.vp))
        self.warnings.extend(check_style_background(self.sd, self.vp))

        # B. Visual Prompter → Manim Coder
        self.errors.extend(check_objects_implemented(self.vp, self.code))
        self.warnings.extend(check_object_types(self.vp, self.code))
        self.warnings.extend(check_sequence_implemented(self.vp, self.code))
        self.warnings.extend(check_tex_parts_colors(self.vp, self.code))
        self.errors.extend(check_fixed_in_frame(self.vp, self.code))
        self.warnings.extend(check_position_conversion(self.vp, self.code))

        # C. Timing
        self.errors.extend(check_total_duration_match(self.timing, self.code))
        self.warnings.extend(check_sequence_timing(self.vp, self.code))

    def _phase1_syntax(self):
        """Phase 1: 문법 검증"""
        self.errors.extend(check_mathtex_r_string(self.code))
        self.errors.extend(check_mathtex_braces(self.code))
        self.errors.extend(check_text_korean_font(self.code))
        self.errors.extend(check_always_redraw_lambda(self.code))

    def _phase2_logic(self):
        """Phase 2: 로직 검증"""
        self.errors.extend(check_transform_targets(self.code))
        self.errors.extend(check_3d_scene_class(self.code, self.vp))
        self.errors.extend(check_camera_orientation(self.code))
        self.errors.extend(check_cube_vs_square(self.code, self.vp))

    def _phase3_timing(self):
        """Phase 3: 타이밍 검증"""
        self.errors.extend(check_wait_tags(self.code, self.scene_id))
        self.errors.extend(check_duplicate_tags(self.code))

    def _phase4_style(self):
        """Phase 4: 스타일 검증"""
        self.warnings.extend(check_color_palette(self.code, self.style))
        self.warnings.extend(check_style_effects(self.code, self.style))

    def auto_fix(self):
        """자동 수정 가능한 오류 수정"""
        fixed_code = self.code

        # 자동 수정 적용
        fixed_code = fix_mathtex_r_string(fixed_code)
        fixed_code = fix_korean_font(fixed_code)
        fixed_code = fix_wait_tags(fixed_code, self.scene_id)
        fixed_code = fix_3d_scene_class(fixed_code)
        fixed_code = fix_timing(fixed_code, self.timing["total_duration"])

        return fixed_code
```

---

## 출력 형식

### 검증 결과 예시

```json
{
  "status": "FAILED",
  "error_count": 3,
  "warning_count": 5,
  "errors": [
    {
      "type": "ELEMENT_NOT_FOUND",
      "phase": "SD→VP",
      "message": "required_elements의 이미지 'snack_bag_shrunk.png'이 Visual Prompter objects에 없음",
      "severity": "ERROR"
    },
    {
      "type": "OBJECT_NOT_IMPLEMENTED",
      "phase": "VP→Code",
      "message": "Visual Prompter의 객체 'equation'가 코드에서 생성되지 않음",
      "severity": "ERROR"
    },
    {
      "type": "MISSING_WAIT_TAG",
      "phase": "Timing",
      "message": "wait()에 wait_tag 주석 누락",
      "line": 25,
      "severity": "ERROR",
      "auto_fixable": true
    }
  ],
  "warnings": [
    {
      "type": "WOW_MOMENT_NOT_IMPLEMENTED",
      "phase": "SD→VP",
      "message": "wow_moment '줄어든 과자가 등장하는 순간'에 대한 강조 애니메이션 없음",
      "severity": "WARNING"
    },
    {
      "type": "TEX_COLOR_NOT_SET",
      "phase": "VP→Code",
      "message": "equation[0]의 색상 YELLOW이 set_color()로 설정되지 않았을 수 있음",
      "severity": "WARNING"
    }
  ]
}
```

### 자동 수정 결과 예시

```json
{
  "status": "FIXED",
  "original_errors": 5,
  "auto_fixed": 3,
  "remaining_errors": 2,
  "fixed_code": "..."
}
```

---

## 검증 체크리스트

### Phase 0: 파이프라인 일관성

#### A. Scene Director → Visual Prompter

- [ ] required_elements의 모든 요소가 objects에 있는가?
- [ ] wow_moment에 대응하는 강조 애니메이션(Indicate/Flash)이 있는가?
- [ ] is_3d 값이 일치하는가?
- [ ] scene_class 값이 일치하는가?
- [ ] required_assets의 파일들이 objects[].source에 있는가?
- [ ] style에 맞는 canvas.background가 설정되었는가?

#### B. Visual Prompter → Manim Coder

- [ ] objects[]의 모든 id가 코드에서 변수로 생성되었는가?
- [ ] objects[].type에 맞는 Manim 클래스를 사용했는가?
- [ ] sequence[].actions의 모든 액션이 코드에 구현되었는가?
- [ ] tex_parts의 각 부분에 set_color()가 적용되었는가?
- [ ] fixed_in_frame: true인 객체에 add_fixed_in_frame_mobjects() 호출했는가?
- [ ] position의 method(shift/to_edge/next_to)가 올바르게 변환되었는가?

#### C. Timing 일관성

- [ ] timing.json의 total_duration과 코드 총 시간이 ±10% 이내인가?
- [ ] sequence[].time_range와 코드의 run_time 합계가 일치하는가?

### Phase 1: 문법

- [ ] 모든 MathTex에 r-string 사용
- [ ] LaTeX 중괄호 짝 맞음
- [ ] 모든 한글 Text에 font="Noto Sans KR"
- [ ] always_redraw에 lambda 함수 사용

### Phase 2: 로직

- [ ] Transform 타겟 객체가 정의되어 있음
- [ ] 3D 객체 사용 시 ThreeDScene 클래스 사용
- [ ] ThreeDScene에서 set_camera_orientation() 호출
- [ ] 3D 씬에서 Square 대신 Cube 사용

### Phase 3: 타이밍

- [ ] 모든 wait()/play()에 wait_tag 주석
- [ ] wait_tag 중복 없음
- [ ] 총 애니메이션 시간이 timing.json과 일치

### Phase 4: 스타일

- [ ] 스타일에 맞는 컬러 팔레트 사용
- [ ] cyberpunk 스타일에서 글로우 효과 적용

---

## 검증 우선순위

| 우선순위     | 유형              | 예시                                 | 대응        |
| ------------ | ----------------- | ------------------------------------ | ----------- |
| **Critical** | 파이프라인 불일치 | required_elements 누락, is_3d 불일치 | 재작성 필요 |
| **High**     | 문법 오류         | r-string 누락, 폰트 누락             | 자동 수정   |
| **Medium**   | 로직 오류         | Transform 타겟 미정의                | 수동 수정   |
| **Low**      | 스타일 경고       | 컬러 가시성, 글로우 효과             | 권장 사항   |

---

## 금지 사항

❌ Phase 0 검증 없이 코드만 검증
❌ 파이프라인 불일치 무시
❌ 치명적 오류(ERROR) 무시하고 통과
❌ 자동 수정 실패 시 원본 그대로 반환
❌ timing.json과 20% 이상 차이나는 코드 허용

---

## 작업 흐름 요약

```
1. 입력 파일 로드:
   ├── scenes.json → 해당 씬 추출
   ├── s#_visual.json
   ├── s#_manim.py
   └── s#_timing.json

2. Phase 0: 파이프라인 일관성 검증
   ├── Scene Director ↔ Visual Prompter
   ├── Visual Prompter ↔ Manim Coder
   └── timing.json ↔ 코드

3. Phase 1-4: 코드 자체 검증
   ├── 문법
   ├── 로직
   ├── 타이밍
   └── 스타일

4. 결과 출력:
   ├── errors (ERROR 레벨)
   ├── warnings (WARNING 레벨)
   └── status (OK / FAILED)

5. 자동 수정 (선택적):
   └── auto_fixable: true인 오류 자동 수정

6. 최종 판정:
   ├── errors = 0 → 통과
   ├── errors > 0, auto_fixable → 자동 수정 후 재검증
   └── errors > 0, not auto_fixable → 실패, 수동 수정 필요
```
