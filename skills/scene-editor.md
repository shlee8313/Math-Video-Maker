# Scene Editor - 씬 수정 가이드

> **역할**: 완성된 영상의 개별 씬을 수정/추가/삭제하는 가이드
> **사용 시점**: final 영상 생성 후 수정이 필요할 때

---

## 🚀 수정 방식 선택

> **1-2개 씬 수정**: Claude가 직접 처리 (빠름)
> **3개 이상 씬 수정**: Sub-agents 사용 권장 (컨텍스트 절약)

| 수정 씬 개수 | 권장 방식 | 이유 |
|-------------|-----------|------|
| 1-2개 | **직접 수정** | 에이전트 호출 오버헤드 > 직접 처리 |
| 3개 이상 | **Sub-agents** | 컨텍스트 절약, 일관성 보장 |
| 10개 이상 | **Sub-agents 필수** | 메인 컨텍스트 오염 방지 |

---

## ⚠️ 수정 전 필수 검증

> **중요**: 씬 내용(narration) 수정 시 반드시 대본-TTS 동기화 검증 필요!

### 동기화 검증 명령어

```bash
# 전체 씬 검증
python math_video_pipeline.py verify-sync

# 특정 씬만 검증
python math_video_pipeline.py verify-sync s7
```

### 검증 결과 해석

| 결과 | 의미 | 조치 |
|------|------|------|
| ✅ 일치 | 대본 = TTS 녹음 | 정상, 자막/Manim만 수정 가능 |
| ❌ 불일치 | 대본 ≠ TTS 녹음 | TTS 재생성 필수 |
| ⚠️ 타이밍 파일 없음 | TTS 미생성 | TTS 생성 필요 |

### Claude가 내용 수정 시 반드시:

1. **수정 전**: `python math_video_pipeline.py verify-sync s{n}` 실행
2. **narration_tts 변경 시**: TTS 재생성 필수 안내
3. **narration_display만 변경 시**: 자막 재생성만 필요

---

## 📋 수정 유형별 파이프라인

### 파이프라인 단계 (전체)
```
script → scenes → tts → visual → manim → render → subtitle → compose → merge
   1        2       3       4        5        6         7          8        9
```

### 단계별 실행 방식

| 단계 | 실행 방식 | Claude 필요 | Sub-agent |
|------|-----------|-------------|-----------|
| script | Claude 작성 | ✅ | - |
| scenes | Claude 작성 | ✅ | - |
| tts | `python math_video_pipeline.py tts-scene {id}` | ❌ | - |
| visual | Claude 작성 또는 Sub-agent | ✅ | `visual-layout`, `visual-animation`, `visual-review` |
| manim | Claude 작성 또는 Sub-agent | ✅ | `manim-coder` |
| render | `python math_video_pipeline.py render-scene {id}` | ❌ | - |
| subtitle | `python math_video_pipeline.py subtitle-scene {id}` | ❌ | - |
| compose | `python math_video_pipeline.py compose-scene {id}` | ❌ | - |
| merge | `python math_video_pipeline.py merge-final` | ❌ | - |

---

## 🔧 수정 유형별 절차 (직접 수정 - 1-2개 씬)

### 1. TTS 재생성 (음성만 수정)

**사용 케이스**: TTS가 이상하게 녹음된 경우

**필요 단계**: tts → subtitle → compose

**Claude가 할 것**:
1. `2_scenes/s{n}.json`의 `narration_tts` 확인/수정 (필요시)
2. 다음 명령어 순차 실행:
   ```bash
   python math_video_pipeline.py tts-scene s7
   python math_video_pipeline.py subtitle-scene s7
   python math_video_pipeline.py compose-scene s7
   ```
3. 결과 확인 안내

---

### 2. Manim 수정 (애니메이션만 수정)

**사용 케이스**: Manim 렌더링 결과가 이상한 경우

**필요 단계**: visual → manim → render → compose

**Claude가 할 것**:
1. `skills/visual-prompter-layout.md` 읽기 (필요시)
2. `skills/manim-coder.md` 읽기
3. `3_visual_prompts/s{n}_visual.json` 확인/수정
4. `4_manim_code/s{n}_manim.py` 수정
5. 다음 명령어 순차 실행:
   ```bash
   python math_video_pipeline.py render-scene s7
   python math_video_pipeline.py compose-scene s7
   ```
