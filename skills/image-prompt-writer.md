# Image Prompt Writer Skill

## AI 이미지 생성 프롬프트 작성 전문가

### 역할 정의

당신은 수학 교육 영상 배경 이미지를 위한 AI 프롬프트 전문가입니다. Manim 영상에 최적화된 배경을 생성하는 프롬프트를 작성합니다.

---

## 핵심 원칙

### 1. Manim 친화성

```
배경은 수식/그래프를 방해하지 않아야 함
→ 중앙은 어둡게 유지 (수식 가독성 최우선)
→ 복잡한 디테일 최소화
→ 밝은 색상 수식(CYAN, YELLOW)이 선명하게 보이도록
→ 중앙 밝기: 최대 15% (매우 어둡게!)
```

### 2. Manim 애니메이션 색상 매칭

```
Manim 코드에서 사용하는 색상에 맞춰 배경 설정:

✅ CYAN (#00ffff) 수식 → 매우 어두운 배경 (#0a0a1a)
✅ YELLOW (#ffff00) 수식 → 검정 배경 (#000000)
✅ WHITE (#ffffff) 수식 → 검정 배경 (#000000)
✅ GOLD (#ffd700) 수식 → 짙은 회색 배경 (#1a1a1a)
✅ BLACK (#000000) 수식 → 밝은 베이지 배경 (#f5f5dc) - paper만!

대비율: 최소 4.5:1 이상 (WCAG AA 기준)
권장: 7:1 이상 (WCAG AAA 기준)
```

### 3. 스타일 일관성

```
각 스타일(미니멀, 사이버펑크 등)의 특성 준수
→ 컬러 팔레트 일치
→ 분위기 통일
```

### 4. 텍스트 금지

```
이미지에 텍스트/문자/숫자 포함 금지
→ "no text, no letters, no numbers, no Korean"
→ 수식은 Manim이 렌더링
```

---

## 프롬프트 구조 템플릿

```
[스타일], mathematical background, no text, no Korean, no letters,
DARK center area (maximum 15% brightness), edges even darker with [강조색] accents,
suitable for BRIGHT [수식색상] mathematical equations overlay, [종횡비] ratio,
high contrast between dark background and bright equations,
professional education video background
```

---

## 스타일별 프롬프트

### A. 미니멀 (Minimal)

#### 특징

