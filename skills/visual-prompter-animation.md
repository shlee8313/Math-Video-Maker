# Visual Prompter - Animation Stage

> **역할**: Layout의 객체들에 시간순 애니메이션 시퀀스 추가
> **입력**: s{n}_layout.json, s{n}_timing.json
> **출력**: s{n}_visual.json (objects + sequence 완성)

---

## 1. timing.json 구조

```json
{
  "scene_id": "s1",
  "total_duration": 12.5,
  "segments": [
    {
      "start": 0,
      "end": 4.2,
      "text": "동적 가격이란 무엇일까요?"
    },
    {
      "start": 4.2,
      "end": 8.5,
      "text": "같은 물건인데 가격이 달라지는 거죠"
    },
    {
      "start": 8.5,
      "end": 12.5,
      "text": "어떻게 이런 일이 가능할까요?"
    }
  ]
}
```

---

## 2. sequence 구조

```json
"sequence": [
  {
    "step": 1,
    "time_range": [0, 4.2],
    "sync_with": "동적 가격이란 무엇일까요?",
    "actions": [
      {
        "type": "FadeIn",
        "target": "title_text",
        "run_time": 0.8
      }
    ],
    "purpose": "제목 등장"
  }
]
```

### 필수 필드

| 필드 | 설명 |
|------|------|
| step | 순서 번호 (1, 2, 3...) |
| time_range | [시작초, 종료초] |
| sync_with | timing.json의 해당 text |
| actions | 애니메이션 배열 |
| purpose | 이 단계의 목적 |

---

## 3. 애니메이션 유형별 명세

### 3.1 등장 애니메이션

**FadeIn (페이드)**
```json
{
  "type": "FadeIn",
  "target": "stickman",
  "shift": "LEFT",
  "run_time": 0.6
}
```
- shift 옵션: UP, DOWN, LEFT, RIGHT (생략 가능)
- 권장 run_time: 0.5~0.8

**Write (텍스트 작성)**
```json
{
  "type": "Write",
  "target": "title_text",
  "run_time": 1.5
}
```
- 한 글자씩 나타남
- 권장 run_time: 글자수 * 0.1 (최소 1.0)

**Create (도형/선 그리기)**
```json
{
  "type": "Create",
  "target": "axes",
  "run_time": 1.0
}
```
- 선/도형이 그려지는 효과
- 권장 run_time: 0.8~1.5

**GrowFromCenter (중앙에서 커짐)**
```json
{
  "type": "GrowFromCenter",
  "target": "circle1",
  "run_time": 0.6
}
```
- 점에서 시작해서 전체 크기로 커짐
- 권장 run_time: 0.5~0.8

**DrawBorderThenFill (테두리 후 채우기)**
```json
{
  "type": "DrawBorderThenFill",
  "target": "icon1",
  "run_time": 0.8
}
```
- SVG 아이콘에 적합
- 권장 run_time: 0.6~1.0

**GrowArrow (화살표 성장)**
```json
{
  "type": "GrowArrow",
  "target": "arrow1",
  "run_time": 0.5
}
```
- 시작점에서 끝점으로 화살표 성장
- 권장 run_time: 0.4~0.6

**SpinInFromNothing (회전 등장)**
```json
{
  "type": "SpinInFromNothing",
  "target": "question_mark",
  "run_time": 0.8
}
```
- 회전하며 등장
- 아이콘, 기호에 적합

### 3.2 강조 애니메이션

**Indicate (깜빡임 강조)**
```json
{
  "type": "Indicate",
  "target": "result_text",
  "color": "YELLOW",
  "scale_factor": 1.2,
  "run_time": 0.8
}
```
- 색상 변화 + 크기 변화 후 원래대로
- 권장 run_time: 0.6~1.0

**Flash (번쩍임)**
```json
{
  "type": "Flash",
  "target": "answer",
  "color": "WHITE",
  "run_time": 0.5
}
```
- 밝게 번쩍
- 권장 run_time: 0.3~0.5

**Circumscribe (테두리 그리기)**
```json
{
  "type": "Circumscribe",
  "target": "key_formula",
  "color": "RED",
  "run_time": 1.0
}
```
- 객체 주변에 테두리 그렸다가 사라짐
- 권장 run_time: 0.8~1.2

**Wiggle (흔들림)**
```json
{
  "type": "Wiggle",
  "target": "warning_text",
  "run_time": 0.5
}
```
- 좌우로 흔들림
- 권장 run_time: 0.4~0.6

**FocusOn (포커스)**
```json
{
  "type": "FocusOn",
  "target": "important_obj",
  "run_time": 1.0
}
```
- 주변 어둡게 + 대상 강조
- 권장 run_time: 0.8~1.2

### 3.3 변환 애니메이션

**Transform (형태 변환)**
```json
{
  "type": "Transform",
  "target": "eq1",
  "to": "eq2",
  "run_time": 1.0
}
```
- 한 객체를 다른 객체로 변환
- 권장 run_time: 0.8~1.5

