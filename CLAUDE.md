# Math Video Maker 프로젝트

## 🚀 빠른 시작

"시작" 이라고 입력하면 영상 제작을 시작합니다.

---

## 📋 대화형 워크플로우

사용자가 "시작" 입력 시, 아래 순서대로 진행:

### Step 1: 프로젝트 설정 수집

Claude가 물어볼 것:

1. "영상 주제가 무엇인가요?"
2. "영상 길이는 몇 분인가요?" (기본값: 8분)
3. "화면 비율을 선택하세요: 16:9 (YouTube) / 9:16 (Shorts)" (기본값: 16:9)
4. "스타일을 선택하세요: minimal / cyberpunk / paper / space / geometric / stickman" (기본값: cyberpunk)
5. "난이도를 선택하세요: beginner / intermediate / advanced" (기본값: intermediate)

모든 정보 수집 후:
→ `python math_video_pipeline.py init --title "주제" --duration 초 --style 스타일 --difficulty 난이도 --aspect 비율` 실행
→ state.json 생성 확인

---

### Step 2: 대본 작성

Claude가 할 것:

1. `skills/script-writer.md` 읽기
2. 5단계 구조로 대본 작성:
   - Hook (10초): 흥미 유발
   - 분석 (30%): 문제 상황
   - 핵심 수학 (40%): 개념 설명
   - 적용 (20%): 실생활 연결
   - 아웃트로 (10초): 마무리
3. 사용자에게 대본 보여주고 승인 요청
4. 승인 시 → `output/{project_id}/1_script/reading_script.json` 저장
5. TTS용 변환 (숫자→한글 발음)
6. **state.json 업데이트**: `current_phase: "script_approved"`, `files.script` 경로 저장

✅ **이 시점에서 `/clear` 가능**

---

### Step 3: 씬 분할

Claude가 할 것:

1. `skills/scene-director.md` 읽기
2. 대본을 씬으로 분할 (평균 10-20초/씬)
3. 각 씬에 포함:
   - scene_id (s1, s2, s3...)
   - section (Hook/분석/핵심수학/적용/아웃트로)
   - duration
   - narration_display (화면 자막용: 9×9=81)
   - narration_tts (음성용: 구 곱하기 구는 팔십일)
   - visual_concept
   - wow_moment
   - **required_assets** (필요한 PNG 에셋 목록)
   - **is_3d** (3D 씬 여부: true/false)
   - **scene_class** (Scene 또는 ThreeDScene)
   - **camera_settings** (3D일 때 카메라 설정)
4. 사용자에게 씬 목록 보여주고 승인 요청
5. 승인 시 → `output/{project_id}/2_scenes/scenes.json` 저장
6. **state.json 업데이트**: `current_phase: "scenes_approved"`, `files.scenes` 경로 저장

✅ **이 시점에서 `/clear` 가능**

---

### Step 3.5: 에셋 체크 (NEW)

Claude가 할 것:

1. `scenes.json`에서 모든 `required_assets` 수집
2. `assets/` 폴더 (루트 레벨) 구조 확인
3. 필요한 파일 vs 존재하는 파일 비교
4. **없는 파일이 있으면** → 누락 에셋 목록과 권장 사양(500x500px+, PNG 투명배경) 안내

5. 사용자가 "에셋 준비 완료" 입력 시 → 다시 폴더 확인
6. 모든 파일 존재 → Step 4 진행
7. 아직 없는 파일 → 누락 목록 다시 안내
8. **state.json 업데이트**: `current_phase: "assets_checked"`

✅ **이 시점에서 `/clear` 가능**

---

### Step 4: TTS 생성

Claude가 할 것:

1. **사용자에게 TTS 방식 선택 요청:**
   - "음성 생성 방식을 선택하세요:"
     1. **OpenAI TTS 사용** (권장, 유료 $0.20/영상)
     2. **직접 녹음해서 업로드** (무료)

2. **OpenAI TTS 선택 시:**
   - `python math_video_pipeline.py tts-all` 실행
   - 결과 확인 후 사용자에게 알림
   - **state.json 업데이트**: `current_phase: "tts_completed"`, `files.audio[]` 배열 저장

