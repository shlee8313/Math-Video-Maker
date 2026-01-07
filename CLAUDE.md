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
   - **semantic_goal** (씬의 목적: "대비로 충격 주기")
   - **required_elements** (필요한 요소 목록)
   - **wow_moment** (강조 포인트)
   - **emotion_flow** (감정 흐름: "평범→의아→충격")
   - **is_3d** (3D 씬 여부: true/false)
   - **scene_class** (Scene 또는 ThreeDScene)
   - **camera_settings** (3D일 때 카메라 설정)
4. `output/{project_id}/2_scenes/scenes.json` 저장 (승인 없이 자동 진행)
5. **씬 분할 저장** (토큰 절약):
   ```bash
   python math_video_pipeline.py split-scenes
   ```
   → `2_scenes/s1.json`, `s2.json`, ... 개별 파일 생성
   → 이후 Claude가 필요한 씬만 읽어 토큰 80% 절약
6. **state.json 업데이트**: `current_phase: "scenes_approved"`, `files.scenes` 경로 저장

> 💡 **자동 생성**: 사용자 승인 없이 자동 진행. 수정이 필요하면 "씬 수정" 명령 사용.

✅ **이 시점에서 `/clear` 가능**

---

### Step 3.5: 에셋 체크 (Supabase 연동)

> **에셋 저장소**: Supabase Storage (`math-video-assets` 버킷)
> **메타데이터**: Supabase `assets` 테이블

Claude가 할 것:

1. `python math_video_pipeline.py asset-check` 실행
   - `scenes.json`에서 `required_elements` 중 이미지 타입 수집
   - Supabase `assets` 테이블에서 보유 목록 조회
   - **있으면** → 로컬 `assets/`에 다운로드 (캐시)
   - **없으면** → `missing_assets.json` 생성

2. **누락 에셋이 있으면 Claude가 두 개의 프롬프트 파일 생성**:
   - `skills/asset-prompt-writer.md` 읽기 ← **필수!**
   - `output/{project_id}/svg_ai_prompts.json` → 아이콘용 SVG AI 생성 프롬프트
   - `output/{project_id}/png_gemini_prompts.json` → 캐릭터/물체용 PNG Gemini 생성 프롬프트

3. 사용자가 이미지 생성:
   - **SVG**: AI에 프롬프트 입력 → SVG 생성 → `assets/icons/`에 저장
   - **PNG**: Gemini에 프롬프트 입력 → 이미지 생성 → **배경 제거** → `assets/`에 저장

4. 사용자가 "에셋 준비 완료" 입력

5. `python math_video_pipeline.py asset-sync` 실행
   - 신규 파일 감지 → Supabase Storage에 업로드
   - `assets` 테이블에 메타데이터 저장
   - 모든 파일 존재 확인 → Step 4 진행

6. **state.json 업데이트**: `current_phase: "assets_checked"`

### 프롬프트 생성 규칙 (상세: `skills/asset-prompt-writer.md`)

> **핵심**: AI가 투명 배경을 생성해도 실제로 투명하지 않음
> → **흰색 배경**으로 생성 후 배경 제거 도구 사용

| 항목 | 규칙 |
|------|------|
| 배경 | `solid white background` (투명 X) |
| 내부 | `solid filled design` (빈 내부 X) |
| Negative | `hollow, outline only, transparent inside` |

#### 카테고리별 크기
| 카테고리 | 크기 | 스타일 |
|----------|------|--------|
| characters | 500x700 px | 졸라맨 stick figure |
| icons | 300x300 px | minimalist 2D |
| objects | 500x500 px | minimalist 2D |

