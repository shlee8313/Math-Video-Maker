# Asset Prompt Writer Skill

## 역할
누락된 에셋에 대한 이미지 생성 프롬프트를 작성합니다.

---

## 에셋 포맷 분류

### SVG (AI 생성)
- **대상**: 아이콘
- **소스**: 사용자가 AI에 프롬프트 입력 → SVG 생성
- **장점**: 배경 제거 불필요, 색상 변경 가능, 벡터 확장 가능
- **스타일**: 적당한 디테일 (너무 단순 X, 너무 복잡 X)

### PNG (Gemini 생성)
- **대상**: 복잡한 물체, 캐릭터, 사실적 이미지
- **소스**: 사용자가 직접 Gemini에 프롬프트 입력
- **후처리**: 사용자가 직접 배경 제거 후 업로드

### PNG 우선 원칙
- SVG로 직접 만들어야 하는 경우 → **PNG로 대체**
- 복잡한 도형, 캐릭터 등은 PNG가 더 효율적

---

## 핵심 원칙

### 1. 배경 제거를 고려한 디자인
> **중요**: AI가 투명 배경을 생성해도 실제로는 투명하지 않은 경우가 많음
> → 포토샵/remove.bg로 배경 제거 시 **내부 색상이 없으면 내부까지 삭제됨**

