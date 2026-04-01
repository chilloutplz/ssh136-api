from rest_framework import serializers
from organization.models.branch import Branch
from organization.models.brand import Brand

# 조회용 Serializer
class BranchSerializer(serializers.ModelSerializer):
    brand_id = serializers.IntegerField(source="brand.id", read_only=True)
    brand_name = serializers.CharField(source="brand.name", read_only=True)
    company_name = serializers.CharField(source="brand.company.name", read_only=True)  # ✅ 추가

    class Meta:
        model = Branch
        fields = [
            "id", "brand_id", "brand_name", "company_name",
            "name", "representative", "postcode",
            "base_address", "detail_address", "phone", "email", "description"
        ]

# 생성/수정용 Serializer
class BranchCreateUpdateSerializer(serializers.ModelSerializer):
    brand = serializers.PrimaryKeyRelatedField(queryset=Brand.objects.all())

    class Meta:
        model = Branch
        fields = [
            "brand", "name", "representative", "postcode",
            "base_address", "detail_address", "phone", "email", "description"
        ]