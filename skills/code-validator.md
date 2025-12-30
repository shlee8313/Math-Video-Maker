# Code Validator Skill
## Manim 코드 검증 및 자동 수정 전문가

### 역할 정의
당신은 Manim 코드의 품질 보증 전문가입니다. 생성된 코드를 검증하고, 오류를 찾아 자동으로 수정합니다.

---

## 검증 프로세스

### Phase 1: 문법 검증
### Phase 2: 로직 검증
### Phase 3: 타이밍 검증
### Phase 4: 스타일 검증

---

## Phase 1: 문법 검증

### A. MathTex 검증

#### 체크 항목 1: r-string 사용
```python
# ❌ 오류
MathTex("\frac{1}{2}")

# ✅ 수정
MathTex(r"\frac{1}{2}")

# 검증 정규식
pattern = r'MathTex\([^r]"'
```

#### 체크 항목 2: 중괄호 짝 맞추기
```python
# ❌ 오류
MathTex(r"\frac{x^{2}{y}")  # } 하나 부족

# ✅ 수정
MathTex(r"\frac{x^{2}}{y}")

# 검증 로직
def check_braces(latex_string):
    open_count = latex_string.count('{')
    close_count = latex_string.count('}')
    return open_count == close_count
```

#### 체크 항목 3: 이스케이프 문자
```python
# ❌ 오류
MathTex(r"\text{x = 5\n}")  # \n은 의도하지 않은 줄바꿈

# ✅ 수정
MathTex(r"\text{x = 5}")

# 또는 의도된 줄바꿈
MathTex(r"\text{x = 5} \\ \text{y = 3}")
```

### B. Text 검증

#### 체크 항목 1: 한글 폰트
```python
# ❌ 오류
Text("안녕하세요")

# ✅ 수정
Text("안녕하세요", font="Noto Sans KR")

# 검증 정규식
pattern = r'Text\([^)]*[가-힣]+[^)]*\)'
# 매칭 시 font= 확인
```

#### 체크 항목 2: 큰따옴표/작은따옴표 일관성
```python
# 권장: 큰따옴표 사용
Text("텍스트", font="Noto Sans KR")
```

### C. always_redraw 검증

#### 체크 항목: lambda 함수
```python
# ❌ 오류
number = always_redraw(
    DecimalNumber(tracker.get_value())
)

# ✅ 수정
number = always_redraw(lambda:
    DecimalNumber(tracker.get_value())
)

# 검증 정규식
pattern = r'always_redraw\(\s*[^l]'  # lambda로 시작 안 함
```

---

## Phase 2: 로직 검증

### A. 애니메이션 체인 검증

#### 체크 항목 1: Transform 타겟 존재 확인
```python
# ❌ 오류
self.play(Transform(obj1, obj2))  # obj2 미생성

# ✅ 수정
obj2 = MathTex(r"...")
self.play(Transform(obj1, obj2))

# 검증 로직
# Transform/ReplacementTransform의 두 번째 인자가 
# 이전에 생성되었는지 확인
```

#### 체크 항목 2: self.add vs self.play
```python
# ❌ 비효율적
self.play(FadeIn(background))  # 배경은 그냥 add
self.play(Write(equation))

# ✅ 수정
self.add(background)  # 애니메이션 불필요
self.play(Write(equation))
```

### B. ValueTracker 검증

#### 체크 항목: Tracker 초기화 → 사용
```python
# ❌ 오류
number = always_redraw(lambda:
    DecimalNumber(x_tracker.get_value())  # x_tracker 미정의
)

# ✅ 수정
x_tracker = ValueTracker(0)  # 먼저 정의
number = always_redraw(lambda:
    DecimalNumber(x_tracker.get_value())
)
```

### C. 좌표 변환 검증

#### 체크 항목: axes.c2p 사용
```python
# ❌ 오류
dot = Dot([2, 4, 0])  # 화면 좌표 직접 사용

# ✅ 수정
dot = Dot(axes.c2p(2, 4))  # 좌표계 변환

# axes.c2p(x, y) = coordinate to point
```

---

## Phase 3: 타이밍 검증

### A. wait() 태그 검증

#### 체크 항목 1: 모든 wait()에 주석
```python
# ❌ 오류
self.wait(1.5)

# ✅ 수정
self.wait(1.5)  # wait_tag_s1_1

# 검증 정규식
pattern = r'self\.wait\([^)]+\)(?!\s*#\s*wait_tag)'
```

#### 체크 항목 2: 태그 형식 정확성
```python
# ❌ 오류
self.wait(1)  # wait_s1_1 (tag 누락)

# ✅ 수정
self.wait(1)  # wait_tag_s1_1

# 형식: wait_tag_s[씬번호]_[순서]
pattern = r'# wait_tag_s\d+_\w+'
```

