from decimal import Decimal
from .models import Account, JournalEntry, JournalLine

# 계정코드 상수 (초기 데이터로 Account에 등록되어 있어야 함)
ACC_INVENTORY_EXPENSE = "5000"   # 원재료비(비용) 또는 재고자산을 쓰려면 별도 코드 사용
ACC_AP = "2000"                  # 매입채무(부채)
ACC_AR = "1100"                  # 매출채권(자산)
ACC_REVENUE = "4000"             # 매출(수익)

def get_account(code: str) -> Account:
    return Account.objects.get(code=code)

def upsert_purchase_entry(purchase, amount: Decimal):
    """
    Purchase 생성/수정 시 분개를 생성 또는 업데이트.
    - 차변: 원재료비(5000)
    - 대변: 매입채무(2000)
    """
    entry, created = JournalEntry.objects.get_or_create(
        source_type="PURCHASE",
        source_id=purchase.id,
        defaults={
            "date": purchase.purchased_at.date(),
            "description": f"Purchase {purchase.id}",
        }
    )
    if not created:
        entry.date = purchase.purchased_at.date()
        entry.description = f"Purchase {purchase.id}"
        entry.save()

    # 라인 두 개를 upsert
    lines = list(entry.lines.all())
    if len(lines) == 0:
        JournalLine.objects.create(
            entry=entry,
            account=get_account(ACC_INVENTORY_EXPENSE),
            party=purchase.party,
            debit=amount,
            credit=Decimal("0"),
        )
        JournalLine.objects.create(
            entry=entry,
            account=get_account(ACC_AP),
            party=purchase.party,
            debit=Decimal("0"),
            credit=amount,
        )
    else:
        # 첫 번째 라인: 비용(차변)
        expense_line = next((l for l in lines if l.account.code == ACC_INVENTORY_EXPENSE), None)
        ap_line = next((l for l in lines if l.account.code == ACC_AP), None)

        if expense_line:
            expense_line.debit = amount
            expense_line.credit = Decimal("0")
            expense_line.party = purchase.party
            expense_line.save()
        else:
            JournalLine.objects.create(
                entry=entry,
                account=get_account(ACC_INVENTORY_EXPENSE),
                party=purchase.party,
                debit=amount,
                credit=Decimal("0"),
            )

        if ap_line:
            ap_line.debit = Decimal("0")
            ap_line.credit = amount
            ap_line.party = purchase.party
            ap_line.save()
        else:
            JournalLine.objects.create(
                entry=entry,
                account=get_account(ACC_AP),
                party=purchase.party,
                debit=Decimal("0"),
                credit=amount,
            )

def delete_purchase_entry(purchase_id: int):
    JournalEntry.objects.filter(source_type="PURCHASE", source_id=purchase_id).delete()

def upsert_sale_entry(sale, amount: Decimal):
    """
    Sale 생성/수정 시 분개를 생성 또는 업데이트.
    - 차변: 매출채권(1100) 또는 현금(자산) — 여기서는 매출채권으로 가정
    - 대변: 매출(4000)
    """
    entry, created = JournalEntry.objects.get_or_create(
        source_type="SALE",
        source_id=sale.id,
        defaults={
            "date": sale.sold_at.date(),
            "description": f"Sale {sale.id}",
        }
    )
    if not created:
        entry.date = sale.sold_at.date()
        entry.description = f"Sale {sale.id}"
        entry.save()

    lines = list(entry.lines.all())
    if len(lines) == 0:
        JournalLine.objects.create(
            entry=entry,
            account=get_account(ACC_AR),
            party=sale.party,
            debit=amount,
            credit=Decimal("0"),
        )
        JournalLine.objects.create(
            entry=entry,
            account=get_account(ACC_REVENUE),
            party=sale.party,
            debit=Decimal("0"),
            credit=amount,
        )
    else:
        ar_line = next((l for l in lines if l.account.code == ACC_AR), None)
        rev_line = next((l for l in lines if l.account.code == ACC_REVENUE), None)

        if ar_line:
            ar_line.debit = amount
            ar_line.credit = Decimal("0")
            ar_line.party = sale.party
            ar_line.save()
        else:
            JournalLine.objects.create(
                entry=entry,
                account=get_account(ACC_AR),
                party=sale.party,
                debit=amount,
                credit=Decimal("0"),
            )

        if rev_line:
            rev_line.debit = Decimal("0")
            rev_line.credit = amount
            rev_line.party = sale.party
            rev_line.save()
        else:
            JournalLine.objects.create(
                entry=entry,
                account=get_account(ACC_REVENUE),
                party=sale.party,
                debit=Decimal("0"),
                credit=amount,
            )

def delete_sale_entry(sale_id: int):
    JournalEntry.objects.filter(source_type="SALE", source_id=sale_id).delete()