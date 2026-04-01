"""
API vs DB 주문 비교 스크립트
- API trSeq/금액 과 DB order_seq/금액 을 각각 나란히 표시
- verify 집계 금액도 함께 출력
- 사용: python compare_sales.py
- 날짜 변경: COMPARE_DATE 수정
"""
import httpx
import asyncio
import django
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db.models import Sum, Count, Q
from sale.models import Sale

# ── 확인할 날짜 ───────────────────────────────────────────────
COMPARE_DATE = "20240622"

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


# ── API 리스트 수집 ───────────────────────────────────────────
async def fetch_api_list(client: httpx.AsyncClient, target_date: str) -> list[dict]:
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
        body       = resp.json()
        result     = body["data"]["result"]
        content    = result.get("content", [])
        total_page = result.get("totalPage", 1)
        all_content.extend(content)

        if page >= total_page:
            break
        page += 1
        await asyncio.sleep(0.2)

    return sorted(all_content, key=lambda x: int(x.get("trSeq", 0)))


# ── DB 수집 ───────────────────────────────────────────────────
def fetch_db_list(target_date: str) -> list[dict]:
    date_str = f"{target_date[:4]}-{target_date[4:6]}-{target_date[6:8]}"
    return list(
        Sale.objects
        .filter(business_date=date_str)
        .order_by('order_seq')
        .values(
            'order_seq', 'channel', 'payment_status',
            'actual_sale_amount', 'channel_discount', 'org_business_date'
        )
    )


# ── verify 집계 ───────────────────────────────────────────────
def fetch_verify_totals(target_date: str) -> dict:
    """verify.py 와 동일한 집계 로직"""
    date_str = f"{target_date[:4]}-{target_date[4:6]}-{target_date[6:8]}"

    # 정상+취소 건 (반품 제외)
    normal = (
        Sale.objects
        .filter(business_date=date_str, org_business_date__isnull=True)
        .aggregate(
            cnt=Count('id', filter=Q(payment_status='결제완료')),
            amt=Sum('actual_sale_amount') - Sum('channel_discount'),
        )
    )

    # 반품 건
    returns = (
        Sale.objects
        .filter(business_date=date_str, org_business_date__isnull=False)
        .aggregate(
            cnt=Count('id'),
            amt=Sum('actual_sale_amount'),
        )
    )

    return {
        "normal_cnt": normal['cnt'] or 0,
        "normal_amt": normal['amt'] or 0,
        "return_cnt": returns['cnt'] or 0,
        "return_amt": returns['amt'] or 0,
        "total_amt":  (normal['amt'] or 0) + (returns['amt'] or 0),
    }


# ── 비교 출력 ─────────────────────────────────────────────────
def print_comparison(api_list: list[dict], db_list: list[dict], verify: dict):
    W = 10

    # API 정리
    api_rows = [
        {
            "seq":    int(o.get("trSeq", 0)),
            "channel": str(o.get("channelCd") or ""),
            "status": "취소" if o.get("cancelYn") == "Y" else ("반품" if o.get("returnYn") == "Y" else "완료"),
            "amt":    int(o.get("actualSaleAmt") or 0),
        }
        for o in api_list
    ]

    # DB 정리
    db_rows = [
        {
            "seq":    row['order_seq'],
            "channel": row['channel'],
            "status": "취소" if row['payment_status'] == '결제취소' else ("반품" if row['org_business_date'] else "완료"),
            "amt":    row['actual_sale_amount'] - row['channel_discount'],
        }
        for row in db_list
    ]

    max_rows = max(len(api_rows), len(db_rows))

    SEP = "  │  "
    HDR = f"{'API seq':>7} {'채널':<8} {'금액':>{W}} {'상태':^4}{SEP}{'DB seq':>6} {'채널':<8} {'금액':>{W}} {'상태':^4}"

    print()
    print("=" * len(HDR))
    print(f"비교 날짜: {COMPARE_DATE}")
    print("=" * len(HDR))
    print(HDR)
    print("-" * len(HDR))

    api_total = 0
    db_total  = 0

    for i in range(max_rows):
        a = api_rows[i] if i < len(api_rows) else None
        d = db_rows[i]  if i < len(db_rows)  else None

        a_str = (
            f"{a['seq']:>7} {a['channel']:<8} {a['amt']:>{W},} {a['status']:^4}"
            if a else f"{'':>7} {'':8} {'':>{W}} {'':4}"
        )
        d_str = (
            f"{d['seq']:>6} {d['channel']:<8} {d['amt']:>{W},} {d['status']:^4}"
            if d else f"{'':>6} {'':8} {'':>{W}} {'':4}"
        )

        if a: api_total += a['amt']
        if d: db_total  += d['amt']

        print(f"{a_str}{SEP}{d_str}")

    print("-" * len(HDR))
    print(
        f"{'합계':>7} {'':8} {api_total:>{W},} {'':4}{SEP}"
        f"{'':>6} {'':8} {db_total:>{W},}"
    )
    print("=" * len(HDR))
    print(f"API {len(api_rows)}건  /  DB {len(db_rows)}건")

    # ── verify 집계 ───────────────────────────────────────────
    print()
    print("── verify 집계 ─────────────────────────────────────────")
    print(f"  DB 정상매출  : {verify['normal_cnt']:>3}건  {verify['normal_amt']:>12,}원")
    print(f"  DB 반품매출  : {verify['return_cnt']:>3}건  {verify['return_amt']:>12,}원")
    print(f"  DB 합계      :        {verify['total_amt']:>12,}원")
    print(f"  API 합계     :        {api_total:>12,}원")
    diff = verify['normal_amt'] - api_total
    print(f"  차이(정상-API):       {diff:>+12,}원  {'✓ 일치' if diff == 0 else '← 불일치'}")
    print("─" * 55)


# ── 메인 ─────────────────────────────────────────────────────
async def run():
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=20) as client:
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
            print("[로그인 실패]")
            return
        print("[로그인 성공]")

        api_list = await fetch_api_list(client, COMPARE_DATE)

    from asgiref.sync import sync_to_async
    db_list = await sync_to_async(fetch_db_list)(COMPARE_DATE)
    verify  = await sync_to_async(fetch_verify_totals)(COMPARE_DATE)

    print_comparison(api_list, db_list, verify)


if __name__ == "__main__":
    asyncio.run(run())