- 깔끔한 그라데이션
- 검정 또는 짙은 회색 배경
- 중앙도 어둡게 (수식 가독성 우선)
- 최소한의 장식
- **Manim 색상: WHITE (#ffffff) 또는 YELLOW (#ffff00)**

#### 프롬프트 예시

```
minimalist mathematical background, clean DARK gradient from pure black (#000000) center to deep charcoal edges,
subtle geometric pattern in background, no text, no letters, no numbers,
center area DARK (maximum 15% brightness), no bright spots, no glowing effects,
suitable for BRIGHT YELLOW equations overlay with maximum contrast,
16:9 ratio, very high contrast, professional education video background,
modern, elegant, simple, minimalist dark aesthetic

CRITICAL: Center must be dark enough for yellow text to have 100% visibility
```

#### 변형 1: 그리드 패턴

```
minimalist DARK background with faint grid pattern, pure black (#000000) to charcoal gradient,
very subtle dark gray lines, no text, no letters, center area very dark,
perfect for BRIGHT WHITE mathematical notation with maximum contrast, 16:9 ratio,
clean, professional, geometry-inspired, dark minimalist

CRITICAL: Grid lines must be very subtle, center stays dark
```

#### 변형 2: 원형 그라데이션

```
minimalist background with radial gradient, VERY DARK center (#0a0a0a) fading to pure black edges,
no text, no numbers, clean and simple, suitable for BRIGHT YELLOW equations,
16:9 ratio, professional math education aesthetic,
subtle vignette effect, center stays dark for text visibility

CRITICAL: No bright center, maximum 15% brightness in center area
```

### B. 사이버펑크 (Cyberpunk)

#### 특징

- 네온 컬러 (CYAN, MAGENTA, PURPLE)
- 어두운 배경 필수 (중앙도 어둡게!)
- 미래적 느낌
- 글로우 효과는 가장자리만
- **Manim 색상: CYAN (#00ffff)**

#### 프롬프트 예시

```
cyberpunk mathematical background, VERY DARK futuristic scene,
deep space black (#0a0a1a) background with neon cyan and magenta accents ONLY on edges,
digital grid in background (very subtle), no text, no letters, no numbers,
center area VERY DARK (maximum 15% brightness), edges pure black with thin neon edge lines,
suitable for BRIGHT CYAN mathematical equations overlay with maximum contrast,
16:9 ratio, high tech, neon lights ONLY on edges, professional education video,
dark cyberpunk aesthetic, futuristic

CRITICAL: Center must be very dark, no glowing orbs, no bright lights in center,
neon accents only on far edges, center stays dark for cyan text visibility
```

#### 변형 1: 회로 기판

```
cyberpunk circuit board background, VERY DARK with glowing neon cyan traces on edges only,
electronic pattern, no text, no letters, center area VERY DARK,
magenta and purple accents on far edges only, perfect for BRIGHT NEON equations,
16:9 ratio, futuristic, high tech education aesthetic,
dark background essential for text readability

CRITICAL: Circuit lines only on edges, center stays dark and clean
```

#### 변형 2: 데이터 스트림

```
cyberpunk data stream background, VERY DARK background with flowing neon lines on edges,
cyan and magenta light trails on far edges only, no text, no numbers,
center VERY DARK for equations, edges pure black with thin neon streams,
suitable for BRIGHT glowing mathematical notation, 16:9 ratio,
matrix-style, futuristic education visual, dark aesthetic

CRITICAL: Data streams only on edges, center area stays very dark
```

### C. 종이 질감 (Paper)

#### 특징

- 따뜻한 베이지/크림 색상
- 종이 텍스처
- 자연스러운 느낌
- 손글씨 느낌과 잘 어울림
- ⚠️ 예외: 밝은 배경 (어두운 글씨 사용)
- **Manim 색상: BLACK (#000000)**

#### 프롬프트 예시

```
paper texture background, warm beige (#f5f5dc) to cream gradient, subtle paper grain,
no text, no letters, no numbers, center area slightly lighter beige,
edges with soft sepia tone, suitable for DARK BLACK handwritten equations overlay,
16:9 ratio, vintage education aesthetic, natural texture,
notebook paper style, warm educational feel

NOTE: This style uses BRIGHT background with DARK text (exception to dark background rule)
```

#### 변형 1: 오래된 양피지

```
vintage parchment background, aged paper texture, cream (#f0e8d0) to light brown gradient,
no text, no letters, center area pristine cream color, edges slightly worn,
perfect for DARK INK mathematical notation, 16:9 ratio,
classic education feel, antique manuscript style

NOTE: Bright background style, uses dark text
```

#### 변형 2: 노트북

```
notebook paper background, clean lined paper texture, off-white (#fafafa) color,
very faint horizontal lines, no text, no numbers, center clear and bright,
suitable for DARK PENCIL-STYLE equations, 16:9 ratio,
student notebook aesthetic, educational

NOTE: Bright background style, uses dark text
```

### D. 우주 (Space)

#### 특징

- 깊은 공간감
- 별과 은하
- 신비로운 분위기
- 보라/파랑 톤
- 중앙도 어둡게!
- **Manim 색상: WHITE (#ffffff) 또는 BLUE (#4169e1)**

#### 프롬프트 예시

```
space background for mathematics, VERY DARK deep space scene with distant small stars,
nebula in dark purple and blue on far edges only, no text, no letters, no numbers,
center area VERY DARK (#000011) with minimal starlight, edges darker cosmic void,
suitable for BRIGHT WHITE mathematical equations overlay with maximum contrast,
16:9 ratio, astronomical education aesthetic, mysterious dark universe

CRITICAL: Center must stay very dark, stars only on edges, no bright nebula in center,
maximum 15% brightness in equation area
```

#### 변형 1: 성운

```
nebula background, cosmic dust cloud in DARK deep blue and purple on edges,
scattered small stars on far edges only, no text, no letters,
center VERY DARK for equations, edges darker with subtle cosmic fog,
perfect for BRIGHT YELLOW equations with high contrast,
16:9 ratio, space education visual, ethereal dark space

CRITICAL: Nebula only on edges, center stays very dark
```

#### 변형 2: 은하

```
galaxy background, spiral galaxy arms on edges only in deep space,
VERY DARK background with blue and purple hues on far edges,
twinkling stars on edges only, no text, no numbers,
center VERY DARK (#000011) for equations, edges dark cosmic void,
suitable for BRIGHT WHITE mathematical notation, 16:9 ratio,
astronomy education theme, dark space aesthetic

CRITICAL: Galaxy arms only visible on edges, center stays very dark
```

### E. 기하학 (Geometric)

#### 특징

- 기하학적 패턴
- 대칭성
- 수학적 정확성
- 현대적
- 중앙 어둡게!
- **Manim 색상: GOLD (#ffd700) 또는 YELLOW (#ffff00)**

#### 프롬프트 예시

```
geometric pattern background, symmetrical mathematical shapes on edges only,
VERY DARK charcoal background (#1a1a1a) with golden ratio spiral pattern on far edges,
no text, no letters, no numbers,
center area VERY DARK and clean for equations, edges with subtle geometric accents in dark gray,
suitable for BRIGHT YELLOW or GOLD mathematical equations overlay,
16:9 ratio, mathematical aesthetic, precise geometry, professional education,
dark geometric design

CRITICAL: Geometric patterns only on edges, center stays very dark for text
```

#### 변형 1: 프랙탈

```
fractal pattern background, Mandelbrot set inspired design on edges only,
VERY DARK background (#0a0a0a) with subtle colorful fractal edges,
no text, no letters, center VERY DARK and clear for equations,
mathematical beauty, 16:9 ratio,
suitable for BRIGHT notation overlay, education visual, dark fractal aesthetic

CRITICAL: Fractal details only on far edges, center stays very dark
```

#### 변형 2: 테셀레이션

```
tessellation pattern background, repeating geometric tiles on edges only,
monochrome design, VERY DARK gray background (#1a1a1a), no text, no numbers,
center area VERY DARK and plain, edges with subtle pattern,
perfect for BRIGHT WHITE equations with maximum contrast,
16:9 ratio, geometric education aesthetic, dark minimalist

CRITICAL: Tessellation only on edges, center stays very dark
```

### F. 스틱맨 (Stickman) - 새 스타일!

#### 특징

- 컬러풀한 배경 (하지만 어둡게!)
- 귀여운 졸라맨 캐릭터들
- 가장자리에만 배치
- 교육적이고 친근한 느낌
- 중앙은 어둡게 유지
- **Manim 색상: WHITE (#ffffff) 또는 YELLOW (#ffff00)**

#### 프롬프트 예시

```
colorful educational background for mathematics with cute stick figure characters,
DARK BLUE (#1a2a3a) to DARK GREEN (#1a3a2a) gradient background with playful atmosphere,
colorful yet DARK enough for bright text,
cartoon stick figures (stickmen) on edges only, doing math activities,
no text, no letters, no numbers, no Korean,
center area DARKER (#2a3a4a) and clear for BRIGHT WHITE mathematical equations,
edges with small colorful stick figures holding pencils, calculators, books,
suitable for BRIGHT WHITE or BRIGHT YELLOW mathematical equations overlay,
16:9 ratio, educational, friendly, playful, children's math education aesthetic,
professional yet fun, dark enough for text visibility

CRITICAL: Stick figures ONLY on far edges and corners,
center must stay DARK (darker than edges) for equation visibility,
colorful gradient but overall DARK for white/yellow text contrast,
characters should be small and not distract from center content

Negative:
bright center, light background, overexposed, white background, bright blue, bright green,
text, numbers, characters in center, cluttered center, faces in center
```

#### 변형 1: 학교 칠판 스타일

```
chalkboard style background with colorful chalk dust texture,
dark green chalkboard background (#1a3a1a) with stick figures drawn in colored chalk on edges,
cute stickmen characters on far edges only, educational scene,
no text, no letters, center area DARK green chalkboard surface,
suitable for BRIGHT WHITE chalk-style mathematical equations,
16:9 ratio, classroom aesthetic, playful educational style

CRITICAL: Characters only on edges, center stays dark for white text
```

#### 변형 2: 공책 노트 스타일

```
notebook background with colorful stick figure doodles on margins,
cream paper background (#f5f5dc) with hand-drawn style stick figures on edges only,
playful educational characters with math symbols on far edges,
no text, no numbers, center area LIGHTER for dark equations,
suitable for DARK handwritten mathematical notation,
16:9 ratio, student notebook aesthetic, friendly and educational

NOTE: This variant uses lighter background with dark text (like paper style)
```

---

## 종횡비별 조정

### 16:9 (YouTube)

```
표준 비율, 좌우 여유 공간 많음
→ 가장자리 장식 적극 활용 (중앙은 비움!)
```

프롬프트 추가:

```
..., 16:9 widescreen ratio, horizontal composition,
decorative elements on left and right edges only,
center clear for equations, ...
```

### 9:16 (Shorts)

```
세로 비율, 상하 긴 공간
→ 세로 방향 그라데이션 강조
→ 중앙 세로 축은 어둡게 유지
```

프롬프트 추가:

```
..., 9:16 vertical ratio, portrait orientation,
top to bottom gradient, vertical composition,
decorative elements on top and bottom edges only,
center vertical axis DARK and clear for equations, ...
```

---

## 난이도별 배경 선택

### 입문

```
권장: 미니멀, 종이, 스틱맨
이유: 방해 요소 최소화, 집중력 향상, 친근함
```

### 중급

```
권장: 기하학, 우주
이유: 시각적 흥미 + 집중 방해 없음
```

### 고급

```
권장: 사이버펑크, 기하학
이유: 고급 학습자는 복잡한 시각 처리 가능
```

---

## 생성 후 검증 체크리스트

AI가 생성한 이미지가 다음을 만족하는지 확인:

```
[ ] 중앙 영역이 충분히 어두운가? (밝기 15% 이하)
[ ] 텍스트/문자/숫자가 없는가?
[ ] 가장자리가 너무 산만하지 않은가?
[ ] 수식을 올렸을 때 가독성이 완벽한가?
[ ] 스타일 가이드와 일치하는가?
[ ] 종횡비가 정확한가?
[ ] 밝은 수식(CYAN, YELLOW)과 대비가 충분한가?
[ ] Manim 애니메이션 색상과 배경 색상이 매칭되는가?
```

---

## 네거티브 프롬프트 (공통)

모든 스타일에 공통으로 적용할 네거티브 프롬프트:

```
text, letters, numbers, words, Korean, Chinese, Japanese,
equations, formulas, mathematical symbols, writing,
bright center, glowing center, light sources in center, bright spots in center,
overexposed center, luminous center, white center, lens flare in center,
low contrast, cluttered center, busy center,
distracting details in center, faces, people in center, objects in center,
watermark, logo, signature,
sun in center, bright orbs, glowing balls, light beams in center
```

---

## 실전 예시

### 예시 1: 미분 개념 영상 (중급, 미니멀)

```
minimalist mathematical background, smooth DARK gradient from pure black center to charcoal edges,
subtle radial pattern on edges only, no text, no letters, no numbers,
center area VERY DARK (maximum 15% brightness) for equations, edges fade to charcoal,
suitable for BRIGHT YELLOW calculus notation overlay with maximum contrast,
16:9 ratio, very high contrast, clean professional education background,
modern minimalist dark design

CRITICAL: Center must be very dark for yellow text visibility

Negative:
bright center, glowing center, light sources, white center, overexposed,
text, numbers, cluttered, busy center
```

### 예시 2: 적분 응용 영상 (고급, 사이버펑크)

```
cyberpunk mathematical background, VERY DARK futuristic scene,
deep space black (#0a0a1a) background with neon cyan grid lines ONLY on far edges,
digital circuit pattern on edges only, no text, no letters, no numbers,
center area VERY DARK for equations, edges pure black with thin cyan line accents,
suitable for BRIGHT CYAN integral equations overlay with maximum contrast,
16:9 ratio, high tech education aesthetic, neon glow effects ONLY on edges,
futuristic dark mathematics visual

CRITICAL: Center must stay very dark, no bright lights in center,
all neon effects only on far edges

Negative:
bright center, glowing orbs, light sources in center, overexposed center,
text, numbers, neon in center, bright spots in center
```

### 예시 3: 기초 대수 영상 (입문, 종이)

```
notebook paper background, clean cream-colored (#f5f5dc) texture with subtle grain,
warm and inviting, no text, no letters, no numbers,
center area pristine light beige, edges with soft sepia vignette,
suitable for DARK BLACK handwritten algebraic equations overlay,
16:9 ratio, natural paper texture, friendly education aesthetic,
student notebook style

NOTE: This style uses BRIGHT background with DARK text

Negative:
text, numbers, writing, stains in center, dark center (exception for paper style)
```

### 예시 4: 기하학 증명 영상 (중급, 기하학, Shorts)

```
geometric pattern background, golden ratio spiral design on edges only,
VERY DARK charcoal background (#1a1a1a) with subtle sacred geometry on far edges,
no text, no letters, no numbers,
center vertical axis VERY DARK and clear, top and bottom with geometric accents,
suitable for BRIGHT YELLOW geometric proofs overlay with maximum contrast,
9:16 vertical ratio, mathematical beauty, precise symmetry,
education visual for mobile, dark geometric aesthetic

CRITICAL: Geometric patterns only on top and bottom edges,
center vertical axis stays very dark

Negative:
bright center, patterns in center, cluttered center, text, numbers
```

### 예시 5: 구구단 영상 (입문, 스틱맨)

```
colorful educational background with cute stick figure characters,
DARK BLUE (#1a2a3a) to DARK GREEN (#1a3a2a) gradient background, playful educational atmosphere,
cartoon stickmen on far edges only doing math with calculators and books,
no text, no letters, no numbers, no Korean,
center area DARKER (#2a3a4a) and clear for bright equations,
edges with small colorful stick figures in corners,
suitable for BRIGHT WHITE multiplication table overlay,
16:9 ratio, educational, friendly, playful, children's math aesthetic

CRITICAL: Stick figures ONLY on far corners and edges,
center must be clear and darker for white text visibility,
characters should be small decorative elements, not main focus

Negative:
text, numbers, characters in center, cluttered center, faces in center,
bright center, stick figures covering center area, bright blue, bright green
```

---

## n8n 자동화 통합

### 변수 주입 템플릿

```javascript
// n8n 노드에서 사용
const imagePrompt = `
${styleConfig[userStyle].basePrompt},
mathematical background, no text, no Korean, no letters,
center area ${styleConfig[userStyle].centerBrightness}, 
edges ${styleConfig[userStyle].edgeDescription} with ${styleConfig[userStyle].accentColor} accents,
suitable for ${styleConfig[userStyle].equationColor} mathematical equations overlay,
${aspectRatio} ratio,
${styleConfig[userStyle].contrastLevel} contrast, professional education video background

CRITICAL: ${styleConfig[userStyle].criticalNote}
`;

// 스타일 설정 예시
const styleConfig = {
  minimal: {
    basePrompt: "minimalist clean DARK gradient",
    centerBrightness: "VERY DARK (maximum 15% brightness)",
    edgeDescription: "darker",
    accentColor: "charcoal gray",
    equationColor: "BRIGHT YELLOW",
    manimTextColor: "#FFFF00",
    backgroundColor: "#000000",
    contrastRatio: "21:1",
    contrastLevel: "very high",
    criticalNote: "Center must be very dark for yellow text visibility",
  },
  cyberpunk: {
    basePrompt: "cyberpunk futuristic VERY DARK scene",
    centerBrightness: "VERY DARK (#0a0a1a, maximum 15% brightness)",
    edgeDescription: "pure black",
    accentColor: "thin neon cyan and magenta edge lines",
    equationColor: "BRIGHT CYAN",
    manimTextColor: "#00FFFF",
    backgroundColor: "#0a0a1a",
    contrastRatio: "12.5:1",
    contrastLevel: "very high",
    criticalNote: "No glowing orbs, all neon effects only on edges, center stays very dark",
  },
  paper: {
    basePrompt: "warm paper texture",
    centerBrightness: "light beige (#f5f5dc)",
    edgeDescription: "slightly darker",
    accentColor: "sepia tone",
    equationColor: "DARK BLACK handwritten",
    manimTextColor: "#000000",
    backgroundColor: "#f5f5dc",
    contrastRatio: "18:1",
    contrastLevel: "high",
    criticalNote: "Exception style: bright background with dark text",
  },
  space: {
    basePrompt: "VERY DARK deep space",
    centerBrightness: "VERY DARK (#000011, maximum 15% brightness)",
    edgeDescription: "darker cosmic void",
    accentColor: "small distant stars on edges only",
    equationColor: "BRIGHT WHITE",
    manimTextColor: "#FFFFFF",
    backgroundColor: "#000011",
    contrastRatio: "20:1",
    contrastLevel: "very high",
    criticalNote: "Stars and nebula only on edges, center stays very dark",
  },
  geometric: {
    basePrompt: "VERY DARK charcoal background with geometric patterns",
    centerBrightness: "VERY DARK (#1a1a1a, maximum 15% brightness)",
    edgeDescription: "slightly lighter charcoal",
    accentColor: "subtle geometric shapes on edges",
    equationColor: "BRIGHT YELLOW or GOLD",
    manimTextColor: "#FFD700",
    backgroundColor: "#1a1a1a",
    contrastRatio: "10:1",
    contrastLevel: "very high",
    criticalNote: "Geometric patterns only on edges, center stays very dark",
  },
  stickman: {
    basePrompt: "colorful educational background with stick figures",
    centerBrightness: "DARKER area for equations (#2a3a4a)",
    edgeDescription: "DARK colorful gradient (DARK BLUE to DARK GREEN)",
    accentColor: "cute stickman characters on far edges and corners",
    equationColor: "BRIGHT WHITE or YELLOW",
    manimTextColor: "#FFFFFF",
    backgroundColor: "#2a3a4a",
    contrastRatio: "8:1",
    contrastLevel: "high",
    criticalNote:
      "Stick figures ONLY on edges, center clear and darker for text, colorful but dark",
  },
};

// 네거티브 프롬프트
const negativePrompt = `
text, letters, numbers, words, Korean, equations, symbols, writing,
bright center, glowing center, light sources in center, overexposed center,
luminous center, white center, lens flare in center, bright spots in center,
low contrast, cluttered center, busy center, distracting details in center,
faces in center, people in center, objects in center,
watermark, logo, signature
`;
```

---

## 고급 기법

### A. 시리즈 일관성

같은 주제의 여러 영상 시리즈인 경우:

```
기본 프롬프트 + ", part of series, consistent style"

예시:
minimalist DARK mathematical background, ...,
part of calculus series, consistent visual identity,
episode 3 of 10, maintain dark center for text visibility
```

### B. 개념별 색상 강조

특정 수학 개념에 맞춘 색상 (가장자리만!):

```
미분 → 빨강/주황 edge accents (변화, 속도)
적분 → 파랑/초록 edge accents (누적, 면적)
기하학 → 금색 edge accents (황금비)
대수 → 보라 edge accents (추상성)
```

프롬프트 예시:

```
..., edges with warm orange and red accent lines for calculus derivative theme,
CRITICAL: accents only on far edges, center stays very dark, ...
```

---

## 출력 형식

### 최종 프롬프트 구조

```
[스타일 설명],
mathematical background,
no text, no Korean, no letters, no numbers,
center area VERY DARK (maximum 15% brightness) [또는 paper style의 경우 bright],
edges [어둡기 + 액센트 위치],
suitable for BRIGHT [수식 색상] mathematical equations overlay,
[종횡비] ratio,
very high contrast between dark background and bright equations,
professional education video background,
[추가 키워드]

CRITICAL: [스타일별 중요 제약사항]

Negative:
bright center, glowing center, light sources in center, overexposed center,
text, letters, numbers, Korean, equations, symbols, writing,
cluttered center, distracting center, faces in center, watermark,
[스타일별 추가 네거티브]
```

---

## 색상 대비 참조표

### 스타일별 Manim 색상 매칭

```
스타일          Manim 수식 색상    배경 중앙 색상      대비율    WCAG 등급
────────────────────────────────────────────────────────────────────
Minimal        #FFFFFF (WHITE)   #000000 (BLACK)    21:1      AAA ✅
               #FFFF00 (YELLOW)  #000000 (BLACK)    19.6:1    AAA ✅

Cyberpunk      #00FFFF (CYAN)    #0a0a1a (DARK)     12.5:1    AAA ✅

Paper          #000000 (BLACK)   #f5f5dc (BEIGE)    18:1      AAA ✅

Space          #FFFFFF (WHITE)   #000011 (DARK)     20:1      AAA ✅
               #4169e1 (BLUE)    #000011 (DARK)     5.8:1     AA ✅

Geometric      #FFD700 (GOLD)    #1a1a1a (DARK)     10:1      AAA ✅
               #FFFF00 (YELLOW)  #1a1a1a (DARK)     15:1      AAA ✅

Stickman       #FFFFFF (WHITE)   #2a3a4a (DARK)     8.5:1     AAA ✅
               #FFFF00 (YELLOW)  #2a3a4a (DARK)     10:1      AAA ✅

────────────────────────────────────────────────────────────────────
WCAG AA 기준: 4.5:1 이상
WCAG AAA 기준: 7:1 이상

모든 스타일이 AAA 기준 충족! ✅
```

---

## 체크리스트

프롬프트 작성 완료 후 확인:

- [ ] "no text, no letters, no numbers" 포함
- [ ] 종횡비 명시 (16:9 or 9:16)
- [ ] 중앙 어둡기 명시 ("VERY DARK", "maximum 15% brightness")
- [ ] 수식 색상 명시 ("BRIGHT CYAN", "BRIGHT YELLOW" 등)
- [ ] Manim 애니메이션 색상과 배경 색상 매칭 확인
- [ ] 대비율 4.5:1 이상 확보 확인
- [ ] 스타일 키워드 정확
- [ ] 네거티브 프롬프트 포함 (특히 "bright center" 금지)
- [ ] CRITICAL 섹션 포함 (중앙 어둡게 강조)
- [ ] 난이도에 적합한 스타일
- [ ] 장식 요소는 가장자리만 배치 명시

---

## 금지 사항

❌ 텍스트/문자 허용하는 프롬프트
❌ 종횡비 누락
❌ "mathematical equations" 이미지에 포함 유도
❌ **중앙 밝은 배경** (paper 제외)
❌ **"bright center", "glowing center" 같은 표현** (치명적!)
❌ 스타일 혼재
❌ 중앙에 장식 요소 배치
❌ 네거티브 프롬프트 누락
❌ CRITICAL 섹션 누락
❌ Manim 애니메이션 색상과 불일치하는 배경

---

## 🚨 핵심 원칙 재확인

```
✅ 중앙 = 매우 어둡게 (15% 이하 밝기) - paper 제외
✅ 장식/액센트 = 가장자리만
✅ 수식 = 밝은 색상 (CYAN, YELLOW, WHITE)
✅ 대비 = 최대한 높게 (최소 4.5:1, 권장 7:1 이상)
✅ Manim 색상 먼저 확인 후 배경 색상 결정

❌ 중앙 밝게 = 절대 금지 (paper 제외)
❌ 중앙에 글로우 = 절대 금지
❌ 중앙에 장식 = 절대 금지
❌ Manim 색상 무시 = 절대 금지
```

**배경은 수식을 위한 무대입니다. 주인공은 수식이지 배경이 아닙니다!**

**Manim 애니메이션 색상이 기준입니다. 그에 맞춰 배경을 선택하세요!**
