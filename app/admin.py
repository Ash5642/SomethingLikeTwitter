from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(UserProfile)
admin.site.register(Posts)
admin.site.register(Groups)
admin.site.register(GroupMembers)
admin.site.register(Following)
admin.site.register(Mentions)
admin.site.register(PostLikes)
admin.site.register(Tags)
admin.site.register(Chat)
admin.site.register(Chats)
admin.site.register(PostReports)
admin.site.register(Votes)
admin.site.register(Images)

admin.site.register(Poll)
admin.site.register(Videos)
admin.site.register(Tag)
admin.site.register(Notifications)
admin.site.register(NotifyPosts)
admin.site.register(Saved)
admin.site.register(Collections)
admin.site.register(CollectionPosts)
admin.site.register(Change_Password_Token)
admin.site.register(FollowCollection)
admin.site.register(PostBodyText)
admin.site.register(OverWatchers)
admin.site.register(OverWatchVotes)
admin.site.register(Offense)
admin.site.register(FireBaseNotificationTokens)
admin.site.register(PostLink)
admin.site.register(UserViolations)

admin.site.register(UserPhoneNumber)
admin.site.register(UserOTPToken)

admin.site.register(LastHandleChange)