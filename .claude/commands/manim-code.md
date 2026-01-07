# Manim 코드 생성

## 작업 순서 (반드시 따를 것)

1. **skill 파일 읽기**: `skills/manim-coder.md` 파일을 Read 도구로 읽어라
2. **state.json 읽기**: 현재 프로젝트 정보 확인 (style, difficulty 등)
3. **visual.json 파일 읽기**: `output/{project_id}/3_visual_prompts/s{n}_visual.json` 파일들 읽기
4. **timing 파일 읽기**: `output/{project_id}/0_audio/s{n}_timing.json` 파일들 읽기
5. **Manim 코드 생성**: visual.json을 Python Manim 코드로 변환
6. **파일 저장**: `output/{project_id}/4_manim_code/s{n}_manim.py`로 저장
7. **state.json 업데이트**: scenes.completed 업데이트

## 입력 인자

$ARGUMENTS = "시작씬번호 끝씬번호" (예: "1 15" → s1~s15)

## 필수 코드 규칙

```python
# 1. MathTex - r-string 필수
MathTex(r"\frac{a}{b}")  # ✅

# 2. 한글 Text - 폰트 필수
Text("안녕", font="Noto Sans KR")  # ✅

# 3. wait() - 태그 필수
self.wait(1.5)  # wait_tag_s1_1

# 4. PNG 에셋 - set_height() 필수
stickman = ImageMobject("assets/characters/stickman.png")
stickman.set_height(4)  # ✅

# 5. 3D 씬 - ThreeDScene 사용
class S5Scene(ThreeDScene):
    def construct(self):
        self.add_fixed_in_frame_mobjects(title)  # 텍스트는 fixed
```

## 스타일별 설정

- cyberpunk: 글로우 효과, CYAN/MAGENTA 색상
- minimal: 흰색 텍스트, 깔끔
- paper: 어두운 텍스트, 밝은 배경

## state.json 업데이트 형식

```json
{
  "current_phase": "manim_coding",
  "scenes": {
    "completed": ["s1", "s2", ...],
    "next_scene": "s{다음번호}"
  }
}
```

모든 코드 완료 시:
```json
{
  "current_phase": "manim_completed"
}
```

## 완료 시

"✅ Manim 코드 완료: s{시작}~s{끝}" 출력
