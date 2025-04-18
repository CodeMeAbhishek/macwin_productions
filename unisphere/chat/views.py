from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import RegisterForm, ProfileForm, ProfileCompletionForm, PostForm, CommentForm
from .models import Profile, Post, Like, Comment, Notification
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import FriendRequest, Message
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.db.models import Q
from django.views.generic import TemplateView
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta
from django.template.loader import render_to_string
from .utils import get_user_friends, get_friends_with_unread_messages

@login_required
def index_view(request):
    if request.method == 'POST':
        return handle_post_request(request)
    
    form = PostForm()
    comment_form = CommentForm()
    query = request.GET.get('q')
    results = handle_search(query, request.user) if query else None
    
    posts = Post.objects.select_related('user', 'user__profile').prefetch_related('likes', 'comments__user').order_by('-timestamp')
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False)

    return render(request, 'chat/index.html', {
        'form': form,
        'comment_form': comment_form,
        'posts': posts,
        'results': results,
        'unread_notifications': unread_notifications
    })

def handle_post_request(request):
    if 'comment_content' in request.POST:
        return handle_comment(request)
    else:
        return handle_post_creation(request)

def handle_comment(request):
    post_id = request.POST.get('post_id')
    post = Post.objects.get(id=post_id)
    comment = Comment.objects.create(
        user=request.user,
        post=post,
        content=request.POST.get('comment_content')
    )
    if post.user != request.user:
        Notification.objects.create(
            user=post.user,
            sender=request.user,
            notif_type='comment',
            message=f"{request.user.username} commented on your post.",
            post=post
        )
    return redirect('index')

def handle_post_creation(request):
    form = PostForm(request.POST, request.FILES)
    if form.is_valid():
        post = form.save(commit=False)
        post.user = request.user
        post.save()
    return redirect('index')

def handle_search(query, current_user):
    return User.objects.filter(
        Q(username__icontains=query) | Q(profile__full_name__icontains=query)
    ).exclude(id=current_user.id)

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
            # Check if user has a profile
            try:
                user.profile
                return redirect('index')
            except Profile.DoesNotExist:
                return redirect('complete_profile', user_id=user.id)
        else:
            messages.error(request, "Invalid Credentials.")
    return render(request, 'chat/login.html')

