import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from notifications.models import Notification
from django.contrib.auth import get_user_model
User = get_user_model()
from notifications.enums import NotificationType

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

            if not receiver_id or int(receiver_id) == self.scope["user"].id:  # 🚫 block self-message
                self.send(text_data=json.dumps({
                    "event": "error",
                    "message": "You cannot send a message to yourself."
                }))
                return

            # Save general chat to DB
            Notification.objects.create(
                user=User.objects.get(id=receiver_id),
                sender=self.scope["user"],
                event=NotificationType.GENERAL,
                task_id=data.get("task_id"),  # optional
                message=message,
            )

            # Broadcast
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
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
            print(f"Error sending notification: {e}")
