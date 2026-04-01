from rest_framework import serializers
from organization.models.company import Company, UserCompanyRole
from accounts.models.user import User


# CompanyMembership Serializer
class CompanyMembershipSerializer(serializers.ModelSerializer):
    company_id = serializers.IntegerField(source="company.id", read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.name", read_only=True)

    class Meta:
        model = UserCompanyRole
        fields = ["company_id","user_id", "user_email", "user_name", "role"]


# Company Serializer (조회용, 멤버 포함)
class CompanySerializer(serializers.ModelSerializer):
    members = CompanyMembershipSerializer(many=True, read_only=True)

    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "representative",
            "business_number",
            "postcode",
            "base_address",
            "detail_address",
            "phone",
            "fax",
            "email",
            "members",
        ]


# Company 생성/수정용 Serializer (멤버 포함 X)
class CompanyCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            "name",
            "representative",
            "business_number",
            "postcode",
            "base_address",
            "detail_address",
            "phone",
            "fax",
            "email",
        ]