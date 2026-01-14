# Math Video Maker 프로젝트

## 🚀 빠른 시작

"시작" 입력 → 영상 제작 시작

---

## 📋 워크플로우 개요

| Step | 단계 | 담당 | 주요 출력 |
|------|------|------|----------|
| 1 | 프로젝트 설정 | Claude | state.json |
| 2 | 대본 작성 | Claude → script-writer | reading_script.json |
| 3 | 씬 분할 + 나레이션 | Sub-agents (6개) | scenes.json, s#.json |
| 3.1 | 전환 텍스트 생성 | Claude | transitions.json |
| 3.5 | 에셋 체크 | Claude + Supabase | assets/ 폴더 |
| 4 | TTS 생성 | OpenAI API | 0_audio/*.mp3 |
| 4.5 | Visual Prompter | Sub-agents (30씬 배치) | s#_visual.json |
| 5 | Manim 코드 | Sub-agents (20씬 배치) | s#_manim.py |
| 5.1 | 코드 검증 | Claude | 검증된 s#_manim.py |
| 5.5 | 배경 이미지 | 외부 생성 | 9_backgrounds/ |
| 6 | 렌더링 | Manim | 8_renders/ |
| 7 | 자막 + 합성 | FFmpeg | s#_final.mp4 |
| 7.5 | 전환 클립 생성 | FFmpeg | t_after_s#.mp4, concat_list.txt |
| 8 | 최종 병합 | FFmpeg | final_video.mp4 |

---

## Step 1: 프로젝트 설정

Claude가 물어볼 것:
1. 영상 주제
2. 영상 길이 (기본: 8분)
3. 화면 비율: 16:9 / 9:16 (기본: 16:9)
4. 스타일: minimal / cyberpunk / paper / space / geometric / stickman (기본: cyberpunk)
5. 난이도: beginner / intermediate / advanced (기본: intermediate)

→ `python math_video_pipeline.py init --title "주제" --duration 초 --style 스타일`

---

## Step 2: 대본 작성

### 2a. 메인 Claude가 대본 작성
1. `skills/script-writer.md` 읽기 ← **필수**
2. 5단계 구조로 작성: Hook(10초) → 분석(30%) → 핵심수학(40%) → 적용(20%) → 아웃트로(10초)
3. 사용자 검토 → 수정 반복 → **승인**
4. `1_script/approved_script.json` 저장 (승인된 대본 원문)
5. state.json 업데이트: `current_phase: "script_saved"`

⚠️ **여기서 /clear 필수** — 사용자에게 안내 후 대기

### 2b. script-writer 에이전트 호출 (/clear 후 "계속" 입력 시)
```
"approved_script.json을 reading_script.json으로 변환하세요.
프로젝트: {project_id}"
```
→ `1_script/reading_script.json` 저장 (content + tts 변환 포함)

### 2c. state.json 업데이트
```bash
# current_phase: "script_approved" 로 변경
```

✅ **/clear 가능**

---

## Step 3: 씬 분할 + 나레이션 + 에셋 설계

> **6개 Sub-agent 순차 호출** (Scene Director → Asset Designer 쌍)
> 에이전트 참조: `skills/scene-director.md`, `skills/narration-designer.md`

| 섹션 | Scene Director | Asset Designer | 파일 |
|------|----------------|----------------|------|
| Hook + 분석 | scene-director-hook | asset-designer-hook | scenes_part1.json |
| 핵심수학 | scene-director-core | asset-designer-core | scenes_part2.json |
| 적용 + 아웃트로 | scene-director-outro | asset-designer-outro | scenes_part3.json |

에이전트 완료 후:
```bash
python math_video_pipeline.py merge-scenes
```
→ `2_scenes/scenes.json` + 개별 `s#.json` 생성

**씬 JSON 핵심 필드:**
- `narration_display`, `subtitle_display`, `narration_tts` (나레이션 3종)
- `semantic_goal`, `required_elements`, `required_assets`

✅ **/clear 가능**

---

## Step 3.1: 전환 텍스트 생성

씬 분할 완료 후, 섹션 전환 지점에 휴식 클립용 텍스트를 작성한다.

**Claude가 할 일:**
1. `scenes.json`에서 section이 바뀌는 지점 확인
2. 각 전환점에 질문형 텍스트 작성 (다음 내용에 대한 호기심 유발)
3. `2_scenes/transitions.json` 저장

**transitions.json 형식:**
```json
[
  {"after_scene": "s11", "text": "그래서, 얼마나 더 받을 수 있을까?", "duration": 2},
  {"after_scene": "s36", "text": "알았다면, 이제 뭘 해야 할까?", "duration": 2}
]
```

