#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OpenAI TTS 연결 테스트 및 음성 샘플 생성"""

import os
import sys
import io
from pathlib import Path
from dotenv import load_dotenv

# Windows UTF-8 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# .env 파일 로드
load_dotenv()

# OpenAI API 키 확인
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
    print("   .env 파일에 OPENAI_API_KEY=sk-... 를 추가하세요.")
    exit(1)

print("✅ API 키 확인됨")

# OpenAI 클라이언트 생성
from openai import OpenAI
client = OpenAI(api_key=api_key)

# 테스트 문장
test_text = "안녕하세요. 저는 수학 교육 영상의 나레이션을 담당합니다. 미분은 순간 변화율을 나타냅니다."

# 모든 음성 테스트
voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

print(f"\n🎤 OpenAI TTS 테스트 시작")
print(f"   테스트 문장: {test_text}")
print("=" * 60)

output_dir = Path("tts_test_samples")
output_dir.mkdir(exist_ok=True)

for voice in voices:
    print(f"\n🔊 [{voice}] 생성 중...")
    try:
        response = client.audio.speech.create(
            model="tts-1-hd",
            voice=voice,
            input=test_text,
            response_format="mp3"
        )

        output_file = output_dir / f"sample_{voice}.mp3"
        response.stream_to_file(str(output_file))
        print(f"   ✅ 저장됨: {output_file}")

    except Exception as e:
        print(f"   ❌ 실패: {e}")

print("\n" + "=" * 60)
print(f"✅ 완료! 샘플 파일 위치: {output_dir.absolute()}")
print("\n🎧 재생하려면:")
for voice in voices:
    print(f"   start tts_test_samples\\sample_{voice}.mp3")