3. **외부 녹음 선택 시:** → Step 4.5로 이동

✅ **이 시점에서 `/clear` 가능**

---

### Step 4.5: 외부 녹음 옵션 (선택사항)

사용자가 직접 녹음을 원할 때 사용:

Claude가 할 것:

1. "외부 녹음을 진행합니다. 텍스트를 내보냅니다."
2. `python math_video_pipeline.py tts-export` 실행
3. 사용자에게 안내: `0_audio/tts_texts.json` 참조하여 문장별 녹음 (파일명: s1_1.mp3, s1_2.mp3...)

4. 사용자가 "오디오 파일 준비완료" 입력 시:
   - `python math_video_pipeline.py audio-check` 실행
   - 누락 파일 있으면 목록 안내
   - 모든 파일 존재 시 → 다음 진행

5. `python math_video_pipeline.py audio-process` 실행
   - Whisper로 각 파일 duration 분석
   - 씬별 timing.json 생성

6. **state.json 업데이트**: `current_phase: "tts_completed"`, `files.audio[]` 배열 저장

✅ **이 시점에서 `/clear` 가능**

---

### ⚠️ TTS 엔진 변경 시 주의사항

**중간에 TTS 방식을 바꾸면 반드시 `0_audio/` 폴더를 비워야 합니다!**

이유: 목소리가 섞이면 일관성이 깨짐

```powershell
# 0_audio 폴더 비우기
Remove-Item "output/{project_id}/0_audio/*" -Force
```

---

### Step 5: Manim 코드 생성 (씬별 반복)

각 씬에 대해:

1. `skills/manim-coder.md` 읽기
2. 해당 씬의 타이밍 데이터 로드 (`0_audio/{scene_id}_timing.json`)
3. 실제 음성 길이에 맞춰 코드 생성
4. 필수 규칙 적용:
   - `MathTex(r"...")` - r-string
   - `Text("한글", font="Noto Sans KR")`
   - `self.wait(n)  # wait_tag_s{씬}_{순서}`
   - 컬러 팔레트 준수
   - **PNG 에셋은 ImageMobject 사용** (경로: `assets/...`)
5. `output/{project_id}/4_manim_code/{scene_id}_manim.py` 저장
6. **state.json 업데이트**: `scenes.completed[]` 배열에 추가, `scenes.current` 업데이트
7. 다음 씬으로 진행

✅ **매 3-5씬 완료 후 `/clear` 가능**

모든 씬 완료 후 → "모든 Manim 코드 생성 완료!" 알림

---

### Step 5.5: 배경 이미지 생성 (외부 작업)

Claude가 할 것:

1. "이미지 프롬프트를 내보냅니다."
2. `python math_video_pipeline.py prompts-export` 실행
3. 사용자에게 안내:
   - `6_image_prompts/prompts_batch.txt` 파일 확인
   - Midjourney, DALL-E, Leonardo 등에서 이미지 생성
   - 생성된 이미지를 `9_backgrounds/` 폴더에 저장
   - 파일명 규칙: `s1_bg.png`, `s2_bg.png`, ...

사용자가 이미지 준비 후:

1. `python math_video_pipeline.py images-check` 로 검증
2. 또는 `python math_video_pipeline.py images-import --source "다운로드폴더"` 로 일괄 가져오기
3. **state.json 업데이트**: `current_phase: "images_ready"`, `files.images[]` 배열 저장

✅ **이 시점에서 `/clear` 가능**

---

### Step 6: Manim 렌더링

Claude가 할 것:

1. "렌더링을 시작할까요?" 물어보기
2. 승인 시 → `python math_video_pipeline.py render-all` 실행
3. 결과 확인 (28개 씬 렌더링 성공 여부)
4. **state.json 업데이트**: `current_phase: "rendered"`

✅ **이 시점에서 `/clear` 가능**

---

### Step 7: 자막 생성 및 최종 합성

Claude가 할 것:

1. SRT 자막 파일 생성
   → `python math_video_pipeline.py subtitle-generate`
   → `7_subtitles/` 폴더에 `s1.srt`, `s2.srt`, ... 생성