6. 결과 확인 안내

---

### 3. 자막만 수정

**사용 케이스**: 자막 텍스트나 타이밍만 수정

**필요 단계**: subtitle → compose

**Claude가 할 것**:
1. `7_subtitles/s{n}.srt` 직접 수정
2. 다음 명령어 실행:
   ```bash
   python math_video_pipeline.py compose-scene s7
   ```
3. 결과 확인 안내

---

### 4. 내용 전체 수정

**사용 케이스**: 대사, 설명 등 내용 자체를 변경

**필요 단계**: scenes → tts → visual → manim → render → subtitle → compose

**Claude가 할 것**:
1. `2_scenes/s{n}.json` 수정 (narration_display, narration_tts 등)
2. `skills/visual-prompter-layout.md`, `skills/visual-prompter-animation.md` 읽기
3. `3_visual_prompts/s{n}_visual.json` 수정
4. `skills/manim-coder.md` 읽기
5. `4_manim_code/s{n}_manim.py` 수정
6. 다음 명령어 순차 실행:
   ```bash
   python math_video_pipeline.py tts-scene s7
   python math_video_pipeline.py render-scene s7
   python math_video_pipeline.py subtitle-scene s7
   python math_video_pipeline.py compose-scene s7
   ```
7. 결과 확인 안내

---

### 5. 씬 삽입 (새 씬 추가)

**사용 케이스**: s16과 s17 사이에 새 씬 추가

**필요 단계**: 새 씬 풀 파이프라인

**Claude가 할 것**:
1. 새 씬 ID 결정 (예: `s16b`)
2. `2_scenes/s16b.json` 생성:
   ```json
   {
     "scene_id": "s16b",
     "section": "...",
     "duration": ...,
     "narration_display": "...",
     "narration_tts": "...",
     ...
   }
   ```
3. `skills/visual-prompter-layout.md`, `skills/visual-prompter-animation.md` 읽기
4. `3_visual_prompts/s16b_layout.json`, `s16b_visual.json` 생성
5. `skills/manim-coder.md` 읽기
6. `4_manim_code/s16b_manim.py` 생성
7. 다음 명령어 순차 실행:
   ```bash
   python math_video_pipeline.py tts-scene s16b
   python math_video_pipeline.py render-scene s16b
   python math_video_pipeline.py subtitle-scene s16b
   python math_video_pipeline.py compose-scene s16b
   ```
8. `scenes.json`에 s16b 추가 (s16 다음 위치)
9. `state.json` 업데이트
10. `python math_video_pipeline.py merge-final` (전체 병합 필요시)

---

### 6. 씬 삭제

**사용 케이스**: 특정 씬이 불필요해서 삭제

**필요 단계**: scenes.json 수정 → merge

**Claude가 할 것**:
1. `2_scenes/scenes.json`에서 해당 씬 제거
2. `2_scenes/s{n}.json` 파일 삭제 (또는 보관)
3. `state.json` 업데이트
4. `python math_video_pipeline.py merge-final --exclude s15` 또는 전체 재병합

---

### 7. 씬 순서 변경

**사용 케이스**: s20을 s10 뒤로 이동

**필요 단계**: scenes.json 수정 → merge

**Claude가 할 것**:
1. `2_scenes/scenes.json`에서 씬 순서 변경
2. `python math_video_pipeline.py merge-final`

---

### 8. 배경만 교체

**사용 케이스**: Manim/TTS 유지, 배경 이미지만 변경

**필요 단계**: compose

**Claude가 할 것**:
1. 새 배경 이미지를 `9_backgrounds/s{n}_bg.png`로 저장
2. 다음 명령어 실행:
   ```bash
   python math_video_pipeline.py compose-scene s7
   ```

---

### 9. 자막 스타일 변경 (전체)

**사용 케이스**: 폰트, 크기, 색상, 마진 변경

**필요 단계**: math_video_pipeline.py 설정 수정 → compose-all

**Claude가 할 것**:
1. `math_video_pipeline.py`의 자막 force_style 설정 수정:
   - FontName, FontSize, PrimaryColour, MarginL, MarginR, MarginV 등
