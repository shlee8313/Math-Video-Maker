#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini 2.5 TTS 테스트 스크립트
==============================

사용법:
    python test_gemini_tts.py

필요한 설정:
    1. pip install google-genai
    2. GOOGLE_API_KEY 환경변수 설정 또는 .env 파일에 추가
"""

import os
import sys
import wave
from pathlib import Path
from datetime import datetime

# ============================================================================
# 라이브러리 확인
# ============================================================================

try:
    from google import genai
    from google.genai import types
    print("✅ google-genai 라이브러리 로드 성공")
except ImportError:
    print("❌ google-genai 라이브러리가 설치되지 않았습니다.")
    print("   설치: pip install google-genai")
    sys.exit(1)

# ============================================================================
# API 키 로드
# ============================================================================

def load_api_key() -> str:
    """API 키 로드 (환경변수 또는 .env 파일)"""
    
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        # .env 파일에서 로드 시도
        env_file = Path(".env")
        if env_file.exists():
            print("📄 .env 파일에서 API 키 로드 중...")
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GOOGLE_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip('"\'')
                        break
    
    if not api_key:
        print("❌ GOOGLE_API_KEY가 설정되지 않았습니다.")
        print()
        print("설정 방법:")
        print("  1. 환경변수: export GOOGLE_API_KEY=your-api-key")
        print("  2. .env 파일: GOOGLE_API_KEY=your-api-key")
        print()
        api_key = input("또는 여기에 API 키를 직접 입력하세요: ").strip()
    
    return api_key

# ============================================================================
# WAV 파일 저장
# ============================================================================

def save_wav(filename: Path, pcm_data: bytes, channels: int = 1, rate: int = 24000, sample_width: int = 2):
    """PCM 데이터를 WAV 파일로 저장"""
    with wave.open(str(filename), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm_data)

# ============================================================================
# TTS 테스트
# ============================================================================

def test_tts(client: genai.Client, text: str, voice: str, output_file: Path) -> bool:
    """Gemini 2.5 TTS 테스트"""
    
    print(f"\n🎤 TTS 생성 중...")
    print(f"   텍스트: {text}")
    print(f"   음성: {voice}")
    print(f"   출력: {output_file}")
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice,
                        )
                    ),
                ),
            )
        )
        
        # 오디오 데이터 추출
        audio_data = response.candidates[0].content.parts[0].inline_data.data
        
        # WAV 파일로 저장
        save_wav(output_file, audio_data)
        
        # 파일 크기 확인
        file_size = output_file.stat().st_size
        print(f"\n✅ TTS 생성 성공!")
        print(f"   파일 크기: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TTS 생성 실패: {e}")
        return False

# ============================================================================
# 메인
# ============================================================================

def main():
    print("=" * 60)
    print("🎤 Gemini 2.5 TTS 테스트")
    print("=" * 60)
    
    # API 키 로드
    api_key = load_api_key()
    if not api_key:
        print("❌ API 키가 없습니다. 종료합니다.")
        return
    
    print(f"✅ API 키 로드 완료 ({api_key[:8]}...)")
    
    # 클라이언트 초기화
    print("\n🔧 Gemini 클라이언트 초기화 중...")
    try:
        client = genai.Client(api_key=api_key)
        print("✅ 클라이언트 초기화 성공")
    except Exception as e:
        print(f"❌ 클라이언트 초기화 실패: {e}")
        return
    
    # 출력 폴더 생성
    output_dir = Path("tts_test_output")
    output_dir.mkdir(exist_ok=True)
    
    # 사용 가능한 음성 목록
    voices = {
        "1": ("Kore", "여성 (밝음, 생기)"),
        "2": ("Charon", "남성 (중저음, 신뢰감)"),
        "3": ("Aoede", "여성 (차분함, 지적임)"),
        "4": ("Puck", "남성 (장난기, 에너지)"),
        "5": ("Fenrir", "남성 (깊음, 권위)"),
        "6": ("Leda", "여성 (따뜻함, 친근함)"),
    }
    
    print("\n" + "=" * 60)
    print("🎭 사용 가능한 음성")
    print("=" * 60)
    for key, (name, desc) in voices.items():
        print(f"  {key}. {name} - {desc}")
    
    # 음성 선택
    print()
    voice_choice = input("음성을 선택하세요 (1-6, 기본값 2): ").strip() or "2"
    if voice_choice not in voices:
        voice_choice = "2"
    
    voice_name = voices[voice_choice][0]
    print(f"✅ 선택된 음성: {voice_name}")
    
    # 테스트 텍스트
    print("\n" + "=" * 60)
    print("📝 테스트 텍스트")
    print("=" * 60)
    
    # 기본 테스트 텍스트 (구두점으로 쉼 표현)
    default_texts = [
        "안녕하세요, 저는 제미나이 TTS입니다.",
        "수학은, 세상을 이해하는 언어입니다. 함께 배워볼까요?",
        "미분은 순간 변화율입니다... 쉽게 말하면, 자동차 속도계와 같습니다.",
    ]
    
    print("기본 테스트 텍스트:")
    for i, text in enumerate(default_texts, 1):
        print(f"  {i}. {text}")
    print(f"  {len(default_texts)+1}. 직접 입력")
    
    text_choice = input(f"\n텍스트를 선택하세요 (1-{len(default_texts)+1}, 기본값 1): ").strip() or "1"
    
    try:
        text_idx = int(text_choice) - 1
        if 0 <= text_idx < len(default_texts):
            test_text = default_texts[text_idx]
        else:
            test_text = input("텍스트를 입력하세요: ").strip()
    except:
        test_text = default_texts[0]
    
    print(f"✅ 선택된 텍스트: {test_text}")
    
    # TTS 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"test_{voice_name}_{timestamp}.wav"
    
    success = test_tts(client, test_text, voice_name, output_file)
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 테스트 완료!")
        print("=" * 60)
        print(f"📁 출력 파일: {output_file}")
        print()
        print("재생 방법:")
        print(f"  - Windows: start {output_file}")
        print(f"  - macOS: open {output_file}")
        print(f"  - Linux: aplay {output_file}")
        
        # 추가 테스트 여부
        print()
        again = input("다른 음성/텍스트로 다시 테스트하시겠습니까? (y/n): ").strip().lower()
        if again == 'y':
            main()
    else:
        print("\n❌ 테스트 실패. API 키와 네트워크 연결을 확인하세요.")

if __name__ == "__main__":
    main()