2. 씬별 최종 합성 (배경 + Manim + 오디오 + 자막)
   → `python math_video_pipeline.py compose-all`
   → FFmpeg로 각 씬 합성: 배경 이미지 + Manim 애니메이션 + TTS 오디오 + SRT 자막

3. 전체 영상 병합
   → `python math_video_pipeline.py merge-final`
   → `final_video.mp4` 생성

4. **state.json 업데이트**: `current_phase: "completed"`

---

## 🔄 /clear 가능 지점

> 각 Step 완료 후 ✅ 표시된 시점에서 `/clear` 가능. "계속" 입력으로 재개.

### /clear 가능 지점 요약

| 지점 | 타이밍                | 저장된 파일                   | state.json 자동 업데이트     | 재개 명령             |
| ---- | --------------------- | ----------------------------- | ---------------------------- | --------------------- |
| #1   | 대본 승인 후          | `1_script/*.json`             | ✅ phase→script_approved     | "계속"                |
| #2   | 씬 분할 승인 후       | `2_scenes/scenes.json`        | ✅ phase→scenes_approved     | "계속"                |
| #2.5 | 에셋 체크 완료 후     | `assets/` 폴더 PNG 파일들     | ✅ phase→assets_checked      | "계속"                |
| #3   | TTS 생성 완료 후      | `0_audio/*.mp3, *.json`       | ✅ phase→tts_completed       | "계속"                |
| #4   | 씬 3-5개 코드 완료 후 | `4_manim_code/s1~s5_manim.py` | ✅ scenes.completed 업데이트 | "계속" 또는 "s6 코드" |
| #5   | 모든 코드 완료 후     | 모든 `_manim.py`              | ✅ phase→manim_completed     | "프롬프트 내보내기"   |
| #6   | 이미지 준비 완료 후   | `9_backgrounds/*.png`         | ✅ phase→images_ready        | "렌더링"              |
| #7   | Manim 렌더링 완료 후  | `8_renders/*.mp4`             | ✅ phase→rendered            | "자막 생성"           |

### ⚠️ /clear 금지 구간

| 구간                     | 이유                   |
| ------------------------ | ---------------------- |
| 대본 작성 **중**         | 승인 전이라 저장 안 됨 |
| 씬 분할 **중**           | 승인 전이라 저장 안 됨 |
| 에셋 체크 **중**         | 확인 완료 전           |
| TTS 생성 **중**          | API 호출 중단됨        |
| 특정 씬 코드 작성 **중** | 해당 씬 코드 유실      |

### /clear 후 재개 방법

```
사용자: "계속" 또는 "상태"
Claude: state.json 읽고 현재 단계 파악 → 이어서 진행
```

### 권장 워크플로우 (토큰 절약)

```
세션 1: 시작 → 대본 승인 → /clear
세션 2: 계속 → 씬 분할 승인 → /clear
세션 3: 계속 → 에셋 체크 → 에셋 준비 → /clear
세션 4: 계속 → TTS 생성 → /clear
세션 5: 계속 → s1~s5 코드 → /clear
세션 6: 계속 → s6~s10 코드 → /clear
세션 7: 렌더링
```

---

## 📊 state.json 구조

```json
{
  "project_id": "P20250615_143000",
  "title": "피타고라스 정리",
  "current_phase": "manim_coding",
  "settings": {
    "style": "cyberpunk",
    "difficulty": "intermediate",
    "duration": 300,
    "aspect_ratio": "16:9",
    "voice": "onyx"
  },
  "scenes": {
    "total": 8,
    "completed": ["s1", "s2"],
    "pending": ["s3", "s4", "s5", "s6", "s7", "s8"],
    "current": "s3"
  },
  "files": {
    "script": "output/P20250615_143000/1_script/reading_script.json",
    "scenes": "output/P20250615_143000/2_scenes/scenes.json",
    "audio": ["s1_audio.mp3", "s2_audio.mp3"],
    "manim": ["s1_manim.py", "s2_manim.py"]
  },
  "assets": {
    "required": ["characters/stickman_confused.png", "objects/snack_bag.png"],
    "available": ["characters/stickman_confused.png"],
    "missing": ["objects/snack_bag.png"]
  },
  "last_updated": "2025-06-15T14:35:00"
}
```

### state.json 자동 업데이트 규칙

