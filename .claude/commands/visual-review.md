# Visual Review (검증)

## 작업 순서 (반드시 따를 것)

1. **skill 파일 읽기**: `skills/visual-prompter-review.md` 파일을 Read 도구로 읽어라
2. **state.json 읽기**: 현재 프로젝트 정보 확인
3. **visual.json 파일 읽기**: `output/{project_id}/3_visual_prompts/s{n}_visual.json` 파일들 읽기
4. **검증 수행**: skill의 체크리스트에 따라 검증
5. **오류 수정**: 발견된 오류 자동 수정
6. **state.json 업데이트**: visual_progress 업데이트

## 입력 인자

$ARGUMENTS = "시작씬번호 끝씬번호" (예: "1 10" → s1~s10)

## 검증 체크리스트

1. **구조 검증**: 필수 필드 존재 여부 (scene_id, objects, sequence)
2. **objects 검증**:
   - id 고유성
   - 필수 필드 (type, position)
   - 세이프존 범위 내
3. **sequence 검증**:
   - 시간 연속성
   - target이 objects에 존재하는지
4. **3D 검증**:
   - scene_class가 ThreeDScene이면 camera 설정 필수
   - Text/MathTex는 fixed_in_frame: true

## 오류 발견 시

- 자동 수정 가능 → 수정 적용 후 저장
- 자동 수정 불가 → 오류 목록 출력

## state.json 업데이트 형식

모든 Review 완료 시:
```json
{
  "current_phase": "visual_prompts_completed",
  "visual_progress": {}
}
```

## 완료 시

"✅ Review 완료: s{시작}~s{끝}" 출력
