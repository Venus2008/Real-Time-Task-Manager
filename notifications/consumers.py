import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from notifications.models import Notification
from django.contrib.auth import get_user_model
User = get_user_model()
from notifications.enums import NotificationType
from django.core.cache import cache

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        # Use the room_name from the URL to create a group
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"notifications_{self.room_name}"

        # Join the group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()
        self.send(text_data=json.dumps({
            "event": "connected",
            "message": f"Welcome to the {self.room_name} chat!"
        }))

    def disconnect(self, close_code):
        # Leave the group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        data = json.loads(text_data)
        notification_type = data.get("event")

        if notification_type == NotificationType.GENERAL:
            receiver_id = data.get("receiver_id")
            message = data.get("message")

            # Prevent sending message to self
            if not receiver_id or int(receiver_id) == self.scope["user"].id:  # 🚫 block self-message
                self.send(text_data=json.dumps({
                    "event": "error",
                    "message": "You cannot send a message to yourself."
                }))
                return
            
            receiver = User.objects.get(id=receiver_id)

            # Save general chat to DB
            receiver = User.objects.get(id=receiver_id)
            Notification.objects.create(
                user=receiver,
                sender=self.scope["user"],
                event=NotificationType.GENERAL,
                task_id=data.get("task_id"),  # optional
                message=message,
            )

            # Invalidate related caches
            cache.delete(f"notifications_{receiver.email}")  # receiver's notifications
            if data.get("task_id"):
                cache.delete(f"chat_history_{data['task_id']}_{receiver.id}")  # chat history

            # Broadcast to group
            async_to_sync(self.channel_layer.group_send)(
                f"notifications_{receiver.id}",
                {
                    "type": "send_notification",
                    "event": "general",
                    "sender": self.scope["user"].email,
                    "receiver_id": receiver_id,
                    "task_id": data.get("task_id"),
                    "message": message,
                },
            )
    def send_notification(self, event):
        """
        This method is called when the server sends a notification to the group.
        The 'event' is a dict containing keys like:
        - type (always "send_notification")
        - event (e.g., "task_assigned")
        - task_id, title, message, etc.
        """
        try:
            self.send(text_data=json.dumps(event))
        except Exception as e:
            self.send(text_data=json.dumps({
            "event": "error",
            "message": f"Failed to send notification: {str(e)}"
            }))