2. `python math_video_pipeline.py compose-all`

---

## 🤖 Sub-agents를 사용한 다중 씬 수정 (3개 이상)

> **사용 시점**: 3개 이상의 씬을 동시에 수정할 때
> **장점**: 메인 컨텍스트 절약, 일관성 보장, /clear 불필요

### Sub-agents 호출 방식

Claude가 Task tool을 사용하여 에이전트 호출:

```
Task tool 사용:
- subagent_type: "visual-layout" 또는 "visual-animation" 또는 "visual-review" 또는 "manim-coder"
- prompt: 수정할 씬 목록과 수정 내용 상세 설명
```

---

### 다중 씬 Manim 수정 (3개 이상)

**사용 케이스**: s3, s7, s12, s18, s25 애니메이션 일괄 수정

**Claude가 할 것**:

1. 수정 대상 씬 목록 확인
2. 각 씬의 `3_visual_prompts/s{n}_visual.json` 수정 (필요시)
3. **`manim-coder` 에이전트 호출** (Task tool 사용):
   ```
   prompt: |
     다음 씬들의 Manim 코드를 수정해주세요:
     - s3: [수정 내용 상세]
     - s7: [수정 내용 상세]
     - s12: [수정 내용 상세]
     - s18: [수정 내용 상세]
     - s25: [수정 내용 상세]

     각 씬의 visual.json과 timing.json을 참조하여 코드 수정.
   ```
4. 에이전트 완료 후 렌더링:
   ```bash
   python math_video_pipeline.py render-scene s3
   python math_video_pipeline.py render-scene s7
   python math_video_pipeline.py render-scene s12
   python math_video_pipeline.py render-scene s18
   python math_video_pipeline.py render-scene s25
   python math_video_pipeline.py compose-scene s3
   python math_video_pipeline.py compose-scene s7
   python math_video_pipeline.py compose-scene s12
   python math_video_pipeline.py compose-scene s18
   python math_video_pipeline.py compose-scene s25
   ```
5. `python math_video_pipeline.py merge-final`

---

### 다중 씬 Visual + Manim 수정 (3개 이상)

**사용 케이스**: s5, s10, s15, s20 비주얼과 코드 모두 수정

**Claude가 할 것**:

1. 수정 대상 씬 목록 확인
2. **단계별 에이전트 순차 호출**:

   **Step 1: Layout 수정** (`visual-layout` 에이전트)
   ```
   prompt: |
     다음 씬들의 Layout을 수정해주세요:
     - s5: [객체 배치 수정 내용]
     - s10: [객체 배치 수정 내용]
     - s15: [객체 배치 수정 내용]
     - s20: [객체 배치 수정 내용]
   ```

   **Step 2: Animation 수정** (`visual-animation` 에이전트)
   ```
   prompt: |
     다음 씬들의 Animation을 수정해주세요:
     - s5: [시퀀스 수정 내용]
     - s10: [시퀀스 수정 내용]
     - s15: [시퀀스 수정 내용]
     - s20: [시퀀스 수정 내용]
   ```

   **Step 3: Review** (`visual-review` 에이전트)
   ```
   prompt: |
     다음 씬들의 visual.json을 검증해주세요:
     s5, s10, s15, s20
   ```

   **Step 4: Manim 코드** (`manim-coder` 에이전트)
   ```
   prompt: |
     다음 씬들의 Manim 코드를 수정해주세요:
     s5, s10, s15, s20

     각 씬의 수정된 visual.json 참조.
   ```

3. 에이전트 완료 후 렌더링 및 합성 (위와 동일)

---

### 다중 씬 내용 전체 수정 (3개 이상)

**사용 케이스**: s8, s9, s10 대사와 시각화 모두 변경

**Claude가 할 것**:

1. `2_scenes/s{n}.json` 직접 수정 (narration_display, narration_tts)
2. TTS 재생성:
   ```bash
   python math_video_pipeline.py tts-scene s8
   python math_video_pipeline.py tts-scene s9
   python math_video_pipeline.py tts-scene s10
   ```
3. **Sub-agents로 Visual + Manim 처리** (위 "다중 씬 Visual + Manim 수정" 참조)
4. 렌더링 및 합성

