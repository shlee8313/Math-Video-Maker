# Subtitle Designer Skill
## 자막 생성 및 음성 동기화 전문가

### 역할 정의
당신은 자막 시스템 설계 전문가입니다. TTS 타이밍 데이터를 활용해 다양한 스타일의 자막을 생성합니다.

---

## 자막 레벨 시스템

### Level 1: 기본 하단 고정
- **사용 시기**: 입문 난이도, 단순 설명
- **특징**: 가장 단순, 가독성 최우선

### Level 2: 음성 동기화
- **사용 시기**: 중급 난이도, 정확한 타이밍 필요
- **특징**: Whisper API 타이밍 데이터 활용

### Level 3: 카라오케 스타일
- **사용 시기**: 고급 난이도, 시각적 강조
- **특징**: 단어별 색상 변화

### Level 4: 수식 연동 (최고급)
- **사용 시기**: 수학 개념 집중 설명
- **특징**: 수식 객체와 자막 연결

---

## Level 1: 기본 하단 고정

### 설계 원칙
```python
# 위치: 하단 고정
# 등장: FadeIn (상향)
# 퇴장: FadeOut
# 배경: 반투명 검정
# 지속: 나레이션 길이
```

### 구현 코드
```python
def show_subtitle(self, text, duration):
    """
    기본 자막 표시 함수
    
    Args:
        text: 자막 텍스트
        duration: 표시 시간 (초)
    """
    subtitle = Text(
        text,
        font="Noto Sans KR",
        font_size=36,
        color=WHITE
    )
    subtitle.to_edge(DOWN, buff=0.5)
    subtitle.add_background_rectangle(
        color=BLACK,
        opacity=0.7,
        buff=0.2
    )
    
    self.play(FadeIn(subtitle, shift=UP*0.2), run_time=0.2)  # wait_tag_sub_in
    self.wait(duration)  # wait_tag_sub_stay
    self.play(FadeOut(subtitle), run_time=0.2)  # wait_tag_sub_out
```

### 사용 예시
```python
class Scene1(Scene):
    def construct(self):
        # 메인 애니메이션
        equation = MathTex(r"f(x) = x^2")
        self.play(Write(equation))  # wait_tag_s1_1
        
        # 자막
        self.show_subtitle("이차함수는 포물선 모양입니다", duration=3.5)
        
        self.wait(1)  # wait_tag_s1_2
```

### 최적화: 함수 정의 위치
```python
# 씬 클래스 외부에 정의 (재사용)
def create_subtitle(text):
    """자막 객체 생성"""
    subtitle = Text(text, font="Noto Sans KR", font_size=36, color=WHITE)
    subtitle.to_edge(DOWN, buff=0.5)
    subtitle.add_background_rectangle(color=BLACK, opacity=0.7, buff=0.2)
    return subtitle

class Scene1(Scene):
    def construct(self):
        sub = create_subtitle("텍스트")
        self.play(FadeIn(sub, shift=UP*0.2))
        # ...
```

---

## Level 2: 음성 동기화

### TTS 타이밍 데이터 구조
```python
# Whisper API 출력 예시
subtitle_data = [
    {"text": "미분은", "start": 0.5, "end": 1.0, "duration": 0.5},
    {"text": "순간", "start": 1.2, "end": 1.6, "duration": 0.4},
    {"text": "변화율입니다", "start": 1.8, "end": 2.5, "duration": 0.7}
]
```

### 구현 코드 (n8n 주입 방식)
```python
class AutoSubtitle(Scene):
    def construct(self):
        # ========== SUBTITLE_DATA_INJECT_POINT ==========
        # n8n이 이 위치에 실제 데이터 주입
        subtitles = [
            {"text": "미분은", "start": 0.5, "end": 1.0, "duration": 0.5},
            {"text": "순간", "start": 1.2, "end": 1.6, "duration": 0.4},
            # ...
        ]
        
        # 메인 애니메이션 (예시)
        equation = MathTex(r"\frac{dy}{dx}")
        self.play(Write(equation))  # wait_tag_s1_1
        
        # 동기화된 자막
        for i, sub_data in enumerate(subtitles):
            subtitle = Text(
                sub_data["text"],
                font="Noto Sans KR",
                font_size=36,
                color=WHITE
            )
            subtitle.to_edge(DOWN, buff=0.5)
            subtitle.add_background_rectangle(
                color=BLACK,
                opacity=0.8,
                buff=0.2
            )
            
            # 등장
            self.play(
                FadeIn(subtitle, shift=UP*0.2),
                run_time=0.2
            )  # wait_tag_sub_{i}_in
            
            # 표시
            self.wait(sub_data["duration"])  # wait_tag_sub_{i}_stay
            
            # 퇴장
            self.play(
                FadeOut(subtitle),
                run_time=0.15
            )  # wait_tag_sub_{i}_out
```

