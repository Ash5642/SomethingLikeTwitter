from re import M, T
from django.db import models
from django.contrib.auth.models import User
from django.db.models.base import ModelStateFieldsCacheDescriptor
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
import uuid
from django.utils.crypto import get_random_string
from django.contrib.auth.models import AbstractUser
from sorl.thumbnail import ImageField, get_thumbnail
from PIL import Image
from django.core.files.storage import default_storage
from io import BytesIO
from django.core.files import File
from pathlib import Path
from . import task
from django.core import validators
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _
from . import validators


VIOLENCE, CP, HARASSMENT, MISLEADING, SPAM = range(5)
USEROFFENSES = (
    (VIOLENCE, 'Promotes violence'),
    (CP, 'CP'),
    (HARASSMENT, 'Harassment'),
    (MISLEADING, 'Misleading content'),
    (SPAM, 'SPAM')
)

ONLYPOSTS, ONLYTOPCOMMENTS, ALL = range(3)
SHOW_STATUS_TYPE_OPTIONS = (
    (ONLYPOSTS, 'Only Posts'),
    (ONLYTOPCOMMENTS, 'Only top comments'),
    (ALL, 'All')
)

en, hi, bn, mr, pa, ta, te, kn = range(8)
Language_options = (
    (en, 'English'),
    (hi, 'Hindi'),
    (bn, 'Bengali'),
    (mr, 'Marathi'),
    (pa, 'Punjabi'),
    (ta, 'Tamil'),
    (te, 'Telugu'),
    (kn, 'Kannada'),
)

Normal, Verified, OverWatch, SiteAdmin = range(4)
UserStatusTypes = (
    (Normal, 'Nornal user'),
    (Verified, 'VerifiedUser'),
    (OverWatch, 'OverWatcher'),
    (SiteAdmin, 'Site Admin')
)

AUTh, RESET_PASSWORD, NUMBER_CONF= range(3)
OTPTokenType = (
    (AUTh, 'Auth token'),
    (RESET_PASSWORD, 'Reset password token'),
    (NUMBER_CONF, 'Number confirmation token')
)

class UserPhoneNumber(models.Model):
    user = models.OneToOneField(User, null=True, on_delete=models.CASCADE, db_index=True, related_name='PhoneNumber')
    PhoneNumber = models.CharField(max_length=13, unique=True)

class UserOTPToken(models.Model):
    Created = models.DateTimeField(auto_now_add=True, null = True)
    Phone = models.OneToOneField(UserPhoneNumber, null=True, on_delete=models.CASCADE, db_index=True)
    Key = models.CharField(null = False, max_length = 5)
    OTPType = models.IntegerField(
        choices=OTPTokenType,
        verbose_name="OTPType",
        null=False,
        blank=False
    )


class UserProfile(models.Model):
    user = models.OneToOneField(User, null=True, on_delete=models.CASCADE, db_index=True)
    Name = models.CharField(max_length=300, null=False, db_index=True, blank=False)
    Bio = models.TextField(max_length=256, blank=True)

    ProfilePicture = models.ImageField(null=False, blank=False,  upload_to='images/Users/ProfilePictures', default='/images/icons/DefaultUserIcon.png')
    Banner = models.ImageField(null=True, blank=True, upload_to='images/Users/Banners', default='/images/icons/DefaultUserBanner.jpg')
    ProfilePictureSmall = models.ImageField(null=True, blank=True, max_length=512, upload_to='images/Users/Thumbnails')

    Followers = models.IntegerField(default=0)
    FollowingCount = models.IntegerField(default = 0)
    PostCount = models.IntegerField(default=0)

    RequirePermissionToFollow = models.BooleanField(default=False, null=False)

    Points = models.IntegerField(default=0)

    Link = models.URLField(null = True, blank = True)
    BirthDay = models.DateField(null = True, blank = True)
    Location = models.CharField(max_length=40, null=True, blank=True)
    UserType = models.IntegerField(
        choices=UserStatusTypes,
        verbose_name="Language",
        default=Normal,
        null=False
    )

    TrustFactor = models.FloatField(default=1)

    Language = models.IntegerField(
        choices=Language_options,
        verbose_name="Language",
        null=True
    )

    @property
    def image_url_with_default(self):
        return self.ProfilePicture or 'images/Users/ProfilePictures/DefaultUserIcon.jpg'

    def __init__(self, *args, **kwargs):
        super(UserProfile, self).__init__(*args, **kwargs)
        self.__original_ProfilePicture = self.ProfilePicture

    def Save_Final(self, force_insert=False, force_update=False, using=None, update_fields=None, *args, **kwargs):
        super().save(*args, **kwargs)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.ProfilePicture != self.__original_ProfilePicture:
            task.GenerateSmallProfilePicture.delay(self.id)


