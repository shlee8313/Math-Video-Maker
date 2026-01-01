
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

# TTS 설정 (OpenAI TTS)
TTS_CONFIG = {
    "voices": {
        "alloy": "중성적, 균형잡힌 (기본값)",
        "echo": "남성적, 차분함",
        "fable": "영국식 억양",
        "onyx": "남성적, 깊은 목소리",
        "nova": "여성적, 밝고 친근",
        "shimmer": "여성적, 부드러움"
    },
    "default_voice": "onyx",
    "model": "tts-1-hd",
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


# ============================================================================
# TTS 생성기 클래스
# ============================================================================

class TTSGenerator:
    """OpenAI TTS - 문장별 분할 생성"""

    # OpenAI TTS 지원 음성
    OPENAI_VOICES = {
        "alloy": "중성적, 균형잡힌 (기본값)",
        "echo": "남성적, 차분함",
        "fable": "영국식 억양",
        "onyx": "남성적, 깊은 목소리",
        "nova": "여성적, 밝고 친근",
        "shimmer": "여성적, 부드러움",
    }

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

    def _generate_openai_tts(self, text: str, voice: str, output_file: Path, max_retries: int = 3) -> bool:
        """OpenAI TTS로 음성 생성 (MP3 출력)"""
        import time

        for attempt in range(max_retries):
            try:
                response = self.openai_client.audio.speech.create(
                    model="tts-1-hd",  # 고품질 모델
                    voice=voice,
                    input=text,
                    response_format="mp3"
                )

                # MP3 파일로 저장
                mp3_file = output_file.with_suffix('.mp3')
                response.stream_to_file(str(mp3_file))

                # 성공 후 짧은 대기 (Rate limit 방지)
                time.sleep(0.5)
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
        return "onyx"  # 기본값

    def generate(
        self,
        scene_id: str,
        text: str,
        voice: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """OpenAI TTS - 문장별 음성 생성"""

        if not self.openai_client:
            print("❌ OpenAI 클라이언트를 초기화할 수 없습니다.")
            print("   .env 파일에 OPENAI_API_KEY를 설정하세요.")
            return None

        project_dir = OUTPUT_DIR / self.state.get("project_id", "unknown")
        audio_dir = project_dir / "0_audio"
        audio_dir.mkdir(parents=True, exist_ok=True)

        # 음성 설정 (기본값: onyx)
        voice_setting = voice or self.state.get("settings.voice", "onyx")
        voice_name = self._extract_voice_name(voice_setting)

        print(f"\n🎤 [{scene_id}] TTS 생성 중... (OpenAI)")
        print(f"   음성: {voice_name}")

        # 텍스트를 문장 단위로 분할
        sentences = self._split_into_sentences(text)
        print(f"   문장 수: {len(sentences)}개")

        sentence_results = []
        total_duration = 0.0
        audio_files = []

        for idx, sentence in enumerate(sentences, 1):
            sentence_id = f"{scene_id}_{idx}"
            audio_file = audio_dir / f"{sentence_id}.mp3"

            # 문장 미리보기 (너무 길면 자름)
            preview = sentence[:40] + "..." if len(sentence) > 40 else sentence
            print(f"      [{idx}/{len(sentences)}] {preview}")

            # OpenAI TTS 생성
            success = self._generate_openai_tts(sentence, voice_name, audio_file)

            if success:
                duration = self._get_mp3_duration(audio_file)
                sentence_results.append({
                    "sentence_id": sentence_id,
                    "sentence_index": idx,
                    "text": sentence,
                    "audio_file": str(audio_file),
                    "start": total_duration,
                    "end": total_duration + duration,
                    "duration": duration
                })
                audio_files.append(str(audio_file))
                total_duration += duration
                print(f"         ✅ {duration:.2f}초")
            else:
                print(f"         ❌ 실패")

        if not sentence_results:
            return None

        # 타이밍 JSON 저장
        timing_file = audio_dir / f"{scene_id}_timing.json"
        timing_data = {
            "scene_id": scene_id,
            "voice": voice_name,
            "total_duration": total_duration,
            "sentence_count": len(sentence_results),
            "sentences": sentence_results,
            "audio_files": audio_files,
            "created_at": datetime.now().isoformat()
        }

        with open(timing_file, 'w', encoding='utf-8') as f:
            json.dump(timing_data, f, ensure_ascii=False, indent=2)

        print(f"   ✅ 완료: {len(sentence_results)}개 문장, 총 {total_duration:.2f}초")

        # state에 오디오 파일 추가
        for af in audio_files:
            self.state.add_file("audio", af)

        return timing_data
    
    def generate_all_from_scenes(self, start_from: int = 1) -> List[Dict[str, Any]]:
        """scenes.json의 모든 씬에 대해 TTS 생성 (문장별)

        Args:
            start_from: 시작할 씬 번호 (1부터 시작, 예: 14면 s14부터 시작)
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
            scenes = data.get("scenes", [])
        if not scenes:
            print("❌ 씬이 없습니다.")
            return []

        print(f"\n🎬 총 {len(scenes)}개 씬 TTS 생성 시작 (OpenAI TTS)")
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

            text = scene.get("narration_tts") or scene.get("narration_display", "")

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

    def export_texts(self) -> Optional[Path]:
        """외부 녹음용 텍스트 JSON 내보내기

        scenes.json에서 모든 씬의 narration_tts를 문장별로 분리하여
        0_audio/tts_texts.json으로 내보냅니다.

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

        # 문장별 텍스트 수집
        tts_texts = {}
        total_sentences = 0

        print(f"🎙️ 외부 녹음용 텍스트 내보내기")
        print("=" * 60)

        for scene in scenes:
            scene_id = scene.get("scene_id", "")
            narration_tts = scene.get("narration_tts", "")

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

                sentence_results.append({
                    "index": sent["index"],
                    "text": sent["text"],
                    "file": f"{key}.{file_ext}",
                    "start": round(current_time, 3),
                    "end": round(current_time + duration, 3),
                    "duration": round(duration, 3)
                })

                audio_files.append(f"{key}.{file_ext}")
                all_audio_files.append(f"{key}.{file_ext}")
                current_time += duration

                print(f"   {key}: {duration:.2f}초")

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
        
        scenes = data.get("scenes", [])
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
        """스타일별 이미지 프롬프트 생성"""
        
        # 스타일별 기본 프롬프트
        style_prompts = {
            "minimal": {
                "base": "minimalist mathematical background, clean dark gradient from black center to deep gray edges",
                "accent": "subtle geometric pattern",
                "equation_color": "bright yellow and white"
            },
            "cyberpunk": {
                "base": "cyberpunk mathematical background, dark futuristic scene with neon cyan and magenta accents, digital grid",
                "accent": "holographic glow effects, circuit patterns",
                "equation_color": "bright cyan and magenta"
            },
            "paper": {
                "base": "vintage paper texture background, warm beige to cream gradient, subtle paper grain",
                "accent": "aged parchment feel, soft edges",
                "equation_color": "dark ink, handwritten style"
            },
            "space": {
                "base": "deep space background, cosmic scene with distant stars and nebula in dark purple and blue",
                "accent": "galaxy swirls, stellar glow",
                "equation_color": "bright white and yellow"
            },
            "geometric": {
                "base": "geometric pattern background, symmetrical mathematical shapes, golden ratio spiral",
                "accent": "sacred geometry, precise lines",
                "equation_color": "gold and white"
            },
            "stickman": {
                "base": "dark colorful background gradient from deep blue to purple, clean and simple",
                "accent": "subtle playful elements, friendly atmosphere",
                "equation_color": "bright white and yellow"
            }
        }
        
        config = style_prompts.get(style, style_prompts["cyberpunk"])
        
        # 종횡비 텍스트
        ratio_text = "16:9 widescreen horizontal" if aspect_ratio == "16:9" else "9:16 vertical portrait mobile"
        
        prompt = f"""{config['base']},
{config['accent']},
mathematical education video background,
no text, no letters, no numbers, no Korean, no equations,
center area bright and clean for overlay,
edges darker with subtle accents,
suitable for {config['equation_color']} mathematical equations overlay,
{ratio_text} ratio,
high contrast, professional education aesthetic,
8K quality, sharp details

Negative prompt: text, letters, numbers, words, Korean, Chinese, Japanese, equations, formulas, mathematical symbols, writing, watermark, logo, signature, blurry, low quality, pixelated, faces, people, hands"""

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
        
        scenes = data.get("scenes", [])
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
        
        scenes = data.get("scenes", [])
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
        
        # 모두 성공하면 완료 상태로 업데이트
        if success_count == len(results):
            renders_dir = project_dir / "8_renders"
            self.state.update_completed(str(renders_dir))
        
        return results
    
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


def print_help():
    """도움말 출력"""
    help_text = """
╔══════════════════════════════════════════════════════════════════╗
║        수학 교육 영상 제작 파이프라인 v6.3                        ║
║        Claude Code 통합 버전 (OpenAI TTS)                        ║
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

  tts           단일 씬 TTS 생성
                --scene s1         씬 ID (필수)
                --text "텍스트"    나레이션 텍스트 (필수)

  tts-all       모든 씬 TTS 생성 (scenes.json 기반)

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

  render-script 렌더링 스크립트 생성

  convert       텍스트를 TTS용으로 변환
                --text "9×9=81"    변환할 텍스트

  files         프로젝트 파일 목록

  help          이 도움말 표시

🎤 TTS 음성 옵션 (OpenAI TTS):
  alloy      중성적, 균형잡힌
  echo       남성적, 차분함
  fable      영국식 억양
  onyx       남성적, 깊은 목소리 [기본값]
  nova       여성적, 밝고 친근
  shimmer    여성적, 부드러움

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
    init_parser.add_argument("--voice", default="onyx",
                            choices=["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
                            help="TTS 음성 (OpenAI)")
    
    # status 명령어
    subparsers.add_parser("status", help="현재 상태 확인")
    
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
    
    else:
        print(f"❌ 알 수 없는 명령어: {args.command}")
        print("   python math_video_pipeline.py help 로 도움말을 확인하세요.")


# ============================================================================
# 진입점
# ============================================================================

if __name__ == "__main__":
    main()