### 개선: 부드러운 전환
```python
# 이전 자막과 겹치기
for i, sub_data in enumerate(subtitles):
    new_sub = create_subtitle(sub_data["text"])
    
    if i == 0:
        # 첫 자막
        self.play(FadeIn(new_sub, shift=UP*0.2))
    else:
        # 이전 자막 제거 + 새 자막 등장 동시
        self.play(
            FadeOut(prev_sub),
            FadeIn(new_sub, shift=UP*0.2),
            run_time=0.2
        )
    
    self.wait(sub_data["duration"])
    prev_sub = new_sub

# 마지막 자막 제거
self.play(FadeOut(prev_sub))
```

---

## Level 3: 카라오케 스타일

### 설계 원칙
```
1. 전체 문장을 먼저 회색으로 표시
2. 발화되는 단어만 노란색으로 강조
3. 단어별 확대 효과 (1.1배)
```

### 구현 코드
```python
class KaraokeSubtitle(Scene):
    def construct(self):
        # ========== SUBTITLE_DATA_INJECT_POINT ==========
        word_timings = [
            {"text": "미분은", "start": 0.5, "duration": 0.5},
            {"text": "순간", "start": 1.2, "duration": 0.4},
            {"text": "변화율입니다", "start": 1.8, "duration": 0.7}
        ]
        
        # 전체 텍스트 조합
        full_text = " ".join([w["text"] for w in word_timings])
        
        # 회색으로 전체 표시
        subtitle_base = Text(
            full_text,
            font="Noto Sans KR",
            font_size=36,
            color=GRAY_B
        )
        subtitle_base.to_edge(DOWN, buff=0.5)
        subtitle_base.add_background_rectangle(
            color=BLACK,
            opacity=0.7,
            buff=0.2
        )
        
        self.add(subtitle_base)
        
        # 단어별 강조
        char_index = 0
        for i, timing in enumerate(word_timings):
            word_len = len(timing["text"])
            
            # 해당 단어만 노란색 + 확대
            self.play(
                subtitle_base[char_index:char_index+word_len]
                .animate
                .set_color(YELLOW)
                .scale(1.1),
                run_time=0.2
            )  # wait_tag_karaoke_{i}_highlight
            
            # 발화 시간 대기
            self.wait(timing["duration"])  # wait_tag_karaoke_{i}_stay
            
            # 다음 단어로 (+1은 공백)
            char_index += word_len + 1
        
        # 전체 제거
        self.play(FadeOut(subtitle_base))  # wait_tag_karaoke_out
```

### 개선: 이전 단어 원위치
```python
for i, timing in enumerate(word_timings):
    word_len = len(timing["text"])
    
    # 새 단어 강조
    animations = [
        subtitle_base[char_index:char_index+word_len]
        .animate
        .set_color(YELLOW)
        .scale(1.1)
    ]
    
    # 이전 단어 원위치
    if i > 0:
        prev_start = sum(len(w["text"])+1 for w in word_timings[:i])
        prev_len = len(word_timings[i-1]["text"])
        animations.append(
            subtitle_base[prev_start:prev_start+prev_len]
            .animate
            .set_color(GRAY_B)
            .scale(1/1.1)
        )
    
    self.play(*animations, run_time=0.2)
    self.wait(timing["duration"])
    
    char_index += word_len + 1
```

---

## Level 4: 수식 연동 (최고급)

### 설계 원칙
```
1. 자막이 수식의 특정 부분을 가리킴
2. 화살표로 연결
3. 해당 수식 부분 강조 (색상 변경 + 확대)
```