---

### 다중 씬 삽입 (3개 이상 새 씬)

**사용 케이스**: s10 뒤에 s10a, s10b, s10c 삽입

**Claude가 할 것**:

1. 새 씬 JSON 생성 (`2_scenes/s10a.json`, `s10b.json`, `s10c.json`)
2. TTS 생성:
   ```bash
   python math_video_pipeline.py tts-scene s10a
   python math_video_pipeline.py tts-scene s10b
   python math_video_pipeline.py tts-scene s10c
   ```
3. **Sub-agents로 Visual + Manim 생성**:

   **Layout** → **Animation** → **Review** → **Manim** (순차 호출)

   각 에이전트 prompt에 새 씬 목록 전달: `s10a, s10b, s10c`

4. 렌더링, 자막, 합성
5. `scenes.json` 업데이트 및 `merge-final`

---

## 📊 수정 유형별 요약표

### 직접 수정 (1-2개 씬)

| # | 수정 유형 | Claude 작업 | CLI 명령어 |
|---|-----------|-------------|------------|
| 1 | TTS 재생성 | narration_tts 확인 | tts-scene → subtitle-scene → compose-scene |
| 2 | Manim 수정 | visual.json, manim.py 수정 | render-scene → compose-scene |
| 3 | 자막만 수정 | srt 직접 수정 | compose-scene |
| 4 | 내용 전체 수정 | scene.json, visual, manim 수정 | tts → render → subtitle → compose |
| 5 | 씬 삽입 | 새 파일들 생성 | tts → render → subtitle → compose → merge |
| 6 | 씬 삭제 | scenes.json 수정 | merge-final |
| 7 | 순서 변경 | scenes.json 수정 | merge-final |
| 8 | 배경 교체 | 이미지 교체 | compose-scene |
| 9 | 자막 스타일 | pipeline.py 수정 | compose-all |

### Sub-agents 사용 (3개 이상 씬)

| 수정 유형 | 사용 에이전트 | 순서 |
|-----------|--------------|------|
| Visual만 수정 | visual-layout → visual-animation → visual-review | 순차 |
| Manim만 수정 | manim-coder | 단독 |
| Visual + Manim | visual-layout → visual-animation → visual-review → manim-coder | 순차 |
| 내용 전체 | Claude(scene.json) + TTS CLI + 위 에이전트들 | 혼합 |

---

## ⚠️ 주의사항

1. **파일 백업**: 수정 전 기존 파일 백업 권장
2. **의존성 주의**: 상위 단계 수정 시 하위 단계 모두 재실행 필요
3. **씬 ID 규칙**: 삽입 시 `s16b`, `s16c` 형태로 명명 (기존 번호 유지)
4. **state.json 동기화**: 수정 후 반드시 state.json 업데이트
5. **Sub-agents 순서**: Visual 에이전트는 Layout → Animation → Review 순서 필수
6. **에이전트 prompt**: 수정 내용을 상세히 설명해야 정확한 수정 가능

---

## 🔍 수정 전 확인 명령어

```bash
# 현재 프로젝트 상태 확인
python math_video_pipeline.py status

# 특정 씬 파일 존재 확인 (Windows)
dir output\{project_id}\2_scenes\s7.json
dir output\{project_id}\3_visual_prompts\s7_visual.json
dir output\{project_id}\4_manim_code\s7_manim.py
dir output\{project_id}\0_audio\s7.mp3
dir output\{project_id}\8_renders\s7.mov
dir output\{project_id}\7_subtitles\s7.srt
dir output\{project_id}\10_scene_final\s7_final.mp4
```

---

## 💡 Sub-agents vs 직접 수정 결정 가이드

```
수정할 씬 개수?
├── 1-2개 → 직접 수정 (skills 파일 참조)
├── 3-9개 → Sub-agents 권장 (컨텍스트 절약)
└── 10개+ → Sub-agents 필수 (메인 컨텍스트 보호)

수정 복잡도?
├── 단순 (자막, 배경) → 직접 수정
├── 중간 (Manim만) → 1-2개: 직접, 3개+: Sub-agent
└── 복잡 (Visual+Manim) → Sub-agents 권장
```