**텍스트 작성 규칙:**
- 질문형으로 작성 (호기심 유발)
- 1문장, 짧고 임팩트 있게
- 다음 섹션 내용을 암시하되 스포일러 금지

**전환 클립이 필요 없는 구간:**
- Hook → 분석: Hook이 짧고, 바로 본론 진입해야 몰입 유지
- 적용 → 아웃트로: 아웃트로도 짧고, 자연스럽게 마무리해야 함

✅ **/clear 가능**

---

## Step 3.5: 에셋 체크

1. `python math_video_pipeline.py asset-check`
   - Supabase에서 보유 에셋 조회 → 로컬 다운로드
   - 누락 시 `missing_assets.json` 생성

2. 누락 에셋 있으면:
   - `skills/asset-prompt-writer.md` 읽기 ← **필수**
   - 프롬프트 파일 생성 → 사용자가 AI로 이미지 생성

3. 사용자: "에셋 준비 완료" → `python math_video_pipeline.py asset-sync`

✅ **/clear 가능**

---

## Step 4: TTS 생성

**OpenAI TTS (권장):**
```bash
python math_video_pipeline.py tts-all
```

**외부 녹음:**
```bash
python math_video_pipeline.py tts-export  # 텍스트 내보내기
# 녹음 후...
python math_video_pipeline.py audio-check
python math_video_pipeline.py audio-process
```

> ⚠️ 중간에 TTS 방식 변경 시 `0_audio/` 폴더 비워야 함

✅ **/clear 가능**

---

## Step 4.5: Visual Prompter (3단계)

> **30씬 배치** 단위로 에이전트 자동 호출

| 단계 | 에이전트 | 역할 | 출력 |
|------|----------|------|------|
| 4.5a | visual-layout | 객체 배치 | s#_layout.json |
| 4.5b | visual-animation | 시퀀스 추가 | s#_visual.json |
| 4.5c | visual-review | 검증 | 수정된 s#_visual.json |

**에이전트 호출 템플릿:**
```
"s{시작}부터 s{끝}까지 [Layout/Animation/Review] 작업을 수행하세요.
프로젝트: {project_id}
씬 범위: s{시작} ~ s{끝}"
```

✅ **/clear 가능** (전체 완료 후)

---

## Step 5: Manim 코드 생성

> **20씬 배치** 단위로 `manim-coder` 에이전트 호출
> 에이전트 참조: `skills/manim-coder-reference.md`

**에이전트 호출 템플릿:**
```
"s{시작}부터 s{끝}까지 Manim 코드를 생성하세요.
프로젝트: {project_id}
입력: 3_visual_prompts/s{n}_visual.json
출력: 4_manim_code/s{n}_manim.py"
```

**출력**: `4_manim_code/s#_manim.py`

✅ **/clear 가능**

---

## Step 5.1: 코드 검증

> `skills/code-validator.md` 참조

```bash
python math_video_pipeline.py validate-all
```

**검증 항목:**
- MathTex r-string, 중괄호 짝, 한글 폰트
- Transform 타겟 존재, 3D Scene 클래스 일치
- wait() 태그, TTS 길이 vs 애니메이션 길이

✅ **/clear 가능**

---

## Step 5.5: 배경 이미지 (외부)

> `skills/image-prompt-writer.md` 참조

```bash
python math_video_pipeline.py prompts-export  # 프롬프트 내보내기
# Midjourney/DALL-E로 생성 → 9_backgrounds/에 저장
python math_video_pipeline.py images-check
```

- **파일명**: `s1_bg.png`, `s2_bg.png`, ...
- **해상도**: 1920×1080 (16:9) 또는 1080×1920 (9:16)

✅ **/clear 가능**

---

## Step 6: 렌더링

```bash
python math_video_pipeline.py render-all      # Manim 렌더링
```

---

## Step 7: 자막 + 합성

```bash
python math_video_pipeline.py subtitle-generate  # SRT 생성
python math_video_pipeline.py compose-all        # 씬별 합성 → s*_final.mp4 생성
```

---

## Step 7.5: 전환 클립 생성

> ⚠️ **반드시 compose-all 이후에 실행** (s*_final.mp4 파일이 있어야 concat_list.txt 생성됨)

```bash
python math_video_pipeline.py transition-generate
```

**동작:**
1. `2_scenes/transitions.json` 읽기
2. 각 전환점에 대해 FFmpeg로 클립 생성:
   - 배경: 스타일에 맞는 어두운 그라데이션
   - 텍스트: 페이드인 → 유지 → 페이드아웃
   - 시간: transitions.json의 duration 값 (기본 2초)