| 단계 완료 | current_phase | 주요 업데이트 |
|----------|---------------|--------------|
| Step 2 | script_approved | files.script, files.tts_script |
| Step 3 | scenes_approved | files.scenes, scenes.total/pending, assets.required |
| Step 3.5 | assets_checked | assets.available, assets.missing=[] |
| Step 4 | tts_completed | files.audio[] |
| Step 5 | manim_coding→manim_completed | scenes.completed[], files.manim[] |
| Step 5.5 | images_ready | files.images[] |
| Step 6 | rendered | - |
| Step 7 | completed | files.final_video |

---

## 🎨 에셋(Asset) 시스템

### 에셋 폴더 위치

**중요:** 에셋은 프로젝트별이 아닌 **루트 레벨**에 위치합니다.
→ 모든 프로젝트에서 공용으로 사용

```
Math-Video-Maker/
├── assets/                    ← 🔥 루트 레벨 (모든 프로젝트 공용)
│   ├── characters/
│   ├── objects/
│   ├── icons/
│   └── metaphors/
│
└── output/
    └── {project_id}/          ← 프로젝트별 출력물
```

### 에셋이 필요한 경우

| 구분              | Manim으로 그리기 ✅       | PNG 에셋 사용 ✅    |
| ----------------- | ------------------------- | ------------------- |
| 수식              | `MathTex(r"x^2")`         | -                   |
| 그래프            | `axes.plot(...)`          | -                   |
| 기본 도형         | `Circle()`, `Rectangle()` | -                   |
| 화살표            | `Arrow()`, `Vector()`     | -                   |
| **캐릭터**        | ❌ 이상하게 나옴          | `stickman_*.png`    |
| **실물 물체**     | ❌ 이상하게 나옴          | `snack_bag.png`     |
| **복잡한 아이콘** | ❌                        | `question_mark.png` |

### 에셋 폴더 구조

```
assets/                            ← 루트 레벨 (모든 프로젝트 공용)
├── characters/                    ← 캐릭터
│   ├── stickman_neutral.png           # 기본 자세
│   ├── stickman_thinking.png          # 생각하는 🤔
│   ├── stickman_surprised.png         # 놀란 😲
│   ├── stickman_happy.png             # 기쁜 😊
│   ├── stickman_confused.png          # 혼란 😕
│   ├── stickman_pointing.png          # 가리키는 👉
│   ├── stickman_holding.png           # 물건 든
│   └── stickman_sad.png               # 슬픈 😢
│
├── objects/                       ← 물체
│   ├── snack_bag_normal.png           # 일반 과자
│   ├── snack_bag_shrunk.png           # 줄어든 과자
│   ├── money.png                      # 돈
│   ├── cart.png                       # 카트
│   ├── receipt.png                    # 영수증
│   ├── scale.png                      # 저울
│   └── calculator.png                 # 계산기
│
├── icons/                         ← 아이콘
│   ├── question_mark.png              # 물음표
│   ├── exclamation.png                # 느낌표
│   ├── lightbulb.png                  # 전구 (아이디어)
│   ├── arrow_right.png                # 화살표
│   └── checkmark.png                  # 체크마크
│
└── metaphors/                     ← 은유/비유
    └── golden_chain.png               # 금사슬에 묶인 캐릭터
```

### 에셋 파일 사양
- 해상도: 500x500px+ (1000x1000 권장), PNG 투명배경
- 파일명: `{이름}_{상태}.png` (예: stickman_happy.png)

> 상세 목록: `skills/asset-catalog.md` 참조

### 에셋 요청 시
누락 에셋별로 파일명, 설명, 사용 씬, 저장 위치를 안내. 권장: 500x500px+, PNG 투명배경.

> 한 번 만든 에셋은 모든 프로젝트에서 재사용!

---

## ⚠️ Manim 필수 규칙

