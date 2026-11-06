#!/usr/bin/env python3
"""
gen_icons.py
2027 쭈갑시즌 예약 추천일 웹앱용 패밀리 룩 엠블럼 아이콘 세트 생성
- 모티프: 다크 네이비 림 뱃지 + 2027 캘린더 + 황금빛 달(물때) + 에기/쭈꾸미
- 해상도: 512px, 192px, 180px, 32px
"""

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent

def create_season_icon(size: int = 512) -> Image.Image:
    # 2배 슈퍼샘플링
    scale = 2
    canvas_size = size * scale
    im = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    center = canvas_size / 2.0
    r_outer = canvas_size * 0.46
    r_inner = canvas_size * 0.43

    # 1. 섀도우 레이어
    for i in range(12):
        s_offset = (i + 1) * 2 * scale
        alpha = int(45 * (1.0 - i / 12.0))
        draw.ellipse(
            [
                center - r_outer + s_offset * 0.3,
                center - r_outer + s_offset,
                center + r_outer + s_offset * 0.3,
                center + r_outer + s_offset
            ],
            fill=(0, 0, 0, alpha)
        )

    # 2. 다크 네이비 림 뱃지 본체
    # 바깥 림 테두리 (슬레이트/골드 톤 테두리)
    draw.ellipse(
        [center - r_outer, center - r_outer, center + r_outer, center + r_outer],
        fill="#212d40",
        outline="#e3a94c",
        width=int(5 * scale)
    )

    # 안쪽 서피스 배경 (다크 네이비 #10151d)
    draw.ellipse(
        [center - r_inner, center - r_inner, center + r_inner, center + r_inner],
        fill="#10151d"
    )

    # 은은한 배경 원형 조류 파동
    for step in range(3):
        r_wave = r_inner * (0.85 - step * 0.22)
        draw.arc(
            [center - r_wave, center - r_wave, center + r_wave, center + r_wave],
            start=20,
            end=160,
            fill=(227, 169, 76, 35 + step * 15),
            width=int(2 * scale)
        )

    # 3. 달의 위상 (물때 상징 - 우측 상단 앰버 골드 초승달)
    moon_cx = center + r_inner * 0.40
    moon_cy = center - r_inner * 0.40
    moon_r = r_inner * 0.25

    # 외곽 원
    draw.ellipse(
        [moon_cx - moon_r, moon_cy - moon_r, moon_cx + moon_r, moon_cy + moon_r],
        fill="#e3a94c"
    )
    # 파고드는 다크 원 (초승달 형상 완성)
    shadow_offset = moon_r * 0.45
    draw.ellipse(
        [
            moon_cx - moon_r - shadow_offset,
            moon_cy - moon_r - shadow_offset * 0.5,
            moon_cx + moon_r - shadow_offset,
            moon_cy + moon_r - shadow_offset * 0.5
        ],
        fill="#10151d"
    )

    # 4. 2027 캘린더 본체 (좌측 하단 ~ 중앙)
    cal_w = r_inner * 0.95
    cal_h = r_inner * 0.90
    cal_x = center - cal_w * 0.55
    cal_y = center - cal_h * 0.38

    # 캘린더 바디 (라운드 렉트)
    cal_radius = int(12 * scale)
    draw.rounded_rectangle(
        [cal_x, cal_y, cal_x + cal_w, cal_y + cal_h],
        radius=cal_radius,
        fill="#1a2433",
        outline="#2c3a4f",
        width=int(3 * scale)
    )

    # 캘린더 상단 헤더 바 (골드 앰버)
    header_h = cal_h * 0.26
    draw.rounded_rectangle(
        [cal_x, cal_y, cal_x + cal_w, cal_y + header_h],
        radius=cal_radius,
        fill="#e3a94c"
    )
    # 헤더 하단 사각 채우기 (라운드 모서리 보정)
    draw.rectangle(
        [cal_x, cal_y + header_h - cal_radius, cal_x + cal_w, cal_y + header_h],
        fill="#e3a94c"
    )

    # 캘린더 링 바인더 (상단 구멍 2개)
    ring_r = int(5 * scale)
    draw.ellipse([cal_x + cal_w * 0.25 - ring_r, cal_y - ring_r, cal_x + cal_w * 0.25 + ring_r, cal_y + ring_r * 3], fill="#e8edf4")
    draw.ellipse([cal_x + cal_w * 0.75 - ring_r, cal_y - ring_r, cal_x + cal_w * 0.75 + ring_r, cal_y + ring_r * 3], fill="#e8edf4")

    # 캘린더 그리드 점/타일 (달력 날짜들)
    cols = 4
    rows = 3
    pad_x = cal_w * 0.14
    pad_y = cal_h * 0.36
    cell_w = (cal_w - pad_x * 2) / (cols - 1)
    cell_h = (cal_h - pad_y - cal_h * 0.1) / (rows - 1)

    for r in range(rows):
        for c in range(cols):
            cx = cal_x + pad_x + c * cell_w
            cy = cal_y + pad_y + r * cell_h
            # 특정 황금 날짜(중앙 하단)는 골드 별빛 포인트
            if r == 1 and c == 2:
                star_r = int(7 * scale)
                draw.ellipse([cx - star_r, cy - star_r, cx + star_r, cy + star_r], fill="#e3a94c")
            else:
                dot_r = int(3.5 * scale)
                draw.ellipse([cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r], fill="#4a5d78")

    # 5. 에기(Squid Jig) / 쭈꾸미 루어 모티프 (우측 하단 대각선 크로스)
    # 에기 몸체 (새우 형상 곡선)
    egi_head = (center + cal_w * 0.45, center + cal_h * 0.40)
    egi_tail = (center - cal_w * 0.15, center - cal_h * 0.10)

    # 에기 유선형 실루엣 폴리곤
    angle = math.atan2(egi_head[1] - egi_tail[1], egi_head[0] - egi_tail[0])
    perp = angle + math.pi / 2
    w_egi = 14 * scale

    p1 = (egi_tail[0], egi_tail[1])
    p2 = (center + 10 * scale + math.cos(perp) * w_egi, center + 25 * scale + math.sin(perp) * w_egi)
    p3 = (egi_head[0], egi_head[1])
    p4 = (center + 10 * scale - math.cos(perp) * (w_egi * 0.6), center + 25 * scale - math.sin(perp) * (w_egi * 0.6))

    draw.polygon([p1, p2, p3, p4], fill="#cf8f66", outline="#ffffff", width=int(2.5 * scale))

    # 에기 야광 눈빛 (민트 그린)
    eye_cx = egi_head[0] - 8 * scale
    eye_cy = egi_head[1] - 8 * scale
    draw.ellipse([eye_cx - 4 * scale, eye_cy - 4 * scale, eye_cx + 4 * scale, eye_cy + 4 * scale], fill="#4a9b8f", outline="#ffffff")

    # 에기 바늘 훅 (후방 훅 빗살)
    hook_len = 16 * scale
    draw.line([p1[0], p1[1], p1[0] - hook_len * 0.7, p1[1] + hook_len * 0.7], fill="#e8edf4", width=int(3 * scale))
    draw.line([p1[0], p1[1], p1[0] - hook_len, p1[1]], fill="#e8edf4", width=int(3 * scale))

    # 리사이즈 안티앨리어싱
    final_img = im.resize((size, size), Image.Resampling.LANCZOS)
    return final_img

def main():
    icons = [
        (512, "icon-512.png"),
        (192, "icon-192.png"),
        (180, "favicon-180.png"),
        (32, "favicon-32.png"),
    ]

    print("[gen_icons] 2027 쭈갑시즌 패밀리 룩 아이콘 생성 시작...")
    for sz, name in icons:
        out_path = BASE_DIR / name
        img = create_season_icon(sz)
        img.save(out_path, "PNG")
        print(f"  - 생성 완료: {name} ({sz}x{sz})")

    # 아티팩트 디렉터리 복사 (보고서용)
    artifact_dir = Path("/home/ttolmany/.gemini/antigravity-cli/brain/a057154b-4870-44b4-ae5c-e9839a4bffd5")
    if artifact_dir.exists():
        art_path = artifact_dir / "season-2027-icon.png"
        img512 = create_season_icon(512)
        img512.save(art_path, "PNG")
        print(f"  - 아티팩트 저장 완료: {art_path}")

if __name__ == "__main__":
    main()