class Groups(models.Model):
    Name = models.CharField(max_length = 16, null = False, blank = False, unique=True)
    Description = models.TextField(max_length = 2048, null = True, blank = True)
    Image = models.ImageField(null=False, blank=False, upload_to = 'images/Communities/Icons', default='/images/icons/DefaultGroupicon.png')
    Banner = models.ImageField(null=False, blank=False, upload_to ='images/Communities/Banners', default='/images/icons/DefaultGroupBanner.webp')
    ImageSmall = models.ImageField(null=True, blank=True, max_length=512,
                                            upload_to='images/Communities/ImagesSmall')
    AnyOneCanJoin = models.BooleanField(default = False)
    PostsArePublic = models.BooleanField(default = True)
    PostsAreNSFW = models.BooleanField(default = False)
    MemberCount = models.IntegerField(default = 0)
    PostCount = models.IntegerField(default=0)

    AllowTextPosts = models.BooleanField(default=True)
    AllowImagePosts = models.BooleanField(default=True)
    AllowVideoPosts = models.BooleanField(default=True)
    AllowLinkPosts = models.BooleanField(default=True)
    AllowPollPosts = models.BooleanField(default=True)
    AllowRePosts = models.BooleanField(default=True)

    Language = models.IntegerField(
        choices=Language_options,
        verbose_name="Language",
        null=True
    )

    def __init__(self, *args, **kwargs):
        super(Groups, self).__init__(*args, **kwargs)
        self.__original_Image = self.Image

    def Save_Final(self, force_insert=False, force_update=False, using=None, update_fields=None, *args, **kwargs):
        super().save(*args, **kwargs)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.Image != self.__original_Image:
            task.GenerateSmallGroupImage.delay(self.id)

class Collections(models.Model):
    Name = models.CharField(null=False, blank=False, max_length = 128, unique=True)
    Image = models.ImageField(null = False, blank = False, upload_to='images/Collections/Icons', default='images/Collections/Icons/DefaultImage.png')
    Banner = models.ImageField(null=False, blank=False, upload_to='images/Collections/Banners', default='images/Collections/Banners/DefaultBanner.jpg')
    Description = models.TextField(max_length = 1024, null = True)
    CreatedBy = models.ForeignKey(UserProfile, on_delete = models.CASCADE, null=True, blank=True, related_name = 'Collections')
    MemberCount = models.IntegerField(default=0)
    FollowingCount = models.IntegerField(default=0)
    Show = models.IntegerField(
        choices=SHOW_STATUS_TYPE_OPTIONS,
        default=ONLYPOSTS,
        verbose_name="status type"
    )

########################################################################################################################

NOTACCEPTED, MEMBER, MOD, BANNED = range(4)
GROUP_STATUS_TYPE_OPTIONS = (
    (NOTACCEPTED, 'NOTACCEPTED'),
    (MEMBER, 'MEMBER'),
    (MOD, 'MOD'),
    (BANNED, 'BANNED')
)

PENDING, ACCEPTED, BLOCKED = range(3)
STATUS_TYPE_OPTIONS = (
    (PENDING, 'Pending'),
    (ACCEPTED, 'Accepted'),
    (BLOCKED, 'Blocked')
)