### 구현 코드
```python
class FormulaFocus(Scene):
    def construct(self):
        # 수식
        eq = MathTex(
            r"E", "=", "m", "c^{2}"
        ).scale(2)
        eq.move_to(ORIGIN)
        
        self.add(eq)
        self.wait(1)  # wait_tag_formula_1
        
        # ===== 'm' 설명 =====
        sub_m = Text(
            "여기서 m은 질량을 의미합니다",
            font="Noto Sans KR",
            font_size=32
        ).scale(0.6)
        sub_m.to_edge(DOWN, buff=0.5)
        sub_m.add_background_rectangle(opacity=0.8)
        
        # 화살표
        arrow_m = Arrow(
            sub_m.get_top(),
            eq[2].get_bottom(),  # 'm' 위치
            color=YELLOW,
            buff=0.1
        )
        
        # 애니메이션
        self.play(
            FadeIn(sub_m, shift=UP*0.2),
            GrowArrow(arrow_m),
            eq[2].animate.set_color(YELLOW).scale(1.2)
        )  # wait_tag_formula_2
        
        self.wait(2)  # wait_tag_formula_3
        
        # ===== 'c²' 설명 =====
        sub_c = Text(
            "c는 빛의 속도입니다",
            font="Noto Sans KR",
            font_size=32
        ).scale(0.6)
        sub_c.to_edge(DOWN, buff=0.5)
        sub_c.add_background_rectangle(opacity=0.8)
        
        arrow_c = Arrow(
            sub_c.get_top(),
            eq[3].get_bottom(),  # 'c²' 위치
            color=YELLOW,
            buff=0.1
        )
        
        # 전환
        self.play(
            FadeOut(sub_m),
            FadeOut(arrow_m),
            eq[2].animate.set_color(WHITE).scale(1/1.2),  # 'm' 원위치
            FadeIn(sub_c, shift=UP*0.2),
            GrowArrow(arrow_c),
            eq[3].animate.set_color(YELLOW).scale(1.2)
        )  # wait_tag_formula_4
        
        self.wait(2)  # wait_tag_formula_5
        
        # 정리
        self.play(
            FadeOut(sub_c),
            FadeOut(arrow_c),
            eq[3].animate.set_color(WHITE).scale(1/1.2)
        )  # wait_tag_formula_6
```

### 응용: 여러 부분 순차 강조
```python
# 수식
eq = MathTex(
    r"\int_{0}^{1}", "x^{2}", "dx"
).scale(1.5)

# 설명 리스트
explanations = [
    {"part": 0, "text": "0부터 1까지 적분합니다", "duration": 2.5},
    {"part": 1, "text": "x 제곱 함수를", "duration": 2.0},
    {"part": 2, "text": "x에 대해 적분합니다", "duration": 2.5}
]

self.add(eq)

for i, exp in enumerate(explanations):
    # 자막 + 화살표
    sub = create_subtitle(exp["text"])
    arrow = Arrow(sub.get_top(), eq[exp["part"]].get_bottom(), color=YELLOW)
    
    # 등장
    self.play(
        FadeIn(sub, shift=UP*0.2),
        GrowArrow(arrow),
        eq[exp["part"]].animate.set_color(YELLOW).scale(1.2)
    )  # wait_tag_focus_{i}_in
    
    self.wait(exp["duration"])  # wait_tag_focus_{i}_stay
    
    # 다음으로 (마지막 아니면)
    if i < len(explanations) - 1:
        self.play(
            FadeOut(sub),
            FadeOut(arrow),
            eq[exp["part"]].animate.set_color(WHITE).scale(1/1.2)
        )  # wait_tag_focus_{i}_out
```

---

## 자막 배치 전략

### A. 수직 위치

```python
# 하단 (기본)
subtitle.to_edge(DOWN, buff=0.5)

# 중단 (수식이 하단에 있을 때)
subtitle.move_to(DOWN*2)

# 상단 (특수한 경우)
subtitle.to_edge(UP, buff=0.5)
```

### B. 수평 위치

```python
# 중앙 (기본)
subtitle.move_to(DOWN*3.5)

# 좌측
subtitle.to_edge(DOWN, buff=0.5).to_edge(LEFT, buff=1)

# 우측
subtitle.to_edge(DOWN, buff=0.5).to_edge(RIGHT, buff=1)
```

### C. 가려짐 방지

```python
def place_subtitle_safely(subtitle, existing_objects):
    """
    기존 객체와 겹치지 않게 배치
    """
    subtitle.to_edge(DOWN, buff=0.5)
    
    # 겹침 확인
    for obj in existing_objects:
        if subtitle.get_top()[1] > obj.get_bottom()[1]:
            # 겹침 발생 → 위로 이동
            subtitle.shift(UP*1)
            break
    
    return subtitle
```

