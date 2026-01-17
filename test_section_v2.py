#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
섹션별 합성 테스트 v2 - 영상 길이 맞춤
"""

import json
import subprocess
import sys
import io
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

PROJECT_ID = "P20260113_194549"
PROJECT_PATH = Path(f"C:/PROJECT/Math-Video-Maker/output/{PROJECT_ID}")
SECTION = "analysis"
SECTION_SCENES = ["s4", "s5", "s6", "s7", "s8", "s9", "s10", "s11", "s12", "s13", "s14"]
FFMPEG_PATH = "ffmpeg"


def format_srt_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def step1_generate_srt():
    """자막 생성"""
    print("\n[Step 1] 자막 생성...")

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


def step2_extend_scenes():
    """각 씬을 target duration에 맞게 확장 (마지막 프레임 유지)"""
    print("\n[Step 2] 씬별 영상 확장...")

    sp_file = PROJECT_PATH / "0_audio" / f"split_points_{SECTION}.json"
    with open(sp_file, 'r', encoding='utf-8') as f:
        split_points = json.load(f)

    output_path = PROJECT_PATH / "11_section_test"
    extended_files = []

    for split in split_points["splits"]:
        scene_id = split["scene_id"]
        target_duration = split["duration"]
        render_file = PROJECT_PATH / "8_renders" / f"{scene_id}.mov"
        extended_file = output_path / f"{scene_id}_ext.mp4"

        if not render_file.exists():
            print(f"  {scene_id}: 렌더 없음!")
            extended_files.append(None)
            continue

        # tpad로 마지막 프레임 유지하면서 확장
        cmd = [
            FFMPEG_PATH,
            "-i", str(render_file),
            "-vf", f"tpad=stop_mode=clone:stop_duration={target_duration}",
            "-t", str(target_duration),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-an",
            "-y", str(extended_file)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  {scene_id}: 확장 실패")
            extended_files.append(None)
        else:
            print(f"  {scene_id}: {target_duration:.2f}s")
            extended_files.append(extended_file)

    return extended_files


def step3_concat_extended(extended_files):
    """확장된 씬들 병합"""
    print("\n[Step 3] 영상 병합...")

    output_path = PROJECT_PATH / "11_section_test"
    concat_file = output_path / f"{SECTION}_concat.txt"

    lines = []
    for ext_file in extended_files:
        if ext_file and ext_file.exists():
            file_path = str(ext_file).replace("\\", "/")
            lines.append(f"file '{file_path}'")

    with open(concat_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

    output_file = output_path / f"{SECTION}_video.mp4"

    cmd = [
        FFMPEG_PATH,
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        "-y", str(output_file)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  실패: {result.stderr[:200]}")
        return None

    print(f"  -> {output_file.name}")
    return output_file


def step4_add_audio_subtitle(video_file, srt_file):
    """오디오 + 자막 합성"""
    print("\n[Step 4] 오디오 + 자막 합성...")

    audio_file = PROJECT_PATH / "0_audio" / f"{SECTION}.mp3"
    output_path = PROJECT_PATH / "11_section_test"
    output_file = output_path / f"{SECTION}_final.mp4"

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
        print(f"  실패: {result.stderr[:300]}")
        return None

    print(f"  -> {output_file.name}")
    return output_file


def get_duration(file_path):
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


def main():
    print("=" * 50)
    print(f"Section Compose Test v2: {SECTION}")
    print("=" * 50)

    srt_file = step1_generate_srt()
    extended_files = step2_extend_scenes()
    video_file = step3_concat_extended(extended_files)

    if not video_file:
        print("\n[FAILED]")
        return

    final_file = step4_add_audio_subtitle(video_file, srt_file)

    if final_file:
        video_dur = get_duration(final_file)
        audio_dur = get_duration(PROJECT_PATH / "0_audio" / f"{SECTION}.mp3")
        print("\n" + "=" * 50)
        print(f"DONE: {final_file}")
        print(f"  Video: {video_dur:.2f}s")
        print(f"  Audio: {audio_dur:.2f}s")
        print(f"  Diff:  {video_dur - audio_dur:.2f}s")
        print("=" * 50)


if __name__ == "__main__":
    main()
