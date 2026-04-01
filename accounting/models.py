from django.db import models
from core.models.base import BaseModel
from party.models import Party

class Account(BaseModel):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    type = models.CharField(
        max_length=20,
        choices=[
            ("ASSET", "자산"),
            ("LIABILITY", "부채"),
            ("EQUITY", "자본"),
            ("REVENUE", "수익"),
            ("EXPENSE", "비용"),
        ]
    )

    def __str__(self):
        return f"{self.code} | {self.name}"

class JournalEntry(BaseModel):
    date = models.DateField()
    description = models.CharField(max_length=255, blank=True, null=True)

    # 원본 거래 연결 (간단한 방식)
    source_type = models.CharField(max_length=20, choices=[("PURCHASE", "Purchase"), ("SALE", "Sale")])
    source_id = models.PositiveIntegerField()

    class Meta:
        indexes = [
            models.Index(fields=["source_type", "source_id"]),
        ]

    def __str__(self):
        return f"{self.date} | {self.description}"

class JournalLine(BaseModel):
    entry = models.ForeignKey(JournalEntry, related_name="lines", on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    party = models.ForeignKey(Party, on_delete=models.SET_NULL, blank=True, null=True)
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.account.name} | D:{self.debit} C:{self.credit}"