class GroupMembers(models.Model):
    User = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=False, db_index=True)
    Group = models.ForeignKey(Groups, on_delete=models.CASCADE, null=False)
    Status = models.IntegerField(
        choices=GROUP_STATUS_TYPE_OPTIONS,
        default=NOTACCEPTED,
        verbose_name="status type"
    )
    Time = models.DateTimeField(auto_now_add = True, null = True)
    class Meta:
        unique_together = ['User', 'Group']
        indexes = [
            models.Index(fields=['User', 'Group']),
        ]

class Following(models.Model):
    Follower = models.ForeignKey(UserProfile, null=False, on_delete=models.CASCADE, related_name='Follower')
    GettingFollowed = models.ForeignKey(UserProfile, null=False, on_delete=models.CASCADE, related_name='Followee')
    Status = models.IntegerField(
        choices=STATUS_TYPE_OPTIONS,
        default=PENDING,
        verbose_name="status type"
    )
    class Meta:
        unique_together = ['Follower', 'GettingFollowed']
        indexes = [
            models.Index(fields=['Follower', 'GettingFollowed']),
        ]

class NotifyPosts(models.Model):
    Users = models.OneToOneField(Following, null=False, on_delete=models.CASCADE, related_name='Notify')

class FollowCollection(models.Model):
    Collection = models.ForeignKey(Collections, on_delete = models.CASCADE, null=True, blank=True, related_name = 'Member', db_index=True)
    User = models.ForeignKey(UserProfile, on_delete = models.CASCADE, null=True, blank=True, related_name = 'CollectionMember')
    class Meta:
        indexes = [
            models.Index(fields=['Collection', 'User']),
        ]

class CollectionPosts(models.Model):
    Collection = models.ForeignKey(Collections, on_delete = models.CASCADE, null=True, blank=True, related_name = 'Posts')
    User = models.ForeignKey(UserProfile, on_delete = models.CASCADE, null=True, blank=True, related_name = 'PartOf')

########################################################################################################################

FOLLOWERS, MENTIONED, EVERYONE = range(3)
WHOCANCOMMNENT = (
    (FOLLOWERS, 'FOLLOWERS'),
    (MENTIONED, 'MENTIONED'),
    (EVERYONE, 'EVERYONE'),
)

class Posts(models.Model):
    PostedBy = models.ForeignKey(UserProfile, null=False, on_delete=models.CASCADE, related_name = 'Posts', db_index = True)
    Group = models.ForeignKey(Groups, null=True, blank=True, on_delete=models.CASCADE, related_name='Posts')

    Title = models.TextField(max_length=720, null=False, db_index=True)
    PostedOn = models.DateTimeField(auto_now_add=True, null=True, blank=False, db_index = True)
    Public = models.BooleanField(default=True, null=True, blank = True, db_index = True)

    WhoCanComment = models.IntegerField(
        choices=WHOCANCOMMNENT,
        default=EVERYONE,
        verbose_name="status type",
        null = True, blank = True
    )

    RePost = models.ForeignKey('self', null = True, blank = True, on_delete = models.CASCADE, related_name = 'Reposts',  db_index = True)

    CommentCount = models.IntegerField(default=0, db_index = True)
    Vote = models.IntegerField(default=0, db_index=True)
    ReportCount = models.IntegerField(default=0)

    ByMod = models.BooleanField(default = False, null = True, blank = True)
    Sensitive = models.BooleanField(default = False)

    ParentPost = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE,related_name='ParentPostrev')
    ReplyingTo = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='Replies')
    Language = models.IntegerField(
        choices=Language_options,
        verbose_name="Language",
        null=True
    )
    RePostCount = models.IntegerField(default = 0, db_index = True)
    class Meta:
        unique_together = ['PostedBy', 'RePost']
        indexes = [
            models.Index(fields=['id']),
            models.Index(fields=['PostedBy', 'RePost'])
        ]


class Videos(models.Model):
    Post = models.OneToOneField(Posts, null = False, blank = False, on_delete = models.CASCADE, related_name = 'Video')
    video = models.FileField(upload_to='videos/', validators= [validators.validate_file_extension])

