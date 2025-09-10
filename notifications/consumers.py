import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"notifications_{self.room_name}"

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        data = json.loads(text_data)
        event_type = data.get("type")
        

        if event_type == "task_assigned":
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    "type": "send_notification",
                    "event": "task_assigned",
                    "task_id": data.get("task_id"),
                    "assigned_to": data.get("assigned_to"),
                    "message": f"Task {data.get('task_id')} assigned to {data.get('assigned_to')}",
                },
            )
        elif event_type == "status_changed":
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    "type": "send_notification",
                    "event": "status_changed",
                    "task_id": data.get("task_id"),
                    "new_status": data.get("new_status"),
                    "message": f"Task {data.get('task_id')} status changed to {data.get('new_status')}",
                },
            )
        else:
            # Fallback for unknown events
            self.send(text_data=json.dumps({
                "event": "error",
                "message": f"Unknown event type: {event_type}"
            }))
    
    def send_notification(self, event):
        """
        Called when a group message is received.
        """
        self.send(text_data=json.dumps(event))
