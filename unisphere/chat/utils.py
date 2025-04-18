from django.db.models import Q
from .models import FriendRequest, Message

def get_user_friends(user):
    """Get all friends of a user."""
    sent_requests = FriendRequest.objects.filter(from_user=user, is_accepted=True)
    received_requests = FriendRequest.objects.filter(to_user=user, is_accepted=True)
    friends = [req.to_user for req in sent_requests] + [req.from_user for req in received_requests]
    return friends

def get_friends_with_unread_messages(user):
    """Get friends with their unread message counts and last messages."""
    friends = get_user_friends(user)
    friends_data = []
    
    for friend in friends:
        unread_count = Message.objects.filter(
            sender=friend,
            receiver=user,
            is_read=False
        ).count()

        last_message = Message.objects.filter(
            Q(sender=user, receiver=friend) |
            Q(sender=friend, receiver=user)
        ).order_by('-timestamp').first()

        friends_data.append({
            'user': friend,
            'unread': unread_count,
            'last_message': last_message
        })
    
    return friends_data 