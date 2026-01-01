# Gemini 2.5 TTS 가이드

## 설정 방법

### 1. Google AI Studio에서 API 키 발급

1. https://aistudio.google.com/apikey 접속
2. "Create API Key" 클릭
3. API 키 복사

### 2. .env 파일 설정

```env
GOOGLE_API_KEY=your-api-key-here
```

### 3. 패키지 설치

```powershell
pip install google-genai
```

---

## 음성 옵션

| 음성 | 성별 | 특징 |
|------|------|------|
| **Fenrir** | 남성 | 기본값, 안정적 |
| **Charon** | 남성 | 중저음, 신뢰감 |
| **Kore** | 여성 | 밝음, 생기 |
| **Aoede** | 여성 | 차분함, 지적임 |

---

## 사용량 제한 (무료 티어)

| 항목 | 제한 |
|------|------|
| 분당 요청 (RPM) | 15회 |
| 일일 요청 (RPD) | 1,500회 |

> 파이프라인은 자동으로 4초 간격으로 요청하여 RPM 제한 준수

---

## TTS 쉼(Pause) 규칙

Gemini TTS는 구두점으로 자연스러운 쉼 생성:

| 구두점 | 효과 | 예시 |
|--------|------|------|
| `,` (쉼표) | 짧은 쉼 | "미분은, 순간 변화율입니다." |
| `.` (마침표) | 보통 쉼 | "이것이 핵심입니다." |
| `...` (줄임표) | 긴 쉼, 망설임 | "그런데..." |

---

## 문제 해결

### "GOOGLE_API_KEY가 설정되지 않았습니다"

```
❌ GOOGLE_API_KEY가 설정되지 않았습니다 (Gemini TTS용)
```

**해결**: `.env` 파일에 API 키 추가

### "Gemini TTS 일일 한도 초과"

```
🚨 Gemini TTS 일일 한도 초과!
```

**해결**:
- 다음 날 UTC 자정 (한국시간 오전 9시) 이후 재시도
- `python math_video_pipeline.py tts-all --start-from N` 으로 이어서 진행

### Rate limit 에러

자동으로 재시도됨 (10초, 20초, 40초... 대기)

---

## 비용

**완전 무료** (무료 티어 범위 내)

- 일일 1,500회 요청 가능
- 8분 영상 1개 = 약 30~50개 문장 = 여유 있음
