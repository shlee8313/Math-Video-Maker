#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
섹션별 합성 간단 테스트 - analysis만
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

PROJECT_ID = "P20260113_194549"
PROJECT_PATH = Path(f"C:/PROJECT/Math-Video-Maker/output/{PROJECT_ID}")
SECTION = "analysis"
SECTION_SCENES = ["s4", "s5", "s6", "s7", "s8", "s9", "s10", "s11", "s12", "s13", "s14"]
FFMPEG_PATH = "ffmpeg"


def format_srt_time(seconds):
    """초를 SRT 시간 형식으로 변환"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def step1_generate_srt():
    """Step 1: 자막 생성"""
    print("\n[Step 1] 자막 생성...")

    # 타임스탬프와 분할점 로드
    ts_file = PROJECT_PATH / "0_audio" / f"{SECTION}_timestamps.json"
    sp_file = PROJECT_PATH / "0_audio" / f"split_points_{SECTION}.json"

    with open(ts_file, 'r', encoding='utf-8') as f:
        timestamps = json.load(f)
    with open(sp_file, 'r', encoding='utf-8') as f:
        split_points = json.load(f)

    output_path = PROJECT_PATH / "11_section_test"
    output_path.mkdir(exist_ok=True)

    srt_lines = []
    idx = 1

    for split in split_points["splits"]:
        scene_id = split["scene_id"]
        scene_file = PROJECT_PATH / "2_scenes" / f"{scene_id}.json"

        with open(scene_file, 'r', encoding='utf-8') as f:
            scene = json.load(f)

        subtitles = scene["subtitle_display"].split(";;")
        matched_segs = split["matched_segments"]

        for seg_idx, sub_text in zip(matched_segs, subtitles):
            if seg_idx < len(timestamps["segments"]):
                seg = timestamps["segments"][seg_idx]
                start_str = format_srt_time(seg["start"])
                end_str = format_srt_time(seg["end"])

                srt_lines.append(f"{idx}")
                srt_lines.append(f"{start_str} --> {end_str}")
                srt_lines.append(sub_text.strip())
                srt_lines.append("")
                idx += 1

    srt_file = output_path / f"{SECTION}.srt"
    with open(srt_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(srt_lines))

    print(f"  -> {srt_file.name} ({idx-1}개 자막)")
    return srt_file


def step2_create_concat_list():
    """Step 2: concat 리스트 생성 (split_points 기반 duration)"""
    print("\n[Step 2] concat 리스트 생성...")

    sp_file = PROJECT_PATH / "0_audio" / f"split_points_{SECTION}.json"
    with open(sp_file, 'r', encoding='utf-8') as f:
        split_points = json.load(f)

    output_path = PROJECT_PATH / "11_section_test"
    concat_file = output_path / f"{SECTION}_concat.txt"

    lines = []
    for split in split_points["splits"]:
        scene_id = split["scene_id"]
        render_file = PROJECT_PATH / "8_renders" / f"{scene_id}.mov"

        if render_file.exists():
            # Windows 경로를 FFmpeg 형식으로
            render_path = str(render_file).replace("\\", "/")
            lines.append(f"file '{render_path}'")
            lines.append(f"duration {split['duration']}")
            print(f"  {scene_id}: {split['duration']:.2f}s")
        else:
            print(f"  {scene_id}: 렌더 없음!")

    with open(concat_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

    print(f"  -> {concat_file.name}")
    return concat_file


def step3_concat_videos(concat_file):
    """Step 3: 영상 병합 (무음)"""
    print("\n[Step 3] 영상 병합...")

    output_path = PROJECT_PATH / "11_section_test"
    output_file = output_path / f"{SECTION}_video.mp4"

    cmd = [
        FFMPEG_PATH,
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-an",
        "-y", str(output_file)
    ]

    print(f"  실행: ffmpeg concat...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  실패: {result.stderr[:200]}")
        return None

    print(f"  -> {output_file.name}")
    return output_file


def step4_add_audio_subtitle(video_file, srt_file):
    """Step 4: 오디오 + 자막 합성"""
    print("\n[Step 4] 오디오 + 자막 합성...")

    audio_file = PROJECT_PATH / "0_audio" / f"{SECTION}.mp3"
    output_path = PROJECT_PATH / "11_section_test"
    output_file = output_path / f"{SECTION}_final.mp4"

    # 자막 경로 (FFmpeg용)
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

    print(f"  실행: ffmpeg audio+subtitle...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  실패: {result.stderr[:300]}")
        return None

    print(f"  -> {output_file.name}")
    return output_file


def main():
    print("=" * 50)
    print(f"Section Compose Test: {SECTION}")
    print("=" * 50)

    # Step 1: 자막 생성
    srt_file = step1_generate_srt()

    # Step 2: concat 리스트
    concat_file = step2_create_concat_list()

    # Step 3: 영상 병합
    video_file = step3_concat_videos(concat_file)
    if not video_file:
        print("\n[FAILED] Step 3")
        return

    # Step 4: 오디오 + 자막
    final_file = step4_add_audio_subtitle(video_file, srt_file)

    if final_file:
        print("\n" + "=" * 50)
        print(f"DONE: {final_file}")
        print("=" * 50)
    else:
        print("\n[FAILED] Step 4")


if __name__ == "__main__":
    main()
