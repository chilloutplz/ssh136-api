from product.models import Product, ProductAlias
from sale.utils import normalize_name


def get_or_map_product(name):
    """
    상품 매핑

    1. alias 조회
    2. 정규화 후 조회
    3. 없으면 생성
    """

    if not name:
        name = "Unknown"

    # 1️⃣ alias
    alias = ProductAlias.objects.filter(name=name).first()
    if alias:
        return alias.product

    # 2️⃣ 정규화
    normalized = normalize_name(name)

    product = Product.objects.filter(name=normalized).first()
    if product:
        ProductAlias.objects.create(name=name, product=product)
        return product

    # 3️⃣ 생성
    product = Product.objects.create(
        name=normalized,
        is_stock_managed=False
    )

    ProductAlias.objects.create(name=name, product=product)

    return product