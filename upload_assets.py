"""로컬 assets를 Supabase에 업로드"""
import os
import sys
from pathlib import Path
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")  # Service Role Key 사용
supabase: Client = create_client(url, key)

ASSETS_DIR = Path("C:/PROJECT/Math-Video-Maker/assets")
BUCKET_NAME = "math-video-assets"

# 에셋 메타데이터 정의
ASSET_METADATA = {
    # characters
    "characters/stickman_celebrating.png": {
        "description": "축하하는 스틱맨 캐릭터",
        "tags": ["character", "stickman", "emotion", "celebrating", "happy"]
    },
    "characters/stickman_confused.png": {
        "description": "혼란스러운 표정의 스틱맨",
        "tags": ["character", "stickman", "emotion", "confused"]
    },
    "characters/stickman_explaining.png": {
        "description": "설명하는 스틱맨",
        "tags": ["character", "stickman", "action", "explaining", "teaching"]
    },
    "characters/stickman_happy.png": {
        "description": "기쁜 표정의 스틱맨",
        "tags": ["character", "stickman", "emotion", "happy"]
    },
    "characters/stickman_pointing.png": {
        "description": "가리키는 스틱맨",
        "tags": ["character", "stickman", "action", "pointing"]
    },
    "characters/stickman_surprised.png": {
        "description": "놀란 표정의 스틱맨",
        "tags": ["character", "stickman", "emotion", "surprised"]
    },
    "characters/stickman_thinking.png": {
        "description": "생각하는 스틱맨",
        "tags": ["character", "stickman", "emotion", "thinking"]
    },
    "characters/stickman_writing.png": {
        "description": "글쓰는 스틱맨",
        "tags": ["character", "stickman", "action", "writing"]
    },
    # icons
    "icons/arrow_right.png": {
        "description": "오른쪽 화살표 아이콘",
        "tags": ["icon", "arrow", "direction", "right"]
    },
    "icons/checkmark.png": {
        "description": "체크마크 아이콘",
        "tags": ["icon", "checkmark", "success", "done"]
    },
    "icons/exclamation.png": {
        "description": "느낌표 아이콘",
        "tags": ["icon", "exclamation", "warning", "attention"]
    },
    "icons/heart.png": {
        "description": "하트 아이콘",
        "tags": ["icon", "heart", "love", "like"]
    },
    "icons/question_mark.png": {
        "description": "물음표 아이콘",
        "tags": ["icon", "question", "help", "inquiry"]
    },
    "icons/star.png": {
        "description": "별 아이콘",
        "tags": ["icon", "star", "rating", "favorite"]
    },
    # metaphors
    "metaphors/golden_chain.png": {
        "description": "금사슬 (구속/연결 은유)",
        "tags": ["metaphor", "chain", "golden", "constraint", "connection"]
    },
    # objects
    "objects/calculator.png": {
        "description": "계산기",
        "tags": ["object", "calculator", "math", "tool"]
    },
    "objects/coin.png": {
        "description": "동전",
        "tags": ["object", "coin", "money", "currency"]
    },
    "objects/compass_drawing.png": {
        "description": "제도용 컴퍼스",
        "tags": ["object", "compass", "geometry", "drawing", "tool"]
    },
    "objects/graph_paper.png": {
        "description": "모눈종이",
        "tags": ["object", "paper", "graph", "grid", "math"]
    },
    "objects/lightbulb.png": {
        "description": "전구 (아이디어)",
        "tags": ["object", "lightbulb", "idea", "insight"]
    },
    "objects/protractor.png": {
        "description": "각도기",
        "tags": ["object", "protractor", "geometry", "angle", "tool"]
    },
    "objects/ruler.png": {
        "description": "자",
        "tags": ["object", "ruler", "measurement", "tool"]
    },
    "objects/snack_bag_normal.png": {
        "description": "일반 과자봉지",
        "tags": ["object", "snack", "bag", "food", "normal"]
    },
    "objects/snack_bag_shrunk.png": {
        "description": "줄어든 과자봉지 (슈링크플레이션)",
        "tags": ["object", "snack", "bag", "food", "shrunk", "shrinkflation"]
    },
}


def get_image_info(file_path: Path) -> dict:
    """이미지 크기와 파일 크기 반환"""
    try:
        with Image.open(file_path) as img:
            width, height = img.size
        file_size = file_path.stat().st_size
        return {"width": width, "height": height, "file_size": file_size}
    except Exception as e:
        print(f"  [WARN] Cannot read image info: {e}")
        return {"width": None, "height": None, "file_size": file_path.stat().st_size}


def upload_asset(file_path: Path, folder: str, file_name: str):
    """단일 에셋 업로드"""
    storage_path = f"{folder}/{file_name}"
    file_key = f"{folder}/{file_name}"

    # 1. Storage에 파일 업로드
    with open(file_path, "rb") as f:
        file_data = f.read()

    try:
        result = supabase.storage.from_(BUCKET_NAME).upload(
            path=storage_path,
            file=file_data,
            file_options={"content-type": "image/png"}
        )
        print(f"  [STORAGE] Uploaded: {storage_path}")
    except Exception as e:
        if "Duplicate" in str(e) or "already exists" in str(e):
            print(f"  [STORAGE] Already exists: {storage_path}")
        else:
            print(f"  [ERROR] Upload failed: {e}")
            return False

    # 2. 이미지 정보 가져오기
    img_info = get_image_info(file_path)

    # 3. 메타데이터 가져오기
    metadata = ASSET_METADATA.get(file_key, {
        "description": f"{folder} asset: {file_name}",
        "tags": [folder.rstrip('s'), file_name.replace('.png', '')]
    })

    # 4. DB에 메타데이터 저장
    try:
        data = {
            "file_name": file_name,
            "folder": folder,
            "storage_path": storage_path,
            "description": metadata.get("description"),
            "tags": metadata.get("tags", []),
            "width": img_info.get("width"),
            "height": img_info.get("height"),
            "file_size": img_info.get("file_size"),
        }

        # upsert (있으면 업데이트, 없으면 삽입)
        result = supabase.table("assets").upsert(
            data,
            on_conflict="folder,file_name"
        ).execute()
        print(f"  [DB] Metadata saved: {file_key}")
        return True
    except Exception as e:
        print(f"  [ERROR] DB insert failed: {e}")
        return False


def main():
    print("=" * 50)
    print("Uploading local assets to Supabase...")
    print("=" * 50)

    # PNG 파일 목록 수집
    png_files = list(ASSETS_DIR.rglob("*.png"))
    print(f"\nFound {len(png_files)} PNG files\n")

    success_count = 0
    fail_count = 0

    for file_path in png_files:
        # 상대 경로에서 폴더와 파일명 추출
        rel_path = file_path.relative_to(ASSETS_DIR)
        folder = rel_path.parent.as_posix()
        file_name = rel_path.name

        print(f"[{folder}/{file_name}]")

        if upload_asset(file_path, folder, file_name):
            success_count += 1
        else:
            fail_count += 1
        print()

    print("=" * 50)
    print(f"DONE! Success: {success_count}, Failed: {fail_count}")
    print("=" * 50)


if __name__ == "__main__":
    main()
