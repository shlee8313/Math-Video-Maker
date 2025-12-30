# 🎤 Google Cloud TTS + OpenAI Whisper 완벽 가이드

## 📋 목차
1. [설정 방법](#설정-방법)
2. [주요 개선 사항](#주요-개선-사항)
3. [SSML 지원](#ssml-지원)
4. [Whisper 프롬프트 최적화](#whisper-프롬프트-최적화)
5. [묵음 구간 처리](#묵음-구간-처리)
6. [이상한 단어 필터링](#이상한-단어-필터링)
7. [실행 예시](#실행-예시)
8. [문제 해결](#문제-해결)

---

## 🔧 설정 방법

### 1. Google Cloud TTS API 활성화

1. https://console.cloud.google.com/ 접속
2. "API 및 서비스" → "라이브러리"
3. "Cloud Text-to-Speech API" 검색 → "사용" 클릭

### 2. 서비스 계정 JSON 생성

1. "API 및 서비스" → "사용자 인증 정보"
2. "서비스 계정 만들기" 클릭
3. 역할: "Cloud Text-to-Speech 사용자" 선택
4. "키 만들기" → JSON 다운로드
5. 다운로드한 JSON 파일을 프로젝트 폴더에 저장

### 3. .env 파일 설정

프로젝트 루트에 `.env` 파일 생성:

```env
# Google Cloud TTS 인증
GOOGLE_APPLICATION_CREDENTIALS=C:\PROJECT\Math-Video-Maker\google-tts-key.json

# OpenAI API (Whisper용)
OPENAI_API_KEY=sk-proj-your-actual-key-here
```

### 4. 패키지 설치

```powershell
pip install google-cloud-texttospeech openai python-dotenv
```

---

## ✨ 주요 개선 사항

### OpenAI TTS → Google Cloud TTS 전환

| 항목 | OpenAI TTS | Google Cloud TTS |
|------|------------|------------------|
| **언어** | 영어 최적화 | 한국어 Neural2 모델 |
| **SSML** | ❌ 미지원 | ✅ 완벽 지원 |
| **음성 옵션** | alloy, nova, onyx 등 | ko-KR-Neural2-A/B/C |
| **가격** | $15/1M 글자 | 무료 100만 글자/월 |
| **품질** | 자연스러움 | 매우 자연스러움 |
| **속도 제어** | speed 파라미터 | SSML prosody |
| **휴지 제어** | ❌ 불가능 | ✅ `<break time='500ms'/>` |

### Before (OpenAI TTS)
```
❌ 한국어 발음 부자연스러움
❌ 휴지 제어 불가
❌ SSML 미지원
❌ 유료
```

### After (Google Cloud TTS)
```
✅ 한국어 Neural2 모델로 자연스러운 발음
✅ SSML로 정확한 휴지 제어
✅ <break time='500ms'/> 정상 작동
✅ 무료 100만 글자/월
✅ OpenAI Whisper로 타이밍 검증
```

---

## 🎯 SSML 지원

### 기본 SSML 구조

```python
text = "<speak>여러분<break time='500ms'/>, 어제 사먹은 초콜릿이...</speak>"
```

Google Cloud TTS는 SSML을 자동으로 인식하여 처리합니다.

### 주요 SSML 태그

#### 1. 휴지 (Break)

```xml
<break time='500ms'/>  <!-- 0.5초 침묵 -->
<break time='1s'/>     <!-- 1초 침묵 -->
<break time='2s'/>     <!-- 2초 침묵 -->
```

**사용 예시:**
```python
narration_tts = "여러분<break time='500ms'/>, 오늘은 벡터의 내적을 알아볼게요."
```

#### 2. 강조 (Emphasis)

```xml
<emphasis level='strong'>강조할 내용</emphasis>
<emphasis level='moderate'>중간 강조</emphasis>
<emphasis level='reduced'>약한 강조</emphasis>
```

**사용 예시:**
```python
narration_tts = "이것이 바로 <emphasis level='strong'>핵심</emphasis>입니다."
```

#### 3. 속도 조절 (Prosody)

```xml
<prosody rate='slow'>천천히 말하기</prosody>
<prosody rate='fast'>빠르게 말하기</prosody>
<prosody rate='80%'>원래 속도의 80%</prosody>
```

#### 4. 음높이 (Pitch)

```xml
<prosody pitch='+2st'>2음 높게</prosody>
<prosody pitch='-2st'>2음 낮게</prosody>
```

---

## 🎤 음성 옵션

### 사용 가능한 한국어 음성

| Voice Name | 성별 | 특징 | 권장 용도 |
|------------|------|------|-----------|
| **ko-KR-Neural2-C** | 남성 | 또렷하고 명확함 (기본값) | 수학 교육 영상 |
| ko-KR-Neural2-A | 여성 | 차분하고 안정적 | 침착한 설명 |
| ko-KR-Neural2-B | 여성 | 밝고 활기찬 | 흥미 유발 |
| ko-KR-Wavenet-A | 여성 | 매우 자연스러움 | 고품질 요구 시 |
| ko-KR-Wavenet-C | 남성 | 매우 자연스러움 | 고품질 요구 시 |

### 음성 변경 방법

`state.json` 파일에서:
```json
{
  "settings": {
    "voice": "ko-KR-Neural2-C"
  }
}
```

---

## 🎯 Whisper 프롬프트 최적화

### 엄격한 규칙 프롬프트

```python
prompt = """[엄격 규칙]
1. 음성에 들린 내용만 정확히 전사
2. 인사말, 감사, 추임새, 감탄사 절대 추가 금지
3. 묵음 구간은 그대로 묵음으로 유지 (시간 엄수)
4. 타임스탬프는 실제 발화 시간 정확히 반영
5. 음성 외 배경음, 잡음 무시

이것은 수학 교육 영상 나레이션입니다.
수학 용어: 미분, 적분, 벡터, 내적, 제곱근 등

예상 내용: {원본 텍스트 일부}"""
```

### 왜 중요한가?

**Whisper는 프롬프트를 "힌트"로 사용합니다:**
- 인사말 금지 명시 → 실제로 추가 안 함
- 수학 용어 제시 → 인식 정확도 향상
- 원본 텍스트 일부 제공 → 맥락 이해

---

## 🔇 묵음 구간 처리

### 자동 감지

```python
silence_gaps = [
    {
        "start": 5.2,
        "end": 7.5,
        "duration": 2.3,  # ← 2.3초 묵음!
        "after_word": "미분은",
        "before_word": "순간"
    }
]
```

### 중요성

**묵음 = 애니메이션 wait() 시간!**

```python
# 묵음이 2.3초면
self.wait(2.3)  # 정확히 이만큼 대기해야 싱크 맞음
```

### SSML break vs 자연 묵음

**SSML break:**
```python
text = "미분은<break time='2s'/> 변화율입니다."
# → 정확히 2초 묵음
```

**자연 묵음:**
```python
text = "미분은 변화율입니다."
# → TTS가 자연스럽게 휴지 추가 (보통 0.2~0.5초)
```

---

## 🚫 이상한 단어 필터링

### 필터링 대상

```python
FORBIDDEN_WORDS = {
    # 인사말
    "안녕하세요", "감사합니다", "여러분안녕하세요",

    # 추임새
    "어", "음", "그", "아", "에",

    # 마무리 멘트
    "끝", "마칩니다", "이상입니다",

    # 기타
    "자막", "구독", "좋아요", "알림"
}
```

### 필터링 로직

1. **금지 단어 체크**
   ```
   🚫 필터링: '안녕하세요' (금지 단어)
   ```

2. **너무 짧은 발화**
   ```
   🚫 필터링: '어' (너무 짧음: 0.03초)
   ```

3. **원본에 없는 단어**
   ```
   🚫 필터링: '구독' (원본에 없음)
   ```

---

## 📊 실행 예시

### 콘솔 출력

```
============================================================
🎬 씬 s1 처리 중...
============================================================

🎤 [s1] TTS 생성 중...
   텍스트: 여러분<break time='500ms'/>, 두 벡터가 얼마나...
   음성: ko-KR-Neural2-C
   ✅ Google TTS 연결 완료
   🔊 TTS 생성 중... (3~5초 소요)
   ✅ TTS 생성 완료: s1_audio.mp3

   ⏱️  Whisper 타이밍 분석 중...
   🚫 필터링: '안녕하세요' (금지 단어)
   🚫 필터링: '어' (너무 짧음: 0.03초)
   ✅ 2개 이상한 단어 제거됨

   ✅ 타임스탬프 추출 완료
   ⏱️  실제 음성 길이: 10.85초
   📝 추출된 텍스트: 여러분 두 벡터가 얼마나 같은 방향을...
   📊 단어 타임스탬프: 42개
   🔇 묵음 구간: 3개
   ✅ 전사 정확도 우수 (97.8%)
```

---

## 🎬 생성된 타이밍 JSON

```json
{
  "scene_id": "s1",
  "audio_file": "output/P20251226051305/0_audio/s1_audio.mp3",
  "actual_duration": 10.85,
  "full_text": "여러분 두 벡터가 얼마나 같은 방향을 보고 있는지 숫자 하나로 표현할 수 있다면 믿으시겠어요",
  "input_text": "여러분<break time='500ms'/>, 두 벡터가...",
  "word_count": 42,
  "words": [
    {
      "word": "여러분",
      "start": 0.0,
      "end": 0.48,
      "duration": 0.48
    },
    {
      "word": "두",
      "start": 1.02,
      "end": 1.18,
      "duration": 0.16
    }
  ],
  "created_at": "2025-12-26T05:13:05"
}
```

---

## 🔧 문제 해결

### 1. "GOOGLE_APPLICATION_CREDENTIALS not found"

```
❌ GOOGLE_APPLICATION_CREDENTIALS가 설정되지 않았거나 파일을 찾을 수 없습니다.
```

**해결:**
1. `.env` 파일 생성 확인
2. 서비스 계정 JSON 파일 경로 확인
3. 경로가 정확한지 확인 (절대 경로 사용 권장)

---

### 2. "Permission denied"

```
❌ Google TTS 클라이언트 초기화 실패: Permission denied
```

**원인:**
- 서비스 계정에 "Cloud Text-to-Speech 사용자" 역할 없음

**해결:**
1. Google Cloud Console → "IAM 및 관리"
2. 서비스 계정 찾기
3. 역할 추가: "Cloud Text-to-Speech 사용자"

---

### 3. SSML break가 작동하지 않음

```
⚠️ <break time='500ms'/>가 묵음으로 변환되지 않음
```

**원인:**
- SSML이 plain text로 처리됨

**해결:**
`math_video_pipeline.py`에서 확인:
```python
synthesis_input = texttospeech.SynthesisInput(
    ssml=f"<speak>{text}</speak>"  # ✅ ssml 파라미터 사용
)
```

---

### 4. TTS 생성이 너무 느림

**Google Cloud TTS는 OpenAI보다 훨씬 빠릅니다!**

```
Google TTS: 3~5초 (평균)
OpenAI TTS: 10~20초 (평균)
```

---

### 5. Whisper 인식 정확도 낮음

```
⚠️ 전사 정확도 낮음 (65.3%)
```

**해결:**
1. 프롬프트 강화:
   ```python
   prompt=f"""원문 그대로: {원본_텍스트_전체}"""
   ```

2. Neural2 모델 사용 확인 (Wavenet보다 정확함)

---

## 📈 성능 지표

### TTS 생성 시간 (Google Cloud)

- **짧은 텍스트 (100자)**: 2~3초
- **보통 텍스트 (300자)**: 3~5초
- **긴 텍스트 (500자)**: 5~8초

### Whisper 처리 시간

- **10초 음성**: 3~5초
- **30초 음성**: 8~12초
- **60초 음성**: 15~20초

### 총 소요 시간 (씬 1개)

```
Google TTS: 4초
Whisper: 5초
필터링: 1초
검증: 1초
----------
총: 약 11초 (OpenAI 대비 45% 빠름!)
```

---

## 💰 비용 비교

### Google Cloud TTS

```
무료: 100만 글자/월
초과: $16 per 1M 글자

예시 (8분 영상, 10개 씬):
- 총 글자 수: ~2,500 글자
- 월 15개 영상 제작 = 37,500 글자
- 비용: 무료! (100만 글자 한도의 약 4%)
```

### OpenAI TTS (비교)

```
$15 per 1M 글자

예시 (8분 영상, 10개 씬):
- 총 글자 수: ~2,500 글자
- 비용: $0.04 per 영상
- 월 15개 영상 = $0.60
```

### OpenAI Whisper

```
$0.006 per minute

예시 (8분 영상):
- 비용: $0.048 per 영상
- 월 15개 영상 = $0.72
```

### 총 비용

- **Google TTS + Whisper**: 월 $0.72 (TTS 무료)
- **OpenAI TTS + Whisper**: 월 $1.32

---

## 🎯 베스트 프랙티스

### 1. SSML 활용

```python
# ✅ 좋은 예
"여러분<break time='500ms'/>, 벡터의 내적은 두 벡터의 방향 일치도를 나타냅니다."

# ❌ 나쁜 예 (SSML 없음)
"여러분 벡터의 내적은 두 벡터의 방향 일치도를 나타냅니다"
```

### 2. 씬 길이

```python
# ✅ 적절: 150~300자, 10~20초
scene_text = "..."  # 250자

# ❌ 너무 김: 500자+, 40초+
scene_text = "..."  # 600자
```

### 3. 음성 선택

```python
# 수학 교육: ko-KR-Neural2-C (남성, 또렷함)
# 침착한 설명: ko-KR-Neural2-A (여성, 차분함)
# 흥미 유발: ko-KR-Neural2-B (여성, 밝음)
```

---

## ✅ 체크리스트

파이프라인 실행 전:
- [ ] Google Cloud TTS API 활성화
- [ ] 서비스 계정 JSON 생성 및 저장
- [ ] `.env` 파일에 GOOGLE_APPLICATION_CREDENTIALS 설정
- [ ] `.env` 파일에 OPENAI_API_KEY 설정 (Whisper용)
- [ ] `google-cloud-texttospeech`, `openai`, `python-dotenv` 설치
- [ ] 대본에 SSML 태그 추가 (`<break time='500ms'/>`)
- [ ] 씬당 150~300자 유지
- [ ] 인터넷 연결 확인

실행 후 확인:
- [ ] `0_audio/` 폴더에 mp3 파일 생성
- [ ] 타임스탬프 JSON 파일 생성
- [ ] 전사 정확도 90% 이상
- [ ] SSML break가 묵음으로 정상 변환
- [ ] 이상한 단어 필터링 확인

---

## 🚀 다음 단계

1. **TTS 음성 확인**
   ```powershell
   # 생성된 음성 파일 재생
   start output/P20251226XXXXXX/0_audio/s1_audio.mp3
   ```

2. **타이밍 검증**
   - 실제 vs 설계 시간 확인
   - SSML break 정상 작동 확인

3. **Manim 렌더링**
   - 타이밍 맞춰진 코드로 렌더링
   - 음성 + 영상 합성

---

## 💡 팁

### 한국어 발음 최적화

```python
# 숫자는 한글로
"3×4 = 12" → "삼 곱하기 사는 십이"

# 영문은 한글 발음으로
"AI" → "에이아이"
"API" → "에이피아이"

# 수식은 음성용으로 변환
"f(x)" → "에프엑스"
"dy/dx" → "디와이 디엑스"
```

### SSML 강조 활용

```python
# 중요한 개념 강조
text = "이것이 바로 <emphasis level='strong'>벡터의 내적</emphasis>입니다."

# 천천히 설명
text = "<prosody rate='90%'>미분은 순간 변화율을 나타냅니다.</prosody>"
```

---

**이제 완벽한 Google Cloud TTS + Whisper 시스템이 준비되었습니다!** 🎉

**주요 장점:**
- ✅ 한국어 최적화 (Neural2)
- ✅ SSML 완벽 지원
- ✅ 무료 100만 글자/월
- ✅ OpenAI 대비 2배 빠른 속도
- ✅ 높은 음성 품질
