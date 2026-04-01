# product/serializers.py
from rest_framework import serializers
from .models import Product, BOM
from core.utils.bom_utils import check_bom_cycle


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id", "code", "name", "spec",
            "base_unit", "purchase_unit", "purchase_conversion_factor",
            "sales_unit", "sales_conversion_factor",
            "is_resell", "is_active",
            "created_at", "updated_at",
        ]

    def validate(self, attrs):
        # 단위 표준화
        for unit_field in ["base_unit", "purchase_unit", "sales_unit"]:
            if unit_field in attrs and not attrs[unit_field].strip():
                attrs[unit_field] = "EA"

        # code가 빈 문자열이면 None 처리
        code = attrs.get("code")
        if code is not None and not code.strip():
            attrs["code"] = None

        return attrs


class BOMSerializer(serializers.ModelSerializer):
    parent_detail = ProductSerializer(source="parent", read_only=True)
    component_detail = ProductSerializer(source="component", read_only=True)

    class Meta:
        model = BOM
        fields = [
            "id", "parent", "component", "quantity",
            "parent_detail", "component_detail",
            "is_active", "created_at", "updated_at",
        ]

    def validate(self, attrs):
        parent = attrs.get("parent")
        component = attrs.get("component")

        # 자기 자신 참조 방지
        if parent and component and parent.id == component.id:
            raise serializers.ValidationError(
                {"component": "BOM에서 parent와 component는 동일할 수 없습니다."}
            )

        # 순환 참조 방지 (DFS 기반)
        if parent and component and check_bom_cycle(parent, component):
            raise serializers.ValidationError(
                {"component": "이 관계는 순환 BOM을 만들어 허용되지 않습니다."}
            )

        # 수량 검증
        qty = attrs.get("quantity")
        if qty is not None and qty <= 0:
            raise serializers.ValidationError(
                {"quantity": "BOM 수량은 0보다 커야 합니다."}
            )

        return attrs
