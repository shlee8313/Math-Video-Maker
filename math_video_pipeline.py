
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
수학 교육 영상 제작 파이프라인 v6.1
=====================================

Claude Code 통합 버전
- 창의적 작업(대본, 씬, Manim 코드): Claude Code가 skills/*.md 참조하여 생성
- API 작업(TTS, Whisper): 이 Python 스크립트가 담당
- 파일 관리: state.json으로 진행 상태 추적

사용법:
    python math_video_pipeline.py --help
    python math_video_pipeline.py init --title "피타고라스 정리" --duration 480
    python math_video_pipeline.py tts --scene s1 --text "나레이션 텍스트"
    python math_video_pipeline.py tts-all
    python math_video_pipeline.py status
    python math_video_pipeline.py render --scene s1
    python math_video_pipeline.py render-all
"""

import argparse
import json
import os
import sys
import io
import subprocess
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# UTF-8 인코딩 강제 설정 (Windows 콘솔 호환)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ============================================================================
# OpenAI 클라이언트 초기화 (TTS + Whisper)
# ============================================================================

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  OpenAI 라이브러리가 설치되지 않았습니다 (TTS/Whisper용).")
    print("   설치: pip install openai")

try:
    from google.cloud import texttospeech
    GOOGLE_TTS_AVAILABLE = True
except ImportError:
    GOOGLE_TTS_AVAILABLE = False
    print("⚠️  Google Cloud TTS 라이브러리가 설치되지 않았습니다.")
    print("   설치: pip install google-cloud-texttospeech")

# Gemini TTS (google-genai)
try:
    from google import genai
    from google.genai import types
    GEMINI_TTS_AVAILABLE = True
except ImportError:
    GEMINI_TTS_AVAILABLE = False
    print("⚠️  Gemini TTS 라이브러리가 설치되지 않았습니다.")
    print("   설치: pip install google-genai")

import wave

# Supabase (에셋 관리)
try:
    from supabase import create_client, Client as SupabaseClient
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("⚠️  Supabase 라이브러리가 설치되지 않았습니다.")
    print("   설치: pip install supabase")

# PIL (이미지 메타데이터)
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# ============================================================================
# 커스텀 예외 클래스
# ============================================================================

class QuotaExceededException(Exception):
    """API 일일 한도 초과 예외"""
    pass


def get_openai_client() -> Optional['OpenAI']:
    """OpenAI 클라이언트 생성"""
    if not OPENAI_AVAILABLE:
        return None
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # .env 파일에서 로드 시도
        env_file = Path(".env")
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith("OPENAI_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip('"\'')
                        break
    
    if not api_key:
        print("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
        print("   .env 파일에 OPENAI_API_KEY=sk-... 를 추가하세요.")
        return None
    
    return OpenAI(api_key=api_key)


def get_google_tts_client() -> Optional['texttospeech.TextToSpeechClient']:
    """Google Cloud TTS 클라이언트 생성"""
    if not GOOGLE_TTS_AVAILABLE:
        return None

    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not credentials_path:
        # .env 파일에서 로드 시도
        env_file = Path(".env")
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith("GOOGLE_APPLICATION_CREDENTIALS="):
                        credentials_path = line.split("=", 1)[1].strip().strip('"\'')
                        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
                        break

    if not credentials_path or not Path(credentials_path).exists():
        print("❌ GOOGLE_APPLICATION_CREDENTIALS가 설정되지 않았거나 파일을 찾을 수 없습니다.")
        print("   .env 파일에 GOOGLE_APPLICATION_CREDENTIALS=경로 를 추가하세요.")
        return None

    try:
        return texttospeech.TextToSpeechClient()
    except Exception as e:
        print(f"❌ Google TTS 클라이언트 초기화 실패: {e}")
        return None


def get_gemini_client() -> Optional['genai.Client']:
    """Gemini 클라이언트 생성 (TTS용)"""
    if not GEMINI_TTS_AVAILABLE:
        return None

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        # .env 파일에서 로드 시도
        env_file = Path(".env")
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GOOGLE_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip('"\'')
                        break

    if not api_key:
        print("❌ GOOGLE_API_KEY가 설정되지 않았습니다 (Gemini TTS용).")
        print("   .env 파일에 GOOGLE_API_KEY=... 를 추가하세요.")
        return None

    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        print(f"❌ Gemini 클라이언트 초기화 실패: {e}")
        return None


# ============================================================================
# 설정 및 상수
# ============================================================================

# 프로젝트 루트 (이 스크립트가 있는 디렉토리)
PROJECT_ROOT = Path(__file__).parent.resolve()

# 주요 경로
STATE_FILE = PROJECT_ROOT / "state.json"
OUTPUT_DIR = PROJECT_ROOT / "output"
SKILLS_DIR = PROJECT_ROOT / "skills"

# TTS 설정 (OpenAI gpt-4o-mini-tts)
TTS_CONFIG = {
    "voices": {
        "ash": "차분한 남성 (기본값)",
        "alloy": "중성적, 균형잡힌",
        "ballad": "부드러운 낭독",
        "coral": "따뜻한 여성",
        "echo": "남성적, 차분함",
        "fable": "영국식 억양",
        "onyx": "남성적, 깊은 목소리",
        "nova": "여성적, 밝고 친근",
        "sage": "지적인 톤",
        "shimmer": "여성적, 부드러움",
        "verse": "표현력 풍부",
        "marin": "고품질",
        "cedar": "고품질"
    },
    "default_voice": "alloy",
    "model": "gpt-4o-mini-tts",
    "audio_encoding": "MP3"
}

# 스타일 설정
STYLE_CONFIG = {
    "minimal": {
        "glow": False,
        "primary_color": "WHITE",
        "background_color": "BLACK",
        "flash_frequency": "low"
    },
    "cyberpunk": {
        "glow": True,
        "primary_color": "CYAN",
        "background_color": "#0a0a0a",
        "flash_frequency": "high"
    },
    "paper": {
        "glow": False,
        "primary_color": "BLACK",
        "background_color": "#f5f5dc",
        "flash_frequency": "medium"
    },
    "space": {
        "glow": True,
        "primary_color": "BLUE",
        "background_color": "#000011",
        "flash_frequency": "medium"
    },
    "geometric": {
        "glow": False,
        "primary_color": "GOLD",
        "background_color": "#1a1a1a",
        "flash_frequency": "medium"
    },
    "stickman": {
        "glow": False,
        "primary_color": "WHITE",
        "background_color": "#1a1a2e",
        "flash_frequency": "medium"
    }
}

# 컬러 팔레트
COLOR_PALETTE = {
    "variable": "YELLOW",
    "constant": "ORANGE",
    "result": "GREEN",
    "emphasis": "RED",
    "auxiliary": "GRAY_B"
}


# ============================================================================
# 상태 관리 클래스
# ============================================================================

class StateManager:
    """프로젝트 상태 관리"""
    
    def __init__(self, state_file: Path = STATE_FILE):
        self.state_file = state_file
        self._state = None
    
    def load(self) -> Dict[str, Any]:
        """state.json 로드"""
        if self._state is not None:
            return self._state

        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    self._state = json.load(f)
            except json.JSONDecodeError:
                print(f"⚠️  {self.state_file} 파싱 오류. 초기화합니다.")
                self._state = self._default_state()
        else:
            self._state = self._default_state()

        return self._state

    def reload(self) -> Dict[str, Any]:
        """state.json 강제 재로드 (캐시 무시)"""
        self._state = None
        return self.load()
    
    def save(self) -> None:
        """state.json 저장"""
        if self._state is None:
            self._state = self._default_state()
        
        self._state["last_updated"] = datetime.now().isoformat()
        
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self._state, f, ensure_ascii=False, indent=2)
    
    def _default_state(self) -> Dict[str, Any]:
        """기본 상태"""
        return {
            "project_id": None,
            "title": None,
            "current_phase": "idle",
            "settings": {
                "style": "cyberpunk",
                "difficulty": "intermediate",
                "duration": 480,
                "aspect_ratio": "16:9",
                "voice": "ko-KR-Neural2-C",
                "subtitle_style": "karaoke"
            },
            "scenes": {
                "total": 0,
                "completed": [],
                "pending": [],
                "current": None
            },
            "files": {
                "script": None,
                "tts_script": None,
                "scenes": None,
                "audio": [],
                "manim": [],
                "subtitles": []
            },
            "last_updated": None
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """상태 값 조회"""
        state = self.load()
        keys = key.split(".")
        value = state
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any) -> None:
        """상태 값 설정"""
        state = self.load()
        keys = key.split(".")
        target = state
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value
        self._state = state
    
    def update_phase(self, phase: str) -> None:
        """현재 단계 업데이트"""
        self.set("current_phase", phase)
        self.save()
        print(f"✅ state.json 업데이트됨: current_phase = {phase}")
    
    def add_completed_scene(self, scene_id: str) -> None:
        """완료된 씬 추가"""
        state = self.load()
        
        if scene_id in state["scenes"]["pending"]:
            state["scenes"]["pending"].remove(scene_id)
        
        if scene_id not in state["scenes"]["completed"]:
            state["scenes"]["completed"].append(scene_id)
        
        # 현재 씬 업데이트
        if state["scenes"]["pending"]:
            state["scenes"]["current"] = state["scenes"]["pending"][0]
        else:
            state["scenes"]["current"] = None
        
        self._state = state
        self.save()
    
    def reset(self) -> None:
        """상태를 기본값으로 초기화"""
        self._state = self._default_state()
        self.save()
        print("✅ state.json 초기화됨")

    def add_file(self, category: str, filepath: str) -> None:
        """파일 경로 추가"""
        state = self.load()
        
        if category not in state["files"]:
            state["files"][category] = []
        
        if isinstance(state["files"][category], list):
            if filepath not in state["files"][category]:
                state["files"][category].append(filepath)
        else:
            state["files"][category] = filepath
        
        self._state = state
        self.save()
    
    # ========================================================================
    # /clear 후 재개를 위한 상세 업데이트 함수들
    # ========================================================================
    
    def update_script_approved(self, project_id: str) -> None:
        """Step 2 완료: 대본 승인 후"""
        state = self.load()
        
        state['current_phase'] = 'script_approved'
        
        # files 초기화
        if 'files' not in state:
            state['files'] = {
                'script': None, 
                'tts_script': None, 
                'scenes': None, 
                'audio': [], 
                'manim': [],
                'subtitles': []
            }
        
        state['files']['script'] = f"output/{project_id}/1_script/reading_script.json"
        state['files']['tts_script'] = f"output/{project_id}/1_script/tts_script.json"
        
        self._state = state
        self.save()
        
        print(f"✅ state.json 업데이트: script_approved")
        print(f"   📝 대본 경로: {state['files']['script']}")
    
    def update_scenes_approved(self, project_id: str, scene_ids: List[str]) -> None:
        """Step 3 완료: 씬 분할 승인 후"""
        state = self.load()
        
        state['current_phase'] = 'scenes_approved'
        
        # files 업데이트
        if 'files' not in state:
            state['files'] = {
                'script': None, 
                'tts_script': None, 
                'scenes': None, 
                'audio': [], 
                'manim': [],
                'subtitles': []
            }
        
        state['files']['scenes'] = f"output/{project_id}/2_scenes/scenes.json"
        
        # scenes 정보 업데이트
        state['scenes'] = {
            'total': len(scene_ids),
            'completed': [],
            'pending': scene_ids,
            'current': scene_ids[0] if scene_ids else None
        }
        
        self._state = state
        self.save()
        
        print(f"✅ state.json 업데이트: scenes_approved")
        print(f"   🎬 씬 분할: {len(scene_ids)}개 씬")
    
    def update_tts_completed(self, project_id: str, audio_files: List[str]) -> None:
        """Step 4 완료: TTS 생성 완료 후"""
        state = self.load()
        
        state['current_phase'] = 'tts_completed'
        
        # files 업데이트
        if 'files' not in state:
            state['files'] = {
                'script': None, 
                'tts_script': None, 
                'scenes': None, 
                'audio': [], 
                'manim': [],
                'subtitles': []
            }
        
        state['files']['audio'] = audio_files
        
        self._state = state
        self.save()

        print(f"✅ state.json 업데이트: tts_completed")
        print(f"   🎤 TTS 완료: {len(audio_files)}개 파일")

    def update_tts_partial(self, project_id: str, audio_files: List[str], resume_from: int) -> None:
        """TTS 부분 완료: 한도 초과로 중단됨"""
        state = self.load()

        state['current_phase'] = 'tts_partial'
        state['tts_resume_from'] = resume_from

        # files 업데이트
        if 'files' not in state:
            state['files'] = {
                'script': None,
                'tts_script': None,
                'scenes': None,
                'audio': [],
                'manim': [],
                'subtitles': []
            }

        state['files']['audio'] = audio_files

        self._state = state
        self.save()

        print(f"⚠️  state.json 업데이트: tts_partial (s{resume_from}부터 재개 필요)")

    def update_manim_scene_completed(self, scene_id: str, manim_file: str) -> None:
        """Step 5 진행: 씬별 Manim 코드 완료 후"""
        state = self.load()
        
        state['current_phase'] = 'manim_coding'
        
        # scenes 업데이트
        if 'scenes' not in state:
            state['scenes'] = {'total': 0, 'completed': [], 'pending': [], 'current': None}
        
        # completed에 추가
        if scene_id not in state['scenes']['completed']:
            state['scenes']['completed'].append(scene_id)
        
        # pending에서 제거
        if scene_id in state['scenes']['pending']:
            state['scenes']['pending'].remove(scene_id)
        
        # current 업데이트 (다음 pending 씬)
        if state['scenes']['pending']:
            state['scenes']['current'] = state['scenes']['pending'][0]
        else:
            state['scenes']['current'] = None
            state['current_phase'] = 'manim_completed'
        
        # files.manim 업데이트
        if 'files' not in state:
            state['files'] = {
                'script': None, 
                'tts_script': None, 
                'scenes': None, 
                'audio': [], 
                'manim': [],
                'subtitles': []
            }
        
        if manim_file not in state['files']['manim']:
            state['files']['manim'].append(manim_file)
        
        self._state = state
        self.save()
        
        print(f"✅ state.json 업데이트: {scene_id} 코드 완료")
        print(f"   완료: {state['scenes']['completed']}")
        print(f"   남음: {state['scenes']['pending']}")
    
    def update_rendering(self) -> None:
        """Step 6: 렌더링 시작"""
        state = self.load()
        state['current_phase'] = 'rendering'
        self._state = state
        self.save()
        print(f"✅ state.json 업데이트: rendering")
    
    def update_completed(self, final_video_path: str) -> None:
        """모든 작업 완료"""
        state = self.load()
        
        state['current_phase'] = 'completed'
        
        if 'files' not in state:
            state['files'] = {
                'script': None, 
                'tts_script': None, 
                'scenes': None, 
                'audio': [], 
                'manim': [],
                'subtitles': []
            }
        
        state['files']['final_video'] = final_video_path
        
        self._state = state
        self.save()
        
        print(f"✅ state.json 업데이트: completed")
        print(f"   🎉 프로젝트 완료: {final_video_path}")
    
    def get_resume_point(self) -> tuple:
        """재개 지점 확인 및 안내"""
        state = self.load()
        
        if not state.get("project_id"):
            return ("시작", "새 프로젝트를 시작하세요. python math_video_pipeline.py init --title \"주제\"")
        
        phase = state.get('current_phase', 'initialized')
        
        resume_guide = {
            'idle': ('시작', '새 프로젝트를 시작하세요.'),
            'initialized': ('대본 작성', 'skills/script-writer.md를 참조하여 대본을 작성하세요.'),
            'script_approved': ('씬 분할', 'skills/scene-director.md를 참조하여 씬을 분할하세요.'),
            'scenes_approved': ('TTS 생성', 'python math_video_pipeline.py tts-all 실행'),
            'tts_completed': ('Manim 코드', f"씬 {state.get('scenes', {}).get('current', 's1')} 코드 작성"),
            'manim_coding': ('Manim 코드 계속', f"씬 {state.get('scenes', {}).get('current', 's1')} 코드 작성"),
            'manim_completed': ('렌더링', 'python math_video_pipeline.py render-all 실행'),
            'rendering': ('렌더링 대기', '렌더링이 진행 중입니다.'),
            'completed': ('완료', '프로젝트가 완료되었습니다.')
        }
        
        next_step, guide = resume_guide.get(phase, ('알 수 없음', '상태를 확인하세요.'))
        
        return (next_step, guide)


# ============================================================================
# 프로젝트 관리 클래스
# ============================================================================

class ProjectManager:
    """프로젝트 초기화 및 관리"""
    
    def __init__(self, state_manager: StateManager):
        self.state = state_manager
    
    def init_project(
        self,
        title: str,
        duration: int = 480,
        style: str = "cyberpunk",
        difficulty: str = "intermediate",
        aspect_ratio: str = "16:9",
        voice: str = "ko-KR-Neural2-C"
    ) -> str:
        """새 프로젝트 초기화"""
        
        # 프로젝트 ID 생성
        project_id = f"P{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 출력 디렉토리 생성
        project_dir = OUTPUT_DIR / project_id
        folders = [
            "0_audio",
            "1_script",
            "2_scenes",
            "3_visual_plans",
            "4_manim_code",
            "5_validation",
            "6_image_prompts",
            "7_subtitles",
            "8_renders",
            "9_backgrounds",
            "10_scene_final"
        ]
        
        for folder in folders:
            (project_dir / folder).mkdir(parents=True, exist_ok=True)
        
        # 상태 업데이트
        self.state.set("project_id", project_id)
        self.state.set("title", title)
        self.state.set("current_phase", "initialized")
        self.state.set("settings.style", style)
        self.state.set("settings.difficulty", difficulty)
        self.state.set("settings.duration", duration)
        self.state.set("settings.aspect_ratio", aspect_ratio)
        self.state.set("settings.voice", voice)
        self.state.set("scenes.total", 0)
        self.state.set("scenes.completed", [])
        self.state.set("scenes.pending", [])
        self.state.set("scenes.current", None)
        self.state.set("files.script", None)
        self.state.set("files.tts_script", None)
        self.state.set("files.scenes", None)
        self.state.set("files.audio", [])
        self.state.set("files.manim", [])
        self.state.set("files.subtitles", [])
        self.state.save()
        
        print(f"✅ 프로젝트 생성 완료: {project_id}")
        print(f"   📁 출력 폴더: {project_dir}")
        print(f"   📝 제목: {title}")
        print(f"   ⏱️  길이: {duration}초 ({duration//60}분 {duration%60}초)")
        print(f"   📐 종횡비: {aspect_ratio}")
        print(f"   🎨 스타일: {style}")
        print(f"   📊 난이도: {difficulty}")
        print(f"   🎤 음성: {voice}")
        print()
        print("📌 다음 단계:")
        print("   Claude Code에서 대본 작성을 요청하세요:")
        print(f'   "skills/script-writer.md 읽고 "{title}" 대본 작성해줘"')
        
        return project_id
    
    def get_project_dir(self) -> Optional[Path]:
        """현재 프로젝트 디렉토리"""
        project_id = self.state.get("project_id")
        if project_id:
            return OUTPUT_DIR / project_id
        return None
    
    def show_status(self) -> None:
        """현재 상태 출력"""
        state = self.state.load()
        
        print("\n" + "="*60)
        print("📊 프로젝트 상태")
        print("="*60)
        
        if not state["project_id"]:
            print("❌ 활성 프로젝트가 없습니다.")
            print("\n새 프로젝트 시작:")
            print('   python math_video_pipeline.py init --title "주제"')
            return
        
        print(f"🆔 프로젝트 ID: {state['project_id']}")
        print(f"📝 제목: {state['title']}")
        print(f"📍 현재 단계: {state['current_phase']}")
        print()
        
        settings = state.get("settings", {})
        print("⚙️  설정:")
        print(f"   스타일: {settings.get('style', 'N/A')}")
        print(f"   난이도: {settings.get('difficulty', 'N/A')}")
        print(f"   길이: {settings.get('duration', 0)}초")
        print(f"   종횡비: {settings.get('aspect_ratio', 'N/A')}")
        print(f"   음성: {settings.get('voice', 'N/A')}")
        print()
        
        scenes = state.get("scenes", {})
        print("🎬 씬 진행 상황:")
        print(f"   총 씬: {scenes.get('total', 0)}개")
        print(f"   완료: {len(scenes.get('completed', []))}개 {scenes.get('completed', [])}")
        print(f"   대기: {len(scenes.get('pending', []))}개 {scenes.get('pending', [])}")
        print(f"   현재: {scenes.get('current', 'N/A')}")
        print()
        
        files = state.get("files", {})
        print("📁 파일:")
        print(f"   대본: {'✅ ' + files.get('script') if files.get('script') else '❌ 없음'}")
        print(f"   TTS대본: {'✅ ' + files.get('tts_script') if files.get('tts_script') else '❌ 없음'}")
        print(f"   씬: {'✅ ' + files.get('scenes') if files.get('scenes') else '❌ 없음'}")
        print(f"   오디오: {len(files.get('audio', []))}개")
        print(f"   Manim: {len(files.get('manim', []))}개")
        print(f"   자막: {len(files.get('subtitles', []))}개")
        print()
        
        if state.get("last_updated"):
            print(f"🕐 마지막 업데이트: {state['last_updated']}")
        
        print("="*60)
        
        # 재개 지점 안내
        next_step, guide = self.state.get_resume_point()
        print(f"\n🔄 재개 지점: {next_step}")
        print(f"   📌 {guide}")
        
        # 다음 단계 안내
        self._suggest_next_step(state)
    
    def _suggest_next_step(self, state: Dict) -> None:
        """다음 단계 제안"""
        phase = state.get("current_phase", "idle")
        
        print("\n📌 다음 단계:")
        
        if phase == "idle":
            print('   프로젝트 시작: python math_video_pipeline.py init --title "주제"')
        
        elif phase == "initialized":
            print("   Claude Code에서 대본 작성:")
            print('   "skills/script-writer.md 읽고 대본 작성해줘"')
        
        elif phase == "script_approved":
            print("   Claude Code에서 씬 분할:")
            print('   "skills/scene-director.md 읽고 씬 분할해줘"')
        
        elif phase == "scenes_approved":
            print("   TTS 생성: python math_video_pipeline.py tts-all")
        
        elif phase == "tts_completed":
            current = state.get("scenes", {}).get("current", "s1")
            print(f"   Claude Code에서 Manim 코드:")
            print(f'   "skills/manim-coder.md 읽고 {current} 코드 생성해줘"')
        
        elif phase == "manim_coding":
            pending = state.get("scenes", {}).get("pending", [])
            if pending:
                next_scene = pending[0]
                print(f"   다음 씬 처리: {next_scene}")
                print(f'   "skills/manim-coder.md 읽고 {next_scene} 코드 생성해줘"')
            else:
                print("   모든 씬 완료! 렌더링 준비:")
                print("   python math_video_pipeline.py render-all")
        
        elif phase == "manim_completed":
            print("   렌더링 실행:")
            print("   python math_video_pipeline.py render-all")
        
        elif phase == "completed":
            print("   🎉 프로젝트가 완료되었습니다!")

    def list_projects(self) -> List[Dict]:
        """output 폴더 내 모든 프로젝트 목록 조회"""
        projects = []

        if not OUTPUT_DIR.exists():
            print("❌ output 폴더가 없습니다.")
            return projects

        for item in OUTPUT_DIR.iterdir():
            if item.is_dir() and item.name.startswith("P"):
                # 프로젝트 폴더 정보 수집
                project_info = {
                    "id": item.name,
                    "path": str(item),
                    "folders": {},
                    "total_size": 0
                }

                # 각 하위 폴더 상태 확인
                for folder in item.iterdir():
                    if folder.is_dir():
                        files = list(folder.glob("*"))
                        file_count = len([f for f in files if f.is_file()])
                        folder_size = sum(f.stat().st_size for f in files if f.is_file())
                        project_info["folders"][folder.name] = {
                            "files": file_count,
                            "size": folder_size
                        }
                        project_info["total_size"] += folder_size

                projects.append(project_info)

        # 날짜 기준 정렬 (최신순)
        projects.sort(key=lambda x: x["id"], reverse=True)

        # 출력
        print("\n" + "="*70)
        print("📁 프로젝트 목록")
        print("="*70)

        if not projects:
            print("❌ 프로젝트가 없습니다.")
            return projects

        current_project = self.state.get("project_id")

        for p in projects:
            is_current = "⭐" if p["id"] == current_project else "  "
            size_mb = p["total_size"] / (1024 * 1024)
            print(f"{is_current} {p['id']} ({size_mb:.1f} MB)")

            # 주요 폴더 상태
            folder_status = []
            folder_order = ["1_script", "2_scenes", "0_audio", "4_manim_code", "8_renders", "10_scene_final"]
            for fname in folder_order:
                if fname in p["folders"]:
                    count = p["folders"][fname]["files"]
                    if count > 0:
                        folder_status.append(f"{fname.split('_')[-1]}:{count}")

            if folder_status:
                print(f"      └─ {', '.join(folder_status)}")

        print("="*70)
        print(f"총 {len(projects)}개 프로젝트")

        return projects

    def delete_project(self, project_id: str, force: bool = False) -> bool:
        """프로젝트 삭제"""
        import shutil

        project_dir = OUTPUT_DIR / project_id

        if not project_dir.exists():
            print(f"❌ 프로젝트를 찾을 수 없습니다: {project_id}")
            return False

        # 현재 활성 프로젝트인지 확인
        current_project = self.state.get("project_id")
        is_current = project_id == current_project

        # 삭제 전 정보 표시
        total_size = sum(f.stat().st_size for f in project_dir.rglob("*") if f.is_file())
        file_count = len(list(project_dir.rglob("*")))

        print(f"\n🗑️  삭제 대상: {project_id}")
        print(f"   📁 경로: {project_dir}")
        print(f"   📊 파일: {file_count}개")
        print(f"   💾 크기: {total_size / (1024*1024):.1f} MB")
        if is_current:
            print(f"   ⚠️  현재 활성 프로젝트입니다!")

        if not force:
            print("\n⚠️  이 작업은 되돌릴 수 없습니다!")
            print("   삭제를 확인하려면 --force 옵션을 추가하세요:")
            print(f"   python math_video_pipeline.py delete {project_id} --force")
            return False

        # 삭제 실행
        try:
            shutil.rmtree(project_dir)
            print(f"\n✅ 프로젝트 삭제 완료: {project_id}")

            # 현재 프로젝트였다면 state 초기화
            if is_current:
                self.state.reset()
                print("   state.json 초기화됨")

            return True
        except Exception as e:
            print(f"❌ 삭제 실패: {e}")
            return False

    def clean_project(self, project_id: str = None, folders: List[str] = None, force: bool = False) -> bool:
        """프로젝트 특정 폴더 내용 정리 (폴더 구조는 유지)"""
        import shutil

        # 프로젝트 ID 결정
        if project_id is None:
            project_id = self.state.get("project_id")

        if not project_id:
            print("❌ 프로젝트 ID를 지정하거나 활성 프로젝트가 필요합니다.")
            return False

        project_dir = OUTPUT_DIR / project_id

        if not project_dir.exists():
            print(f"❌ 프로젝트를 찾을 수 없습니다: {project_id}")
            return False

        # 정리할 폴더 결정
        all_folders = [
            "0_audio", "1_script", "2_scenes", "3_visual_plans",
            "4_manim_code", "5_validation", "6_image_prompts",
            "7_subtitles", "8_renders", "9_backgrounds", "10_scene_final"
        ]

        if folders is None:
            target_folders = all_folders
        else:
            # 사용자 지정 폴더 검증
            target_folders = []
            for f in folders:
                # 숫자만 입력해도 매칭
                matched = [af for af in all_folders if f in af or af.startswith(f)]
                target_folders.extend(matched)
            target_folders = list(set(target_folders))

        if not target_folders:
            print("❌ 정리할 폴더가 없습니다.")
            return False

        # 정리 대상 정보 표시
        print(f"\n🧹 정리 대상: {project_id}")
        total_files = 0
        total_size = 0

        for folder_name in sorted(target_folders):
            folder_path = project_dir / folder_name
            if folder_path.exists():
                files = list(folder_path.glob("*"))
                file_count = len([f for f in files if f.is_file()])
                folder_size = sum(f.stat().st_size for f in files if f.is_file())
                if file_count > 0:
                    print(f"   📁 {folder_name}: {file_count}개 ({folder_size/(1024*1024):.1f} MB)")
                    total_files += file_count
                    total_size += folder_size

        if total_files == 0:
            print("   ✅ 정리할 파일이 없습니다.")
            return True

        print(f"\n   📊 총 {total_files}개 파일, {total_size/(1024*1024):.1f} MB")

        if not force:
            print("\n⚠️  이 작업은 되돌릴 수 없습니다!")
            print("   정리를 확인하려면 --force 옵션을 추가하세요")
            return False

        # 정리 실행
        cleaned_count = 0
        for folder_name in target_folders:
            folder_path = project_dir / folder_name
            if folder_path.exists():
                for item in folder_path.iterdir():
                    if item.is_file():
                        item.unlink()
                        cleaned_count += 1
                    elif item.is_dir():
                        shutil.rmtree(item)
                        cleaned_count += 1

        print(f"\n✅ 정리 완료: {cleaned_count}개 항목 삭제")
        return True

    def reset_project(self, project_id: str = None, from_phase: str = None, force: bool = False) -> bool:
        """프로젝트를 특정 단계로 리셋 (해당 단계 이후 산출물 삭제)"""

        # 프로젝트 ID 결정
        if project_id is None:
            project_id = self.state.get("project_id")

        if not project_id:
            print("❌ 프로젝트 ID를 지정하거나 활성 프로젝트가 필요합니다.")
            return False

        project_dir = OUTPUT_DIR / project_id

        if not project_dir.exists():
            print(f"❌ 프로젝트를 찾을 수 없습니다: {project_id}")
            return False

        # 단계별 삭제 대상 폴더 정의
        phase_folders = {
            "initialized": ["1_script", "2_scenes", "3_visual_plans", "4_manim_code",
                           "5_validation", "6_image_prompts", "7_subtitles",
                           "8_renders", "9_backgrounds", "10_scene_final", "0_audio"],
            "script_approved": ["2_scenes", "3_visual_plans", "4_manim_code",
                               "5_validation", "6_image_prompts", "7_subtitles",
                               "8_renders", "9_backgrounds", "10_scene_final", "0_audio"],
            "scenes_completed": ["3_visual_plans", "4_manim_code", "5_validation",
                                "6_image_prompts", "7_subtitles", "8_renders",
                                "9_backgrounds", "10_scene_final", "0_audio"],
            "assets_checked": ["3_visual_plans", "4_manim_code", "5_validation",
                              "6_image_prompts", "7_subtitles", "8_renders",
                              "9_backgrounds", "10_scene_final", "0_audio"],
            "tts_completed": ["3_visual_plans", "4_manim_code", "5_validation",
                             "6_image_prompts", "7_subtitles", "8_renders",
                             "9_backgrounds", "10_scene_final"],
            "visual_prompts_completed": ["4_manim_code", "5_validation",
                                        "8_renders", "10_scene_final"],
            "manim_completed": ["5_validation", "8_renders", "10_scene_final"],
            "manim_validated": ["8_renders", "10_scene_final"],
            "images_ready": ["10_scene_final"],
            "rendered": ["10_scene_final"],
        }

        if from_phase is None:
            print("\n📋 사용 가능한 리셋 지점:")
            for phase in phase_folders.keys():
                folders = phase_folders[phase]
                print(f"   {phase}: {len(folders)}개 폴더 삭제")
            print("\n사용법: python math_video_pipeline.py reset --from <phase> --force")
            return False

        if from_phase not in phase_folders:
            print(f"❌ 알 수 없는 단계: {from_phase}")
            print(f"   사용 가능: {', '.join(phase_folders.keys())}")
            return False

        target_folders = phase_folders[from_phase]

        print(f"\n🔄 리셋 대상: {project_id}")
        print(f"   📍 리셋 지점: {from_phase}")
        print(f"   📁 삭제 폴더: {', '.join(target_folders)}")

        if not force:
            print("\n⚠️  이 작업은 되돌릴 수 없습니다!")
            print(f"   python math_video_pipeline.py reset --from {from_phase} --force")
            return False

        # 리셋 실행
        return self.clean_project(project_id, target_folders, force=True)


# ============================================================================
# TTS 생성기 클래스
# ============================================================================

class TTSGenerator:
    """OpenAI TTS (gpt-4o-mini-tts) - 문장별 분할 생성"""

    # OpenAI gpt-4o-mini-tts 지원 음성 (13개)
    OPENAI_VOICES = {
        "alloy": "중성적, 균형잡힌",
        "ash": "차분한 남성 [기본값]",
        "ballad": "부드러운 낭독",
        "coral": "따뜻한 여성",
        "echo": "남성적, 차분함",
        "fable": "영국식 억양",
        "onyx": "남성적, 깊은 목소리",
        "nova": "여성적, 밝고 친근",
        "sage": "지적인 톤",
        "shimmer": "여성적, 부드러움",
        "verse": "표현력 풍부",
        "marin": "고품질 추천",
        "cedar": "고품질 추천",
    }

    # 한국어 TTS 기본 instructions
    DEFAULT_INSTRUCTIONS = "Speak in a deep, calm, educational Korean tone with clear pronunciation."

    def __init__(self, state_manager: StateManager):
        self.state = state_manager
        self.openai_client = get_openai_client()

    def _split_into_sentences(self, text: str) -> List[str]:
        """텍스트를 문장 단위로 분할 (줄바꿈 기준)

        TTS 녹음을 위해 각 줄을 개별 문장으로 처리합니다.
        - \n\n (빈 줄): 문단 구분
        - \n (줄바꿈): 문장 구분
        """
        # 모든 줄바꿈으로 분할 (빈 줄이든 단일 줄바꿈이든)
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        return lines

    def _save_wav(self, filename: Path, pcm_data: bytes, channels: int = 1, rate: int = 24000, sample_width: int = 2):
        """PCM 데이터를 WAV 파일로 저장"""
        with wave.open(str(filename), "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(rate)
            wf.writeframes(pcm_data)

    def _get_wav_duration(self, filename: Path) -> float:
        """WAV 파일의 재생 시간 계산"""
        try:
            with wave.open(str(filename), "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                return frames / float(rate)
        except:
            return 0.0

    def _save_partial_timing(self, audio_dir: Path, scene_id: str, voice_name: str,
                             sentence_results: list, audio_files: list, total_duration: float):
        """부분 완료된 TTS 타이밍 저장 (한도 초과 시 사용)"""
        timing_file = audio_dir / f"{scene_id}_timing_partial.json"
        timing_data = {
            "scene_id": scene_id,
            "voice": voice_name,
            "total_duration": total_duration,
            "sentence_count": len(sentence_results),
            "sentences": sentence_results,
            "audio_files": audio_files,
            "created_at": datetime.now().isoformat(),
            "status": "partial"  # 부분 완료 표시
        }
        with open(timing_file, 'w', encoding='utf-8') as f:
            json.dump(timing_data, f, ensure_ascii=False, indent=2)
        print(f"   📁 부분 저장: {timing_file}")

    def _generate_openai_tts(self, text: str, voice: str, output_file: Path,
                              instructions: str = None, max_retries: int = 3) -> bool:
        """OpenAI gpt-4o-mini-tts로 음성 생성 (MP3 출력)"""
        import time

        # instructions 기본값
        if instructions is None:
            instructions = self.DEFAULT_INSTRUCTIONS

        for attempt in range(max_retries):
            try:
                response = self.openai_client.audio.speech.create(
                    model="gpt-4o-mini-tts",  # 새 모델 (한국어 품질 개선, 저렴)
                    voice=voice,
                    input=text,
                    instructions=instructions,  # 음성 스타일 지정
                    response_format="mp3"
                )

                # MP3 파일로 저장
                mp3_file = output_file.with_suffix('.mp3')
                response.stream_to_file(str(mp3_file))

                # 성공 후 짧은 대기 (Rate limit 방지)
                time.sleep(0.3)
                return True

            except Exception as e:
                error_str = str(e).lower()
                if "429" in str(e) or "rate" in error_str:
                    wait_time = 5 * (2 ** attempt)  # 5, 10, 20초
                    print(f"      ⏳ Rate limit - {wait_time}초 대기 후 재시도 ({attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"      ❌ OpenAI TTS 실패: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2)

        return False

    def _get_mp3_duration(self, filename: Path) -> float:
        """MP3 파일의 재생 시간 계산 (mutagen 또는 ffprobe 사용)"""
        try:
            # mutagen 시도
            from mutagen.mp3 import MP3
            audio = MP3(str(filename))
            return audio.info.length
        except ImportError:
            pass
        except Exception:
            pass

        try:
            # ffprobe 시도
            import subprocess
            result = subprocess.run(
                ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                 '-of', 'csv=p=0', str(filename)],
                capture_output=True, text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
        except Exception:
            pass

        return 0.0

    def _extract_voice_name(self, voice_setting: str) -> str:
        """설정에서 OpenAI 음성 이름 추출"""
        voice_setting_lower = voice_setting.lower()
        for voice_name in self.OPENAI_VOICES.keys():
            if voice_name in voice_setting_lower:
                return voice_name
        return "ash"  # 기본값

    # ========================================================================
    # [DEPRECATED] 기존 generate() - 문장별 TTS 방식
    # ========================================================================
    # 이유: 문장별로 TTS를 호출하면 문장 사이가 부자연스럽게 끊기고,
    #       자막이 2줄로 나오는 문제가 있었음.
    # 개선: 씬 전체를 한 번에 TTS → Whisper로 문장별 timestamp 추출
    # ========================================================================
    # def generate_old(
    #     self,
    #     scene_id: str,
    #     text: str,
    #     voice: Optional[str] = None
    # ) -> Optional[Dict[str, Any]]:
    #     """OpenAI TTS - 문장별 음성 생성 (DEPRECATED)"""
    #
    #     if not self.openai_client:
    #         print("❌ OpenAI 클라이언트를 초기화할 수 없습니다.")
    #         print("   .env 파일에 OPENAI_API_KEY를 설정하세요.")
    #         return None
    #
    #     project_dir = OUTPUT_DIR / self.state.get("project_id", "unknown")
    #     audio_dir = project_dir / "0_audio"
    #     audio_dir.mkdir(parents=True, exist_ok=True)
    #
    #     # 음성 설정 (기본값: ash)
    #     voice_setting = voice or self.state.get("settings.voice", "ash")
    #     voice_name = self._extract_voice_name(voice_setting)
    #
    #     print(f"\n🎤 [{scene_id}] TTS 생성 중... (OpenAI)")
    #     print(f"   음성: {voice_name}")
    #
    #     # 텍스트를 문장 단위로 분할
    #     sentences = self._split_into_sentences(text)
    #     print(f"   문장 수: {len(sentences)}개")
    #
    #     sentence_results = []
    #     total_duration = 0.0
    #     audio_files = []
    #
    #     for idx, sentence in enumerate(sentences, 1):
    #         sentence_id = f"{scene_id}_{idx}"
    #         audio_file = audio_dir / f"{sentence_id}.mp3"
    #
    #         # 문장 미리보기 (너무 길면 자름)
    #         preview = sentence[:40] + "..." if len(sentence) > 40 else sentence
    #         print(f"      [{idx}/{len(sentences)}] {preview}")
    #
    #         # OpenAI TTS 생성
    #         success = self._generate_openai_tts(sentence, voice_name, audio_file)
    #
    #         if success:
    #             duration = self._get_mp3_duration(audio_file)
    #             gap = 0.1  # 문장 사이 여유 시간
    #             sentence_results.append({
    #                 "sentence_id": sentence_id,
    #                 "sentence_index": idx,
    #                 "text": sentence,
    #                 "audio_file": str(audio_file),
    #                 "start": total_duration,
    #                 "end": total_duration + duration + gap,
    #                 "duration": duration + gap
    #             })
    #             audio_files.append(str(audio_file))
    #             total_duration += duration + gap
    #             print(f"         ✅ {duration:.2f}초 (+{gap}s gap)")
    #         else:
    #             print(f"         ❌ 실패")
    #
    #     if not sentence_results:
    #         return None
    #
    #     # 타이밍 JSON 저장
    #     timing_file = audio_dir / f"{scene_id}_timing.json"
    #     timing_data = {
    #         "scene_id": scene_id,
    #         "voice": voice_name,
    #         "total_duration": total_duration,
    #         "sentence_count": len(sentence_results),
    #         "sentences": sentence_results,
    #         "audio_files": audio_files,
    #         "created_at": datetime.now().isoformat()
    #     }
    #
    #     with open(timing_file, 'w', encoding='utf-8') as f:
    #         json.dump(timing_data, f, ensure_ascii=False, indent=2)
    #
    #     print(f"   ✅ 완료: {len(sentence_results)}개 문장, 총 {total_duration:.2f}초")
    #
    #     # state에 오디오 파일 추가
    #     for af in audio_files:
    #         self.state.add_file("audio", af)
    #
    #     return timing_data
    # ========================================================================

    def _transcribe_with_whisper(self, audio_file: Path, original_text: str) -> Optional[Dict[str, Any]]:
        """Whisper API로 오디오 파일 분석하여 문장별 timestamp 추출

        Args:
            audio_file: 분석할 오디오 파일 경로
            original_text: 원본 텍스트 (힌트용)

        Returns:
            {
                "segments": [...],  # 문장별 시간 정보
                "words": [...],     # 단어별 시간 정보 (있을 경우)
                "full_text": "...", # 전사된 전체 텍스트
                "duration": 10.5    # 총 길이
            }
        """
        if not self.openai_client:
            return None

        try:
            print(f"   📊 Whisper 타임스탬프 추출 중...")

            # Whisper 프롬프트 (인식 정확도 향상용)
            prompt = f"""[엄격 규칙]
1. 음성에 들린 내용만 정확히 전사
2. 인사말, 감사, 추임새, 감탄사 절대 추가 금지
3. 타임스탬프는 실제 발화 시간 정확히 반영

이것은 수학 교육 영상 나레이션입니다.
수학 용어: 미분, 적분, 벡터, 내적, 제곱근, 함수, 그래프 등

예상 내용: {original_text[:200]}"""

            with open(audio_file, "rb") as f:
                # verbose_json으로 segment별 timestamp 획득
                response = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    language="ko",
                    response_format="verbose_json",
                    timestamp_granularities=["segment", "word"],
                    prompt=prompt
                )

            result = {
                "segments": [],
                "words": [],
                "full_text": response.text,
                "duration": response.duration if hasattr(response, 'duration') else 0
            }

            # Segment 정보 추출 (문장 단위)
            if hasattr(response, 'segments') and response.segments:
                for seg in response.segments:
                    result["segments"].append({
                        "text": seg.text.strip() if hasattr(seg, 'text') else "",
                        "start": seg.start if hasattr(seg, 'start') else 0,
                        "end": seg.end if hasattr(seg, 'end') else 0,
                        "duration": (seg.end - seg.start) if hasattr(seg, 'end') and hasattr(seg, 'start') else 0
                    })

            # Word 정보 추출 (단어 단위) - 있으면
            if hasattr(response, 'words') and response.words:
                for word in response.words:
                    result["words"].append({
                        "text": word.word.strip() if hasattr(word, 'word') else "",
                        "start": word.start if hasattr(word, 'start') else 0,
                        "end": word.end if hasattr(word, 'end') else 0
                    })

            print(f"      ✅ {len(result['segments'])}개 세그먼트, {len(result['words'])}개 단어 추출")

            return result

        except Exception as e:
            print(f"      ❌ Whisper 분석 실패: {e}")
            return None

    def generate(
        self,
        scene_id: str,
        text: str,
        voice: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """OpenAI TTS + Whisper - 씬 전체 음성 생성 후 문장별 timestamp 추출

        개선점:
        - 씬 전체를 한 번에 TTS → 자연스러운 음성
        - Whisper로 문장별 timestamp 추출 → 정확한 자막 타이밍
        - 파일 1개로 관리 용이
        """

        if not self.openai_client:
            print("❌ OpenAI 클라이언트를 초기화할 수 없습니다.")
            print("   .env 파일에 OPENAI_API_KEY를 설정하세요.")
            return None

        project_dir = OUTPUT_DIR / self.state.get("project_id", "unknown")
        audio_dir = project_dir / "0_audio"
        audio_dir.mkdir(parents=True, exist_ok=True)

        # 음성 설정 (기본값: alloy)
        voice_setting = voice or self.state.get("settings.voice", "alloy")
        voice_name = self._extract_voice_name(voice_setting)

        print(f"\n🎤 [{scene_id}] TTS 생성 중... (OpenAI + Whisper)")
        print(f"   음성: {voice_name}")

        # 텍스트 미리보기
        preview = text[:60] + "..." if len(text) > 60 else text
        print(f"   텍스트: {preview}")

        # 1. 씬 전체 텍스트로 TTS 생성 (파일 1개)
        audio_file = audio_dir / f"{scene_id}.mp3"
        print(f"   🔊 TTS 생성 중...")

        success = self._generate_openai_tts(text, voice_name, audio_file)

        if not success:
            print(f"   ❌ TTS 생성 실패")
            return None

        # 전체 duration 확인
        total_duration = self._get_mp3_duration(audio_file)
        print(f"   ✅ TTS 완료: {total_duration:.2f}초")

        # 2. Whisper로 문장별 timestamp 추출
        whisper_result = self._transcribe_with_whisper(audio_file, text)

        if not whisper_result or not whisper_result.get("segments"):
            # Whisper 실패 시 전체를 하나의 segment로 처리
            print(f"   ⚠️ Whisper 분석 실패, 전체를 단일 세그먼트로 처리")
            whisper_result = {
                "segments": [{
                    "text": text,
                    "start": 0,
                    "end": total_duration,
                    "duration": total_duration
                }],
                "words": [],
                "full_text": text,
                "duration": total_duration
            }

        # 3. timing.json 형식으로 변환 (기존 형식 호환)
        sentence_results = []
        for idx, seg in enumerate(whisper_result["segments"], 1):
            sentence_results.append({
                "sentence_id": f"{scene_id}_{idx}",
                "sentence_index": idx,
                "text": seg["text"],
                "start": seg["start"],
                "end": seg["end"],
                "duration": seg["duration"]
            })

        # 타이밍 JSON 저장
        timing_file = audio_dir / f"{scene_id}_timing.json"
        timing_data = {
            "scene_id": scene_id,
            "voice": voice_name,
            "total_duration": total_duration,
            "sentence_count": len(sentence_results),
            "sentences": sentence_results,
            "audio_files": [str(audio_file)],  # 이제 파일 1개
            "words": whisper_result.get("words", []),  # 단어별 타이밍 (보너스)
            "whisper_text": whisper_result.get("full_text", ""),  # Whisper 전사 결과
            "created_at": datetime.now().isoformat(),
            "method": "tts_whisper"  # 새 방식 표시
        }

        with open(timing_file, 'w', encoding='utf-8') as f:
            json.dump(timing_data, f, ensure_ascii=False, indent=2)

        print(f"   ✅ 완료: {len(sentence_results)}개 세그먼트, 총 {total_duration:.2f}초")

        # 전사 정확도 표시
        if whisper_result.get("full_text"):
            # 간단한 유사도 체크
            original_clean = text.replace(" ", "").replace(",", "").replace(".", "")
            whisper_clean = whisper_result["full_text"].replace(" ", "").replace(",", "").replace(".", "")
            if original_clean and whisper_clean:
                # 공통 글자 수 기반 유사도
                common = sum(1 for c in whisper_clean if c in original_clean)
                similarity = (common / max(len(original_clean), len(whisper_clean))) * 100
                print(f"   📝 전사 유사도: {similarity:.1f}%")

        # state에 오디오 파일 추가
        self.state.add_file("audio", str(audio_file))

        return timing_data
    
    def _get_narration_tts(self, project_dir: Path, scene_id: str, scene_data: dict) -> str:
        """narration_tts 텍스트를 가져옴 (우선순위: narration#.json > scenes.json)

        Args:
            project_dir: 프로젝트 디렉토리
            scene_id: 씬 ID (예: s1)
            scene_data: scenes.json에서 읽은 씬 데이터 (fallback용)

        Returns:
            narration_tts 텍스트
        """
        # 1. narration#.json 우선 확인
        narration_file = project_dir / "2_narration" / f"{scene_id}_narration.json"
        if narration_file.exists():
            try:
                with open(narration_file, 'r', encoding='utf-8') as f:
                    narration_data = json.load(f)
                    narration_tts = narration_data.get("narration_tts", "")
                    if narration_tts:
                        return narration_tts
            except Exception:
                pass

        # 2. Fallback: scenes.json의 narration_tts 또는 narration_display
        return scene_data.get("narration_tts") or scene_data.get("narration_display", "")

    def generate_all_from_scenes(self, start_from: int = 1) -> List[Dict[str, Any]]:
        """scenes.json의 모든 씬에 대해 TTS 생성 (문장별)

        Args:
            start_from: 시작할 씬 번호 (1부터 시작, 예: 14면 s14부터 시작)

        텍스트 소스 우선순위:
            1. 2_narration/{scene_id}_narration.json의 narration_tts
            2. 2_scenes/scenes.json의 narration_tts (fallback)
            3. 2_scenes/scenes.json의 narration_display (fallback)
        """
        project_id = self.state.get("project_id", "unknown")
        project_dir = OUTPUT_DIR / project_id
        scenes_file = project_dir / "2_scenes" / "scenes.json"
        audio_dir = project_dir / "0_audio"

        if not scenes_file.exists():
            print(f"❌ 씬 파일이 없습니다: {scenes_file}")
            return []

        with open(scenes_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # scenes.json이 배열이면 직접 사용, 객체면 scenes 키 사용
        if isinstance(data, list):
            scenes = data
        else:
            scenes = data if isinstance(data, list) else data.get("scenes", [])
        if not scenes:
            print("❌ 씬이 없습니다.")
            return []

        # narration 파일 존재 여부 확인
        narration_dir = project_dir / "2_narration"
        use_narration_files = narration_dir.exists() and list(narration_dir.glob("*_narration.json"))

        print(f"\n🎬 총 {len(scenes)}개 씬 TTS 생성 시작 (OpenAI TTS)")
        if use_narration_files:
            print(f"   📁 텍스트 소스: 2_narration/")
        else:
            print(f"   📁 텍스트 소스: 2_scenes/scenes.json (fallback)")
        if start_from > 1:
            print(f"   s{start_from}부터 시작 (s1-s{start_from-1} 건너뜀)")
        print("="*60)

        results = []
        all_audio_files = []
        total_sentences = 0
        total_duration = 0.0
        skipped = 0

        for i, scene in enumerate(scenes, 1):
            scene_id = scene.get("scene_id", f"s{i}")

            # start_from 이전의 씬은 건너뛰기
            scene_num = int(scene_id[1:]) if scene_id.startswith('s') and scene_id[1:].isdigit() else i
            if scene_num < start_from:
                # 기존 타이밍 파일이 있으면 결과에 추가
                timing_file = audio_dir / f"{scene_id}_timing.json"
                if timing_file.exists():
                    with open(timing_file, 'r', encoding='utf-8') as f:
                        existing = json.load(f)
                        results.append(existing)
                        all_audio_files.extend(existing.get("audio_files", []))
                        total_sentences += existing.get("sentence_count", 0)
                        total_duration += existing.get("total_duration", 0.0)
                skipped += 1
                continue

            # narration_tts 텍스트 가져오기 (narration#.json 우선)
            text = self._get_narration_tts(project_dir, scene_id, scene)

            if not text:
                print(f"\n⚠️  [{scene_id}] 나레이션 텍스트가 없습니다. 건너뜁니다.")
                continue

            print(f"\n[{i}/{len(scenes)}] {scene_id}")

            try:
                result = self.generate(scene_id, text)
            except QuotaExceededException:
                # 한도 초과 시 현재까지 진행 상황 저장 후 중단
                print("\n" + "="*60)
                print(f"⚠️  TTS 생성 중단: {len(results)}/{len(scenes)}개 씬 완료")
                print(f"   총 문장: {total_sentences}개")
                print(f"   총 시간: {total_duration:.1f}초 ({total_duration/60:.1f}분)")
                print(f"\n   📌 다음 명령으로 이어서 진행하세요:")
                print(f"   python math_video_pipeline.py tts-all --start-from {scene_num}")
                print("="*60)

                # 부분 완료 상태 저장
                if results:
                    self.state.update_tts_partial(project_id, all_audio_files, scene_num)

                return results  # 현재까지 결과 반환

            if result:
                results.append(result)
                # 문장별 오디오 파일 수집
                all_audio_files.extend(result.get("audio_files", []))
                total_sentences += result.get("sentence_count", 0)
                total_duration += result.get("total_duration", 0.0)

        print("\n" + "="*60)
        print(f"✅ TTS 생성 완료: {len(results)}/{len(scenes)}개 씬")
        print(f"   총 문장: {total_sentences}개")
        print(f"   총 시간: {total_duration:.1f}초 ({total_duration/60:.1f}분)")

        if results:
            self.state.update_tts_completed(project_id, all_audio_files)

        return results

    def generate_for_scene(self, scene_id: str) -> Optional[Dict[str, Any]]:
        """단일 씬의 TTS 재생성 (narration#.json 우선, scenes.json fallback)"""
        project_id = self.state.get("project_id", "unknown")
        project_dir = OUTPUT_DIR / project_id
        scenes_dir = project_dir / "2_scenes"

        # 개별 씬 파일 먼저 확인
        scene_file = scenes_dir / f"{scene_id}.json"
        if scene_file.exists():
            with open(scene_file, 'r', encoding='utf-8') as f:
                scene_data = json.load(f)
        else:
            # scenes.json에서 찾기
            scenes_file = scenes_dir / "scenes.json"
            if not scenes_file.exists():
                print(f"❌ 씬 파일이 없습니다: {scenes_file}")
                return None

            with open(scenes_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            scenes = data if isinstance(data, list) else data.get("scenes", [])
            scene_data = None
            for scene in scenes:
                if scene.get("scene_id") == scene_id:
                    scene_data = scene
                    break

            if not scene_data:
                print(f"❌ 씬을 찾을 수 없습니다: {scene_id}")
                return None

        # narration_tts 텍스트 가져오기 (narration#.json 우선)
        text = self._get_narration_tts(project_dir, scene_id, scene_data)
        if not text:
            print(f"❌ {scene_id}: 나레이션 텍스트가 없습니다.")
            return None

        print(f"\n🎤 {scene_id} TTS 재생성 시작...")
        result = self.generate(scene_id, text)

        if result:
            print(f"✅ {scene_id} TTS 생성 완료: {result.get('total_duration', 0):.1f}초")

        return result

    def verify_sync(self, scene_id: Optional[str] = None) -> dict:
        """대본(scenes.json)과 TTS 녹음(timing.json) 동기화 검증

        Args:
            scene_id: 특정 씬만 검증 (None이면 전체 검증)

        Returns:
            {"ok": [...], "mismatch": [...], "missing_scene": [...], "missing_timing": [...]}
        """
        project_id = self.state.get("project_id", "unknown")
        project_dir = OUTPUT_DIR / project_id
        scenes_dir = project_dir / "2_scenes"
        audio_dir = project_dir / "0_audio"

        result = {"ok": [], "mismatch": [], "missing_scene": [], "missing_timing": []}

        def normalize(text: str) -> str:
            """비교를 위한 텍스트 정규화 (구두점/공백 제거)"""
            return text.replace(',', '').replace('.', '').replace('...', '').replace(' ', '').replace('?', '').replace('!', '')[:40]

        def check_scene(sid: str):
            scene_file = scenes_dir / f"{sid}.json"
            timing_file = audio_dir / f"{sid}_timing.json"

            if not scene_file.exists():
                result["missing_scene"].append(sid)
                return
            if not timing_file.exists():
                result["missing_timing"].append(sid)
                return

            with open(scene_file, 'r', encoding='utf-8') as f:
                scene_data = json.load(f)
            with open(timing_file, 'r', encoding='utf-8') as f:
                timing_data = json.load(f)

            scene_tts = scene_data.get('narration_tts', '').strip()
            whisper_text = timing_data.get('whisper_text', '').strip()

            if normalize(scene_tts) == normalize(whisper_text):
                result["ok"].append(sid)
            else:
                result["mismatch"].append({
                    "scene_id": sid,
                    "script": scene_tts[:60] + "..." if len(scene_tts) > 60 else scene_tts,
                    "recorded": whisper_text[:60] + "..." if len(whisper_text) > 60 else whisper_text
                })

        if scene_id:
            # 단일 씬 검증
            check_scene(scene_id)
        else:
            # 전체 검증 - scenes 폴더의 모든 s*.json
            import re
            scene_files = sorted(scenes_dir.glob("s*.json"),
                                key=lambda p: (int(re.match(r's(\d+)', p.stem).group(1)) if re.match(r's(\d+)', p.stem) else 0, p.stem))
            for sf in scene_files:
                sid = sf.stem
                if re.match(r's\d+[a-z]?$', sid):  # s1, s2, s32a 등
                    check_scene(sid)

        # 결과 출력
        print("\n" + "="*60)
        print("📋 대본-TTS 동기화 검증 결과")
        print("="*60)

        if result["ok"]:
            print(f"\n✅ 일치: {len(result['ok'])}개")
            if len(result["ok"]) <= 10:
                print(f"   {', '.join(result['ok'])}")

        if result["mismatch"]:
            print(f"\n❌ 불일치: {len(result['mismatch'])}개")
            for m in result["mismatch"][:5]:  # 처음 5개만 상세 출력
                print(f"\n   [{m['scene_id']}]")
                print(f"   대본: {m['script']}")
                print(f"   녹음: {m['recorded']}")
            if len(result["mismatch"]) > 5:
                mismatch_ids = [m["scene_id"] for m in result["mismatch"][5:]]
                print(f"\n   ... 외 {len(mismatch_ids)}개: {', '.join(mismatch_ids)}")

            # TTS 재생성 안내
            first_mismatch = result["mismatch"][0]["scene_id"]
            scene_num = int(first_mismatch[1:]) if first_mismatch[1:].isdigit() else 1
            print(f"\n   💡 해결: python math_video_pipeline.py tts-all --start-from {scene_num}")

        if result["missing_scene"]:
            print(f"\n⚠️ 씬 파일 없음: {', '.join(result['missing_scene'])}")

        if result["missing_timing"]:
            print(f"\n⚠️ 타이밍 파일 없음: {', '.join(result['missing_timing'])}")

        if not result["mismatch"] and not result["missing_scene"] and not result["missing_timing"]:
            print("\n🎉 모든 씬이 동기화되어 있습니다!")

        print("\n" + "="*60)

        return result

    def export_texts(self) -> Optional[Path]:
        """외부 녹음용 텍스트 JSON 내보내기

        narration#.json (우선) 또는 scenes.json에서 모든 씬의 narration_tts를
        문장별로 분리하여 0_audio/tts_texts.json으로 내보냅니다.

        Returns:
            생성된 JSON 파일 경로 (실패 시 None)
        """
        project_id = self.state.get("project_id")
        if not project_id:
            print("❌ 활성 프로젝트가 없습니다.")
            return None

        project_dir = OUTPUT_DIR / project_id
        scenes_file = project_dir / "2_scenes" / "scenes.json"

        if not scenes_file.exists():
            print(f"❌ scenes.json이 없습니다: {scenes_file}")
            return None

        with open(scenes_file, 'r', encoding='utf-8') as f:
            scenes_data = json.load(f)

        # scenes.json은 배열 형태일 수도, {"scenes": [...]} 형태일 수도 있음
        if isinstance(scenes_data, list):
            scenes = scenes_data
        else:
            scenes = scenes_data.get("scenes", [])

        if not scenes:
            print("❌ scenes.json에 씬 데이터가 없습니다.")
            return None

        # 오디오 폴더 생성
        audio_dir = project_dir / "0_audio"
        audio_dir.mkdir(parents=True, exist_ok=True)

        # narration 파일 존재 여부 확인
        narration_dir = project_dir / "2_narration"
        use_narration_files = narration_dir.exists() and list(narration_dir.glob("*_narration.json"))

        # 문장별 텍스트 수집
        tts_texts = {}
        total_sentences = 0

        print(f"🎙️ 외부 녹음용 텍스트 내보내기")
        if use_narration_files:
            print(f"   📁 텍스트 소스: 2_narration/")
        else:
            print(f"   📁 텍스트 소스: 2_scenes/scenes.json (fallback)")
        print("=" * 60)

        for scene in scenes:
            scene_id = scene.get("scene_id", "")

            # narration_tts 가져오기 (narration#.json 우선)
            narration_tts = self._get_narration_tts(project_dir, scene_id, scene)

            if not narration_tts:
                continue

            # 문장 분할
            sentences = self._split_into_sentences(narration_tts)

            for idx, sentence in enumerate(sentences, 1):
                key = f"{scene_id}_{idx}"
                tts_texts[key] = sentence
                total_sentences += 1

            print(f"   {scene_id}: {len(sentences)}개 문장")

        # JSON 저장
        output_file = audio_dir / "tts_texts.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(tts_texts, f, ensure_ascii=False, indent=2)

        print("=" * 60)
        print(f"✅ 텍스트 내보내기 완료!")
        print(f"   📁 파일: {output_file}")
        print(f"   📊 총 {len(scenes)}개 씬, {total_sentences}개 문장")
        print()
        print("📋 녹음 안내:")
        print("   1. 각 문장별로 개별 파일 녹음")
        print("   2. 파일명: s1_1.mp3, s1_2.mp3, s2_1.wav ...")
        print(f"   3. 저장 위치: {audio_dir}")
        print()
        print('녹음 완료 후 "python math_video_pipeline.py audio-check" 실행')

        return output_file

    def check_audio_files(self) -> Dict[str, List[str]]:
        """외부 녹음 파일 누락 확인

        tts_texts.json과 실제 오디오 파일을 비교하여
        누락된 파일 목록을 반환합니다.

        Returns:
            {"available": [...], "missing": [...]}
        """
        project_id = self.state.get("project_id")
        if not project_id:
            print("❌ 활성 프로젝트가 없습니다.")
            return {"available": [], "missing": []}

        project_dir = OUTPUT_DIR / project_id
        audio_dir = project_dir / "0_audio"
        texts_file = audio_dir / "tts_texts.json"

        if not texts_file.exists():
            print(f"❌ tts_texts.json이 없습니다.")
            print(f"   먼저 'python math_video_pipeline.py tts-export' 실행하세요.")
            return {"available": [], "missing": []}

        with open(texts_file, 'r', encoding='utf-8') as f:
            tts_texts = json.load(f)

        # 파일 확인
        available = []
        missing = []

        print(f"🔍 외부 녹음 파일 확인")
        print("=" * 60)

        for key in tts_texts.keys():
            # mp3 또는 wav 확인
            mp3_file = audio_dir / f"{key}.mp3"
            wav_file = audio_dir / f"{key}.wav"

            if mp3_file.exists():
                available.append(f"{key}.mp3")
            elif wav_file.exists():
                available.append(f"{key}.wav")
            else:
                missing.append(key)

        total = len(tts_texts)

        if missing:
            print(f"⚠️  누락된 파일: {len(missing)}/{total}개")
            print()
            for key in missing[:20]:  # 최대 20개만 표시
                print(f"   ❌ {key}.mp3 (또는 .wav)")
                print(f"      텍스트: {tts_texts[key][:50]}...")
            if len(missing) > 20:
                print(f"   ... 외 {len(missing) - 20}개")
            print()
            print(f"📁 저장 위치: {audio_dir}")
        else:
            print(f"✅ 모든 파일 준비 완료! ({len(available)}/{total}개)")
            print()
            print('다음 단계: "python math_video_pipeline.py audio-process"')

        print("=" * 60)

        return {"available": available, "missing": missing}

    def process_audio_files(self) -> bool:
        """외부 녹음 파일 처리 (Whisper 분석 + timing.json 생성)

        각 문장별 오디오 파일의 duration을 측정하고
        씬별 timing.json을 생성합니다.

        Returns:
            성공 여부
        """
        project_id = self.state.get("project_id")
        if not project_id:
            print("❌ 활성 프로젝트가 없습니다.")
            return False

        project_dir = OUTPUT_DIR / project_id
        audio_dir = project_dir / "0_audio"
        texts_file = audio_dir / "tts_texts.json"

        if not texts_file.exists():
            print(f"❌ tts_texts.json이 없습니다.")
            print(f"   먼저 'python math_video_pipeline.py tts-export' 실행하세요.")
            return False

        # 누락 파일 확인
        check_result = self.check_audio_files()
        if check_result["missing"]:
            print(f"\n❌ 누락된 파일이 있습니다. 먼저 녹음을 완료하세요.")
            return False

        with open(texts_file, 'r', encoding='utf-8') as f:
            tts_texts = json.load(f)

        print()
        print(f"🎧 오디오 파일 처리 시작")
        print("=" * 60)

        # 씬별로 그룹화
        scene_sentences = {}
        for key, text in tts_texts.items():
            # key: s1_1, s1_2, s2_1 ...
            parts = key.rsplit('_', 1)
            scene_id = parts[0]
            sentence_idx = int(parts[1])

            if scene_id not in scene_sentences:
                scene_sentences[scene_id] = []
            scene_sentences[scene_id].append({
                "key": key,
                "index": sentence_idx,
                "text": text
            })

        # 각 씬별로 처리
        all_audio_files = []

        for scene_id in sorted(scene_sentences.keys(), key=lambda x: int(x[1:]) if x[1:].isdigit() else 0):
            sentences = sorted(scene_sentences[scene_id], key=lambda x: x["index"])

            print(f"\n[{scene_id}] {len(sentences)}개 문장 처리 중...")

            sentence_results = []
            audio_files = []
            current_time = 0.0

            for sent in sentences:
                key = sent["key"]

                # 파일 찾기 (mp3 또는 wav)
                mp3_file = audio_dir / f"{key}.mp3"
                wav_file = audio_dir / f"{key}.wav"

                if mp3_file.exists():
                    audio_file = mp3_file
                    file_ext = "mp3"
                else:
                    audio_file = wav_file
                    file_ext = "wav"

                # duration 측정
                duration = self._get_audio_duration(audio_file)
                gap = 0.1  # 문장 사이 여유 시간

                sentence_results.append({
                    "index": sent["index"],
                    "text": sent["text"],
                    "file": f"{key}.{file_ext}",
                    "start": round(current_time, 3),
                    "end": round(current_time + duration + gap, 3),
                    "duration": round(duration + gap, 3)
                })

                audio_files.append(f"{key}.{file_ext}")
                all_audio_files.append(f"{key}.{file_ext}")
                current_time += duration + gap

                print(f"   {key}: {duration:.2f}초 (+{gap}s gap)")

            # timing.json 저장
            timing_file = audio_dir / f"{scene_id}_timing.json"
            timing_data = {
                "scene_id": scene_id,
                "voice": "external_recording",
                "total_duration": round(current_time, 3),
                "sentence_count": len(sentence_results),
                "sentences": sentence_results,
                "audio_files": audio_files,
                "created_at": datetime.now().isoformat()
            }

            with open(timing_file, 'w', encoding='utf-8') as f:
                json.dump(timing_data, f, ensure_ascii=False, indent=2)

            print(f"   ✅ {timing_file.name} 저장 (총 {current_time:.2f}초)")

        # state 업데이트
        self.state.update_tts_completed(project_id, all_audio_files)

        print()
        print("=" * 60)
        print(f"✅ 오디오 처리 완료!")
        print(f"   📊 {len(scene_sentences)}개 씬, {len(all_audio_files)}개 파일")
        print(f"   📁 timing.json 생성 완료")
        print()
        print("다음 단계: Manim 코드 생성")

        return True

    def _get_audio_duration(self, audio_file: Path) -> float:
        """오디오 파일의 재생 시간 측정 (mp3/wav 지원)"""
        import subprocess

        try:
            # ffprobe 사용
            result = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    str(audio_file)
                ],
                capture_output=True,
                text=True
            )
            return float(result.stdout.strip())
        except:
            pass

        # wav 파일인 경우 wave 모듈 사용
        if audio_file.suffix.lower() == ".wav":
            return self._get_wav_duration(audio_file)

        # mp3 파일인 경우 mutagen 시도
        try:
            from mutagen.mp3 import MP3
            audio = MP3(str(audio_file))
            return audio.info.length
        except:
            pass

        print(f"      ⚠️  duration 측정 실패: {audio_file.name}")
        return 0.0

# ============================================================================
# 파일 관리 클래스
# ============================================================================

class FileManager:
    """파일 저장 및 로드"""
    
    def __init__(self, state_manager: StateManager):
        self.state = state_manager
    
    def get_project_dir(self) -> Optional[Path]:
        """현재 프로젝트 디렉토리"""
        project_id = self.state.get("project_id")
        if project_id:
            return OUTPUT_DIR / project_id
        return None
    
    def save_script(self, script: Dict[str, Any]) -> Optional[Path]:
        """대본 저장"""
        project_dir = self.get_project_dir()
        if not project_dir:
            print("❌ 활성 프로젝트가 없습니다.")
            return None
        
        project_id = self.state.get("project_id")
        script_dir = project_dir / "1_script"
        script_dir.mkdir(parents=True, exist_ok=True)
        
        # JSON 저장
        json_file = script_dir / "reading_script.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(script, f, ensure_ascii=False, indent=2)
        
        # 마크다운 저장
        md_file = script_dir / "reading_script.md"
        md_content = self._script_to_markdown(script)
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        # 상태 업데이트 - 새로운 함수 사용
        self.state.update_script_approved(project_id)
        
        print(f"✅ 대본 저장 완료")
        print(f"   JSON: {json_file}")
        print(f"   Markdown: {md_file}")
        
        return json_file
    
    def _script_to_markdown(self, script: Dict[str, Any]) -> str:
        """대본을 마크다운으로 변환"""
        lines = [
            f"# {script.get('title', '제목 없음')}",
            "",
            "## Hook",
            script.get('hook', ''),
            "",
            "## 분석",
            script.get('analysis', ''),
            "",
            "## 핵심 수학",
            script.get('core_math', ''),
            "",
            "## 적용",
            script.get('application', ''),
            "",
            "## 아웃트로",
            script.get('outro', ''),
            "",
            "---",
            "",
            "## 메타 정보",
        ]
        
        meta = script.get('meta', {})
        for key, value in meta.items():
            lines.append(f"- {key}: {value}")
        
        return "\n".join(lines)
    
    def save_scenes(self, scenes: List[Dict[str, Any]]) -> Optional[Path]:
        """씬 분할 저장"""
        project_dir = self.get_project_dir()
        if not project_dir:
            print("❌ 활성 프로젝트가 없습니다.")
            return None
        
        project_id = self.state.get("project_id")
        scenes_dir = project_dir / "2_scenes"
        scenes_dir.mkdir(parents=True, exist_ok=True)
        
        scenes_file = scenes_dir / "scenes.json"
        
        data = {
            "project_id": project_id,
            "total_scenes": len(scenes),
            "total_duration": sum(s.get("duration", 0) for s in scenes),
            "scenes": scenes,
            "created_at": datetime.now().isoformat()
        }
        
        with open(scenes_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 상태 업데이트 - 새로운 함수 사용
        scene_ids = [s.get("scene_id", f"s{i+1}") for i, s in enumerate(scenes)]
        self.state.update_scenes_approved(project_id, scene_ids)
        
        print(f"✅ 씬 분할 저장 완료")
        print(f"   파일: {scenes_file}")
        print(f"   총 씬: {len(scenes)}개")
        print(f"   총 시간: {data['total_duration']}초")
        
        return scenes_file
    
    def save_manim_code(self, scene_id: str, code: str) -> Optional[Path]:
        """Manim 코드 저장"""
        project_dir = self.get_project_dir()
        if not project_dir:
            print("❌ 활성 프로젝트가 없습니다.")
            return None
        
        code_dir = project_dir / "4_manim_code"
        code_dir.mkdir(parents=True, exist_ok=True)
        
        code_file = code_dir / f"{scene_id}_manim.py"
        
        with open(code_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        # 상태 업데이트 - 새로운 함수 사용
        self.state.update_manim_scene_completed(scene_id, str(code_file))
        
        print(f"✅ Manim 코드 저장: {code_file}")
        
        return code_file
    
    def save_subtitles(self, scene_id: str, subtitles: Dict[str, Any]) -> Optional[Path]:
        """자막 데이터 저장"""
        project_dir = self.get_project_dir()
        if not project_dir:
            return None
        
        subtitles_dir = project_dir / "7_subtitles"
        subtitles_dir.mkdir(parents=True, exist_ok=True)
        
        subtitles_file = subtitles_dir / f"{scene_id}_subtitles.json"
        
        with open(subtitles_file, 'w', encoding='utf-8') as f:
            json.dump(subtitles, f, ensure_ascii=False, indent=2)
        
        self.state.add_file("subtitles", str(subtitles_file))
        
        print(f"✅ 자막 저장: {subtitles_file}")
        
        return subtitles_file
    
    def save_image_prompt(self, scene_id: str, prompt: str) -> Optional[Path]:
        """이미지 프롬프트 저장"""
        project_dir = self.get_project_dir()
        if not project_dir:
            return None
        
        prompts_dir = project_dir / "6_image_prompts"
        prompts_dir.mkdir(parents=True, exist_ok=True)
        
        prompt_file = prompts_dir / f"{scene_id}_background.txt"
        
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt)
        
        print(f"✅ 이미지 프롬프트 저장: {prompt_file}")
        
        return prompt_file
    
    def load_scenes(self) -> Optional[List[Dict[str, Any]]]:
        """씬 데이터 로드"""
        project_dir = self.get_project_dir()
        if not project_dir:
            return None
        
        scenes_file = project_dir / "2_scenes" / "scenes.json"
        
        if not scenes_file.exists():
            return None
        
        with open(scenes_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data.get("scenes", [])
    
    def load_timing(self, scene_id: str) -> Optional[Dict[str, Any]]:
        """타이밍 데이터 로드"""
        project_dir = self.get_project_dir()
        if not project_dir:
            return None
        
        timing_file = project_dir / "0_audio" / f"{scene_id}_timing.json"
        
        if not timing_file.exists():
            return None
        
        with open(timing_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def list_files(self) -> Dict[str, List[str]]:
        """프로젝트 파일 목록"""
        project_dir = self.get_project_dir()
        if not project_dir:
            return {}
        
        files = {}
        
        for folder in project_dir.iterdir():
            if folder.is_dir():
                files[folder.name] = [f.name for f in folder.iterdir() if f.is_file()]
        
        return files


# ============================================================================
# Supabase 클라이언트
# ============================================================================

def get_supabase_client() -> Optional['SupabaseClient']:
    """Supabase 클라이언트 생성 (Service Role Key 사용)"""
    if not SUPABASE_AVAILABLE:
        return None

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")

    if not url or not key:
        # .env 파일에서 로드 시도
        env_file = Path(".env")
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("SUPABASE_URL="):
                        url = line.split("=", 1)[1].strip().strip('"\'')
                    elif line.startswith("SUPABASE_SERVICE_KEY="):
                        key = line.split("=", 1)[1].strip().strip('"\'')

    if not url or not key:
        print("❌ SUPABASE_URL 또는 SUPABASE_SERVICE_KEY가 설정되지 않았습니다.")
        return None

    return create_client(url, key)


# ============================================================================
# 에셋 관리 클래스 (Supabase 연동)
# ============================================================================

class AssetManager:
    """에셋 관리 (Supabase Storage + DB 연동)"""

    BUCKET_NAME = "math-video-assets"
    ASSETS_DIR = Path("assets")

    def __init__(self, state_manager: StateManager):
        self.state = state_manager
        self.supabase = get_supabase_client()

    def get_project_dir(self) -> Optional[Path]:
        """현재 프로젝트 디렉토리"""
        project_id = self.state.get("project_id")
        if project_id:
            return OUTPUT_DIR / project_id
        return None

    def check_assets(self) -> dict:
        """
        에셋 체크: Supabase 조회 + 다운로드 + 누락 목록 생성 + scenes.json 확장자 업데이트

        Returns:
            {"available": [...], "missing": [...], "downloaded": [...]}
        """
        project_dir = self.get_project_dir()
        if not project_dir:
            print("❌ 활성 프로젝트가 없습니다.")
            return {"available": [], "missing": [], "downloaded": []}

        scenes_file = project_dir / "2_scenes" / "scenes.json"
        if not scenes_file.exists():
            print("❌ 씬 파일이 없습니다. 먼저 씬 분할을 진행하세요.")
            return {"available": [], "missing": [], "downloaded": []}

        # 1. scenes.json에서 required_elements 수집
        with open(scenes_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        scenes = data if isinstance(data, list) else data.get("scenes", [])

        required_assets = {}  # file_path -> {scenes, description, tags, original_name}
        for scene in scenes:
            scene_id = scene.get("scene_id", "unknown")

            # 1. required_elements에서 추출
            elements = scene.get("required_elements", [])
            for elem in elements:
                if isinstance(elem, str) and "/" in elem:
                    # 이미 경로 형식
                    base_name = elem.rsplit(".", 1)[0] if "." in elem else elem
                    if base_name not in required_assets:
                        required_assets[base_name] = {"scenes": [], "description": "", "tags": [], "original_name": elem}
                    required_assets[base_name]["scenes"].append(scene_id)
                elif isinstance(elem, dict) and elem.get("type") in ["image", "icon"]:
                    # {"type": "image"/"icon", "asset": "snack_bag" 또는 "snack_bag.png", "role": "..."} 형식
                    asset_name = elem.get("asset", elem.get("file", elem.get("path", "")))
                    elem_type = elem.get("type")
                    if asset_name:
                        # 확장자 제거
                        base_name = asset_name.rsplit(".", 1)[0] if "." in asset_name else asset_name

                        # 카테고리 결정: type이 icon이면 icons/, 아니면 기존 로직
                        if elem_type == "icon":
                            file_path = f"icons/{base_name}"
                        elif "stickman" in base_name or "pigou" in base_name:
                            file_path = f"characters/{base_name}"
                        elif "_icon" in base_name or base_name in ["question_mark", "exclamation", "lightbulb", "checkmark", "arrow_right", "star", "heart", "clock", "calendar", "battery_low", "server_icon", "algorithm_icon", "amazon_logo", "dollar_sign"]:
                            file_path = f"icons/{base_name}"
                        else:
                            file_path = f"objects/{base_name}"

                        if file_path not in required_assets:
                            required_assets[file_path] = {
                                "scenes": [],
                                "description": elem.get("role", elem.get("description", "")),
                                "tags": [],
                                "original_name": asset_name
                            }
                        required_assets[file_path]["scenes"].append(scene_id)

            # 2. required_assets에서도 추출 (별도 필드)
            assets_list = scene.get("required_assets", [])
            for asset in assets_list:
                if isinstance(asset, dict):
                    category = asset.get("category", "objects")
                    filename = asset.get("filename", "")
                    if filename:
                        # 확장자 제거
                        base_name = filename.rsplit(".", 1)[0] if "." in filename else filename
                        file_path = f"{category}/{base_name}"
                        if file_path not in required_assets:
                            required_assets[file_path] = {
                                "scenes": [],
                                "description": asset.get("description", ""),
                                "tags": [category, base_name],
                                "original_name": filename
                            }
                        if scene_id not in required_assets[file_path]["scenes"]:
                            required_assets[file_path]["scenes"].append(scene_id)

        print(f"\n📋 필요한 에셋: {len(required_assets)}개")

        # 2. 실제 파일 확장자 찾기 (로컬에서 .png 또는 .svg 탐색)
        resolved_assets = {}  # base_path -> actual_path (with extension)
        for base_path in required_assets.keys():
            # 로컬에서 .png, .svg 순서로 찾기
            for ext in [".png", ".svg"]:
                local_path = self.ASSETS_DIR / f"{base_path}{ext}"
                if local_path.exists():
                    resolved_assets[base_path] = f"{base_path}{ext}"
                    break
            # 없으면 일단 .png로 가정 (누락 목록에 추가됨)
            if base_path not in resolved_assets:
                resolved_assets[base_path] = f"{base_path}.png"

        if not self.supabase:
            print("❌ Supabase 연결 실패. 로컬 파일만 확인합니다.")
            result = self._check_local_only(required_assets, resolved_assets)
            # scenes.json 업데이트
            self._update_scenes_with_extensions(scenes_file, scenes, resolved_assets)
            return result

        # 3. Supabase에서 보유 목록 조회
        try:
            result = self.supabase.table("assets").select("file_path, folder, file_name, description, tags").execute()
            supabase_assets = {item["file_path"]: item for item in result.data}
            print(f"☁️  Supabase 보유: {len(supabase_assets)}개")

            # Supabase에서도 확장자 찾기
            for base_path in required_assets.keys():
                if base_path not in resolved_assets or not (self.ASSETS_DIR / resolved_assets[base_path]).exists():
                    for ext in [".png", ".svg"]:
                        full_path = f"{base_path}{ext}"
                        if full_path in supabase_assets:
                            resolved_assets[base_path] = full_path
                            break
        except Exception as e:
            print(f"⚠️  Supabase 조회 오류: {e}")
            supabase_assets = {}

        available = []
        missing = []
        downloaded = []

        # 4. 각 에셋 확인 (확장자 포함된 경로로)
        for base_path, info in required_assets.items():
            file_path = resolved_assets.get(base_path, f"{base_path}.png")
            local_path = self.ASSETS_DIR / file_path

            if file_path in supabase_assets:
                # Supabase에 있음
                if local_path.exists():
                    # 로컬에도 있음
                    available.append(file_path)
                else:
                    # 로컬에 없음 → 다운로드
                    if self._download_asset(file_path):
                        downloaded.append(file_path)
                        available.append(file_path)
                    else:
                        missing.append({
                            "file_path": file_path,
                            "base_path": base_path,
                            "folder": file_path.rsplit("/", 1)[0] if "/" in file_path else "",
                            "file_name": file_path.rsplit("/", 1)[-1],
                            "description": supabase_assets[file_path].get("description", ""),
                            "tags": supabase_assets[file_path].get("tags", []),
                            "used_in_scenes": info["scenes"],
                            "spec": {"min_size": "500x500", "format": "PNG or SVG", "background": "transparent"}
                        })
            else:
                # Supabase에 없음
                if local_path.exists():
                    # 로컬에만 있음 (업로드 필요)
                    available.append(file_path)
                else:
                    # 어디에도 없음
                    missing.append({
                        "file_path": file_path,
                        "base_path": base_path,
                        "folder": file_path.rsplit("/", 1)[0] if "/" in file_path else "",
                        "file_name": file_path.rsplit("/", 1)[-1],
                        "description": info.get("description", f"에셋: {file_path}"),
                        "tags": info.get("tags", [file_path.split("/")[0], base_path.rsplit("/", 1)[-1]]),
                        "used_in_scenes": info["scenes"],
                        "spec": {"min_size": "500x500", "format": "PNG or SVG", "background": "transparent"}
                    })

        # 5. 결과 출력
        print(f"\n✅ 사용 가능: {len(available)}개")
        if downloaded:
            print(f"⬇️  다운로드됨: {len(downloaded)}개")
            for fp in downloaded:
                print(f"   - {fp}")

        if missing:
            print(f"❌ 누락: {len(missing)}개")
            for m in missing:
                print(f"   - {m['file_path']} (씬: {', '.join(m['used_in_scenes'])})")

            # missing_assets.json 저장
            missing_file = project_dir / "missing_assets.json"
            with open(missing_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "missing": missing,
                    "generated_at": datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
            print(f"\n📄 누락 목록 저장: {missing_file}")
        else:
            print("\n🎉 모든 에셋 준비 완료!")
            # state.json 업데이트
            self.state.set("assets.required", [resolved_assets[k] for k in required_assets.keys()])
            self.state.set("assets.available", available)
            self.state.set("assets.missing", [])
            self.state.update_phase("assets_checked")

        # 6. scenes.json 업데이트 (확장자 반영)
        self._update_scenes_with_extensions(scenes_file, scenes, resolved_assets)

        return {"available": available, "missing": missing, "downloaded": downloaded}

    def _update_scenes_with_extensions(self, scenes_file: Path, scenes: list, resolved_assets: dict) -> bool:
        """scenes.json에 실제 파일 확장자를 반영"""
        updated = False

        for scene in scenes:
            # 1. required_elements 업데이트
            elements = scene.get("required_elements", [])
            for elem in elements:
                if isinstance(elem, dict) and elem.get("type") == "image":
                    asset_name = elem.get("asset", "")
                    if asset_name:
                        base_name = asset_name.rsplit(".", 1)[0] if "." in asset_name else asset_name

                        # 카테고리 추측
                        if "stickman" in base_name or "pigou" in base_name:
                            base_path = f"characters/{base_name}"
                        elif "_icon" in base_name or base_name in ["question_mark", "exclamation", "lightbulb", "checkmark", "arrow_right", "star", "heart", "clock", "calendar", "battery_low", "server_icon", "algorithm_icon", "amazon_logo", "dollar_sign"]:
                            base_path = f"icons/{base_name}"
                        else:
                            base_path = f"objects/{base_name}"

                        if base_path in resolved_assets:
                            new_name = resolved_assets[base_path].rsplit("/", 1)[-1]  # 파일명만
                            if asset_name != new_name:
                                elem["asset"] = new_name
                                updated = True

            # 2. required_assets 업데이트
            assets_list = scene.get("required_assets", [])
            for asset in assets_list:
                if isinstance(asset, dict):
                    category = asset.get("category", "objects")
                    filename = asset.get("filename", "")
                    if filename:
                        base_name = filename.rsplit(".", 1)[0] if "." in filename else filename
                        base_path = f"{category}/{base_name}"

                        if base_path in resolved_assets:
                            new_filename = resolved_assets[base_path].rsplit("/", 1)[-1]
                            if filename != new_filename:
                                asset["filename"] = new_filename
                                updated = True

        if updated:
            with open(scenes_file, 'w', encoding='utf-8') as f:
                json.dump(scenes, f, ensure_ascii=False, indent=2)
            print(f"\n📝 scenes.json 업데이트됨 (확장자 반영)")

        return updated

    def _check_local_only(self, required_assets: dict, resolved_assets: dict) -> dict:
        """로컬 파일만 확인 (Supabase 없을 때)

        Args:
            required_assets: 필요한 에셋 (확장자 없는 경로 -> info)
            resolved_assets: 실제 파일 경로 (확장자 없는 경로 -> 확장자 있는 경로)
        """
        available = []
        missing = []

        for base_path, info in required_assets.items():
            # resolved_assets에서 실제 파일 경로 확인
            if base_path in resolved_assets:
                actual_path = resolved_assets[base_path]
                available.append(actual_path)
            else:
                # 누락된 에셋
                category = base_path.rsplit("/", 1)[0] if "/" in base_path else ""
                is_icon = category == "icons"
                missing.append({
                    "file_path": base_path,  # 확장자 없는 경로
                    "folder": category,
                    "file_name": base_path.rsplit("/", 1)[-1],
                    "description": info.get("description", f"에셋: {base_path}"),
                    "tags": info.get("tags", []),
                    "used_in_scenes": info["scenes"],
                    "spec": {
                        "min_size": "300x300" if is_icon else "500x500",
                        "format": "SVG (권장) 또는 PNG" if is_icon else "PNG",
                        "background": "transparent"
                    }
                })

        print(f"✅ 로컬 존재: {len(available)}개")
        print(f"❌ 누락: {len(missing)}개")

        return {"available": available, "missing": missing, "downloaded": []}

    def _download_asset(self, file_path: str) -> bool:
        """Supabase Storage에서 에셋 다운로드"""
        try:
            local_path = self.ASSETS_DIR / file_path
            local_path.parent.mkdir(parents=True, exist_ok=True)

            data = self.supabase.storage.from_(self.BUCKET_NAME).download(file_path)

            with open(local_path, 'wb') as f:
                f.write(data)

            return True
        except Exception as e:
            print(f"   ⚠️  다운로드 실패 ({file_path}): {e}")
            return False

    def sync_assets(self) -> dict:
        """
        에셋 동기화: 로컬 신규 파일 → Supabase 업로드
        missing_assets.json 참조하여 메타데이터 적용

        Returns:
            {"uploaded": [...], "failed": [...]}
        """
        project_dir = self.get_project_dir()
        if not project_dir:
            print("❌ 활성 프로젝트가 없습니다.")
            return {"uploaded": [], "failed": []}

        if not self.supabase:
            print("❌ Supabase 연결 실패.")
            return {"uploaded": [], "failed": []}

        # missing_assets.json 로드
        missing_file = project_dir / "missing_assets.json"
        missing_metadata = {}
        if missing_file.exists():
            with open(missing_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data.get("missing", []):
                    missing_metadata[item["file_path"]] = item

        # Supabase 보유 목록 조회
        try:
            result = self.supabase.table("assets").select("file_path").execute()
            supabase_paths = {item["file_path"] for item in result.data}
        except Exception as e:
            print(f"⚠️  Supabase 조회 오류: {e}")
            supabase_paths = set()

        uploaded = []
        failed = []

        # 로컬 assets 폴더 스캔 (PNG + SVG)
        asset_files = list(self.ASSETS_DIR.rglob("*.png")) + list(self.ASSETS_DIR.rglob("*.svg"))

        for asset_file in asset_files:
            rel_path = asset_file.relative_to(self.ASSETS_DIR).as_posix()

            if rel_path in supabase_paths:
                continue  # 이미 업로드됨

            print(f"\n📤 업로드 중: {rel_path}")

            # 메타데이터 준비
            metadata = missing_metadata.get(rel_path, {})
            folder = rel_path.rsplit("/", 1)[0] if "/" in rel_path else ""
            file_name = rel_path.rsplit("/", 1)[-1]

            if self._upload_asset(asset_file, rel_path, folder, file_name, metadata):
                uploaded.append(rel_path)
            else:
                failed.append(rel_path)

        print(f"\n{'='*50}")
        print(f"✅ 업로드 완료: {len(uploaded)}개")
        if failed:
            print(f"❌ 실패: {len(failed)}개")
            for fp in failed:
                print(f"   - {fp}")

        # 업로드 후 다시 체크
        if uploaded:
            print("\n🔄 에셋 상태 재확인 중...")
            self.check_assets()

        # 카탈로그 업데이트
        self.update_catalog()

        return {"uploaded": uploaded, "failed": failed}

    def update_catalog(self) -> bool:
        """
        Supabase에서 전체 에셋 목록을 가져와서 asset-catalog.md 자동 생성
        """
        if not self.supabase:
            print("⚠️  Supabase 연결 없음. 카탈로그 업데이트 생략.")
            return False

        try:
            result = self.supabase.table("assets").select("*").execute()
            assets = result.data
        except Exception as e:
            print(f"⚠️  Supabase 조회 오류: {e}")
            return False

        if not assets:
            print("⚠️  Supabase에 에셋이 없습니다.")
            return False

        # 카테고리별 분류
        categories = {
            "characters": [],
            "objects": [],
            "icons": [],
            "metaphors": []
        }

        for asset in assets:
            folder = asset.get("folder", "objects")
            if folder not in categories:
                folder = "objects"
            categories[folder].append(asset)

        # Markdown 생성
        catalog_path = Path("skills/asset-catalog.md")

        lines = [
            "# 에셋 카탈로그",
            "",
            "> 이 파일은 `asset-sync` 실행 시 Supabase에서 자동 생성됩니다.",
            "> 수동으로 수정하지 마세요.",
            "",
            f"**마지막 업데이트**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**총 에셋 수**: {len(assets)}개",
            "",
            "---",
            "",
        ]

        # 카테고리별 테이블 생성
        category_info = {
            "characters": ("캐릭터", "characters/"),
            "objects": ("물체", "objects/"),
            "icons": ("아이콘", "icons/"),
            "metaphors": ("은유/비유", "metaphors/")
        }

        for cat_key, (cat_name, cat_path) in category_info.items():
            cat_assets = categories.get(cat_key, [])
            if not cat_assets:
                continue

            lines.append(f"## {cat_name} ({cat_path})")
            lines.append("")
            lines.append("| 파일명 | 설명 | 크기 | 태그 |")
            lines.append("|--------|------|------|------|")

            for asset in sorted(cat_assets, key=lambda x: x.get("file_name", "")):
                file_name = asset.get("file_name", "unknown")
                description = asset.get("description", "")[:50]  # 50자 제한
                width = asset.get("width", "?")
                height = asset.get("height", "?")
                size_str = f"{width}x{height}" if width and height else "?"
                tags = asset.get("tags", [])
                # tags가 중첩 리스트일 경우 flatten
                if tags and isinstance(tags[0], list):
                    tags = [item for sublist in tags for item in sublist]
                # 문자열만 필터링
                tags = [t for t in tags if isinstance(t, str)]
                tags_str = ", ".join(tags[:3]) if tags else ""  # 태그 3개까지

                lines.append(f"| `{file_name}` | {description} | {size_str} | {tags_str} |")

            lines.append("")

        # 파일 사양 섹션
        lines.extend([
            "---",
            "",
            "## 에셋 파일 사양",
            "",
            "| 카테고리 | 권장 크기 | 스타일 |",
            "|----------|-----------|--------|",
            "| characters | 500x700 px | 졸라맨 stick figure |",
            "| objects | 500x500 px | minimalist 2D |",
            "| icons | 300x300 px | minimalist 2D |",
            "| metaphors | 700x500 px | minimalist 2D |",
            "",
            "**공통 사양**:",
            "- 포맷: PNG (투명 배경)",
            "- 생성 시 흰색 배경으로 생성 후 배경 제거",
            "- 내부는 반드시 solid color로 채우기",
            "",
        ])

        # 파일 저장
        catalog_path.parent.mkdir(parents=True, exist_ok=True)
        with open(catalog_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

        print(f"\n📋 카탈로그 업데이트: {catalog_path}")
        print(f"   - 총 {len(assets)}개 에셋 등록")

        return True

    def _upload_asset(self, local_path: Path, storage_path: str, folder: str, file_name: str, metadata: dict) -> bool:
        """단일 에셋 업로드 (Storage + DB)"""
        try:
            # 파일 확장자 확인
            is_svg = file_name.lower().endswith(".svg")
            content_type = "image/svg+xml" if is_svg else "image/png"

            # 1. Storage 업로드
            with open(local_path, 'rb') as f:
                file_data = f.read()

            try:
                self.supabase.storage.from_(self.BUCKET_NAME).upload(
                    path=storage_path,
                    file=file_data,
                    file_options={"content-type": content_type}
                )
                print(f"   [STORAGE] OK")
            except Exception as e:
                if "Duplicate" in str(e) or "already exists" in str(e):
                    print(f"   [STORAGE] Already exists")
                else:
                    raise e

            # 2. 이미지 정보
            width, height, file_size = None, None, local_path.stat().st_size

            if is_svg:
                # SVG 파일은 viewBox에서 크기 추출 시도
                try:
                    import re
                    svg_content = local_path.read_text(encoding='utf-8')
                    # viewBox="0 0 300 300" 또는 width="300" height="300" 추출
                    viewbox_match = re.search(r'viewBox="[^"]*\s+(\d+)\s+(\d+)"', svg_content)
                    if viewbox_match:
                        width, height = int(viewbox_match.group(1)), int(viewbox_match.group(2))
                    else:
                        width_match = re.search(r'width="(\d+)"', svg_content)
                        height_match = re.search(r'height="(\d+)"', svg_content)
                        if width_match and height_match:
                            width, height = int(width_match.group(1)), int(height_match.group(1))
                except:
                    pass
            elif PIL_AVAILABLE:
                try:
                    with Image.open(local_path) as img:
                        width, height = img.size
                except:
                    pass

            # 3. DB 저장
            # 확장자 제거 (태그용)
            base_name = file_name.rsplit(".", 1)[0] if "." in file_name else file_name

            db_data = {
                "file_name": file_name,
                "folder": folder,
                "storage_path": storage_path,
                "description": metadata.get("description", f"{folder} asset: {file_name}"),
                "tags": metadata.get("tags", [folder, base_name]),
                "width": width,
                "height": height,
                "file_size": file_size,
            }

            self.supabase.table("assets").upsert(
                db_data,
                on_conflict="folder,file_name"
            ).execute()
            print(f"   [DB] OK")

            return True
        except Exception as e:
            print(f"   [ERROR] {e}")
            return False


# ============================================================================
# 이미지 관리 클래스
# ============================================================================

class ImageManager:
    """배경 이미지 프롬프트 및 파일 관리"""
    
    def __init__(self, state_manager: StateManager):
        self.state = state_manager
    
    def get_project_dir(self) -> Optional[Path]:
        """현재 프로젝트 디렉토리"""
        project_id = self.state.get("project_id")
        if project_id:
            return OUTPUT_DIR / project_id
        return None
    
    def export_prompts(self) -> Optional[Path]:
        """모든 이미지 프롬프트를 하나의 파일로 내보내기"""
        project_dir = self.get_project_dir()
        if not project_dir:
            print("❌ 활성 프로젝트가 없습니다.")
            return None
        
        prompts_dir = project_dir / "6_image_prompts"
        scenes_file = project_dir / "2_scenes" / "scenes.json"
        
        if not scenes_file.exists():
            print("❌ 씬 파일이 없습니다. 먼저 씬 분할을 진행하세요.")
            return None
        
        # 씬 정보 로드
        with open(scenes_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        scenes = data if isinstance(data, list) else data.get("scenes", [])
        if not scenes:
            print("❌ 씬이 없습니다.")
            return None
        
        # 스타일 정보
        style = self.state.get("settings.style", "cyberpunk")
        aspect_ratio = self.state.get("settings.aspect_ratio", "16:9")
        
        # 배치 파일 생성
        batch_file = prompts_dir / "prompts_batch.txt"
        prompts_dir.mkdir(parents=True, exist_ok=True)
        
        lines = [
            "=" * 70,
            f"프로젝트: {self.state.get('project_id')}",
            f"제목: {self.state.get('title')}",
            f"스타일: {style}",
            f"종횡비: {aspect_ratio}",
            f"총 씬: {len(scenes)}개",
            "=" * 70,
            "",
            "📌 사용법:",
            "1. 각 프롬프트를 복사하여 이미지 생성 AI에 입력",
            "2. 생성된 이미지를 다운로드",
            f"3. 파일명을 s1_bg.png, s2_bg.png, ... 형식으로 변경",
            f"4. 9_backgrounds/ 폴더에 저장",
            "5. python math_video_pipeline.py images-check 로 검증",
            "",
            "=" * 70,
            ""
        ]
        
        # 각 씬별 프롬프트 생성
        for i, scene in enumerate(scenes):
            scene_id = scene.get("scene_id", f"s{i+1}")
            section = scene.get("section", "")
            duration = scene.get("duration", 0)
            visual_concept = scene.get("visual_concept", "")
            
            # 개별 프롬프트 파일도 저장
            prompt = self._generate_prompt(style, aspect_ratio, visual_concept, section)
            
            prompt_file = prompts_dir / f"{scene_id}_background.txt"
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(prompt)
            
            # 배치 파일에 추가
            lines.append(f"=== Scene {scene_id} ({section}) ===")
            lines.append(f"[Duration: {duration}초]")
            lines.append(f"[Visual: {visual_concept[:50]}...]" if len(visual_concept) > 50 else f"[Visual: {visual_concept}]")
            lines.append("")
            lines.append(prompt)
            lines.append("")
            lines.append("-" * 70)
            lines.append("")
        
        # 배치 파일 저장
        with open(batch_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        
        print(f"✅ 프롬프트 내보내기 완료")
        print(f"   📄 배치 파일: {batch_file}")
        print(f"   📁 개별 파일: {prompts_dir}/")
        print(f"   🎬 총 {len(scenes)}개 프롬프트 생성")
        
        return batch_file
    
    def _generate_prompt(self, style: str, aspect_ratio: str, visual_concept: str, section: str) -> str:
        """스타일별 이미지 프롬프트 생성 - 장식 요소는 희미한 회색으로 통일"""

        # 스타일별 기본 프롬프트 (바탕색 유지, 장식은 faint gray)
        style_prompts = {
            "minimal": {
                "base": "minimalist mathematical background, clean dark gradient",
                "tint": "soft muted blue undertones",
                "decoration": "very faint gray geometric patterns, barely visible grid lines, subtle ghost-like shapes at 15% opacity",
            },
            "cyberpunk": {
                "base": "cyberpunk mathematical background, very dark futuristic scene, near-black base",
                "tint": "subtle purple tint",
                "decoration": "faint gray digital grid barely visible, ghost-like circuit patterns in light gray, very subtle gray holographic rectangles at 15% opacity, all decorative elements in muted gray",
            },
            "paper": {
                "base": "paper texture background, warm beige to cream gradient, subtle paper grain texture",
                "tint": "",
                "decoration": "faint gray digital grid barely visible, ghost-like circuit patterns in light gray, very subtle gray holographic rectangles at 15% opacity, faint gray futuristic UI elements, barely visible tech lines and connection nodes, very faint gray mathematical formulas scattered in background like integral signs and sigma notation and partial derivatives and matrix brackets and limit expressions, all decorative elements in muted gray #BBBBBB to #CCCCCC",
            },
            "space": {
                "base": "space background, deep dark space scene, near-black",
                "tint": "subtle purple tint",
                "decoration": "very faint gray stars barely visible, ghost-like nebula hints in muted gray, subtle gray cosmic dust at 10% opacity, no bright stars, no colorful nebula",
            },
            "geometric": {
                "base": "geometric pattern background, dark gradient base",
                "tint": "subtle blue tint",
                "decoration": "very faint gray geometric shapes, barely visible symmetrical patterns, ghost-like mathematical lines in light gray, all patterns at 15% opacity",
            },
            "stickman": {
                "base": "educational background, soft dark gradient",
                "tint": "subtle teal tint",
                "decoration": "very faint gray playful shapes, barely visible doodle patterns, ghost-like circles and squares in light gray, friendly but subtle decorative elements",
            }
        }

        config = style_prompts.get(style, style_prompts["cyberpunk"])

        # 종횡비 텍스트
        ratio_text = "16:9 widescreen horizontal" if aspect_ratio == "16:9" else "9:16 vertical portrait mobile"

        # 틴트가 있으면 추가
        tint_text = f", {config['tint']}" if config['tint'] else ""

        prompt = f"""{config['base']}{tint_text},
{config['decoration']},
no neon colors, no bright accents, no glowing elements,
mathematical education video background,
no text, no letters, no numbers, no Korean, no equations,
{ratio_text} ratio,
high contrast for text overlay, professional education aesthetic,
8K quality, sharp details

Negative prompt: text, letters, numbers, words, Korean, Chinese, Japanese, equations, formulas, mathematical symbols, writing, watermark, logo, signature, blurry, low quality, pixelated, faces, people, hands, neon colors, bright accents, glowing elements, vibrant colors, saturated colors, high contrast patterns"""

        return prompt
    
    def check_images(self) -> Dict[str, Any]:
        """배경 이미지 준비 상태 확인"""
        project_dir = self.get_project_dir()
        if not project_dir:
            print("❌ 활성 프로젝트가 없습니다.")
            return {"status": "error", "message": "No active project"}
        
        scenes_file = project_dir / "2_scenes" / "scenes.json"
        backgrounds_dir = project_dir / "9_backgrounds"
        
        if not scenes_file.exists():
            print("❌ 씬 파일이 없습니다.")
            return {"status": "error", "message": "No scenes file"}
        
        # 씬 정보 로드
        with open(scenes_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        scenes = data if isinstance(data, list) else data.get("scenes", [])
        scene_ids = [s.get("scene_id", f"s{i+1}") for i, s in enumerate(scenes)]
        
        # 이미지 확인
        found = []
        missing = []
        
        for scene_id in scene_ids:
            # 여러 확장자 확인
            image_found = False
            for ext in [".png", ".jpg", ".jpeg", ".webp"]:
                image_file = backgrounds_dir / f"{scene_id}_bg{ext}"
                if image_file.exists():
                    found.append(str(image_file.name))
                    image_found = True
                    break
            
            if not image_found:
                missing.append(f"{scene_id}_bg.png")
        
        # 결과 출력
        print("\n" + "=" * 60)
        print("🖼️  배경 이미지 상태 확인")
        print("=" * 60)
        print(f"📁 폴더: {backgrounds_dir}")
        print(f"🎬 총 씬: {len(scene_ids)}개")
        print(f"✅ 준비됨: {len(found)}개")
        print(f"❌ 누락: {len(missing)}개")
        print()
        
        if found:
            print("✅ 준비된 이미지:")
            for f in found:
                print(f"   - {f}")
            print()
        
        if missing:
            print("❌ 누락된 이미지:")
            for m in missing:
                print(f"   - {m}")
            print()
            print("📌 이미지를 생성하려면:")
            print("   1. python math_video_pipeline.py prompts-export")
            print("   2. 프롬프트로 이미지 생성 (Midjourney, DALL-E 등)")
            print(f"   3. {backgrounds_dir}/ 에 저장")
        else:
            print("🎉 모든 이미지가 준비되었습니다!")
        
        print("=" * 60)
        
        return {
            "status": "complete" if not missing else "incomplete",
            "total": len(scene_ids),
            "found": found,
            "missing": missing
        }
    
    def import_images(self, source_dir: str) -> Dict[str, Any]:
        """외부 폴더에서 이미지 일괄 가져오기"""
        project_dir = self.get_project_dir()
        if not project_dir:
            print("❌ 활성 프로젝트가 없습니다.")
            return {"status": "error", "imported": 0}
        
        source_path = Path(source_dir)
        if not source_path.exists():
            print(f"❌ 소스 폴더가 존재하지 않습니다: {source_dir}")
            return {"status": "error", "imported": 0}
        
        backgrounds_dir = project_dir / "9_backgrounds"
        backgrounds_dir.mkdir(parents=True, exist_ok=True)
        
        scenes_file = project_dir / "2_scenes" / "scenes.json"
        if not scenes_file.exists():
            print("❌ 씬 파일이 없습니다.")
            return {"status": "error", "imported": 0}
        
        # 씬 정보 로드
        with open(scenes_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        scenes = data if isinstance(data, list) else data.get("scenes", [])
        scene_ids = [s.get("scene_id", f"s{i+1}") for i, s in enumerate(scenes)]
        
        # 소스 폴더의 이미지 파일들
        image_extensions = {".png", ".jpg", ".jpeg", ".webp"}
        source_images = sorted([
            f for f in source_path.iterdir() 
            if f.is_file() and f.suffix.lower() in image_extensions
        ])
        
        if not source_images:
            print(f"❌ 소스 폴더에 이미지가 없습니다: {source_dir}")
            return {"status": "error", "imported": 0}
        
        print(f"\n🖼️  이미지 가져오기")
        print(f"   소스: {source_dir}")
        print(f"   대상: {backgrounds_dir}")
        print(f"   발견된 이미지: {len(source_images)}개")
        print(f"   필요한 씬: {len(scene_ids)}개")
        print()
        
        imported = []
        
        # 방법 1: 파일명에 씬 ID가 포함된 경우
        for scene_id in scene_ids:
            for img in source_images:
                if scene_id in img.stem.lower():
                    dest = backgrounds_dir / f"{scene_id}_bg{img.suffix}"
                    if not dest.exists():
                        import shutil
                        shutil.copy2(img, dest)
                        imported.append(f"{img.name} → {dest.name}")
                        print(f"   ✅ {img.name} → {dest.name}")
                    break
        
        # 방법 2: 순서대로 매칭 (아직 매칭 안 된 것들)
        remaining_scenes = [s for s in scene_ids if not (backgrounds_dir / f"{s}_bg.png").exists() 
                          and not (backgrounds_dir / f"{s}_bg.jpg").exists()
                          and not (backgrounds_dir / f"{s}_bg.jpeg").exists()
                          and not (backgrounds_dir / f"{s}_bg.webp").exists()]
        
        remaining_images = [img for img in source_images 
                          if not any(img.name in i for i in imported)]
        
        for scene_id, img in zip(remaining_scenes, remaining_images):
            dest = backgrounds_dir / f"{scene_id}_bg{img.suffix}"
            import shutil
            shutil.copy2(img, dest)
            imported.append(f"{img.name} → {dest.name}")
            print(f"   ✅ {img.name} → {dest.name} (순서 매칭)")
        
        print()
        print(f"✅ 총 {len(imported)}개 이미지 가져오기 완료")
        
        # 검증 실행
        print()
        self.check_images()
        
        return {
            "status": "success",
            "imported": len(imported),
            "files": imported
        }


# ============================================================================
# 렌더링 관리 클래스
# ============================================================================

class RenderManager:
    """Manim 렌더링 관리"""
    
    def __init__(self, state_manager: StateManager):
        self.state = state_manager
    
    def render_scene(
        self,
        scene_id: str,
        quality: str = "l",  # l=low, m=medium, h=high, k=4k
        preview: bool = True
    ) -> bool:
        """단일 씬 렌더링"""
        
        project_dir = OUTPUT_DIR / self.state.get("project_id", "unknown")
        code_file = project_dir / "4_manim_code" / f"{scene_id}_manim.py"
        
        if not code_file.exists():
            print(f"❌ 코드 파일이 없습니다: {code_file}")
            return False
        
        # 클래스 이름 추출 (scene_id를 PascalCase로)
        class_name = scene_id.capitalize()
        
        # Manim 명령어 구성
        cmd = ["manim"]

        if preview:
            cmd.append("-p")

        cmd.append(f"-q{quality}")
        cmd.append("--transparent")  # 투명 배경 (배경 이미지 합성용)
        cmd.append(str(code_file))
        cmd.append(class_name)
        
        print(f"\n🎬 렌더링: {scene_id}")
        print(f"   명령어: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"   ✅ 렌더링 성공")
                return True
            else:
                print(f"   ❌ 렌더링 실패")
                print(f"   오류: {result.stderr}")
                return False
                
        except FileNotFoundError:
            print("   ❌ Manim이 설치되지 않았습니다.")
            print("   설치: pip install manim")
            return False
        except Exception as e:
            print(f"   ❌ 렌더링 오류: {e}")
            return False
    
    def render_all(
        self,
        quality: str = "l",
        preview: bool = False
    ) -> Dict[str, bool]:
        """모든 씬 렌더링"""
        
        # 렌더링 시작 상태 업데이트
        self.state.update_rendering()
        
        project_dir = OUTPUT_DIR / self.state.get("project_id", "unknown")
        code_dir = project_dir / "4_manim_code"
        
        if not code_dir.exists():
            print(f"❌ 코드 폴더가 없습니다: {code_dir}")
            return {}
        
        # 모든 Manim 파일 찾기
        code_files = list(code_dir.glob("*_manim.py"))
        
        if not code_files:
            print("❌ Manim 코드 파일이 없습니다.")
            return {}
        
        print(f"\n🎬 총 {len(code_files)}개 씬 렌더링 시작")
        print("="*60)
        
        results = {}
        
        for code_file in sorted(code_files):
            scene_id = code_file.stem.replace("_manim", "")
            success = self.render_scene(scene_id, quality, preview)
            results[scene_id] = success
        
        print("\n" + "="*60)
        success_count = sum(1 for v in results.values() if v)
        print(f"✅ 렌더링 완료: {success_count}/{len(results)}개 성공")

        # 렌더링 성공한 것이 있으면 결과물 자동 수집
        if success_count > 0:
            print("\n📦 렌더링 결과물 자동 수집 중...")
            self.collect_renders()

        return results

    def collect_renders(self) -> Dict[str, str]:
        """media/videos/ 폴더에서 렌더링 결과물을 수집하여 8_renders/로 복사"""

        project_dir = OUTPUT_DIR / self.state.get("project_id", "unknown")
        renders_dir = project_dir / "8_renders"
        renders_dir.mkdir(parents=True, exist_ok=True)

        # Manim 기본 출력 폴더
        media_dir = Path("media/videos")

        if not media_dir.exists():
            print(f"❌ media/videos 폴더가 없습니다.")
            return {}

        # 프로젝트의 씬 ID 목록 가져오기
        scenes = self.state.get("scenes", {})
        completed_scenes = scenes.get("completed", [])

        if not completed_scenes:
            # 코드 파일에서 씬 ID 추출
            code_dir = project_dir / "4_manim_code"
            if code_dir.exists():
                code_files = list(code_dir.glob("*_manim.py"))
                completed_scenes = [f.stem.replace("_manim", "") for f in code_files]

        print(f"\n📦 렌더링 결과물 수집")
        print(f"   소스: {media_dir}")
        print(f"   대상: {renders_dir}")
        print(f"   씬 개수: {len(completed_scenes)}")
        print("="*60)

        collected = {}
        missing = []

        for scene_id in completed_scenes:
            # 씬별 폴더 찾기 (예: s1_manim, s2_manim 등)
            scene_folder_pattern = f"{scene_id}_manim"
            scene_folders = list(media_dir.glob(scene_folder_pattern))

            if not scene_folders:
                missing.append(scene_id)
                continue

            scene_folder = scene_folders[0]

            # 품질 폴더 찾기 (480p15, 720p30, 1080p60 등)
            quality_folders = [d for d in scene_folder.iterdir() if d.is_dir()]

            if not quality_folders:
                missing.append(scene_id)
                continue

            # 가장 최근 폴더 사용 (보통 하나뿐)
            quality_folder = sorted(quality_folders, key=lambda x: x.stat().st_mtime, reverse=True)[0]

            # 비디오 파일 찾기 (.mov 또는 .mp4)
            video_files = list(quality_folder.glob("*.mov")) + list(quality_folder.glob("*.mp4"))

            if not video_files:
                missing.append(scene_id)
                continue

            # 가장 최근 파일 사용
            source_file = sorted(video_files, key=lambda x: x.stat().st_mtime, reverse=True)[0]

            # 대상 파일명 (scene_id.확장자)
            dest_file = renders_dir / f"{scene_id}{source_file.suffix}"

            # 복사
            import shutil
            shutil.copy2(source_file, dest_file)

            collected[scene_id] = str(dest_file)
            print(f"   ✅ {scene_id}: {source_file.name} → {dest_file.name}")

        print("\n" + "="*60)
        print(f"✅ 수집 완료: {len(collected)}개")

        if missing:
            print(f"⚠️  누락: {len(missing)}개 - {', '.join(missing)}")

        # state.json 업데이트
        if collected:
            state_data = self.state.load()
            state_data.setdefault("files", {})["renders"] = list(collected.values())
            state_data["current_phase"] = "rendered"
            self.state.save()
            print(f"\n📝 state.json 업데이트 완료")
            print(f"   current_phase: rendered")
            print(f"   files.renders: {len(collected)}개 파일")

        return collected

    def generate_render_script(self) -> Optional[Path]:
        """렌더링 스크립트 생성"""
        
        project_dir = OUTPUT_DIR / self.state.get("project_id", "unknown")
        code_dir = project_dir / "4_manim_code"
        
        if not code_dir.exists():
            return None
        
        code_files = sorted(code_dir.glob("*_manim.py"))
        
        if not code_files:
            return None
        
        # Bash 스크립트 생성
        script_file = project_dir / "render_all.sh"
        
        lines = [
            "#!/bin/bash",
            "# Manim 렌더링 스크립트",
            f"# 프로젝트: {self.state.get('project_id')}",
            f"# 생성일: {datetime.now().isoformat()}",
            "",
            "set -e  # 오류 시 중단",
            "",
        ]
        
        for code_file in code_files:
            scene_id = code_file.stem.replace("_manim", "")
            class_name = scene_id.capitalize()
            
            lines.append(f'echo "렌더링: {scene_id}..."')
            lines.append(f'manim -pql "{code_file}" {class_name}')
            lines.append("")
        
        lines.append('echo "모든 씬 렌더링 완료!"')
        
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        
        # 실행 권한 부여 (Unix)
        try:
            script_file.chmod(0o755)
        except:
            pass
        
        # Windows용 배치 파일도 생성
        bat_file = project_dir / "render_all.bat"
        
        bat_lines = [
            "@echo off",
            f"REM Manim 렌더링 스크립트",
            f"REM 프로젝트: {self.state.get('project_id')}",
            "",
        ]
        
        for code_file in code_files:
            scene_id = code_file.stem.replace("_manim", "")
            class_name = scene_id.capitalize()
            
            bat_lines.append(f'echo 렌더링: {scene_id}...')
            bat_lines.append(f'manim -pql "{code_file}" {class_name}')
            bat_lines.append("")
        
        bat_lines.append('echo 모든 씬 렌더링 완료!')
        bat_lines.append("pause")
        
        with open(bat_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(bat_lines))
        
        print(f"✅ 렌더링 스크립트 생성")
        print(f"   Bash: {script_file}")
        print(f"   Windows: {bat_file}")

        return script_file


# ============================================================================
# 씬 분할 저장 (토큰 절약)
# ============================================================================

class SceneSplitter:
    """scenes.json을 개별 씬 파일로 분할"""

    def __init__(self, state: StateManager):
        self.state = state

    def split(self):
        """scenes.json을 개별 파일로 분할"""
        project_id = self.state.get("project_id")
        if not project_id:
            print("❌ 활성 프로젝트가 없습니다.")
            return

        scenes_path = Path(f"output/{project_id}/2_scenes/scenes.json")
        if not scenes_path.exists():
            print(f"❌ scenes.json이 없습니다: {scenes_path}")
            return

        # scenes.json 읽기
        with open(scenes_path, "r", encoding="utf-8") as f:
            scenes = json.load(f)

        if not scenes:
            print("❌ scenes.json이 비어있습니다.")
            return

        # 개별 파일로 저장
        output_dir = scenes_path.parent
        saved_count = 0

        for scene in scenes:
            scene_id = scene.get("scene_id", "unknown")
            scene_file = output_dir / f"{scene_id}.json"

            with open(scene_file, "w", encoding="utf-8") as f:
                json.dump(scene, f, ensure_ascii=False, indent=2)

            saved_count += 1

        print(f"✅ {saved_count}개 씬을 개별 파일로 분할했습니다.")
        print(f"   위치: {output_dir}/")
        print(f"   예: {output_dir}/s1.json, s2.json, ...")
        print(f"\n💡 이제 Claude가 필요한 씬만 읽어 토큰을 절약합니다.")


# ============================================================================
# 나레이션 추출 (Narration Designer용)
# ============================================================================

class NarrationExtractor:
    """씬 파일에서 narration_display를 추출하여 Narration Designer에게 전달"""

    def __init__(self, state: StateManager):
        self.state = state

    def extract(self, scene_ids: Optional[List[str]] = None):
        """씬 파일들에서 narration_display를 추출하여 출력

        Args:
            scene_ids: 추출할 씬 ID 목록. None이면 전체 추출
        """
        project_id = self.state.get("project_id")
        if not project_id:
            print("❌ 활성 프로젝트가 없습니다.")
            return

        scenes_path = Path(f"output/{project_id}/2_scenes")
        if not scenes_path.exists():
            print(f"❌ 씬 폴더가 없습니다: {scenes_path}")
            return

        # 씬 파일 목록 가져오기
        if scene_ids:
            scene_files = [scenes_path / f"{sid}.json" for sid in scene_ids]
            scene_files = [f for f in scene_files if f.exists()]
        else:
            scene_files = sorted(scenes_path.glob("s*.json"),
                               key=lambda x: self._scene_sort_key(x.stem))

        if not scene_files:
            print("❌ 씬 파일이 없습니다.")
            return

        # narration_display 추출
        extractions = []
        for scene_file in scene_files:
            try:
                with open(scene_file, "r", encoding="utf-8") as f:
                    scene_data = json.load(f)

                scene_id = scene_data.get("scene_id", scene_file.stem)
                narration_display = scene_data.get("narration_display", "")

                if narration_display:
                    extractions.append({
                        "scene_id": scene_id,
                        "narration_display": narration_display
                    })
            except Exception as e:
                print(f"  ⚠️ {scene_file.name} 로드 실패: {e}")

        # 결과 출력 (Claude가 읽어서 Narration Designer에게 전달)
        print(f"\n📝 나레이션 추출 완료: {len(extractions)}개 씬")
        print("\n```json")
        print(json.dumps(extractions, ensure_ascii=False, indent=2))
        print("```")
        print(f"\n💡 위 내용을 Narration Designer에게 전달하세요.")
        print(f"   출력 위치: output/{project_id}/2_narration/")

    def _scene_sort_key(self, scene_id: str):
        """씬 ID 정렬 키 (s1, s2, ..., s10, s11, ...)"""
        import re
        match = re.match(r's(\d+)([a-z]*)', scene_id)
        if match:
            return (int(match.group(1)), match.group(2))
        return (0, scene_id)

    def save_narration(self, scene_id: str, subtitle_display: str, narration_tts: str):
        """Narration Designer가 생성한 나레이션을 저장

        Args:
            scene_id: 씬 ID (예: s1)
            subtitle_display: 자막용 텍스트 (;; 구분자 포함)
            narration_tts: TTS 음성용 텍스트 (한글 발음)
        """
        project_id = self.state.get("project_id")
        if not project_id:
            print("❌ 활성 프로젝트가 없습니다.")
            return False

        narration_path = Path(f"output/{project_id}/2_narration")
        narration_path.mkdir(parents=True, exist_ok=True)

        narration_data = {
            "scene_id": scene_id,
            "subtitle_display": subtitle_display,
            "narration_tts": narration_tts
        }

        output_file = narration_path / f"{scene_id}_narration.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(narration_data, f, ensure_ascii=False, indent=2)

        print(f"  ✅ {output_file.name} 저장됨")
        return True

    def check_narrations(self) -> Dict[str, Any]:
        """나레이션 파일 상태 확인"""
        project_id = self.state.get("project_id")
        if not project_id:
            return {"error": "활성 프로젝트가 없습니다."}

        scenes_path = Path(f"output/{project_id}/2_scenes")
        narration_path = Path(f"output/{project_id}/2_narration")

        # 씬 목록
        scene_files = list(scenes_path.glob("s*.json")) if scenes_path.exists() else []
        scene_ids = [f.stem for f in scene_files]

        # 나레이션 파일 목록
        narration_files = list(narration_path.glob("*_narration.json")) if narration_path.exists() else []
        completed_ids = [f.stem.replace("_narration", "") for f in narration_files]

        missing = [sid for sid in scene_ids if sid not in completed_ids]

        result = {
            "total_scenes": len(scene_ids),
            "completed": len(completed_ids),
            "missing": missing,
            "missing_count": len(missing)
        }

        print(f"\n📊 나레이션 상태:")
        print(f"   전체 씬: {result['total_scenes']}개")
        print(f"   완료: {result['completed']}개")
        print(f"   미완료: {result['missing_count']}개")
        if missing:
            print(f"   미완료 목록: {', '.join(missing[:10])}{'...' if len(missing) > 10 else ''}")

        return result


# ============================================================================
# 영상 합성 및 자막 관리
# ============================================================================

class ComposerManager:
    """영상 합성 및 자막 생성 관리"""

    def __init__(self, state: StateManager):
        self.state = state
        self.ffmpeg_path = self._find_ffmpeg()
        self.ffprobe_path = self._find_ffprobe()

    def _find_ffmpeg(self) -> str:
        """FFmpeg 경로 찾기"""
        import shutil

        # 시스템 PATH에서 찾기
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg:
            return ffmpeg

        # Windows 일반적인 경로들
        common_paths = [
            Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/WinGet/Links/ffmpeg.exe",
            Path("C:/ffmpeg/bin/ffmpeg.exe"),
            Path("C:/Program Files/ffmpeg/bin/ffmpeg.exe"),
        ]

        for path in common_paths:
            if path.exists():
                return str(path)

        return "ffmpeg"  # PATH에 있다고 가정

    def _find_ffprobe(self) -> str:
        """FFprobe 경로 찾기"""
        import shutil

        ffprobe = shutil.which("ffprobe")
        if ffprobe:
            return ffprobe

        # FFmpeg와 같은 폴더에서 찾기
        ffmpeg_dir = Path(self.ffmpeg_path).parent
        ffprobe_path = ffmpeg_dir / "ffprobe.exe"
        if ffprobe_path.exists():
            return str(ffprobe_path)

        return "ffprobe"

    def _get_duration(self, file_path: Path) -> Optional[float]:
        """오디오/비디오 파일 길이 확인 (ffprobe 사용)"""
        try:
            result = subprocess.run([
                self.ffprobe_path, "-v", "error",
                "-show_entries", "format=duration",
                "-of", "csv=p=0", str(file_path)
            ], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
        except Exception as e:
            print(f"  ⚠️ 길이 확인 실패: {e}")
        return None

    def _get_project_paths(self) -> Dict[str, Path]:
        """프로젝트 경로들 반환"""
        project_id = self.state.get("project_id")
        if not project_id:
            return {}

        base = Path("output") / project_id
        return {
            "base": base,
            "audio": base / "0_audio",
            "scenes": base / "2_scenes",
            "subtitles": base / "7_subtitles",
            "renders": base / "8_renders",
            "backgrounds": base / "9_backgrounds",
            "final": base / "10_scene_final",
        }

    def _format_srt_time(self, seconds: float) -> str:
        """초를 SRT 시간 형식으로 변환: HH:MM:SS,mmm"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def _get_subtitle_display(self, project_dir: Path, scene_id: str, scene_data: dict) -> str:
        """subtitle_display 텍스트를 가져옴 (우선순위: narration#.json > scenes.json)

        Args:
            project_dir: 프로젝트 디렉토리
            scene_id: 씬 ID (예: s1)
            scene_data: scenes.json에서 읽은 씬 데이터 (fallback용)

        Returns:
            subtitle_display 텍스트
        """
        # 1. narration#.json 우선 확인
        narration_file = project_dir / "2_narration" / f"{scene_id}_narration.json"
        if narration_file.exists():
            try:
                with open(narration_file, 'r', encoding='utf-8') as f:
                    narration_data = json.load(f)
                    subtitle_display = narration_data.get("subtitle_display", "")
                    if subtitle_display:
                        return subtitle_display
            except Exception:
                pass

        # 2. Fallback: scenes.json의 subtitle_display 또는 narration_display
        return scene_data.get("subtitle_display") or scene_data.get("narration_display", "")

    def generate_subtitles(self) -> bool:
        """모든 씬의 SRT 자막 생성 (문장 단위)

        텍스트 소스 우선순위:
            1. 2_narration/{scene_id}_narration.json의 subtitle_display (;; 포함)
            2. 2_scenes/{scene_id}.json의 subtitle_display (fallback)
            3. 2_scenes/{scene_id}.json의 narration_display (fallback)

        타이밍 소스: timing.json의 sentences 배열 (Whisper segments)

        방식:
        1. subtitle_display를 ;; 또는 .?! 기준으로 문장 분리 → 텍스트
        2. timing.json의 sentences 배열에서 타이밍 추출 → start/end
        3. 문장 수 일치하면 1:1 매핑, 불일치하면 균등 분배
        """
        paths = self._get_project_paths()
        if not paths:
            print("❌ 활성 프로젝트가 없습니다.")
            return False

        audio_path = paths["audio"]
        subtitle_path = paths["subtitles"]
        scenes_path = paths["scenes"]
        project_dir = paths["base"]

        # 자막 폴더 생성
        subtitle_path.mkdir(parents=True, exist_ok=True)

        # narration 파일 존재 여부 확인
        narration_dir = project_dir / "2_narration"
        use_narration_files = narration_dir.exists() and list(narration_dir.glob("*_narration.json"))

        print(f"\n📝 자막 생성 시작")
        if use_narration_files:
            print(f"   📁 텍스트 소스: 2_narration/")
        else:
            print(f"   📁 텍스트 소스: 2_scenes/ (fallback)")
        print("="*60)

        # scenes.json에서 자막 텍스트 로드
        # 우선순위: narration#.json > subtitle_display > narration_display
        scene_texts = {}
        for scene_file in scenes_path.glob("s*.json"):
            try:
                with open(scene_file, 'r', encoding='utf-8') as f:
                    scene_data = json.load(f)
                    scene_id = scene_data.get('scene_id', scene_file.stem)
                    # subtitle_display 가져오기 (narration#.json 우선)
                    subtitle_text = self._get_subtitle_display(project_dir, scene_id, scene_data)
                    scene_texts[scene_id] = subtitle_text
            except Exception as e:
                print(f"  ⚠️ {scene_file.name} 로드 실패: {e}")

        # timing 파일 찾기 (s32a 같은 ID도 지원)
        def scene_sort_key(path):
            scene_id = path.stem.split("_")[0][1:]  # "s32a" -> "32a"
            import re
            match = re.match(r'(\d+)([a-z]*)', scene_id)
            if match:
                return (int(match.group(1)), match.group(2))
            return (0, scene_id)

        timing_files = sorted(audio_path.glob("*_timing.json"), key=scene_sort_key)

        if not timing_files:
            print("❌ timing.json 파일을 찾을 수 없습니다.")
            print("   먼저 TTS 생성 또는 audio-process를 실행하세요.")
            return False

        generated = []

        for timing_file in timing_files:
            scene_id = timing_file.stem.replace("_timing", "")

            with open(timing_file, 'r', encoding='utf-8') as f:
                timing_data = json.load(f)

            # 원본 텍스트 가져오기 (Whisper 결과가 아닌 narration_display 사용!)
            original_text = scene_texts.get(scene_id, '')
            if not original_text:
                print(f"  ⚠️ {scene_id}: narration_display 없음, Whisper 텍스트 사용")
                original_text = timing_data.get('whisper_text', '')

            total_duration = timing_data.get('total_duration', timing_data.get('duration', 0))
            timing_sentences = timing_data.get('sentences', timing_data.get('segments', []))

            # narration_display를 문장 분리 (.?! 기준)
            display_sentences = self._split_sentences(original_text)

            if not display_sentences or total_duration <= 0:
                # SRT 파일 저장 (빈 파일)
                srt_file = subtitle_path / f"{scene_id}.srt"
                with open(srt_file, 'w', encoding='utf-8') as f:
                    f.write("")
                generated.append(scene_id)
                continue

            # 타이밍 계산: sentences 배열 타이밍 + narration_display 텍스트
            sentence_timings = self._calculate_sentence_timings_from_segments(
                display_sentences, timing_sentences, total_duration
            )

            # SRT 생성 - 문장 단위
            srt_lines = []
            for idx, (sentence, start, end) in enumerate(sentence_timings, 1):
                start_time = self._format_srt_time(start)
                end_time = self._format_srt_time(end)

                srt_lines.append(str(idx))
                srt_lines.append(f"{start_time} --> {end_time}")
                srt_lines.append(sentence)
                srt_lines.append("")

            # SRT 파일 저장
            srt_file = subtitle_path / f"{scene_id}.srt"
            with open(srt_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(srt_lines))

            generated.append(scene_id)
            print(f"  ✅ {scene_id}.srt: {len(display_sentences)}문장")

        print(f"\n✅ 자막 생성 완료: {len(generated)}개 파일")
        print(f"   위치: {subtitle_path}")
        print(f"   ℹ️  텍스트: narration_display, 타이밍: Whisper segments")

        return True

    def generate_subtitle_for_scene(self, scene_id: str) -> bool:
        """단일 씬의 SRT 자막 생성 (narration#.json 우선, scenes.json fallback)"""
        paths = self._get_project_paths()
        if not paths:
            print("❌ 활성 프로젝트가 없습니다.")
            return False

        audio_path = paths["audio"]
        subtitle_path = paths["subtitles"]
        scenes_path = paths["scenes"]
        project_dir = paths["base"]

        subtitle_path.mkdir(parents=True, exist_ok=True)

        # 씬 파일에서 데이터 로드
        scene_file = scenes_path / f"{scene_id}.json"
        if not scene_file.exists():
            print(f"❌ 씬 파일을 찾을 수 없습니다: {scene_file}")
            return False

        with open(scene_file, 'r', encoding='utf-8') as f:
            scene_data = json.load(f)

        # subtitle_display 가져오기 (narration#.json 우선)
        original_text = self._get_subtitle_display(project_dir, scene_id, scene_data)

        # timing 파일 로드
        timing_file = audio_path / f"{scene_id}_timing.json"
        if not timing_file.exists():
            print(f"❌ 타이밍 파일을 찾을 수 없습니다: {timing_file}")
            return False

        with open(timing_file, 'r', encoding='utf-8') as f:
            timing_data = json.load(f)

        total_duration = timing_data.get('total_duration', 0)
        timing_sentences = timing_data.get('sentences', [])

        # 문장 분리 및 타이밍 계산
        display_sentences = self._split_sentences(original_text)

        if not display_sentences or total_duration <= 0:
            srt_file = subtitle_path / f"{scene_id}.srt"
            with open(srt_file, 'w', encoding='utf-8') as f:
                f.write("")
            print(f"  ⚠️ {scene_id}: 빈 자막 생성")
            return True

        sentence_timings = self._calculate_sentence_timings_from_segments(
            display_sentences, timing_sentences, total_duration
        )

        # SRT 생성
        srt_lines = []
        for idx, (sentence, start, end) in enumerate(sentence_timings, 1):
            start_time = self._format_srt_time(start)
            end_time = self._format_srt_time(end)
            srt_lines.append(str(idx))
            srt_lines.append(f"{start_time} --> {end_time}")
            srt_lines.append(sentence)
            srt_lines.append("")

        srt_file = subtitle_path / f"{scene_id}.srt"
        with open(srt_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(srt_lines))

        print(f"✅ {scene_id}.srt 생성 완료: {len(display_sentences)}문장")
        return True

    def _split_sentences(self, text: str) -> List[str]:
        """텍스트를 문장 단위로 분리

        핵심: Scene Director가 s{n}.json의 subtitle_display에 ;;로 분할 위치를 지정
        Python은 ;; 기준으로 분리만 수행 (자동 분할 없음)

        - ;; 구분자가 있으면: ;; 기준으로 분리
        - ;; 구분자가 없으면: 텍스트 전체를 하나의 자막으로 사용
        """
        if not text:
            return []

        # ;; 구분자가 있으면 ;; 기준으로 분리
        if ';;' in text:
            sentences = text.split(';;')
            sentences = [s.strip() for s in sentences if s.strip()]
            return sentences

        # ;; 가 없으면 텍스트 전체를 하나의 자막으로 반환
        return [text.strip()]

    def _calculate_sentence_timings_from_segments(
        self,
        display_sentences: List[str],
        timing_sentences: List[dict],
        total_duration: float
    ) -> List[tuple]:
        """문장별 타이밍 계산 (균등 분배 방식)

        ============================================================
        [자막 타이밍 계산 로직] - 균등 분배
        ============================================================

        Whisper의 한계:
        - segments: 발화 단위(pause 기준)이지 문장 단위(.?!)가 아님
        - words: 텍스트 오인식 많음 ("탄력성" → "팔력성")

        따라서 균등 분배 사용:
        - 텍스트: narration_display에서 .?! 기준 분리 (정확함)
        - 타이밍: total_duration / 문장수 (근사치)

        예시 (s16, 14.35초, 5문장):
        - 문장1: 0.00 ~ 2.87초
        - 문장2: 2.87 ~ 5.74초
        - 문장3: 5.74 ~ 8.61초
        - 문장4: 8.61 ~ 11.48초
        - 문장5: 11.48 ~ 14.35초
        ============================================================

        Args:
            display_sentences: narration_display에서 분리한 문장들 (텍스트용)
            timing_sentences: timing.json의 sentences 배열 (현재 미사용)
            total_duration: 전체 오디오 길이

        Returns:
            List of (sentence_text, start_time, end_time)
        """
        n_display = len(display_sentences)

        # ============================================================
        # 균등 분배: total_duration / 문장수
        # ============================================================
        duration_per_sentence = total_duration / n_display
        result = []
        for i, sentence in enumerate(display_sentences):
            start = i * duration_per_sentence
            end = (i + 1) * duration_per_sentence
            # 마지막 문장은 정확히 total_duration까지
            if i == n_display - 1:
                end = total_duration
            result.append((sentence, start, end))
        return result

    def _merge_audio(self, scene_id: str) -> Optional[Path]:
        """씬의 오디오 파일 반환 (새 방식: 단일 파일 / 구 방식: 병합)"""
        paths = self._get_project_paths()
        audio_path = paths["audio"]

        # 1. 새 방식: 단일 파일 (s1.mp3) 확인
        single_file = audio_path / f"{scene_id}.mp3"
        if single_file.exists():
            return single_file

        # 2. 구 방식: 문장별 파일들 (s1_1.mp3, s1_2.mp3, ...) 병합
        audio_files = sorted(
            audio_path.glob(f"{scene_id}_*.mp3"),
            key=lambda x: int(x.stem.split("_")[1]) if "_" in x.stem and x.stem.split("_")[1].isdigit() else 0
        )

        # timing.json, concat.txt 등 제외
        audio_files = [f for f in audio_files if not any(x in f.stem for x in ["timing", "concat", "merged"])]

        if not audio_files:
            print(f"  ⚠️  {scene_id}: 오디오 파일 없음")
            return None

        # 파일이 1개면 바로 반환
        if len(audio_files) == 1:
            return audio_files[0]

        merged_file = audio_path / f"{scene_id}_merged.mp3"

        # 이미 병합된 파일이 있고 최신이면 재사용
        if merged_file.exists():
            merged_time = merged_file.stat().st_mtime
            if all(f.stat().st_mtime < merged_time for f in audio_files):
                return merged_file

        # concat 파일 생성
        concat_file = audio_path / f"{scene_id}_concat.txt"
        with open(concat_file, 'w', encoding='utf-8') as f:
            for audio in audio_files:
                f.write(f"file '{audio.name}'\n")

        # FFmpeg로 병합
        cmd = [
            self.ffmpeg_path,
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",
            "-y", str(merged_file)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"  ❌ {scene_id}: 오디오 병합 실패")
            return None

        return merged_file

    def _find_manim_render(self, scene_id: str) -> Optional[Path]:
        """Manim 렌더링 결과 찾기"""
        # media/videos/{scene_id}_manim 폴더에서 찾기
        media_path = Path("media/videos") / f"{scene_id}_manim"

        if media_path.exists():
            # 품질별 폴더 확인 (높은 품질 우선)
            for quality in ["1080p60", "1080p30", "720p30", "480p15"]:
                quality_path = media_path / quality
                if quality_path.exists():
                    # Scene*.mov 또는 Scene*.mp4 찾기
                    for ext in ["mov", "mp4"]:
                        scene_files = list(quality_path.glob(f"Scene*.{ext}"))
                        if scene_files:
                            return scene_files[0]

        # 8_renders 폴더에서도 찾기
        paths = self._get_project_paths()
        renders_path = paths.get("renders")
        if renders_path and renders_path.exists():
            for ext in ["mov", "mp4"]:
                render_files = list(renders_path.glob(f"{scene_id}*.{ext}"))
                if render_files:
                    return render_files[0]

        return None

    def _find_background(self, scene_id: str) -> Optional[Path]:
        """배경 이미지 찾기"""
        paths = self._get_project_paths()
        bg_path = paths.get("backgrounds")

        if not bg_path or not bg_path.exists():
            return None

        for ext in ["png", "jpg", "jpeg", "webp"]:
            bg_file = bg_path / f"{scene_id}_bg.{ext}"
            if bg_file.exists():
                return bg_file

        return None

    def compose_scene(self, scene_id: str, with_subtitle: bool = True, end_padding: float = 1.0) -> Optional[Path]:
        """단일 씬 합성 (배경 + Manim + 오디오 + 자막)

        Args:
            scene_id: 씬 ID (예: s1, s2)
            with_subtitle: 자막 포함 여부
            end_padding: 씬 끝에 추가할 무음 패딩 (초). 마지막 프레임 유지됨.
        """
        paths = self._get_project_paths()
        if not paths:
            print("❌ 활성 프로젝트가 없습니다.")
            return None

        print(f"\n🎬 {scene_id} 합성 시작...")

        # 출력 폴더 생성
        final_path = paths["final"]
        final_path.mkdir(parents=True, exist_ok=True)

        # 필요한 파일들 찾기
        manim_file = self._find_manim_render(scene_id)
        bg_file = self._find_background(scene_id)
        audio_file = self._merge_audio(scene_id)
        subtitle_file = paths["subtitles"] / f"{scene_id}.srt" if with_subtitle else None

        # 파일 체크
        if not manim_file:
            print(f"  ❌ Manim 렌더링 파일 없음")
            return None

        if not audio_file:
            print(f"  ❌ 오디오 파일 없음")
            return None

        # 오디오 길이 확인 (오디오 기준으로 영상 길이 결정)
        audio_duration = self._get_duration(audio_file)
        if not audio_duration:
            print(f"  ⚠️ 오디오 길이 확인 불가, 기본값 사용")
            audio_duration = 30.0

        # 패딩 포함 총 길이 계산
        total_duration = audio_duration + end_padding

        print(f"  📹 Manim: {manim_file.name}")
        print(f"  🎵 Audio: {audio_file.name} ({audio_duration:.2f}초 + {end_padding}초 패딩)")
        if bg_file:
            print(f"  🖼️  Background: {bg_file.name}")
        if subtitle_file and subtitle_file.exists():
            print(f"  📝 Subtitle: {subtitle_file.name}")

        # 출력 파일 경로
        output_file = final_path / f"{scene_id}_final.mp4"

        # 자막 필터 준비 (문장 단위, 화면 맨 아래 배치)
        # MarginV=15: 화면 아래 여유
        # MarginL/R=20: 좌우 여백
        # FontSize=20: 가독성 확보
        subtitle_filter_part = ""
        if with_subtitle and subtitle_file and subtitle_file.exists():
            srt_path = str(subtitle_file).replace("\\", "/").replace(":", "\\:")
            subtitle_filter_part = (
                f",subtitles='{srt_path}':"
                f"force_style='FontName=Malgun Gothic,FontSize=20,"
                f"PrimaryColour=&HFFFFFF,OutlineColour=&H000000,"
                f"Outline=2,Shadow=1,MarginV=15,MarginL=20,MarginR=20'"
            )

        # FFmpeg 합성 명령 구성 (배경 + Manim + 오디오 + 자막 한 번에)
        # eof_action=repeat: Manim 영상 끝나면 마지막 프레임 유지
        # apad: 오디오 끝에 무음 패딩 추가 (씬 간 여유)
        if bg_file:
            # 배경 + Manim 오버레이 + 자막
            # subtitles 필터는 overlay 후 별도 체인으로 적용
            if with_subtitle and subtitle_file and subtitle_file.exists():
                srt_path_fc = str(subtitle_file).replace("\\", "/").replace(":", "\\:")
                filter_complex = (
                    f"[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,"
                    f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2[bg];"
                    f"[1:v]scale=1920:1080:force_original_aspect_ratio=decrease,format=rgba[fg];"
                    f"[bg][fg]overlay=(W-w)/2:(H-h)/2:eof_action=repeat[ov];"
                    f"[ov]subtitles='{srt_path_fc}':"
                    f"force_style='FontName=Malgun Gothic,FontSize=20,"
                    f"PrimaryColour=&HFFFFFF,OutlineColour=&H000000,"
                    f"Outline=2,Shadow=1,MarginV=15,MarginL=20,MarginR=20'[outv];"
                    f"[2:a]apad=pad_dur={end_padding}[outa]"
                )
            else:
                filter_complex = (
                    f"[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,"
                    f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2[bg];"
                    f"[1:v]scale=1920:1080:force_original_aspect_ratio=decrease,format=rgba[fg];"
                    f"[bg][fg]overlay=(W-w)/2:(H-h)/2:eof_action=repeat[outv];"
                    f"[2:a]apad=pad_dur={end_padding}[outa]"
                )

            cmd = [
                self.ffmpeg_path,
                "-loop", "1", "-i", str(bg_file),
                "-i", str(manim_file),
                "-i", str(audio_file),
                "-filter_complex", filter_complex,
                "-map", "[outv]", "-map", "[outa]",
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "192k",
                "-t", str(total_duration),
                "-y", str(output_file)
            ]
        else:
            # Manim만 사용 (배경 없음) + 자막
            # tpad: Manim 끝나면 마지막 프레임 유지
            video_filter = f"scale=1920:1080,tpad=stop_mode=clone:stop_duration={total_duration}{subtitle_filter_part}"
            cmd = [
                self.ffmpeg_path,
                "-i", str(manim_file),
                "-i", str(audio_file),
                "-vf", video_filter,
                "-af", f"apad=pad_dur={end_padding}",
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "192k",
                "-t", str(total_duration),
                "-y", str(output_file)
            ]

        # 합성 실행
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"  ❌ 합성 실패: {result.stderr[:200]}")
            return None

        if with_subtitle and subtitle_file and subtitle_file.exists():
            print(f"  ✅ 자막 포함 합성 완료")

        print(f"  ✅ 합성 완료: {output_file.name}")
        return output_file

    def compose_all(self, with_subtitle: bool = True) -> List[Path]:
        """모든 씬 합성"""
        paths = self._get_project_paths()
        if not paths:
            print("❌ 활성 프로젝트가 없습니다.")
            return []

        # scenes.json에서 씬 목록 가져오기
        scenes_file = paths["scenes"] / "scenes.json"
        if not scenes_file.exists():
            print("❌ scenes.json 파일이 없습니다.")
            return []

        with open(scenes_file, 'r', encoding='utf-8') as f:
            scenes = json.load(f)

        scene_ids = [s["scene_id"] for s in scenes]

        print(f"\n🎬 전체 씬 합성 시작 ({len(scene_ids)}개)")
        print("=" * 50)

        composed = []
        failed = []

        for i, scene_id in enumerate(scene_ids, 1):
            print(f"\n[{i}/{len(scene_ids)}] {scene_id}")

            result = self.compose_scene(scene_id, with_subtitle=with_subtitle)

            if result:
                composed.append(result)
            else:
                failed.append(scene_id)

        print("\n" + "=" * 50)
        print(f"✅ 합성 완료: {len(composed)}개")
        if failed:
            print(f"❌ 실패: {len(failed)}개 ({', '.join(failed)})")

        return composed

    def transition_generate(self) -> bool:
        """섹션 전환 클립 생성 + concat_list.txt 생성"""
        paths = self._get_project_paths()
        if not paths:
            print("❌ 활성 프로젝트가 없습니다.")
            return False

        # transitions.json 읽기
        transitions_file = paths["scenes"] / "transitions.json"
        if not transitions_file.exists():
            print("⚠️ transitions.json이 없습니다. 전환 클립 없이 진행합니다.")
            # concat_list.txt만 생성
            return self._generate_concat_list(paths, [])

        with open(transitions_file, 'r', encoding='utf-8') as f:
            transitions = json.load(f)

        if not transitions:
            print("⚠️ 전환 클립이 정의되지 않았습니다.")
            return self._generate_concat_list(paths, [])

        print(f"\n🎬 전환 클립 생성 ({len(transitions)}개)")

        # 스타일별 색상 설정
        style = self.state.get("settings.style", "cyberpunk")
        style_colors = {
            "minimal": {"bg": "black", "text": "white"},
            "cyberpunk": {"bg": "#0a0a1a", "text": "#00ffff"},
            "paper": {"bg": "#2a2a2a", "text": "#f5f5dc"},
            "space": {"bg": "#000022", "text": "#4444ff"},
            "geometric": {"bg": "#1a1a1a", "text": "#ffd700"},
            "stickman": {"bg": "#1a1a2e", "text": "#ffffff"},
        }
        colors = style_colors.get(style, style_colors["cyberpunk"])

        # 해상도 설정
        aspect = self.state.get("settings.aspect_ratio", "16:9")
        if aspect == "16:9":
            width, height = 1920, 1080
        else:  # 9:16
            width, height = 1080, 1920

        final_path = paths["final"]
        final_path.mkdir(parents=True, exist_ok=True)

        created_transitions = []

        for t in transitions:
            scene_id = t["after_scene"]
            text = t["text"]
            duration = t.get("duration", 2)

            output_file = final_path / f"t_after_{scene_id}.mp4"
            print(f"  {scene_id} 뒤 전환: \"{text}\"")

            # Windows용 폰트 경로
            font_path = "C\\:/Windows/Fonts/malgun.ttf"

            # 텍스트에서 특수문자 이스케이프
            escaped_text = text.replace("'", "\\'").replace(":", "\\:")

            # 비디오 필터: 텍스트 + 페이드인/아웃
            # fade=in:0:12 (0.5초 = 12프레임 @24fps), fade=out:36:12 (1.5초 지점부터)
            fade_frames = 12  # 0.5초 at 24fps
            total_frames = int(duration * 24)
            fade_out_start = total_frames - fade_frames

            vf_filter = (
                f"drawtext=text='{escaped_text}':"
                f"fontfile='{font_path}':"
                f"fontsize=56:"
                f"fontcolor={colors['text']}:"
                f"x=(w-text_w)/2:y=(h-text_h)/2,"
                f"fade=t=in:st=0:d=0.5,"
                f"fade=t=out:st={duration - 0.5}:d=0.5"
            )

            cmd = [
                self.ffmpeg_path,
                "-f", "lavfi",
                "-i", f"color=c={colors['bg']}:s={width}x{height}:d={duration}:r=24",
                "-f", "lavfi",
                "-i", f"anullsrc=r=44100:cl=stereo",
                "-t", str(duration),
                "-vf", vf_filter,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "128k",
                "-pix_fmt", "yuv420p",
                "-y", str(output_file)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')

            if result.returncode == 0 and output_file.exists():
                print(f"    ✅ 생성: {output_file.name}")
                created_transitions.append(scene_id)
            else:
                print(f"    ❌ 실패: {result.stderr[:200] if result.stderr else 'Unknown error'}")

        # concat_list.txt 생성
        success = self._generate_concat_list(paths, created_transitions)

        print(f"\n✅ 전환 클립 생성 완료: {len(created_transitions)}개")
        return success

    def _generate_concat_list(self, paths: Dict[str, Path], transition_scenes: List[str]) -> bool:
        """concat_list.txt 생성 (전환 클립 포함)"""
        final_path = paths["final"]
        scenes_file = paths["scenes"] / "scenes.json"

        if not scenes_file.exists():
            print("❌ scenes.json이 없습니다.")
            return False

        with open(scenes_file, 'r', encoding='utf-8') as f:
            scenes = json.load(f)

        scene_ids = [s["scene_id"] for s in scenes]
        transition_set = set(transition_scenes)

        concat_lines = []
        for scene_id in scene_ids:
            scene_file = final_path / f"{scene_id}_final.mp4"
            if scene_file.exists():
                concat_lines.append(f"file '{scene_id}_final.mp4'")

                # 이 씬 뒤에 전환 클립이 있는지 확인
                if scene_id in transition_set:
                    transition_file = final_path / f"t_after_{scene_id}.mp4"
                    if transition_file.exists():
                        concat_lines.append(f"file 't_after_{scene_id}.mp4'")

        # subscribe.mp4가 있으면 맨 끝에 추가
        subscribe_file = Path(__file__).parent / "subscribe.mp4"
        if subscribe_file.exists():
            concat_lines.append(f"file '{subscribe_file.resolve()}'")
            print("🔔 subscribe.mp4 추가됨 (영상 끝)")

        concat_file = final_path / "concat_list.txt"
        with open(concat_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(concat_lines))

        print(f"📝 concat_list.txt 생성: {len(concat_lines)}개 항목")
        return True

    def _merge_with_filter_complex(self, video_files: List[str], output_file: Path, work_dir: Path) -> subprocess.CompletedProcess:
        """filter_complex를 사용하여 영상 병합 (전환 클립 포함 시)"""
        # 입력 파일 인자 구성 (work_dir 기준 상대경로)
        input_args = []
        for vf in video_files:
            input_args.extend(["-i", vf])

        # filter_complex 구성
        n = len(video_files)
        filter_parts = []
        for i in range(n):
            filter_parts.append(f"[{i}:v][{i}:a]")
        filter_str = "".join(filter_parts) + f"concat=n={n}:v=1:a=1[outv][outa]"

        # 출력 파일을 절대 경로로 변환
        output_abs = output_file.resolve() if hasattr(output_file, 'resolve') else Path(output_file).resolve()

        cmd = [
            self.ffmpeg_path,
            *input_args,
            "-filter_complex", filter_str,
            "-map", "[outv]",
            "-map", "[outa]",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-y", str(output_abs)
        ]

        return subprocess.run(cmd, capture_output=True, text=True, cwd=str(work_dir))

    def _merge_in_batches(self, video_files: List[str], output_file: Path, work_dir: Path) -> subprocess.CompletedProcess:
        """파일이 많을 때 배치로 나눠서 병합"""
        batch_size = 15  # FFmpeg 입력 제한 고려
        temp_files = []

        # 배치별로 임시 파일 생성
        for i in range(0, len(video_files), batch_size):
            batch = video_files[i:i + batch_size]
            batch_num = i // batch_size + 1
            temp_output = work_dir / f"_temp_batch_{batch_num}.mp4"
            temp_files.append(temp_output)

            print(f"    배치 {batch_num} 처리 ({len(batch)}개)...")
            result = self._merge_with_filter_complex(batch, temp_output, work_dir)
            if result.returncode != 0:
                # 실패 시 임시 파일 정리
                for tf in temp_files:
                    if tf.exists():
                        tf.unlink()
                return result

        # 임시 파일들을 최종 병합
        if len(temp_files) == 1:
            # 배치가 하나면 그냥 이름 변경
            temp_files[0].rename(output_file)
            result = subprocess.CompletedProcess(args=[], returncode=0)
        else:
            print(f"    최종 병합 ({len(temp_files)}개 배치)...")
            temp_names = [tf.name for tf in temp_files]
            result = self._merge_with_filter_complex(temp_names, output_file, work_dir)

        # 임시 파일 정리
        for tf in temp_files:
            if tf.exists():
                tf.unlink()

        return result

    def merge_final(self) -> Optional[Path]:
        """모든 씬을 하나의 최종 영상으로 병합"""
        paths = self._get_project_paths()
        if not paths:
            print("❌ 활성 프로젝트가 없습니다.")
            return None

        final_path = paths["final"]

        # concat_list.txt가 있으면 그것을 우선 사용 (전환 클립 포함)
        concat_list_file = final_path / "concat_list.txt"
        if concat_list_file.exists():
            print("📝 concat_list.txt 사용 (전환 클립 포함)")
            concat_file = concat_list_file
            # 파일 개수 확인
            with open(concat_file, 'r', encoding='utf-8') as f:
                lines = [l for l in f.readlines() if l.strip()]
            print(f"\n🎬 최종 영상 병합 ({len(lines)}개 클립)")
        else:
            # 기존 방식: scenes.json에서 순서 가져오기
            scene_files = []
            scenes_file = paths["scenes"] / "scenes.json"
            if scenes_file.exists():
                with open(scenes_file, 'r', encoding='utf-8') as f:
                    scenes = json.load(f)
                scene_ids = [s["scene_id"] for s in scenes]
            else:
                # 파일명에서 추출
                all_files = list(final_path.glob("*_final*.mp4"))
                scene_ids = sorted(set(f.stem.split("_")[0] for f in all_files),
                                 key=lambda x: int(x[1:]) if x[1:].isdigit() else 0)

            for scene_id in scene_ids:
                scene_file = final_path / f"{scene_id}_final.mp4"
                if scene_file.exists():
                    scene_files.append(scene_file)

            if not scene_files:
                print("❌ 합성된 씬 파일이 없습니다.")
                print("   먼저 compose-all을 실행하세요.")
                return None

            print(f"\n🎬 최종 영상 병합 ({len(scene_files)}개 씬)")

            # concat 파일 생성
            concat_file = final_path / "final_concat.txt"
            with open(concat_file, 'w', encoding='utf-8') as f:
                for video in scene_files:
                    f.write(f"file '{video.name}'\n")

        # 출력 파일 (절대 경로로 변환)
        output_file = (paths["base"] / "final_video.mp4").resolve()

        # FFmpeg 병합
        # concat_list.txt에서 파일 목록 읽기
        with open(concat_file, 'r', encoding='utf-8') as f:
            video_files = [line.strip().replace("file '", "").replace("'", "")
                          for line in f.readlines() if line.strip()]

        has_transitions = any('t_after_' in f for f in video_files)

        if has_transitions:
            # filter_complex 방식 사용 (전환 클립 포함 시)
            print("  병합 중 (filter_complex)...")
            # 모든 파일을 한번에 처리 (FFmpeg는 많은 입력 처리 가능)
            result = self._merge_with_filter_complex(video_files, output_file, final_path)
        else:
            # 전환 없으면 빠른 concat demuxer 사용
            concat_file_relative = concat_file.name
            cmd = [
                self.ffmpeg_path,
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file_relative,
                "-c", "copy",
                "-y", str(output_file)
            ]
            print("  병합 중...")
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(final_path))

        if result.returncode != 0 or not output_file.exists():
            print(f"  ❌ 병합 실패")
            if result.stderr:
                # FFmpeg 버전 정보가 아닌 실제 오류만 출력
                error_lines = [l for l in result.stderr.split('\n') if 'error' in l.lower() or 'Error' in l]
                if error_lines:
                    print(f"     {error_lines[0][:200]}")
            return None

        # 파일 정보 출력
        probe_cmd = [
            self.ffprobe_path,
            "-v", "error",
            "-show_entries", "format=duration,size",
            "-of", "json",
            str(output_file)
        ]

        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)

        if probe_result.returncode == 0:
            info = json.loads(probe_result.stdout)
            duration = float(info.get("format", {}).get("duration", 0))
            size = int(info.get("format", {}).get("size", 0))

            mins = int(duration // 60)
            secs = int(duration % 60)
            size_mb = size / (1024 * 1024)

            print(f"\n✅ 최종 영상 생성 완료!")
            print(f"   📁 파일: {output_file}")
            print(f"   ⏱️  길이: {mins}분 {secs}초")
            print(f"   💾 크기: {size_mb:.1f} MB")
        else:
            print(f"\n✅ 최종 영상 생성 완료: {output_file}")

        # state.json 업데이트
        self.state.set("current_phase", "completed")
        self.state.set("files.final_video", str(output_file))
        self.state.save()

        return output_file


# ============================================================================
# 유틸리티 함수
# ============================================================================

def convert_to_tts_text(text: str) -> str:
    """
    읽기용 텍스트를 TTS용 텍스트로 변환
    (숫자/기호 → 한글 발음)
    """
    
    # 변환 규칙
    conversions = [
        # 연산자
        (r'×', ' 곱하기 '),
        (r'\*', ' 곱하기 '),
        (r'÷', ' 나누기 '),
        (r'/', ' 나누기 '),
        (r'\+', ' 플러스 '),
        (r'(?<!\w)-(?!\w)', ' 마이너스 '),  # 단독 마이너스만
        (r'=', '는 '),
        
        # 수학 기호
        (r'√', '루트 '),
        (r'²', ' 제곱'),
        (r'³', ' 세제곱'),
        (r'∫', '적분 '),
        (r'Σ', '시그마 '),
        (r'∞', '무한대'),
        (r'π', '파이'),
        (r'θ', '세타'),
        (r'α', '알파'),
        (r'β', '베타'),
        (r'γ', '감마'),
        (r'Δ', '델타'),
        
        # 함수 표기
        (r'f\(x\)', '에프엑스'),
        (r'g\(x\)', '지엑스'),
        (r'h\(x\)', '에이치엑스'),
        (r'dy/dx', '디와이 디엑스'),
        (r'd/dx', '디 디엑스'),
        (r'dx', '디엑스'),
        (r'dy', '디와이'),
        (r'lim', '극한값 '),
        (r'sin', '사인 '),
        (r'cos', '코사인 '),
        (r'tan', '탄젠트 '),
        (r'log', '로그 '),
        (r'ln', '자연로그 '),
        
        # 단위
        (r'cm²', '제곱센티미터'),
        (r'cm', '센티미터'),
        (r'm²', '제곱미터'),
        (r'km', '킬로미터'),
        (r'kg', '킬로그램'),
        
        # 숫자 (두 자리 이상은 그대로)
        (r'\b0\b', '영'),
        (r'\b1\b', '일'),
        (r'\b2\b', '이'),
        (r'\b3\b', '삼'),
        (r'\b4\b', '사'),
        (r'\b5\b', '오'),
        (r'\b6\b', '육'),
        (r'\b7\b', '칠'),
        (r'\b8\b', '팔'),
        (r'\b9\b', '구'),
        (r'\b10\b', '십'),
    ]
    
    result = text
    for pattern, replacement in conversions:
        result = re.sub(pattern, replacement, result)
    
    # 연속 공백 제거
    result = re.sub(r'\s+', ' ', result)
    
    return result.strip()


# ============================================================================
# ValidatorManager - visual.json 검증
# ============================================================================

class ValidatorManager:
    """Visual JSON 검증 매니저 (visual-review.md 기반)"""

    # Manim 색상 상수 목록
    VALID_COLORS = {
        "WHITE", "BLACK", "GRAY", "GRAY_A", "GRAY_B", "GRAY_C", "GRAY_D", "GRAY_E",
        "RED", "RED_A", "RED_B", "RED_C", "RED_D", "RED_E",
        "GREEN", "GREEN_A", "GREEN_B", "GREEN_C", "GREEN_D", "GREEN_E",
        "BLUE", "BLUE_A", "BLUE_B", "BLUE_C", "BLUE_D", "BLUE_E",
        "YELLOW", "YELLOW_A", "YELLOW_B", "YELLOW_C", "YELLOW_D", "YELLOW_E",
        "ORANGE", "PINK", "PURPLE", "TEAL", "GOLD", "MAROON",
        "CYAN", "MAGENTA", "LIGHT_GRAY", "DARK_GRAY", "LIGHT_BROWN", "DARK_BROWN"
    }

    # 타입별 필수 필드
    TYPE_REQUIRED_FIELDS = {
        "ImageMobject": ["source", "size"],
        "SVGMobject": ["source", "size"],
        "Text": ["content", "font_size", "color"],
        "MathTex": ["content", "font_size", "color"],
        "Rectangle": ["width", "height"],
        "Circle": ["radius"],
        "Arrow": ["start", "end"],
        "Axes": ["x_range", "y_range", "x_length", "y_length"],
    }

    # position method별 필수 필드
    POSITION_REQUIRED_FIELDS = {
        "shift": ["x", "y"],
        "to_edge": ["edge"],
        "to_corner": ["corner"],
        "next_to": ["reference", "direction"],
        "move_to": ["reference"],
    }

    def __init__(self, state: StateManager):
        self.state = state
        self.project_id = state.get("project_id")
        self.output_dir = Path(f"output/{self.project_id}")
        self.visual_dir = self.output_dir / "3_visual_prompts"
        self.errors = []
        self.warnings = []
        self.auto_fixed = []

    def validate_all(self, auto_fix: bool = True):
        """모든 visual.json 파일 검증"""
        if not self.project_id:
            print("❌ 활성 프로젝트가 없습니다.")
            return

        if not self.visual_dir.exists():
            print(f"❌ visual_prompts 폴더가 없습니다: {self.visual_dir}")
            return

        # visual 파일 목록
        visual_files = sorted(self.visual_dir.glob("s*_visual.json"))
        if not visual_files:
            print("❌ 검증할 visual.json 파일이 없습니다.")
            return

        print(f"\n🔍 Visual JSON 검증 시작 ({len(visual_files)}개 파일)")
        print("=" * 60)

        total_errors = 0
        total_warnings = 0
        total_fixed = 0
        failed_scenes = []

        for vf in visual_files:
            scene_id = vf.stem.replace("_visual", "")
            self.errors = []
            self.warnings = []
            self.auto_fixed = []

            try:
                with open(vf, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 검증 수행
                self._validate_structure(data)
                self._validate_objects(data)
                self._validate_sequence(data)
                self._validate_3d(data)
                self._validate_timing(data)

                # 자동 수정
                if auto_fix and (self.auto_fixed or self._needs_auto_fix(data)):
                    data = self._apply_auto_fixes(data)
                    with open(vf, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)

                # 결과 출력
                if self.errors:
                    print(f"❌ {scene_id}: {len(self.errors)} 오류, {len(self.warnings)} 경고")
                    for e in self.errors[:3]:  # 최대 3개만 표시
                        print(f"   - [ERROR] {e}")
                    if len(self.errors) > 3:
                        print(f"   ... 외 {len(self.errors) - 3}개 오류")
                    failed_scenes.append(scene_id)
                elif self.warnings:
                    print(f"⚠️  {scene_id}: {len(self.warnings)} 경고")
                    for w in self.warnings[:2]:
                        print(f"   - [WARN] {w}")
                else:
                    print(f"✅ {scene_id}: 통과")

                if self.auto_fixed:
                    print(f"   🔧 자동 수정: {len(self.auto_fixed)}개")
                    total_fixed += len(self.auto_fixed)

                total_errors += len(self.errors)
                total_warnings += len(self.warnings)

            except json.JSONDecodeError as e:
                print(f"❌ {scene_id}: JSON 파싱 오류 - {e}")
                total_errors += 1
                failed_scenes.append(scene_id)
            except Exception as e:
                print(f"❌ {scene_id}: 검증 오류 - {e}")
                total_errors += 1
                failed_scenes.append(scene_id)

        # 최종 요약
        print("\n" + "=" * 60)
        if total_errors == 0:
            print(f"✅ 검증 완료: 모든 {len(visual_files)}개 파일 통과")
        else:
            print(f"❌ 검증 결과: {total_errors} 오류, {total_warnings} 경고")
            print(f"   실패 씬: {', '.join(failed_scenes)}")

        if total_fixed > 0:
            print(f"🔧 자동 수정: 총 {total_fixed}개 항목")

        return total_errors == 0

    def _validate_structure(self, data: dict):
        """구조 검증 - 필수 최상위 필드"""
        required_fields = [
            "scene_id", "is_3d", "scene_class", "style",
            "total_duration", "canvas", "objects", "sequence"
        ]

        for field in required_fields:
            if field not in data:
                self.errors.append(f"필수 필드 누락: {field}")

        # canvas 검증
        if "canvas" in data:
            canvas = data["canvas"]
            if "background" not in canvas:
                self.warnings.append("canvas.background 누락")
            if "safe_margin" not in canvas:
                self.warnings.append("canvas.safe_margin 누락")

        # 배열 타입 확인
        if "objects" in data and not isinstance(data["objects"], list):
            self.errors.append("objects는 배열이어야 함")

        if "sequence" in data and not isinstance(data["sequence"], list):
            self.errors.append("sequence는 배열이어야 함")

    def _validate_objects(self, data: dict):
        """objects 검증"""
        objects = data.get("objects", [])
        ids_seen = set()

        for i, obj in enumerate(objects):
            obj_id = obj.get("id", f"[index {i}]")

            # id 검증
            if "id" not in obj:
                self.errors.append(f"objects[{i}]: id 누락")
            elif obj["id"] in ids_seen:
                self.errors.append(f"objects[{i}]: id '{obj['id']}' 중복")
            else:
                ids_seen.add(obj["id"])

            # type 검증
            if "type" not in obj:
                self.errors.append(f"{obj_id}: type 누락")

            # position 검증
            if "position" not in obj:
                self.warnings.append(f"{obj_id}: position 누락")
            else:
                self._validate_position(obj_id, obj["position"])

            # 타입별 필수 필드
            obj_type = obj.get("type", "")
            if obj_type in self.TYPE_REQUIRED_FIELDS:
                for field in self.TYPE_REQUIRED_FIELDS[obj_type]:
                    # size는 height 또는 width로 대체 가능
                    if field == "size":
                        if "size" not in obj and "height" not in obj.get("size", {}):
                            if not obj.get("size"):
                                self.warnings.append(f"{obj_id}: size 누락")
                    elif field not in obj:
                        self.warnings.append(f"{obj_id}: {field} 누락 ({obj_type} 필수)")

            # 한글 텍스트 폰트 검증
            if obj_type == "Text":
                content = obj.get("content", "")
                if any('\uac00' <= c <= '\ud7a3' for c in content):  # 한글 포함
                    font = obj.get("font", "")
                    if "Noto Sans KR" not in font and "NanumGothic" not in font:
                        self.warnings.append(f"{obj_id}: 한글 텍스트에 font='Noto Sans KR' 권장")

            # 에셋 경로 검증
            if "source" in obj:
                source = obj["source"]
                if not source.startswith("assets/"):
                    self.errors.append(f"{obj_id}: source는 'assets/'로 시작해야 함")
                # 파일 존재 확인
                asset_path = Path(source)
                if not asset_path.exists():
                    self.warnings.append(f"{obj_id}: 에셋 파일 없음: {source}")

            # 색상 검증
            color = obj.get("color", "")
            if color and not color.startswith("#"):  # 헥스 코드가 아닌 경우
                if color not in self.VALID_COLORS:
                    self.warnings.append(f"{obj_id}: 알 수 없는 색상 '{color}'")

    def _validate_position(self, obj_id: str, position: dict):
        """position 검증"""
        method = position.get("method", "shift")

        # method별 필수 필드
        if method in self.POSITION_REQUIRED_FIELDS:
            for field in self.POSITION_REQUIRED_FIELDS[method]:
                if field not in position:
                    self.warnings.append(f"{obj_id}: position.{field} 누락 (method: {method})")

        # 세이프존 검증
        x = position.get("x", 0)
        y = position.get("y", 0)

        if abs(x) > 6.6:
            self.warnings.append(f"{obj_id}: x={x} 화면 밖 (권장: -6.6 ~ 6.6)")
            self.auto_fixed.append((obj_id, "x", max(-6.5, min(6.5, x))))

        if y < -2.5:
            self.warnings.append(f"{obj_id}: y={y} 자막 영역 침범 (권장: y >= -2.5)")
            self.auto_fixed.append((obj_id, "y", -2.3))
        elif y > 3.5:
            self.warnings.append(f"{obj_id}: y={y} 화면 밖 (권장: y <= 3.5)")
            self.auto_fixed.append((obj_id, "y", 3.3))

    def _validate_sequence(self, data: dict):
        """sequence 검증"""
        sequence = data.get("sequence", [])
        objects_ids = {obj.get("id") for obj in data.get("objects", [])}

        prev_end = 0
        for i, step in enumerate(sequence):
            step_num = step.get("step", i + 1)

            # 필수 필드
            if "step" not in step:
                self.warnings.append(f"sequence[{i}]: step 번호 누락")

            if "time_range" not in step:
                self.errors.append(f"step {step_num}: time_range 누락")
            else:
                tr = step["time_range"]
                if len(tr) != 2:
                    self.errors.append(f"step {step_num}: time_range는 [start, end] 형식")
                else:
                    start, end = tr

                    # 시간 연속성
                    if i == 0 and start != 0:
                        self.warnings.append(f"step 1: time_range[0]은 0이어야 함")
                    elif i > 0 and abs(start - prev_end) > 0.01:
                        self.warnings.append(f"step {step_num}: 시간 불연속 ({prev_end} → {start})")

                    prev_end = end

            # actions 검증
            actions = step.get("actions", [])
            if not actions:
                self.warnings.append(f"step {step_num}: actions 비어있음")

            for j, action in enumerate(actions):
                action_type = action.get("type", "")
                target = action.get("target", "")

                # target 참조 확인
                if target and target not in objects_ids:
                    if action_type != "wait":
                        self.errors.append(f"step {step_num}: target '{target}' 미정의")

                # run_time 검증
                if "run_time" not in action and action_type != "wait":
                    self.warnings.append(f"step {step_num}: action[{j}] run_time 누락")

                # Transform 검증
                if action_type in ["Transform", "ReplacementTransform"]:
                    to_target = action.get("to", "")
                    if not to_target:
                        self.errors.append(f"step {step_num}: {action_type}에 'to' 필드 필수")
                    elif to_target not in objects_ids:
                        self.errors.append(f"step {step_num}: Transform to '{to_target}' 미정의")

        # 마지막 step과 total_duration 일치
        total_duration = data.get("total_duration", 0)
        if sequence and prev_end != total_duration:
            diff = abs(prev_end - total_duration)
            if diff > 0.5:
                self.warnings.append(f"sequence 끝({prev_end}s)과 total_duration({total_duration}s) 불일치")

    def _validate_3d(self, data: dict):
        """3D 씬 검증"""
        is_3d = data.get("is_3d", False)
        scene_class = data.get("scene_class", "Scene")

        # 3D 객체 존재 확인
        objects = data.get("objects", [])
        three_d_types = {"Cube", "Cylinder", "Sphere", "Cone", "Surface", "ThreeDAxes"}
        has_3d_objects = any(obj.get("type") in three_d_types for obj in objects)

        if has_3d_objects and not is_3d:
            self.errors.append("3D 객체 사용 시 is_3d: true 필수")

        if is_3d:
            if scene_class != "ThreeDScene":
                self.errors.append("is_3d: true이면 scene_class: 'ThreeDScene' 필수")

            if "camera" not in data:
                self.warnings.append("3D 씬에서 camera 설정 권장")

            # 텍스트/수식 fixed_in_frame 확인
            for obj in objects:
                if obj.get("type") in ["Text", "MathTex"]:
                    if not obj.get("fixed_in_frame", False):
                        self.warnings.append(f"{obj.get('id')}: 3D 씬 텍스트에 fixed_in_frame: true 권장")

    def _validate_timing(self, data: dict):
        """타이밍 검증"""
        total_duration = data.get("total_duration", 0)

        if total_duration <= 0:
            self.errors.append("total_duration은 0보다 커야 함")

        # 씬 길이 권장 범위 (5~30초)
        if total_duration < 5:
            self.warnings.append(f"씬 길이 {total_duration}s가 너무 짧음 (권장: 5초 이상)")
        elif total_duration > 30:
            self.warnings.append(f"씬 길이 {total_duration}s가 너무 김 (권장: 30초 이하)")

    def _needs_auto_fix(self, data: dict) -> bool:
        """자동 수정 필요 여부"""
        return len(self.auto_fixed) > 0

    def _apply_auto_fixes(self, data: dict) -> dict:
        """자동 수정 적용"""
        for obj_id, field, value in self.auto_fixed:
            for obj in data.get("objects", []):
                if obj.get("id") == obj_id:
                    if "position" in obj:
                        obj["position"][field] = value

        return data


def print_help():
    """도움말 출력"""
    help_text = """
╔══════════════════════════════════════════════════════════════════╗
║        수학 교육 영상 제작 파이프라인 v6.4                        ║
║        Claude Code 통합 버전 (gpt-4o-mini-tts)                   ║
╚══════════════════════════════════════════════════════════════════╝

📌 사용법:
    python math_video_pipeline.py <명령어> [옵션]

📋 명령어:

  init          새 프로젝트 초기화
                --title "제목"     영상 제목 (필수)
                --duration 480     길이(초), 기본값 480 (8분)
                --aspect 16:9      종횡비 (16:9 / 9:16)
                --style cyberpunk  스타일 (minimal/cyberpunk/paper/space/geometric/stickman)
                --difficulty intermediate  난이도 (beginner/intermediate/advanced)
                --voice alloy              TTS 음성 (OpenAI)

  status        현재 프로젝트 상태 확인

  list          모든 프로젝트 목록 조회
                output/ 폴더 내 프로젝트 목록과 크기 표시

  delete        프로젝트 삭제
                <project_id>       삭제할 프로젝트 ID (필수)
                --force, -f        확인 없이 삭제

  clean         프로젝트 폴더 내용 정리 (폴더 구조 유지)
                --project, -p      프로젝트 ID (기본: 현재 프로젝트)
                --folders, -d      정리할 폴더 (예: 0_audio 8_renders)
                --force, -f        확인 없이 정리

  reset         프로젝트를 특정 단계로 리셋
                --project, -p      프로젝트 ID (기본: 현재 프로젝트)
                --from             리셋 시작 단계 (예: tts_completed)
                --force, -f        확인 없이 리셋

  tts           단일 씬 TTS 생성
                --scene s1         씬 ID (필수)
                --text "텍스트"    나레이션 텍스트 (필수)

  tts-all       모든 씬 TTS 생성
                (텍스트 소스: 2_narration/ 우선, 없으면 scenes.json)

  narration-extract  씬에서 narration_display 추출 (Narration Designer용)
                     --scenes s1,s2,s3  추출할 씬 ID (쉼표 구분, 생략시 전체)

  narration-check    나레이션 파일 상태 확인
                     (완료/미완료 씬 목록 표시)

  prompts-export    모든 이미지 프롬프트를 하나의 파일로 내보내기
                    → 6_image_prompts/prompts_batch.txt

  images-check      배경 이미지 준비 상태 확인
                    → 9_backgrounds/ 폴더의 이미지 검증

  images-import     외부 폴더에서 이미지 일괄 가져오기
                    --source "폴더경로"  이미지가 있는 폴더 (필수)

  render        단일 씬 렌더링
                --scene s1         씬 ID (필수)
                --quality l        품질 (l/m/h/k)
                --no-preview       미리보기 없이 렌더링

  render-all    모든 씬 렌더링
                --quality l        품질 (l/m/h/k)

  render-collect 렌더링 결과물 수집
                media/videos/에서 8_renders/로 파일 복사
                state.json에 files.renders 업데이트

  render-script 렌더링 스크립트 생성

  subtitle-generate  모든 씬 SRT 자막 생성
                     → 7_subtitles/ 폴더에 s1.srt, s2.srt, ... 생성

  compose       단일 씬 합성 (배경+Manim+오디오+자막)
                --scene s1         씬 ID (필수)
                --no-subtitle      자막 없이 합성

  compose-all   모든 씬 합성
                --no-subtitle      자막 없이 합성

  merge-final   모든 씬을 최종 영상으로 병합
                → final_video.mp4 생성

  convert       텍스트를 TTS용으로 변환
                --text "9×9=81"    변환할 텍스트

  files         프로젝트 파일 목록

  help          이 도움말 표시

🎤 TTS 음성 옵션 (gpt-4o-mini-tts):
  ash        차분한 남성 [기본값] ⭐
  onyx       남성적, 깊은 목소리
  echo       남성적, 차분함
  alloy      중성적, 균형잡힌
  coral      따뜻한 여성
  nova       여성적, 밝고 친근
  marin      고품질 추천
  cedar      고품질 추천

  💡 한국어 발음 개선 + 저렴한 비용 (~$0.015/분)
  🎧 음성 샘플: https://platform.openai.com/docs/guides/text-to-speech

📖 예시:

  # 1. 새 프로젝트 시작
  python math_video_pipeline.py init --title "피타고라스 정리" --duration 480

  # 2. Claude Code에서 대본 작성
  # "skills/script-writer.md 읽고 대본 작성해줘"

  # 3. Claude Code에서 씬 분할
  # "skills/scene-director.md 읽고 씬 분할해줘"

  # 4. 모든 씬 TTS 생성
  python math_video_pipeline.py tts-all

  # 5. Claude Code에서 Manim 코드 생성
  # "skills/manim-coder.md 읽고 s1 코드 생성해줘"

  # 6. 이미지 프롬프트 내보내기
  python math_video_pipeline.py prompts-export

  # 7. 외부에서 이미지 생성 후 가져오기
  python math_video_pipeline.py images-import --source "C:/Downloads/backgrounds"

  # 8. 이미지 검증
  python math_video_pipeline.py images-check

  # 9. 렌더링
  python math_video_pipeline.py render-all

  # 10. 자막 생성
  python math_video_pipeline.py subtitle-generate

  # 11. 모든 씬 합성 (배경+Manim+오디오+자막)
  python math_video_pipeline.py compose-all

  # 12. 최종 영상 병합
  python math_video_pipeline.py merge-final

📁 출력 구조:
  output/{project_id}/
  ├── 0_audio/          TTS 음성 + 타이밍
  ├── 1_script/         대본
  ├── 2_scenes/         씬 분할
  ├── 4_manim_code/     Manim 코드
  ├── 6_image_prompts/  이미지 생성 프롬프트
  ├── 7_subtitles/      자막
  ├── 8_renders/        Manim 렌더링 결과
  ├── 9_backgrounds/    배경 이미지 (외부 생성)
  ├── 10_scene_final/   씬별 합성 영상
  └── final_video.mp4   최종 영상

🖼️ 배경 이미지 파일명 규칙:
  s1_bg.png, s2_bg.png, s3_bg.png, ...
  (씬 ID + _bg.png)

🔄 /clear 가능 지점:
  ✅ 대본 승인 후 (script_approved)
  ✅ 씬 분할 후 (scenes_approved)
  ✅ TTS 완료 후 (tts_completed)
  ✅ 매 3-5씬 코드 완료 후
  ✅ 이미지 준비 완료 후
  
  재개: "계속" 또는 "상태" 입력
"""
    print(help_text)


# ============================================================================
# CLI 메인
# ============================================================================

def main():
    """메인 함수"""
    
    parser = argparse.ArgumentParser(
        description="수학 교육 영상 제작 파이프라인 v6.1",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="명령어")
    
    # init 명령어
    init_parser = subparsers.add_parser("init", help="새 프로젝트 초기화")
    init_parser.add_argument("--title", "-t", required=True, help="영상 제목")
    init_parser.add_argument("--duration", "-d", type=int, default=480, help="영상 길이(초), 기본값 480 (8분)")
    init_parser.add_argument("--style", "-s", default="cyberpunk",
                            choices=["minimal", "cyberpunk", "paper", "space", "geometric", "stickman"],
                            help="시각 스타일")
    init_parser.add_argument("--difficulty", default="intermediate",
                            choices=["beginner", "intermediate", "advanced"],
                            help="난이도")
    init_parser.add_argument("--aspect", default="16:9",
                            choices=["16:9", "9:16"],
                            help="종횡비")
    init_parser.add_argument("--voice", default="alloy",
                            choices=["ash", "alloy", "ballad", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer", "verse", "marin", "cedar"],
                            help="TTS 음성 (OpenAI gpt-4o-mini-tts)")
    
    # status 명령어
    subparsers.add_parser("status", help="현재 상태 확인")

    # list 명령어 (프로젝트 목록)
    subparsers.add_parser("list", help="모든 프로젝트 목록 조회")

    # delete 명령어 (프로젝트 삭제)
    delete_parser = subparsers.add_parser("delete", help="프로젝트 삭제")
    delete_parser.add_argument("project_id", help="삭제할 프로젝트 ID (예: P20250110_143000)")
    delete_parser.add_argument("--force", "-f", action="store_true", help="확인 없이 삭제")

    # clean 명령어 (폴더 내용 정리)
    clean_parser = subparsers.add_parser("clean", help="프로젝트 폴더 내용 정리 (폴더 구조는 유지)")
    clean_parser.add_argument("--project", "-p", help="프로젝트 ID (기본: 현재 프로젝트)")
    clean_parser.add_argument("--folders", "-d", nargs="+", help="정리할 폴더 (예: 0_audio 8_renders)")
    clean_parser.add_argument("--force", "-f", action="store_true", help="확인 없이 정리")

    # reset 명령어 (단계 리셋)
    reset_parser = subparsers.add_parser("reset", help="프로젝트를 특정 단계로 리셋")
    reset_parser.add_argument("--project", "-p", help="프로젝트 ID (기본: 현재 프로젝트)")
    reset_parser.add_argument("--from", dest="from_phase", help="리셋 시작 단계 (예: tts_completed)")
    reset_parser.add_argument("--force", "-f", action="store_true", help="확인 없이 리셋")

    # verify-sync 명령어 (대본-TTS 동기화 검증)
    verify_sync_parser = subparsers.add_parser("verify-sync", help="대본(scenes.json)과 TTS 녹음 동기화 검증")
    verify_sync_parser.add_argument("scene_id", nargs="?", help="씬 ID (예: s7). 생략하면 전체 검증")

    # validate-all 명령어 (visual.json 검증)
    validate_parser = subparsers.add_parser("validate-all", help="모든 visual.json 검증 (visual-review.md 기반)")
    validate_parser.add_argument("--no-fix", action="store_true", help="자동 수정 비활성화")

    # tts 명령어
    tts_parser = subparsers.add_parser("tts", help="단일 씬 TTS 생성")
    tts_parser.add_argument("--scene", "-s", required=True, help="씬 ID")
    tts_parser.add_argument("--text", "-t", required=True, help="나레이션 텍스트")
    tts_parser.add_argument("--voice", "-v", help="TTS 음성 (기본값: 프로젝트 설정)")
    
    # tts-all 명령어
    tts_all_parser = subparsers.add_parser("tts-all", help="모든 씬 TTS 생성")
    tts_all_parser.add_argument("--start-from", "-f", type=int, default=1,
                               help="시작할 씬 번호 (예: 14면 s14부터 시작)")

    # tts-export 명령어 (외부 녹음용 텍스트 내보내기)
    subparsers.add_parser("tts-export", help="외부 녹음용 텍스트 JSON 내보내기")

    # audio-check 명령어 (외부 녹음 파일 확인)
    subparsers.add_parser("audio-check", help="외부 녹음 파일 누락 확인")

    # audio-process 명령어 (외부 녹음 파일 처리)
    subparsers.add_parser("audio-process", help="외부 녹음 파일 Whisper 분석 + timing.json 생성")

    # asset-check 명령어 (Supabase 에셋 체크)
    subparsers.add_parser("asset-check", help="에셋 체크 (Supabase 조회 + 다운로드 + 누락 목록)")

    # asset-sync 명령어 (로컬 → Supabase 업로드)
    subparsers.add_parser("asset-sync", help="에셋 동기화 (로컬 신규 파일 → Supabase 업로드)")

    # catalog-update 명령어 (Supabase → asset-catalog.md)
    subparsers.add_parser("catalog-update", help="에셋 카탈로그 업데이트 (Supabase에서 목록 가져오기)")

    # render 명령어
    render_parser = subparsers.add_parser("render", help="단일 씬 렌더링")
    render_parser.add_argument("--scene", "-s", required=True, help="씬 ID")
    render_parser.add_argument("--quality", "-q", default="l",
                              choices=["l", "m", "h", "k"],
                              help="렌더링 품질")
    render_parser.add_argument("--no-preview", action="store_true",
                              help="미리보기 없이 렌더링")
    
    # render-all 명령어
    render_all_parser = subparsers.add_parser("render-all", help="모든 씬 렌더링")
    render_all_parser.add_argument("--quality", "-q", default="l",
                                   choices=["l", "m", "h", "k"],
                                   help="렌더링 품질")
    
    # render-script 명령어
    subparsers.add_parser("render-script", help="렌더링 스크립트 생성")

    # render-collect 명령어
    subparsers.add_parser("render-collect", help="media/videos/에서 렌더링 결과물 수집하여 8_renders/로 복사")

    # prompts-export 명령어
    subparsers.add_parser("prompts-export", help="모든 이미지 프롬프트를 하나의 파일로 내보내기")
    
    # images-check 명령어
    subparsers.add_parser("images-check", help="배경 이미지 준비 상태 확인")
    
    # images-import 명령어
    images_import_parser = subparsers.add_parser("images-import", help="외부 폴더에서 이미지 일괄 가져오기")
    images_import_parser.add_argument("--source", "-s", required=True, help="이미지가 있는 폴더 경로")
    
    # convert 명령어
    convert_parser = subparsers.add_parser("convert", help="텍스트를 TTS용으로 변환")
    convert_parser.add_argument("--text", "-t", required=True, help="변환할 텍스트")
    
    # files 명령어
    subparsers.add_parser("files", help="프로젝트 파일 목록")

    # help 명령어
    subparsers.add_parser("help", help="도움말 표시")

    # subtitle-generate 명령어
    subparsers.add_parser("subtitle-generate", help="모든 씬 SRT 자막 생성")

    # subtitle-scene 명령어 (개별 씬 자막 생성)
    subtitle_scene_parser = subparsers.add_parser("subtitle-scene", help="단일 씬 SRT 자막 생성")
    subtitle_scene_parser.add_argument("scene_id", help="씬 ID (예: s7)")

    # tts-scene 명령어 (개별 씬 TTS 재생성 - scenes.json에서 텍스트 자동 로드)
    tts_scene_parser = subparsers.add_parser("tts-scene", help="단일 씬 TTS 재생성 (scenes.json에서 텍스트 로드)")
    tts_scene_parser.add_argument("scene_id", help="씬 ID (예: s7)")

    # render-scene 명령어 (개별 씬 렌더링 - 간편 버전)
    render_scene_parser = subparsers.add_parser("render-scene", help="단일 씬 Manim 렌더링")
    render_scene_parser.add_argument("scene_id", help="씬 ID (예: s7)")
    render_scene_parser.add_argument("--quality", "-q", default="l", choices=["l", "m", "h", "k"], help="렌더링 품질")

    # compose-scene 명령어 (개별 씬 합성 - 간편 버전)
    compose_scene_parser = subparsers.add_parser("compose-scene", help="단일 씬 합성")
    compose_scene_parser.add_argument("scene_id", help="씬 ID (예: s7)")
    compose_scene_parser.add_argument("--no-subtitle", action="store_true", help="자막 없이 합성")

    # compose 명령어 (단일 씬)
    compose_parser = subparsers.add_parser("compose", help="단일 씬 합성 (배경+Manim+오디오+자막)")
    compose_parser.add_argument("--scene", "-s", required=True, help="씬 ID (예: s1)")
    compose_parser.add_argument("--no-subtitle", action="store_true", help="자막 없이 합성")

    # compose-all 명령어
    compose_all_parser = subparsers.add_parser("compose-all", help="모든 씬 합성")
    compose_all_parser.add_argument("--no-subtitle", action="store_true", help="자막 없이 합성")

    # transition-generate 명령어
    subparsers.add_parser("transition-generate", help="섹션 전환 클립 생성 + concat_list.txt")

    # merge-final 명령어
    subparsers.add_parser("merge-final", help="모든 씬을 최종 영상으로 병합")

    # split-scenes 명령어
    subparsers.add_parser("split-scenes", help="scenes.json을 개별 씬 파일로 분할 (토큰 절약)")

    # narration-extract 명령어 (Narration Designer용)
    narration_extract_parser = subparsers.add_parser("narration-extract", help="씬에서 narration_display 추출 (Narration Designer용)")
    narration_extract_parser.add_argument("--scenes", "-s", help="추출할 씬 ID (쉼표 구분, 예: s1,s2,s3)")

    # narration-check 명령어 (나레이션 파일 상태 확인)
    subparsers.add_parser("narration-check", help="나레이션 파일 상태 확인")

    args = parser.parse_args()
    
    # 명령어 없으면 도움말
    if not args.command:
        print_help()
        return
    
    # 상태 관리자 초기화
    state = StateManager()
    
    # 명령어 실행
    if args.command == "help":
        print_help()
    
    elif args.command == "init":
        project = ProjectManager(state)
        project.init_project(
            title=args.title,
            duration=args.duration,
            style=args.style,
            difficulty=args.difficulty,
            aspect_ratio=args.aspect,
            voice=args.voice
        )
    
    elif args.command == "status":
        project = ProjectManager(state)
        project.show_status()

    elif args.command == "list":
        project = ProjectManager(state)
        project.list_projects()

    elif args.command == "delete":
        project = ProjectManager(state)
        project.delete_project(args.project_id, force=args.force)

    elif args.command == "clean":
        project = ProjectManager(state)
        project.clean_project(
            project_id=args.project,
            folders=args.folders,
            force=args.force
        )

    elif args.command == "reset":
        project = ProjectManager(state)
        project.reset_project(
            project_id=args.project,
            from_phase=args.from_phase,
            force=args.force
        )

    elif args.command == "verify-sync":
        tts = TTSGenerator(state)
        tts.verify_sync(args.scene_id)

    elif args.command == "validate-all":
        validator = ValidatorManager(state)
        auto_fix = not getattr(args, 'no_fix', False)
        validator.validate_all(auto_fix=auto_fix)

    elif args.command == "tts":
        tts = TTSGenerator(state)
        tts.generate(args.scene, args.text, args.voice)
    
    elif args.command == "tts-all":
        tts = TTSGenerator(state)
        start_from = getattr(args, 'start_from', 1)
        tts.generate_all_from_scenes(start_from=start_from)

    elif args.command == "tts-export":
        tts = TTSGenerator(state)
        tts.export_texts()

    elif args.command == "audio-check":
        tts = TTSGenerator(state)
        tts.check_audio_files()

    elif args.command == "audio-process":
        tts = TTSGenerator(state)
        tts.process_audio_files()

    elif args.command == "asset-check":
        assets = AssetManager(state)
        assets.check_assets()

    elif args.command == "asset-sync":
        assets = AssetManager(state)
        assets.sync_assets()

    elif args.command == "catalog-update":
        assets = AssetManager(state)
        assets.update_catalog()

    elif args.command == "render":
        renderer = RenderManager(state)
        renderer.render_scene(
            args.scene,
            quality=args.quality,
            preview=not args.no_preview
        )
    
    elif args.command == "render-all":
        renderer = RenderManager(state)
        renderer.render_all(quality=args.quality, preview=False)
    
    elif args.command == "render-script":
        renderer = RenderManager(state)
        renderer.generate_render_script()

    elif args.command == "render-collect":
        renderer = RenderManager(state)
        renderer.collect_renders()

    elif args.command == "prompts-export":
        images = ImageManager(state)
        images.export_prompts()
    
    elif args.command == "images-check":
        images = ImageManager(state)
        images.check_images()
    
    elif args.command == "images-import":
        images = ImageManager(state)
        images.import_images(args.source)
    
    elif args.command == "convert":
        result = convert_to_tts_text(args.text)
        print(f"\n입력: {args.text}")
        print(f"변환: {result}")
    
    elif args.command == "files":
        files = FileManager(state)
        file_list = files.list_files()

        if not file_list:
            print("❌ 활성 프로젝트가 없거나 파일이 없습니다.")
        else:
            print("\n📁 프로젝트 파일:")
            for folder, items in sorted(file_list.items()):
                print(f"\n  {folder}/")
                for item in sorted(items):
                    print(f"    - {item}")

    elif args.command == "subtitle-generate":
        composer = ComposerManager(state)
        composer.generate_subtitles()

    elif args.command == "subtitle-scene":
        composer = ComposerManager(state)
        composer.generate_subtitle_for_scene(args.scene_id)

    elif args.command == "tts-scene":
        tts = TTSGenerator(state)
        tts.generate_for_scene(args.scene_id)

    elif args.command == "render-scene":
        renderer = RenderManager(state)
        renderer.render_scene(args.scene_id, quality=args.quality, preview=False)

    elif args.command == "compose-scene":
        composer = ComposerManager(state)
        with_subtitle = not getattr(args, 'no_subtitle', False)
        composer.compose_scene(args.scene_id, with_subtitle=with_subtitle)

    elif args.command == "compose":
        composer = ComposerManager(state)
        with_subtitle = not getattr(args, 'no_subtitle', False)
        composer.compose_scene(args.scene, with_subtitle=with_subtitle)

    elif args.command == "compose-all":
        composer = ComposerManager(state)
        with_subtitle = not getattr(args, 'no_subtitle', False)
        composer.compose_all(with_subtitle=with_subtitle)

    elif args.command == "transition-generate":
        composer = ComposerManager(state)
        composer.transition_generate()

    elif args.command == "merge-final":
        composer = ComposerManager(state)
        composer.merge_final()

    elif args.command == "split-scenes":
        scene_splitter = SceneSplitter(state)
        scene_splitter.split()

    elif args.command == "narration-extract":
        extractor = NarrationExtractor(state)
        scene_ids = None
        if hasattr(args, 'scenes') and args.scenes:
            scene_ids = [s.strip() for s in args.scenes.split(',')]
        extractor.extract(scene_ids)

    elif args.command == "narration-check":
        extractor = NarrationExtractor(state)
        extractor.check_narrations()

    else:
        print(f"❌ 알 수 없는 명령어: {args.command}")
        print("   python math_video_pipeline.py help 로 도움말을 확인하세요.")


# ============================================================================
# 진입점
# ============================================================================

if __name__ == "__main__":
    main()