```python
# 1. MathTex - r-string 필수
MathTex(r"\frac{a}{b}")  # ✅
MathTex("\frac{a}{b}")   # ❌

# 2. 한글 Text - 폰트 필수
Text("안녕", font="Noto Sans KR")  # ✅
Text("안녕")  # ❌

# 3. wait() - 태그 필수
self.wait(1.5)  # wait_tag_s1_1 ✅
self.wait(1.5)  # ❌

# 4. 수식 가독성
equation.set_stroke(width=8, background=True)  # 그림자
equation.add_background_rectangle()  # 배경

# 5. PNG 에셋 사용 (캐릭터/물체) - 루트 assets 폴더에서 로드
STICKMAN_HEIGHT = 4  # 기준 높이 (필수!)

stickman = ImageMobject("assets/characters/stickman_confused.png")
stickman.set_height(STICKMAN_HEIGHT).shift(LEFT*3)

snack = ImageMobject("assets/objects/snack_bag.png")
snack.set_height(STICKMAN_HEIGHT * 0.30).next_to(stickman, RIGHT)
```

# 직접 그리기 금지 ❌

# stickman_head = Circle(radius=0.3)

# stickman_body = Line(...)

```

---

## 🎨 컬러 팔레트

| 용도        | 색상   | 사용 예시                    |
| ----------- | ------ | ---------------------------- |
| 변수 (x, y) | YELLOW | `MathTex("x", color=YELLOW)` |
| 상수        | ORANGE | `MathTex("3", color=ORANGE)` |
| 결과/답     | GREEN  | `MathTex("=5", color=GREEN)` |
| 강조        | RED    | `Indicate(eq, color=RED)`    |
| 보조선      | GRAY_B | `axes.set_color(GRAY_B)`     |

---

## 🎨 스타일별 설정

### 스타일-색상 매핑표

| 스타일    | 배경 타입 | text_color_mode | 배경 색상 | Manim 텍스트 색상 |
| --------- | --------- | --------------- | --------- | ----------------- |
| minimal   | 어두운    | **light**       | #000000   | WHITE, YELLOW     |
| cyberpunk | 어두운    | **light**       | #0a0a0a   | CYAN, MAGENTA     |
| space     | 어두운    | **light**       | #000011   | WHITE, BLUE       |
| geometric | 어두운    | **light**       | #1a1a1a   | GOLD, YELLOW      |
| stickman  | 어두운    | **light**       | #1a2a3a   | WHITE, YELLOW     |
| **paper** | **밝은**  | **dark**        | #f5f5dc   | BLACK, DARK_BLUE  |

> `text_color_mode`: light=어두운배경→밝은텍스트, dark=밝은배경→어두운텍스트
>
> **cyberpunk/space**: 글로우 효과 적용 (`set_stroke width=15, opacity=0.3`)
> **stickman**: 캐릭터는 PNG 에셋 사용 (코드로 그리지 않음)

---

## 🎤 TTS 음성 옵션 (OpenAI TTS)

| 음성 | 특징 | 추천 용도 |
|------|------|----------|
| alloy | 중성적, 균형잡힌 | 균형 잡힌 설명 |
| echo | 남성적, 차분함 | 차분한 설명 |
| fable | 영국식 억양 | 특별한 분위기 |
| **onyx** | 남성적, 깊은 목소리 | 수학 교육 (기본값) |
| nova | 여성적, 밝고 친근 | 친근한 분위기 |
| shimmer | 여성적, 부드러움 | 부드러운 설명 |

> 🎧 **음성 샘플 듣기**: https://platform.openai.com/docs/guides/text-to-speech

### 비용 (유료)

| 항목 | 비용 |
|------|------|
| TTS | $15 / 1M 글자 |
| Whisper | $0.006 / 분 |

**예시 (3분 영상, 5개 씬):**
- TTS: 7,500 글자 ≈ $0.11
- Whisper: 15분 ≈ $0.09
- **총: 약 $0.20/영상**

> 일일 한도 없음! Gemini보다 안정적

### TTS 쉼(Pause) 규칙

| 구두점         | 효과          | 예시                         |
| -------------- | ------------- | ---------------------------- |
| `,` (쉼표)     | 짧은 쉼       | "미분은, 순간 변화율입니다." |
| `.` (마침표)   | 보통 쉼       | "이것이 핵심입니다."         |
| `...` (줄임표) | 긴 쉼, 망설임 | "그런데..."                  |
| 문단 나눔      | 호흡          | (빈 줄로 구분)               |

---

## 📝 이중 나레이션 체계

화면과 음성에 다른 텍스트 사용:

| 필드              | 용도      | 예시                  |
| ----------------- | --------- | --------------------- |
| narration_display | 화면 자막 | 9×9 = 81              |
| narration_tts     | TTS 음성  | 구 곱하기 구는 팔십일 |

### 변환 규칙

| 기호  | TTS 발음      |
| ----- | ------------- |
| ×     | 곱하기        |
| ÷     | 나누기        |
| =     | 는/은         |
| √     | 루트          |
| ²     | 제곱          |
| ³     | 세제곱        |
| f(x)  | 에프엑스      |
| dy/dx | 디와이 디엑스 |
| π     | 파이          |
| ∞     | 무한대        |

---

## 📁 프로젝트 구조

```