3. `10_scene_final/t_after_s{n}.mp4` 출력
4. `10_scene_final/concat_list.txt` 생성 (전체 병합 순서)

**concat_list.txt 예시:**
```
file 's1_final.mp4'
file 's2_final.mp4'
...
file 's11_final.mp4'
file 't_after_s11.mp4'
file 's12_final.mp4'
...
```

---

## Step 8: 최종 병합

```bash
python math_video_pipeline.py merge-final        # 최종 병합 (concat_list.txt 사용)
```

> ⚠️ `merge-final`은 `concat_list.txt`가 있으면 해당 순서대로 병합

---

## 🔄 /clear 가능 지점

| 지점 | 타이밍 | state.json phase | 재개 명령 |
|------|--------|------------------|-----------|
| #2a | 대본 저장 후 | script_saved | "계속" ⚠️ **필수** |
| #2b | TTS 변환 후 | script_approved | "계속" |
| #3 | 씬 분할 완료 후 | scenes_completed | "계속" |
| #3.5 | 에셋 체크 완료 후 | assets_checked | "계속" |
| #4 | TTS 생성 완료 후 | tts_completed | "계속" |
| #4.5 | Visual Prompter 완료 | visual_prompts_completed | "계속" |
| #5 | Manim 코드 완료 | manim_completed | "계속" |
| #5.1 | 코드 검증 완료 후 | manim_validated | "계속" |
| #5.5 | 이미지 준비 완료 후 | images_ready | "렌더링" |
| #6 | 렌더링 완료 후 | rendered | "자막 생성" |

### ⚠️ /clear 금지 구간

| 구간 | 이유 |
|------|------|
| 대본 작성 **중** | 승인 전이라 저장 안 됨 |
| 씬 분할 **중** | 에이전트 완료 전 |
| 에셋 체크 **중** | 확인 완료 전 |
| TTS 생성 **중** | API 호출 중단됨 |

### /clear 후 재개

```
사용자: "계속" 또는 "상태"
Claude: state.json 읽고 현재 단계 파악 → 이어서 진행
```

---

## 📁 프로젝트 구조

```
Math-Video-Maker/
├── CLAUDE.md
├── state.json
├── math_video_pipeline.py
├── .claude/agents/          # Sub-agents
├── assets/                  # 🔥 공용 에셋 (루트 레벨)
├── skills/                  # 가이드라인 문서
└── output/{project_id}/     # 프로젝트별 출력
    ├── 0_audio/
    ├── 1_script/
    ├── 2_scenes/
    ├── 3_visual_prompts/
    ├── 4_manim_code/
    ├── 7_subtitles/
    ├── 8_renders/
    ├── 9_backgrounds/
    └── final_video.mp4
```

---

## 📚 Skills 참조

| 파일 | 사용처 | 용도 |
|------|--------|------|
| `script-writer.md` | 메인 Claude + script-writer 에이전트 | 대본 작성 규칙, 5단계 구조, TTS 변환 |
| `scene-director.md` | scene-director-* 에이전트 | 씬 분할 규칙, 씬 길이(5~30초), 3D 판단 |
| `narration-designer.md` | scene-director-* 에이전트 | 자막 분할 규칙 (;; 삽입), 분할 패턴 |
| `asset-prompt-writer.md` | 메인 Claude (Step 3.5) | 누락 에셋용 AI 프롬프트 작성 |
| `manim-coder-reference.md` | manim-coder 에이전트 | 객체/애니메이션 변환 규칙, 코드 템플릿 |
| `code-validator.md` | 메인 Claude (Step 5.1) | Manim 코드 검증, 파이프라인 일관성 |
| `image-prompt-writer.md` | 메인 Claude (Step 5.5) | 배경 이미지용 프롬프트, 스타일별 색상 |
| `scene-editor.md` | 메인 Claude (Post-Production) | 씬 수정/추가/삭제 가이드 |
| `youtube-uploader.md` | 메인 Claude (Post-Production) | 유튜브 업로드 메타데이터 생성 |

---

## 🔧 CLI 명령어 (핵심)

| 명령어 | 용도 |
|--------|------|
| `init --title "제목"` | 프로젝트 생성 |
| `status` | 상태 확인 |
| `list` | 모든 프로젝트 목록 |
| `delete <id> --force` | 프로젝트 삭제 |
| `clean --folders 0_audio --force` | 폴더 내용 정리 |
| `reset --from tts_completed --force` | 단계 리셋 |
| `merge-scenes` | 씬 파트 병합 |
| `asset-check` / `asset-sync` | 에셋 관리 |
| `tts-all` | TTS 생성 |
| `validate-all` | 코드 검증 |
| `render-all` | Manim 렌더링 |
| `transition-generate` | 전환 클립 생성 + concat_list.txt |
| `compose-all` / `merge-final` | 최종 합성 |
| `verify-sync [s#]` | 대본-TTS 동기화 검증 |
| `tts-scene s#` | 개별 씬 TTS |
| `render-scene s#` | 개별 씬 렌더링 |
| `compose-scene s#` | 개별 씬 합성 |

