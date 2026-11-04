from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.layers import get_channel_layer


def user_group(user_id):
    return f"user-{user_id}"


def push(user_ids, event, **data):
    send = async_to_sync(get_channel_layer().group_send)
    for user_id in set(user_ids):
        send(user_group(user_id), {"type": "chat.event", "event": event, **data})


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if not user.is_authenticated:
            return await self.close()
        self.group = user_group(user.id)
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive_json(self, content):
        if isinstance(content.get("typing"), int):
            await self.channel_layer.group_send(user_group(content["typing"]), {"type": "chat.event", "event": "typing", "user": self.scope["user"].id})

    async def chat_event(self, event):
        await self.send_json({key: value for key, value in event.items() if key != "type"})
