# 🎓 수학 교육 영상 제작 자동화 시스템

**Claude Code × Manim**으로 구현한 완전 자동화된 수학 교육 영상 제작 파이프라인

---

## 🚀 빠른 시작

### 1. 기본 실행

```bash
python math_video_pipeline.py
```

### 2. 웹 UI 사용

```bash
# 웹 서버 시작 (Python 내장)
python -m http.server 8000

# 브라우저에서 열기
open http://localhost:8000/video_maker_ui.html
```

---

## 📁 프로젝트 구조

```
/home/claude/
├── math_video_pipeline.py      # 메인 파이프라인
├── video_maker_ui.html         # 웹 인터페이스
├── output/                     # 생성된 파일
│   └── P20251226033923/       # 프로젝트 폴더
│       ├── s1_manim.py        # 씬 1 코드
│       ├── s2_manim.py        # 씬 2 코드
│       └── ...
└── skills/              # Skill 가이드
    ├── script-writer.md
    ├── scene-director.md
    ├── visual-planner.md
    ├── manim-coder.md
    ├── code-validator.md
    ├── image-prompt-writer.md
    └── subtitle-designer.md
```

---

## ⚙️ 설정 옵션

```python
config = Config(
    title="미분의 직관적 이해",        # 영상 주제
    style="minimal",                  # minimal / cyberpunk / paper
    difficulty="intermediate",        # beginner / intermediate / advanced
    duration=180,                     # 초 단위 (3분)
    aspect_ratio="16:9"              # 16:9 (YouTube) / 9:16 (Shorts)
)
```

---

## 🎯 7단계 자동화 프로세스

### 1단계: Script Writer

- 입력: 주제, 난이도, 스타일
- 출력: 읽기용 대본 + TTS용 대본

### 2단계: Scene Director

- 입력: 승인된 대본
- 출력: 씬 분할 JSON (narration_display, narration_tts)

### 3단계: Visual Planner

- 입력: 각 씬 정보
- 출력: 연출 계획 (객체, 애니메이션, 색상)

### 4단계: Manim Coder

- 입력: 연출 계획
- 출력: Manim Python 코드

### 5단계: Code Validator

- 입력: 생성된 코드
- 출력: 검증 및 자동 수정된 코드

### 6단계: Image Prompt Writer

- 입력: 씬 스타일 정보
- 출력: AI 이미지 생성 프롬프트

### 7단계: Subtitle Designer

- 입력: TTS 타이밍 데이터
- 출력: 자막 Manim 코드 (4개 레벨)

---

## 📊 출력 예시

### 생성된 Manim 코드 (s1_manim.py)

```python
from manim import *

class S1(Scene):
    def construct(self):
        # ========== 컬러 팔레트 ==========
        COLOR_PALETTE = {
            "variable": YELLOW,
            "constant": ORANGE,
            "result": GREEN,
            "auxiliary": GRAY_B,
            "emphasis": RED
        }

        # ========== 객체 생성 ==========
        question = Text("?", font="Noto Sans KR", font_size=120)
        question.add_background_rectangle()

        symbol = MathTex(r"\frac{dy}{dx}", color=YELLOW, font_size=120)

        # ========== 애니메이션 ==========
        self.play(Write(question), run_time=1.5)  # wait_tag_s1_1
        self.wait(0.5)  # wait_tag_s1_2

        self.play(Transform(question, symbol), run_time=2.0)  # wait_tag_s1_3
        self.play(Flash(symbol, color=GOLD), run_time=1.0)  # wait_tag_s1_4

        # 자막
        subtitle = Text("여러분, 미분이 뭔지 아시나요?", font="Noto Sans KR")
        subtitle.to_edge(DOWN)
        self.play(FadeIn(subtitle))  # wait_tag_s1_sub
```

---

## 🔧 코드 검증 규칙

### ✅ 자동 검증 항목

1. MathTex에 r-string 사용 확인
2. 한글 Text에 `font="Noto Sans KR"` 확인
3. 모든 wait()에 태그 주석 확인
4. 총 애니메이션 시간 vs TTS 길이 비교
5. 컬러 팔레트 준수 확인

### 🛠️ 자동 수정 기능

- r-string 자동 추가
- 한글 폰트 자동 추가
- wait() 태그 자동 생성
- 타이밍 보정 코드 자동 삽입

---

## 🎨 스타일별 특징

### Minimal (미니멀)

- 검은 배경 + 흰색/노란색
- 글로우 효과 없음
- Flash 빈도 낮음

### Cyberpunk (사이버펑크)

- 어두운 배경 + 네온 색상
- 모든 수식에 글로우 효과
- Flash 빈도 높음

### Paper (종이 질감)

- 밝은 베이지 배경
- 검정/진한 회색
- 손글씨 느낌

---

## 📈 난이도별 적응

### Beginner (입문)

- 단순 애니메이션 (Write, FadeIn)
- 씬당 1-2개 객체
- 짧은 씬 (8-12초)

### Intermediate (중급)

- Transform 계열 사용
- 씬당 2-4개 객체
- 중간 길이 씬 (12-18초)

### Advanced (고급)

- ValueTracker + always_redraw
- 3D 전환 사용
- 긴 씬 (15-25초)

---

## 🔗 Google Sheets 연동

모든 작업 결과는 다음 스프레드시트에 자동 저장:
https://docs.google.com/spreadsheets/d/1tdNd4pLiJOBhNhbi2n_GajO8pzLbq4faBjf33cUzhmI/edit

### 저장 탭 구조

- **대본작성**: Script Writer 결과
- **씬분할**: Scene Director 결과
- **Manim코드**: Visual Planner + Manim Coder 결과
- **코드검증**: Code Validator 결과
- **자막시스템**: Subtitle Designer 결과
- **배경이미지**: Image Prompt Writer 결과

---

## 🚀 확장 가능성

### 1. n8n 워크플로우 통합

```javascript
// n8n에서 각 Skill을 LLM API 노드로 구현
const sceneCode = await callLLM(manimCoderPrompt);
const validatedCode = await callLLM(validatorPrompt);
```

### 2. 병렬 렌더링

```bash
# 각 씬을 별도 프로세스에서 동시 렌더링
manim -pql s1_manim.py S1 &
manim -pql s2_manim.py S2 &
wait
```

### 3. 음성 동기화

```python
# Whisper API로 TTS 타이밍 추출
timing_data = whisper_api(tts_audio)
# 자막 시스템에 주입
subtitles = SubtitleDesigner(timing_data).create()
```

---

## 📚 참고 문서

- [Manim Community Edition](https://docs.manim.community/)
- [SSML 가이드](https://cloud.google.com/text-to-speech/docs/ssml)
- [Whisper API](https://platform.openai.com/docs/guides/speech-to-text)

---

## 🎯 핵심 철학

> "매뉴얼은 사람과 AI가 협업하는 공통 언어입니다.  
> Manim은 수학의 본질을 시각화하는 언어이고,  
> Claude Code는 그 언어를 자동화하는 도구입니다."

---

## 📝 라이선스

이 프로젝트는 교육 목적으로 자유롭게 사용 가능합니다.

---

## 🤝 기여

프로젝트 개선 아이디어가 있으시면 언제든지 제안해주세요!

1. Fork the project
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

**Made with ❤️ by Claude Code Team**

```



```
