from django.urls import path
from . import views
urlpatterns = [



    path('auth/PhoneNumber', views.Auth_PhoneNumber),
    path('auth/register/PhoneNumber', views.Auth_Register_VerifyOTP),
    path('auth/login/PhoneNumber', views.Auth_LogIn_VerifyOTP),


    path('u/<str:pk>', views.ViewUserProfile),
    path('u/<str:pk>/Posts', views.ViewPosts),
    path('u/<str:pk>/communities/Posts', views.GetUserCommunityPosts),
    path('u/<str:pk>/self/Posts', views.GetUserSelfPosts),
    path('u/<str:pk>/Replies', views.GetUserReplies),

    path('u/<str:pk>/Chat', views.ChatsAll),
    path('u/<str:pk>/Chat/New', views.ChatNew),
    path('me/Chats', views.ChatPreview),

    path('g/<str:pk>', views.GetGroupPage),
    path('g/<str:pk>/Posts', views.ViewGroupPosts),
    path('g/<str:pk>/Mods', views.GetGroupMods),


    path('auth/Register', views.Register),


    path('u/<str:pk>/Posts/<str:pk2>', views.ViewPostDetails),
    path('u/<str:pk>/Posts/<str:pk2>/Replies/<str:pk3>/<str:pk4>', views.GetOnlyComment),
    path('u/<str:pk>/Posts/<str:pk2>/Replies/<str:pk3>/<str:pk4>/All', views.GetComment),


    path('u/<str:pk>/Posts/<str:pk2>/extra/LikedBy', views.PostLikedBy), ##
    path('u/<str:pk>/Posts/<str:pk2>/Replies/<str:pk3>/<str:pk4>/extra/LikedBy', views.ReplyLikedBy),##


    path('u/<str:pk>/Posts/<str:pk2>/extra/RePostedBy', views.RePostedBy),##    #PAGINATED#
    path('u/<str:pk>/Posts/<str:pk2>/Replies/<str:pk3>/<str:pk4>/extra/RePostedBy', views.ReplyRePostedBy),##


    path('u/<str:pk>/Posts/<str:pk2>/RePost', views.RePost),
    path('u/<str:pk>/Posts/<str:pk2>/Mention', views.Mention),
    path('u/<str:pk>/Posts/<str:pk2>/Replies/<str:pk3>/<str:pk4>/RePost', views.RePostComment),
    path('u/<str:pk>/Posts/<str:pk2>/Replies/<str:pk3>/<str:pk4>/Mention', views.MentionComment),

    path('u/<str:pk>/Posts/<str:pk2>/Replies', views.PostComments), ####################################################
    path('u/<str:pk>/Posts/<str:pk2>/Replies/<str:pk3>/<str:pk4>/Replies', views.GetCommentReplies),############################


    path('u/<str:pk>/Posts/<str:pk2>/Like', views.LikePost),##
    path('u/<str:pk>/Posts/<str:pk2>/Like', views.LikePost),##
    path('u/<str:pk>/Posts/<str:pk2>/DisLike', views.DisLikePost),##


    path('u/<str:pk>/Posts/<str:pk2>/Report', views.ReportPost),
    path('u/<str:pk>/Posts/<str:pk2>/UnReport', views.UndoPostReport), ##
    path('u/<str:pk>/Posts/<str:pk2>/Replies/<str:pk3>/<str:pk4>/Report', views.ReportComment),
    path('u/<str:pk>/Posts/<str:pk2>/UnReport', views.UndoCommentReport), ##




    path('u/<str:pk>/Posts/<str:pk2>/Vote', views.VoteOnPoll),


    path('u/<str:pk>/Following', views.GetFollowing),
    path('u/<str:pk>/Followers', views.UsersFollowers),
    path('u/<str:pk>/Followers/ByPeopleIKnow', views.UserFollowsByPeopleIKnow),


    path('create/Community', views.CreateCommunity),
    path('create/Collection', views.CreateCollection),


    path('g/<str:pk>/extra/Membership', views.ModifyGroupMembership),


    path('g/<str:pk>/Members/<str:pk2>', views.ModToolsProfileOverView),
    path('g/<str:pk>/Members/<str:pk2>/Posts', views.ModToolsProfileOverView_Posts),
    path('g/<str:pk>/Members/<str:pk2>/Accept', views.ModTools_Accept),
    path('g/<str:pk>/Members/<str:pk2>/Kick', views.ModTools_Kick),
    path('g/<str:pk>/Members/<str:pk2>/UnKick', views.ModTools_UnKick),
    path('g/<str:pk>/Members/<str:pk2>/MakeMod', views.ModTools_Makemod),
    path('g/<str:pk>/Members', views.ModTools_Members),

    path('tags/<str:pk>', views.GetTagPage),



    path('u/<str:pk>/Posts/<str:pk2>/Replies/<str:pk3>/<str:pk4>/Save', views.SaveComment),


    path('u/<str:pk>/SendFollowRequest', views.SendFollowRequest),
    path('u/<str:pk>/Similar', views.AlsoFollow),

    path('Feed', views.PostFeed),

    path('u', views.SearchUser),
    path('g', views.SearchGroup),

    path('me', views.Me),
    path('me/Followers', views.FollowersAll),
    path('me/Followers/Accepted', views.Followers),
    path('me/Followers/Pending', views.FollowersPending),
    path('me/Followers/Pending/<str:pk>', views.ManagePending),
    path('me/Followers/Remove/<str:pk>', views.RemoveFollower),
    path('me/Following/Remove/<str:pk>', views.RemoveFollowing),



    path('me/Following', views.FollowingsAll),
    path('me/Following/Accepted', views.Followings),
    path('me/Following/Notify', views.NotifyFor),
    path('me/Following/Pending', views.FollowingsPending),
    path('me/Following/Modify/<str:pk>', views.ModifyFollowing),
    path('me/Mentions', views.MyMentions),
    path('utils/UserExists/<str:pk>', views.UserExists),
    path('utils/GroupExists', views.CommunityExists),
    path('utils/CollectionExists', views.CollectionExists),
    path('me/Posts', views.CreatePost),

    path('Trending/<str:pk>', views.Trending),
    path('Trending', views.SearchTrending),
    path('TrendingPosts', views.TrendingPosts),
    path('Posts', views.SearchPosts),

    path('Popular', views.Popular),
    path('Trends', views.Trends),
    path('me/Suggested', views.SuggestFollowing),
    path('me/Suggested/Tags', views.SugegstTrends),
    path('me/Notifications', views.GetNotifications),
    path('u/<str:pk>/Notify', views.Notify),
    path('u/<str:pk>/Posts/<str:pk2>/Save', views.SavePost),
    path('me/Posts/<str:pk>', views.DeletePost),

    path('u/<str:pk>/Mentions', views.UserMentions),
    path('me/Saved', views.GetSavedPosts),
    path('me/Groups', views.MyGroups),
    path('me/Liked', views.LikedPosts),
    path('me/DisLiked', views.DisLikedPosts),
    path('me/Suggested/Groups', views.GrowingCommunities),
    path('auth/SignIn', views.LogIn),
    path('me/auth/change-email', views.ChangeEmail),
    path('me/auth/change-handle', views.ChangeUserHandle),
    path('me/auth/log-out-all', views.LogOutOfAll),
    path('me/auth/DELETE', views.DeleteAccount),

    path('c/<str:pk>/Posts', views.GetCollectionPosts),
    path('c/<str:pk>', views.GetCollection),
    path('c/<str:pk>/Members', views.GetCollectionMembers),
    path('c/<str:pk>/Members/add/<str:pk2>', views.AddCollectionMember),
    path('c/<str:pk>/Members/remove/<str:pk2>', views.RemoveCollectionMember),
    path('c/<str:pk>/Join', views.AddRemoveCollection),

    path('me/Collections', views.MyCollections),
    path('c', views.SearchCollections),


    path('extra/addtocollection/<str:pk>', views.AddToCollection),

    path('u/<str:pk>/Block', views.BlockUser),
    path('u/<str:pk>/UnBlock', views.UnBlockUser),

    path('me/Following', views.FollowingsAll),
    path('me/BlockedUsers', views.BlockedUsers),

    path('overwatch/pending', views.PendingPosts),
    path('overwatch/action/<str:pk>', views.OverWatchVote),
    path('me/Reported', views.MyReportedPosts),

    path('me/RegisterFBToken', views.AddNotificationToken),
    path('me/NotificationStatus', views.CheckNotificationStatus),

    path('auth/PasswordResetKey', views.ResetPasswordNoToken),
    path('auth/PasswordReset', views.ResetPasswordNoAuth),

    path('updates', views.GetPostUpdates),



    path('auth/reset-password/send-mobile-otp', views.ResetPasswordUsingMobileOTP_Send),
    path('auth/reset-password/verify-mobile-otp', views.ResetPasswordUsingMobileOTP_Verify),

    path('auth/reset-password/send-email-otp', views.ResetPasswordUsingMobileOTP_Send),
    path('auth/reset-password/send-email-otp', views.ResetPasswordUsingMobileOTP_Send),

    path('auth/update-handle', views.UpdateUserName),

    path('auth/update-mobile-number/send-mobile-otp', views.AddPhonbeNumber_SendOTp),
    path('auth/update-mobile-number/verify-mobile-otp', views.AddPhonbeNumber_VerifyOTP),


    

]