class Images(models.Model):
    Post = models.ForeignKey(Posts, blank = True, null = True, on_delete = models.CASCADE, related_name = 'PostImages')
    Image = ImageField(null=True, blank=True, upload_to ='posts/images', max_length=2048)
    Height = models.IntegerField(default=0)
    Width = models.IntegerField(default=0)
    ThumbNail = ImageField(null = True, blank = True, upload_to='posts/thumbnails', max_length=2048)
    Caption = models.JSONField(max_length=1000, null = True, blank = True)

class PostBodyText(models.Model):
    Post = models.OneToOneField(Posts, blank=True, null=True, on_delete=models.CASCADE, related_name='PostBody')
    PostBody = models.TextField(max_length=40000, null=True, blank=True)

class PostLink(models.Model):
    Post = models.OneToOneField(Posts, blank=True, null=True, on_delete=models.CASCADE, related_name='PostLink')
    Link = models.URLField(null=True, blank=True)
    Image = models.URLField(null = True, blank=True)
    Description = models.CharField(null = True, blank = True, max_length = 2048)

class Mentions(models.Model):
    User = models.ForeignKey(UserProfile, models.CASCADE)
    Post = models.ForeignKey(Posts, on_delete=models.CASCADE, related_name='Mentions')
    class Meta:
        indexes = [
            models.Index(fields=['User', 'Post']),
        ]

class Tags(models.Model):
    Tag = models.CharField(max_length=256, null=False)
    Posts = models.IntegerField(default=0)
    Created = models.DateTimeField(auto_now_add = True)
    Vote = models.IntegerField(default = 0)
    Description = models.TextField(max_length=512, null = True, blank = True)
    TagType = models.CharField(max_length=64, null = True, blank = True)
    Image = models.ImageField(null = True, blank = True)

class Tag(models.Model):
    Post = models.ForeignKey(Posts, blank = True, null = True, on_delete = models.CASCADE, related_name = 'Tags', db_index = True)
    Tag = models.ForeignKey(Tags, blank = True, null = True, on_delete = models.CASCADE, related_name = 'Post', db_index = True)
    class Meta:
        unique_together = ['Post', 'Tag']
        indexes = [
            models.Index(fields=['Post', 'Tag'])
        ]

class Poll(models.Model):
    Post = models.ForeignKey(Posts, blank=True, null=True, on_delete=models.CASCADE, related_name='Poll')
    Text = models.CharField(null=False, blank=False, max_length=128)
    Count = models.IntegerField(default = 0)

class Votes(models.Model):
    Post = models.ForeignKey(Posts, null = True, blank = True, on_delete=models.CASCADE)
    Poll = models.ForeignKey(Poll, null = True, blank = True, on_delete=models.CASCADE)
    User = models.ForeignKey(UserProfile, null = False, blank = False, on_delete=models.CASCADE)

########################################################################################################################

class PostLikes(models.Model):
    User = models.ForeignKey(UserProfile, null=True, on_delete=models.SET_NULL, related_name = 'LikedPost', db_index=True)
    Post = models.ForeignKey(Posts, null=False, on_delete=models.CASCADE, related_name = 'Likes', db_index=True)
    Status = models.BooleanField(null = True, blank = True)
    class Meta:
        unique_together = ['Post', 'User']
        indexes = [
            models.Index(fields=['User', 'Post']),
        ]

class Saved(models.Model):
    Post = models.ForeignKey(Posts, null = False, blank = False, on_delete = models.CASCADE, related_name = 'Saves', db_index=True)
    User = models.ForeignKey(UserProfile, null = False, blank = False, on_delete = models.CASCADE, related_name = 'Saved')

    class Meta:
        unique_together = ['Post', 'User']
        indexes = [
            models.Index(fields=['User', 'Post'])
        ]


########################################################################################################################

class Chats(models.Model):
    User1 = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='OOGABOOGA1')
    User2 = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='OOGABOOGA2')
    LastUpdated = models.DateTimeField(null=True, blank=True)
    class Meta:
        indexes = [
            models.Index(fields=['User1', 'User2']),
            models.Index(fields=['User2', 'User1'])
        ]