@login_required
def profile_view(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        return redirect('complete_profile', user_id=request.user.id)
        
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated!")
    else:
        form = ProfileForm(instance=profile)
    
    # Get user's friends
    friends = get_user_friends(request.user)
    
    return render(request, 'chat/profile.html', {
        'form': form,
        'friends': friends
    })

def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def send_friend_request(request, user_id):
    """Send a friend request to another user."""
    try:
        to_user = User.objects.get(id=user_id)
        if request.user != to_user:
            friend_request, created = FriendRequest.objects.get_or_create(
                from_user=request.user, 
                to_user=to_user
            )
            if created:
                # Create notification for friend request
                Notification.objects.create(
                    user=to_user,
                    sender=request.user,
                    notif_type='friend_request',
                    message=f"{request.user.username} sent you a friend request."
                )
                return JsonResponse({'status': 'success', 'message': 'Friend request sent'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error': 'Friend request already sent'}, 
                    status=400
                )
        else:
            return JsonResponse(
                {'status': 'error', 'error': 'You cannot send a friend request to yourself'}, 
                status=400
            )
    except User.DoesNotExist:
        return JsonResponse(
            {'status': 'error', 'error': 'User not found'}, 
            status=404
        )
    except Exception as e:
        return JsonResponse(
            {'status': 'error', 'error': str(e)}, 
            status=500
        )

@login_required
def cancel_friend_request(request, user_id):
    try:
        to_user = User.objects.get(id=user_id)
        FriendRequest.objects.filter(from_user=request.user, to_user=to_user).delete()
        return JsonResponse({'status': 'success', 'message': 'Friend request cancelled'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=400)

@login_required
def accept_friend_request(request, request_id):
    try:
        friend_request = FriendRequest.objects.get(id=request_id)
        if friend_request.to_user == request.user:
            friend_request.is_accepted = True
            friend_request.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Friend request accepted',
                'friend_name': friend_request.from_user.profile.full_name
            })
        return JsonResponse({'status': 'error', 'error': 'Invalid request'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=400)

@login_required
def friends_list_view(request):
    friends_data = get_friends_with_unread_messages(request.user)
    return render(request, 'chat/friends.html', {'friends': friends_data})


@login_required
def find_friends_view(request):
    query = request.GET.get('q')
    results = None
    if query:
        # Search for users excluding current user and their friends
        current_user_friends = get_user_friends(request.user)
        results = User.objects.filter(
            Q(username__icontains=query) | 
            Q(profile__full_name__icontains=query)
        ).exclude(
            id__in=[request.user.id] + [friend.id for friend in current_user_friends]
        )
        
        # Add friend request status for each user
        for user in results:
            # Check if friend request is sent
            user.friend_request_sent = FriendRequest.objects.filter(
                from_user=request.user,
                to_user=user,
                is_accepted=False
            ).exists()
            # Check if friend request is received
            user.friend_request_received = FriendRequest.objects.filter(
                from_user=user,
                to_user=request.user,
                is_accepted=False
            ).exists()
            # Check if they are friends
            user.is_friend = FriendRequest.objects.filter(
                (Q(from_user=request.user, to_user=user) |
                Q(from_user=user, to_user=request.user)),
                is_accepted=True
            ).exists()

    return render(request, 'chat/find_friends.html', {
        'results': results,
        'query': query
    })

def get_user_friends(user):
    # Get all accepted friend requests where user is either sender or receiver
    sent_requests = FriendRequest.objects.filter(from_user=user, is_accepted=True)
    received_requests = FriendRequest.objects.filter(to_user=user, is_accepted=True)
    
    # Combine friends from both sent and received requests
    friends = [req.to_user for req in sent_requests] + [req.from_user for req in received_requests]
    return friends

@login_required
def user_profile_view(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    profile = other_user.profile
    
    # Get user's friends
    user_friends = get_user_friends(other_user)
    
    # Handle the friend request acceptance
    if request.method == 'POST' and request.POST.get('action') == 'accept_request':
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
        'friends': user_friends,
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
    user = get_object_or_404(User, id=user_id)
    
    # If user already has a profile, redirect to index
    try:
        user.profile
        return redirect('index')
    except Profile.DoesNotExist:
        pass
        
    if request.method == 'POST':
        form = ProfileCompletionForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = user
            profile.save()
            
            # Log the user in if they're not already logged in
            if not request.user.is_authenticated:
                login(request, user)
            
            messages.success(request, "Profile completed successfully!")
            return redirect('index')
    else:
        form = ProfileCompletionForm()
    return render(request, 'chat/complete_profile.html', {'form': form})

@login_required
def like_post(request, post_id):
    post = Post.objects.get(id=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
        # Create notification for like
        if post.user != request.user:
            Notification.objects.create(
                user=post.user,
                sender=request.user,
                notif_type='like',
                message=f"{request.user.username} liked your post."
            )
    
    return JsonResponse({
        'liked': liked,
        'likes_count': post.likes.count()
    })

@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)

    if request.method == 'POST':
        new_content = request.POST.get('content')
        post.content = new_content
        post.save()
        return redirect('index')

    return render(request, 'chat/edit_post.html', {'post': post})

@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)
    post.delete()
    return redirect('index')

@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, user=request.user)
    comment.delete()
    return redirect('index')

@login_required
def notifications_view(request):
    notifs = Notification.objects.filter(user=request.user).order_by('-timestamp')
    unread_count = notifs.filter(is_read=False).count()

    # If it's an AJAX call, mark all as read
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        notifs.update(is_read=True)
        html = render_to_string('chat/partials/notification_list.html', {'notifications': notifs})
        return JsonResponse({'html': html, 'unread_count': 0})

    return render(request, 'chat/notifications.html', {'notifications': notifs})

# Static pages
class AboutView(TemplateView):
    template_name = 'chat/about.html'

class FAQView(TemplateView):
    template_name = 'chat/faq.html'

class TermsView(TemplateView):
    template_name = 'chat/terms.html'

class PrivacyView(TemplateView):
    template_name = 'chat/privacy.html'

@csrf_exempt
def contact_view(request):
    success = False
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        # Optional: send email (or store in DB/log)
        print(f"Message from {name} ({email}): {message}")
        success = True
    return render(request, 'chat/contact.html', {'success': success})

@staff_member_required
def admin_dashboard(request):
    users = User.objects.all()
    posts = Post.objects.select_related('user').order_by('-timestamp')
    
    # Basic counts
    total_users = users.count()
    total_posts = posts.count()
    total_comments = Comment.objects.count()
    active_users = users.filter(is_active=True).count()
    blocked_users = total_users - active_users

    # Posts this week (last 7 days)
    today = timezone.now()
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    posts_per_day = []
    for day in last_7_days:
        count = Post.objects.filter(
            timestamp__date=day.date()
        ).count()
        posts_per_day.append({'date': day.strftime("%b %d"), 'count': count})

    context = {
        'users': users,
        'posts': posts,
        'total_users': total_users,
        'total_posts': total_posts,
        'total_comments': total_comments,
        'active_users': active_users,
        'blocked_users': blocked_users,
        'posts_per_day': posts_per_day,
    }
    return render(request, 'chat/admin_dashboard.html', context)

@require_POST
@staff_member_required
def toggle_block_user(request, user_id):
    user = User.objects.get(id=user_id)
    user.is_active = not user.is_active
    user.save()
    return redirect('admin_dashboard')

@require_POST
@staff_member_required
def delete_post_admin(request, post_id):
    post = Post.objects.get(id=post_id)
    post.delete()
    return redirect('admin_dashboard')

@login_required
@require_POST
def delete_notification(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id, user=request.user)
    notif.delete()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    return redirect('notifications')

@login_required
def messages_view(request):
    """View all messages across all conversations."""
    friends_data = get_friends_with_unread_messages(request.user)
    return render(request, 'chat/messages.html', {
        'friends_data': friends_data
    })

@login_required
def account_view(request):
    """View and manage account settings."""
    if request.method == 'POST':
        # Handle password change
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if new_password == confirm_password:
            user = authenticate(username=request.user.username, password=current_password)
            if user is not None:
                user.set_password(new_password)
                user.save()
                messages.success(request, "Password updated successfully!")
                login(request, user)  # Re-login the user
            else:
                messages.error(request, "Current password is incorrect.")
        else:
            messages.error(request, "New passwords don't match.")
    
    return render(request, 'chat/account.html')

@login_required
def privacy_view(request):
    """View and manage privacy settings."""
    profile = request.user.profile
    
    if request.method == 'POST':
        # Update privacy settings
        profile.relationship_status = request.POST.get('relationship_status', '')
        profile.save()
        messages.success(request, "Privacy settings updated!")
    
    return render(request, 'chat/privacy.html', {
        'profile': profile
    })

@login_required
def remove_friend(request, user_id):
    try:
        friend = get_object_or_404(User, id=user_id)
        FriendRequest.objects.filter(
            (Q(from_user=request.user, to_user=friend) |
             Q(from_user=friend, to_user=request.user)),
            is_accepted=True
        ).delete()
        return JsonResponse({
            'status': 'success',
            'message': f'Removed {friend.profile.full_name} from your friends'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=400)
