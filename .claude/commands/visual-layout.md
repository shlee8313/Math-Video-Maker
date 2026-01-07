# Visual Layout 생성

## 작업 순서 (반드시 따를 것)

1. **skill 파일 읽기**: `skills/visual-prompter-layout.md` 파일을 Read 도구로 읽어라
2. **state.json 읽기**: 현재 프로젝트 정보 확인
3. **씬 파일 읽기**: `output/{project_id}/2_scenes/` 폴더에서 $ARGUMENTS 범위의 씬 파일들 읽기
4. **Layout JSON 생성**: skill 규칙에 따라 각 씬의 Layout JSON 생성
5. **파일 저장**: `output/{project_id}/3_visual_prompts/s{n}_layout.json`으로 저장
6. **state.json 업데이트**: visual_progress 업데이트

## 입력 인자

$ARGUMENTS = "시작씬번호 끝씬번호" (예: "1 10" → s1~s10)

## 필수 규칙

- 세이프존: x: -6.6~6.6, y: -3.5~3.5
- 하단 y < -2.5는 자막 영역 (비워둘 것)
- ImageMobject는 반드시 set_height() 사용
- 3D 씬은 fixed_in_frame 처리

## state.json 업데이트 형식

```json
{
  "current_phase": "visual_layout_in_progress",
  "visual_progress": {
    "stage": "layout",
    "completed_scenes": ["s1", "s2", ...],
    "next_scene": "s{다음번호}"
  }
}
```

## 완료 시

"✅ Layout 완료: s{시작}~s{끝}" 출력
