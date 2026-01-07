# Visual Animation 생성

## 작업 순서 (반드시 따를 것)

1. **skill 파일 읽기**: `skills/visual-prompter-animation.md` 파일을 Read 도구로 읽어라
2. **state.json 읽기**: 현재 프로젝트 정보 확인
3. **Layout 파일 읽기**: `output/{project_id}/3_visual_prompts/s{n}_layout.json` 파일들 읽기
4. **timing 파일 읽기**: `output/{project_id}/0_audio/s{n}_timing.json` 파일들 읽기
5. **Animation 추가**: Layout에 sequence(애니메이션 시퀀스) 추가
6. **파일 저장**: `output/{project_id}/3_visual_prompts/s{n}_visual.json`으로 저장
7. **state.json 업데이트**: visual_progress 업데이트

## 입력 인자

$ARGUMENTS = "시작씬번호 끝씬번호" (예: "1 10" → s1~s10)

## sequence 구조

```json
{
  "sequence": [
    {
      "step": 1,
      "time_range": [0.0, 2.5],
      "actions": [
        {"type": "FadeIn", "target": "title", "duration": 0.5}
      ],
      "purpose": "타이틀 등장"
    }
  ]
}
```

## 필수 규칙

- timing.json의 segments에 맞춰 시간 배분
- 나레이션과 애니메이션 동기화
- wait() 시간은 TTS duration에 맞춤

## state.json 업데이트 형식

```json
{
  "current_phase": "visual_animation_in_progress",
  "visual_progress": {
    "stage": "animation",
    "completed_scenes": ["s1", "s2", ...],
    "next_scene": "s{다음번호}"
  }
}
```

## 완료 시

"✅ Animation 완료: s{시작}~s{끝}" 출력