Math-Video-Maker/
├── CLAUDE.md ← 이 파일
├── state.json ← 현재 프로젝트 상태
├── math_video_pipeline.py ← CLI 도구
├── .env ← API 키 설정 (OPENAI_API_KEY)
│
├── assets/ ← 🔥 공용 에셋 폴더 (모든 프로젝트 공유)
│ ├── characters/ # 캐릭터 PNG
│ ├── objects/ # 물체 PNG
│ └── icons/ # 아이콘 PNG
│
├── skills/ ← 가이드라인 문서
│ ├── script-writer.md
│ ├── scene-director.md
│ ├── visual-planner.md
│ ├── manim-coder.md  
│ ├── manim-coder-reference.md ← 상세 패턴 (필요시 참조)
│ ├── code-validator.md
│ ├── image-prompt-writer.md
│ └── subtitle-designer.md
│
└── output/ ← 프로젝트별 출력
└── {project_id}/
├── 0_audio/ # TTS 음성 + 타이밍
├── 1_script/ # 대본
├── 2_scenes/ # 씬 분할
├── 4_manim_code/ # Manim 코드
├── 6_image_prompts/ # 이미지 프롬프트 + prompts_batch.txt
├── 7_subtitles/ # 자막
├── 8_renders/ # Manim 렌더링 결과
├── 9_backgrounds/ # 배경 이미지 (외부 생성)
├── 10_scene_final/ # 씬별 합성 영상
└── final_video.mp4 # 최종 영상

````

---

## 🔧 CLI 명령어 참조

```bash
# 프로젝트 초기화
python math_video_pipeline.py init --title "제목" --duration 480

# 상태 확인
python math_video_pipeline.py status

# TTS 생성
python math_video_pipeline.py tts-all

# 외부 녹음용 텍스트 내보내기
python math_video_pipeline.py tts-export

# 외부 녹음 파일 확인
python math_video_pipeline.py audio-check

# 외부 녹음 파일 처리 (Whisper 분석 + timing.json 생성)
python math_video_pipeline.py audio-process

# 이미지 프롬프트 내보내기
python math_video_pipeline.py prompts-export

# 이미지 상태 확인
python math_video_pipeline.py images-check

# 이미지 일괄 가져오기
python math_video_pipeline.py images-import --source "C:/Downloads/backgrounds"

# Manim 렌더링
python math_video_pipeline.py render-all

# SRT 자막 생성
python math_video_pipeline.py subtitle-generate

# 씬별 최종 합성 (배경 + Manim + 오디오 + 자막)
python math_video_pipeline.py compose-all

# 전체 영상 병합
python math_video_pipeline.py merge-final

# 도움말
python math_video_pipeline.py help
````

---

## 🎯 기타 명령어

| 사용자 입력         | Claude 동작                   |
| ------------------- | ----------------------------- |
| "시작"              | 새 프로젝트 시작 (Step 1부터) |
| "상태"              | 현재 프로젝트 상태 확인       |
| "계속"              | 중단된 지점부터 재개          |
| "대본 수정"         | 대본 수정 모드                |
| "씬 수정"           | 씬 분할 수정 모드             |
| "에셋 체크"         | 🆕 필요한 에셋 확인 (assets/) |
| "에셋 준비 완료"    | 🆕 에셋 재확인 후 다음 단계   |
| "에셋 목록"         | 🆕 현재 보유 에셋 목록 표시   |
| "외부 녹음"         | OpenAI TTS 대신 직접 녹음     |
| "오디오 파일 준비완료" | 🆕 녹음 파일 확인 후 처리   |
| "s1 코드"           | 특정 씬 Manim 코드 생성       |
| "프롬프트 내보내기" | 이미지 프롬프트 일괄 내보내기 |
| "이미지 확인"       | 배경 이미지 준비 상태 확인    |
| "렌더링"            | Manim 렌더링 시작             |
| "자막 생성"         | SRT 자막 파일 생성            |
| "합성"              | 최종 영상 합성 시작           |

---

## 🖼️ 배경 이미지 가이드

### 파일명 규칙

```
s1_bg.png, s2_bg.png, s3_bg.png, ...
(씬 ID + _bg + 확장자)