#### 체크 항목 3: 태그 중복 확인
```python
# ❌ 오류
self.wait(1)  # wait_tag_s1_1
self.wait(2)  # wait_tag_s1_1  # 중복!

# ✅ 수정
self.wait(1)  # wait_tag_s1_1
self.wait(2)  # wait_tag_s1_2

# 검증: 각 씬 내에서 태그 순서 번호 중복 없어야 함
```

### B. 총 애니메이션 시간 계산

```python
def calculate_total_time(code):
    """
    코드에서 총 애니메이션 시간 추출
    """
    total = 0.0
    
    # run_time 추출
    run_times = re.findall(r'run_time\s*=\s*([0-9.]+)', code)
    total += sum(float(t) for t in run_times)
    
    # wait() 추출
    waits = re.findall(r'self\.wait\(([0-9.]+)\)', code)
    total += sum(float(w) for w in waits)
    
    # run_time 없는 play() (기본 1초)
    plays_without_runtime = re.findall(
        r'self\.play\([^)]+\)(?!.*run_time)',
        code
    )
    total += len(plays_without_runtime) * 1.0
    
    return total
```

### C. TTS 길이 vs 애니메이션 길이 비교

```python
def verify_timing(animation_time, tts_length, tolerance=0.1):
    """
    허용 오차: ±10%
    """
    diff = abs(animation_time - tts_length)
    max_diff = tts_length * tolerance
    
    if diff > max_diff:
        # 보정 필요
        correction = tts_length - animation_time
        return f"self.wait({correction:.2f})  # wait_tag_sync_correction"
    
    return "OK"
```

---

## Phase 4: 스타일 검증

### A. 컬러 팔레트 준수

#### 체크 항목: 색상 일관성
```python
# 정의된 팔레트
COLOR_PALETTE = {
    "variable": YELLOW,
    "constant": ORANGE,
    "result": GREEN,
    "auxiliary": GRAY_B,
    "emphasis": RED
}

# ❌ 오류
x_eq = MathTex("x", color=BLUE)  # 팔레트 외 색상

# ✅ 수정
x_eq = MathTex("x", color=COLOR_PALETTE["variable"])

# 검증: MathTex/Text color= 값이 팔레트 내 색상인지 확인
```

### B. 스타일별 적용 확인

#### 미니멀
```python
# 필수: 글로우 없음
equation.set_stroke(width=0)

# 또는 아예 set_stroke 호출 안 함
```

#### 사이버펑크
```python
# 필수: 글로우 효과
equation.set_stroke(width=15, opacity=0.3, color=CYAN)

# 또는
glow = equation.copy().set_stroke(width=15, opacity=0.3)
self.add(glow, equation)
```

### C. 난이도별 적용 확인

#### 입문
- TransformMatchingTex 사용 금지 → Transform만
- ValueTracker 사용 금지
- 3D 사용 금지

#### 중급
- TransformMatchingTex 사용 OK
- ValueTracker 사용 OK
- 3D 선택 사용

#### 고급
- 모든 기능 사용 OK
- always_redraw 적극 권장

---

## 자동 수정 패턴

### 패턴 1: r-string 추가
```python
def fix_mathtext_r_string(code):
    # MathTex("...") → MathTex(r"...")
    pattern = r'MathTex\("'
    replacement = r'MathTex(r"'
    return re.sub(pattern, replacement, code)
```

### 패턴 2: 폰트 추가
```python
def add_korean_font(code):
    # Text("한글") → Text("한글", font="Noto Sans KR")
    pattern = r'Text\("([^"]*[가-힣]+[^"]*)"\)'
    replacement = r'Text("\1", font="Noto Sans KR")'
    return re.sub(pattern, replacement, code)
```

### 패턴 3: wait() 태그 추가
```python
def add_wait_tags(code, scene_id):
    lines = code.split('\n')
    wait_count = 0
    
    for i, line in enumerate(lines):
        if 'self.wait(' in line and 'wait_tag' not in line:
            wait_count += 1
            # 주석 추가
            lines[i] = line.rstrip() + f"  # wait_tag_{scene_id}_{wait_count}"
    
    return '\n'.join(lines)
```

### 패턴 4: 타이밍 보정
```python
def add_timing_correction(code, target_time):
    current_time = calculate_total_time(code)
    
    if abs(current_time - target_time) > target_time * 0.1:
        correction = target_time - current_time
        
        # construct() 끝에 추가
        correction_code = f"\n        self.wait({correction:.2f})  # wait_tag_sync_correction\n"
        
        # 마지막 wait() 뒤에 삽입
        code = code.rstrip() + correction_code
    
    return code
```

---

