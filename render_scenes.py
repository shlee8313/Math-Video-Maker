#!/usr/bin/env python3
"""
Manim 씬 순차 렌더링 스크립트
- 프로젝트 ID 자동 감지 또는 사용자 입력
- 순차적 렌더링 (씬별 진행 상황 표시)
- 렌더링 완료 파일은 8_renders/ 폴더로 자동 이동
- 오류 발생 시 로그 저장
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# ========== 프로젝트 선택 ==========
class ProjectSelector:
    """output 폴더에서 프로젝트 선택"""
    
    OUTPUT_DIR = Path("output")
    
    @classmethod
    def list_projects(cls) -> List[str]:
        """프로젝트 목록 반환"""
        if not cls.OUTPUT_DIR.exists():
            return []
        
        projects = []
        for item in cls.OUTPUT_DIR.iterdir():
            if item.is_dir() and item.name.startswith('P'):
                projects.append(item.name)
        
        return sorted(projects, reverse=True)  # 최신순
    
    @classmethod
    def select_project(cls) -> Optional[Path]:
        """사용자가 프로젝트 선택"""
        projects = cls.list_projects()
        
        if not projects:
            print("❌ output 폴더에 프로젝트가 없습니다.")
            return None
        
        print("\n" + "="*70)
        print("📁 렌더링할 프로젝트 선택")
        print("="*70)
        
        for i, proj in enumerate(projects, 1):
            proj_path = cls.OUTPUT_DIR / proj
            summary_file = proj_path / "project_summary.json"
            
            # 프로젝트 정보 표시
            if summary_file.exists():
                try:
                    with open(summary_file, 'r', encoding='utf-8') as f:
                        summary = json.load(f)
                    
                    title = summary.get('title', '제목 없음')
                    scene_count = summary.get('scenes', {}).get('count', '?')
                    duration = summary.get('config', {}).get('duration', '?')
                    
                    print(f"  {i}. {proj}")
                    print(f"     제목: {title}")
                    print(f"     씬 개수: {scene_count}개, 분량: {duration}초")
                    
                except:
                    print(f"  {i}. {proj}")
            else:
                print(f"  {i}. {proj}")
        
        print("  0. 직접 입력")
        print()
        
        while True:
            choice = input("선택 (1-{}, 기본값 1): ".format(len(projects))).strip() or "1"
            
            if choice == "0":
                # 직접 입력
                proj_id = input("프로젝트 ID를 입력하세요 (예: P20251226142136): ").strip()
                proj_path = cls.OUTPUT_DIR / proj_id
                
                if proj_path.exists():
                    return proj_path
                else:
                    print(f"❌ 프로젝트를 찾을 수 없습니다: {proj_path}")
                    continue
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(projects):
                    return cls.OUTPUT_DIR / projects[idx]
                else:
                    print(f"❌ 1-{len(projects)} 사이의 숫자를 입력하세요.")
            except ValueError:
                print("❌ 숫자를 입력하세요.")


# ========== 씬 정보 로더 ==========
class SceneLoader:
    """프로젝트의 씬 정보 로드"""
    
    @staticmethod
    def load_scenes(project_path: Path) -> List[Dict]:
        """씬 정보 로드"""
        scenes_file = project_path / "2_scenes" / "scenes.json"
        
        if not scenes_file.exists():
            print(f"❌ 씬 정보 파일을 찾을 수 없습니다: {scenes_file}")
            return []
        
        try:
            with open(scenes_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            scenes = data.get('scenes', [])
            print(f"✅ {len(scenes)}개 씬 정보 로드 완료")
            return scenes
        
        except Exception as e:
            print(f"❌ 씬 정보 로드 실패: {e}")
            return []


# ========== 렌더러 ==========
class ManimRenderer:
    """Manim 순차 렌더링"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.code_dir = project_path / "4_manim_code"
        self.renders_dir = project_path / "8_renders"
        self.log_dir = project_path / "logs"
        
        # 폴더 생성
        self.renders_dir.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)
        
        self.render_results = []
    
    def render_all(self, scenes: List[Dict], quality: str = "l"):
        """모든 씬 순차 렌더링"""
        print("\n" + "="*70)
        print("🎬 순차 렌더링 시작")
        print("="*70)
        print(f"프로젝트: {self.project_path.name}")
        print(f"총 씬 개수: {len(scenes)}개")
        print(f"품질: {self._quality_name(quality)}")
        print("="*70)
        
        start_time = datetime.now()
        
        for i, scene in enumerate(scenes, 1):
            scene_id = scene['scene_id']
            
            print(f"\n[{i}/{len(scenes)}] 씬 {scene_id} 렌더링 중...")
            print("-"*70)
            
            success = self.render_scene(scene, quality)
            
            self.render_results.append({
                "scene_id": scene_id,
                "success": success,
                "index": i
            })
            
            if success:
                print(f"✅ 씬 {scene_id} 렌더링 완료")
            else:
                print(f"❌ 씬 {scene_id} 렌더링 실패")
                
                # 계속 진행 여부 물어보기
                continue_render = input("\n계속 진행하시겠습니까? (y/n, 기본값 y): ").strip().lower() or "y"
                if continue_render != 'y':
                    print("렌더링을 중단합니다.")
                    break
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 결과 요약
        self.print_summary(duration)
    
    def render_scene(self, scene: Dict, quality: str) -> bool:
        """단일 씬 렌더링"""
        scene_id = scene['scene_id']
        class_name = scene_id.capitalize()  # s1 → S1
        
        # 코드 파일 경로
        code_file = self.code_dir / f"{scene_id}_manim.py"
        
        if not code_file.exists():
            print(f"   ❌ 코드 파일이 없습니다: {code_file}")
            return False
        
        # Manim 명령어
        cmd = [
            "manim",
            f"-p{quality}",  # -pl (저화질) 또는 -ph (고화질)
            str(code_file),
            class_name
        ]
        
        print(f"   🎬 실행: {' '.join(cmd)}")
        
        # 로그 파일
        log_file = self.log_dir / f"{scene_id}_render.log"
        
        try:
            with open(log_file, 'w', encoding='utf-8') as log:
                # 렌더링 실행
                process = subprocess.run(
                    cmd,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=str(self.project_path.parent)  # Math-Video-Maker 루트
                )
            
            if process.returncode == 0:
                # 렌더링 성공 → 파일 이동
                self._move_rendered_file(scene_id, class_name, quality)
                return True
            else:
                print(f"   ❌ 렌더링 오류 (종료 코드: {process.returncode})")
                print(f"   로그: {log_file}")
                return False
        
        except FileNotFoundError:
            print("   ❌ Manim이 설치되지 않았습니다.")
            print("   설치: pip install manim")
            return False
        
        except Exception as e:
            print(f"   ❌ 렌더링 중 오류: {e}")
            return False
    
    def _move_rendered_file(self, scene_id: str, class_name: str, quality: str):
        """렌더링된 파일을 8_renders로 이동"""
        # Manim 기본 출력 경로: media/videos/{파일명}/{품질}/
        quality_dir = {
            "l": "480p15",
            "m": "720p30",
            "h": "1080p60",
            "k": "2160p60"
        }.get(quality, "480p15")
        
        # 소스 경로
        source_dir = self.project_path.parent / "media" / "videos" / f"{scene_id}_manim" / quality_dir
        
        if not source_dir.exists():
            print(f"   ⚠️  렌더링 파일을 찾을 수 없습니다: {source_dir}")
            return
        
        # MP4 파일 찾기
        mp4_files = list(source_dir.glob("*.mp4"))
        
        if not mp4_files:
            print(f"   ⚠️  MP4 파일을 찾을 수 없습니다: {source_dir}")
            return
        
        # 가장 최근 파일 (보통 1개)
        source_file = mp4_files[-1]
        
        # 목적지 경로
        dest_file = self.renders_dir / f"{scene_id}.mp4"
        
        try:
            # 파일 이동 (복사 후 삭제)
            import shutil
            shutil.copy2(source_file, dest_file)
            
            print(f"   📦 파일 이동: {dest_file.name}")
        
        except Exception as e:
            print(f"   ⚠️  파일 이동 실패: {e}")
    
    def _quality_name(self, quality: str) -> str:
        """품질 코드 → 이름"""
        names = {
            "l": "저화질 (480p)",
            "m": "중화질 (720p)",
            "h": "고화질 (1080p)",
            "k": "4K (2160p)"
        }
        return names.get(quality, "저화질")
    
    def print_summary(self, duration: float):
        """렌더링 결과 요약"""
        print("\n" + "="*70)
        print("📊 렌더링 결과 요약")
        print("="*70)
        
        success_count = sum(1 for r in self.render_results if r['success'])
        fail_count = len(self.render_results) - success_count
        
        print(f"총 씬 개수: {len(self.render_results)}개")
        print(f"성공: {success_count}개")
        print(f"실패: {fail_count}개")
        print(f"소요 시간: {duration:.1f}초 ({duration/60:.1f}분)")
        print()
        
        # 실패한 씬 목록
        if fail_count > 0:
            print("❌ 실패한 씬:")
            for r in self.render_results:
                if not r['success']:
                    print(f"   - {r['scene_id']}")
            print()
        
        # 출력 폴더
        print(f"📁 렌더링 파일: {self.renders_dir}")
        print(f"📄 로그 파일: {self.log_dir}")
        print("="*70)


