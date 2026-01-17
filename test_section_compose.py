#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
섹션별 합성 테스트 스크립트
- analysis 섹션만 테스트
- 씬별 영상(무음) + 섹션 오디오 합성
"""

import json
import subprocess
import sys
import io
from pathlib import Path

# Windows 콘솔 UTF-8 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 프로젝트 경로
PROJECT_ID = "P20260113_194549"
PROJECT_PATH = Path(f"C:/PROJECT/Math-Video-Maker/output/{PROJECT_ID}")
FFMPEG_PATH = "ffmpeg"

# 섹션 정보
SECTION = "analysis"
SECTION_SCENES = ["s4", "s5", "s6", "s7", "s8", "s9", "s10", "s11", "s12", "s13", "s14"]


def get_duration(file_path: Path) -> float:
    """FFprobe로 파일 길이 확인"""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(file_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 0.0


def load_timestamps(section: str) -> dict:
    """Whisper 타임스탬프 로드"""
    ts_file = PROJECT_PATH / "0_audio" / f"{section}_timestamps.json"
    with open(ts_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_split_points(section: str) -> dict:
    """분할 지점 로드"""
    sp_file = PROJECT_PATH / "0_audio" / f"split_points_{section}.json"
    with open(sp_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_scene(scene_id: str) -> dict:
    """씬 정보 로드"""
    scene_file = PROJECT_PATH / "2_scenes" / f"{scene_id}.json"
    with open(scene_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_section_srt(section: str, output_path: Path) -> Path:
    """섹션 전체 자막 SRT 생성 (Whisper timestamps 기반)"""
    timestamps = load_timestamps(section)
    split_points = load_split_points(section)

    srt_lines = []
    subtitle_idx = 1

    for split in split_points["splits"]:
        scene_id = split["scene_id"]
        scene = load_scene(scene_id)

        # subtitle_display를 ;; 로 분리
        subtitles = scene["subtitle_display"].split(";;")

        # 매칭된 segments 가져오기
        matched_segs = split["matched_segments"]

        # segment와 subtitle 매칭
        for i, (seg_idx, sub_text) in enumerate(zip(matched_segs, subtitles)):
            if seg_idx < len(timestamps["segments"]):
                seg = timestamps["segments"][seg_idx]
                start_time = seg["start"]
                end_time = seg["end"]

                # SRT 시간 형식으로 변환
                start_str = format_srt_time(start_time)
                end_str = format_srt_time(end_time)

                srt_lines.append(f"{subtitle_idx}")
                srt_lines.append(f"{start_str} --> {end_str}")
                srt_lines.append(sub_text.strip())
                srt_lines.append("")

                subtitle_idx += 1

    # SRT 파일 저장
    srt_file = output_path / f"{section}.srt"
    with open(srt_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(srt_lines))

    print(f"✅ 자막 생성: {srt_file.name} ({subtitle_idx - 1}개 자막)")
    return srt_file


def format_srt_time(seconds: float) -> str:
    """초를 SRT 시간 형식으로 변환 (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def compose_scene_silent(scene_id: str, output_path: Path) -> Path:
    """씬 합성 (무음) - 렌더링 + 배경만"""
    render_file = PROJECT_PATH / "8_renders" / f"{scene_id}.mov"
    bg_file = PROJECT_PATH / "9_backgrounds" / f"{scene_id}_bg.png"
    output_file = output_path / f"{scene_id}_silent.mp4"

    if output_file.exists():
        print(f"  ⏭️  {scene_id} 무음 영상 이미 존재")
        return output_file

    if not render_file.exists():
        print(f"  ❌ {scene_id} 렌더링 없음")
        return None

    # 배경 유무에 따라 명령 구성
    if bg_file.exists():
        # 배경 + Manim 오버레이
        filter_complex = (
            "[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,"
            "pad=1920:1080:(ow-iw)/2:(oh-ih)/2[bg];"
            "[1:v]scale=1920:1080:force_original_aspect_ratio=decrease,format=rgba[fg];"
            "[bg][fg]overlay=(W-w)/2:(H-h)/2:eof_action=repeat[outv]"
        )
        cmd = [
            FFMPEG_PATH,
            "-loop", "1", "-i", str(bg_file),
            "-i", str(render_file),
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-an",  # 오디오 없음
            "-y", str(output_file)
        ]
    else:
        # Manim만
        cmd = [
            FFMPEG_PATH,
            "-i", str(render_file),
            "-vf", "scale=1920:1080",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-an",
            "-y", str(output_file)
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ❌ {scene_id} 합성 실패")
        return None

    print(f"  ✅ {scene_id} 무음 영상 생성")
    return output_file


def concat_scenes_with_timing(section: str, scene_files: list, output_path: Path) -> Path:
    """씬들을 타이밍에 맞춰 병합 (split_points 기준)"""
    split_points = load_split_points(section)

    # concat 리스트 생성
    concat_list = output_path / f"{section}_concat.txt"

    with open(concat_list, 'w', encoding='utf-8') as f:
        for split, scene_file in zip(split_points["splits"], scene_files):
            if scene_file:
                f.write(f"file '{scene_file}'\n")
                # 씬 길이를 split duration에 맞춤
                target_duration = split["duration"]
                f.write(f"duration {target_duration}\n")

    # FFmpeg concat
    output_file = output_path / f"{section}_video_silent.mp4"

    cmd = [
        FFMPEG_PATH,
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-an",
        "-y", str(output_file)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ 섹션 병합 실패: {result.stderr[:200]}")
        return None

    print(f"✅ 섹션 무음 영상 생성: {output_file.name}")
    return output_file


def add_audio_and_subtitle(section: str, video_file: Path, output_path: Path) -> Path:
    """섹션 영상에 오디오와 자막 추가"""
    audio_file = PROJECT_PATH / "0_audio" / f"{section}.mp3"
    srt_file = output_path / f"{section}.srt"
    output_file = output_path / f"{section}_final.mp4"

    if not audio_file.exists():
        print(f"❌ 오디오 파일 없음: {audio_file}")
        return None

    # 자막 경로 (Windows 특수 처리)
    srt_path = str(srt_file).replace("\\", "/").replace(":", "\\:")

    cmd = [
        FFMPEG_PATH,
        "-i", str(video_file),
        "-i", str(audio_file),
        "-vf", f"subtitles='{srt_path}':force_style='FontName=Malgun Gothic,FontSize=20,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=2,Shadow=1,MarginV=15'",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        "-y", str(output_file)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ 오디오/자막 합성 실패: {result.stderr[:300]}")
        return None

    print(f"✅ 최종 섹션 영상: {output_file.name}")
    return output_file


def main():
    print("=" * 60)
    print(f"🎬 섹션별 합성 테스트: {SECTION}")
    print("=" * 60)

    # 출력 폴더
    output_path = PROJECT_PATH / "11_section_test"
    output_path.mkdir(exist_ok=True)

    # 1. 자막 생성 (Whisper 타이밍 기반)
    print("\n📝 Step 1: 자막 생성")
    srt_file = generate_section_srt(SECTION, output_path)

    # 2. 각 씬 무음 영상 생성
    print("\n🎥 Step 2: 씬별 무음 영상 생성")
    scene_files = []
    for scene_id in SECTION_SCENES:
        result = compose_scene_silent(scene_id, output_path)
        scene_files.append(result)

    # 3. 씬들 병합 (타이밍 맞춤)
    print("\n🔗 Step 3: 씬 병합")
    video_file = concat_scenes_with_timing(SECTION, scene_files, output_path)

    if not video_file:
        print("❌ 병합 실패")
        return

    # 4. 오디오 + 자막 추가
    print("\n🎵 Step 4: 오디오 + 자막 합성")
    final_file = add_audio_and_subtitle(SECTION, video_file, output_path)

    if final_file:
        duration = get_duration(final_file)
        print("\n" + "=" * 60)
        print(f"✅ 완료! {final_file}")
        print(f"   길이: {duration:.2f}초")
        print("=" * 60)


if __name__ == "__main__":
    main()