지원 확장자: .png, .jpg, .jpeg, .webp
```

### 이미지 생성 워크플로우

```
1. python math_video_pipeline.py prompts-export
   → 6_image_prompts/prompts_batch.txt 생성

2. prompts_batch.txt 내용을 이미지 생성 AI에 입력
   - Midjourney: Discord에서 /imagine
   - DALL-E: ChatGPT 또는 API
   - Leonardo.ai: 웹 인터페이스
   - Stable Diffusion: 로컬 또는 웹

3. 생성된 이미지 다운로드

4. 이미지 가져오기 (둘 중 하나 선택):
   - 수동: 9_backgrounds/ 폴더에 직접 저장 (파일명 변경)
   - 자동: python math_video_pipeline.py images-import --source "다운로드폴더"

5. python math_video_pipeline.py images-check
   → 누락된 이미지 확인
```

### 이미지 사양 권장

| 항목   | 16:9              | 9:16      |
| ------ | ----------------- | --------- |
| 해상도 | 1920×1080         | 1080×1920 |
| 포맷   | PNG (투명 불필요) | PNG       |
| 용량   | < 5MB             | < 5MB     |

---

## ⚡ 단축 워크플로우

빠른 진행을 원하면:

```
사용자: "시작"
Claude: 주제 물어봄
사용자: "피타고라스 정리 3분 cyberpunk"
Claude: 바로 전체 진행 (대본→씬→에셋체크→TTS→코드→렌더링)
```

---

## 🚨 중요 참고사항

- **Skills 파일은 참조용**: Claude가 읽고 가이드라인 따름
- **Python은 API 호출용**: TTS, Whisper, 렌더링
- **state.json으로 상태 추적**: 중단 후 재개 가능
- **각 단계 승인 후 진행**: 사용자 확인 없이 다음 단계 안 넘어감
- **OpenAI TTS 사용**: 유료지만 안정적, 일일 한도 없음
- **캐릭터/물체는 PNG 사용**: Manim으로 직접 그리면 품질 저하
- **에셋은 루트 폴더**: `assets/` 폴더는 모든 프로젝트가 공유
- **에셋 체크 단계 필수**: PNG 없으면 Manim 코드 생성 전에 사용자에게 요청

---

## 🔐 환경 설정 (.env)

```env
# OpenAI TTS (필수)
OPENAI_API_KEY=sk-proj-your-api-key-here
```

> API 키 발급: https://platform.openai.com/api-keys

---

## 📊 current_phase 값 목록

| phase 값        | 의미              | 다음 단계         |
| --------------- | ----------------- | ----------------- |
| initialized     | 프로젝트 생성됨   | 대본 작성         |
| script_approved | 대본 승인됨       | 씬 분할           |
| scenes_approved | 씬 분할 승인됨    | 에셋 체크         |
| assets_checked  | 에셋 확인 완료    | TTS 생성          |
| tts_completed   | TTS 생성 완료     | Manim 코드        |
| manim_coding    | 코드 작성 중      | 계속 코드 작성    |
| manim_completed | 모든 코드 완료    | 이미지 프롬프트   |
| images_ready    | 배경 이미지 준비  | Manim 렌더링      |
| rendering       | Manim 렌더링 중   | 렌더링 완료 대기  |
| rendered        | Manim 렌더링 완료 | 자막 및 최종 합성 |
| composing       | 최종 합성 중      | 합성 완료 대기    |
| completed       | 모든 작업 완료    | -                 |
