from rest_framework.serializers import ModelSerializer, UUIDField
from .models import User

# User serializer with UUID support
class UserSerializer(ModelSerializer):
    id = UUIDField(read_only=True)
    
    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "first_name", "last_name", "is_vendor", "is_customer")
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        # Create user with UUID as primary key (handled by default)
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            is_vendor=validated_data.get("is_vendor", False),
            is_customer=validated_data.get("is_customer", True),
        )
        return user