**필수 규칙:**
- 모든 오브젝트/캐릭터는 **내부에 solid color 채우기** 필수
- "transparent inside", "hollow", "outline only" 금지
- 배경만 단색으로 하고, 오브젝트 자체는 완전히 색칠
- ⚠️ **흰색(#FFFFFF) 내부 금지** → 배경 제거 시 같이 삭제됨
- 흰색 대신: 크림색(#FFF8DC), 연한 베이지(#FAF0E6), 연한 회색(#E8E8E8) 사용

### 2. PNG 배경색 강제 (회색 배경 방지)
> **문제**: 크림색 등 밝은 물체를 그릴 때 AI가 대비를 위해 배경을 회색으로 바꿈
> **해결**: 배경색을 Hex 코드로 명시적으로 강제

**PNG 배경 필수 키워드:**
```
pure solid white background (#FFFFFF), flat white background
```

**Negative에 추가:**
```
gray background, grey background, off-white background
```

---

## 프롬프트 템플릿

### 캐릭터 (졸라맨 스타일)

```
Simple stick figure character (졸라맨 style),

minimalist 2D illustration,

round head with solid peach/beige skin color (#FFDAB9),

black dot eyes and {표정} expression mouth drawn ON the colored face,

arms and legs as bold, thick black stick lines,

wearing a {감정에 맞는 색상} t-shirt,

{포즈 설명},

full body visible,

pure solid white background (#FFFFFF), flat white background,

500x700 px portrait orientation,

centered composition,

no watermark
```

**Negative:**
```
realistic, 3D, complex shading, gradient background, gray background, grey background, off-white background, white face, transparent face, hollow, outline only, cyberpunk, neon, Korean text, hangul, text on background
```

#### 감정별 옷 색상
| 감정 | 색상 | Hex |
|------|------|-----|
| 기쁨/행복 | 골드 | #FFD700 |
| 자신감/이해 | 로얄블루 | #4169E1 |
| 걱정/불안 | 회색 | #808080 |
| 분노 | 크림슨 | #DC143C |
| 슬픔 | 스틸블루 | #4682B4 |
| 중립/평범 | 라임그린 | #32CD32 |
| 학자적/진지 | 네이비 | #1E3A5F |
| 놀람 | 보라 | #8A2BE2 |
| 혼란 | 주황 | #FF8C00 |

---

### 아이콘 (SVG용 - 적당한 디테일)

```
{아이콘명} icon,

clean 2D vector illustration with moderate detail,

{형태 설명 - 구체적으로},

{색상} as main color with {보조색상} accents,

subtle shadows or highlights for depth,

solid filled design with clean edges,

professional icon style,

transparent background, NO background,

300x300 px,

centered composition,

no watermark
```

**Negative:**
```
realistic, 3D render, photo, overly complex, too simple, stick figure, hollow, outline only, transparent parts, Korean text, hangul
```

#### 아이콘 디테일 가이드
| 요소 | 단순 (X) | 적당 (O) |
|------|----------|----------|
| 전구 | 동그라미+선 | 전구 형태 + 필라멘트 + 나사산 베이스 + 광선 |
| 시계 | 동그라미+바늘 | 시계 프레임 + 숫자 표시 + 시/분침 + 작은 초침 |
| 서버 | 네모 박스 | 랙 형태 + LED 표시등 + 통풍구 패턴 + 케이블 |
| 달력 | 네모+줄 | 달력 프레임 + 바인딩 링 + 날짜 그리드 + 빨간 헤더 |
| 배터리 | 네모+채움 | 배터리 형태 + 단자 + 충전 레벨 표시 + 경고 표시 |

---

### 오브젝트

```
{오브젝트명},

minimalist 2D illustration,

{형태/특징 설명},

{색상} color scheme,

solid filled design with no transparent parts,

{필요시: with 'ENGLISH LABEL' text on product},

clean product style,

pure solid white background (#FFFFFF), flat white background,

500x500 px,

centered composition,

no watermark, no brand
```

**Negative:**
```
realistic, 3D, complex shading, gradient background, gray background, grey background, off-white background, hollow, outline only, transparent inside, cyberpunk, neon, dark background, Korean text, hangul, text on background
```

---

## 필수 키워드

### 반드시 포함 (PNG)
| 키워드 | 이유 |
|--------|------|
| `pure solid white background (#FFFFFF)` | 배경색 명시적 강제 |
| `flat white background` | 조명 효과로 인한 회색 방지 |
| `solid filled design` | 내부 색상 채우기 보장 |
| `minimalist 2D illustration` | 일관된 스타일 |
| `centered composition` | 중앙 배치 |
| `no watermark` | 워터마크 방지 |

### 반드시 포함 (SVG)
| 키워드 | 이유 |
|--------|------|
| `clean 2D vector illustration` | 벡터 스타일 |
| `moderate detail` | 적당한 디테일 (너무 단순 방지) |
| `transparent background, NO background` | 투명 배경 |
| `professional icon style` | 전문적 품질 |

### 반드시 Negative에 포함 (PNG)
| 키워드 | 이유 |
|--------|------|
| `gray background, grey background, off-white background` | 회색 배경 방지 |
| `hollow` | 빈 내부 방지 |
| `outline only` | 외곽선만 있는 것 방지 |
| `transparent inside` | 투명 내부 방지 |
| `gradient background` | 그라데이션 배경 방지 |
| `realistic, 3D` | 스타일 일관성 |
| `Korean text, hangul` | 한글 텍스트 방지 |
| `text on background` | 배경에 텍스트 방지 |

### 반드시 Negative에 포함 (SVG)
| 키워드 | 이유 |
|--------|------|
| `too simple, stick figure` | 너무 단순한 아이콘 방지 |
| `overly complex` | 너무 복잡한 것 방지 |
| `hollow, outline only` | 빈 디자인 방지 |

---

## 텍스트 규칙

### 허용되는 텍스트
- **물체 내부의 영어 텍스트** → OK
  - 예: 생수병에 "WATER", 우유팩에 "MILK", 맥주캔에 "BEER"
- **물체를 설명하는 라벨** → OK
  - 예: 가격표에 "$1.99"

### 금지되는 텍스트
- **한글 (절대 금지)** → ❌
  - 예: "물", "우유", "과자" 등
- **배경에 있는 모든 텍스트** → ❌
  - 배경 제거 시 남거나 잘림
- **워터마크, 서명** → ❌

### 프롬프트 작성법
```
# 텍스트 허용 시
"milk carton with 'MILK' text on package"

# 텍스트 불필요 시 (기본)
"milk carton, no watermark"

# Negative에 항상 포함
"Korean text, hangul, text on background"
```

---

## 출력 파일 구조

Claude는 두 개의 파일을 생성합니다:

### 1. svg_ai_prompts.json (SVG AI 생성용)

```json
{
  "total": 2,
  "common_negative": "realistic, 3D render, photo, overly complex, too simple, stick figure, hollow, outline only, transparent parts, Korean text, hangul",
  "assets": [
    {
      "file_path": "icons/lightbulb.svg",
      "size": "300x300",
      "prompt": "Lightbulb icon, clean 2D vector illustration with moderate detail, classic Edison bulb shape with visible filament inside, screw base with thread lines, small light rays emanating from bulb, yellow (#FFD700) as main color with orange accents, subtle highlights for depth, solid filled design with clean edges, professional icon style, transparent background, NO background, centered composition, no watermark",
      "negative": "realistic, 3D render, photo, overly complex, too simple, stick figure, hollow, outline only, transparent parts, Korean text, hangul",
      "style_notes": "전구 아이콘, 필라멘트+나사산+광선 포함"
    },
    {
      "file_path": "icons/clock.svg",
      "size": "300x300",
      "prompt": "Analog clock icon, clean 2D vector illustration with moderate detail, circular clock face with hour markers at 12 3 6 9 positions, bold hour and minute hands pointing at 10:10, thin second hand, raised bezel frame, gray (#708090) as main color with dark gray accents, subtle shadow for depth, solid filled design with clean edges, professional icon style, transparent background, NO background, centered composition, no watermark",
      "negative": "realistic, 3D render, photo, overly complex, too simple, stick figure, hollow, outline only, transparent parts, Korean text, hangul",
      "style_notes": "시계 아이콘, 시간표시+프레임+초침 포함"
    }
  ]
}
```

### 2. png_gemini_prompts.json (PNG Gemini 생성용)

```json
{
  "total": 2,
  "common_negative": "gray background, grey background, off-white background, hollow, outline only, transparent inside, Korean text, hangul, text on background",
  "assets": [
    {
      "file_path": "characters/stickman_happy.png",
      "size": "500x700",
      "prompt": "Simple stick figure character (졸라맨 style), minimalist 2D illustration, round head with solid peach/beige skin color (#FFDAB9), black dot eyes and happy smiling expression, wearing a gold (#FFD700) t-shirt, arms raised in celebration pose, full body visible, pure solid white background (#FFFFFF), flat white background, centered composition, no watermark",
      "negative": "realistic, 3D, complex shading, gradient background, gray background, grey background, off-white background, white face, transparent face, hollow, outline only",
      "style_notes": "기쁜 졸라맨, 환호 자세, 금색 옷"
    },
    {
      "file_path": "objects/airplane.png",
      "size": "500x500",
      "prompt": "Commercial passenger airplane, minimalist 2D illustration, side view of jet aircraft, cream (#FFF8DC) fuselage body with blue (#4169E1) tail and wing accents, simple streamlined design, solid filled design, clean product style, pure solid white background (#FFFFFF), flat white background, 500x500 px, centered composition, no watermark, no airline logo",
      "negative": "realistic, 3D, complex shading, gradient background, gray background, grey background, off-white background, hollow, outline only, transparent inside, Korean text, hangul, text on background",
      "style_notes": "비행기, 크림+파란색, 순백색 배경 강제"
    }
  ]
}
```

---

## 카테고리별 크기

| 카테고리 | 크기 | 비율 |
|----------|------|------|
| characters | 500x700 px | 세로형 (5:7) |
| icons | 300x300 px | 정사각형 |
| objects | 500x500 px | 정사각형 |
| metaphors | 700x500 px | 가로형 (7:5) |

---

## 예시 프롬프트

### 예시 1: 걱정하는 졸라맨 (PNG)
```
Simple stick figure character (졸라맨 style),

minimalist 2D illustration,

round head with solid peach/beige skin color (#FFDAB9),

black dot eyes and worried anxious expression with raised tilted eyebrows and frowning mouth drawn ON the colored face,

arms and legs as bold, thick black stick lines,

wearing a gray (#808080) t-shirt,

hands near face showing anxiety,

standing pose showing distress,

full body visible,

pure solid white background (#FFFFFF), flat white background,

500x700 px portrait orientation,

centered composition,

no watermark
```

**Negative:** realistic, 3D, complex shading, gradient background, gray background, grey background, off-white background, white face, transparent face, hollow, outline only, cyberpunk, neon, Korean text, hangul, text on background

---

### 예시 2: 전구 아이콘 (SVG - 적당한 디테일)
```
Lightbulb icon,

clean 2D vector illustration with moderate detail,

classic Edison bulb shape with visible glass bulb,

internal filament coil visible,

screw base with horizontal thread lines,

3-4 small light rays emanating from sides,

yellow (#FFD700) as main color with orange (#FFA500) filament,

subtle highlight on glass for depth,

solid filled design with clean edges,

professional icon style,

transparent background, NO background,

300x300 px,

centered composition,

no watermark
```

**Negative:** realistic, 3D render, photo, overly complex, too simple, stick figure, hollow, outline only, transparent parts, Korean text, hangul

---

### 예시 3: 서버 아이콘 (SVG - 적당한 디테일)
```
Server rack icon,

clean 2D vector illustration with moderate detail,

rectangular server tower with 3 horizontal server units stacked,

each unit has small LED indicator dots on left side,

ventilation grille pattern on front panels,

subtle cable connections on side,

slate gray (#708090) as main color with blue (#4169E1) LED indicators,

green (#32CD32) for power LED,

subtle shadow for depth,

professional icon style,

transparent background, NO background,

300x300 px,

centered composition,

no watermark
```

**Negative:** realistic, 3D render, photo, overly complex, too simple, stick figure, hollow, outline only, transparent parts, Korean text, hangul

---

### 예시 4: 우유팩 (PNG - 영어 라벨 포함)
```
Milk carton,

minimalist 2D illustration,

cream (#FFF8DC) and blue solid colors,

carton shape with solid fill,

NO pure white interior - use cream or off-white for light areas,

with 'MILK' text on package,

clean product style,

pure solid white background (#FFFFFF), flat white background,

500x500 px,

centered composition,

no watermark, no brand
```

**Negative:** realistic, 3D, complex shading, gradient background, gray background, grey background, off-white background, hollow, outline only, transparent inside, cyberpunk, neon, Korean text, hangul, text on background

---

### 예시 5: 과자봉지 (PNG - 영어 라벨 포함)
```
Colorful potato chip snack bag,

minimalist 2D illustration,

front view package design,

orange and yellow solid colors,

fully colored with no transparent parts,

with 'CHIPS' text on package,

clean product style,

pure solid white background (#FFFFFF), flat white background,

500x500 px,

centered composition,

no watermark, no brand
```

**Negative:** realistic, 3D, complex shading, gradient background, gray background, grey background, off-white background, hollow, outline only, transparent inside, cyberpunk, neon, Korean text, hangul, text on background

---

## 워크플로우

1. **missing_assets.json 확인** → 누락 에셋 목록 파악
2. **포맷 분류** → SVG(아이콘) / PNG(캐릭터, 복잡한 물체)
3. **두 파일 생성**:
   - `svg_ai_prompts.json` → SVG AI 생성 프롬프트
   - `png_gemini_prompts.json` → PNG Gemini 생성 프롬프트
4. **사용자 작업**:
   - SVG: AI에 프롬프트 입력 → SVG 생성
   - PNG: Gemini에 프롬프트 입력 → 이미지 생성 → 배경 제거
5. **assets/ 폴더에 저장** → 해당 하위 폴더에 저장
6. **"에셋 준비 완료" 입력**
7. **asset-sync 실행** → Supabase에 업로드
