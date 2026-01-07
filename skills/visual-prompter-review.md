# Visual Prompter - Review Stage

> **역할**: 생성된 visual.json의 오류 검출 및 수정
> **입력**: s{n}_visual.json
> **출력**: 검증된 s{n}_visual.json

---

## 1. 검증 체크리스트

### 1.1 구조 검증

**필수 최상위 필드**
```
□ scene_id 존재
□ is_3d 존재 (true/false)
□ scene_class 존재 (Scene/ThreeDScene)
□ style 존재
□ total_duration 존재 (숫자)
□ canvas 존재
□ objects 존재 (배열)
□ sequence 존재 (배열)
□ visual_notes 존재
```

**canvas 검증**
```
□ background 존재 ("#000000" 형식)
□ safe_margin 존재 (보통 0.5)
```

---

### 1.2 objects 검증

**모든 객체 공통**
```
□ 모든 객체에 고유한 id 있음
□ 모든 객체에 type 있음
□ 모든 객체에 position 있음
□ id 중복 없음
```

**타입별 필수 필드**

| type | 필수 필드 |
|------|-----------|
| ImageMobject | source, size |
| SVGMobject | source, size |
| Text | content, font, font_size, color |
| MathTex | content, font_size, color |
| Rectangle | width, height |
| Circle | radius |
| Arrow | start, end |
| Axes | x_range, y_range, x_length, y_length |

**한글 텍스트**
```
□ type이 Text이고 content에 한글 포함 → font: "Noto Sans KR" 필수
```

**에셋 경로**
```
□ source가 "assets/"로 시작
□ 확장자 올바름 (.png, .svg)
```

---

### 1.3 position 검증

**method별 필수 필드**

| method | 필수 필드 |
|--------|-----------|
| shift | x, y |
| to_edge | edge |
| to_corner | corner |
| next_to | reference, direction |
| move_to | reference |

**세이프존 검증**
```
□ x 범위: -6.6 ~ 6.6
□ y 범위: -2.5 ~ 3.5 (자막 영역 제외)

위반 시 → 경고 또는 좌표 조정
```

---

### 1.4 sequence 검증

**구조 검증**
```
□ 모든 step에 step 번호 있음
□ 모든 step에 time_range 있음
□ 모든 step에 actions 있음 (배열)
□ 모든 step에 purpose 있음
```

**시간 연속성**
```
□ step 1의 time_range[0] = 0
□ step N의 time_range[1] = step N+1의 time_range[0]
□ 마지막 step의 time_range[1] = total_duration
```

**예시**
```json
❌ 시간 불연속
step 1: [0, 4.0]
step 2: [5.0, 8.0]  // 4.0~5.0 구간 누락

✅ 시간 연속
step 1: [0, 4.0]
step 2: [4.0, 8.0]
```

**target 참조 검증**
```
□ actions의 모든 target이 objects에 정의됨
□ Transform의 to 객체가 objects에 정의됨
```

**예시**
```json
❌ 정의되지 않은 target
objects: [{"id": "text1"}]
actions: [{"target": "text2"}]  // text2 없음

✅ 올바른 참조
objects: [{"id": "text1"}, {"id": "text2"}]
actions: [{"target": "text1"}]
```

---

### 1.5 3D 씬 검증

**3D 필수 조건**
```
is_3d: true인 경우:
□ scene_class: "ThreeDScene"
□ camera 설정 존재 (phi, theta)
□ 3D 객체 있으면 (Cube, Sphere 등) is_3d: true
□ 텍스트/수식에 fixed_in_frame: true
```

**예시**
```json
❌ 3D 객체인데 Scene 사용
{
  "is_3d": false,
  "scene_class": "Scene",
  "objects": [{"type": "Cube"}]
}

✅ ThreeDScene 사용
{
  "is_3d": true,
  "scene_class": "ThreeDScene",
  "camera": {"phi": 60, "theta": -45},
  "objects": [{"type": "Cube"}]
}
```

```json
❌ 3D 씬에서 텍스트 fixed_in_frame 누락
{
  "is_3d": true,
  "objects": [{"id": "title", "type": "MathTex"}]
}

✅ fixed_in_frame 명시
{
  "is_3d": true,
  "objects": [{"id": "title", "type": "MathTex", "fixed_in_frame": true}]
}
```

---

### 1.6 애니메이션 검증

**run_time 검증**
```
□ 모든 action에 run_time 있음
□ run_time > 0
□ 각 step의 애니메이션 총 시간 < time_range 길이
```

**타입별 권장 run_time**

| 애니메이션 | 최소 | 최대 |
|-----------|------|------|
| FadeIn/FadeOut | 0.3 | 1.0 |
| Write | 0.8 | 2.5 |
| Create | 0.5 | 2.0 |
| Transform | 0.6 | 2.0 |
| Indicate | 0.4 | 1.5 |
| Flash | 0.2 | 0.8 |

**Transform 검증**
```
□ Transform/ReplacementTransform에 to 필드 있음
□ to 객체가 objects에 정의됨
□ to 객체와 target 객체 타입 호환
```

---

## 2. 금지 사항

### 2.1 좌표 금지

```
❌ y < -2.5 (자막 영역 침범)
   {"position": {"y": -3.0}}

❌ 화면 밖 좌표
   {"position": {"x": 8.0}}  // x > 6.6

❌ 무의미한 정확도
   {"position": {"x": 2.3456789}}

✅ 적정 정밀도
   {"position": {"x": 2.5}}
```

### 2.2 id 금지

