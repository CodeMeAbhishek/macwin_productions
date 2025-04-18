from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import RegisterForm, ProfileForm, ProfileCompletionForm
from .models import Profile
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import FriendRequest, Message
from django.http import HttpResponse
from django.urls import reverse
from django.db.models import Q

@login_required
def index_view(request):
    query = request.GET.get('q')
    results = None
    if query:
        results = User.objects.filter(
            Q(username__icontains=query) | Q(profile__full_name__icontains=query)
        ).exclude(id=request.user.id)
    return render(request, 'chat/index.html', {'results': results})

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )
            return redirect('complete_profile', user_id=user.id)
    else:
        form = RegisterForm()
    return render(request, 'chat/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        uname = request.POST.get('username')
        pwd = request.POST.get('password')
        user = authenticate(request, username=uname, password=pwd)

        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            messages.error(request, "Invalid Credentials.")
    return render(request, 'chat/login.html')

@login_required
def profile_view(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated!")
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'chat/profile.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def send_friend_request(request, user_id):
    to_user = User.objects.get(id=user_id)
    if request.user != to_user:
        FriendRequest.objects.get_or_create(from_user=request.user, to_user=to_user)
    return redirect('index')

@login_required
def cancel_friend_request(request, user_id):
    to_user = User.objects.get(id=user_id)
    FriendRequest.objects.filter(from_user=request.user, to_user=to_user).delete()
    return redirect('index')

@login_required
def accept_friend_request(request, request_id):
    friend_request = FriendRequest.objects.get(id=request_id)
    if friend_request.to_user == request.user:
        friend_request.is_accepted = True
        friend_request.save()
    return redirect('index')

@login_required
def friends_list_view(request):
    sent = FriendRequest.objects.filter(from_user=request.user, is_accepted=True)
    received = FriendRequest.objects.filter(to_user=request.user, is_accepted=True)
    friends = [fr.to_user for fr in sent] + [fr.from_user for fr in received]

    friends_data = []
    for friend in friends:
        unread_count = Message.objects.filter(
            sender=friend,
            receiver=request.user,
            is_read=False
        ).count()

        last_message = Message.objects.filter(
            Q(sender=request.user, receiver=friend) |
            Q(sender=friend, receiver=request.user)
        ).order_by('-timestamp').first()

        friends_data.append({
            'user': friend,
            'unread': unread_count,
            'last_message': last_message
        })

    return render(request, 'chat/friends.html', {'friends': friends_data})


@login_required
def user_profile_view(request, user_id):
    other_user = User.objects.get(id=user_id)
    profile = other_user.profile
    
    # Handle the friend request acceptance
    if request.method == 'POST' and request.POST.get('action') == 'accept_request':
        # Find the pending friend request
        friend_request = FriendRequest.objects.filter(
            from_user=other_user,
            to_user=request.user,
            is_accepted=False
        ).first()
        
        if friend_request:
            friend_request.is_accepted = True
            friend_request.save()
            messages.success(request, f"You are now friends with {other_user.username}!")
        return redirect('user_profile', user_id=user_id)
    
    # Rest of your existing view code...
    friend_request_sent = FriendRequest.objects.filter(
        from_user=request.user, to_user=other_user, is_accepted=False
    ).exists()

    friend_request_received = FriendRequest.objects.filter(
        from_user=other_user, to_user=request.user, is_accepted=False
    ).exists()

    is_friend = FriendRequest.objects.filter(
        (
            Q(from_user=request.user, to_user=other_user) |
            Q(from_user=other_user, to_user=request.user)
        ),
        is_accepted=True
    ).exists()

    context = {
        'other_user': other_user,
        'profile': profile,
        'friend_request_sent': friend_request_sent,
        'friend_request_received': friend_request_received,
        'is_friend': is_friend,
    }

    return render(request, 'chat/user_profile.html', context)

@login_required
def chat_with_friend(request, friend_id):
    friend = User.objects.get(id=friend_id)

    # Ensure they're friends
    is_friend = FriendRequest.objects.filter(
        Q(from_user=request.user, to_user=friend) |
        Q(from_user=friend, to_user=request.user),
        is_accepted=True
    ).exists()

    if not is_friend:
        messages.error(request, "You are not friends with this user.")
        return redirect('friends')

    # Get chat history
    messages_qs = Message.objects.filter(
        Q(sender=request.user, receiver=friend) |
        Q(sender=friend, receiver=request.user)
    )

    # Create a unique room name based on user IDs
    room_name = f"{min(request.user.id, friend.id)}_{max(request.user.id, friend.id)}"

    # Mark unread messages as read
    Message.objects.filter(sender=friend, receiver=request.user, is_read=False).update(is_read=True)


    return render(request, 'chat/chat_room.html', {
        'friend': friend,
        'chat_messages': messages_qs,
        'room_name': room_name
    })

def complete_profile_view(request, user_id):
    user = User.objects.get(id=user_id)
    if request.method == 'POST':
        form = ProfileCompletionForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = user
            profile.save()
            messages.success(request, "Profile completed. Please login.")
            return redirect('login')
    else:
        form = ProfileCompletionForm()
    return render(request, 'chat/complete_profile.html', {'form': form})
