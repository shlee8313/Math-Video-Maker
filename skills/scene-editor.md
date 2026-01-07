# Scene Editor - 씬 수정 가이드

> **역할**: 완성된 영상의 개별 씬을 수정/추가/삭제하는 가이드
> **사용 시점**: final 영상 생성 후 수정이 필요할 때

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

| 단계 | 실행 방식 | Claude 필요 |
|------|-----------|-------------|
| script | Claude 작성 | ✅ |
| scenes | Claude 작성 | ✅ |
| tts | `python math_video_pipeline.py tts-scene {id}` | ❌ |
| visual | Claude 작성 (visual-prompter-*.md) | ✅ |
| manim | Claude 작성 (manim-coder.md) | ✅ |
| render | `python math_video_pipeline.py render-scene {id}` | ❌ |
| subtitle | `python math_video_pipeline.py subtitle-scene {id}` | ❌ |
| compose | `python math_video_pipeline.py compose-scene {id}` | ❌ |
| merge | `python math_video_pipeline.py merge-final` | ❌ |

---

## 🔧 수정 유형별 절차

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

## 📊 수정 유형별 요약표

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

---

## ⚠️ 주의사항

1. **파일 백업**: 수정 전 기존 파일 백업 권장
2. **의존성 주의**: 상위 단계 수정 시 하위 단계 모두 재실행 필요
3. **씬 ID 규칙**: 삽입 시 `s16b`, `s16c` 형태로 명명 (기존 번호 유지)
4. **state.json 동기화**: 수정 후 반드시 state.json 업데이트

---

## 🔍 수정 전 확인 명령어

```bash
# 현재 프로젝트 상태 확인
python math_video_pipeline.py status

# 특정 씬 파일 존재 확인
ls output/{project_id}/2_scenes/s7.json
ls output/{project_id}/3_visual_prompts/s7_visual.json
ls output/{project_id}/4_manim_code/s7_manim.py
ls output/{project_id}/0_audio/s7.mp3
ls output/{project_id}/8_renders/s7.mov
ls output/{project_id}/7_subtitles/s7.srt
ls output/{project_id}/10_scene_final/s7_final.mp4
```
