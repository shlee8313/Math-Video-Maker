
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
# OpenAI 및 Google Cloud TTS 클라이언트 초기화
# ============================================================================

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  OpenAI 라이브러리가 설치되지 않았습니다 (Whisper용).")
    print("   설치: pip install openai")

try:
    from google.cloud import texttospeech
    GOOGLE_TTS_AVAILABLE = True
except ImportError:
    GOOGLE_TTS_AVAILABLE = False
    print("⚠️  Google Cloud TTS 라이브러리가 설치되지 않았습니다.")
    print("   설치: pip install google-cloud-texttospeech")


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


# ============================================================================
# 설정 및 상수
# ============================================================================

# 프로젝트 루트 (이 스크립트가 있는 디렉토리)
PROJECT_ROOT = Path(__file__).parent.resolve()

# 주요 경로
STATE_FILE = PROJECT_ROOT / "state.json"
OUTPUT_DIR = PROJECT_ROOT / "output"
SKILLS_DIR = PROJECT_ROOT / "skills"

# TTS 설정 (Google Cloud TTS - Chirp 3 HD 포함)
TTS_CONFIG = {
    "voices": {
        # 기존 Neural2/Wavenet/Standard 성우
        "ko-KR-Neural2-A": "여성 (차분함)",
        "ko-KR-Neural2-B": "여성 (밝음)",
        "ko-KR-Neural2-C": "남성 (또렷함)",
        "ko-KR-Wavenet-A": "여성 (자연스러움)",
        "ko-KR-Wavenet-C": "남성 (자연스러움)",
        "ko-KR-Standard-A": "여성 (비용 절약)",
        "ko-KR-Standard-C": "남성 (비용 절약)",
        # Chirp 3 HD 성우 (고품질 스트리밍)
        "ko-KR-Chirp3-HD-Charon": "남성 (중저음, 신뢰감) [HD]",
        "ko-KR-Chirp3-HD-Aoede": "여성 (차분함, 지적임) [HD]",
        "ko-KR-Chirp3-HD-Kore": "여성 (밝음, 생기) [HD]",
        "ko-KR-Chirp3-HD-Puck": "남성 (장난기, 에너지) [HD]"
    },
    "default_voice": "ko-KR-Chirp3-HD-Charon",
    "language_code": "ko-KR",
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
    """Google Cloud TTS - Chirp 3 HD 스트리밍 + 기존 API 지원"""

    def __init__(self, state_manager: StateManager):
        self.state = state_manager
        self.tts_client = get_google_tts_client()
        self.openai_client = get_openai_client()
    
    def _is_chirp_hd_voice(self, voice_name: str) -> bool:
        """Chirp 3 HD 성우인지 확인"""
        return "Chirp3-HD" in voice_name
    
    def generate(
        self,
        scene_id: str,
        text: str,
        voice: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """TTS 음성 생성 + Whisper 타이밍 측정"""

        if not self.tts_client:
            print("❌ Google TTS 클라이언트를 초기화할 수 없습니다.")
            return None

        if not self.openai_client:
            print("❌ OpenAI 클라이언트를 초기화할 수 없습니다 (Whisper 타이밍 분석용).")
            return None
        
        project_dir = OUTPUT_DIR / self.state.get("project_id", "unknown")
        audio_dir = project_dir / "0_audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        
        # 음성 설정
        if voice is None:
            voice = self.state.get("settings.voice", TTS_CONFIG["default_voice"])
        
        audio_file = audio_dir / f"{scene_id}_audio.mp3"
        timing_file = audio_dir / f"{scene_id}_timing.json"
        
        print(f"\n🎤 [{scene_id}] TTS 생성 중...")
        print(f"   텍스트: {text[:50]}..." if len(text) > 50 else f"   텍스트: {text}")
        print(f"   음성: {voice}")
        
        try:
            # Chirp 3 HD vs 기존 API 분기
            if self._is_chirp_hd_voice(voice):
                print(f"   🌟 Chirp 3 HD 스트리밍 모드")
                self._generate_chirp_hd(audio_file, text, voice)
            else:
                print(f"   📢 기존 Neural2/Wavenet 모드")
                self._generate_standard(audio_file, text, voice)
            
            print(f"   ✅ 음성 파일: {audio_file.name}")

        except Exception as e:
            print(f"   ❌ TTS 생성 실패: {e}")
            return None
        
        # Step 2: Whisper 타이밍 분석
        print(f"   ⏱️  Whisper 타이밍 분석 중...")

        try:
            with open(audio_file, "rb") as f:
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    response_format="verbose_json",
                    timestamp_granularities=["word"]
                )
            
            words = []
            if hasattr(transcript, 'words') and transcript.words:
                for w in transcript.words:
                    words.append({
                        "word": w.word,
                        "start": w.start,
                        "end": w.end,
                        "duration": round(w.end - w.start, 3)
                    })
            
            timing_data = {
                "scene_id": scene_id,
                "audio_file": str(audio_file),
                "actual_duration": transcript.duration,
                "full_text": transcript.text,
                "input_text": text,
                "word_count": len(words),
                "words": words,
                "voice": voice,
                "is_chirp_hd": self._is_chirp_hd_voice(voice),
                "created_at": datetime.now().isoformat()
            }
            
            with open(timing_file, 'w', encoding='utf-8') as f:
                json.dump(timing_data, f, ensure_ascii=False, indent=2)
            
            print(f"   ✅ 실제 음성 길이: {transcript.duration:.2f}초")
            print(f"   ✅ 단어 수: {len(words)}개")
            
            self.state.add_file("audio", str(audio_file))
            return timing_data
            
        except Exception as e:
            print(f"   ⚠️  Whisper 분석 실패: {e}")
            estimated_duration = len(text) / 5
            
            timing_data = {
                "scene_id": scene_id,
                "audio_file": str(audio_file),
                "actual_duration": estimated_duration,
                "full_text": text,
                "input_text": text,
                "word_count": len(text.split()),
                "words": [],
                "voice": voice,
                "is_chirp_hd": self._is_chirp_hd_voice(voice),
                "estimated": True,
                "created_at": datetime.now().isoformat()
            }
            
            with open(timing_file, 'w', encoding='utf-8') as f:
                json.dump(timing_data, f, ensure_ascii=False, indent=2)
            
            self.state.add_file("audio", str(audio_file))
            return timing_data
    
    def _generate_chirp_hd(self, audio_file: Path, text: str, voice: str) -> None:
        """Chirp 3 HD 스트리밍 TTS 생성"""
        
        streaming_config = texttospeech.StreamingSynthesizeConfig(
            voice=texttospeech.VoiceSelectionParams(
                name=voice,
                language_code=TTS_CONFIG["language_code"],
            )
        )
        
        def request_generator():
            yield texttospeech.StreamingSynthesizeRequest(streaming_config=streaming_config)
            yield texttospeech.StreamingSynthesizeRequest(
                input=texttospeech.StreamingSynthesisInput(text=text)
            )
        
        responses = self.tts_client.streaming_synthesize(request_generator())
        
        with open(audio_file, "wb") as out:
            for response in responses:
                out.write(response.audio_content)
    
    def _generate_standard(self, audio_file: Path, text: str, voice: str) -> None:
        """기존 Neural2/Wavenet TTS 생성 (SSML 지원)"""
        
        synthesis_input = texttospeech.SynthesisInput(
            ssml=f"<speak>{text}</speak>"
        )

        voice_params = texttospeech.VoiceSelectionParams(
            language_code=TTS_CONFIG["language_code"],
            name=voice
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = self.tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice_params,
            audio_config=audio_config
        )

        with open(audio_file, "wb") as out:
            out.write(response.audio_content)
    
    def generate_all_from_scenes(self) -> List[Dict[str, Any]]:
        """scenes.json의 모든 씬에 대해 TTS 생성"""
        # 이 메서드는 기존과 동일 - 변경 없음
        project_id = self.state.get("project_id", "unknown")
        project_dir = OUTPUT_DIR / project_id
        scenes_file = project_dir / "2_scenes" / "scenes.json"
        
        if not scenes_file.exists():
            print(f"❌ 씬 파일이 없습니다: {scenes_file}")
            return []
        
        with open(scenes_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        scenes = data.get("scenes", [])
        if not scenes:
            print("❌ 씬이 없습니다.")
            return []
        
        print(f"\n🎬 총 {len(scenes)}개 씬 TTS 생성 시작")
        print("="*60)
        
        results = []
        audio_files = []
        
        for i, scene in enumerate(scenes, 1):
            scene_id = scene.get("scene_id", f"s{i}")
            text = scene.get("narration_tts") or scene.get("narration_display", "")
            
            if not text:
                print(f"\n⚠️  [{scene_id}] 나레이션 텍스트가 없습니다. 건너뜁니다.")
                continue
            
            print(f"\n[{i}/{len(scenes)}] {scene_id}")
            result = self.generate(scene_id, text)
            
            if result:
                results.append(result)
                audio_files.append(result["audio_file"])
        
        print("\n" + "="*60)
        print(f"✅ TTS 생성 완료: {len(results)}/{len(scenes)}개")
        
        if results:
            self.state.update_tts_completed(project_id, audio_files)
        
        return results
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
        (r'\+', ' 더하기 '),
        (r'(?<!\w)-(?!\w)', ' 빼기 '),  # 단독 마이너스만
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
║        수학 교육 영상 제작 파이프라인 v6.2                        ║
║        Claude Code 통합 버전 (Google Cloud TTS)                  ║
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
                --voice ko-KR-Neural2-C    TTS 음성

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

🎤 TTS 음성 옵션 (Google Cloud TTS):
  ko-KR-Neural2-A    여성 (차분함)
  ko-KR-Neural2-B    여성 (밝음)
  ko-KR-Neural2-C    남성 (또렷함) [기본값]
  ko-KR-Wavenet-A    여성 (자연스러움)
  ko-KR-Wavenet-C    남성 (자연스러움)
  ko-KR-Standard-A   여성 (비용 절약)
  ko-KR-Standard-C   남성 (비용 절약)

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
    init_parser.add_argument("--voice", default="ko-KR-Chirp3-HD-Charon",
                            choices=[
                                # Chirp 3 HD (권장)
                                "ko-KR-Chirp3-HD-Charon",
                                "ko-KR-Chirp3-HD-Aoede",
                                "ko-KR-Chirp3-HD-Kore",
                                "ko-KR-Chirp3-HD-Puck",
                                # 기존 Neural2/Wavenet/Standard
                                "ko-KR-Neural2-A", 
                                "ko-KR-Neural2-B", 
                                "ko-KR-Neural2-C",
                                "ko-KR-Wavenet-A", 
                                "ko-KR-Wavenet-C",
                                "ko-KR-Standard-A",
                                "ko-KR-Standard-C"
                            ],
                            help="TTS 음성 (Chirp 3 HD 권장)")
    
    # status 명령어
    subparsers.add_parser("status", help="현재 상태 확인")
    
    # tts 명령어
    tts_parser = subparsers.add_parser("tts", help="단일 씬 TTS 생성")
    tts_parser.add_argument("--scene", "-s", required=True, help="씬 ID")
    tts_parser.add_argument("--text", "-t", required=True, help="나레이션 텍스트")
    tts_parser.add_argument("--voice", "-v", help="TTS 음성 (기본값: 프로젝트 설정)")
    
    # tts-all 명령어
    subparsers.add_parser("tts-all", help="모든 씬 TTS 생성")
    
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
        tts.generate_all_from_scenes()
    
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



# #!/usr/bin/env python3
# """
# 수학 교육 영상 제작 자동화 파이프라인 v5.0
# - Skills 폴더 실제 참조
# - OpenAI TTS + Whisper 타이밍 측정
# - 완전 대화형
# - 음성 길이 기준 Manim 코드 생성
# """

# import json
# import os
# import re
# import sys
# from datetime import datetime
# from pathlib import Path
# from typing import List, Dict, Optional
# import time

# # OpenAI 설치 확인
# try:
#     import openai
#     from openai import OpenAI
# except ImportError:
#     print("❌ OpenAI 라이브러리가 설치되지 않았습니다.")
#     print("설치: pip install openai")
#     sys.exit(1)

# # 환경변수에서 API 키 로드
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# if not OPENAI_API_KEY:
#     print("⚠️  OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
#     print(".env 파일에 OPENAI_API_KEY=sk-... 를 추가하거나")
#     print("export OPENAI_API_KEY=sk-... 로 설정하세요.")
#     OPENAI_API_KEY = input("또는 여기에 API 키를 입력하세요: ").strip()

# # OpenAI 클라이언트 초기화
# client = OpenAI(api_key=OPENAI_API_KEY)


# # ========== Skill 로더 ==========
# class SkillLoader:
#     """Skills 폴더에서 가이드라인 로드"""
    
#     SKILLS_DIR = Path("skills")
    
#     @classmethod
#     def load(cls, skill_name: str) -> str:
#         """Skill 가이드라인 로드"""
#         skill_file = cls.SKILLS_DIR / f"{skill_name}.md"
        
#         if not skill_file.exists():
#             print(f"⚠️  스킬 파일을 찾을 수 없습니다: {skill_file}")
#             return ""
        
#         try:
#             with open(skill_file, 'r', encoding='utf-8') as f:
#                 content = f.read()
#             print(f"✅ Skill 로드: {skill_name}.md ({len(content)}자)")
#             return content
#         except Exception as e:
#             print(f"❌ Skill 로드 실패 ({skill_name}): {e}")
#             return ""
    
#     @classmethod
#     def extract_section(cls, content: str, section_title: str) -> str:
#         """특정 섹션 추출"""
#         # ## 섹션명 찾기
#         pattern = rf"##\s+{re.escape(section_title)}.*?\n(.*?)(?=\n##|\Z)"
#         match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        
#         if match:
#             return match.group(1).strip()
#         return ""
    
#     @classmethod
#     def extract_examples(cls, content: str) -> List[str]:
#         """예시 코드 블록 추출"""
#         # ```python ... ``` 블록 찾기
#         pattern = r"```(?:python)?\n(.*?)\n```"
#         matches = re.findall(pattern, content, re.DOTALL)
#         return matches


# # ========== 설정 클래스 ==========
# class Config:
#     """프로젝트 설정"""
    
#     def __init__(
#         self,
#         title: str,
#         background_style: str,
#         voice_style: str,
#         font_style: str,
#         subtitle_style: str,
#         difficulty: str,
#         aspect_ratio: str,
#         duration: int
#     ):
#         self.title = title
#         self.background_style = background_style
#         self.voice_style = voice_style
#         self.font_style = font_style
#         self.subtitle_style = subtitle_style
#         self.difficulty = difficulty
#         self.aspect_ratio = aspect_ratio
#         self.duration = duration
        
#         self.project_id = self._generate_project_id()
#         self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
#         # 컬러 팔레트
#         self.color_palette = {
#             "variable": "YELLOW",
#             "constant": "ORANGE",
#             "result": "GREEN",
#             "auxiliary": "GRAY_B",
#             "emphasis": "RED"
#         }
        
#         # 스타일별 설정
#         self.style_config = {
#             "minimal": {
#                 "glow": False,
#                 "flash_frequency": "low",
#                 "primary_color": "WHITE",
#                 "background_color": "BLACK"
#             },
#             "cyberpunk": {
#                 "glow": True,
#                 "flash_frequency": "high",
#                 "primary_color": "CYAN",
#                 "background_color": "#0a0a0a"
#             },
#             "paper": {
#                 "glow": False,
#                 "flash_frequency": "medium",
#                 "primary_color": "BLACK",
#                 "background_color": "#f5f5dc"
#             },
#             "space": {
#                 "glow": True,
#                 "flash_frequency": "medium",
#                 "primary_color": "BLUE",
#                 "background_color": "#000011"
#             },
#             "geometric": {
#                 "glow": False,
#                 "flash_frequency": "medium",
#                 "primary_color": "GOLD",
#                 "background_color": "#1a1a1a"
#             }
#         }
        
#         # OpenAI TTS 설정
#         self.tts_config = {
#             "model": "tts-1-hd",
#             "voice": self._map_voice_style(voice_style),
#             "speed": 1.0
#         }
    
#     def _generate_project_id(self) -> str:
#         """프로젝트 ID 생성"""
#         return f"P{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
#     def _map_voice_style(self, style: str) -> str:
#         """성우 스타일 → OpenAI 음성 매핑"""
#         mapping = {
#             "calm": "alloy",      # 차분한
#             "energetic": "echo",  # 열정적
#             "friendly": "nova"    # 친근한
#         }
#         return mapping.get(style, "alloy")
    
#     def get_style_config(self) -> dict:
#         """현재 스타일 설정 반환"""
#         return self.style_config.get(self.background_style, self.style_config["cyberpunk"])


# # ========== 대화형 설정 수집 ==========
# class InteractiveSetup:
#     """사용자로부터 모든 설정 수집"""
    
#     def __init__(self):
#         self.title = ""
#         self.background_style = ""
#         self.voice_style = ""
#         self.font_style = ""
#         self.subtitle_style = ""
#         self.difficulty = ""
#         self.aspect_ratio = ""
#         self.duration = 0
    
#     def run(self) -> Config:
#         """전체 설정 프로세스 실행"""
#         print("="*70)
#         print("🎬 수학 교육 영상 제작 파이프라인 v5.0")
#         print("   (Skills 통합 + OpenAI TTS + Whisper)")
#         print("="*70)
#         print()
        
#         # 1. 제목
#         self._input_title()
        
#         # 2. 스타일 설정
#         self._input_styles()
        
#         # 3. 분량
#         self._input_duration()
        
#         # 4. 확인
#         if not self._confirm_settings():
#             return self._modify_settings()
        
#         # Config 객체 생성
#         config = Config(
#             title=self.title,
#             background_style=self.background_style,
#             voice_style=self.voice_style,
#             font_style=self.font_style,
#             subtitle_style=self.subtitle_style,
#             difficulty=self.difficulty,
#             aspect_ratio=self.aspect_ratio,
#             duration=self.duration
#         )
        
#         return config
    
#     def _input_title(self):
#         """제목 입력"""
#         print("📝 1단계: 제목")
#         print("-"*70)
#         self.title = input("영상 제목을 입력하세요: ").strip()
        
#         while not self.title:
#             print("❌ 제목은 필수입니다.")
#             self.title = input("영상 제목을 입력하세요: ").strip()
        
#         print(f"✅ 제목: {self.title}\n")
    
#     def _input_styles(self):
#         """스타일 설정"""
#         print("🎨 2단계: 스타일 설정")
#         print("-"*70)
        
#         # 배경 이미지 스타일
#         print("\n📐 배경 이미지 스타일:")
#         bg_styles = {
#             "1": ("minimal", "미니멀 (깔끔한 그라데이션)"),
#             "2": ("cyberpunk", "사이버펑크 (네온 + 글로우)"),
#             "3": ("paper", "종이 질감 (따뜻한 베이지)"),
#             "4": ("space", "우주 (별과 은하)"),
#             "5": ("geometric", "기하학 (수학적 패턴)")
#         }
#         for key, (_, desc) in bg_styles.items():
#             print(f"  {key}. {desc}")
        
#         bg_choice = self._get_choice("배경 스타일을 선택하세요 (1-5)", list(bg_styles.keys()), "2")
#         self.background_style = bg_styles[bg_choice][0]
#         print(f"✅ 배경: {bg_styles[bg_choice][1]}")
        
#         # 성우 스타일
#         print("\n🎤 성우 스타일:")
#         voice_styles = {
#             "1": ("calm", "차분한 선생님 (alloy)"),
#             "2": ("energetic", "열정적인 강사 (echo)"),
#             "3": ("friendly", "친근한 친구 (nova)")
#         }
#         for key, (_, desc) in voice_styles.items():
#             print(f"  {key}. {desc}")
        
#         voice_choice = self._get_choice("성우 스타일을 선택하세요 (1-3)", list(voice_styles.keys()), "1")
#         self.voice_style = voice_styles[voice_choice][0]
#         print(f"✅ 성우: {voice_styles[voice_choice][1]}")
        
#         # 폰트 스타일
#         print("\n✍️  폰트 스타일:")
#         font_styles = {
#             "1": ("handwriting", "손글씨 느낌"),
#             "2": ("sans-serif", "깔끔한 산세리프"),
#             "3": ("serif", "클래식 세리프")
#         }
#         for key, (_, desc) in font_styles.items():
#             print(f"  {key}. {desc}")
        
#         font_choice = self._get_choice("폰트 스타일을 선택하세요 (1-3)", list(font_styles.keys()), "1")
#         self.font_style = font_styles[font_choice][0]
#         print(f"✅ 폰트: {font_styles[font_choice][1]}")
        
#         # 자막 스타일
#         print("\n📺 자막 스타일:")
#         subtitle_styles = {
#             "1": ("fixed", "하단 고정형 (Level 1)"),
#             "2": ("karaoke", "카라오케형 (Level 3)"),
#             "3": ("formula", "수식 연동형 (Level 4)")
#         }
#         for key, (_, desc) in subtitle_styles.items():
#             print(f"  {key}. {desc}")
        
#         sub_choice = self._get_choice("자막 스타일을 선택하세요 (1-3)", list(subtitle_styles.keys()), "2")
#         self.subtitle_style = subtitle_styles[sub_choice][0]
#         print(f"✅ 자막: {subtitle_styles[sub_choice][1]}")
        
#         # 난이도
#         print("\n📊 난이도:")
#         difficulties = {
#             "1": ("beginner", "입문 (Beginner)"),
#             "2": ("intermediate", "중급 (Intermediate)"),
#             "3": ("advanced", "고급 (Advanced)")
#         }
#         for key, (_, desc) in difficulties.items():
#             print(f"  {key}. {desc}")
        
#         diff_choice = self._get_choice("난이도를 선택하세요 (1-3)", list(difficulties.keys()), "2")
#         self.difficulty = difficulties[diff_choice][0]
#         print(f"✅ 난이도: {difficulties[diff_choice][1]}")
        
#         # 종횡비
#         print("\n📐 종횡비:")
#         aspects = {
#             "1": ("16:9", "16:9 (YouTube)"),
#             "2": ("9:16", "9:16 (Shorts)")
#         }
#         for key, (_, desc) in aspects.items():
#             print(f"  {key}. {desc}")
        
#         aspect_choice = self._get_choice("종횡비를 선택하세요 (1-2)", list(aspects.keys()), "1")
#         self.aspect_ratio = aspects[aspect_choice][0]
#         print(f"✅ 종횡비: {aspects[aspect_choice][1]}\n")
    
#     def _input_duration(self):
#         """분량 입력"""
#         print("⏱️  3단계: 영상 분량")
#         print("-"*70)
        
#         durations = {
#             "1": (60, "1분 미만 (Shorts)"),
#             "2": (180, "3분"),
#             "3": (300, "5분"),
#             "4": (600, "10분"),
#             "5": (900, "15분"),
#             "6": (1200, "20분"),
#             "7": (1800, "30분"),
#             "8": (0, "직접 입력")
#         }
        
#         for key, (_, desc) in durations.items():
#             print(f"  {key}. {desc}")
        
#         dur_choice = self._get_choice("분량을 선택하세요 (1-8)", list(durations.keys()), "3")
        
#         if dur_choice == "8":
#             while True:
#                 try:
#                     self.duration = int(input("시간을 초 단위로 입력하세요: ").strip())
#                     if self.duration > 0:
#                         break
#                     else:
#                         print("❌ 양수를 입력하세요.")
#                 except ValueError:
#                     print("❌ 숫자를 입력하세요.")
#         else:
#             self.duration = durations[dur_choice][0]
        
#         print(f"✅ 분량: {self.duration}초 ({self.duration//60}분 {self.duration%60}초)\n")
    
#     def _get_choice(self, prompt: str, valid_choices: List[str], default: str) -> str:
#         """선택지 입력 받기"""
#         choice = input(f"{prompt} (기본값 {default}): ").strip() or default
        
#         while choice not in valid_choices:
#             print(f"❌ {', '.join(valid_choices)} 중에서 선택하세요.")
#             choice = input(f"{prompt} (기본값 {default}): ").strip() or default
        
#         return choice
    
#     def _confirm_settings(self) -> bool:
#         """설정 확인"""
#         print("\n" + "="*70)
#         print("📋 설정 확인")
#         print("="*70)
#         print(f"제목: {self.title}")
#         print(f"배경: {self.background_style}")
#         print(f"성우: {self.voice_style}")
#         print(f"폰트: {self.font_style}")
#         print(f"자막: {self.subtitle_style}")
#         print(f"난이도: {self.difficulty}")
#         print(f"종횡비: {self.aspect_ratio}")
#         print(f"분량: {self.duration}초 ({self.duration//60}분 {self.duration%60}초)")
#         print("="*70)
        
#         confirm = input("\n이대로 진행하시겠습니까? (y/n, 기본값 y): ").strip().lower() or "y"
#         return confirm == 'y'
    
#     def _modify_settings(self) -> Config:
#         """설정 수정"""
#         print("\n수정이 필요한 항목:")
#         print("  1. 제목")
#         print("  2. 스타일 설정")
#         print("  3. 분량")
#         print("  0. 처음부터 다시")
        
#         choice = input("선택 (0-3): ").strip()
        
#         if choice == "1":
#             self._input_title()
#         elif choice == "2":
#             self._input_styles()
#         elif choice == "3":
#             self._input_duration()
#         else:
#             return self.run()
        
#         return self.run()


# # ========== Script Writer ==========
# class ScriptWriter:
#     """대본 작성 전문가 - script-writer.md 참조"""
    
#     def __init__(self, config: Config):
#         self.config = config
#         self.guidelines = SkillLoader.load("script-writer")
        
#         print("\n" + "="*70)
#         print("📖 Script Writer Skill 로드 완료")
#         print("="*70)
    
#     def generate_script(self) -> dict:
#         """대본 생성 메인 함수"""
#         print("\n📝 4단계: 대본 작성")
#         print("-"*70)
        
#         print("\n대본 작성 방식:")
#         print("  1. 직접 작성 (단계별 입력)")
#         print("  2. 파일 업로드 (.txt, .md)")
        
#         method = input("선택 (1-2, 기본값 1): ").strip() or "1"
        
#         if method == "1":
#             script = self._interactive_input()
#         elif method == "2":
#             script = self._load_from_file()
#         else:
#             print("❌ 잘못된 선택입니다. 직접 작성 모드로 진행합니다.")
#             script = self._interactive_input()
        
#         # TTS용 변환 (script-writer.md 규칙 적용)
#         tts_script = self._convert_to_tts(script)
        
#         return {
#             "reading_script": script,
#             "tts_script": tts_script
#         }
    
#     def _interactive_input(self) -> dict:
#         """사용자 직접 입력 (script-writer.md 구조 따름)"""
#         print("\n" + "-"*70)
#         print("✍️  각 섹션별로 대본을 입력해주세요")
#         print("   (script-writer.md의 5단계 구조)")
#         print("-"*70)
        
#         print("\n🎣 Hook (10초, 흥미 유발):")
#         print("   예시: 여러분, 미분이 뭔지 아세요? 사실 미분은 자동차 속도계입니다.")
#         hook = input("> ").strip()
        
#         print("\n🔍 분석 (30%, 문제 상황 설명):")
#         print("   예시: 속도계가 보여주는 숫자는 평균 속도가 아닙니다...")
#         analysis = input("> ").strip()
        
#         print("\n🧮 핵심 수학 (40%, 개념 설명):")
#         print("   예시: 미분은 순간 변화율입니다. dy/dx는...")
#         core_math = input("> ").strip()
        
#         print("\n🚀 적용 (20%, 실생활 연결):")
#         print("   예시: 자율주행차는 매 순간 미분을 계산합니다...")
#         application = input("> ").strip()
        
#         print("\n👋 아웃트로 (10초, 마무리):")
#         print("   예시: 미분은 변화를 측정하는 강력한 도구입니다.")
#         outro = input("> ").strip()
        
#         script = {
#             "title": self.config.title,
#             "hook": hook,
#             "analysis": analysis,
#             "core_math": core_math,
#             "application": application,
#             "outro": outro,
#             "meta": {
#                 "duration": self.config.duration,
#                 "difficulty": self.config.difficulty,
#                 "created_at": datetime.now().isoformat()
#             }
#         }
        
#         print("\n✅ 대본 작성 완료!")
#         return script
    
#     def _load_from_file(self) -> dict:
#         """파일에서 로드"""
#         filepath = input("파일 경로를 입력하세요: ").strip()
        
#         try:
#             with open(filepath, 'r', encoding='utf-8') as f:
#                 content = f.read()
            
#             print(f"✅ 파일 로드 완료 ({len(content)}자)")
            
#             script = self._parse_content(content)
#             script["title"] = self.config.title
#             script["meta"] = {
#                 "duration": self.config.duration,
#                 "difficulty": self.config.difficulty,
#                 "created_at": datetime.now().isoformat(),
#                 "source_file": filepath
#             }
            
#             return script
        
#         except FileNotFoundError:
#             print(f"❌ 파일을 찾을 수 없습니다: {filepath}")
#             print("직접 입력 모드로 전환합니다.")
#             return self._interactive_input()
    
#     def _parse_content(self, content: str) -> dict:
#         """파일 내용 파싱"""
#         sections = {
#             "hook": "",
#             "analysis": "",
#             "core_math": "",
#             "application": "",
#             "outro": ""
#         }
        
#         lines = content.split('\n')
#         current_section = None
        
#         for line in lines:
#             lower_line = line.lower()
            
#             if 'hook' in lower_line or '흥미' in lower_line:
#                 current_section = 'hook'
#             elif '분석' in lower_line or 'analysis' in lower_line:
#                 current_section = 'analysis'
#             elif '핵심' in lower_line or '수학' in lower_line or 'core' in lower_line:
#                 current_section = 'core_math'
#             elif '적용' in lower_line or 'application' in lower_line:
#                 current_section = 'application'
#             elif '아웃트로' in lower_line or 'outro' in lower_line:
#                 current_section = 'outro'
#             elif current_section:
#                 sections[current_section] += line + " "
        
#         if not any(sections.values()):
#             sections['core_math'] = content
        
#         return sections
    
#     def _convert_to_tts(self, script: dict) -> dict:
#         """읽기용 → TTS용 변환 (script-writer.md 규칙)"""
#         print("\n🎤 TTS용 대본 변환 중 (script-writer.md 규칙 적용)...")
        
#         tts = {}
        
#         for section in ['hook', 'analysis', 'core_math', 'application', 'outro']:
#             text = script.get(section, "")
#             tts[f"{section}_tts"] = self._apply_tts_rules(text)
        
#         print("✅ TTS 변환 완료")
#         return tts
    
#     def _apply_tts_rules(self, text: str) -> str:
#         """숫자/기호 → 한글 발음 변환 (script-writer.md 표 참조)"""
        
#         # script-writer.md의 변환 규칙
#         conversions = {
#             # 기본 연산자
#             r'×': ' 곱하기 ',
#             r'\*': ' 곱하기 ',
#             r'÷': ' 나누기 ',
#             r'/': ' 나누기 ',
#             r'\+': ' 더하기 ',
#             r'-': ' 빼기 ',
#             r'=': '는 ',
            
#             # 수학 기호
#             r'√': '루트 ',
#             r'²': ' 제곱',
#             r'³': ' 세제곱',
#             r'∫': '적분 ',
#             r'Σ': '시그마 ',
#             r'lim': '극한값 ',
            
#             # 함수
#             r'f\(x\)': '에프엑스',
#             r'g\(x\)': '지엑스',
#             r'dy/dx': '디와이 디엑스',
#             r'd/dx': '디 디엑스',
            
#             # 숫자 (0-10)
#             r'\b0\b': '영',
#             r'\b1\b': '일',
#             r'\b2\b': '이',
#             r'\b3\b': '삼',
#             r'\b4\b': '사',
#             r'\b5\b': '오',
#             r'\b6\b': '육',
#             r'\b7\b': '칠',
#             r'\b8\b': '팔',
#             r'\b9\b': '구',
#             r'\b10\b': '십',
#         }
        
#         result = text
#         for pattern, replacement in conversions.items():
#             result = re.sub(pattern, replacement, result)
        
#         # 연속 공백 제거
#         result = re.sub(r'\s+', ' ', result)
        
#         return result.strip()


# # ========== OpenAI TTS Generator ==========
# class OpenAITTSGenerator:
#     """OpenAI TTS 음성 생성 + Whisper 타이밍 측정"""
    
#     def __init__(self, output_dir: Path, config: Config):
#         self.output_dir = output_dir
#         self.audio_dir = output_dir / "0_audio"
#         self.audio_dir.mkdir(exist_ok=True)
#         self.config = config
        
#         # OpenAI TTS Whisper 가이드 로드
#         self.guidelines = SkillLoader.load("OPENAI_TTS_WHISPER_GUIDE")
        
#         print("\n" + "="*70)
#         print("📖 OpenAI TTS + Whisper Skill 로드 완료")
#         print("="*70)
    
#     def generate_audio_with_timing(self, scene: dict) -> dict:
#         """TTS 음성 생성 + Whisper 타이밍 측정"""
#         scene_id = scene['scene_id']
#         tts_text = scene['narration_tts']
        
#         print(f"\n   🎤 [{scene_id}] OpenAI TTS 음성 생성 중...")
        
#         # Step 1: TTS 음성 생성
#         audio_file = self.audio_dir / f"{scene_id}_audio.mp3"
        
#         try:
#             response = client.audio.speech.create(
#                 model=self.config.tts_config["model"],
#                 voice=self.config.tts_config["voice"],
#                 input=tts_text,
#                 speed=self.config.tts_config["speed"]
#             )
            
#             # MP3 저장
#             response.stream_to_file(str(audio_file))
#             print(f"      ✅ 음성 파일 생성: {audio_file.name}")
            
#         except Exception as e:
#             print(f"      ❌ TTS 생성 실패: {e}")
#             # 더미 데이터 반환
#             return self._create_dummy_timing(scene)
        
#         # Step 2: Whisper로 타이밍 분석
#         print(f"   ⏱️  [{scene_id}] Whisper 타이밍 분석 중...")
        
#         try:
#             with open(audio_file, "rb") as audio:
#                 transcript = client.audio.transcriptions.create(
#                     model="whisper-1",
#                     file=audio,
#                     response_format="verbose_json",
#                     timestamp_granularities=["word"]
#                 )
            
#             # 타이밍 데이터 추출
#             duration = transcript.duration
#             words = []
            
#             if hasattr(transcript, 'words') and transcript.words:
#                 for word_data in transcript.words:
#                     words.append({
#                         "word": word_data.word,
#                         "start": word_data.start,
#                         "end": word_data.end,
#                         "duration": word_data.end - word_data.start
#                     })
            
#             print(f"      ✅ 실제 음성 길이: {duration:.2f}초")
#             print(f"      ✅ 단어 개수: {len(words)}개")
            
#             return {
#                 "scene_id": scene_id,
#                 "audio_file": str(audio_file),
#                 "actual_duration": duration,
#                 "full_text": transcript.text,
#                 "words": words,
#                 "tts_text": tts_text
#             }
            
#         except Exception as e:
#             print(f"      ⚠️  Whisper 분석 실패: {e}")
#             print(f"      → 음성 파일 기반 추정치 사용")
            
#             # 음성 파일 존재하면 추정
#             if audio_file.exists():
#                 estimated_duration = len(tts_text) / 5  # 초당 약 5자
#                 return {
#                     "scene_id": scene_id,
#                     "audio_file": str(audio_file),
#                     "actual_duration": estimated_duration,
#                     "full_text": tts_text,
#                     "words": self._estimate_word_timings(tts_text, estimated_duration),
#                     "tts_text": tts_text,
#                     "estimated": True
#                 }
            
#             # 최악의 경우 더미
#             return self._create_dummy_timing(scene)
    
#     def _create_dummy_timing(self, scene: dict) -> dict:
#         """더미 타이밍 데이터 (TTS/Whisper 실패 시)"""
#         tts_text = scene['narration_tts']
#         duration = scene['duration'] * 0.95
        
#         return {
#             "scene_id": scene['scene_id'],
#             "audio_file": "dummy.mp3",
#             "actual_duration": duration,
#             "full_text": tts_text,
#             "words": self._estimate_word_timings(tts_text, duration),
#             "tts_text": tts_text,
#             "dummy": True
#         }
    
#     def _estimate_word_timings(self, text: str, total_duration: float) -> List[dict]:
#         """단어별 타이밍 추정"""
#         words = text.split()
#         time_per_word = total_duration / max(len(words), 1)
        
#         result = []
#         current_time = 0.0
        
#         for word in words:
#             result.append({
#                 "word": word,
#                 "start": current_time,
#                 "end": current_time + time_per_word,
#                 "duration": time_per_word
#             })
#             current_time += time_per_word
        
#         return result


# # ========== Scene Director ==========
# class SceneDirector:
#     """씬 분할 전문가 - scene-director.md 참조"""
    
#     def __init__(self, reading_script: dict, tts_script: dict, config: Config):
#         self.reading_script = reading_script
#         self.tts_script = tts_script
#         self.config = config
#         self.total_duration = config.duration
        
#         # scene-director.md 로드
#         self.guidelines = SkillLoader.load("scene-director")
        
#         print("\n" + "="*70)
#         print("📖 Scene Director Skill 로드 완료")
#         print("="*70)
    
#     def split_scenes(self) -> List[Dict]:
#         """대본 내용을 분석하여 자연스럽게 씬 분할 (scene-director.md 원칙)"""
#         print("\n🎬 5단계: 씬 분할")
#         print("-"*70)
        
#         # 섹션별 텍스트
#         sections = {
#             'hook': self.reading_script['hook'],
#             'analysis': self.reading_script['analysis'],
#             'core_math': self.reading_script['core_math'],
#             'application': self.reading_script['application'],
#             'outro': self.reading_script['outro']
#         }
        
#         # scene-director.md의 시간 배분
#         time_distribution = {
#             'hook': 0.05,       # 5%
#             'analysis': 0.30,   # 30%
#             'core_math': 0.40,  # 40%
#             'application': 0.20, # 20%
#             'outro': 0.05       # 5%
#         }
        
#         scenes = []
#         scene_counter = 1
        
#         for section_name, text in sections.items():
#             section_time = int(self.total_duration * time_distribution[section_name])
            
#             if not text.strip():
#                 continue
            
#             # 문장 분리
#             sentences = self._split_into_sentences(text)
            
#             if not sentences:
#                 continue
            
#             # 씬 개수 결정 (scene-director.md: 평균 10-20초)
#             avg_scene_duration = 15
#             num_scenes = max(1, section_time // avg_scene_duration)
#             sentences_per_scene = max(1, len(sentences) // num_scenes)
            
#             # 씬 생성
#             for i in range(num_scenes):
#                 start_idx = i * sentences_per_scene
#                 end_idx = start_idx + sentences_per_scene if i < num_scenes - 1 else len(sentences)
                
#                 scene_sentences = sentences[start_idx:end_idx]
#                 scene_text = " ".join(scene_sentences)
                
#                 # TTS 텍스트 추출
#                 tts_key = f"{section_name}_tts"
#                 tts_full = self.tts_script.get(tts_key, scene_text)
#                 tts_text = self._extract_tts_portion(tts_full, i / num_scenes, (i + 1) / num_scenes)
                
#                 # 시간 추정
#                 duration = self._estimate_duration(scene_text)
                
#                 scene = {
#                     "scene_id": f"s{scene_counter}",
#                     "section": section_name.replace('_', ' ').title(),
#                     "duration": duration,
#                     "narration_display": scene_text,  # 화면 표시용 (숫자/기호)
#                     "narration_tts": tts_text,        # TTS 음성용 (한글 발음)
#                     "visual_concept": self._suggest_visual_concept(scene_text, section_name),
#                     "main_objects": self._suggest_main_objects(scene_text),
#                     "wow_moment": self._suggest_wow_moment(section_name, i, num_scenes)
#                 }
                
#                 scenes.append(scene)
#                 scene_counter += 1
        
#         # 시간 조정
#         scenes = self._adjust_scene_timings(scenes)
        
#         print(f"✅ 총 {len(scenes)}개 씬 생성 완료")
#         print(f"⏱️  설계 총 시간: {sum(s['duration'] for s in scenes)}초")
        
#         return scenes
    
#     def _split_into_sentences(self, text: str) -> List[str]:
#         """텍스트를 문장으로 분리"""
#         text = text.replace('\n', ' ').strip()
#         text = re.sub(r'\s+', ' ', text)
#         sentences = re.split(r'(?<=[.!?])\s+', text)
#         return [s.strip() for s in sentences if s.strip()]
    
#     def _estimate_duration(self, text: str) -> int:
#         """텍스트 길이로 시간 추정 (한국어 평균: 분당 300자)"""
#         char_count = len(text)
#         duration = (char_count / 300) * 60
#         return max(5, min(30, int(duration)))
    
#     def _extract_tts_portion(self, tts_text: str, start_ratio: float, end_ratio: float) -> str:
#         """TTS 텍스트의 일부 추출"""
#         sentences = self._split_into_sentences(tts_text)
#         total = len(sentences)
        
#         if total == 0:
#             return tts_text
        
#         start_idx = int(total * start_ratio)
#         end_idx = int(total * end_ratio)
        
#         return " ".join(sentences[start_idx:end_idx])
    
#     def _suggest_visual_concept(self, text: str, section: str) -> str:
#         """시각적 콘셉트 제안 (scene-director.md 기반)"""
#         concepts = {
#             'hook': "흥미로운 질문 → 핵심 개념 Flash",
#             'analysis': "문제 상황 시각화 → 해결 필요성",
#             'core_math': "수식 전개 → 개념 설명",
#             'application': "실생활 적용 사례",
#             'outro': "전체 요약 → 여운"
#         }
#         return concepts.get(section, "기본 설명")
    
#     def _suggest_main_objects(self, text: str) -> List[str]:
#         """주요 객체 제안"""
#         objects = []
        
#         if any(word in text for word in ['함수', 'f(x)', 'g(x)']):
#             objects.append("MathTex(r'f(x)')")
        
#         if any(word in text for word in ['그래프', '곡선']):
#             objects.append("Axes + FunctionGraph")
        
#         if any(word in text for word in ['벡터', '화살표']):
#             objects.append("Vector / Arrow")
        
#         if not objects:
#             objects.append("Text / MathTex")
        
#         return objects
    
#     def _suggest_wow_moment(self, section: str, scene_idx: int, total_scenes: int) -> str:
#         """Wow 모멘트 제안"""
#         if section == 'hook':
#             return "Flash 효과"
#         elif section == 'core_math' and scene_idx == total_scenes - 1:
#             return "최종 수식 Flash"
#         elif section == 'application':
#             return "실생활 사례 시각화"
#         elif section == 'outro':
#             return "최종 Flash + 여운"
#         return "Indicate"
    
#     def _adjust_scene_timings(self, scenes: List[Dict]) -> List[Dict]:
#         """전체 시간 맞추기"""
#         current_total = sum(s['duration'] for s in scenes)
#         target = self.total_duration
        
#         if current_total == target:
#             return scenes
        
#         ratio = target / current_total
        
#         for scene in scenes:
#             scene['duration'] = max(5, int(scene['duration'] * ratio))
        
#         adjusted_total = sum(s['duration'] for s in scenes)
#         diff = target - adjusted_total
        
#         if diff != 0:
#             scenes[-1]['duration'] += diff
        
#         return scenes


# # ========== Visual Planner ==========
# class VisualPlanner:
#     """연출 계획 수립 - visual-planner.md 참조"""
    
#     def __init__(self, scene: dict, config: Config, timing_data: dict):
#         self.scene = scene
#         self.config = config
#         self.timing_data = timing_data
        
#         # visual-planner.md 로드
#         self.guidelines = SkillLoader.load("visual-planner")
    
#     def create_plan(self) -> dict:
#         """연출 계획 (visual-planner.md 출력 형식)"""
#         print(f"   🎨 [{self.scene['scene_id']}] Visual Planning")
        
#         return {
#             "scene_id": self.scene['scene_id'],
#             "main_objects": self.scene['main_objects'],
#             "visual_concept": self.scene['visual_concept'],
#             "wow_moment": self.scene['wow_moment'],
#             "duration": self.scene['duration'],
#             "actual_audio_duration": self.timing_data.get('actual_duration', 0),
#             "color_scheme": self.config.color_palette,
#             "style": self.config.background_style,
#             "camera_work": "정적",  # visual-planner.md 기본값
#             "difficulty_adaptation": {
#                 "beginner": "Write + FadeIn 중심",
#                 "intermediate": "Transform 추가",
#                 "advanced": "TransformMatchingTex + ValueTracker"
#             }
#         }


# # ========== Manim Coder ==========
# class ManimCoder:
#     """Manim 코드 생성 - manim-coder.md 참조"""
    
#     def __init__(self, plan: dict, scene: dict, config: Config, timing_data: dict):
#         self.plan = plan
#         self.scene = scene
#         self.config = config
#         self.timing_data = timing_data
        
#         # manim-coder.md 로드
#         self.guidelines = SkillLoader.load("manim-coder")
        
#         # 타이밍 보정 계산
#         self.timing_correction = self._calculate_correction()
    
#     def _calculate_correction(self) -> dict:
#         """타이밍 보정 계산"""
#         designed = self.scene['duration']
#         actual = self.timing_data.get('actual_duration', designed)
        
#         # 애니메이션 기본 시간 (Write + Indicate + FadeOut 등)
#         animation_base_time = 4.5  # 예상 애니메이션 시간
        
#         # 필요한 wait() 시간
#         needed_wait = actual - animation_base_time
        
#         if needed_wait < 0:
#             return {
#                 "status": "TOO_SHORT",
#                 "correction": 0,
#                 "note": "음성이 너무 짧음. 애니메이션 속도 조정 필요"
#             }
        
#         return {
#             "status": "OK",
#             "correction": needed_wait,
#             "note": f"wait({needed_wait:.2f}) 추가"
#         }
    
#     def generate_code(self) -> str:
#         """Manim 코드 생성 (manim-coder.md 템플릿)"""
#         scene_id = self.scene['scene_id']
#         style = self.config.background_style
        
#         print(f"   💻 [{scene_id}] Manim 코드 생성 ({style} 스타일)")
        
#         # 스타일별 생성
#         generators = {
#             "minimal": self._generate_minimal,
#             "cyberpunk": self._generate_cyberpunk,
#             "paper": self._generate_paper,
#             "space": self._generate_space,
#             "geometric": self._generate_geometric
#         }
        
#         generator = generators.get(style, self._generate_cyberpunk)
#         return generator(scene_id)
    
#     def _generate_minimal(self, scene_id: str) -> str:
#         """미니멀 스타일 (manim-coder.md 예시)"""
#         correction = self.timing_correction['correction']
#         actual_duration = self.timing_data.get('actual_duration', 0)
        
#         return f'''from manim import *

# class {scene_id.capitalize()}(Scene):
#     """
#     씬: {self.scene['scene_id']}
#     섹션: {self.scene['section']}
#     설계 시간: {self.scene['duration']}초
#     실제 음성: {actual_duration:.2f}초
#     """
    
#     def construct(self):
#         # ========== 미니멀 스타일 (manim-coder.md) ==========
#         self.camera.background_color = BLACK
        
#         # ========== Scene Director 데이터 ==========
#         scene_data = {{
#             "narration_display": "{self._escape_quotes(self.scene['narration_display'][:80])}...",
#             "duration": {actual_duration:.2f}
#         }}
        
#         # ========== 컬러 팔레트 ==========
#         COLOR_PALETTE = {str(self.config.color_palette)}
        
#         # ========== 객체 생성 ==========
#         title = Text(
#             scene_data["narration_display"],
#             font="Noto Sans KR",
#             font_size=48,
#             color=WHITE
#         )
#         title.add_background_rectangle(color=BLACK, opacity=0.7)
        
#         # ========== 애니메이션 ==========
#         self.play(Write(title), run_time=2.0)  # wait_tag_{scene_id}_1
#         self.wait(1.0)  # wait_tag_{scene_id}_2
        
#         self.play(
#             Indicate(title, scale_factor=1.2),
#             run_time=1.0
#         )  # wait_tag_{scene_id}_3
        
#         # ⭐ 음성 길이 맞추기 (타이밍 보정)
#         self.wait({correction:.2f})  # wait_tag_{scene_id}_sync_correction
        
#         # ========== 종료 ==========
#         self.play(FadeOut(title))  # wait_tag_{scene_id}_final
#         self.wait(0.5)  # wait_tag_{scene_id}_end
# '''
    
#     def _generate_cyberpunk(self, scene_id: str) -> str:
#         """사이버펑크 스타일"""
#         correction = self.timing_correction['correction']
#         actual_duration = self.timing_data.get('actual_duration', 0)
        
#         return f'''from manim import *

# class {scene_id.capitalize()}(Scene):
#     """
#     씬: {self.scene['scene_id']}
#     섹션: {self.scene['section']}
#     설계 시간: {self.scene['duration']}초
#     실제 음성: {actual_duration:.2f}초
#     """
    
#     def construct(self):
#         # ========== 사이버펑크 스타일 (manim-coder.md) ==========
#         self.camera.background_color = "#0a0a0a"
        
#         CYBER_CYAN = "#00ffff"
#         CYBER_MAGENTA = "#ff00ff"
        
#         # ========== Scene Director 데이터 ==========
#         scene_data = {{
#             "narration_display": "{self._escape_quotes(self.scene['narration_display'][:80])}...",
#             "duration": {actual_duration:.2f}
#         }}
        
#         # ========== 객체 생성 ==========
#         title = Text(
#             scene_data["narration_display"],
#             font="Noto Sans KR",
#             font_size=48,
#             color=CYBER_CYAN
#         )
        
#         # 글로우 효과 (manim-coder.md)
#         title.set_stroke(width=10, opacity=0.3, color=CYBER_CYAN)
#         title.add_background_rectangle(color="#0a0a0a", opacity=0.8)
        
#         # ========== 애니메이션 ==========
#         self.play(Write(title), run_time=2.0)  # wait_tag_{scene_id}_1
#         self.wait(1.0)  # wait_tag_{scene_id}_2
        
#         self.play(
#             Flash(title, color=CYBER_MAGENTA, flash_radius=2.0, num_lines=12),
#             run_time=1.0
#         )  # wait_tag_{scene_id}_3
        
#         # ⭐ 음성 길이 맞추기 (Whisper 측정값 기준)
#         self.wait({correction:.2f})  # wait_tag_{scene_id}_sync_correction
        
#         # ========== 종료 ==========
#         self.play(FadeOut(title))  # wait_tag_{scene_id}_final
#         self.wait(0.5)  # wait_tag_{scene_id}_end
# '''
    
#     def _generate_paper(self, scene_id: str) -> str:
#         """종이 질감 스타일"""
#         correction = self.timing_correction['correction']
#         actual_duration = self.timing_data.get('actual_duration', 0)
        
#         return f'''from manim import *

# class {scene_id.capitalize()}(Scene):
#     """
#     씬: {self.scene['scene_id']}
#     섹션: {self.scene['section']}
#     설계 시간: {self.scene['duration']}초
#     실제 음성: {actual_duration:.2f}초
#     """
    
#     def construct(self):
#         # ========== 종이 질감 스타일 ==========
#         self.camera.background_color = "#f5f5dc"
        
#         # ========== 객체 생성 ==========
#         title = Text(
#             "{self._escape_quotes(self.scene['narration_display'][:80])}...",
#             font="Noto Sans KR",
#             font_size=48,
#             color=BLACK
#         )
        
#         # ========== 애니메이션 ==========
#         self.play(Write(title), run_time=2.0)  # wait_tag_{scene_id}_1
#         self.wait(1.0)  # wait_tag_{scene_id}_2
        
#         self.play(
#             Circumscribe(title, color=DARK_GRAY),
#             run_time=1.0
#         )  # wait_tag_{scene_id}_3
        
#         self.wait({correction:.2f})  # wait_tag_{scene_id}_sync_correction
        
#         # ========== 종료 ==========
#         self.play(FadeOut(title))  # wait_tag_{scene_id}_final
#         self.wait(0.5)  # wait_tag_{scene_id}_end
# '''
    
#     def _generate_space(self, scene_id: str) -> str:
#         """우주 스타일"""
#         correction = self.timing_correction['correction']
#         actual_duration = self.timing_data.get('actual_duration', 0)
        
#         return f'''from manim import *

# class {scene_id.capitalize()}(Scene):
#     """
#     씬: {self.scene['scene_id']}
#     섹션: {self.scene['section']}
#     설계 시간: {self.scene['duration']}초
#     실제 음성: {actual_duration:.2f}초
#     """
    
#     def construct(self):
#         # ========== 우주 스타일 ==========
#         self.camera.background_color = "#000011"
        
#         SPACE_BLUE = "#4169e1"
        
#         # ========== 객체 생성 ==========
#         title = Text(
#             "{self._escape_quotes(self.scene['narration_display'][:80])}...",
#             font="Noto Sans KR",
#             font_size=48,
#             color=SPACE_BLUE
#         )
#         title.set_stroke(width=8, opacity=0.4, color=SPACE_BLUE)
        
#         # ========== 애니메이션 ==========
#         self.play(Write(title), run_time=2.0)  # wait_tag_{scene_id}_1
#         self.wait(1.0)  # wait_tag_{scene_id}_2
        
#         self.play(
#             Flash(title, color=WHITE, flash_radius=1.5),
#             run_time=1.0
#         )  # wait_tag_{scene_id}_3
        
#         self.wait({correction:.2f})  # wait_tag_{scene_id}_sync_correction
        
#         # ========== 종료 ==========
#         self.play(FadeOut(title))  # wait_tag_{scene_id}_final
#         self.wait(0.5)  # wait_tag_{scene_id}_end
# '''
    
#     def _generate_geometric(self, scene_id: str) -> str:
#         """기하학 스타일"""
#         correction = self.timing_correction['correction']
#         actual_duration = self.timing_data.get('actual_duration', 0)
        
#         return f'''from manim import *

# class {scene_id.capitalize()}(Scene):
#     """
#     씬: {self.scene['scene_id']}
#     섹션: {self.scene['section']}
#     설계 시간: {self.scene['duration']}초
#     실제 음성: {actual_duration:.2f}초
#     """
    
#     def construct(self):
#         # ========== 기하학 스타일 ==========
#         self.camera.background_color = "#1a1a1a"
        
#         # ========== 객체 생성 ==========
#         title = Text(
#             "{self._escape_quotes(self.scene['narration_display'][:80])}...",
#             font="Noto Sans KR",
#             font_size=48,
#             color=GOLD
#         )
        
#         # ========== 애니메이션 ==========
#         self.play(Write(title), run_time=2.0)  # wait_tag_{scene_id}_1
#         self.wait(1.0)  # wait_tag_{scene_id}_2
        
#         self.play(
#             Circumscribe(title, color=GOLD, shape=Rectangle),
#             run_time=1.0
#         )  # wait_tag_{scene_id}_3
        
#         self.wait({correction:.2f})  # wait_tag_{scene_id}_sync_correction
        
#         # ========== 종료 ==========
#         self.play(FadeOut(title))  # wait_tag_{scene_id}_final
#         self.wait(0.5)  # wait_tag_{scene_id}_end
# '''
    
#     def _escape_quotes(self, text: str) -> str:
#         """따옴표 이스케이프"""
#         return text.replace('"', '\\"').replace("'", "\\'")


# # ========== Code Validator ==========
# class CodeValidator:
#     """코드 검증 - code-validator.md 참조"""
    
#     def __init__(self):
#         # code-validator.md 로드
#         self.guidelines = SkillLoader.load("code-validator")
    
#     def validate(self, code: str, scene: dict, timing_data: dict) -> dict:
#         """코드 검증 (code-validator.md 체크리스트)"""
#         print(f"   🔍 [{scene['scene_id']}] Code Validation")
        
#         errors = []
#         warnings = []
        
#         # Phase 1: 문법 검증
#         self._check_mathtex_rstring(code, errors)
#         self._check_text_font(code, warnings)
        
#         # Phase 2: 로직 검증
#         self._check_always_redraw(code, errors)
        
#         # Phase 3: 타이밍 검증
#         self._check_wait_tags(code, scene, warnings)
#         timing_status = self._check_total_timing(code, timing_data, warnings)
        
#         # Phase 4: 스타일 검증
#         # (간소화)
        
#         status = "OK" if not errors else "FAILED"
        
#         return {
#             "status": status,
#             "errors": errors,
#             "warnings": warnings,
#             "timing_check": timing_status
#         }
    
#     def _check_mathtex_rstring(self, code: str, errors: List[str]):
#         """MathTex r-string 확인"""
#         if 'MathTex(' in code:
#             pattern = r'MathTex\([^r]"'
#             if re.search(pattern, code):
#                 errors.append("MathTex에 r-string 사용 필요")
    
#     def _check_text_font(self, code: str, warnings: List[str]):
#         """한글 폰트 확인"""
#         if 'Text(' in code:
#             # 간단 체크
#             if 'font="Noto Sans KR"' not in code:
#                 warnings.append("한글 Text에 Noto Sans KR 폰트 권장")
    
#     def _check_always_redraw(self, code: str, errors: List[str]):
#         """always_redraw lambda 확인"""
#         if 'always_redraw(' in code:
#             pattern = r'always_redraw\(\s*[^l]'
#             if re.search(pattern, code):
#                 errors.append("always_redraw는 lambda 함수 필요")
    
#     def _check_wait_tags(self, code: str, scene: dict, warnings: List[str]):
#         """wait() 태그 확인"""
#         wait_count = len(re.findall(r'self\.wait\(', code))
#         tag_count = len(re.findall(r'# wait_tag_', code))
        
#         if wait_count != tag_count:
#             warnings.append(f"wait() 개수({wait_count})와 태그({tag_count}) 불일치")
    
#     def _check_total_timing(self, code: str, timing_data: dict, warnings: List[str]) -> dict:
#         """총 시간 계산"""
#         # run_time 추출
#         run_times = re.findall(r'run_time\s*=\s*([0-9.]+)', code)
#         total_runtime = sum(float(t) for t in run_times)
        
#         # wait() 추출
#         waits = re.findall(r'self\.wait\(([0-9.]+)\)', code)
#         total_wait = sum(float(w) for w in waits)
        
#         # play() without run_time (기본 1초)
#         plays = len(re.findall(r'self\.play\(', code))
#         plays_with_runtime = len(run_times)
#         plays_without = plays - plays_with_runtime
        
#         total_animation = total_runtime + total_wait + plays_without
        
#         actual_audio = timing_data.get('actual_duration', 0)
#         diff = abs(total_animation - actual_audio)
        
#         if diff > actual_audio * 0.1:  # 10% 이상 차이
#             warnings.append(f"타이밍 차이: 애니메이션 {total_animation:.1f}초 vs 음성 {actual_audio:.1f}초")
        
#         return {
#             "total_animation_time": total_animation,
#             "actual_audio_duration": actual_audio,
#             "difference": diff,
#             "status": "OK" if diff <= actual_audio * 0.1 else "WARNING"
#         }


# # ========== Image Prompt Writer ==========
# class ImagePromptWriter:
#     """배경 이미지 프롬프트 - image-prompt-writer.md 참조"""
    
#     def __init__(self):
#         # image-prompt-writer.md 로드
#         self.guidelines = SkillLoader.load("image-prompt-writer")
    
#     def create_prompt(self, scene: dict, config: Config) -> str:
#         """배경 프롬프트 생성 (image-prompt-writer.md 템플릿)"""
#         style = config.background_style
#         aspect = config.aspect_ratio
        
#         # image-prompt-writer.md의 스타일별 프롬프트
#         prompts = {
#             "minimal": f"""minimalist mathematical background, clean dark gradient from black center to deep gray edges,
# subtle geometric pattern in background, no text, no letters, no numbers,
# center area with soft white glow, suitable for bright yellow equations overlay,
# {aspect} ratio, high contrast, professional education video background,
# modern, elegant, simple""",
            
#             "cyberpunk": f"""cyberpunk mathematical background, dark futuristic scene with neon cyan and magenta accents,
# digital grid in background, no text, no letters, no numbers,
# center area with purple glow, edges darker with cyan highlights,
# suitable for bright cyan mathematical equations overlay, {aspect} ratio,
# high tech, neon lights, holographic feel, professional education video""",
            
#             "paper": f"""paper texture background, warm beige to cream gradient, subtle paper grain,
# no text, no letters, no numbers, center area slightly lighter,
# edges with soft sepia tone, suitable for dark handwritten equations overlay,
# {aspect} ratio, vintage education aesthetic, natural texture,
# notebook paper style""",
            
#             "space": f"""space background for mathematics, deep blue cosmic scene with distant stars,
# nebula in dark purple and blue, no text, no letters, no numbers,
# center area with bright starlight glow, edges darker with galaxy swirls,
# suitable for bright white mathematical equations overlay, {aspect} ratio,
# astronomical education aesthetic, mysterious universe""",
            
#             "geometric": f"""geometric pattern background, symmetrical mathematical shapes,
# dark background with golden ratio spiral pattern, no text, no letters, no numbers,
# center area clean, edges with subtle geometric accents in gray,
# suitable for yellow mathematical equations overlay, {aspect} ratio,
# mathematical aesthetic, precise geometry, professional education"""
#         }
        
#         return prompts.get(style, prompts["cyberpunk"])


# # ========== Subtitle Designer ==========
# class SubtitleDesigner:
#     """자막 시스템 - subtitle-designer.md 참조"""
    
#     def __init__(self):
#         # subtitle-designer.md 로드
#         self.guidelines = SkillLoader.load("subtitle-designer")
    
#     def create_subtitles(self, scene: dict, timing_data: dict, config: Config) -> dict:
#         """자막 정보 생성 (subtitle-designer.md 레벨)"""
        
#         # subtitle-designer.md의 레벨 시스템
#         subtitle_levels = {
#             "fixed": 1,     # Level 1: 기본 하단 고정
#             "karaoke": 3,   # Level 3: 카라오케 스타일
#             "formula": 4    # Level 4: 수식 연동
#         }
        
#         level = subtitle_levels.get(config.subtitle_style, 1)
        
#         # Whisper 단어별 타이밍 활용
#         words = timing_data.get('words', [])
        
#         # narration_display (화면 표시용) 와 매칭
#         subtitle_data = self._match_display_with_timing(
#             scene['narration_display'],
#             words
#         )
        
#         return {
#             "scene_id": scene['scene_id'],
#             "subtitle_text": scene['narration_display'],  # 화면용 (숫자/기호)
#             "audio_text": timing_data.get('full_text', ''),  # 음성용 (한글)
#             "duration": timing_data.get('actual_duration', scene['duration']),
#             "level": level,
#             "style": config.background_style,
#             "words": subtitle_data
#         }
    
#     def _match_display_with_timing(self, display_text: str, audio_words: List[dict]) -> List[dict]:
#         """표시용 텍스트와 음성 타이밍 매칭"""
#         # 간단한 매칭 (실제로는 더 정교한 알고리즘 필요)
        
#         if not audio_words:
#             return []
        
#         # display_text를 단어로 분리
#         display_words = display_text.split()
        
#         # 길이 맞추기
#         if len(display_words) != len(audio_words):
#             # 비율로 매칭
#             result = []
#             ratio = len(audio_words) / max(len(display_words), 1)
            
#             for i, disp_word in enumerate(display_words):
#                 audio_idx = min(int(i * ratio), len(audio_words) - 1)
#                 audio_word = audio_words[audio_idx]
                
#                 result.append({
#                     "display_text": disp_word,
#                     "audio_text": audio_word.get('word', ''),
#                     "start": audio_word.get('start', 0),
#                     "duration": audio_word.get('duration', 0.5)
#                 })
            
#             return result
        
#         # 1:1 매칭
#         result = []
#         for disp_word, audio_word in zip(display_words, audio_words):
#             result.append({
#                 "display_text": disp_word,
#                 "audio_text": audio_word.get('word', ''),
#                 "start": audio_word.get('start', 0),
#                 "duration": audio_word.get('duration', 0.5)
#             })
        
#         return result


# # ========== 메인 파이프라인 ==========
# class VideoProductionPipeline:
#     """v5.0 완전 Skills 통합 파이프라인"""
    
#     def __init__(self, config: Config):
#         self.config = config
#         self.output_dir = Path(f"output/{config.project_id}")
        
#         # 폴더 구조
#         self.folders = {
#             "audio": self.output_dir / "0_audio",
#             "script": self.output_dir / "1_script",
#             "scenes": self.output_dir / "2_scenes",
#             "plans": self.output_dir / "3_visual_plans",
#             "code": self.output_dir / "4_manim_code",
#             "validation": self.output_dir / "5_validation",
#             "prompts": self.output_dir / "6_image_prompts",
#             "subtitles": self.output_dir / "7_subtitles",
#             "renders": self.output_dir / "8_renders"
#         }
        
#         for folder in self.folders.values():
#             folder.mkdir(parents=True, exist_ok=True)
        
#         print(f"\n📁 프로젝트 폴더 생성: {self.output_dir}")
    
#     def run(self):
#         """파이프라인 실행"""
#         print("\n" + "="*70)
#         print("🚀 파이프라인 시작")
#         print("="*70)
        
#         # Step 4: 대본 작성
#         writer = ScriptWriter(self.config)
#         scripts = writer.generate_script()
        
#         reading_script = scripts['reading_script']
#         tts_script = scripts['tts_script']
        
#         # 저장
#         self.save_json(reading_script, self.folders["script"] / "reading_script.json")
#         self.save_json(tts_script, self.folders["script"] / "tts_script.json")
#         self.save_markdown(reading_script, self.folders["script"] / "reading_script.md")
        
#         # Step 5: 씬 분할
#         director = SceneDirector(reading_script, tts_script, self.config)
#         scenes = director.split_scenes()
        
#         self.save_json({"scenes": scenes}, self.folders["scenes"] / "scenes.json")
        
#         # Step 6+: 각 씬 처리
#         tts_gen = OpenAITTSGenerator(self.output_dir, self.config)
        
#         print("\n" + "="*70)
#         print("🎬 씬별 처리 시작 (OpenAI TTS + Whisper)")
#         print("="*70)
        
#         for i, scene in enumerate(scenes, 1):
#             scene_id = scene['scene_id']
#             print(f"\n[{i}/{len(scenes)}] 씬 {scene_id} 처리 중...")
#             print("-"*70)
            
#             # ⭐ OpenAI TTS + Whisper 타이밍 측정
#             timing_data = tts_gen.generate_audio_with_timing(scene)
#             self.save_json(timing_data, self.folders["audio"] / f"{scene_id}_timing.json")
            
#             # 연출 계획
#             planner = VisualPlanner(scene, self.config, timing_data)
#             plan = planner.create_plan()
#             self.save_json(plan, self.folders["plans"] / f"{scene_id}_plan.json")
            
#             # Manim 코드 (실제 음성 길이 기준)
#             coder = ManimCoder(plan, scene, self.config, timing_data)
#             code = coder.generate_code()
            
#             # 검증
#             validator = CodeValidator()
#             validation = validator.validate(code, scene, timing_data)
#             self.save_json(validation, self.folders["validation"] / f"{scene_id}_validation.json")
            
#             if validation['status'] == 'FAILED':
#                 print(f"      ⚠️  검증 실패: {validation['errors']}")
            
#             # 코드 저장
#             code_file = self.folders["code"] / f"{scene_id}_manim.py"
#             with open(code_file, 'w', encoding='utf-8') as f:
#                 f.write(code)
            
#             print(f"      ✅ 코드 저장: {code_file.name}")
            
#             # 배경 프롬프트
#             prompt_writer = ImagePromptWriter()
#             prompt = prompt_writer.create_prompt(scene, self.config)
            
#             prompt_file = self.folders["prompts"] / f"{scene_id}_background.txt"
#             with open(prompt_file, 'w', encoding='utf-8') as f:
#                 f.write(prompt)
            
#             # 자막
#             subtitle_designer = SubtitleDesigner()
#             subtitles = subtitle_designer.create_subtitles(scene, timing_data, self.config)
#             self.save_json(subtitles, self.folders["subtitles"] / f"{scene_id}_subtitles.json")
            
#             print(f"      ✅ 씬 {scene_id} 완료")
        
#         # 요약
#         self.save_project_summary(reading_script, scenes)
        
#         # 렌더링 스크립트 생성
#         self.generate_render_script(scenes)
        
#         print("\n" + "="*70)
#         print("✅ 전체 파이프라인 완료!")
#         print("="*70)
#         print(f"📁 출력 폴더: {self.output_dir}")
#         print(f"📊 씬 개수: {len(scenes)}개")
#         print(f"🎨 스타일: {self.config.background_style}")
#         print(f"📺 자막: {self.config.subtitle_style}")
#         print("="*70)
        
#         # 다음 단계 안내
#         print("\n📌 다음 단계:")
#         print(f"1. 음성 파일 확인: {self.folders['audio']}/")
#         print(f"2. Manim 코드 확인: {self.folders['code']}/")
#         print(f"3. 렌더링 실행: bash {self.output_dir}/render_all.sh")
#         print()
    
#     def generate_render_script(self, scenes: List[Dict]):
#         """렌더링 스크립트 생성"""
#         render_script = self.output_dir / "render_all.sh"
        
#         lines = ["#!/bin/bash\n", "# Manim 렌더링 스크립트\n\n"]
        
#         for scene in scenes:
#             scene_id = scene['scene_id']
#             class_name = scene_id.capitalize()
#             code_file = self.folders["code"] / f"{scene_id}_manim.py"
            
#             lines.append(f"echo '렌더링: {scene_id}...'\n")
#             lines.append(f"manim -pql {code_file} {class_name}\n\n")
        
#         lines.append("echo '모든 씬 렌더링 완료!'\n")
        
#         with open(render_script, 'w', encoding='utf-8') as f:
#             f.writelines(lines)
        
#         # 실행 권한 부여
#         render_script.chmod(0o755)
        
#         print(f"\n✅ 렌더링 스크립트 생성: {render_script}")
    
#     def save_json(self, data: dict, filepath: Path):
#         """JSON 저장"""
#         with open(filepath, 'w', encoding='utf-8') as f:
#             json.dump(data, f, ensure_ascii=False, indent=2)
    
#     def save_markdown(self, script: dict, filepath: Path):
#         """마크다운 저장"""
#         content = f"""# {script['title']}

# ## Hook
# {script.get('hook', '')}

# ## 분석
# {script.get('analysis', '')}

# ## 핵심 수학
# {script.get('core_math', '')}

# ## 적용
# {script.get('application', '')}

# ## 아웃트로
# {script.get('outro', '')}

# ---

# ## 메타 정보
# - 난이도: {script['meta']['difficulty']}
# - 분량: {script['meta']['duration']}초
# - 생성일: {script['meta']['created_at']}
# """
#         with open(filepath, 'w', encoding='utf-8') as f:
#             f.write(content)
    
#     def save_project_summary(self, script: dict, scenes: List[Dict]):
#         """프로젝트 요약"""
#         summary = {
#             "project_id": self.config.project_id,
#             "title": script['title'],
#             "created_at": datetime.now().isoformat(),
#             "config": {
#                 "background_style": self.config.background_style,
#                 "voice_style": self.config.voice_style,
#                 "font_style": self.config.font_style,
#                 "subtitle_style": self.config.subtitle_style,
#                 "difficulty": self.config.difficulty,
#                 "aspect_ratio": self.config.aspect_ratio,
#                 "duration": self.config.duration,
#                 "tts_model": self.config.tts_config["model"],
#                 "tts_voice": self.config.tts_config["voice"]
#             },
#             "scenes": {
#                 "count": len(scenes),
#                 "scene_ids": [s['scene_id'] for s in scenes],
#                 "designed_duration": sum(s['duration'] for s in scenes),
#                 "sections": {}
#             },
#             "skills_used": [
#                 "script-writer.md",
#                 "scene-director.md",
#                 "visual-planner.md",
#                 "manim-coder.md",
#                 "code-validator.md",
#                 "image-prompt-writer.md",
#                 "subtitle-designer.md",
#                 "OPENAI_TTS_WHISPER_GUIDE.md"
#             ]
#         }
        
#         # 섹션별 통계
#         for scene in scenes:
#             section = scene['section']
#             if section not in summary['scenes']['sections']:
#                 summary['scenes']['sections'][section] = {
#                     "count": 0,
#                     "duration": 0
#                 }
#             summary['scenes']['sections'][section]["count"] += 1
#             summary['scenes']['sections'][section]["duration"] += scene['duration']
        
#         self.save_json(summary, self.output_dir / "project_summary.json")


# # ========== 메인 실행 ==========
# def main():
#     """메인 함수"""
#     try:
#         # Skills 폴더 확인
#         if not Path("skills").exists():
#             print("❌ skills 폴더를 찾을 수 없습니다.")
#             print("현재 디렉토리에 skills/ 폴더가 있는지 확인하세요.")
#             sys.exit(1)
        
#         # Phase 0-3: 대화형 설정
#         setup = InteractiveSetup()
#         config = setup.run()
        
#         # Phase 4+: 파이프라인 실행
#         pipeline = VideoProductionPipeline(config)
#         pipeline.run()
        
#     except KeyboardInterrupt:
#         print("\n\n⚠️  사용자가 중단했습니다.")
#         print("진행 중인 작업이 중단되었습니다.")
    
#     except Exception as e:
#         print(f"\n\n❌ 오류 발생: {e}")
#         import traceback
#         traceback.print_exc()


# if __name__ == "__main__":
#     main()