---

## 스타일별 자막 디자인

### 미니멀
```python
subtitle = Text(text, font="Noto Sans KR", font_size=36, color=WHITE)
subtitle.add_background_rectangle(
    color=BLACK,
    opacity=0.5,  # 낮은 투명도
    buff=0.15
)
```

### 사이버펑크
```python
subtitle = Text(text, font="Noto Sans KR", font_size=36, color=CYAN)
subtitle.set_stroke(width=2, color=CYAN, opacity=0.5)  # 글로우
subtitle.add_background_rectangle(
    color="#0a0a0a",
    opacity=0.9,
    buff=0.2
)
```

### 종이
```python
subtitle = Text(text, font="Noto Sans KR", font_size=36, color=BLACK)
subtitle.add_background_rectangle(
    color="#f5f5dc",
    opacity=0.8,
    buff=0.2,
    stroke_width=2,
    stroke_color=DARK_GRAY
)
```

---

## 난이도별 자막 권장

### 입문
- **레벨**: 1 (기본 하단 고정)
- **이유**: 시각적 복잡도 최소화
- **특징**: 긴 지속 시간 (3-5초)

### 중급
- **레벨**: 2 (음성 동기화)
- **이유**: 정확한 타이밍으로 집중력 향상
- **특징**: 단어별 전환 (1-2초)

### 고급
- **레벨**: 3 or 4 (카라오케 / 수식 연동)
- **이유**: 고급 학습자는 시각적 단서 활용 능력 높음
- **특징**: 실시간 강조

---

## n8n 자동화 통합

### 데이터 주입 포인트
```python
class AutoSubtitleScene(Scene):
    def construct(self):
        # ========== CONFIG_INJECT_POINT ==========
        subtitle_level = ${subtitle_level}  # 1, 2, 3, 4
        subtitle_data = ${subtitle_data}    # JSON 데이터
        style = "${style}"                  # minimal, cyberpunk, paper
        
        # 레벨별 분기
        if subtitle_level == 1:
            self.level1_subtitles(subtitle_data, style)
        elif subtitle_level == 2:
            self.level2_subtitles(subtitle_data, style)
        elif subtitle_level == 3:
            self.level3_subtitles(subtitle_data, style)
        elif subtitle_level == 4:
            self.level4_subtitles(subtitle_data, style)
    
    def level1_subtitles(self, data, style):
        # Level 1 구현
        pass
    
    # ... 다른 레벨들
```

---

## 성능 최적화

### A. 자막 재사용
```python
# ❌ 비효율적
for text in texts:
    sub = create_subtitle(text)
    self.play(FadeIn(sub))
    self.wait(2)
    self.play(FadeOut(sub))

# ✅ 효율적
subtitle_template = Text("", font="Noto Sans KR", font_size=36)
subtitle_template.to_edge(DOWN, buff=0.5)
subtitle_template.add_background_rectangle(opacity=0.7)

for text in texts:
    subtitle_template.become(Text(text, font="Noto Sans KR", font_size=36))
    self.play(FadeIn(subtitle_template))
    self.wait(2)
    self.play(FadeOut(subtitle_template))
```

### B. 애니메이션 시간 단축
```python
# 자막 등장/퇴장은 빠르게 (0.15-0.2초)
self.play(FadeIn(sub), run_time=0.2)

# 메인 애니메이션은 정상 속도
self.play(Write(equation), run_time=2)
```

---

## 체크리스트

자막 시스템 완성 후 확인:
- [ ] TTS 타이밍 데이터가 정확히 반영되었는가?
- [ ] 모든 자막에 배경이 있는가?
- [ ] 한글 폰트가 지정되었는가?
- [ ] 자막이 메인 객체를 가리지 않는가?
- [ ] 스타일 가이드를 따르는가?
- [ ] 난이도에 적합한 레벨인가?
- [ ] 등장/퇴장 애니메이션이 부드러운가?

---

## 금지 사항
❌ 자막 없는 영상 (Level 1은 필수)
❌ TTS와 동기화 안 된 Level 2+
❌ 배경 없는 자막 (가독성 저하)
❌ 한글 폰트 누락
❌ 메인 객체 가림
