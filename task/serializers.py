from rest_framework import serializers
from task.models import Task,TaskUpdate

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "created_by"]

    def validate(self, attrs):
            title = attrs.get("title")
            assigned_to = attrs.get("assigned_to")

            if Task.objects.filter(title=title, assigned_to=assigned_to).exists():
                raise serializers.ValidationError(
                    {"assigned_to": f"Task '{title}' is already assigned to {assigned_to.email}."}
                )

            return attrs

class TaskUpdateSerializer(serializers.ModelSerializer):
    updated_by = serializers.ReadOnlyField(source="updated_by.email")
    task = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model=TaskUpdate
        fields="__all__"
        read_only_fields=["id","updated_by","created_at"]