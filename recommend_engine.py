#!/usr/bin/env python3
"""
recommend_engine.py
2027 쭈갑시즌 91일 물때 데이터 기반 어종별(쭈꾸미/갑오징어) 스코어링, 티어 판정, 2027 황금연휴 분석 및 TOP 15 필수 예약일 산출
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_JSON = DATA_DIR / "season_2027_raw.json"
REC_JSON = DATA_DIR / "season_2027_recommend.json"

# 2027년 가을 법정 공휴일 및 연휴 정의
HOLIDAYS_2027 = {
    # 2027 추석 연휴 (음력 8/14~8/16)
    "2027-09-14": {"name": "추석연휴", "type": "chuseok"},
    "2027-09-15": {"name": "추석", "type": "chuseok"},
    "2027-09-16": {"name": "추석연휴", "type": "chuseok"},
    # 개천절 및 대체공휴일
    "2027-10-03": {"name": "개천절", "type": "national"},
    "2027-10-04": {"name": "개천절 대체공휴일", "type": "substitute"},
    # 한글날 및 대체공휴일
    "2027-10-09": {"name": "한글날", "type": "national"},
    "2027-10-11": {"name": "한글날 대체공휴일", "type": "substitute"},
}

# 샌드위치 연차 추천일 (추석 황금연휴 브릿지)
BRIDGE_DAYS_2027 = {
    "2027-09-13": "추석 징검다리 연차 권장 (9/11~9/16 6일 연속 출조 가능)",
    "2027-09-17": "추석 징검다리 연차 권장 (9/14~9/19 6일 연속 출조 가능)"
}

def calc_scores(tide_name: str, tide_num: int, tide_diff: int):
    """
    어종별 물때 스코어 (0~100점)
    """
    # 쭈꾸미: 조류가 완만하고 바닥 감도가 뛰어난 약한 물때가 절대 유리
    score_jjuk = 50
    if tide_name == "조금":
        score_jjuk = 98
    elif tide_name == "무시":
        score_jjuk = 97
    elif tide_num in [1, 2]:
        score_jjuk = 100
    elif tide_num == 3:
        score_jjuk = 95
    elif tide_num == 4:
        score_jjuk = 90
    elif tide_num in [12, 13]:
        score_jjuk = 92
    elif tide_num in [5, 11]:
        score_jjuk = 75
    elif tide_num == 10:
        score_jjuk = 65
    elif tide_num in [6, 9]:
        score_jjuk = 50
    elif tide_num in [7, 8]:
        score_jjuk = 35

    # 갑오징어: 물이 적당히 흘러 에기의 수평 액션이 살고 입질 활성도가 높은 스윗스팟 유리
    score_gap = 50
    if tide_num in [4, 5]:
        score_gap = 100
    elif tide_num in [2, 3]:
        score_gap = 95
    elif tide_num in [9, 10]:
        score_gap = 96
    elif tide_num in [11, 12]:
        score_gap = 90
    elif tide_num in [1, 13]:
        score_gap = 78
    elif tide_name in ["조금", "무시"]:
        score_gap = 65
    elif tide_num in [6, 8]:
        score_gap = 55
    elif tide_num == 7:
        score_gap = 40

    return score_jjuk, score_gap

def determine_tier(score_jjuk: int, score_gap: int, is_offday: bool):
    """
    추천 티어 판정 (S / A / B / C)
    """
    max_score = max(score_jjuk, score_gap)
    
    if is_offday:
        if max_score >= 90:
            return "S", "🌟 초황금 예약일"
        elif max_score >= 75:
            return "A", "✨ 우수 추천일"
        elif max_score >= 55:
            return "B", "🔹 무난한 출조일"
        else:
            return "C", "⚠️ 사리·주의일"
    else:
        # 평일
        if max_score >= 95:
            return "A", "✨ 평일 초황금일"
        elif max_score >= 80:
            return "A", "✨ 평일 우수일"
        elif max_score >= 60:
            return "B", "🔹 평일 출조일"
        else:
            return "C", "⚠️ 사리·주의일"

def get_advice(date_str: str, tide_name: str, tide_num: int, score_jjuk: int, score_gap: int, is_offday: bool, holiday_info: dict):
    """
    전문 조행/예약 맞춤 가이드 코멘트 생성
    """
    month = int(date_str.split("-")[1])
    lines = []
    
    if holiday_info:
        lines.append(f"[{holiday_info['name']}]")
    elif date_str in BRIDGE_DAYS_2027:
        lines.append(f"[{BRIDGE_DAYS_2027[date_str]}]")
    
    if month == 9:
        if score_jjuk >= 95:
            lines.append("시즌 초반 쭈꾸미 마릿수 폭발 최적기! 10~12호 가벼운 봉돌로 바닥 감도 극대화 추천.")
        elif score_gap >= 90:
            lines.append("9월 중순 찰박이 갑오징어 입질 시작 구간. 수평 에기와 12~14호 봉돌 단차 채비 유리.")
        else:
            lines.append("조류가 다소 빠른 물때. 입파도/자월도 등 조류 완만 해역 및 16~18호 봉돌 운용.")
    elif month == 10:
        if score_gap >= 90 and score_jjuk >= 90:
            lines.append("쭈꾸미 씨알과 찰박이 갑오징어를 동시에 노리는 가을 피크 골든데이! 쌍포 또는 가지줄 채비 최적.")
        elif score_gap >= 90:
            lines.append("신발짝 갑오징어 집중 공략일! 틴셀/퍼플 에기 운용 및 물돌이 전후 피딩타임 집중.")
        elif score_jjuk >= 90:
            lines.append("굵직한 가을 쭈꾸미 마릿수 공략일. 채비 엉킴 없이 편안한 조업 가능.")
        else:
            lines.append("사리 물때. 20호 봉돌 준비 및 깊은 수심 대물 갑오징어 바닥긁기 공략 권장.")
    else: # 11월
        if score_gap >= 90:
            lines.append("늦가을 몬스터급 대물(신발짝) 갑오징어 라스트 찬스! 따뜻한 방한복 필수, 오모리그/단차 채비 권장.")
        elif score_jjuk >= 90:
            lines.append("문꾸미급 대형 쭈꾸미 손맛 최적일. 무리한 캐스팅보다 배 밑 직벽 바닥 탐색 유리.")
        else:
            lines.append("겨울 문턱 사리 물때. 기상 및 수온 확인 필수, 무거운 봉돌(18~20호) 운용.")
            
    return " ".join(lines)

def main():
    with open(RAW_JSON, "r", encoding="utf-8") as f:
        days = json.load(f)
        
    enriched_days = []
    top_candidates = []
    
    print("[1/2] 2027년 91일 스코어링 및 연휴 교차분석 수행...")
    for d in days:
        date_str = d["date"]
        tide_name = d["tide_name"]
        tide_num = d["tide_num"]
        is_weekend = d["is_weekend"]
        
        # 공휴일 정보
        holiday_info = HOLIDAYS_2027.get(date_str, None)
        is_holiday = holiday_info is not None
        is_bridge = date_str in BRIDGE_DAYS_2027
        is_offday = is_weekend or is_holiday
        
        # 스코어 계산
        score_jjuk, score_gap = calc_scores(tide_name, tide_num, d.get("tide_diff", 0))
        tier, tier_desc = determine_tier(score_jjuk, score_gap, is_offday)
        advice = get_advice(date_str, tide_name, tide_num, score_jjuk, score_gap, is_offday, holiday_info)
        
        # 주말/연휴 우선순위 가중치 (TOP 15 선별용)
        booking_priority = 0
        if is_offday:
            booking_priority += 100
        if holiday_info and holiday_info["type"] == "chuseok":
            booking_priority += 50
        elif holiday_info:
            booking_priority += 30
        if is_bridge:
            booking_priority += 40
            
        booking_priority += max(score_jjuk, score_gap)
        
        item = {
            **d,
            "is_holiday": is_holiday,
            "holiday_name": holiday_info["name"] if holiday_info else "",
            "is_bridge": is_bridge,
            "is_offday": is_offday,
            "score_jjuk": score_jjuk,
            "score_gap": score_gap,
            "tier": tier,
            "tier_desc": tier_desc,
            "advice": advice,
            "booking_priority": booking_priority
        }
        enriched_days.append(item)
        
        if is_offday or is_bridge:
            top_candidates.append(item)
            
    # TOP 15 랭킹 정렬 (예약 경쟁도 및 물때 우수성)
    top_candidates.sort(key=lambda x: (x["booking_priority"], max(x["score_jjuk"], x["score_gap"])), reverse=True)
    top_15 = top_candidates[:15]
    for idx, cand in enumerate(top_15, 1):
        cand["rank"] = idx
        
    summary = {
        "total_days": len(enriched_days),
        "offdays_count": sum(1 for d in enriched_days if d["is_offday"]),
        "s_tier_count": sum(1 for d in enriched_days if d["tier"] == "S"),
        "a_tier_count": sum(1 for d in enriched_days if d["tier"] == "A"),
        "top_15": [
            {
                "rank": c["rank"],
                "date": c["date"],
                "weekday": c["weekday"],
                "lunar": c["lunar"],
                "tide_name": c["tide_name"],
                "holiday_name": c["holiday_name"],
                "score_jjuk": c["score_jjuk"],
                "score_gap": c["score_gap"],
                "tier": c["tier"],
                "advice": c["advice"]
            }
            for c in top_15
        ],
        "days": enriched_days
    }
    
    with open(REC_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
        
    print(f"[2/2] 추천 데이터셋 저장 완료: {REC_JSON}")
    print(f"  - 총 일정: {summary['total_days']}일")
    print(f"  - 주말 및 공휴일: {summary['offdays_count']}일")
    print(f"  - S등급 초황금일: {summary['s_tier_count']}일")
    print(f"  - A등급 우수일: {summary['a_tier_count']}일")
    print("\n[🏆 2027 쭈갑시즌 광클 예약 필수 TOP 5]")
    for c in summary["top_15"][:5]:
        print(f"  {c['rank']}위 | {c['date']} ({c['weekday']}) | {c['tide_name']} | 쭈 {c['score_jjuk']}점 / 갑 {c['score_gap']}점 | {c['holiday_name'] or '주말'}")

if __name__ == "__main__":
    main()
