#!/usr/bin/env python3
"""
recommend_jeju_engine.py
2027년 상반기 제주 심해갑오징어 (1월 1일 ~ 5월 31일, 151일간) 물때 데이터 기반:
- 70~110m 심해 풍닻 드리프트 특성에 맞춘 스코어링 (사리권 5~7물 스윗스팟)
- 대포알 영등철(1~3월) 및 봄 산란 마릿수 피크(4~5월) 시즌 가중치
- 주말/공휴일(신정, 설 연휴 4일, 삼일절 3일, 5월 황금연휴) 분석 및 TOP 15 필수 예약일 산출
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_JSON = DATA_DIR / "season_2027_jeju_raw.json"
REC_JSON = DATA_DIR / "season_2027_jeju_recommend.json"

HOLIDAYS_JEJU_2027 = {
    "2027-01-01": {"name": "신정", "type": "national"},
    "2027-02-06": {"name": "설날 연휴", "type": "seollal"},
    "2027-02-07": {"name": "설날", "type": "seollal"},
    "2027-02-08": {"name": "설날 연휴", "type": "seollal"},
    "2027-02-09": {"name": "설날 대체공휴일", "type": "substitute"},
    "2027-03-01": {"name": "삼일절", "type": "national"},
    "2027-05-05": {"name": "어린이날", "type": "national"},
    "2027-05-13": {"name": "부처님오신날", "type": "national"}
}

BRIDGE_DAYS_JEJU_2027 = {
    "2027-02-05": "설 연휴 전 금요일 연차 시 5일 황금연휴 출조 찬스 (2/5~2/9)",
    "2027-05-06": "어린이날 브릿지 연차 권장 (5/5~5/9 5일 연속 출조 가능)",
    "2027-05-07": "어린이날 브릿지 연차 권장 (5/5~5/9 5일 연속 출조 가능)",
    "2027-05-14": "부처님오신날 샌드위치 연차 권장 (5/13~5/16 4일 연휴 완성)"
}

def calc_deep_gap_score(date_str: str, tide_name: str, tide_num: int):
    """
    제주 심해갑오징어 전용 스코어링 (0~100점)
    - 70~110m 심해에서 풍닻을 펴고 배를 조류에 흘리므로 사리 전후(4~8물)가 배가 잘 흘러 탐색 면적 극대화!
    - 조금/무시는 배가 멈춰 서서 바닥 탐색 불가, 조황 극도로 저조!
    """
    # 1. 물때 기본 점수
    if tide_num in [5, 6, 7]:
        tide_score = 100 # 풍닻 드리프트 황금 물때
    elif tide_num in [4, 8]:
        tide_score = 95
    elif tide_num in [9, 10]:
        tide_score = 90
    elif tide_num in [3, 11]:
        tide_score = 80
    elif tide_num in [2, 12]:
        tide_score = 68
    elif tide_num in [1, 13]:
        tide_score = 55
    elif tide_name == "무시":
        tide_score = 40
    elif tide_name == "조금":
        tide_score = 35
    else:
        tide_score = 50

    # 2. 시즌 가중치
    month = int(date_str.split('-')[1])
    day = int(date_str.split('-')[2])
    
    # 1월 중순 ~ 3월 중순: 대포알 영등철 피크
    # 4월 ~ 5월 중순: 봄 산란 마릿수 피크
    if month in [1, 2, 3]:
        size_potential = "대포알·신발짝 몬스터급 (1kg~1.5kg+)"
    else:
        size_potential = "봄 산란 마릿수 폭발 찬스"

    return tide_score, size_potential

def determine_tier(score: int, is_offday: bool):
    """
    추천 티어 판정 (S / A / B / C)
    """
    if is_offday:
        if score >= 90:
            return "S", "🌟 초황금 예약일"
        elif score >= 75:
            return "A", "✨ 우수 추천일"
        elif score >= 55:
            return "B", "🔹 무난한 출조일"
        else:
            return "C", "⚠️ 조금·주의일"
    else:
        if score >= 95:
            return "S", "🌟 평일 초황금일 (연차 강추)"
        elif score >= 85:
            return "A", "✨ 평일 우수일"
        elif score >= 65:
            return "B", "🔹 평일 출조일"
        else:
            return "C", "⚠️ 조금·주의일"

def generate_advice(date_str: str, tide_name: str, tide_num: int, tier: str, is_offday: bool, holiday_name: str, size_potential: str):
    m = int(date_str.split('-')[1])
    
    prefix = ""
    if holiday_name:
        prefix = f"[{holiday_name}] "
    elif is_offday:
        prefix = "[주말 찬스] "

    tide_desc = ""
    if tide_num in [5, 6, 7]:
        tide_desc = f"{tide_name} 조류 완벽. 풍닻 드리프트 탐색 효율 극대화."
    elif tide_num in [4, 8, 9]:
        tide_desc = f"{tide_name} 시원한 조류 흐름. 넓은 바닥 공략 가능."
    elif tide_num in [2, 3, 10, 11]:
        tide_desc = f"{tide_name} 완만한 조류. 40~50호 봉돌로 바닥 집중 탐색."
    else:
        tide_desc = f"{tide_name} 조류 약함. 풍닻 흘림 둔화로 바닥 집중 요망."

    if m in [1, 2, 3]:
        season_advice = "수온 14~15도 유지 구간. 대포알급(1kg+) 출현 빈도 최고."
    else:
        season_advice = "수온 상승기. 4~5단 오모리그 채비 및 마릿수 마구잡이 공략."

    gear_advice = "봉돌 40~50호, 수심 70~100m, 합사 0.8~1.0호, 전동릴 또는 하이기어 베이트릴 추천."

    return f"{prefix}{tide_desc} {size_potential}. {season_advice} ({gear_advice})"

def main():
    if not RAW_JSON.exists():
        raise FileNotFoundError(f"원시 데이터 파일이 없습니다: {RAW_JSON}")
        
    with open(RAW_JSON, "r", encoding="utf-8") as f:
        raw_days = json.load(f)
        
    print(f"[recommend_jeju] 총 {len(raw_days)}일 데이터 분석 시작...")
    
    processed_days = []
    
    for d in raw_days:
        date_str = d["date"]
        tide_name = d["tide_name"]
        tide_num = d["tide_num"]
        is_weekend = d["is_weekend"]
        
        # 공휴일 체크
        holiday_info = HOLIDAYS_JEJU_2027.get(date_str)
        is_holiday = holiday_info is not None
        holiday_name = holiday_info["name"] if holiday_info else ""
        
        # 징검다리 연차 체크
        is_bridge = date_str in BRIDGE_DAYS_JEJU_2027
        
        # 휴일 판정
        is_offday = is_weekend or is_holiday
        
        # 심해갑 스코어 계산
        score_deep_gap, size_potential = calc_deep_gap_score(date_str, tide_name, tide_num)
        
        # 티어 판정
        tier, tier_desc = determine_tier(score_deep_gap, is_offday)
        
        # 출조 가이드 문구
        advice = generate_advice(date_str, tide_name, tide_num, tier, is_offday, holiday_name, size_potential)
        
        # 예약 우선순위 점수
        priority = score_deep_gap
        if is_offday:
            priority += 20
        if is_holiday:
            priority += 10
        if is_bridge:
            priority += 5
            
        processed_days.append({
            "date": date_str,
            "day": d["day"],
            "weekday": d["weekday"],
            "is_weekend": is_weekend,
            "lunar": d["lunar"],
            "tide_name": tide_name,
            "tide_num": tide_num,
            "tide_events": d["tide_events"],
            "tide_diff": d["tide_diff"],
            "sunrise": d["sunrise"],
            "sunset": d["sunset"],
            "is_holiday": is_holiday,
            "holiday_name": holiday_name,
            "is_bridge": is_bridge,
            "is_offday": is_offday,
            "score_deep_gap": score_deep_gap,
            "size_potential": size_potential,
            "tier": tier,
            "tier_desc": tier_desc,
            "advice": advice,
            "booking_priority": priority
        })
        
    # TOP 15 필수 예약일 산출
    # 주말 및 공휴일 우선, 점수 순
    candidates = [x for x in processed_days if x["is_offday"]]
    candidates.sort(key=lambda x: (x["booking_priority"], x["score_deep_gap"]), reverse=True)
    top_15 = []
    for rank, item in enumerate(candidates[:15], 1):
        top_15.append({
            "rank": rank,
            "date": item["date"],
            "weekday": item["weekday"],
            "lunar": item["lunar"],
            "tide_name": item["tide_name"],
            "tier": item["tier"],
            "score_deep_gap": item["score_deep_gap"],
            "holiday_name": item["holiday_name"],
            "advice": item["advice"]
        })
        
    s_count = sum(1 for x in processed_days if x["tier"] == "S")
    a_count = sum(1 for x in processed_days if x["tier"] == "A")
    offdays_count = sum(1 for x in processed_days if x["is_offday"])
    
    result = {
        "season_name": "2027 상반기 제주 심해갑오징어",
        "target_species": "제주 심해갑오징어 (70~110m 풍닻 드리프트)",
        "port_base": "한림항·신창항·차귀도 (제주 서부)",
        "total_days": len(processed_days),
        "offdays_count": offdays_count,
        "s_tier_count": s_count,
        "a_tier_count": a_count,
        "top_15": top_15,
        "days": processed_days
    }
    
    with open(REC_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        
    print(f"\n[recommend_jeju] 분석 완료!")
    print(f"  - 총 일정: {len(processed_days)}일")
    print(f"  - 주말 및 공휴일: {offdays_count}일")
    print(f"  - S등급 초황금일: {s_count}일")
    print(f"  - A등급 우수일: {a_count}일")
    print(f"  - TOP 15 예약 추천일 선정 완료")
    print(f"  - 저장 완료: {REC_JSON}")

if __name__ == "__main__":
    main()
