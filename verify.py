"""
MATE POS 원본 vs DB 검증 스크립트 (건별 리스트 기반)
- POS 건별 리스트 API 합계 vs DB 건별 합계 비교
- summary API 대신 실제 주문 데이터로 검증 → 더 정확
- 사용: python verify.py --start 20240301 --end 20240331
"""
import httpx
import asyncio
import argparse
import django
import os
import sys
from datetime import date, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db.models import Sum, Count, Q
from sale.models import Sale

# ── 설정 ─────────────────────────────────────────────────────
MATEPOS_BASE = "https://www.matetech.co.kr"
LOGIN_URL    = f"{MATEPOS_BASE}/login"
HQ_BRAND_ID  = "100201"
MS_STR_ID    = "1020869"
LIST_URL     = f"{MATEPOS_BASE}/api/sal0011/brands/{HQ_BRAND_ID}/stores/{MS_STR_ID}/sales/orders"

MATEPOS_USER_ID  = os.getenv("MATEPOS_USER_ID")
MATEPOS_PASSWORD = os.getenv("MATEPOS_PASSWORD")

HEADERS = {
    "Accept":           "application/json, text/javascript, */*; q=0.01",
    "Accept-Language":  "ko-KR,ko;q=0.9",
    "X-Requested-With": "XMLHttpRequest",
    "Referer":          f"{MATEPOS_BASE}/service/saa0010/sales/analysis/term-orders",
}

BASE_PARAMS = {
    "hqBrandId":      HQ_BRAND_ID,
    "msStrId":        MS_STR_ID,
    "strType":        "ONLY",
    "salesTermType":  "DAILY",
    "searchDate":     "oper",
    "orderTodayFlag": "N",
    "enpCd":          "mp_bnature",
    "corpCd":         "1001",
    "brandCd":        "20001",
    "onlineYn":       "",
    "orderType":      "",
    "returnYn":       "",
    "size":           20,
}


# ── 로그인 ────────────────────────────────────────────────────
async def login(client: httpx.AsyncClient) -> bool:
    resp = await client.post(
        LOGIN_URL,
        data={
            "autoSignOn": "",
            "userId":     MATEPOS_USER_ID,
            "pw":         MATEPOS_PASSWORD,
            "authToken":  "",
            "isAgree":    "false",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if resp.status_code not in (200, 302):
        return False
    print("[로그인 성공]")
    return True


# ── POS 건별 리스트 수집 → 일별 집계 ─────────────────────────
async def fetch_pos_daily(
    client: httpx.AsyncClient,
    target_date: str,
) -> dict:
    """
    하루치 건별 리스트를 수집해서 집계.
    반환: { "cnt": int, "amt": int }
    amt = actualSaleAmt 합계 (취소/반품 포함)
    """
    all_content = []
    page = 1
    total_page = 1

    while True:
        params = {
            **BASE_PARAMS,
            "operDt":     target_date,
            "operDtFrom": target_date,
            "operDtTo":   target_date,
            "page":       page,
        }
        resp = await client.get(LIST_URL, params=params)
        resp.raise_for_status()

        body       = resp.json()
        result     = body["data"]["result"]
        content    = result.get("content", [])
        total_page = result.get("totalPage", 1)
        all_content.extend(content)

        if page >= total_page:
            break
        page += 1
        await asyncio.sleep(0.2)

    # 완료 건수, 전체 금액 합계 (취소/반품 포함)
    cnt = sum(1 for o in all_content if o.get("cancelYn") != "Y")
    amt = sum(int(o.get("actualSaleAmt") or 0) for o in all_content)

    return {"cnt": cnt, "amt": amt}


# ── DB 일별 집계 ──────────────────────────────────────────────
def fetch_db_daily(target_date: str) -> dict:
    """
    DB 건별 집계.
    amt = actual_sale_amount - channel_discount 합계 (취소/반품 포함)
    """
    date_str = f"{target_date[:4]}-{target_date[4:6]}-{target_date[6:8]}"
    result = (
        Sale.objects
        .filter(business_date=date_str)
        .aggregate(
            cnt=Count('id', filter=Q(payment_status='결제완료')),
            amt=Sum('actual_sale_amount') - Sum('channel_discount'),
        )
    )
    return {
        "cnt": result['cnt'] or 0,
        "amt": result['amt'] or 0,
    }


# ── 날짜 범위 생성 ─────────────────────────────────────────────
def date_range(start: str, end: str) -> list[str]:
    s = date(int(start[:4]), int(start[4:6]), int(start[6:8]))
    e = date(int(end[:4]),   int(end[4:6]),   int(end[6:8]))
    days, cur = [], s
    while cur <= e:
        days.append(cur.strftime("%Y%m%d"))
        cur += timedelta(days=1)
    return days


# ── 메인 ─────────────────────────────────────────────────────
async def run(start: str, end: str):
    print(f"검증 범위: {start} ~ {end}")

    days = date_range(start, end)

    ok_count      = 0
    mismatch_days = []
    missing_days  = []
    skip_days     = 0

    from asgiref.sync import sync_to_async

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=20) as client:
        if not await login(client):
            return

        for day in days:
            pos = await fetch_pos_daily(client, day)
            db  = await sync_to_async(fetch_db_daily)(day)

            # 둘 다 0건이면 영업 안 한 날 → 스킵
            if pos["cnt"] == 0 and db["cnt"] == 0:
                skip_days += 1
                continue

            # POS엔 있는데 DB에 없으면 → 미수집
            if pos["cnt"] > 0 and db["cnt"] == 0:
                missing_days.append((day, pos))
                continue

            diff_cnt = db["cnt"] - pos["cnt"]
            diff_amt = db["amt"] - pos["amt"]

            if diff_cnt != 0 or diff_amt != 0:
                mismatch_days.append((day, pos, db, diff_cnt, diff_amt))
            else:
                ok_count += 1

            await asyncio.sleep(0.3)

    # ── 결과 출력 ─────────────────────────────────────────────
    W = 12
    print()
    print("=" * 65)
    print("검증 결과")
    print("=" * 65)
    print(f"일치      : {ok_count}일")
    print(f"불일치    : {len(mismatch_days)}일")
    print(f"미수집    : {len(missing_days)}일")
    print(f"휴무      : {skip_days}일")

    if mismatch_days:
        print()
        print(f"{'날짜':<10} {'POS건수':>6} {'POS금액':>{W}} {'DB건수':>6} {'DB금액':>{W}} {'건수차':>6} {'금액차':>{W}}")
        print("-" * 65)
        for day, pos, db, diff_cnt, diff_amt in mismatch_days:
            d = f"{day[:4]}-{day[4:6]}-{day[6:8]}"
            print(
                f"{d:<10} "
                f"{pos['cnt']:>6} {pos['amt']:>{W},} "
                f"{db['cnt']:>6} {db['amt']:>{W},} "
                f"{diff_cnt:>+6} {diff_amt:>{W},}"
            )

    if missing_days:
        print()
        print("── 미수집 날짜 (재수집 필요) ──────────────────────────")
        for day, pos in missing_days:
            d = f"{day[:4]}-{day[4:6]}-{day[6:8]}"
            print(f"  {d}  POS {pos['cnt']}건  {pos['amt']:,}원")
        print()
        print("재수집 명령:")
        for day, _ in missing_days:
            print(f"  python scraper.py --start {day} --end {day}")

    print("=" * 65)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", required=True, help="시작일 YYYYMMDD")
    parser.add_argument("--end",   required=True, help="종료일 YYYYMMDD")
    args = parser.parse_args()

    asyncio.run(run(args.start, args.end))