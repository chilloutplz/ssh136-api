from rest_framework import serializers
from organization.models.brand import Brand
from organization.models.company import Company

# 브랜드 조회용 Serializer
class BrandSerializer(serializers.ModelSerializer):
    company_id = serializers.IntegerField(source="company.id", read_only=True)
    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = Brand
        fields = ["id", "name", "description", "company_id", "company_name"]


# 브랜드 생성/수정용 Serializer
class BrandCreateUpdateSerializer(serializers.ModelSerializer):
    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all())

    class Meta:
        model = Brand
        fields = ["name", "description", "company"]