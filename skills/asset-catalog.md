# 에셋 카탈로그

Scene Director가 씬 분할 시 참고하는 에셋 목록입니다.

## 캐릭터 (characters/)

| 파일명 | 설명 | 사용 상황 |
|--------|------|----------|
| `stickman_neutral.png` | 기본 자세 | 일반 설명 |
| `stickman_thinking.png` | 생각하는 포즈 (턱 괴기) | "생각해봅시다" |
| `stickman_surprised.png` | 놀란 표정 | 반전, 충격적 사실 |
| `stickman_happy.png` | 기쁜 표정 | 문제 해결, 정답 |
| `stickman_confused.png` | 혼란스러운 표정 | 의문, 이상함 |
| `stickman_pointing.png` | 가리키는 포즈 | 강조, 설명 |
| `stickman_holding.png` | 물건 든 포즈 | 물건 소개 |
| `stickman_sad.png` | 슬픈 표정 | 손해, 실패 |

## 물체 (objects/)

| 파일명 | 설명 | 사용 상황 |
|--------|------|----------|
| `snack_bag_normal.png` | 일반 과자봉지 | 슈링크플레이션 전 |
| `snack_bag_shrunk.png` | 줄어든 과자봉지 | 슈링크플레이션 후 |
| `money.png` | 돈/지폐 | 가격, 비용 |
| `cart.png` | 쇼핑카트 | 마트 장면 |
| `receipt.png` | 영수증 | 계산, 결제 |
| `scale.png` | 저울 | 무게 비교 |
| `calculator.png` | 계산기 | 계산 장면 |

## 아이콘 (icons/)

| 파일명 | 설명 | 사용 상황 |
|--------|------|----------|
| `question_mark.png` | 물음표 | 의문 제기 |
| `exclamation.png` | 느낌표 | 강조, 놀람 |
| `lightbulb.png` | 전구 | 아이디어, 깨달음 |
| `arrow_right.png` | 오른쪽 화살표 | 진행, 변화 |
| `checkmark.png` | 체크마크 | 완료, 정답 |

## 은유/비유 (metaphors/)

| 파일명 | 설명 | 사용 상황 |
|--------|------|----------|
| `golden_chain.png` | 금사슬에 묶인 캐릭터 (보라색 옷, 금화 위) | 돈에 얽매임, 경제적 구속, 황금 사슬 비유 |

## 에셋 파일 사양

| 항목 | 권장 값 |
|------|---------|
| 해상도 | 500x500px 이상 (1000x1000 권장) |
| 포맷 | PNG (투명 배경 필수) |
| 색상 | 밝은 색 (어두운 배경에서 잘 보이게) |
| 스타일 | 단순한 선화/일러스트 |
| 파일 크기 | 1MB 이하 권장 |

## 파일명 규칙

```
{이름}_{상태}.png

예시:
- stickman_neutral.png (기본)
- stickman_happy.png (기쁨)
- snack_bag_normal.png (일반)
- snack_bag_shrunk.png (줄어든)
```

---

## 새 에셋 요청 워크플로우

카탈로그에 없는 에셋이 필요한 경우:

### 1. Claude가 사용자에게 요청
```
필요한 에셋: {파일명}
설명: {상세 설명}
사용 씬: {씬 ID}
저장 위치: assets/{카테고리}/
권장 사양: 500x500px+, PNG 투명배경
```

### 2. 사용자가 에셋 업로드
- 직접 제작 또는 AI 이미지 생성 (Midjourney, DALL-E 등)
- `assets/{카테고리}/` 폴더에 저장

### 3. Claude가 카탈로그에 등록
- 이 파일(`skills/asset-catalog.md`)에 새 에셋 추가
- 해당 카테고리 테이블에 행 추가

> 한 번 등록된 에셋은 모든 프로젝트에서 재사용 가능!
