from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('send-request/<int:user_id>/', views.send_friend_request, name='send_request'),
path('cancel-request/<int:user_id>/', views.cancel_friend_request, name='cancel_request'),
path('accept-request/<int:request_id>/', views.accept_friend_request, name='accept_request'),
path('friends/', views.friends_list_view, name='friends'),
path('user/<int:user_id>/', views.user_profile_view, name='user_profile'),
path('send-request/<int:user_id>/', views.send_friend_request, name='send_request'),
path('accept-request/<int:request_id>/', views.accept_friend_request, name='accept_request'),
path('chat/<int:friend_id>/', views.chat_with_friend, name='chat_with_friend'),
path('complete-profile/<int:user_id>/', views.complete_profile_view, name='complete_profile'),

]