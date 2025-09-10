import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

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
            print(">>> Sending event:", event)
        except Exception as e:
            print(f"Error sending notification: {e}")
