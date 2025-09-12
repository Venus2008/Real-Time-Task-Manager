from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Notification

class NotificationService:
    @staticmethod
    def send(user, event, message, task=None, created_by=None):
        
        # Save in DB
        notification = Notification.objects.create(
            user=user,
            event=event,
            task=task,
            message=message,
            created_by=created_by,
            updated_by=created_by,
        )

        # Broadcast to WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"notifications_{user.id}",
            {
                "type": "send_notification",
                "event": event,
                "task_id": task.id if task else None,
                "title": task.title if task else None,
                "message": message,
                "from": created_by.email if created_by else None,
            }
        )

        return notification