**ReplacementTransform (교체 변환)**
```json
{
  "type": "ReplacementTransform",
  "target": "old_text",
  "to": "new_text",
  "run_time": 0.8
}
```
- Transform과 유사하나 기존 객체 제거
- 권장 run_time: 0.6~1.0

**TransformMatchingTex (수식 부분 변환)**
```json
{
  "type": "TransformMatchingTex",
  "target": "equation1",
  "to": "equation2",
  "run_time": 1.5
}
```
- 수식에서 일치하는 부분만 유지하고 변환
- 권장 run_time: 1.0~2.0

**MoveToTarget (목표 위치로)**
```json
{
  "type": "MoveToTarget",
  "target": "moving_obj",
  "run_time": 0.8
}
```
- 객체가 설정된 target 위치로 이동
- 미리 target 설정 필요

### 3.4 퇴장 애니메이션

**FadeOut (페이드 아웃)**
```json
{
  "type": "FadeOut",
  "target": "old_content",
  "shift": "UP",
  "run_time": 0.5
}
```
- shift 옵션: UP, DOWN, LEFT, RIGHT
- 권장 run_time: 0.4~0.6

**Uncreate (역생성)**
```json
{
  "type": "Uncreate",
  "target": "line1",
  "run_time": 0.5
}
```
- Create의 역순
- 권장 run_time: 0.4~0.6

**ShrinkToCenter (중앙으로 축소)**
```json
{
  "type": "ShrinkToCenter",
  "target": "circle1",
  "run_time": 0.5
}
```
- 점으로 축소되며 사라짐
- 권장 run_time: 0.4~0.6

### 3.5 이동 애니메이션

**animate.shift (이동)**
```json
{
  "type": "animate.shift",
  "target": "object1",
  "direction": "RIGHT",
  "amount": 3,
  "run_time": 1.0
}
```
- 특정 방향으로 이동
- 권장 run_time: 0.6~1.0

**animate.move_to (특정 위치로)**
```json
{
  "type": "animate.move_to",
  "target": "object1",
  "position": {"x": 3, "y": 1},
  "run_time": 0.8
}
```
- 특정 좌표로 이동
- 권장 run_time: 0.6~1.0

**animate.scale (크기 변환)**
```json
{
  "type": "animate.scale",
  "target": "object1",
  "factor": 1.5,
  "run_time": 0.5
}
```
- 크기 배율 변경
- 권장 run_time: 0.4~0.6

### 3.6 속성 변환

**fade_opacity (투명도)**
```json
{
  "type": "fade_opacity",
  "target": "background_text",
  "to": 0.3,
  "run_time": 0.5
}
```
- 투명도 조절
- 권장 run_time: 0.3~0.5

**animate.set_color (색상 변경)**
```json
{
  "type": "animate.set_color",
  "target": "text1",
  "color": "RED",
  "run_time": 0.5
}
```
- 색상 변경
- 권장 run_time: 0.3~0.5

### 3.7 3D 전용 애니메이션

**Rotate (3D 회전)**
```json
{
  "type": "Rotate",
  "target": "cube1",
  "angle": "PI/4",
  "axis": "UP",
  "run_time": 1.5
}
```
- axis: UP, RIGHT, OUT
- angle: PI 기준 (PI/4 = 45도)

**move_camera (카메라 이동)**
```json
{
  "type": "move_camera",
  "phi": 75,
  "theta": -30,
  "run_time": 2.0
}
```
- phi: 상하 각도 (0~90)
- theta: 좌우 각도 (-180~180)

---

## 4. 시간 설계 규칙

### 4.1 나레이션 동기화

```
시간 배분:
├── 애니메이션: segment의 처음 40%
├── 대기: segment의 중간 40%
└── 다음 준비: segment의 마지막 20%
```

**예시** (segment: 4.2초)
```
0~1.7초: 애니메이션 실행 (1.68초)
1.7~3.4초: 안정적 표시 (self.wait)
3.4~4.2초: 다음 단계 준비/전환
```

### 4.2 권장 run_time 정리

| 애니메이션 유형 | run_time |
|----------------|----------|
| FadeIn/FadeOut | 0.5~0.8 |
| Write | 1.0~2.0 |
| Create | 0.8~1.5 |
| GrowFromCenter | 0.5~0.8 |
| Indicate | 0.6~1.0 |
| Flash | 0.3~0.5 |
| Transform | 0.8~1.5 |
| move_camera | 1.5~2.5 |

### 4.3 동시 실행 (AnimationGroup)

```json
{
  "type": "AnimationGroup",
  "animations": [
    {"type": "FadeIn", "target": "obj1", "run_time": 0.5},
    {"type": "FadeIn", "target": "obj2", "run_time": 0.5}
  ],
  "lag_ratio": 0.2
}
```
- lag_ratio: 0이면 동시, 0.2면 약간 순차

### 4.4 연속 실행 (Succession)

```json
{
  "type": "Succession",
  "animations": [
    {"type": "FadeIn", "target": "obj1", "run_time": 0.3},
    {"type": "FadeIn", "target": "obj2", "run_time": 0.3},
    {"type": "FadeIn", "target": "obj3", "run_time": 0.3}
  ]
}
```
- 순서대로 하나씩 실행

