# accounts/serializers/user_serializers.py
from rest_framework import serializers
from accounts.models.user import User

# 유저 정보 조회용
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "name", "phone", "date_joined"]
        read_only_fields = ["id", "email", "date_joined"]

# 유저 정보 수정용
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["name", "phone"]
