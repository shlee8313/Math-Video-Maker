---
name: audio-splitter
description: Whisper 타임스탬프와 씬별 narration_tts를 매칭하여 분할 지점 결정. "오디오 분할", "audio split", "TTS 분할" 작업 시 사용. 섹션별로 split_points_{section}.json 파일 출력.
tools: Read, Write, Glob

---

# Audio Splitter Agent

> **역할**: 섹션별 TTS의 Whisper 타임스탬프와 씬별 narration_tts를 매칭하여 분할 지점 결정
> **입력**: 섹션 타임스탬프 + scenes.json의 narration_tts
> **출력**: split_points_{section}.json

---

## 0. 파일 읽기 규칙 (필수 준수)

### 읽어야 할 파일

| 파일 | 경로 | 용도 |
|------|------|------|
| 섹션 타임스탬프 | `0_audio/{section}_timestamps.json` | Whisper 세그먼트 |
| 씬 목록 | `2_scenes/scenes.json` | 각 씬의 narration_tts, section 정보 |

### 출력 파일

| 파일 | 경로 |
|------|------|
| 분할 지점 | `0_audio/split_points_{section}.json` |

---

## 1. 섹션-씬 매핑

Math Video Maker의 5개 섹션:

| section (대본) | section_key (파일명) | 예상 씬 수 |
|----------------|---------------------|-----------|
| Hook | hook | 2~3개 |
| 분석 | analysis | 6~10개 |
| 핵심수학 | core | 15~25개 |
| 적용 | apply | 6~10개 |
| 아웃트로 | outro | 2~3개 |

---

## 2. 매칭 알고리즘

### 2.1 기본 원칙

1. **의미 기반 매칭**: Whisper 전사 결과와 narration_tts를 의미적으로 매칭
2. **순서 보장**: 씬 순서 = 타임스탬프 순서 (뒤섞이지 않음)
3. **words 레벨 매칭**: 세그먼트가 아닌 **words 배열**을 사용하여 정확한 경계 결정

### 2.2 매칭 전략 (Words 기반)

> ⚠️ **중요**: 세그먼트 단위가 아닌 **words 단위**로 매칭해야 정확한 분할 가능

```
Whisper words: [w0, w1, w2, w3, w4, w5, w6, w7, ...]
               |         |              |
씬:            s1        s2             s3
               w0~w2     w3~w5          w6~w7
               end=w2.end end=w5.end    end=total
```

**매칭 절차:**

1. 각 씬의 `narration_tts` **마지막 단어** 추출
2. Whisper `words` 배열에서 해당 단어 찾기
3. **씬 종료점 계산** (안전 마진 적용):
   ```
   scene_end = 마지막_단어.end - 0.02  # 50ms 앞당겨서 끊기
   ```
4. 마지막 씬은 `total_duration` 사용

**예시:**
```
narration_tts: "...교통이 빨라진다"
words에서 "빨라진다" 찾기 → end: 20.32

scene_end = 20.32 - 0.02 = 20.27  ← 50ms 앞당김
```

> ⚠️ Whisper가 단어 end를 실제보다 늦게 잡는 경향이 있어, 다음 씬 첫 음절이 미세하게 잘려 들어옴
> 50ms 앞당겨서 깔끔하게 분리

### 2.3 마지막 단어 추출 방법

```python
def get_last_word(narration_tts):
    # 줄임표(...), 구두점 제거
    text = re.sub(r'\.{2,}', '', narration_tts)  # ... 제거
    text = re.sub(r'[.,!?]', '', text)
    words = text.strip().split()
    return words[-1] if words else ""
```

### 2.4 Words 매칭 시 주의사항

| narration_tts 마지막 | Whisper words 가능 형태 | 매칭 방법 |
|---------------------|------------------------|----------|
| "빨라진다" | "빨라진다" | 정확 매칭 |
| "됩니다" | "됩니다" | 정확 매칭 |
| "삼십만원" | "30만원" | 숫자 변환 고려 |
| "브라에스" | "브라에스는" | 부분 매칭 (startswith) |

### 2.5 Whisper 인식 오류 허용

| narration_tts | Whisper 가능 오류 | 매칭 가능? |
|---------------|------------------|-----------|
| "울돌목" | "올돌목" | O |
| "러너 지수" | "러너지수" | O |
| "30만원" | "삼십만원" | O |
| "E_d" | "이디" | O |

---

## 3. 출력 형식

### split_points_{section}.json

```json
{
  "section": "core",
  "source_file": "core.mp3",
  "total_duration": 180.5,
  "splits": [
    {
      "scene_id": "s9",
      "start": 0.00,
      "end": 15.32,
      "duration": 15.32,
      "matched_segments": [0, 1, 2],
      "narration_summary": "이제 핵심 수학으로 들어가볼까요..."
    },
    {
      "scene_id": "s10",
      "start": 15.32,
      "end": 28.45,
      "duration": 13.13,
      "matched_segments": [3, 4],
      "narration_summary": "먼저 탄력성이라는 개념부터..."
    }
  ],
  "created_at": "2025-01-14T10:30:00"
}
```

### 필드 설명

