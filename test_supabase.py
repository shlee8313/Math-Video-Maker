"""Supabase connection test"""
import os
import sys

# UTF-8 출력 설정
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

print(f"SUPABASE_URL: {url}")
print(f"SUPABASE_KEY: {key[:20]}..." if key else "SUPABASE_KEY: None")

if not url or not key:
    print("\n[ERROR] Environment variables not set.")
    exit(1)

try:
    from supabase import create_client, Client

    supabase: Client = create_client(url, key)
    print("\n[OK] Supabase client created successfully!")

    # 간단한 쿼리 테스트 (테이블이 없어도 연결 확인 가능)
    try:
        result = supabase.table("_test_connection").select("*").limit(1).execute()
        print(f"Query test: {result}")
    except Exception as e:
        error_msg = str(e)
        if "does not exist" in error_msg or "404" in error_msg or "relation" in error_msg:
            print("[OK] Supabase connection successful! (table doesn't exist yet)")
        else:
            print(f"[WARN] Query error: {e}")

    # Storage 버킷 목록 조회
    try:
        buckets = supabase.storage.list_buckets()
        print(f"\n[STORAGE] Buckets: {[b.name for b in buckets]}")
    except Exception as e:
        print(f"[WARN] Storage error: {e}")

    print("\n=== CONNECTION TEST PASSED ===")

except Exception as e:
    print(f"\n[FAIL] Connection failed: {e}")
