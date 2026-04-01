# core/utils/money.py

def format_money(value):
    """
    금액을 3자리 콤마로 변환.
    """
    if value is None:
        return "0"
    return f"{value:,}"


def calculate_tax(amount, tax_rate=0.1):
    """
    부가세 계산 (기본 10%)
    """
    return int(amount * tax_rate)
