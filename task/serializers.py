from rest_framework import serializers
from task.models import Task,TaskUpdate

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "created_by"]

class TaskUpdateSerializer(serializers.ModelSerializer):
    updated_by = serializers.ReadOnlyField(source="updated_by.email")
    task = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model=TaskUpdate
        fields="__all__"
        read_only_fields=["id","updated_by","created_at"]