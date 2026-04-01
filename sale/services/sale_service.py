from decimal import Decimal
from sale.models import Sale, SaleItem
from sale.services.product_mapper import get_or_map_product


def create_matepos_sale(validated_data):
    """
    MatePOS 주문 생성

    - 재고 처리 없음
    - 회계 처리 없음
    - 상품 자동 매핑
    """

    items_data = validated_data.pop("items", [])

    sale = Sale.objects.create(**validated_data)

    total = Decimal("0")

    for item in items_data:
        product_name = item.get("name")

        product = get_or_map_product(product_name)

        si = SaleItem.objects.create(
            sale=sale,
            product=product,
            quantity=item.get("quantity", 1),
            unit_price=item.get("unit_price", 0),
            discount=item.get("discount", 0),
        )

        total += (
            Decimal(si.quantity) * Decimal(si.unit_price)
            - Decimal(si.discount or 0)
        )

    sale.total_price = total
    sale.save(update_fields=["total_price"])

    return sale