#### 졸라맨 캐릭터 필수 요소
- 얼굴: `solid peach/beige skin (#FFDAB9)`
- 몸: `black stick lines`
- 옷: 감정에 맞는 색상 (happy=#FFD700, worried=#808080 등)

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

3. **외부 녹음 선택 시:**
   - "외부 녹음을 진행합니다. 텍스트를 내보냅니다."
   - `python math_video_pipeline.py tts-export` 실행
   - 사용자에게 안내: `0_audio/tts_texts.json` 참조하여 문장별 녹음 (파일명: s1_1.mp3, s1_2.mp3...)
   - 사용자가 "오디오 파일 준비완료" 입력 시:
     - `python math_video_pipeline.py audio-check` 실행
     - 누락 파일 있으면 목록 안내
     - 모든 파일 존재 시 → 다음 진행
   - `python math_video_pipeline.py audio-process` 실행
     - Whisper로 각 파일 duration 분석
     - 씬별 timing.json 생성
   - **state.json 업데이트**: `current_phase: "tts_completed"`, `files.audio[]` 배열 저장

> ⚠️ **TTS 엔진 변경 시 주의**: 중간에 TTS 방식을 바꾸면 반드시 `0_audio/` 폴더를 비워야 합니다! (목소리가 섞이면 일관성이 깨짐)

✅ **이 시점에서 `/clear` 가능**

---

### Step 4.5: Visual Prompter (시각 설계) - 3단계 분리

> **역할**: Scene Director의 의미적 지시("What")를 Manim Coder가 바로 구현 가능한 구체적 시각 명세("How")로 변환
>
> **3단계 분리 이유**: 토큰 절약 + 실수 방지 (기존 대비 36% 토큰 절감)

---

#### Step 4.5a: Layout 단계 (객체 배치)

> **Sub-agent 사용**: `visual-layout` 에이전트에게 작업 위임
> 에이전트가 별도 컨텍스트에서 실행되어 메인 대화 컨텍스트 절약

Claude가 할 것:

1. **`visual-layout` 에이전트 호출** (Task tool 사용)
2. **개별 씬 파일 읽기** (토큰 절약):
   - `2_scenes/s1.json`, `s2.json`, ... (필요한 씬만)
   - ❌ `scenes.json` 전체 읽지 않음
3. 각 씬에 대해 **objects만** 정의:
   - **canvas**: 배경색, 안전 영역
   - **objects**: 모든 객체의 상세 스펙
     - id, type (Text/MathTex/ImageMobject/3D 등)
     - position (관계 기반 또는 절대 좌표)
     - size, color, font 등
     - 3D 객체는 `fixed_in_frame` 여부
   - **layout_notes**: 배치 의도 설명
4. 씬별 파일로 저장 → `output/{project_id}/3_visual_prompts/s{n}_layout.json`
5. 에이전트 완료 후 state.json 자동 업데이트

> 💡 **Sub-agent 장점**: 에이전트가 별도 컨텍스트에서 실행되므로 메인 대화 컨텍스트 오염 없음
> → 모든 씬을 한 번에 처리 가능 (기존 10씬마다 /clear 불필요)

✅ **Layout 전체 완료 후 Animation 단계로 자동 진행**

---

#### Step 4.5b: Animation 단계 (시퀀스 추가)

> **Sub-agent 사용**: `visual-animation` 에이전트에게 작업 위임
> 에이전트가 별도 컨텍스트에서 실행되어 메인 대화 컨텍스트 절약

Claude가 할 것:

1. **`visual-animation` 에이전트 호출** (Task tool 사용)
2. **개별 파일 읽기**:
   - `3_visual_prompts/s1_layout.json`, ... (해당 씬 레이아웃)
   - `0_audio/s1_timing.json`, ... (타이밍 데이터)
3. 각 씬에 대해 **sequence 추가**:
   - timing.json의 segments에 맞춰 시간 배분
   - step, time_range, actions, purpose
   - 나레이션 동기화
4. 최종 파일로 저장 → `output/{project_id}/3_visual_prompts/s{n}_visual.json`
5. 에이전트 완료 후 state.json 자동 업데이트

> 💡 **Sub-agent 장점**: 에이전트가 별도 컨텍스트에서 실행되므로 메인 대화 컨텍스트 오염 없음
> → 모든 씬을 한 번에 처리 가능 (기존 10씬마다 /clear 불필요)

✅ **Animation 전체 완료 후 Review 단계로 자동 진행**

---

#### Step 4.5c: Review 단계 (검증)

> **Sub-agent 사용**: `visual-review` 에이전트에게 작업 위임
> 에이전트가 별도 컨텍스트에서 실행되어 메인 대화 컨텍스트 절약

Claude가 할 것:

1. **`visual-review` 에이전트 호출** (Task tool 사용)
2. **visual.json 검증**:
   - 구조 검증: 필수 필드 존재 여부
   - objects 검증: id 고유성, 필수 필드, 세이프존
   - sequence 검증: 시간 연속성, target 참조
   - 3D 검증: scene_class, camera, fixed_in_frame
3. 오류 발견 시:
   - 자동 수정 가능 → 수정 적용
   - 수동 필요 → 목록 보고
4. 검증 통과 시 → "✅ s{n} 검증 완료" 출력
5. 에이전트 완료 후 state.json 자동 업데이트 (`current_phase: "visual_prompts_completed"`)

> 💡 **Sub-agent 장점**: 에이전트가 별도 컨텍스트에서 실행되므로 메인 대화 컨텍스트 오염 없음
> → 모든 씬을 한 번에 처리 가능 (기존 10씬마다 /clear 불필요)

✅ **Review 전체 완료 후 Manim 코드 단계로 자동 진행**

---

#### Visual Prompter 전체 흐름 요약 (Sub-agents 사용)

```
🚀 Sub-agents 도입으로 /clear 횟수 대폭 감소!

Visual Prompter 3단계 (50씬 기준):
├── visual-layout 에이전트: s1~s50 전체 Layout (별도 컨텍스트)
├── visual-animation 에이전트: s1~s50 전체 Animation (별도 컨텍스트)
└── visual-review 에이전트: s1~s50 전체 Review (별도 컨텍스트)

메인 대화 컨텍스트 사용량: 최소 (에이전트 호출/결과만)
→ /clear 필요 없이 전체 단계 완료 가능!
```

> 💡 **자동 생성**: 사용자 승인 없이 자동 진행. 수정이 필요하면 "s3 비주얼 수정" 명령 사용.
>
> 💡 **Sub-agent 장점**: 각 에이전트가 독립 컨텍스트에서 실행 → 메인 대화 컨텍스트 절약

✅ **Visual Prompter 완료 후 Manim 코드 단계로 진행**

---

### Step 5: Manim 코드 생성

> **Sub-agent 사용**: `manim-coder` 에이전트에게 작업 위임
> 에이전트가 별도 컨텍스트에서 실행되어 메인 대화 컨텍스트 절약

Claude가 할 것:

1. **`manim-coder` 에이전트 호출** (Task tool 사용)
   - 에이전트가 `skills/manim-coder-reference.md` 참조
2. **모든 씬 처리** (별도 컨텍스트에서 실행):
   - Visual Prompter JSON 로드 (`3_visual_prompts/s{n}_visual.json`)
   - 타이밍 데이터 로드 (`0_audio/{scene_id}_timing.json`)
   - JSON을 Python 코드로 변환:
     - objects → Mobject 생성 코드
     - sequence → self.play() / self.wait() 코드
     - 3D 씬은 ThreeDScene 사용, fixed_in_frame 처리
   - 필수 규칙 적용:
     - `MathTex(r"...")` - r-string
     - `Text("한글", font="Noto Sans KR")`
     - `self.wait(n)  # wait_tag_s{씬}_{순서}`
     - 컬러 팔레트 준수
     - **PNG 에셋은 ImageMobject + set_height() 사용**
   - `output/{project_id}/4_manim_code/s{n}_manim.py` 저장
3. 에이전트 완료 후 state.json 자동 업데이트 (`current_phase: "manim_completed"`)

> 💡 **Sub-agent 장점**: 에이전트가 별도 컨텍스트에서 실행되므로 메인 대화 컨텍스트 오염 없음
> → 모든 씬을 한 번에 처리 가능 (기존 15씬마다 /clear 불필요)

✅ **Manim 코드 전체 완료 후 배경 이미지 단계로 진행**

#### 필수 코드 규칙

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

# 4. PNG 에셋 - set_height() 필수
stickman = ImageMobject("assets/characters/stickman.png")
stickman.set_height(4)  # ✅

# 5. 3D 씬 - ThreeDScene + fixed_in_frame
class S5Scene(ThreeDScene):
    def construct(self):
        self.add_fixed_in_frame_mobjects(title)  # 텍스트는 fixed
```

**출력 파일**: `4_manim_code/s{n}_manim.py`

모든 씬 완료 후 → "모든 Manim 코드 생성 완료!" 알림

✅ **완료 후 state.json**: `current_phase: "manim_completed"`

---

### Step 5.1: 코드 검증

> Step 5 완료 후 자동으로 검증 수행

```bash
# 검증 자동화 (추후 구현 예정)
python math_video_pipeline.py validate-all
```

**검증 항목**:
- MathTex r-string, 중괄호 짝, 한글 폰트
- Transform 타겟 존재, 3D Scene 클래스 일치
- wait() 태그, TTS 길이 vs 애니메이션 길이

✅ **완료 후 state.json**: `current_phase: "manim_validated"`

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
3. **자동 처리됨**:
   - 렌더링 완료 후 `media/videos/`에서 `8_renders/`로 자동 수집
   - `state.json` 자동 업데이트 (`current_phase: "rendered"`, `files.renders[]`)
4. **렌더링 완료 후 Claude가 반드시 안내**:
   - "✅ 렌더링 완료! {N}개 씬이 `8_renders/`에 저장되었습니다."
   - "다음 단계: 자막 생성 (`python math_video_pipeline.py subtitle-generate`)"
   - 사용자에게 다음 진행 여부 확인

> 💡 **참고**: 수동 수집이 필요하면 `python math_video_pipeline.py render-collect` 실행
>
> ⚠️ **Manim 출력 경로**:
> - 원본 출력: `media/videos/{scene_id}_manim/{품질폴더}/` (예: 480p15, 1080p60)
> - 수집 후: `output/{project_id}/8_renders/s1.mov`, `s2.mov`, ...

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

## 🔄 /clear 가능 지점 (Sub-agents 도입 후)

> 🚀 **Sub-agents 도입으로 /clear 횟수 대폭 감소!**
> 에이전트가 별도 컨텍스트에서 실행되어 메인 대화 오염 최소화

### /clear 가능 지점 요약

| 지점   | 타이밍                     | 저장된 파일                       | state.json phase         | 재개 명령 |
| ------ | -------------------------- | --------------------------------- | ------------------------ | --------- |
| #2     | 대본 승인 후               | `1_script/*.json`                 | script_approved          | "계속" |
| #3     | 씬 분할 승인 후            | `2_scenes/scenes.json`            | scenes_approved          | "계속" |
| #3.5   | 에셋 체크 완료 후          | `assets/` 폴더 PNG 파일들         | assets_checked           | "계속" |
| #4     | TTS 생성 완료 후           | `0_audio/*.mp3, *.json`           | tts_completed            | "계속" |
| #4.5   | **Visual Prompter 전체 완료** | 모든 `*_visual.json`           | visual_prompts_completed | "계속" |
| #5     | **Manim 코드 전체 완료**   | 모든 `_manim.py`                  | manim_completed          | "계속" |
| #5.1   | 코드 검증 완료 후          | 모든 `_manim.py` 검증됨           | manim_validated          | "계속" |
| #5.5   | 이미지 준비 완료 후        | `9_backgrounds/*.png`             | images_ready             | "렌더링" |
| #6     | Manim 렌더링 완료 후       | `8_renders/*.mp4`                 | rendered                 | "자막 생성" |

> 💡 **변경 사항**: Visual Prompter와 Manim Coder가 Sub-agents로 실행되어
> 기존 10씬/15씬 단위 /clear가 불필요해짐

### ⚠️ /clear 금지 구간

| 구간                     | 이유                   |
| ------------------------ | ---------------------- |
| 대본 작성 **중**         | 승인 전이라 저장 안 됨 |
| 씬 분할 **중**           | 승인 전이라 저장 안 됨 |
| 에셋 체크 **중**         | 확인 완료 전           |
| TTS 생성 **중**          | API 호출 중단됨        |

> 💡 **Sub-agents 실행 중**: 에이전트가 별도 컨텍스트에서 실행되므로
> 메인 대화에서는 에이전트 완료를 기다리면 됨 (컨텍스트 오염 없음)

### /clear 후 재개 방법

```
사용자: "계속" 또는 "상태"
Claude: state.json 읽고 현재 단계 파악 → 이어서 진행
```

### 권장 워크플로우 (Sub-agents 사용, 56씬 기준)

```
🚀 기존 27세션 → 7~8세션으로 감소!

준비 단계:
├── 세션 1: 시작 → 대본 승인 → /clear (선택)
├── 세션 2: 씬 분할 → 에셋 체크 → /clear (선택)
└── 세션 3: TTS 생성 완료

Visual Prompter + Manim 코드 (Sub-agents):
├── 세션 4: visual-layout 에이전트 → 전체 Layout 완료
├── 세션 5: visual-animation 에이전트 → 전체 Animation 완료
├── 세션 6: visual-review 에이전트 → 전체 Review 완료
└── 세션 7: manim-coder 에이전트 → 전체 코드 완료

마무리:
└── 세션 8: 렌더링 → 자막 → 합성 → 완료
```

---

## 📊 state.json 구조

```json
{
  "project_id": "P20250615_143000",
  "title": "피타고라스 정리",
  "current_phase": "visual_animation_in_progress",
  "settings": {
    "style": "cyberpunk",
    "difficulty": "intermediate",
    "duration": 300,
    "aspect_ratio": "16:9",
    "voice": "ash"
  },
  "scenes": {
    "total": 50,
    "completed": [],
    "pending": ["s1", "s2", "...", "s50"],
    "current": null
  },
  "visual_progress": {
    "stage": "animation",
    "completed_scenes": ["s1", "s2", "...", "s35"],
    "next_scene": "s36"
  },
  "files": {
    "script": "output/P20250615_143000/1_script/reading_script.json",
    "scenes": "output/P20250615_143000/2_scenes/scenes.json",
    "visual_layouts": ["s1_layout.json", "...", "s50_layout.json"],
    "visual_prompts": ["s1_visual.json", "...", "s35_visual.json"],
    "audio": ["s1.mp3", "...", "s50.mp3"],
    "manim": []
  },
  "assets": {
    "required": ["characters/stickman_confused.png", "objects/snack_bag.png"],
    "available": ["characters/stickman_confused.png", "objects/snack_bag.png"],
    "missing": []
  },
  "last_updated": "2025-06-15T14:35:00"
}
```

### state.json 자동 업데이트 규칙 (Sub-agents 사용)

| 단계 완료  | current_phase                  | 주요 업데이트                                       |
| ---------- | ------------------------------ | --------------------------------------------------- |
| Step 2     | script_approved                | files.script, files.tts_script                      |
| Step 3     | scenes_approved                | files.scenes, scenes.total/pending, assets.required |
| Step 3.5   | assets_checked                 | assets.available, assets.missing=[]                 |
| Step 4     | tts_completed                  | files.audio[]                                       |
| **Step 4.5 (전체완료)** | visual_prompts_completed | files.visual_prompts[] (에이전트가 자동 업데이트) |
| **Step 5 (전체완료)** | manim_completed | files.manim[] (에이전트가 자동 업데이트) |
| Step 5.5   | images_ready                   | files.images[]                                      |
| Step 6     | rendered                       | -                                                   |
| Step 7     | completed                      | files.final_video                                   |

### 💡 Sub-agents와 state.json

> Sub-agents 사용 시 각 에이전트가 작업 완료 후 state.json을 자동 업데이트합니다.
> 사용자가 수동으로 체크할 필요 없음!

**에이전트 완료 후 자동 업데이트 예시:**
```json
{
  "current_phase": "visual_prompts_completed",
  "files": {
    "visual_prompts": ["s1_visual.json", ..., "s50_visual.json"]
  },
  "last_updated": "2025-06-15T14:35:00"
}
```

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
assets/                  ← 루트 레벨 (모든 프로젝트 공용)
├── characters/          # stickman_*.png (캐릭터)
├── objects/             # 물체 PNG
├── icons/               # 아이콘 PNG
└── metaphors/           # 은유/비유 PNG
```

### 에셋 파일 사양

- 해상도: 500x500px+, PNG 투명배경
- 파일명: `{이름}_{상태}.png` (예: stickman_happy.png)
- **상세 목록**: `skills/asset-catalog.md` 참조 (Supabase에서 자동 생성)

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

# 6. 3D 씬에서 텍스트
# ThreeDScene에서 Text/MathTex는 반드시 fixed_in_frame 처리
self.add_fixed_in_frame_mobjects(title)

# 7. 그래프 (Axes) - 🔴 필수 체크리스트
# 그래프를 그릴 때 반드시 아래 모든 요소 포함!
axes = Axes(x_range=[0,10,2], y_range=[0,10,2], ...)

# (1) 축 레이블 - 필수! (기호 사용, 한글만 X)
# ✅ "P" 또는 "가격(P)" / ❌ "가격" (한글만 안됨!)
y_label = MathTex("P", font_size=28)  # 기호
x_label = MathTex("Q", font_size=28)  # 기호
y_label.next_to(axes.y_axis, UP, buff=0.1)
x_label.next_to(axes.x_axis, RIGHT, buff=0.1)

# (2) 곡선 레이블 - 필수! (곡선 끝에 작게)
mr_label = Text("MR", font_size=20, color=GREEN)
mr_label.next_to(mr_curve.get_end(), UR, buff=0.1)

# (3) 교차점 - 실제 좌표 계산 필수!
# ❌ 대충 찍기: Dot(axes.c2p(3, 2))
# ✅ 계산 후 찍기: x=5.6 (MR=MC 해 구하기), Dot(axes.c2p(5.6, 5.2))
```

---

## 🎨 컬러 팔레트

### 기본 수학용

| 용도        | 색상   | 사용 예시                    |
| ----------- | ------ | ---------------------------- |
| 변수 (x, y) | YELLOW | `MathTex("x", color=YELLOW)` |
| 상수        | ORANGE | `MathTex("3", color=ORANGE)` |
| 결과/답     | GREEN  | `MathTex("=5", color=GREEN)` |
| 강조        | RED    | `Indicate(eq, color=RED)`    |
| 보조선      | GRAY_B | `axes.set_color(GRAY_B)`     |

### 경제학/비즈니스 Visual Coding

> 영상 전체에서 동일 개념은 동일 색상으로 일관성 유지

| 개념 | 기호 | 색상 | HEX | Manim |
| ---- | ---- | ---- | --- | ----- |
| 가격 (Price) | P | 파란색 | #58C4DD | `BLUE` 또는 `"#58C4DD"` |
| 수량 (Quantity) | Q | 노란색 | #EEEEEE | `YELLOW` 또는 `"#EEEEEE"` |
| 이윤 (Profit) | Π | 초록색 | #83C167 | `GREEN` 또는 `"#83C167"` |
| 탄력성 (Elasticity) | E_d | 분홍색 | #FC6255 | `RED` 또는 `"#FC6255"` |
| 비용 (Cost) | C | 회색 | #888888 | `GRAY` |
| 한계수입 (MR) | MR | 청록색 | #00CED1 | `"#00CED1"` |
| 한계비용 (MC) | MC | 주황색 | #FFA500 | `ORANGE` |

```python
# 예시: 이윤 극대화 조건
profit_eq = MathTex(r"\Pi", r"=", r"P", r"\cdot", r"Q", r"-", r"C")
profit_eq[0].set_color("#83C167")  # Π 초록
profit_eq[2].set_color("#58C4DD")  # P 파랑
profit_eq[4].set_color("#EEEEEE")  # Q 노랑
profit_eq[6].set_color("#888888")  # C 회색
```

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

## 🎤 TTS 음성 옵션 (OpenAI gpt-4o-mini-tts)

| 음성    | 특징                | 추천 용도              |
| ------- | ------------------- | ---------------------- |
| **ash** | 차분한 남성         | 수학 교육 **(기본값)** |
| nova    | 여성적, 밝고 친근   | 친근한 분위기          |
| onyx    | 남성적, 깊은 목소리 | 권위있는 설명          |

> 전체 음성 목록: https://platform.openai.com/docs/guides/text-to-speech

### 비용 (유료)

| 항목            | 비용                    |
| --------------- | ----------------------- |
| gpt-4o-mini-tts | $0.60 / 1M 글자 (저렴!) |
| Whisper         | $0.006 / 분             |

**예시**: 10분 영상 ≈ $0.06 (TTS + Whisper)

### TTS 쉼(Pause) 규칙

쉼표(,)=짧은 쉼, 마침표(.)=보통 쉼, 줄임표(...)=긴 쉼

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
├── CLAUDE.md                      ← 이 파일
├── state.json                     ← 현재 프로젝트 상태
├── math_video_pipeline.py         ← CLI 도구
├── .env                           ← API 키 설정 (OPENAI_API_KEY)
│
├── .claude/                       ← 🔥 Claude Code 설정
│   └── agents/                        # Sub-agents (별도 컨텍스트 실행)
│       ├── visual-layout.md           # Layout 단계 에이전트
│       ├── visual-animation.md        # Animation 단계 에이전트
│       ├── visual-review.md           # Review 단계 에이전트
│       └── manim-coder.md             # Manim 코드 생성 에이전트
│
├── assets/                        ← 🔥 공용 에셋 폴더 (모든 프로젝트 공유)
│   ├── characters/                    # 캐릭터 PNG
│   ├── objects/                       # 물체 PNG
│   └── icons/                         # 아이콘 PNG
│
├── skills/                        ← 가이드라인 문서 (참조용)
│   ├── script-writer.md
│   ├── scene-director.md              # Step 3: 씬 분할 (What)
│   ├── visual-prompter-layout.md      # Step 4.5a: 객체 배치
│   ├── visual-prompter-animation.md   # Step 4.5b: 시퀀스 추가
│   ├── visual-prompter-review.md      # Step 4.5c: 검증
│   ├── manim-visual-prompter.md       # (참조용, 전체 규칙)
│   ├── manim-coder.md                 # Step 5: 코드 구현 (Code)
│   ├── code-validator.md              # Step 5.1: 코드 검증/수정
│   ├── manim-coder-reference.md       # 상세 패턴 (필요시 참조)
│   ├── asset-catalog.md
│   ├── asset-prompt-writer.md
│   ├── image-prompt-writer.md
│   └── subtitle-designer.md
│
└── output/                        ← 프로젝트별 출력
    └── {project_id}/
        ├── 0_audio/                   # TTS 음성 + 타이밍
        ├── 1_script/                  # 대본
        ├── 2_scenes/                  # 씬 분할 (scenes.json)
        ├── 3_visual_prompts/          # 시각 프롬프트 ← NEW
        │   ├── s1_visual.json
        │   ├── s2_visual.json
        │   └── ...
        ├── 4_manim_code/              # Manim 코드
        ├── 6_image_prompts/           # 배경 이미지 프롬프트
        ├── 7_subtitles/               # 자막
        ├── 8_renders/                 # Manim 렌더링 결과
        ├── 9_backgrounds/             # 배경 이미지 (외부 생성)
        ├── 10_scene_final/            # 씬별 합성 영상
        └── final_video.mp4            # 최종 영상
```

---

## 🔧 CLI 명령어 참조

```bash
# 프로젝트 초기화
python math_video_pipeline.py init --title "제목" --duration 480

# 상태 확인
python math_video_pipeline.py status

# 씬 분할 저장 (토큰 절약)
python math_video_pipeline.py split-scenes

# 에셋 체크 (Supabase 조회 + 다운로드 + 누락 목록 생성)
python math_video_pipeline.py asset-check

# 에셋 동기화 (로컬 신규 파일 → Supabase 업로드)
python math_video_pipeline.py asset-sync

# TTS 생성
python math_video_pipeline.py tts-all

# 외부 녹음용 텍스트 내보내기
python math_video_pipeline.py tts-export

# 외부 녹음 파일 확인
python math_video_pipeline.py audio-check

# 외부 녹음 파일 처리 (Whisper 분석 + timing.json 생성)
python math_video_pipeline.py audio-process

# ===== 자동화 명령어 (NEW) =====

# Visual Prompter 전체 자동화 (Layout → Animation → Review)
python math_video_pipeline.py visual-all
python math_video_pipeline.py visual-all --batch 5  # 배치 크기 조정

# Visual Prompter 단계별 실행
python math_video_pipeline.py visual-layout-all     # Layout만
python math_video_pipeline.py visual-animation-all  # Animation만
python math_video_pipeline.py visual-review-all     # Review만

# Manim 코드 전체 자동화
python math_video_pipeline.py manim-all
python math_video_pipeline.py manim-all --batch 10  # 배치 크기 조정

# ===== 렌더링 및 합성 =====

# 이미지 프롬프트 내보내기
python math_video_pipeline.py prompts-export

# 이미지 상태 확인
python math_video_pipeline.py images-check

# 이미지 일괄 가져오기
python math_video_pipeline.py images-import --source "C:/Downloads/backgrounds"

# Manim 렌더링
python math_video_pipeline.py render-all

# 렌더링 결과물 수집 (media/videos/ → 8_renders/)
python math_video_pipeline.py render-collect

# SRT 자막 생성
python math_video_pipeline.py subtitle-generate

# 씬별 최종 합성 (배경 + Manim + 오디오 + 자막)
python math_video_pipeline.py compose-all

# 전체 영상 병합
python math_video_pipeline.py merge-final

# 도움말
python math_video_pipeline.py help
```

---

## 🔧 씬 수정 (Post-Production)

> **사용 시점**: final 영상 생성 후 특정 씬 수정이 필요할 때

사용자가 씬 수정 요청 시 (예: "s7 수정", "s7 TTS 재생성", "s16 뒤에 새 씬 추가"):

**Claude가 할 것**:
1. `skills/scene-editor.md` 읽기 ← **필수!**
2. 수정 유형 파악
3. scene-editor.md의 절차에 따라 진행

### 씬 수정 명령어

| 사용자 입력 | Claude 동작 |
|-------------|-------------|
| "s7 수정" | 수정 유형 질문 → 해당 파이프라인 실행 |
| "s7 TTS 재생성" | `scene-editor.md` 읽기 → tts → subtitle → compose |
| "s7 Manim 수정" | `scene-editor.md` 읽기 → visual → manim → render → compose |
| "s7 자막 수정" | `scene-editor.md` 읽기 → srt 수정 → compose |
| "s7 내용 수정" | `scene-editor.md` 읽기 → scene → tts → visual → manim → render → subtitle → compose |
| "s16 뒤에 새 씬 추가" | `scene-editor.md` 읽기 → 새 씬 풀 파이프라인 |
| "s15 삭제" | `scene-editor.md` 읽기 → scenes.json 수정 → merge |
| "s7 배경 교체" | `scene-editor.md` 읽기 → 이미지 교체 → compose |

### 씬 단위 CLI 명령어

```bash
# ⚠️ 수정 전 필수: 대본-TTS 동기화 검증
python math_video_pipeline.py verify-sync         # 전체 검증
python math_video_pipeline.py verify-sync s7      # 특정 씬 검증

# 개별 씬 처리 명령어
python math_video_pipeline.py tts-scene s7        # TTS 재생성
python math_video_pipeline.py render-scene s7     # Manim 렌더링
python math_video_pipeline.py subtitle-scene s7   # 자막 생성
python math_video_pipeline.py compose-scene s7    # 합성

# 최종 병합
python math_video_pipeline.py merge-final
```

---

## 🎯 기타 명령어

| 사용자 입력 | Claude 동작 |
|-------------|-------------|
| "시작" | 새 프로젝트 시작 |
| "상태" / "계속" | 상태 확인 / 재개 |
| "에셋 체크" / "에셋 준비 완료" | 에셋 확인 |
| "렌더링" / "자막 생성" / "합성" | 해당 단계 실행 |

---

## 🖼️ 배경 이미지 가이드

- **파일명**: `s1_bg.png`, `s2_bg.png`, ... (지원: png, jpg, webp)
- **해상도**: 1920×1080 (16:9) 또는 1080×1920 (9:16)
- **워크플로우**: `prompts-export` → AI 생성 → `9_backgrounds/`에 저장 → `images-check`

---

## ⚡ 단축 워크플로우

빠른 진행을 원하면:

```
사용자: "시작"
Claude: 주제 물어봄
사용자: "피타고라스 정리 3분 cyberpunk"
Claude: 바로 전체 진행 (대본→씬→에셋체크→TTS→Visual Prompter→코드→렌더링)
```

---

## 🔗 3단계 파이프라인 (핵심)

```
┌─────────────────┐    ┌─────────────────────┐    ┌─────────────────┐
│  Scene Director │ → │  Visual Prompter    │ → │   Manim Coder   │
│   (Step 3)      │    │   (Step 4.5)        │    │   (Step 5)      │
├─────────────────┤    ├─────────────────────┤    ├─────────────────┤
│ "무엇을" (What) │    │ "어떻게" (How)      │    │ "코드로" (Code) │
│                 │    │                     │    │                 │
│ • semantic_goal │ →  │ • objects (상세)    │ →  │ • Python 코드   │
│ • required_elem │    │ • sequence (시간순) │    │ • wait_tag      │
│ • wow_moment    │    │ • positions (구체)  │    │ • 렌더링 가능   │
│ • emotion_flow  │    │ • visual_notes      │    │                 │
└─────────────────┘    └─────────────────────┘    └─────────────────┘
   scenes.json            s{n}_visual.json          s{n}_manim.py
```

---

## 🚨 중요 참고사항

- **Sub-agents 사용**: Visual Prompter(Layout/Animation/Review)와 Manim Coder는 별도 에이전트로 실행 → 메인 컨텍스트 절약
- **Skills 파일은 참조용**: 에이전트가 읽고 가이드라인 따름 (`.claude/agents/` 폴더에 에이전트 정의)
- **Python은 API 호출용**: TTS, Whisper, 렌더링
- **state.json으로 상태 추적**: 중단 후 재개 가능
- **각 단계 승인 후 진행**: 사용자 확인 없이 다음 단계 안 넘어감 (Visual Prompter는 자동)
- **OpenAI TTS 사용**: 유료지만 안정적, 일일 한도 없음
- **캐릭터/물체는 PNG 사용**: Manim으로 직접 그리면 품질 저하
- **에셋은 루트 폴더**: `assets/` 폴더는 모든 프로젝트가 공유
- **에셋 체크 단계 필수**: PNG 없으면 Manim 코드 생성 전에 사용자에게 요청
- **Visual Prompter는 자동**: 씬별로 자동 생성, 수정 필요시 명령어 사용

---

## 🔐 환경 설정 (.env)

```env
# OpenAI TTS (필수)
OPENAI_API_KEY=sk-proj-your-api-key-here

# Supabase (에셋 관리)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
```

> API 키 발급:
> - OpenAI: https://platform.openai.com/api-keys
> - Supabase: Dashboard → Settings → API

---

## 📊 current_phase 값 목록

| phase 값                     | 의미                     | 다음 단계           |
| ---------------------------- | ------------------------ | ------------------- |
| initialized                  | 프로젝트 생성됨          | 대본 작성           |
| script_approved              | 대본 승인됨              | 씬 분할             |
| scenes_approved              | 씬 분할 승인됨           | 에셋 체크           |
| assets_checked               | 에셋 확인 완료           | TTS 생성            |
| tts_completed                | TTS 생성 완료            | Visual Layout       |
| visual_layout_in_progress    | Layout 작성 중           | 계속 Layout         |
| visual_animation_in_progress | Animation 작성 중        | 계속 Animation      |
| visual_review_in_progress    | Review 진행 중           | 계속 Review         |
| visual_prompts_completed     | 시각 프롬프트 완료       | Manim 코드          |
| manim_coding                 | 코드 작성 중             | 계속 코드 작성      |
| manim_completed              | 모든 코드 완료           | 코드 검증           |
| manim_validated              | 코드 검증 완료           | 이미지 프롬프트     |
| images_ready                 | 배경 이미지 준비         | Manim 렌더링        |
| rendering                    | Manim 렌더링 중          | 렌더링 완료 대기    |
| rendered                     | Manim 렌더링 완료        | 자막 및 최종 합성   |
| composing                    | 최종 합성 중             | 합성 완료 대기      |
| completed                    | 모든 작업 완료           | -                   |
