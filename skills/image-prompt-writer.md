# Image Prompt Writer Skill

## AI 이미지 생성 프롬프트 작성 전문가

수학 교육 영상 배경 이미지를 위한 AI 프롬프트를 작성합니다.

---

## 핵심 원칙

### 1. 텍스트 금지

```
이미지에 텍스트/문자/숫자 포함 금지
→ "no text, no letters, no numbers, no Korean"
→ 수식은 Manim이 렌더링
```

### 2. 스타일 일관성

```
각 스타일(미니멀, 사이버펑크 등)의 특성 준수
→ 컬러 팔레트 일치
→ 분위기 통일
```

### 3. Manim 색상 매칭 (충돌 방지)

```
⚠️ 핵심 원칙: 배경 색상 ≠ 수식 색상 (같은 색상 금지!)

배경은 항상:
→ 어두운 명도 (dark, deep, dim)
→ 낮은 채도 (muted, subtle, soft, desaturated)
→ 수식과 다른 색상 계열

스타일별 수식 색상:
- minimal: YELLOW, WHITE
- cyberpunk: CYAN, MAGENTA, YELLOW
- paper: BLACK, DARK_BLUE
- space: WHITE, BLUE
- geometric: YELLOW, GREEN, WHITE
- stickman: WHITE, YELLOW

❌ 금지: 배경에 수식과 같은 색상 사용
   예) cyberpunk 배경에 neon cyan → 수식 cyan과 충돌
```

---

## 스타일별 프롬프트

### A. 미니멀 (Minimal)

**수식 색상**: YELLOW, WHITE
**배경 색상**: muted gray, soft blue, subtle purple (YELLOW/WHITE 제외)

```
minimalist mathematical background, clean dark gradient,
soft muted [blue/purple/gray] undertones, low saturation,
subtle geometric pattern, no text, no letters, no numbers, no Korean,
suitable for bright yellow and white equations overlay,
16:9 ratio, high contrast, professional education video background, 8K quality
```

### B. 사이버펑크 (Cyberpunk)

**수식 색상**: CYAN, MAGENTA, YELLOW
**배경 색상**: dark muted purple, dark deep blue, dark soft orange, dark subtle teal (CYAN/MAGENTA 제외)

```
cyberpunk mathematical background, very dark futuristic scene,
dark muted [purple/blue/orange/teal] accents, low saturation glow, dim lighting,
deep shadows, dark atmosphere, near-black base,
digital grid, circuit patterns, subtle holographic effects,
no text, no letters, no numbers, no Korean,
suitable for bright cyan and magenta equations overlay,
16:9 ratio, high contrast, 8K quality
```

**색상 옵션** (씬마다 다르게 선택 가능):
- dark purple + deep blue: 차분한 사이버펑크
- dark orange + muted pink: 따뜻한 레트로
- dark teal + bronze: 고급스러운 테크

**핵심**: 배경은 어둡게 (near-black), 색상 악센트만 연하게

### C. 종이 질감 (Paper)

**수식 색상**: BLACK, DARK_BLUE
**배경 색상**: soft beige, warm cream, subtle ivory

```
paper texture background, warm beige to cream gradient,
soft muted ivory tones, subtle paper grain,
no text, no letters, no numbers, no Korean,
suitable for dark black equations overlay,
16:9 ratio, vintage education aesthetic, 8K quality
```

### D. 우주 (Space)

**수식 색상**: WHITE, BLUE
**배경 색상**: muted purple, soft navy, subtle maroon (WHITE/BLUE 제외)

```
space background, deep space scene with distant stars,
soft muted purple and maroon nebula, low saturation,
no text, no letters, no numbers, no Korean,
suitable for bright white equations overlay,
16:9 ratio, astronomical education aesthetic, 8K quality
```

### E. 기하학 (Geometric)

**수식 색상**: YELLOW, GREEN, WHITE
**배경 색상**: muted blue, soft purple, subtle gray (YELLOW/GOLD 제외)

```
geometric pattern background, symmetrical mathematical shapes,
soft muted [blue/purple/gray] tones, low saturation,
abstract geometric lines, no text, no letters, no numbers, no Korean,
suitable for bright yellow and green equations overlay,
16:9 ratio, mathematical aesthetic, 8K quality
```

### F. 스틱맨 (Stickman)

**수식 색상**: WHITE, YELLOW
**배경 색상**: muted teal, soft navy, subtle purple (WHITE/YELLOW 제외)

```
colorful educational background, playful atmosphere,
soft muted [teal/navy/purple] gradient, low saturation,
no text, no letters, no numbers, no Korean,
suitable for bright white and yellow equations overlay,
16:9 ratio, educational, friendly, 8K quality
```

---

## 섹션별 색상 변화 (긴 영상용)

10분 이상 영상에서 지루함 방지를 위해 섹션별로 배경 색상 변화 권장:

```
| 섹션           | 추천 배경 색상      | 감정/분위기      |
|----------------|---------------------|------------------|
| Hook           | purple + blue       | 긴장감, 호기심   |
| 분석           | orange + pink       | 따뜻함, 친근함   |
| 핵심 수학      | teal + gray         | 집중, 차분함     |
| 적용           | bronze + green      | 성취감, 실용     |
| 아웃트로       | purple + blue       | 마무리, 여운     |
```

**주의**: 같은 섹션 내에서는 색상 통일 권장

---

## 종횡비

### 16:9 (YouTube)
```
16:9 widescreen ratio, horizontal composition
```

### 9:16 (Shorts)
```
9:16 vertical ratio, portrait orientation
```

---

## 네거티브 프롬프트 (공통)

```
text, letters, numbers, words, Korean, Chinese, Japanese,
equations, formulas, mathematical symbols, writing,
watermark, logo, signature, blurry, low quality
```

---

## 체크리스트

- [ ] "no text, no letters, no numbers" 포함
- [ ] 종횡비 명시 (16:9 or 9:16)
- [ ] 스타일 키워드 정확
- [ ] 네거티브 프롬프트 포함

---

## 결과 출력 형식

프롬프트 생성 완료 후 반드시 아래 형식으로 사용자에게 요약 제공:

```
**저장 위치:** `output/{project_id}/6_image_prompts/`
- `prompts_batch.txt` - 복사용
- `prompts_batch.json` - 프로그램용

**섹션별 색상:**

| 섹션 | 씬 | 배경 색상 |
|------|-----|----------|
| Hook | s1~s2 | soft muted **purple + deep blue** |
| 분석 | s3~s23 | soft muted **orange + warm pink** |
| 핵심수학 | s24~s61 | soft muted **teal + gray** |
| 적용 | s62~s79 | soft muted **bronze + olive green** |
| 아웃트로 | s80~s84 | soft muted **purple + deep blue** |
```

**필수 포함 정보:**
- 저장 위치 (폴더 경로)
- 파일 목록 (txt, json)
- 섹션별 씬 범위와 배경 색상 표

---

## 금지 사항

- 텍스트/문자 허용하는 프롬프트
- 종횡비 누락
- "mathematical equations" 이미지에 포함 유도
- 스타일 혼재
