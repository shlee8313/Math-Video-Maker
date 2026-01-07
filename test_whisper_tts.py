"""
새 TTS + Whisper 방식 테스트 스크립트
- 씬 전체 텍스트로 TTS 생성
- Whisper로 문장별 timestamp 추출
"""

import sys
sys.path.insert(0, '.')

from math_video_pipeline import TTSGenerator, StateManager

# 테스트용 텍스트 (s1의 나레이션)
test_text = "일 퍼센트면 백 번 뽑으면 당연히 나오는 거 아니야? 틀렸습니다."

# StateManager 초기화
state = StateManager()
state.data = {
    "project_id": "TEST_WHISPER",
    "settings": {
        "voice": "ash"
    }
}

# TTSGenerator 초기화
tts = TTSGenerator(state)

print("=" * 60)
print("🧪 새 TTS + Whisper 방식 테스트")
print("=" * 60)
print(f"텍스트: {test_text}")
print()

# 새 generate() 메서드 테스트
result = tts.generate("test_s1", test_text)

if result:
    print()
    print("=" * 60)
    print("📊 결과 (timing.json)")
    print("=" * 60)

    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))

    print()
    print("=" * 60)
    print("📝 문장별 타임스탬프")
    print("=" * 60)
    for sent in result.get("sentences", []):
        print(f"  [{sent['start']:.2f}s - {sent['end']:.2f}s] {sent['text']}")

    if result.get("words"):
        print()
        print("=" * 60)
        print("🔤 단어별 타임스탬프 (처음 10개)")
        print("=" * 60)
        for word in result.get("words", [])[:10]:
            print(f"  [{word['start']:.2f}s - {word['end']:.2f}s] {word['text']}")
else:
    print("❌ TTS 생성 실패")
