from .models import *
from django.core import exceptions
from django.db.models import Q
import random
from datetime import datetime, timezone
from django.db.models.signals import pre_delete
import re
from .task import *
from django.db.models import Count
from pyfcm import FCMNotification
import cld3
from .utilities import *

def CreateUserProfileOnUserCreation(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(
            user=instance,
            Name = instance.username
        )
       ###print('Account created')
post_save.connect(CreateUserProfileOnUserCreation, sender = User)

def CreateAuthToken(sender, instance, created, **kwargs):
    if created:
        Token.objects.create(
            user = instance
        )
post_save.connect(CreateAuthToken, sender = User)



def CreateFirstModOnGroupCreation(sender, instance, created, **kwargs):
    if created:
        GroupMembers.objects.create(
            Group = instance,
            User = instance.FoundedBy,
            Status = MOD
        )


def ChangePostVote(sender, instance, created, **kwards):
    if created:
        if instance.Status == True:
            instance.Post.Vote = instance.Post.Vote+1
            instance.Post.save()
           ##print(instance.Post.Vote)
        else:
            instance.Post.Vote = instance.Post.Vote - 1
            instance.Post.save()
           ##print(instance.Post.Vote)



def ChangeFollowers(sender, instance, created, **kwargs):
    if created:
        instance.GettingFollowed.Followers = Following.objects.filter(GettingFollowed = instance.GettingFollowed).count()
        instance.GettingFollowed.save()
post_save.connect(ChangeFollowers, sender=Following)

def AddFollowing(sender, instance, created, **kwargs):
    if created:
        instance.Follower.FollowingCount = Following.objects.filter(Follower = instance.GettingFollowed).count()
        instance.Follower.save()
post_save.connect(AddFollowing, sender = Following)

def IncreaseGroupmemberCount(sender, instance, created, **kwargs):
    if created:
        instance.Group.MemberCount = GroupMembers.objects.filter(Group = instance.Group).count()
       ##print("Group member added")
        instance.Group.save()
post_save.connect(IncreaseGroupmemberCount, sender=GroupMembers)

def PostMentions(sender, instance, created, **kwargs):
    if created:
        if '@' in str(instance.Title):
            AllMentionedUsers = []
            Title = str(instance.Title)
            run = 0
            AllUsers = re.findall(r"@(\w+)", Title)
            for UserName in AllUsers:
               ##print(UserName)
                try:
                    Users = User.objects.select_related('userprofile').get(username__iexact=UserName)
                    AllMentionedUsers.append(Users)
                    Mentions.objects.create(User = Users.userprofile, Post = instance)
                except exceptions.ObjectDoesNotExist:
                    pass
            To = Mentions.objects.filter(Post=instance).values_list('User')
            Tokens = list(FireBaseNotificationTokens.objects.filter(User__in=To).values_list('Token', flat=True))
            SendMentionNotification.delay(Tokens, instance.id)
        else:
            pass

post_save.connect(PostMentions, sender=Posts)

def DetectPostLanguage(sender, instance, created, **kwargs):
    if created:
        Post = Posts.objects.get(id=instance.id)
        try:
            Title = Post.Title
            pred = cld3.get_language(Title)
            #print(pred)
            PredictedLanguage = pred.language.split('-')[0]
            Post.Language = LanguageCodes(PredictedLanguage)
            Post.save()
        except Exception as exception:
            pass
        if instance.ParentPost:
            pass
        else:
            #print('AAAA')
            Lang = Posts.objects.filter(PostedBy = Post.PostedBy).annotate(type = Count('Language')).order_by('-type')[0].Language
            #print('BNBBB')
            Post.PostedBy.Language = Lang
            #print(Lang)
            Post.PostedBy.save()
            #print('AAAAAAAAAAAA')
            

post_save.connect(DetectPostLanguage, sender=Posts)



def AddTags(sender, instance, created, **kwargs):
    if created:
        if '#' in str(instance.Title):
            Title = str(instance.Title)
            run = 0
            AllTags = re.findall(r"#(\w+)", Title)
            for Hashtag in AllTags:
               ##print(Hashtag)
                try:
                    Tagg = Tags.objects.get(Tag = Hashtag)
                except exceptions.ObjectDoesNotExist:
                    Tags.objects.create(
                        Tag = Hashtag
                    )
                    Tagg = Tags.objects.get(Tag = Hashtag)
                Tag.objects.create(
                    Post = instance,
                    Tag = Tagg
                )
        else:
           return
post_save.connect(AddTags, sender=Posts)


def ChatGroup(sender, instance, created, **kwargs):
    if created:
        From = instance.From
        To = instance.To
        try:
            Parent = Chats.objects.get(Q(User1 = From, User2 = To)|Q(User1 = To, User2 = From))
            instance.Chats = Parent
            Parent.LastUpdated = instance.Time
            Parent.save()
            instance.save()
        except exceptions.ObjectDoesNotExist:
            Chats.objects.create(
                User1 = From,
                User2 = To
            )
            Parent = Chats.objects.get(Q(User1=From, User2=To) | Q(User1=To, User2=From))
            instance.Chats = Parent
            Parent.LastUpdated = instance.Time
            Parent.save()
            instance.save()

post_save.connect(ChatGroup, sender=Chat)

def PollVote(sender, instance, created, **kwargs):
    if created:
        PollOption = instance.Poll
        PollOption.Count = Votes.objects.filter(Poll = PollOption.id).count()
        PollOption.save()
post_save.connect(PollVote, sender = Votes)

def AddRepostCount(sender, instance, created, **kwargs):
    if created:
        if instance.RePost:
            UpdateUserScore_Repost.delay(instance.id)
            instance.RePost.RePostCount = Posts.objects.filter(RePost = instance.RePost).count()
            instance.RePost.save()

post_save.connect(AddRepostCount, sender = Posts)


def MentionNotification(sender, instance, created, **kwargs):
    if created:
        if '@' in str(instance.Title):
            Now = datetime.now(timezone.utc)
            Title = str(instance.Title)
            run = 0
            for TagInstance in range(0, Title.count('@')):
                user = Title.split('@')[1].split(' ')[0]
                Title = Title.split(user)[1]
               ##print(user)
               ##print(TagInstance)
                try:
                    MentionedUser = User.objects.get(username = user)
                    Notifications.objects.create(
                        User=MentionedUser.userprofile,
                        Post=instance,
                        Type='Mention',
                        Created=Now
                    )
                except exceptions.ObjectDoesNotExist:
                    return

post_save.connect(MentionNotification, sender = Posts)


def PostNotifications(sender, instance, created, **kwargs):
    if created:
        ManagePostNotifications.delay(instance.id)
post_save.connect(PostNotifications, sender = Posts)


def RemoveVote(sender, instance,  **kwargs):
    Post = instance.Post
    if instance.Status == True:
        Post.Vote = Post.Vote - 1
        Post.save()
       ##print(str(Post.Vote)+' ( like deleted)')
    elif instance.Status == False:
        Post.Vote = Post.Vote + 1
        Post.save()
       ##print(str(Post.Vote) + ' (dislike deleted)')

def OverWatchOutcomeSignal(sender, instance, created, **kwargs):
    if created:
        Innocent = OverWatchVotes.objects.filter(Post = instance.Post, Outcome = INNOCENT).count()
        Hide = OverWatchVotes.objects.filter(Post=instance.Post, Outcome = HIDE).count()
        Delete = OverWatchVotes.objects.filter(Post=instance.Post, Outcome=REMOVE).count()
        if Innocent + Hide + Delete > 10:
            if Innocent>=4:
                Offense.objects.create(Outcome = 0, Post = instance.Post)
            else:
                if Delete >=6:
                    Offense.objects.create(Outcome=2, Post=instance.Post)
                else:
                    Offense.objects.create(Outcome=1, Post=instance.Post)
post_save.connect(OverWatchOutcomeSignal, sender = OverWatchVotes)


def AddUserViolation(sender, instance, created, **kwargs):
    if created:
        ViolationType = PostReports.objects.filter(Post = instance.Post).annotate(type = Count('Type')).order_by('-type')[0].Type
       ##print(instance.Post.Title)
       ##print(ViolationType)
        UserViolations.objects.create(User=instance.Post.PostedBy, Post=instance.Post, OffenseType=ViolationType)
post_save.connect(AddUserViolation, sender = Offense)


def PostAction(sender, instance, created, **kwargs):
    if created:
        if instance.Outcome == 1:
            instance.Post.Public = True
            instance.Post.Sensitive = True
            instance.Post.save()
        elif instance.Outcome == 2:
            instance.Post.Title = '[THIS POST HAS BEEN DELETED BY OVERWATCH]'
            Images.objects.filter(Post = instance.Post).delete()
            Poll.objects.filter(Post=instance.Post).delete()
            Videos.objects.filter(Post=instance.Post).delete()
            PostBodyText.objects.filter(Post=instance.Post).delete()
           ##print("{AAAAAAAAAAA")
            instance.Post.save()
post_save.connect(PostAction, sender = Offense)

def SendChatNotification(sender, instance, created, **kwargs):
    if created:
        try:
            To = instance.To
            Tokens = list(FireBaseNotificationTokens.objects.filter(User = To).values_list('Token', flat=True))
            if Tokens[0]:
                task.SendChatNotification.delay(Tokens, instance.From.id, instance.Text)
        except Exception as exception:
            pass
post_save.connect(SendChatNotification, sender = Chat)

def Link(sender, instance, created, **kwargs):
    if created:
        GetLinkDetails.delay(instance.Link, instance.Post.id)
post_save.connect(Link, sender = PostLink)

def PostThumbnail(sender, instance, created, **kwargs):
    if created:
       ##print('AAGFAYTFAYACYTAIYTS')
        GeneratePostThumbNail.delay(instance.id)
post_save.connect(PostThumbnail, sender = Images)


def MentionNotifiation(sender, instance, created, **kwargs):
    if created:
        To = Mentions.objects.filter(Post= instance).values_list('User')
        Tokens = list(FireBaseNotificationTokens.objects.filter(User=To).values_list('Token', flat=True))
        SendMentionNotification.delay(Tokens, instance.id)
def UpdateReplyCount(sender, instance,created, **kqargs):
    if created:
        if instance.ParentPost:
            if instance.ReplyingTo == None:
                instance.ParentPost.CommentCount = instance.ParentPost.CommentCount+1
                instance.ParentPost.save()
            else:
                 instance.ReplyingTo.CommentCount = instance.ReplyingTo.CommentCount + 1
                 instance.ReplyingTo.save()
        else:
            return
    else:
        return
post_save.connect(UpdateReplyCount, sender = Posts)

def UpdateGroupPostCount(sender, instance, created, **kwargs):
    if created:
        if instance.ParentPost == None and instance.Group:
            instance.Group.PostCount = instance.Group.PostCount
            instance.Group.save()
post_save.connect(UpdateGroupPostCount, sender = Posts)

def UpdateTagPostCount(sender, instance, created, **kwargs):
    if created:
        instance.Tag.Posts = instance.Tag.Posts+1
        instance.Tag.save()
post_save.connect(UpdateTagPostCount, sender = Tag)


def UpdatePoints_Vote(sender, instance, created, **kwargs):
    if created:
        UpdateUserScore_Like.delay(instance.id)

post_save.connect(UpdatePoints_Vote, sender = PostLikes)