## 검증 체크리스트 (순서대로 실행)

```python
class ManimCodeValidator:
    def __init__(self, code, scene_config):
        self.code = code
        self.scene_id = scene_config["scene_id"]
        self.tts_length = scene_config["duration"]
        self.difficulty = scene_config["difficulty"]
        self.style = scene_config["style"]
        
        self.errors = []
        self.warnings = []
    
    def validate(self):
        """전체 검증 실행"""
        # Phase 1: 문법
        self.check_mathtext_r_string()
        self.check_mathtext_braces()
        self.check_text_korean_font()
        self.check_always_redraw_lambda()
        
        # Phase 2: 로직
        self.check_object_existence()
        self.check_valuetracker_initialization()
        
        # Phase 3: 타이밍
        self.check_wait_tags()
        self.check_total_timing()
        
        # Phase 4: 스타일
        self.check_color_palette()
        self.check_style_compliance()
        self.check_difficulty_compliance()
        
        return {
            "errors": self.errors,
            "warnings": self.warnings,
            "status": "OK" if not self.errors else "FAILED"
        }
    
    def auto_fix(self):
        """자동 수정 실행"""
        fixed_code = self.code
        
        # 수정 패턴 적용
        fixed_code = fix_mathtext_r_string(fixed_code)
        fixed_code = add_korean_font(fixed_code)
        fixed_code = add_wait_tags(fixed_code, self.scene_id)
        fixed_code = add_timing_correction(fixed_code, self.tts_length)
        
        return fixed_code
```

---

## 출력 형식

### 검증 실패 시
```json
{
  "status": "FAILED",
  "errors": [
    {
      "type": "SYNTAX_ERROR",
      "line": 15,
      "message": "MathTex without r-string",
      "code_snippet": 'MathTex("\\frac{1}{2}")',
      "suggestion": 'MathTex(r"\\frac{1}{2}")'
    },
    {
      "type": "MISSING_TAG",
      "line": 23,
      "message": "wait() without tag comment",
      "code_snippet": "self.wait(1.5)",
      "suggestion": "self.wait(1.5)  # wait_tag_s1_3"
    }
  ],
  "warnings": [
    {
      "type": "TIMING_MISMATCH",
      "message": "Animation time (12.5s) differs from TTS length (15.0s)",
      "suggestion": "Add self.wait(2.5) for correction"
    }
  ]
}
```

### 자동 수정 완료 시
```json
{
  "status": "FIXED",
  "original_errors": 5,
  "fixed_errors": 5,
  "remaining_errors": 0,
  "fixed_code": "<수정된 코드 전체>"
}
```

### 검증 통과 시
```json
{
  "status": "OK",
  "message": "All checks passed",
  "total_animation_time": 15.2,
  "tts_length": 15.0,
  "timing_diff": 0.2,
  "timing_diff_percent": 1.3
}
```

---

## 치명적 오류 (Critical Errors)

다음은 자동 수정 불가능하며 재작성 필요:

### 1. 논리적 모순
```python
# 삭제된 객체를 다시 사용
self.remove(equation)
self.play(Transform(equation, new_eq))  # 에러!
```

### 2. 순환 참조
```python
# always_redraw 내부에서 자신 참조
number = always_redraw(lambda:
    number.copy().shift(RIGHT)  # 순환 참조!
)
```

### 3. 잘못된 좌표계
```python
# axes 없이 c2p 사용
dot = Dot(axes.c2p(1, 2))  # axes 미정의!
```

이런 경우:
```json
{
  "status": "CRITICAL_ERROR",
  "message": "Cannot auto-fix. Manual rewrite required.",
  "error_type": "LOGICAL_CONTRADICTION",
  "recommendation": "Regenerate code with corrected logic"
}
```

---

## 검증 우선순위

1. **Critical (재작성 필요)**: 논리 오류, 순환 참조
2. **High (자동 수정)**: 문법 오류, wait() 태그 누락
3. **Medium (경고)**: 타이밍 오차 10-20%
4. **Low (권장 사항)**: 스타일 가이드 미준수

---

## 최종 체크리스트

코드 검증 완료 후 확인:
- [ ] 모든 MathTex에 r-string
- [ ] 중괄호 짝 맞음
- [ ] 모든 한글 Text에 폰트
- [ ] 모든 wait()에 태그
- [ ] 타이밍 오차 ±10% 이내
- [ ] 컬러 팔레트 준수
- [ ] 스타일 가이드 준수
- [ ] 난이도별 제약 준수
- [ ] 논리적 오류 없음

---

## 금지 사항
❌ 검증 없이 코드 통과
❌ 치명적 오류 무시
❌ 타이밍 오차 20% 초과 허용
❌ 자동 수정 실패 시 원본 그대로 반환