> 전체 명령어: `python math_video_pipeline.py help`

### 🗑️ 프로젝트 관리 명령어

```bash
# 프로젝트 목록 조회
python math_video_pipeline.py list

# 프로젝트 삭제 (--force 필수)
python math_video_pipeline.py delete P20250110_143000 --force

# 현재 프로젝트 특정 폴더 정리
python math_video_pipeline.py clean --folders 0_audio 8_renders --force

# 특정 프로젝트 전체 폴더 정리
python math_video_pipeline.py clean --project P20250110_143000 --force

# 프로젝트를 특정 단계로 리셋 (해당 단계 이후 산출물 삭제)
python math_video_pipeline.py reset --from tts_completed --force
```

**reset 가능 단계:**
- `initialized`: 대본부터 전부 재시작
- `script_approved`: 씬 분할부터 재시작
- `scenes_completed`: 에셋 체크부터 재시작
- `tts_completed`: Visual Prompter부터 재시작
- `visual_prompts_completed`: Manim 코드부터 재시작
- `manim_completed`: 검증부터 재시작
- `manim_validated`: 렌더링부터 재시작
- `rendered`: 합성부터 재시작

---

## 📊 state.json 핵심

```json
{
  "project_id": "P20250615_143000",
  "current_phase": "visual_prompts_completed",
  "scenes": { "total": 56 },
  "batch_progress": { "stage": "manim", "current_batch": 1 }
}
```

**phase 순서:**
`initialized` → `script_saved` → `script_approved` → `scenes_completed` → `assets_checked` → `tts_completed` → `visual_prompts_completed` → `manim_completed` → `manim_validated` → `images_ready` → `rendered` → `completed`

---

## 🔗 3단계 파이프라인

```
Scene Director    →    Visual Prompter    →    Manim Coder
  (What)                  (How)                  (Code)
semantic_goal    →    objects/sequence    →    Python 코드
scenes.json           s#_visual.json          s#_manim.py
```

---

## 🔧 씬 수정 (Post-Production)

> `skills/scene-editor.md` 참조

### 수정 유형별 명령어

| 사용자 입력 | Claude 동작 |
|-------------|-------------|
| "s7 수정" | 수정 유형 질문 → 해당 파이프라인 실행 |
| "s7 TTS 재생성" | tts → subtitle → compose |
| "s7 Manim 수정" | visual → manim → render → compose |
| "s7 자막 수정" | srt 수정 → compose |
| "s7 내용 수정" | scene → tts → visual → manim → render → subtitle → compose |
| "s16 뒤에 새 씬 추가" | 새 씬 풀 파이프라인 |
| "s15 삭제" | scenes.json 수정 → merge |

### 씬 단위 CLI

```bash
# 수정 전 필수: 대본-TTS 동기화 검증
python math_video_pipeline.py verify-sync         # 전체 검증
python math_video_pipeline.py verify-sync s7      # 특정 씬 검증

# 개별 씬 처리
python math_video_pipeline.py tts-scene s7        # TTS 재생성
python math_video_pipeline.py render-scene s7     # Manim 렌더링
python math_video_pipeline.py subtitle-scene s7   # 자막 생성
python math_video_pipeline.py compose-scene s7    # 합성

# 최종 병합
python math_video_pipeline.py merge-final
```

---

## 🎯 기타 명령어

| 입력 | 동작 |
|------|------|
| "시작" | 새 프로젝트 |
| "상태" / "계속" | 확인 / 재개 |
| "s7 수정" | 씬 수정 (위 참조) |
| "유튜브 업로드 정보" | 제목/설명/태그/썸네일 프롬프트 생성 |

---

## 🔐 환경 설정 (.env)

```env
OPENAI_API_KEY=sk-proj-...
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

---

## 🚨 핵심 규칙

1. **Sub-agents 사용**: Visual Prompter / Manim Coder는 별도 에이전트로 실행
2. **배치 처리**: Visual=30씬, Manim=20씬 단위
3. **에셋은 루트**: `assets/` 폴더는 모든 프로젝트 공유
4. **캐릭터/물체는 PNG**: Manim으로 직접 그리지 않음
5. **state.json으로 상태 추적**: 중단 후 재개 가능
6. **Skills 필수 참조**: 각 단계에서 해당 skill 파일 먼저 읽기