class Chat(models.Model):
    From = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='OOGABOOGA')
    To = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    Text = models.TextField(max_length=1024, null=True)
    Read = models.BooleanField(default=False)
    Chats = models.ForeignKey(Chats, null=True, blank=True, on_delete=models.CASCADE, db_index=True)
    Time = models.DateTimeField(auto_now_add = True, null = True, blank = True)

########################################################################################################################






NOTSURE, INNOCENT, HIDE, REMOVE = range(4)
CHARGES = (
    (NOTSURE, 'Not sure'),
    (INNOCENT, 'Innocent'),
    (HIDE, 'Hide'),
    (REMOVE, 'Remove'),
)
INNOCENT, HIDE, REMOVE = range(3)
FINALCHARGES = (
    (INNOCENT, 'Innocent'),
    (HIDE, 'Hide'),
    (REMOVE, 'Remove'),
)

class PostReports(models.Model):
    Post = models.ForeignKey(Posts, null = False, blank = False, on_delete = models.CASCADE, related_name='Reports', db_index=True)
    From = models.ForeignKey(UserProfile, null = False, blank = False,  on_delete = models.CASCADE)
    Type = models.IntegerField(
        choices=USEROFFENSES,
        verbose_name="OffenseType"
    )
    class Meta:
        indexes = [
            models.Index(fields=['id']),
            models.Index(fields=['From', 'Post'])
        ]

class OverWatchers(models.Model):
    User = models.OneToOneField(UserProfile, on_delete = models.CASCADE, related_name = 'IsOverWatcher')

class OverWatchVotes(models.Model):
    User = models.ForeignKey(OverWatchers, null = False, on_delete = models.CASCADE)
    Post = models.ForeignKey(Posts, null = False, on_delete = models.CASCADE, related_name = 'OverWatchVotes')
    Outcome  = models.IntegerField(
        choices=CHARGES,
        verbose_name="Outcome",
        default = INNOCENT
    )

class Offense(models.Model):
    Post = models.OneToOneField(Posts, on_delete = models.CASCADE, related_name = 'OverWatchFinalOutcome')
    Outcome = models.IntegerField(
        choices=FINALCHARGES,
        verbose_name="Outcome",
        default=INNOCENT
    )


class UserViolations(models.Model):
    User = models.ForeignKey(UserProfile, null = False, blank = False, on_delete = models.CASCADE, related_name='Violations')
    OffenseType = models.IntegerField(
        choices=USEROFFENSES,
        verbose_name="status type"
    )
    Post = models.ForeignKey(Posts, on_delete=models.CASCADE)
    Time = models.DateTimeField(auto_now_add=True)


########################################################################################################################

class Notifications(models.Model):
    User = models.ForeignKey(UserProfile, null=True, blank=True, on_delete=models.CASCADE, related_name='NotificationsTo', db_index=True)
    From = models.ForeignKey(UserProfile, null = True, blank = True, on_delete=models.CASCADE, related_name='NotificationsFrom')
    Post = models.ForeignKey(Posts, null = True, blank = True, on_delete = models.CASCADE)
    Type = models.CharField(max_length = 7, null = True, blank = True)
    Created = models.DateTimeField(null = True, blank = True)
    Group = models.ForeignKey(Groups, null=True, blank=True, on_delete=models.CASCADE, related_name='NotificationsTo')

class FireBaseNotificationTokens(models.Model):
    User = models.ForeignKey(UserProfile, null=False, blank=False, on_delete=models.CASCADE, related_name = 'NotificationToken')
    Token = models.CharField(max_length = 256)

    def __str__(self):
        return self.Token  # id is field of Counsel object you want to show
    class Meta:
        unique_together = ['User', 'Token']

########################################################################################################################

class LastHandleChange(models.Model):
    User = models.OneToOneField(User, on_delete=models.CASCADE, related_name='LastHandleChange')
    Time = models.DateTimeField(auto_now_add = True, null = False)


class Change_Password_Token(models.Model):
    User = models.ForeignKey(User, on_delete = models.CASCADE)
    Key = models.CharField(null = False, max_length = 64)
    Created = models.DateTimeField(auto_now_add=True, null = True)