| 필드 | 타입 | 설명 |
|------|------|------|
| section | string | 섹션 key (hook, analysis, core, apply, outro) |
| source_file | string | 소스 오디오 파일명 |
| total_duration | number | 섹션 전체 길이 (초) |
| splits[].scene_id | string | 씬 ID (s1, s2, ...) |
| splits[].start | number | 시작 시간 (초) |
| splits[].end | number | 종료 시간 (초) - **last_word_end - 0.02** |
| splits[].last_word | string | 씬의 마지막 단어 |
| splits[].last_word_end | number | 마지막 단어의 Whisper end 시간 (원본값) |
| splits[].matched_segments | array | 매칭된 Whisper 세그먼트 인덱스 |
| splits[].narration_summary | string | narration_tts 앞부분 (30자) |

---

## 4. 작업 흐름

```
1. 타임스탬프 파일 읽기
   → 0_audio/{section}_timestamps.json

2. scenes.json에서 해당 섹션 씬 필터링
   → section === 담당 섹션인 씬들만

3. 순서대로 매칭
   for each scene in filtered_scenes:
     - narration_tts 앞 30자 추출
     - 현재 위치 이후의 세그먼트에서 가장 유사한 것 찾기
     - start/end 기록

4. 마지막 씬 end = total_duration

5. split_points_{section}.json 저장
```

---

## 5. 예시

### 입력: hook_timestamps.json

```json
{
  "segments": [
    {"text": "여러분, 어제 30만원이었던 비행기표가", "start": 0.0, "end": 3.2},
    {"text": "오늘 35만원이 됐습니다.", "start": 3.2, "end": 5.8},
    {"text": "왜 이런 일이 벌어지는 걸까요?", "start": 5.8, "end": 8.5},
    {"text": "오늘은 그 비밀을 파헤쳐 보겠습니다.", "start": 8.5, "end": 12.0}
  ],
  "duration": 12.0
}
```

### 입력: scenes.json (Hook 섹션만)

```json
[
  {
    "scene_id": "s1",
    "section": "Hook",
    "narration_tts": "여러분, 어제 삼십만원이었던 비행기표가, 오늘 삼십오만원이 됐습니다"
  },
  {
    "scene_id": "s2",
    "section": "Hook",
    "narration_tts": "왜 이런 일이 벌어지는 걸까요, 오늘은 그 비밀을 파헤쳐 보겠습니다"
  }
]
```

### 출력: split_points_hook.json

> **핵심**: 마지막 단어 end에서 50ms 앞당김 (다음 씬 음성 침범 방지)
> - s1 마지막 단어 "됐습니다" end: 5.6
> - s1.end = 5.6 - 0.02 = **5.55**

```json
{
  "section": "hook",
  "source_file": "hook.mp3",
  "total_duration": 12.0,
  "splits": [
    {
      "scene_id": "s1",
      "start": 0.0,
      "end": 5.55,
      "duration": 5.55,
      "last_word": "됐습니다",
      "last_word_end": 5.6,
      "matched_segments": [0, 1],
      "narration_summary": "여러분, 어제 삼십만원이었던..."
    },
    {
      "scene_id": "s2",
      "start": 5.55,
      "end": 12.0,
      "duration": 6.45,
      "last_word": "보겠습니다",
      "last_word_end": 12.0,
      "matched_segments": [2, 3],
      "narration_summary": "왜 이런 일이 벌어지는 걸까..."
    }
  ]
}
```

---

## 6. 주의사항

### 6.1 씬 ID 확인

- **반드시 scenes.json의 실제 씬 ID 사용**
- scenes.json에서 section 필터링 후 scene_id 확인
- 파트 파일(scenes_part1.json 등)의 ID가 아닌 병합 후 ID 사용

### 6.2 경계 처리 (Words 기반 + 안전 마진)

```
첫 씬: start = 0.0
마지막 씬: end = total_duration (timestamps.json의 duration)
중간 씬: end = 마지막_단어.end - 0.02 (50ms 앞당김)
         start = 이전 씬의 end
```

**핵심 공식:**
```python
# 현재 씬의 마지막 단어 end
last_word_end = find_word_in_whisper(current_scene_last_word).end

# 씬 종료점 = 마지막 단어 end에서 50ms 앞당김
scene_end = last_word_end - 0.02

# 마지막 씬만 예외: total_duration 사용
if is_last_scene:
    scene_end = total_duration
```

> ⚠️ **중요**: Whisper가 단어 end를 실제보다 늦게 잡는 경향이 있어, 다음 씬 첫 음절이 미세하게 잘려 들어옴.
> 50ms 앞당겨서 깔끔하게 분리.

### 6.3 세그먼트 겹침

- 한 세그먼트가 두 씬에 걸칠 수 있음
- 이 경우 세그먼트의 중간 시점에서 분할
- 또는 narration_tts 내용과 더 일치하는 쪽에 배정

### 6.4 매칭 실패 시

1. 앞뒤 세그먼트 확장하여 재시도
2. 전체 narration_tts 비교
3. 여전히 실패 시: 균등 분할 (duration / 씬 수)

---

## 7. 체크리스트

작업 완료 전 확인:

- [ ] 모든 씬의 start < end 보장
- [ ] 연속성: 씬N.end === 씬N+1.start
- [ ] 첫 씬 start === 0.0
- [ ] 마지막 씬 end === total_duration
- [ ] scene_id가 scenes.json과 일치
- [ ] split_points_{section}.json 저장 완료
