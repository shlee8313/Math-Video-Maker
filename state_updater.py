# ============================================================
# state.json 자동 업데이트 함수들
# math_video_pipeline.py에 추가할 코드
# ============================================================

import json
import os
from datetime import datetime

STATE_FILE = "state.json"

def load_state():
    """state.json 로드"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_state(state):
    """state.json 저장"""
    state['last_updated'] = datetime.now().isoformat()
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    print(f"✅ state.json 업데이트됨: {state['current_phase']}")

# ============================================================
# 단계별 업데이트 함수
# ============================================================

def update_state_script_approved(project_id):
    """Step 2 완료: 대본 승인 후"""
    state = load_state()
    if not state:
        print("❌ state.json을 찾을 수 없습니다.")
        return
    
    state['current_phase'] = 'script_approved'
    
    # files 초기화
    if 'files' not in state:
        state['files'] = {'script': None, 'tts_script': None, 'scenes': None, 'audio': [], 'manim': []}
    
    state['files']['script'] = f"output/{project_id}/1_script/reading_script.json"
    state['files']['tts_script'] = f"output/{project_id}/1_script/tts_script.json"
    
    save_state(state)
    print(f"📝 대본 경로 저장: {state['files']['script']}")


def update_state_scenes_approved(project_id, scene_ids):
    """Step 3 완료: 씬 분할 승인 후"""
    state = load_state()
    if not state:
        print("❌ state.json을 찾을 수 없습니다.")
        return
    
    state['current_phase'] = 'scenes_approved'
    
    # files 업데이트
    if 'files' not in state:
        state['files'] = {'script': None, 'tts_script': None, 'scenes': None, 'audio': [], 'manim': []}
    
    state['files']['scenes'] = f"output/{project_id}/2_scenes/scenes.json"
    
    # scenes 정보 업데이트
    state['scenes'] = {
        'total': len(scene_ids),
        'completed': [],
        'pending': scene_ids,
        'current': scene_ids[0] if scene_ids else None
    }
    
    save_state(state)
    print(f"🎬 씬 분할 저장: {len(scene_ids)}개 씬")


def update_state_tts_completed(project_id, audio_files):
    """Step 4 완료: TTS 생성 완료 후"""
    state = load_state()
    if not state:
        print("❌ state.json을 찾을 수 없습니다.")
        return
    
    state['current_phase'] = 'tts_completed'
    
    # files 업데이트
    if 'files' not in state:
        state['files'] = {'script': None, 'tts_script': None, 'scenes': None, 'audio': [], 'manim': []}
    
    state['files']['audio'] = audio_files
    
    save_state(state)
    print(f"🎤 TTS 완료: {len(audio_files)}개 파일")


def update_state_manim_scene_completed(scene_id, manim_file):
    """Step 5 진행: 씬별 Manim 코드 완료 후"""
    state = load_state()
    if not state:
        print("❌ state.json을 찾을 수 없습니다.")
        return
    
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
        state['files'] = {'script': None, 'tts_script': None, 'scenes': None, 'audio': [], 'manim': []}
    
    if manim_file not in state['files']['manim']:
        state['files']['manim'].append(manim_file)
    
    save_state(state)
    print(f"🎨 Manim 코드 완료: {scene_id}")
    print(f"   완료: {state['scenes']['completed']}")
    print(f"   남음: {state['scenes']['pending']}")


def update_state_rendering():
    """Step 6: 렌더링 시작"""
    state = load_state()
    if not state:
        print("❌ state.json을 찾을 수 없습니다.")
        return
    
    state['current_phase'] = 'rendering'
    save_state(state)


def update_state_completed(final_video_path):
    """모든 작업 완료"""
    state = load_state()
    if not state:
        print("❌ state.json을 찾을 수 없습니다.")
        return
    
    state['current_phase'] = 'completed'
    
    if 'files' not in state:
        state['files'] = {'script': None, 'tts_script': None, 'scenes': None, 'audio': [], 'manim': []}
    
    state['files']['final_video'] = final_video_path
    
    save_state(state)
    print(f"🎉 프로젝트 완료: {final_video_path}")


# ============================================================
# 상태 확인 함수
# ============================================================

def get_current_status():
    """현재 상태 출력"""
    state = load_state()
    if not state:
        print("❌ 진행 중인 프로젝트가 없습니다.")
        return None
    
    print("\n" + "="*60)
    print(f"📊 프로젝트 상태: {state['project_id']}")
    print("="*60)
    print(f"제목: {state.get('title', 'N/A')}")
    print(f"현재 단계: {state.get('current_phase', 'N/A')}")
    print(f"마지막 업데이트: {state.get('last_updated', 'N/A')}")
    
    # 설정
    settings = state.get('settings', {})
    print(f"\n⚙️ 설정:")
    print(f"   스타일: {settings.get('style', 'N/A')}")
    print(f"   난이도: {settings.get('difficulty', 'N/A')}")
    print(f"   길이: {settings.get('duration', 0)}초")
    print(f"   음성: {settings.get('voice', 'N/A')}")
    
    # 파일
    files = state.get('files', {})
    print(f"\n📁 파일:")
    print(f"   대본: {'✅' if files.get('script') else '❌'} {files.get('script', '없음')}")
    print(f"   씬: {'✅' if files.get('scenes') else '❌'} {files.get('scenes', '없음')}")
    print(f"   오디오: {len(files.get('audio', []))}개")
    print(f"   Manim: {len(files.get('manim', []))}개")
    
    # 씬 진행 상황
    scenes = state.get('scenes', {})
    if scenes.get('total', 0) > 0:
        completed = len(scenes.get('completed', []))
        total = scenes.get('total', 0)
        print(f"\n🎬 씬 진행: {completed}/{total} 완료")
        print(f"   완료: {scenes.get('completed', [])}")
        print(f"   대기: {scenes.get('pending', [])}")
        print(f"   현재: {scenes.get('current', 'N/A')}")
    
    print("="*60 + "\n")
    
    return state


def get_resume_point():
    """재개 지점 확인 및 안내"""
    state = load_state()
    if not state:
        return "시작", "새 프로젝트를 시작하세요."
    
    phase = state.get('current_phase', 'initialized')
    
    resume_guide = {
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
    
    print(f"\n🔄 재개 지점: {next_step}")
    print(f"   안내: {guide}")
    
    return next_step, guide


# ============================================================
# 사용 예시
# ============================================================

if __name__ == "__main__":
    # 테스트
    print("state.json 업데이트 함수 테스트")
    
    # 상태 확인
    get_current_status()
    get_resume_point()