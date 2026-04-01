# accounts/serializers/auth_serializer.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

# 관리자용 유저 승인 처리
class ApproveUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "name", "status"]

    def update(self, instance, validated_data):
        # 관리자 승인 처리
        instance.status = validated_data.get("status", instance.status)
        instance.save()
        return instance


# 회원가입
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "password", "name", "phone", "company_id", "brand_id", "branch_id"]

    # 이메일 중복 체크
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("이미 등록된 이메일입니다.")
        return value

    # 비밀번호 검증 (Django 기본 password validators 적용)
    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],  # create_user 내부에서 set_password 처리
            name=validated_data.get("name", ""),
            phone=validated_data.get("phone", ""),
            company_id=validated_data.get("company_id"),
            brand_id=validated_data.get("brand_id"),
            branch_id=validated_data.get("branch_id"),
            status="pending",  # 가입 시 기본 상태
        )
        return user

# 로그인 + JWT 발급
class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        # 사용자 상태 체크
        if self.user.status == "pending":
            raise serializers.ValidationError({
                "status": "pending",
                "detail": "관리자 승인 대기 중입니다."
            })
        elif self.user.status == "rejected":
            raise serializers.ValidationError({
                "status": "rejected",
                "detail": "가입이 거절되었습니다."
            })

        # 추가 정보 포함
        data["user"] = {
            "id": self.user.id,
            "email": self.user.email,
            "name": self.user.name,
            "status": self.user.status,  # ✅ 여기서도 포함
        }

        return data
