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
→ 바탕 색상은 스타일별로 다름
→ 장식 요소는 모두 희미한 회색 (#AAAAAA ~ #CCCCCC)
```

### 3. 장식 요소 = 희미한 회색 (모든 스타일 공통)

```
⚠️ 핵심 원칙: 장식 요소는 절대 눈에 띄면 안됨!

모든 스타일에서 장식 요소 색상:
→ very faint gray (#AAAAAA ~ #CCCCCC)
→ barely visible, subtle, ghost-like
→ 10-20% opacity 느낌으로

장식 요소 예시:
- 격자(grid), 회로 패턴(circuit), 기하학 도형
- 별, 성운, 홀로그램, UI 요소
- 선, 점, 패턴 등 모든 장식

❌ 금지: 네온, 밝은 색, 눈에 띄는 장식
✅ 필수: faint gray, barely visible, subtle ghost pattern
```

---

## 스타일별 프롬프트

### A. 미니멀 (Minimal)

**바탕**: clean dark gradient (어두운 그라데이션)
**장식**: faint gray geometric patterns, barely visible

```
minimalist mathematical background, clean dark gradient,
soft muted [green/yellow/gray] undertones,
very faint gray geometric patterns, barely visible grid lines,
subtle ghost-like shapes at 15% opacity,
no text, no letters, no numbers, no Korean,
16:9 ratio, high contrast, professional education video background, 8K quality
```

### B. 사이버펑크 (Cyberpunk)

**바탕**: very dark scene, near-black base (거의 검은색)
**장식**: faint gray circuits, ghost-like grid, subtle gray holographic shapes

```
cyberpunk mathematical background, very dark futuristic scene,
near-black base with subtle [green/yellow/grey] tint,
faint gray digital grid barely visible, ghost-like circuit patterns in light gray,
all decorative elements in muted gray (#AAAAAA to #CCCCCC),
no neon colors, no bright accents, no glowing elements,
no text, no letters, no numbers, no Korean,
16:9 ratio, high contrast for text overlay, 8K quality
```

**바탕 틴트 옵션** (씬마다 선택):
- subtle purple tint: 차분한 분위기
- subtle blue tint: 차가운 테크 느낌
- subtle teal tint: 고급스러운 느낌

**핵심**: 바탕은 거의 검정, 장식은 희미한 회색으로만

### C. 종이 질감 (Paper)

**바탕**: warm beige to cream (따뜻한 베이지/크림색)
**장식**: faint gray cyberpunk elements + mathematical formulas

```
paper texture background, warm beige to cream gradient,
subtle paper grain texture,
faint gray digital grid barely visible, ghost-like circuit patterns in light gray,
faint gray futuristic UI elements, barely visible tech lines and connection nodes,
very faint gray mathematical formulas scattered in background like integral signs and sigma notation and partial derivatives and matrix brackets and limit expressions,
all decorative elements in muted gray #BBBBBB to #CCCCCC,
no text, no letters, no numbers, no Korean,
16:9 ratio, vintage education aesthetic, 8K quality
```

### D. 우주 (Space)

**바탕**: deep dark space (깊고 어두운 우주)
**장식**: faint gray stars, very subtle gray nebula hints

```
space background, deep dark space scene,
near-black with subtle [purple/navy] tint,
very faint gray stars barely visible, ghost-like nebula hints in muted gray,
subtle gray cosmic dust at 10% opacity,
no bright stars, no colorful nebula, no glowing elements,
no text, no letters, no numbers, no Korean,
16:9 ratio, astronomical education aesthetic, 8K quality
```

### E. 기하학 (Geometric)

**바탕**: dark gradient with subtle color tint
**장식**: faint gray geometric shapes, barely visible lines

```
geometric pattern background, dark gradient base,
subtle [blue/purple/gray] tint,
very faint gray geometric shapes, barely visible symmetrical patterns,
ghost-like mathematical lines in light gray (#BBBBBB),
all patterns at 15% opacity,
no text, no letters, no numbers, no Korean,
16:9 ratio, mathematical aesthetic, 8K quality
```

### F. 스틱맨 (Stickman)

**바탕**: soft dark gradient (부드러운 어두운 그라데이션)
**장식**: faint gray playful shapes, subtle doodle-like patterns

```
educational background, soft dark gradient,
subtle [teal/navy/purple] tint,
very faint gray playful shapes, barely visible doodle patterns,
ghost-like circles and squares in light gray,
friendly but subtle decorative elements,
no text, no letters, no numbers, no Korean,
16:9 ratio, educational, friendly, 8K quality
```

---

## 섹션별 바탕 틴트 변화 (긴 영상용)

10분 이상 영상에서 지루함 방지를 위해 섹션별로 바탕 틴트 변화 권장:

```
| 섹션           | 바탕 틴트           | 장식 색상 (고정)    |
|----------------|---------------------|---------------------|
| Hook           | subtle purple tint  | faint gray (#AAAAAA)|
| 분석           | subtle blue tint    | faint gray (#BBBBBB)|
| 핵심 수학      | subtle teal tint    | faint gray (#AAAAAA)|
| 적용           | subtle green tint   | faint gray (#CCCCCC)|
| 아웃트로       | subtle purple tint  | faint gray (#AAAAAA)|
```

**주의**: 장식 요소 색상은 항상 희미한 회색으로 고정!

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
watermark, logo, signature, blurry, low quality,
neon colors, bright accents, glowing elements, vibrant colors,
saturated colors, high contrast patterns, eye-catching decorations
```

---

## 체크리스트

- [ ] "no text, no letters, no numbers" 포함
- [ ] 종횡비 명시 (16:9 or 9:16)
- [ ] 장식 요소 = faint gray, barely visible 명시
- [ ] 네거티브에 neon, bright, glowing 포함
- [ ] 바탕색은 스타일에 맞게 유지

---

## 결과 출력 형식

프롬프트 생성 완료 후 반드시 아래 형식으로 사용자에게 요약 제공:

```
**저장 위치:** `output/{project_id}/6_image_prompts/`
- `prompts_batch.txt` - 복사용
- `prompts_batch.json` - 프로그램용

**섹션별 설정:**

| 섹션 | 씬 | 바탕 틴트 | 장식 색상 |
|------|-----|----------|----------|
| Hook | s1~s2 | subtle **purple** tint | faint gray |
| 분석 | s3~s23 | subtle **blue** tint | faint gray |
| 핵심수학 | s24~s61 | subtle **teal** tint | faint gray |
| 적용 | s62~s79 | subtle **green** tint | faint gray |
| 아웃트로 | s80~s84 | subtle **purple** tint | faint gray |
```

**필수 포함 정보:**
- 저장 위치 (폴더 경로)
- 파일 목록 (txt, json)
- 섹션별 바탕 틴트와 장식 색상 표

---

## 금지 사항

- 텍스트/문자 허용하는 프롬프트
- 종횡비 누락
- 장식 요소에 밝은 색/네온 색 사용
- 눈에 띄는 패턴이나 그래픽
- "mathematical equations" 이미지에 포함 유도
