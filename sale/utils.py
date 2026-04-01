import re
from product.models import ProductAlias, Product


def normalize_name(name: str) -> str:
    """
    상품명 정규화
    - [신메뉴], (특) 제거
    - 공백 정리
    """

    if not name:
        return ""

    name = name.strip()

    name = re.sub(r"\[.*?\]", "", name)
    name = re.sub(r"\(.*?\)", "", name)
    name = re.sub(r"\s+", " ", name)

    return name.strip()

def get_or_map_product(name):
    """
    상품 매핑 로직

    1. alias 테이블에서 찾기
    2. 정규화 후 Product 찾기
    3. 없으면 Product 생성 + alias 생성
    """

    alias = ProductAlias.objects.filter(name=name).first()
    if alias:
        return alias.product

    normalized = normalize_name(name)

    product = Product.objects.filter(name=normalized).first()
    if product:
        ProductAlias.objects.create(name=name, product=product)
        return product

    product = Product.objects.create(
        name=normalized,
        is_stock_managed=False
    )

    ProductAlias.objects.create(name=name, product=product)

    return product