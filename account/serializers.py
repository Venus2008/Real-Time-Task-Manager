from rest_framework import serializers
from account.models import User

class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "email", "role"]
        read_only_fields = ["id"]

    def validate_role(self, value):
        allowed = {"ADMIN", "MANAGER", "EMPLOYEE"}
        if value not in allowed:
            raise serializers.ValidationError("Invalid role.")
        return value

class SetPasswordSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(min_length=8, write_only=True)

class UserMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "email", "role"]
        read_only_fields = fields


class AdminSignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "name", "email", "password"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.role = "ADMIN"         
        user.is_active = True       
        user.set_password(password) 
        user.save()
        return user