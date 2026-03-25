from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'role', 'phone', 'avatar', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name',
                  'role', 'phone', 'password', 'password2']

    def validate_role(self, value):
        if value not in ['admin', 'manager']:
            raise serializers.ValidationError("Role must be 'admin' or 'manager'.")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords don't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'role', 'phone', 'is_active']

    def validate_role(self, value):
        if value not in ['admin', 'manager']:
            raise serializers.ValidationError("Role must be 'admin' or 'manager'.")
        return value


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
