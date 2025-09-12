from rest_framework import serializers
from notifications.models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    task_title = serializers.CharField(source="task.title",read_only=True)
    class Meta:
        model=Notification
        fields=["id", "event", "task", "task_title", "status", "message", "is_read", "created_at"]