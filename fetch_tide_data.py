#!/usr/bin/env python3
"""
fetch_tide_data.py
2027년 9월 1일 ~ 11월 30일 (91일간) badatime.com 영흥도(idx 151) 물때·조위·일출몰 데이터 수집 및 정규화
"""

import urllib.request
import re
import json
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_JSON = DATA_DIR / "season_2027_raw.json"

MONTHS = ["2027-09", "2027-10", "2027-11"]

def fetch_month_html(ym: str) -> str:
    url = f"https://www.badatime.com/151/daily/{ym}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    )
    with urllib.request.urlopen(req, timeout=15) as res:
        return res.read().decode("utf-8", errors="ignore")

def parse_month_data(ym: str, html: str) -> list:
    """
    HTML 테이블 행 파싱
    badatime daily 테이블 행 형식:
    <tr class="day-row">
      <td id="week">5(<font color="#FF0000">일</font>)<br><span>8.5</span></td>
      <td class="moon">...</td>
      <td class="tide">11 물</td>
    ...
    """
    results = []
    
    # <tr> 태그 추출
    rows = re.findall(r'<tr[^>]*>.*?</tr>', html, re.DOTALL)
    
    for row in rows:
        # 모바일 전용 행(mo-row-only) 건너뛰기
        if 'mo-row-only' in row:
            continue
        
        # 주간/일자 셀이 포함된 행만 대상
        if 'id="week"' not in row and 'class="day-cell"' not in row:
            continue
        
        # <td>들 분리
        tds = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
        if len(tds) < 3:
            continue
        
        # 1번째 td: 날짜 및 음력 (HTML 태그 제거 후 파싱)
        td0_clean = re.sub(r'<[^>]+>', ' ', tds[0])
        # 공백 정리
        td0_clean = ' '.join(td0_clean.split())
        
        # 패턴: "5 ( 일 ) 8.5" 또는 "1 ( 수 ) 8.1"
        m_date = re.search(r'(\d+)\s*\(\s*([월화수목금토일])\s*\)\s*(\d+\.\d+)?', td0_clean)
        if not m_date:
            continue
        
        day_num = int(m_date.group(1))
        weekday = m_date.group(2)
        lunar = m_date.group(3) if m_date.group(3) else ""
        
        if not lunar:
            m_lunar = re.search(r'(\d+\.\d+)', td0_clean)
            if m_lunar:
                lunar = m_lunar.group(1)
        
        # 물때 td (보통 3번째 td: class="tide")
        tide_text = ""
        for td in tds[1:4]:
            t_clean = re.sub(r'<[^>]+>', '', td).strip().replace('\n', '').replace(' ', '')
            if any(k in t_clean for k in ['물', '조금', '무시']):
                tide_text = t_clean
                break
        
        # 물때 정규화
        if "조금" in tide_text:
            tide_name = "조금"
            tide_num = 0
        elif "무시" in tide_text:
            tide_name = "무시"
            tide_num = 14
        else:
            m_num = re.search(r'(\d+)물?', tide_text)
            if m_num:
                tide_num = int(m_num.group(1))
                tide_name = f"{tide_num}물"
            else:
                tide_name = tide_text
                tide_num = -1
        
        # td[5]: 만조 파싱
        high_events = []
        if len(tds) > 5:
            t5_clean = re.sub(r'<[^>]+>', ' ', tds[5]).replace('&nbsp;', ' ')
            t5_clean = ' '.join(t5_clean.split())
            for m_h in re.finditer(r'(\d{2}:\d{2})\s*\(\s*(-?\d+)\s*\)', t5_clean):
                high_events.append({
                    "time": m_h.group(1),
                    "height": int(m_h.group(2)),
                    "type": "high"
                })

        # td[6]: 간조 파싱
        low_events = []
        if len(tds) > 6:
            t6_clean = re.sub(r'<[^>]+>', ' ', tds[6]).replace('&nbsp;', ' ')
            t6_clean = ' '.join(t6_clean.split())
            for m_l in re.finditer(r'(\d{2}:\d{2})\s*\(\s*(-?\d+)\s*\)', t6_clean):
                low_events.append({
                    "time": m_l.group(1),
                    "height": int(m_l.group(2)),
                    "type": "low"
                })

        tide_events = sorted(high_events + low_events, key=lambda x: x["time"])

        # td[7]: 일출몰 파싱 (class="s_rs")
        sunrise = ""
        sunset = ""
        if len(tds) > 7:
            t7_clean = re.sub(r'<[^>]+>', ' ', tds[7]).strip()
            sun_times = re.findall(r'\b\d{2}:\d{2}\b', t7_clean)
            if len(sun_times) >= 2:
                sunrise = sun_times[0]
                sunset = sun_times[1]

        iso_date = f"{ym}-{day_num:02d}"
        is_weekend = weekday in ["토", "일"]
        
        # 조위차 (최대 만조 - 최소 간조)
        highs = [e["height"] for e in high_events]
        lows = [e["height"] for e in low_events]
        tide_diff = (max(highs) - min(lows)) if highs and lows else 0
        
        results.append({
            "date": iso_date,
            "day": day_num,
            "weekday": weekday,
            "is_weekend": is_weekend,
            "lunar": lunar,
            "tide_name": tide_name,
            "tide_num": tide_num,
            "tide_events": tide_events,
            "tide_diff": tide_diff,
            "sunrise": sunrise,
            "sunset": sunset
        })
        
    return results

def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    all_days = []
    
    print("[1/3] badatime 2027년 9~11월 데이터 수집 시작...")
    for ym in MONTHS:
        print(f"  - 수집 중: {ym} ...")
        html = fetch_month_html(ym)
        days = parse_month_data(ym, html)
        print(f"    -> {len(days)}일 파싱 완료")
        all_days.extend(days)
        
    # 날짜 정렬 및 중복 제거
    unique_days = {d["date"]: d for d in all_days}
    sorted_days = [unique_days[k] for k in sorted(unique_days.keys())]
    
    print(f"\n[2/3] 총 수집 일수: {len(sorted_days)} / 91일")
    assert len(sorted_days) == 91, f"91일 전수가 수집되지 않았습니다 (현재 {len(sorted_days)}일)"
    
    with open(RAW_JSON, "w", encoding="utf-8") as f:
        json.dump(sorted_days, f, ensure_ascii=False, indent=2)
        
    print(f"[3/3] 원시 데이터 저장 완료: {RAW_JSON}")
    
    # 9월 1일, 추석(9/15), 11월 30일 등 주요 날짜 점검
    check_dates = ["2027-09-01", "2027-09-11", "2027-09-12", "2027-09-15", "2027-10-03", "2027-10-09", "2027-11-30"]
    print("\n[주요 날짜 검증 샘플]")
    for d in sorted_days:
        if d["date"] in check_dates:
            print(f"  {d['date']} ({d['weekday']}) | 음력 {d['lunar']} | {d['tide_name']} | 조위차 {d['tide_diff']}cm | 일출 {d['sunrise']}")

if __name__ == "__main__":
    main()
