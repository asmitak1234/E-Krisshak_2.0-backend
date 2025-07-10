from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        print("🔌 WebSocket connection attempt")

        if self.scope["user"] == AnonymousUser():
            print("❌ Anonymous user detected, closing socket")
            await self.close()
        else:
            self.group_name = f"user_{self.scope['user'].id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
            print(f"✅ WebSocket accepted for user {self.scope['user'].id}")


    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content):
        # Optional: handle messages from client if needed
        pass

    async def send_notification(self, event):
        """Handles sending notification messages via WebSockets."""
        await self.send_json(event["data"])