# ========== 메인 함수 ==========
def main():
    """메인 실행"""
    print("="*70)
    print("🎬 Manim 순차 렌더링 스크립트")
    print("="*70)
    
    # 1. 프로젝트 선택
    project_path = ProjectSelector.select_project()
    
    if not project_path:
        print("\n프로젝트를 선택할 수 없습니다.")
        sys.exit(1)
    
    print(f"\n✅ 선택된 프로젝트: {project_path.name}")
    
    # 2. 씬 정보 로드
    scenes = SceneLoader.load_scenes(project_path)
    
    if not scenes:
        print("\n씬 정보를 로드할 수 없습니다.")
        sys.exit(1)
    
    # 3. 렌더링 품질 선택
    print("\n" + "-"*70)
    print("🎨 렌더링 품질 선택:")
    print("  1. 저화질 (480p15) - 빠름, 프리뷰용")
    print("  2. 중화질 (720p30) - 보통")
    print("  3. 고화질 (1080p60) - 느림, 최종 출력용")
    print("  4. 4K (2160p60) - 매우 느림")
    
    quality_map = {
        "1": "l",
        "2": "m",
        "3": "h",
        "4": "k"
    }
    
    choice = input("선택 (1-4, 기본값 1): ").strip() or "1"
    quality = quality_map.get(choice, "l")
    
    # 4. 최종 확인
    print("\n" + "="*70)
    print("📋 렌더링 설정 확인")
    print("="*70)
    print(f"프로젝트: {project_path.name}")
    print(f"씬 개수: {len(scenes)}개")
    print(f"품질: {ManimRenderer(project_path)._quality_name(quality)}")
    print(f"출력 폴더: {project_path / '8_renders'}")
    print("="*70)
    
    confirm = input("\n렌더링을 시작하시겠습니까? (y/n, 기본값 y): ").strip().lower() or "y"
    
    if confirm != 'y':
        print("취소되었습니다.")
        sys.exit(0)
    
    # 5. 렌더링 실행
    renderer = ManimRenderer(project_path)
    renderer.render_all(scenes, quality)
    
    print("\n✅ 모든 작업 완료!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자가 중단했습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
