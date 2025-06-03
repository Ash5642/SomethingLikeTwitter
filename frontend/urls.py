from django.urls import path
from . import views
urlpatterns = [
    path('u/<str:pk>', views.UserPage),
    path('trending/<str:pk>', views.UserPage),
    path('chat/<str:pk>', views.UserPage),
    path('u/<str:pk>/Posts/<str:pk2>', views.PostPage),
    path('u/<str:pk>/Posts/<str:pk2>/Report', views.ReportPostPage),


    path('u/<str:pk>/Posts/<str:pk2>/LikedBy', views.LikedBy),
    path('u/<str:pk>/Posts/<str:pk2>/RepostedBy', views.RePostedBy),

    path('u/<str:pk>/Posts/<str:pk2>/Replies/<str:pk3>/<str:pk4>/LikedBy', views.ReplyLikedBy),
    path('u/<str:pk>/Posts/<str:pk2>/Replies/<str:pk3>/<str:pk4>/RePostedBy', views.ReplyLikedBy),

    path('Settings', views.Settings),
    path('Settings/MyProfile', views.Settings),
    path('Settings/MyAccount', views.Settings),
    path('Settings/MyActivities', views.Settings),
    path('Settings/ManageContentISee', views.Settings),
    path('Settings/Notifications', views.Settings),

    path('About', views.Settings),

    path('me/Liked', views.Settings),
    path('me/Saved', views.Settings),
    path('me/Collections', views.Settings),
    path('me/Following', views.Settings),
    path('me/Communities', views.Settings),

    path('g/<str:pk>', views.GroupPage),

    path('g/<str:pk>/Create', views.CreateGroupPost),
    path('g/<str:pk>/Posts/<str:pk2>', views.GroupPostPage),
    path('Register', views.SignUp),
    path('CreateProfile', views.CreateProfile),
    path('Comments', views.MyCommentReplies),
    path('Replies', views.MyReples),
    path('Trending/<str:pk>', views.Trending),
    path('Following', views.Following),
    path('Followers', views.Followers),
    path('u/<str:pk>/Chat', views.Chat),
    path('Chats', views.Chats),
    path('Me', views.Me),
    path('u/<str:pk>/Posts/<str:pk2>/Replies/<str:pk3>/<str:pk4>', views.PostComments),
    path('me/Notifications', views.Notifications),
    path('u/<str:pk>/Followers', views.UserFollowers),
    path('', views.Main),
    path('auth/reset-password', views.ResetPassword),
    path('login', views.SignIn),
    path('auth/reset-email', views.ResetEmail),
    path('auth/reset-handle', views.ResetHandle),
    path('extra/agreement', views.UserAgreement),
    path('auth/forgot-password', views.PasswordReset),
    path('me/delete', views.DeleteAccount),
    path('TrendingPosts', views.Settings),
    path('CreatePost', views.Settings),
]