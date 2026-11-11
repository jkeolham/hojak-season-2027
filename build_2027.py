#!/usr/bin/env python3
"""
build_2027.py
2027 쭈갑시즌 예약 추천일 정적 웹앱 컴파일러
- data/season_2027_recommend.json을 읽어 template.html에 주입하여 index.html 생성
- manifest.json 생성
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_JSON_WEST = BASE_DIR / "data" / "season_2027_recommend.json"
DATA_JSON_JEJU = BASE_DIR / "data" / "season_2027_jeju_recommend.json"
DATA_JSON_OPEN = BASE_DIR / "data" / "open_schedules.json"
TEMPLATE_HTML = BASE_DIR / "template.html"
INDEX_HTML = BASE_DIR / "index.html"
MANIFEST_JSON = BASE_DIR / "manifest.json"

def build_manifest():
    manifest = {
        "name": "2027 쭈갑·심해갑 시즌 예약 추천일 & 오픈런 작전판 — Hojak",
        "short_name": "2027 쭈갑작전판",
        "start_url": "./index.html",
        "display": "standalone",
        "background_color": "#0f1620",
        "theme_color": "#0f1620",
        "icons": [
            {
                "src": "icon-192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "icon-512.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    }
    with open(MANIFEST_JSON, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"[build] manifest.json 생성 완료: {MANIFEST_JSON}")

def build_html():
    if not DATA_JSON_WEST.exists():
        raise FileNotFoundError(f"서해 데이터 파일이 없습니다: {DATA_JSON_WEST}")
    if not DATA_JSON_JEJU.exists():
        raise FileNotFoundError(f"제주 데이터 파일이 없습니다: {DATA_JSON_JEJU}")
        
    with open(DATA_JSON_WEST, "r", encoding="utf-8") as f:
        data_west = json.load(f)
    with open(DATA_JSON_JEJU, "r", encoding="utf-8") as f:
        data_jeju = json.load(f)

    open_schedules = []
    if DATA_JSON_OPEN.exists():
        try:
            with open(DATA_JSON_OPEN, "r", encoding="utf-8") as f:
                open_schedules = json.load(f).get("ships", [])
        except Exception as e:
            print(f"[build 경고] open_schedules.json 읽기 실패: {e}")

    # 통합 데이터 패키징
    combined_data = {
        "west": data_west,
        "jeju": data_jeju,
        "open_schedules": open_schedules
    }
        
    with open(TEMPLATE_HTML, "r", encoding="utf-8") as f:
        template = f.read()
        
    # JSON 직렬화 (안전한 스크립트 주입)
    json_str = json.dumps(combined_data, ensure_ascii=False)
    
    # 템플릿 주입
    target_token = "/* [[DATA_JSON]] */ null;"
    if target_token not in template:
        raise ValueError(f"템플릿 내 주입 토큰을 찾을 수 없습니다: {target_token}")
        
    compiled_html = template.replace(target_token, f"{json_str};")
    
    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(compiled_html)
        
    print(f"[build] index.html 컴파일 완료: {INDEX_HTML} ({len(compiled_html)} bytes)")

def main():
    build_manifest()
    build_html()
    print("[build] 2027 쭈갑·제주심해갑 통합 웹앱 빌드 완료!")

if __name__ == "__main__":
    main()