---

## 5. 애니메이션 패턴

### 패턴 1: 제목 등장

```json
{
  "step": 1,
  "time_range": [0, 3.0],
  "actions": [
    {"type": "Write", "target": "title", "run_time": 1.5}
  ],
  "purpose": "제목 등장"
}
```

### 패턴 2: 좌우 비교

```json
{
  "step": 2,
  "time_range": [3.0, 7.0],
  "actions": [
    {"type": "FadeIn", "target": "left_obj", "shift": "RIGHT", "run_time": 0.5},
    {"type": "FadeIn", "target": "right_obj", "shift": "LEFT", "run_time": 0.5}
  ],
  "purpose": "좌우 대비"
}
```

### 패턴 3: 수식 전개

```json
{
  "step": 3,
  "time_range": [7.0, 12.0],
  "actions": [
    {"type": "Write", "target": "eq1", "run_time": 1.5},
    {"type": "Transform", "target": "eq1", "to": "eq2", "run_time": 1.0},
    {"type": "Indicate", "target": "eq2", "color": "YELLOW", "run_time": 0.8}
  ],
  "purpose": "수식 전개 및 강조"
}
```

### 패턴 4: 그래프 그리기

```json
{
  "step": 4,
  "time_range": [0, 5.0],
  "actions": [
    {"type": "Create", "target": "axes", "run_time": 1.0},
    {"type": "FadeIn", "target": "x_label", "run_time": 0.3},
    {"type": "FadeIn", "target": "y_label", "run_time": 0.3},
    {"type": "Create", "target": "curve", "run_time": 1.5}
  ],
  "purpose": "그래프 구성"
}
```

### 패턴 5: 캐릭터 리액션

```json
{
  "step": 5,
  "time_range": [5.0, 8.0],
  "actions": [
    {"type": "FadeIn", "target": "stickman", "run_time": 0.5},
    {"type": "Wiggle", "target": "stickman", "run_time": 0.4}
  ],
  "purpose": "캐릭터 반응"
}
```

### 패턴 6: 화면 전환

```json
{
  "step": 6,
  "time_range": [10.0, 12.0],
  "actions": [
    {"type": "FadeOut", "target": "old_content", "run_time": 0.5},
    {"type": "FadeIn", "target": "new_content", "run_time": 0.5}
  ],
  "purpose": "장면 전환"
}
```

### 패턴 7: wow moment

```json
{
  "step": 7,
  "time_range": [12.0, 15.0],
  "actions": [
    {"type": "GrowFromCenter", "target": "result", "run_time": 0.8},
    {"type": "Flash", "target": "result", "run_time": 0.3},
    {"type": "Indicate", "target": "result", "scale_factor": 1.1, "run_time": 1.0}
  ],
  "purpose": "강렬한 결론"
}
```

---

## 6. wait 태그 규칙

모든 씬의 마지막 시간에 wait 추가:

```json
{
  "step": 4,
  "time_range": [10.5, 14.76],
  "actions": [
    {"type": "GrowFromCenter", "target": "formula", "run_time": 1.0},
    {"type": "Indicate", "target": "formula", "run_time": 1.5}
  ],
  "wait": {
    "duration": "remaining",
    "tag": "wait_tag_s18_4",
    "note": "남은 시간만큼 대기"
  }
}
```

---

## 7. 애니메이션 체크리스트

### 필수 확인

- [ ] 모든 step에 time_range 있음
- [ ] time_range가 순서대로 연결됨
- [ ] 마지막 step의 time_range 끝 = total_duration
- [ ] 모든 target이 objects에 정의되어 있음
- [ ] Transform의 to 객체가 objects에 있음

### 시간 확인

- [ ] 애니메이션 run_time 합계 < time_range 길이
- [ ] 나레이션과 시각적 동기화
- [ ] 급하지 않게 여유 있는 타이밍

### 3D 씬 확인

- [ ] camera 이동 애니메이션 있으면 run_time 충분
- [ ] Rotate 각도와 축 올바름

---

## 8. 출력 형식

### 파일 위치

```
output/{project_id}/3_visual_prompts/s{n}_visual.json
```

### 파일 구조 (Layout + Animation)

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
    // Layout에서 가져옴
  ],

  "sequence": [
    // Animation에서 추가
    {
      "step": 1,
      "time_range": [0, 4.2],
      "sync_with": "동적 가격이란 무엇일까요?",
      "actions": [...],
      "purpose": "..."
    }
  ],

  "visual_notes": {
    "layout_principle": "좌우 대비",
    "focal_point": "result_formula",
    "color_strategy": "노란색=변수, 초록색=결과"
  }
}
```

---

## 작업 흐름

```
1. s{n}_layout.json 읽기
   - objects 배열 확인

2. s{n}_timing.json 읽기
   - segments 배열로 시간 구간 파악

3. sequence 작성
   - 각 segment에 맞는 애니메이션 배치
   - purpose로 의도 설명

4. visual_notes 추가

5. s{n}_visual.json 저장

6. 다음 씬 처리
```
