"""
불일치 날짜 진단 스크립트
- 사용: python diagnose.py
"""
import os
import sys
import django
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from sale.models import Sale

# ── 확인할 날짜 목록 ──────────────────────────────────────────
CHECK_DATES = [
    "2024-03-01",
    "2024-03-02",
    "2024-03-10",
    "2024-03-15",
]

for d in CHECK_DATES:
    sales = Sale.objects.filter(business_date=d).order_by('order_seq')
    print(f"\n{'='*50}")
    print(f"[{d}] 총 {sales.count()}건")
    print(f"{'='*50}")
    print(f"{'seq':>4}  {'상태':<8}  {'채널':<10}  {'실매출':>10}  {'sold_at'}")
    print("-" * 60)
    for s in sales:
        print(
            f"{s.order_seq:>4}  "
            f"{s.payment_status:<8}  "
            f"{s.channel:<10}  "
            f"{s.actual_sale_amount:>10,}  "
            f"{s.sold_at}"
        )