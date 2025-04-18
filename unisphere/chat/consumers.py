import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Message
from django.core.exceptions import ObjectDoesNotExist

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.room_name = self.scope['url_route']['kwargs']['room_name']
            self.room_group_name = f"chat_{self.room_name}"
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
        except Exception as e:
            await self.close(code=4000)  # Close with error code

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        except Exception:
            pass  # Ignore errors during disconnect

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'chat_message')
            
            if message_type == 'read_receipt':
                await self.handle_read_receipt(data)
            else:
                await self.handle_chat_message(data)
        except json.JSONDecodeError:
            await self.send_error("Invalid message format")
        except Exception as e:
            await self.send_error("An error occurred processing your message")

    async def handle_read_receipt(self, data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'read_receipt',
                'sender': data['sender'],
                'receiver': data['receiver']
            }
        )
        if 'receiver' in data and 'sender' in data:
            await self.mark_messages_as_read(data['sender'], data['receiver'])

    async def handle_chat_message(self, data):
        try:
            sender = await self.get_user(data['sender'])
            receiver = await self.get_user(data['receiver'])
            message = data['message']
            
            await self.save_message(sender, receiver, message)
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender': data['sender'],
                    'receiver': data['receiver']
                }
            )
        except ObjectDoesNotExist:
            await self.send_error("User not found")
        except Exception as e:
            await self.send_error("Failed to send message")

    async def send_error(self, message):
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender': event['sender'],
            'receiver': event['receiver']
        }))

    async def read_receipt(self, event):
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'sender': event['sender'],
            'receiver': event['receiver']
        }))

    @database_sync_to_async
    def get_user(self, user_id):
        return User.objects.get(id=user_id)

    @database_sync_to_async
    def save_message(self, sender, receiver, message):
        return Message.objects.create(sender=sender, receiver=receiver, content=message)

    @database_sync_to_async
    def mark_messages_as_read(self, sender_id, receiver_id):
        return Message.objects.filter(
            sender_id=sender_id,
            receiver_id=receiver_id,
            is_read=False
        ).update(is_read=True) 