```
❌ 중복 id
   [{"id": "text1"}, {"id": "text1"}]

❌ 숫자로만 된 id
   {"id": "123"}

❌ 공백 포함
   {"id": "my text"}

✅ 의미있는 고유 id
   {"id": "title_text"}, {"id": "main_formula"}
```

### 2.3 에셋 금지

```
❌ 절대 경로
   {"source": "C:/assets/image.png"}

❌ 존재하지 않는 에셋 추정
   {"source": "assets/characters/robot.png"}  // 없는 파일

✅ 상대 경로
   {"source": "assets/characters/stickman_confused.png"}
```

### 2.4 시간 금지

```
❌ 시간 역행
   step 1: [0, 5.0]
   step 2: [3.0, 7.0]  // 겹침

❌ 시간 건너뜀
   step 1: [0, 3.0]
   step 2: [5.0, 8.0]  // 3.0~5.0 누락

❌ total_duration 초과
   total_duration: 10.0
   step 3: [8.0, 12.0]  // 초과

✅ 연속적 시간
   step 1: [0, 3.0]
   step 2: [3.0, 6.0]
   step 3: [6.0, 10.0]  // total_duration과 일치
```

### 2.5 색상 금지

```
❌ 헥스 코드 (Manim 호환 안됨)
   {"color": "#FF0000"}

❌ 존재하지 않는 색상명
   {"color": "NEON_PINK"}

✅ Manim 색상 상수
   {"color": "RED"}
   {"color": "YELLOW"}
   {"color": "GRAY_B"}
```

---

## 3. 자동 수정 규칙

### 3.1 세이프존 수정

```
입력: {"x": -7.5, "y": 0}
수정: {"x": -6.5, "y": 0}
사유: x가 -6.6 미만
```

```
입력: {"x": 0, "y": -3.2}
수정: {"x": 0, "y": -2.3}
사유: y가 자막 영역 침범
```

### 3.2 누락 필드 추가

```
입력 (Text 객체):
{"id": "title", "type": "Text", "content": "안녕"}

수정:
{"id": "title", "type": "Text", "content": "안녕",
 "font": "Noto Sans KR", "font_size": 48, "color": "WHITE"}
```

### 3.3 시간 갭 수정

```
입력:
step 1: [0, 3.0]
step 2: [4.0, 7.0]

수정:
step 1: [0, 4.0]  // 확장
step 2: [4.0, 7.0]
```

---

## 4. 검증 순서

```
1단계: 구조 검증
├── 최상위 필드 존재 확인
├── 배열 형식 확인
└── 필수 값 타입 확인

2단계: objects 검증
├── id 고유성 확인
├── 필수 필드 확인
├── 에셋 경로 확인
└── 세이프존 확인

3단계: sequence 검증
├── 시간 연속성 확인
├── target 참조 확인
├── run_time 합계 확인
└── 마지막 step = total_duration 확인

4단계: 3D 검증 (is_3d: true인 경우만)
├── scene_class 확인
├── camera 설정 확인
└── fixed_in_frame 확인

5단계: 최종 일관성
├── visual_notes 존재 확인
└── 전체 스타일 일관성 확인
```

---

## 5. 검증 결과 형식

### 통과 시

```
✅ s1_visual.json 검증 통과
   - objects: 8개 정상
   - sequence: 4 steps, 시간 연속성 OK
   - 3D: N/A
```

### 오류 발견 시

```
❌ s15_visual.json 검증 실패

오류 목록:
1. [ERROR] objects[2].id "formula" 중복
2. [ERROR] sequence step 2 target "undefined_obj" 미정의
3. [WARN] objects[5].position.y = -3.0 (자막 영역)

자동 수정:
- 오류 3: y를 -2.3으로 조정

수동 수정 필요:
- 오류 1, 2는 수동 검토 필요
```

---

## 6. 씬 간 일관성 검증

### 연속 씬 검증

```
s15 → s16 전환 시:
□ 동일 객체가 다른 스타일로 바뀌지 않음
□ 캐릭터 위치 급격히 변하지 않음 (연속성)
□ 색상 팔레트 일관성
```

### 섹션별 스타일 검증

```
Hook 섹션:
□ 강렬한 시각적 요소
□ 빠른 애니메이션

핵심수학 섹션:
□ 수식 중심
□ 충분한 표시 시간

아웃트로 섹션:
□ 정리/요약 레이아웃
□ 차분한 마무리
```

---

## 7. 수학 패턴 특화 검증

### 공식 등장 패턴

```
□ 공식 중앙 배치
□ 배경 대비 충분한 가독성
□ Indicate/Circumscribe로 강조
```

### 그래프 패턴

```
□ Axes가 화면 중앙~약간 아래
□ x축, y축 라벨 존재
□ 곡선에 적절한 색상
□ 포인트 강조 있음 (Dot)
```

### 전후 비교 패턴

```
□ Before 왼쪽, After 오른쪽
□ 화살표 또는 시각적 연결
□ 대비되는 색상 사용
```

---

## 8. 최종 출력

검증 통과 시:
- 수정된 s{n}_visual.json 저장
- 다음 씬으로 진행

검증 실패 시:
- 자동 수정 가능한 항목 수정
- 수동 검토 필요 항목 보고
- 재생성 또는 수동 수정 요청

---

## 작업 흐름

```
1. s{n}_visual.json 읽기

2. 5단계 검증 수행
   - 구조 → objects → sequence → 3D → 일관성

3. 오류 발견 시
   - 자동 수정 가능 → 수정 적용
   - 수동 필요 → 목록 보고

4. 검증 통과 시
   - "✅ s{n} 검증 완료" 출력

5. 다음 씬으로 진행
```
