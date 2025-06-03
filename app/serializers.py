from rest_framework import serializers
from .models import *
from django.core import exceptions
from datetime import datetime, timezone,timedelta
class ImageSeriaizer(serializers.ModelSerializer):
    class Meta:
        model = Images
        fields = ['Image', 'ThumbNail', 'Caption', 'Height', 'Width']

class PostBodySerializer(serializers.ModelSerializer):
    class Meta:
        model = PostBodyText
        fields = ['PostBody']
class PollSerializer(serializers.ModelSerializer):
    class Meta:
        model = Poll
        fields = ['Text', 'Count', 'id']

class MiniGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Groups
        fields = ['Name', 'Image', 'Description', 'PostsArePublic', 'ImageSmall']

class VideoSerialzier(serializers.ModelSerializer):
    class Meta:
        model  = Videos
        fields = ['video']

class PostedBySerializer(serializers.ModelSerializer):
    UserName = serializers.ReadOnlyField(source='user.username')
    class Meta:
        model = UserProfile
        fields = ['Name', 'UserName', 'ProfilePicture', 'ProfilePictureSmall', 'UserType']
        read_only_fields = fields

class PostLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostLink
        fields = ['Link', 'Description', 'Image']

class ParentPostSerializer(serializers.ModelSerializer):
    PostedBy = PostedBySerializer(many=False, read_only=True)
    Group = MiniGroupSerializer(many = False, read_only=True)
    class Meta:
        model = Posts
        fields = ['PostedBy', 'Group', 'id']
        read_only_fields = fields


class RePostSerializer(serializers.ModelSerializer):
    PostedBy = PostedBySerializer(many=False, read_only=True)
    PostedToGroupName = serializers.ReadOnlyField(source='PostedToGroup.GroupName')
    PostedToGroupImage = serializers.ReadOnlyField(source='PostedToGroup.GroupImage.url')
    Liked = serializers.SerializerMethodField('_user')
    PostImages = ImageSeriaizer(many = True, read_only = True)
    Poll = PollSerializer(many = True, read_only = True)
    ParentPost = ParentPostSerializer(many=False, read_only=True)
    Video = VideoSerialzier(many=False, read_only=True)
    Time = serializers.SerializerMethodField('_time')
    RePosted = serializers.SerializerMethodField('_RePosted')
    Group = MiniGroupSerializer(many=False, read_only=True)
    PostBody = PostBodySerializer(many = False, read_only = True)

    def _RePosted(self, obj):
        request = self.context.get('request', None)
        if request:
            CurrentUser = request.auth.user
            try:
                Posts.objects.get(PostedBy = CurrentUser.userprofile, RePost = obj.id)
                return True
            except exceptions.ObjectDoesNotExist:
                return False

    def _time(self, obj):
        return datetime.now(timezone.utc) - obj.PostedOn

    MyChoice = serializers.SerializerMethodField('_MyVote')
    def _MyVote(self, obj):
        request = self.context.get('request', None)
        if request:
            CurrentUser = request.auth.user
            try:
                Option = Votes.objects.get(User=CurrentUser.userprofile, Post=obj.id)
                return Option.Poll.id
            except exceptions.ObjectDoesNotExist:
                return None
    # Use this method for the custom field
    def _user(self, obj):
        request = self.context.get('request', None)
        if request:
            CurrentUser = request.auth.user
            try:
                Status = obj.Likes.get(User=CurrentUser.userprofile)
                return Status.Status
            except exceptions.ObjectDoesNotExist:
                return None

    class Meta:
        model = Posts
        fields = ['Title', 'PostBody',
                  'PostedOn', 'Liked', 'id', 'PostedToGroupName',
                  'PostedToGroupImage', 'WhoCanComment', 'PostImages', 'Poll', 'MyChoice',  'PostedBy', 'CommentCount', 'Vote', 'ParentPost', 'Video', 'Time', 'RePosted', 'RePostCount', 'Group', 'Sensitive']
        read_only_fields = fields


class CommentReplYSerailzer(serializers.ModelSerializer):
    PostedBy = PostedBySerializer(many=False, read_only=True)
    PostedToGroupName = serializers.ReadOnlyField(source='PostedToGroup.GroupName')
    PostedToGroupImage = serializers.ReadOnlyField(source='PostedToGroup.GroupImage.url')
    Liked = serializers.SerializerMethodField('_user')
    PostImages = ImageSeriaizer(many=True, read_only=True)
    Poll = PollSerializer(many=True, read_only=True)
    MyChoice = serializers.SerializerMethodField('_MyVote')
    Repost = serializers.SerializerMethodField('_RePost')
    ParentPostUserName = serializers.ReadOnlyField(source='ParentPost.PostedBy.user.username')

    def _RePost(self, obj):
        request = self.context.get('request', None)
        if request:
            if obj.RePost:
                try:
                    OriginalPost = Posts.objects.get(id=obj.RePost.id)
                    serializer = RePostSerializer(OriginalPost, many=False,
                                                  context={'request': self.context.get('request', None)})
                    return serializer.data
                except exceptions.ObjectDoesNotExist:
                    return None
            else:
                return None

    def _MyVote(self, obj):
        request = self.context.get('request', None)
        if request:
           ##print(request)
            CurrentUser = request.auth.user
            try:
                Option = Votes.objects.get(User=CurrentUser.userprofile, Post=obj.id)
                return Option.Poll.id
            except exceptions.ObjectDoesNotExist:
                return None

    # Use this method for the custom field
    def _user(self, obj):
        request = self.context.get('request', None)
        if request:
            CurrentUser = request.auth.user
            try:
                PostLikes.objects.get(Post=obj.id, User=CurrentUser.userprofile)
                return True
            except exceptions.ObjectDoesNotExist:
                return False

    class Meta:
        model = Posts
        fields = ['Title', 'PostBody',
                  'PostedOn', 'Liked', 'id', 'PostedToGroupName',
                  'PostedToGroupImage', 'WhoCanComment', 'PostImages', 'Poll', 'MyChoice',  'PostedBy',
                  'CommentCount', 'Vote', 'ParentPost', 'RePost', 'ParentPost', 'ParentPostUserName']
        read_only_fields = fields
class TextBodySerializer(serializers.ModelSerializer):
    class Meta:
        model = PostBodyText
        fields = ['PostBody']
        read_only_fields = fields

class OverWatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offense
        fields = '__all__'

class PostSerializer(serializers.ModelSerializer):
    PostedBy = PostedBySerializer(many=False, read_only=True)
    Liked = serializers.SerializerMethodField('_user')
    PostImages = ImageSeriaizer(many = True, read_only = True)
    Poll = PollSerializer(many = True, read_only = True)
    MyChoice = serializers.SerializerMethodField('_MyVote')
    RePost = serializers.SerializerMethodField('_RePost')
    Video = VideoSerialzier(many=False, read_only=True)
    Time = serializers.SerializerMethodField('_time')
    ReplyingTo = ParentPostSerializer(many=False, read_only=True)
    Me = serializers.SerializerMethodField('_Me')
    RePosted = serializers.SerializerMethodField('_RePosted')
    Group = MiniGroupSerializer(many = False, read_only = True)
    Auth = serializers.SerializerMethodField('_auth')
    PostBody = TextBodySerializer(many=False, read_only=True)
    OverWatchFinalOutcome = OverWatchSerializer(many = False, read_only = True)
    PostLink = PostLinkSerializer(many = False, read_only = True)

    def _auth(self, obj):
        return self.context.get('auth', False)
    def _RePosted(self, obj):
        request = self.context.get('request', None)
        if request:
            CurrentUser = request.auth.user
            try:
                Posts.objects.get(PostedBy = CurrentUser.userprofile, RePost = obj.id)
                return True
            except exceptions.ObjectDoesNotExist:
                return False
        else:
            return None

    def _time(self, obj):
        return datetime.now(timezone.utc) - obj.PostedOn

    ParentPost = ParentPostSerializer(many = False, read_only = True)
    def _RePost(self, obj):
        request = self.context.get('request', None)
        if obj.RePost:
            try:
                OriginalPost = Posts.objects.get(id=obj.RePost.id)
                serializer = RePostSerializer(OriginalPost, many = False, context={'request':self.context.get('request', None)})
                return serializer.data
            except exceptions.ObjectDoesNotExist:
                return None
        else:
            return None
 



    def _Me(self, obj):
        if self.context.get('request', None):
            if self.context.get('request', None).auth.user.id == obj.PostedBy.id:
                return True
            else:
                return False
        else:
            return None

    def _user(self, obj):
        request = self.context.get('request', None)
        if request:
            CurrentUser = request.auth.user
            try:
                Status = obj.Likes.get(User = CurrentUser.userprofile)
                return Status.Status
            except exceptions.ObjectDoesNotExist:
                return None
        else:
            return None



    def _MyVote(self, obj):
        request = self.context.get('request', None)
        if request:
            CurrentUser = request.auth.user
            try:
                Option = Votes.objects.get(User=CurrentUser.userprofile, Post=obj.id)
                return Option.Poll.id
            except exceptions.ObjectDoesNotExist:
                return None

    class Meta:
        model = Posts
        fields = ['Title', 'PostBody',
                  'PostedOn', 'Liked', 'id'
                  , 'WhoCanComment', 'PostImages', 'Poll', 'MyChoice',  'PostedBy', 'CommentCount', 'Vote', 'ParentPost', 'RePost', 'ParentPost', 'Video', 'Time', 'ReplyingTo', 'Me', 'RePosted', 'RePostCount', 'Group', 'Auth', 'ByMod', 'Sensitive', 'OverWatchFinalOutcome', 'PostLink', 'Public']
        read_only_fields = fields

class PostReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostReports
        fields = ['Type']

class OverWatchSerializer(serializers.ModelSerializer):
    PostImages = ImageSeriaizer(many = True, read_only = True)
    Poll = PollSerializer(many = True, read_only = True)
    Video = VideoSerialzier(many=False, read_only=True)
    Time = serializers.SerializerMethodField('_time')
    PostBody = TextBodySerializer(many=False, read_only=True)
    Reports = PostReportSerializer(many = True, read_only=True)
    def _time(self, obj):
        return datetime.now(timezone.utc) - obj.PostedOn




    # Use this method for the custom field
    def _user(self, obj):
        request = self.context.get('request', None)
        if request:
            CurrentUser = request.auth.user
            try:
                Status = PostLikes.objects.get(Post = obj.id, User = CurrentUser.userprofile)
                return Status.Status
            except exceptions.ObjectDoesNotExist:
                return None

    class Meta:
        model = Posts
        fields = ['Title', 'PostBody',
                  'PostedOn', 'id'
                  , 'WhoCanComment', 'PostImages', 'Poll',  'Vote', 'ParentPost', 'Video', 'Link', 'Time', 'Reports']
        read_only_fields = fields

class PostMultiSerializer(serializers.ModelSerializer):
    PostedBy = PostedBySerializer(many=False, read_only=True)
    PostedToGroupName = serializers.ReadOnlyField(source='PostedToGroup.GroupName')
    PostedToGroupImage = serializers.ReadOnlyField(source='PostedToGroup.GroupImage.url')
    Liked = serializers.SerializerMethodField('_user')
    PostImages = ImageSeriaizer(many = True, read_only = True)
    Poll = PollSerializer(many = True, read_only = True)
    MyChoice = serializers.SerializerMethodField('_MyVote')
    Repost = serializers.SerializerMethodField('_RePost')
    RePost = RePostSerializer(many=False, read_only=True)
    Video = VideoSerialzier(many=False, read_only=True)
    Time = serializers.SerializerMethodField('_time')
    ReplyingTo = ParentPostSerializer(many=False, read_only=True)
    BestReply = serializers.SerializerMethodField('_BestReply')
    Me = serializers.SerializerMethodField('_Me')

    def _Me(self, obj):
        if self.context.get('request', None).auth.user.id == obj.PostedBy.id:
            return True
        else:
            return False

    def _time(self, obj):
        return datetime.now(timezone.utc) - obj.PostedOn

    def _BestReply(self, obj):
        request = self.context.get('request', None)
        if request:
            if obj.Replies:
                try:
                    BestReply = Posts.objects.filter(ReplyingTo=None, ParentPost = obj.id).order_by('-Vote')[0]
                    if BestReply.Vote > 0.75*obj.Vote:
                        serializer = PostSerializer(BestReply, many=False, context={'request': self.context.get('request', None)})
                    else:
                        return None
                    return serializer.data
                except:
                    return None

            else:
                return None

    ParentPost = ParentPostSerializer(many = False, read_only = True)
    def _RePost(self, obj):
        request = self.context.get('request', None)
        if request:
            if obj.RePost:
                try:
                    OriginalPost = Posts.objects.get(id=obj.RePost.id)
                    serializer = RePostSerializer(OriginalPost, many = False, context={'request':self.context.get('request', None)})
                    return serializer.data
                except exceptions.ObjectDoesNotExist:
                    return None
            else:
                return None





    def _MyVote(self, obj):
        request = self.context.get('request', None)
        if request:
           ##print(request)
            CurrentUser = request.auth.user
            try:
                Option = Votes.objects.get(User=CurrentUser.userprofile, Post=obj.id)
                return Option.Poll.id
            except exceptions.ObjectDoesNotExist:
                return None
    # Use this method for the custom field
    def _user(self, obj):
        request = self.context.get('request', None)
        if request:
            CurrentUser = request.auth.user
            try:
                PostLikes.objects.get(Post = obj.id, User = CurrentUser.userprofile)
                return True
            except exceptions.ObjectDoesNotExist:
                return False

    class Meta:
        model = Posts
        fields = ['Title', 'PostBody',
                  'PostedOn', 'Liked', 'id', 'PostedToGroupName',
                  'PostedToGroupImage', 'WhoCanComment', 'PostImages', 'Poll', 'MyChoice',  'PostedBy', 'CommentCount', 'Vote', 'ParentPost', 'RePost', 'ParentPost', 'Repost', 'Video', 'Time', 'ReplyingTo', 'BestReply', 'Link', 'Me']
        read_only_fields = fields

class CommentSerializerFull(serializers.ModelSerializer):
    PostedBy = PostedBySerializer(many=False, read_only=True)
    PostedToGroupName = serializers.ReadOnlyField(source='PostedToGroup.GroupName')
    PostedToGroupImage = serializers.ReadOnlyField(source='PostedToGroup.GroupImage.url')
    Liked = serializers.SerializerMethodField('_user')
    PostImages = ImageSeriaizer(many = True, read_only = True)
    Poll = PollSerializer(many = True, read_only = True)
    MyChoice = serializers.SerializerMethodField('_MyVote')
    Repost = serializers.SerializerMethodField('_RePost')
    RePost = RePostSerializer(many=False, read_only=True)
    Video = VideoSerialzier(many=False, read_only=True)
    Time = serializers.SerializerMethodField('_time')
    ReplyingTo = ParentPostSerializer(many=False, read_only=True)
    BestReply = serializers.SerializerMethodField('_BestReply')
    def _time(self, obj):
        return datetime.now(timezone.utc) - obj.PostedOn

    def _BestReply(self, obj):
        request = self.context.get('request', None)
        if request:
            if obj.Replies:
               ##print(Posts.objects.filter(ReplyingTo=obj.id).order_by('-Vote'))
                try:

                    BestReply = Posts.objects.filter(ReplyingTo=obj.id).order_by('-Vote')[0]
                    serializer = PostSerializer(BestReply, many=False,
                                                  context={'request': self.context.get('request', None)})
                    return serializer.data
                except:
                    return None

            else:
                return None

    ParentPost = ParentPostSerializer(many = False, read_only = True)
    def _RePost(self, obj):
        request = self.context.get('request', None)
        if request:
            if obj.RePost:
                try:
                    OriginalPost = Posts.objects.get(id=obj.RePost.id)
                    serializer = RePostSerializer(OriginalPost, many = False, context={'request':self.context.get('request', None)})
                    return serializer.data
                except exceptions.ObjectDoesNotExist:
                    return None
            else:
                return None





    def _MyVote(self, obj):
        request = self.context.get('request', None)
        if request:
           ##print(request)
            CurrentUser = request.auth.user
            try:
                Option = Votes.objects.get(User=CurrentUser.userprofile, Post=obj.id)
                return Option.Poll.id
            except exceptions.ObjectDoesNotExist:
                return None
    # Use this method for the custom field
    def _user(self, obj):
        request = self.context.get('request', None)
        if request:
            CurrentUser = request.auth.user
            try:
                PostLikes.objects.get(Post = obj.id, User = CurrentUser.userprofile)
                return True
            except exceptions.ObjectDoesNotExist:
                return False

    class Meta:
        model = Posts
        fields = ['Title', 'PostBody',
                  'PostedOn', 'Liked', 'id','PostedToGroupName',
                  'PostedToGroupImage', 'WhoCanComment', 'PostImages', 'Poll', 'MyChoice',  'PostedBy', 'CommentCount', 'Vote', 'ParentPost', 'RePost', 'ParentPost', 'Repost', 'Video', 'Time', 'ReplyingTo', 'BestReply']
        read_only_fields = fields

class PostSerializerFull(serializers.ModelSerializer):
    PostedBy = PostedBySerializer(many=False, read_only=True)
    PostedToGroupName = serializers.ReadOnlyField(source='PostedToGroup.GroupName')
    PostedToGroupImage = serializers.ReadOnlyField(source='PostedToGroup.GroupImage.url')
    Liked = serializers.SerializerMethodField('_user')
    PostImages = ImageSeriaizer(many=True, read_only=True)
    Poll = PollSerializer(many=True, read_only=True)
    AllowedToComment = serializers.SerializerMethodField('_allowed')
    RePosted = serializers.SerializerMethodField('_RePosted')
    RePost = RePostSerializer(many = False, read_only = True)
    ParentPost = ParentPostSerializer(many = False, read_only = True)
    ReplyingTo = ParentPostSerializer(many = False, read_only = True)
    Video = VideoSerialzier(many = False, read_only = True)
    Time = serializers.SerializerMethodField('_time')
    Saved = serializers.SerializerMethodField('_Saved')
    Me = serializers.SerializerMethodField('_Me')
    Group = MiniGroupSerializer(many=False, read_only=True)
    Auth = serializers.SerializerMethodField('_auth')
    PostBody = TextBodySerializer(many=False, read_only=True)
    Reported = serializers.SerializerMethodField('_Reported')
    PostLink = PostLinkSerializer(many=False, read_only=True)
    MyChoice = serializers.SerializerMethodField('_MyVote')
    def _MyVote(self, obj):
        request = self.context.get('request', None)
        if request:
            CurrentUser = request.auth.user
            try:
                Option = Votes.objects.get(User=CurrentUser.userprofile, Post=obj.id)
                return Option.Poll.id
            except exceptions.ObjectDoesNotExist:
                return None
        else:
            return None

    def _auth(self, obj):
        return self.context.get('auth', False)

    def _Me(self, obj):
        if self.context.get('request'):
            if self.context.get('request', None).auth.user.id == obj.PostedBy.id:
                return True
            else:
                return False
        else:
            return False

    def _Saved(self, obj):
        request = self.context.get('request', None)
        if request:
            try:
                Saved.objects.get(User = request.auth.user.userprofile, Post = obj)
                return True
            except exceptions.ObjectDoesNotExist:
                return False
        else:
            return None

    def _Reported(self, obj):
        request = self.context.get('request', None)
        if request:
            try:
                PostReports.objects.get(From = request.auth.user.userprofile, Post = obj)
                return True
            except exceptions.ObjectDoesNotExist:
                return False
        else:
            return None
    def _time(self, obj):
        return datetime.now(timezone.utc)-obj.PostedOn
    def _allowed(self, obj):
        request = self.context.get('request', None)
        if request:
            CurrentUser = request.auth.user
            if CurrentUser.userprofile == obj.PostedBy:
                return True
            try:
                Following.objects.get(Follower=obj.PostedBy, GettingFollowed=CurrentUser.userprofile,
                                      Status=2)
                return 'blocked'
            except exceptions.ObjectDoesNotExist:
                pass
            if obj.ParentPost:
                if obj.Group:
                    try:
                        Membership = GroupMembers.objects.get(User = CurrentUser.userprofile, Group = obj.ParentPost.Group)
                        if Membership.Status == 1 or Membership.Status == 2:
                            return True
                        else:
                            return 'notmember'
                    except exceptions.ObjectDoesNotExist:
                        return 'notmember'
                else:
                    WhoCanComment = obj.ParentPost.WhoCanComment
                    if WhoCanComment == EVERYONE:
                        return True
                    elif WhoCanComment == FOLLOWERS:
                        try:
                            Following.objects.get(GettingFollowed = obj.ParentPost.PostedBy, Follower = CurrentUser.userprofile)
                            return True
                        except exceptions.ObjectDoesNotExist:
                            try:
                                Mentions.objects.get(Post = obj.ParentPost, User = CurrentUser.userprofile)
                                return True
                            except exceptions.ObjectDoesNotExist:
                                return 'notfollowing'
                    elif WhoCanComment == MENTIONED:
                        try:
                            Mentions.objects.get(Post=obj.ParentPost, User=CurrentUser.userprofile)
                            return True
                        except exceptions.ObjectDoesNotExist:
                            return 'notmentioned'
            else:
                if obj.Group:
                    try:
                        Membership = GroupMembers.objects.get(User=CurrentUser.userprofile, Group=obj.Group)
                        if Membership.Status == 1 or Membership.Status == 2:
                            return True
                        else:
                            return 'notmember'
                    except exceptions.ObjectDoesNotExist:
                        return 'notmember'
                else:
                    WhoCanComment = obj.WhoCanComment
                    if WhoCanComment == EVERYONE:
                        return True
                    elif WhoCanComment == FOLLOWERS:
                        try:
                            Following.objects.get(GettingFollowed=obj.PostedBy,
                                                  Follower=CurrentUser.userprofile)
                            return True
                        except exceptions.ObjectDoesNotExist:
                            try:
                                Mentions.objects.get(Post=obj, User=CurrentUser.userprofile)
                                return True
                            except exceptions.ObjectDoesNotExist:
                                return 'notfollowing'
                    elif WhoCanComment == MENTIONED:
                        try:
                            Mentions.objects.get(Post=obj, User=CurrentUser.userprofile)
                            return True
                        except exceptions.ObjectDoesNotExist:
                            return 'notmentioned'
        else:
            return None


    # Use this method for the custom field
    def _user(self, obj):
        request = self.context.get('request', None)
        if request:
            CurrentUser = request.auth.user
            try:
                Status = PostLikes.objects.get(Post = obj.id, User = CurrentUser.userprofile)
                return Status.Status
            except exceptions.ObjectDoesNotExist:
                return None
        else:
            return None
    def _RePosted(self, obj):
        request = self.context.get('request', None)
        if request:
            CurrentUser = request.auth.user
            try:
                RePost = Posts.objects.get(PostedBy = CurrentUser.userprofile, RePost = obj.id)
               ##print(str(RePost)+'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGAHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHIiiiiiiiiiiiiiiiiiiiiii')
                return True
            except exceptions.ObjectDoesNotExist as error:
               ##print(error)
                return False
        else:
            return None

    def _MyVote(self, obj):
        request = self.context.get('request', None)
        if request:
            CurrentUser = request.auth.user
            try:
                Option = Votes.objects.get(User=CurrentUser.userprofile, Post=obj.id)
                return Option.Poll.id
            except exceptions.ObjectDoesNotExist:
                return None
        else:
            return None

    class Meta:
        model = Posts
        fields = ['Title', 'PostBody',
                  'PostedOn', 'Liked', 'id', 'PostedToGroupName',
                  'PostedToGroupImage', 'WhoCanComment', 'PostImages', 'Poll', 'AllowedToComment', 'PostedBy', 'Vote', 'CommentCount', 'PostedOn', 'Public', 'RePosted', 'RePost', 'ParentPost', 'Video', 'RePostCount', 'Time', 'Saved', 'ReplyingTo', 'Me', 'Group', 'Auth', 'Reported', 'PostLink', 'Sensitive', 'MyChoice', 'Language']
        read_only_fields = fields

class UserProfileSerializer(serializers.ModelSerializer):
    UserName = serializers.ReadOnlyField(source='user.username')
    NotificationsEnabled = serializers.SerializerMethodField('_notify')
    Following = serializers.SerializerMethodField('_following')
    Joined = serializers.SerializerMethodField('_joined')
    FollowBack = serializers.SerializerMethodField('_FollowBack')
    Me = serializers.SerializerMethodField('_me')


    def _me(self, obj):
        request = self.context.get('request', None)
        if request:
            if request.auth.user.userprofile == obj:
                return True
            else:
                return False
        else:
            return None

    def _FollowBack(self, obj):
        request = self.context.get('request', None)
        if request:
            try:
                Status = Following.objects.get(GettingFollowed = request.auth.user.userprofile, Follower = obj)
                return Status.Status
            except exceptions.ObjectDoesNotExist:
                return None
        else:
            return None
    def _joined(self, obj):
        return datetime.now(timezone.utc) - obj.user.date_joined

    def _following(self, obj):
        request = self.context.get('request', None)
        if request:
            try:
                Users = Following.objects.get(GettingFollowed = obj, Follower = request.auth.user.userprofile)
                return Users.Status
            except exceptions.ObjectDoesNotExist:
                return None
        else:
            return None
    def _notify(self, obj):
        request = self.context.get('request', None)
        if request:
            try:
                Users = Following.objects.get(GettingFollowed = obj, Follower = request.auth.user.userprofile)
                NotifyPosts.objects.get(Users = Users)
                return True
            except exceptions.ObjectDoesNotExist:
                return False
        else:
            return None
    class Meta:
        model = UserProfile
        fields = ['UserName', 'Name', 'Location', 'ProfilePicture', 'Bio', 'RequirePermissionToFollow', 'Followers', 'Banner', 'NotificationsEnabled','Following', 'Joined', 'PostCount', 'Link', 'BirthDay', 'FollowBack', 'Following', 'id', 'Me', 'IsOverWatcher', 'FollowingCount', 'ProfilePictureSmall', 'UserType', 'Points']
        read_only_fields = fields


class FollowerSerializers(serializers.ModelSerializer):
    FollowerData = serializers.SerializerMethodField('_FollowerData')
    def _FollowerData(self, obj):
        Profile = UserProfile.objects.get(id=obj.Follower.id)
        request = self.context.get('request', None)
        serializer = UserProfileSerializer(Profile, many=False, context={'request': self.context.get('request', None)})
        return serializer.data
        
    class Meta:
        model = Following
        fields = ['Status', 'FollowerData']

class UserPhoneNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPhoneNumber
        fields = '__all__'

class UserSerialzier(serializers.ModelSerializer):
    PhoneNumber = UserPhoneNumberSerializer(many = False, read_only = True)
    class Meta:
        model = User
        fields = '__all__'

class MeUserProfileSerializer(serializers.ModelSerializer):
    user = UserSerialzier(many=False, read_only=True)
    class Meta:
        model = UserProfile
        fields = '__all__'

class BlockedUserProfileSerializer(serializers.ModelSerializer):
    UserName = serializers.ReadOnlyField(source='user.username')
    NotificationsEnabled = serializers.SerializerMethodField('_notify')
    Following = serializers.SerializerMethodField('_following')
    Joined = serializers.SerializerMethodField('_joined')
    FollowBack = serializers.SerializerMethodField('_FollowBack')

    def _FollowBack(self, obj):
        request = self.context.get('request', None)
        if request:
            try:
                Status = Following.objects.get(GettingFollowed = request.auth.user.userprofile, Follower = obj)
                return Status.Status
            except exceptions.ObjectDoesNotExist:
                return None
    def _joined(self, obj):
        return datetime.now(timezone.utc) - obj.user.date_joined

    def _following(self, obj):
        request = self.context.get('request', None)
        if request:
            try:
                Users = Following.objects.get(GettingFollowed = obj, Follower = request.auth.user.userprofile)
                return Users.Status
            except exceptions.ObjectDoesNotExist:
                return None
        else:
            return None
    def _notify(self, obj):
        request = self.context.get('request', None)
        if request:
            try:
                Users = Following.objects.get(GettingFollowed = obj, Follower = request.auth.user.userprofile)
                NotifyPosts.objects.get(Users = Users)
                return True
            except exceptions.ObjectDoesNotExist:
                return False
        else:
            return None
    class Meta:
        model = UserProfile
        fields = ['UserName', 'Name', 'Location', 'ProfilePicture', 'Bio', 'RequirePermissionToFollow', 'Followers', 'Banner', 'NotificationsEnabled','Following', 'Joined', 'PostCount', 'Link', 'BirthDay', 'FollowBack', 'Following', 'id']
        read_only_fields = fields

class GroupMemberSerializer(serializers.ModelSerializer):
    UserName = serializers.ReadOnlyField(source='User.user.username')
    Name = serializers.ReadOnlyField(source='User.Name')
    ProfilePicture = serializers.ReadOnlyField(source='User.ProfilePicture.url')
    class Meta:
        model = GroupMembers
        fields = ['UserName', 'Name', 'ProfilePicture', 'Status']
        read_only_fields = fields

class UserSearchSerializer(serializers.ModelSerializer):
    Follow = serializers.SerializerMethodField('_user')

    # Use this method for the custom field
    def _user(self, obj):
        request = self.context.get('request', None)
        if request:
           ##print(request)
            try:
                CurrentUser = request.auth.user
                try:
                    Follow = Following.objects.get(Follower = CurrentUser, GettingFollowed = obj.userprofile)
                    return Follow
                except exceptions.ObjectDoesNotExist:
                    return None
            except AttributeError:
                return "LogIn"

    UserName = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = UserProfile
        fields = ['UserName', 'Name', 'Location', 'ProfilePicture', 'Bio',
                  'RequirePermissionToFollow', 'Followers', 'Follow']
        read_only_fields = fields


class ImageCrud(serializers.ModelSerializer):
    class Meta:
        model = Images
        fields = ['Image', 'Caption']

class PollCrud(serializers.ModelSerializer):
    class Meta:
        model = Poll
        fields = ['Text']



class PostBodyCRUD(serializers.ModelSerializer):
    class Meta:
        model = PostBodyText
        fields = ['PostBody']

class PostCRUD_Poll(serializers.ModelSerializer):
    Poll = PollCrud(many = True, allow_null=True)
    class Meta:
        model = Posts
        fields = ['Title', 'Poll']

    def create(self, validated_data):
        Title = validated_data.pop('Title', None)
        PostedBy = self.context.get('request').auth.user.userprofile


        Post = Posts.objects.create(Title=validated_data.get('Title'),
                                   PostedBy=self.context.get('request').auth.user.userprofile)
        PollData = validated_data.pop('Poll')
        PostBodyData = self.context.get('PostBody')
       ##print(PostBodyData)
        if PostBodyData:
           ##print('PENISNUTSACKS')
            postbodyserializer = PostBodyCRUD(data={'PostBody': PostBodyData}, many=False)
            if postbodyserializer.is_valid():
               ##print('PENISBALLSACKS')
                postbodyserializer.save(Post=Post)
        poll_serializer = PollCrud(data = PollData, many = True)
        if poll_serializer.is_valid():
            poll_serializer.save(Post = Post)
        return Post


class PostCRUD_Image(serializers.ModelSerializer):
    class Meta:
        model = Posts
        fields = ['Title', 'Public', 'WhoCanComment', 'Sensitive']

    def create(self, validated_data):
        images_data = self.context.get('request').FILES
        Title = validated_data.pop('Title')
        PostedBy = self.context.get('request').auth.user.userprofile
        Group = self.context.get('Group', None)
        WhoCanComment = validated_data.get('WhoCanComment')
        ByMod = self.context.get('by_mod', False)
        Sensitive = validated_data.get('Sensitive', False)
        Public = validated_data.get('Public')
        RePost = self.context.get('RePost', None)
        ParentPost = self.context.get('ParentPost', None)
        ReplyingTo = self.context.get('ReplyingTo', None)
        PostBodyData = self.context.get('PostBody')
        Link = self.context.get('Link')

        if ParentPost:
            Public = ParentPost.Public
            WhoCanComment = None
            PostBodyData = None

        if Group:
            try:
                GroupMembers.objects.get(User=PostedBy, Group=Group, Status=2)
                ByMod = True
            except exceptions.ObjectDoesNotExist:
                ByMod = False
            if ByMod:
                pass
            else:
                if Group.AllowTextPosts:
                    pass
                else:
                    PostBodyData = None

                if Group.AllowImagePosts:
                    pass
                else:
                    images_data = None

                if Group.AllowLinkPosts:
                    pass
                else:
                    Link = None
                if Group.AllowPollPosts:
                    pass
                else:
                    PollData = None

            if Group.PostsAreNSFW:
                Sensitive = True
            else:
                pass


        if Public == False:
            if WhoCanComment == 2:
                WhoCanComment = FOLLOWERS
            else:
                pass
        Post = Posts.objects.create(
            Title=Title,
            PostedBy=PostedBy,
            Public=Public,
            WhoCanComment=WhoCanComment,
            Group=Group,
            ByMod=ByMod,
            Sensitive=Sensitive,
            RePost = RePost,
            ParentPost = ParentPost,
            ReplyingTo = ReplyingTo

        )
        #print('DONE!!!!!!!')
       ##print(PostBodyData)

        if Link:
           ##print(Link)
            LinkSerializer = PostLinkSerializer(data={'Link': Link}, many=False)
            if LinkSerializer.is_valid():
                LinkSerializer.save(Post=Post)
        if PostBodyData:
           ##print('PENISNUTSACKS')
            postbodyserializer = PostBodyCRUD(data={'PostBody': PostBodyData}, many=False)
            if postbodyserializer.is_valid():
               ##print('PENISBALLSACKS')
                postbodyserializer.save(Post=Post)
        
        if Group:
            if Group.AllowImagePosts:
                for image_data in images_data.values():
                    serializer = ImageCrud(data={'Image': image_data, 'Post': Post.id})
                    if serializer.is_valid():
                        serializer.save(Post=Post)
                    ##print('success')
            
            else:
                pass
        else:
            for image_data in images_data.values():
                serializer = ImageCrud(data={'Image': image_data, 'Post': Post.id})
                if serializer.is_valid():
                    serializer.save(Post=Post)
                ##print('success')
        return Post

class RePostCRUD(serializers.ModelSerializer):
    class Meta:
        model = Posts
        fields = ['Title', 'Public', 'WhoCanComment']

    def create(self, validated_data):
        images_data = self.context.get('request').FILES
        RePosted = self.context.get('RePost')
        Post = Posts.objects.create(
            Title=validated_data.get('Title'),
            PostedBy=self.context.get('request').auth.user.userprofile, Public = validated_data.get('Public'), WhoCanComment = validated_data.get('WhoCanComment'), RePost = RePosted)
        for image_data in images_data.values():
            serializer = ImageCrud(data={'Image': image_data, 'Post': Post.id})
            if serializer.is_valid():
                serializer.save(Post=Post)
               ##print('success')
        return Post


class PostCRUD(serializers.ModelSerializer):
    Poll = PollCrud(many = True, allow_null=True)
    class Meta:
        model = Posts
        fields = ['Title', 'Poll', 'Public', 'WhoCanComment', 'Sensitive']

    def create(self, validated_data):

       ##print(validated_data.get('Public'))

        Title = validated_data.pop('Title')
        PostedBy = self.context.get('request').auth.user.userprofile
        Group = self.context.get('Group', None)
        RePost = self.context.get('RePost', None)
        WhoCanComment = validated_data.get('WhoCanComment')
        ByMod = False
        Sensitive = validated_data.get('Sensitive', False)
        Public = validated_data.get('Public')
        ParentPost = self.context.get('ParentPost', None)
        ReplyingTo = self.context.get('ReplyingTo', None)
        PostBodyData = self.context.get('PostBody')
        images_data = self.context.get('request').FILES
        Link = self.context.get('Link')
        PollData = validated_data.pop('Poll')

        if ParentPost:
            Public = ParentPost.Public
            WhoCanComment = None
            PostBodyData = None

        if Group:
            try:
                GroupMembers.objects.get(User = PostedBy, Group = Group, Status = 2)
                ByMod = True
            except exceptions.ObjectDoesNotExist:
                ByMod = False
            if ByMod:
                pass
            else:
                if Group.AllowTextPosts:
                    pass
                else:
                    PostBodyData = None

                if Group.AllowImagePosts:
                    pass
                else:
                    images_data = None

                if Group.AllowLinkPosts:
                    pass
                else:
                    Link = None
                if Group.AllowPollPosts:
                    pass
                else:
                    PollData = None



            if Group.PostsAreNSFW:
                Sensitive = True
            else:
                pass
        else:
            pass

        if Public == False:
            if WhoCanComment == 2:
                WhoCanComment = FOLLOWERS
            else:
                pass

        Post = Posts.objects.create(
                                    Title=Title,
                                    PostedBy= PostedBy,
                                    Public = Public,
                                    WhoCanComment = WhoCanComment,
                                    Group = Group,
                                    ByMod= ByMod,
                                    Sensitive = Sensitive,
                                    RePost = RePost,
                                    ParentPost = ParentPost,
                                    ReplyingTo = ReplyingTo

        )
       ##print(PostBodyData)

        if PostBodyData:
           ##print('PENISNUTSACKS')
            postbodyserializer = PostBodyCRUD(data={'PostBody': PostBodyData}, many=False)
            if postbodyserializer.is_valid():
               ##print('PENISBALLSACKS')
                postbodyserializer.save(Post=Post)
        poll_serializer = PollCrud(data = PollData, many = True)
        if poll_serializer.is_valid():
            poll_serializer.save(Post = Post)

        if Link:
           ##print(Link)
            LinkSerializer = PostLinkSerializer(data={'Link':Link}, many = False)
            if LinkSerializer.is_valid():
                LinkSerializer.save(Post = Post)


        for image_data in images_data.values():
           ##print(images_data)
            serializer = ImageCrud(data={'Image':image_data, 'Post':Post.id})
            if serializer.is_valid():
                serializer.save(Post = Post)
               ##print('success')
        return Post

class GroupCRUD(serializers.ModelSerializer):
    class Meta:
        model = Groups
        fields = ['Name', 'Image', 'Banner', 'Description', 'AnyOneCanJoin', 'PostsArePublic', 'AllowTextPosts', 'AllowImagePosts', 'AllowVideoPosts', 'AllowLinkPosts', 'AllowPollPosts', 'AllowRePosts', 'Language']

class CollectionCRUD(serializers.ModelSerializer):
    class Meta:
        model = Collections
        fields = ['Name', 'Image', 'Description', 'Show', 'Banner']

class CommentCRUDPoll(serializers.ModelSerializer):
    Poll = PollCrud(many=True, allow_null=True)
    class Meta:
        model = Posts
        fields = ['Title', 'Poll']

    def create(self, validated_data):
        images_data = self.context.get('request').FILES
        ParentPost = self.context.get('ParentPost')
        ReplyingTo = self.context.get('ReplyingTo')

        Post = Posts.objects.create(Title=validated_data.get('Title'),
                                    PostedBy=self.context.get('request').auth.user.userprofile, ParentPost = ParentPost, ReplyingTo = ReplyingTo, ByMod=self.context.get('by_mod', False), Group=self.context.get('Group', None))
       ##print(ParentPost.id)
        PollData = validated_data.pop('Poll')
       ##print(PollData)
        poll_serializer = PollCrud(data=PollData, many=True)
        if poll_serializer.is_valid():
            poll_serializer.save(Post=Post)

        Link = self.context.get('Link')
        if Link:
           ##print(Link)
            LinkSerializer = PostLinkSerializer(data={'Link': Link}, many=False)
            if LinkSerializer.is_valid():
                LinkSerializer.save(Post=Post)
        return Post




class CommentCRUD(serializers.ModelSerializer):
    class Meta:
        model = Posts
        fields = ['Title']

    def create(self, validated_data):
        images_data = self.context.get('request').FILES
        ParentPost = self.context.get('ParentPost')
        ReplyingTo = self.context.get('ReplyingTo')

        Post = Posts.objects.create(Title=validated_data.get('Title'),
                                    PostedBy=self.context.get('request').auth.user.userprofile, ParentPost = ParentPost, ReplyingTo = ReplyingTo, ByMod=self.context.get('by_mod', False), Group=self.context.get('Group', None))
       ##print(ParentPost.id)

        Link = self.context.get('Link')
        if Link:
           ##print(Link)
            LinkSerializer = PostLinkSerializer(data={'Link': Link}, many=False)
            if LinkSerializer.is_valid():
                LinkSerializer.save(Post=Post)

        for image_data in images_data.values():
           ##print(images_data)
            serializer = ImageCrud(data={'Image':image_data, 'Post':Post.id})
            if serializer.is_valid():
                serializer.save(Post = Post)
               ##print('success')
        return Post
class NotificationPostSerializer(serializers.ModelSerializer):
    PostedBy = PostedBySerializer(many=False, read_only=True)
    ParentPost = ParentPostSerializer(many=False, read_only=True)
    class Meta:
        model = Posts
        fields = ['Title', 'id', 'PostedBy', 'ParentPost']
class VideoSerializerCRUD(serializers.ModelSerializer):
    class Meta:
        model = Videos
        fields = ['video']

class PostCRUDVideo(serializers.ModelSerializer):
    class Meta:
        model = Posts
        fields = ['Title', 'Public', 'WhoCanComment', 'Sensitive']

    def create(self, validated_data):
        images_data = self.context.get('request').FILES
       ##print('AAA')

        Title = validated_data.pop('Title')
        PostedBy = self.context.get('request').auth.user.userprofile
        Group = self.context.get('Group', None)
        WhoCanComment = validated_data.get('WhoCanComment')
        ByMod = self.context.get('by_mod', False)
        Sensitive = validated_data.get('Sensitive', False)
        Public = validated_data.get('Public')
        RePost = self.context.get('RePost', None)
        ParentPost = self.context.get('ParentPost', None)
        ReplyingTo = self.context.get('ReplyingTo', None)
        PostBodyData = self.context.get('PostBody')
        Link = self.context.get('Link')
        if ParentPost:
            Public = ParentPost.Public
            WhoCanComment = None
            PostBodyData = None

        if Group:
            try:
                GroupMembers.objects.get(User=PostedBy, Group=Group, Status=2)
                ByMod = True
            except exceptions.ObjectDoesNotExist:
                ByMod = False
            if ByMod:
                pass
            else:
                if Group.AllowTextPosts:
                    pass
                else:
                    PostBodyData = None

                if Group.AllowVideoPosts:
                    pass
                else:
                    images_data = None

                if Group.AllowLinkPosts:
                    pass
                else:
                    Link = None
                if Group.AllowPollPosts:
                    pass
                else:
                    PollData = None
            
            if Group.PostsAreNSFW:
                Sensitive = True
            else:
                pass


        if Public == False:
            if WhoCanComment == 2:
                WhoCanComment = FOLLOWERS
            else:
                pass
        Post = Posts.objects.create(
            Title=Title,
            PostedBy=PostedBy,
            Public=Public,
            WhoCanComment=WhoCanComment,
            Group=Group,
            ByMod=ByMod,
            Sensitive=Sensitive,
            RePost = RePost,
            ParentPost = ParentPost,
            ReplyingTo = ReplyingTo

        )
        PostBodyData = self.context.get('PostBody')

       ##print(images_data)
    
        if Link:
           ##print(Link)
            LinkSerializer = PostLinkSerializer(data={'Link': Link}, many=False)
            if LinkSerializer.is_valid():
                LinkSerializer.save(Post=Post)
        PostBodyData = self.context.get('PostBody')
       ##print(PostBodyData)
        if PostBodyData:
           ##print('PENISNUTSACKS')
            postbodyserializer = PostBodyCRUD(data={'PostBody': PostBodyData}, many=False)
            if postbodyserializer.is_valid():
               ##print('PENISBALLSACKS')
                postbodyserializer.save(Post=Post)

        for image_data in images_data.values():
            serializer = VideoSerializerCRUD(data={'video':image_data, 'Post':Post.id})
            if serializer.is_valid():
                serializer.save(Post = Post)
               ##print('success')
                return Post


class NotificationSerialzier(serializers.ModelSerializer):
    Post = NotificationPostSerializer(many = False, read_only = True)
    From = UserProfileSerializer(many = False, read_only = True)
    Group = MiniGroupSerializer(many=False, read_only=True)
    class Meta:
        model = Notifications
        fields = ['Post', 'From', 'Type', 'Group']

class CommentSerializer(serializers.ModelSerializer):
    PostedByName = serializers.ReadOnlyField(source='PostedBy.Name')
    PostedByUserName = serializers.ReadOnlyField(source='PostedBy.user.username')
    ParentPost = ParentPostSerializer(many=False, read_only=True)
    Liked = serializers.SerializerMethodField('_user')
    PostedByPicture = serializers.ReadOnlyField(source='PostedBy.ProfilePicture.url')
    ReplyingToName = serializers.ReadOnlyField(source='ReplyingTo.PostedBy.user.username')
    # Use this method for the custom field
    def _user(self, obj):
        request = self.context.get('request', None)
        if request:
            CurrentUser = request.auth.user
            try:
                PostLikes.objects.get(Post = obj.id, User = CurrentUser.userprofile)
                return True
            except exceptions.ObjectDoesNotExist:
                return False



    class Meta:
        model = Posts
        fields = ['PostedByName', 'PostedByUserName', 'Title', 'id', 'ParentPost', 'id', 'CommentCount', 'Liked', 'Vote', 'PostedByPicture', 'ReplyingToName', 'ReplyingTo']
        read_only_fields = fields


class UserProfileCRUD(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['Name', 'Location','Bio', 'ProfilePicture', 'RequirePermissionToFollow', 'ProfilePicture', 'BirthDay', 'Location', 'Link', 'Banner']

class GroupSerializer(serializers.ModelSerializer):

    Membership = serializers.SerializerMethodField('_membership')
    def _membership(self, obj):
        request = self.context.get('request', None)
        if request:
            try:
                GroupMembership = GroupMembers.objects.get(User = request.auth.user.userprofile, Group = obj.id)
                return GroupMembership.Status
            except exceptions.ObjectDoesNotExist:
                return None

    class Meta:
        model = Groups
        fields = ['Name', 'Image', 'Description', 'PostsArePublic', 'Membership', 'Banner', 'MemberCount', 'PostsAreNSFW', 'AnyOneCanJoin', 'PostCount', 'AllowTextPosts', 'AllowImagePosts', 'AllowVideoPosts', 'AllowLinkPosts', 'AllowPollPosts', 'AllowRePosts']



class GroupEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Groups
        fields = ['Image', 'Banner', 'Description', 'AnyOneCanJoin', 'PostsArePublic', 'AllowTextPosts', 'AllowImagePosts', 'AllowVideoPosts', 'AllowLinkPosts', 'AllowPollPosts', 'AllowRePosts']


class SendGroupJoinSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupMembers
        exclude = ['Group', 'User', 'Status']

class AcceptGroupJoinSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupMembers
        fields = ['Status']

class KickUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupMembers
        exclude = ['Group', 'User', 'Status']


class MyGroupStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupMembers
        fields = ['Status']

class SendFollowRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Following

        exclude = ['Follower', 'GettingFollowed', 'Status']

class AcceptFollowRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Following

        exclude = ['Follower', 'GettingFollowed']

class FollowerSerializer(serializers.ModelSerializer):
    UserName = serializers.ReadOnlyField(source='Follower.user.username')
    Name = serializers.ReadOnlyField(source='Follower.Name')
    ProfilePicture = serializers.ReadOnlyField(source='Follower.ProfilePicture.url')

    class Meta:
        model = Following
        fields = ['UserName', 'Name', 'Status', 'ProfilePicture']

class FollowingSerializer(serializers.ModelSerializer):
    UserName = serializers.ReadOnlyField(source='GettingFollowed.user.username')
    Name = serializers.ReadOnlyField(source='GettingFollowed.Name')
    ProfilePicture = serializers.ReadOnlyField(source='GettingFollowed.ProfilePicture.url')
    class Meta:
        model = Following
        fields = ['UserName', 'Name', 'Status', 'ProfilePicture', 'Notify']

class LikeSerialzier(serializers.ModelSerializer):
    class Meta:
        model = PostLikes
        exclude = ['User', 'Post', 'id']





class RegisterationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = super().create(validated_data)
        user.set_password(password)
        user.save()
        return user

class PartialUserSerializer(serializers.ModelSerializer):
    UserName = serializers.ReadOnlyField(source='user.username')
    class Meta:
        model = UserProfile
        fields = ['UserName', 'Name', 'ProfilePicture', 'UserType']

class CreateGroup(serializers.ModelSerializer):
    class Meta:
        model = Groups
        fields = ['GroupName', 'Description', 'AnyOneCanView']

class TagSerializer(serializers.ModelSerializer):
    PostedToday = serializers.SerializerMethodField('_PostedToday')
    def _PostedToday(self, obj):
        timethreshhold = datetime.now(timezone.utc)-timedelta(24)
        Q1 = Tag.objects.filter(Tag = obj.id)
        return Posts.objects.filter(Tags__in = Q1, PostedOn__gt=timethreshhold).count()
    class Meta:
        model = Tags
        fields = '__all__'


class ChatSerializer(serializers.ModelSerializer):
    Me = serializers.SerializerMethodField('_user')

    def _user(self, obj):
        request = self.context.get('request', None)
        if request:
            CurrentUser = request.auth.user
            if obj.From == CurrentUser.userprofile:
                return True
            else:
                return False
    class Meta:
        model = Chat
        fields = ['Text', 'Me', 'Read']

class ChatCRUD(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = ['Text']

class ChatSummary(serializers.ModelSerializer):
    Me = serializers.SerializerMethodField('_user')
    Name = serializers.SerializerMethodField('_OtherDude')
    UserName = serializers.SerializerMethodField('_OtherDudeUserName')
    ProfilePicture = serializers.SerializerMethodField('_OtherDudeProfilePic')
    Text = serializers.SerializerMethodField('_Text')
    Read = serializers.SerializerMethodField('_Read')

    def _user(self, obj):
        request = self.context.get('request', None)
        CurrentUser = request.auth.user
        if request:
            Message = Chat.objects.filter(Chats = obj.id).order_by('-id')[0]
            if Message.From == CurrentUser.userprofile:
                return True
            else:
                return False
    def _OtherDude(self, obj):
        request = self.context.get('request', None)
        CurrentUser = request.auth.user
        if request:
            Message = Chat.objects.filter(Chats=obj.id).order_by('-id')[0]
            if CurrentUser.userprofile == Message.From:
                return Message.To.Name
            else:
                return Message.From.Name
    def _OtherDudeUserName(self, obj):
        request = self.context.get('request', None)
        CurrentUser = request.auth.user
        if request:
            Message = Chat.objects.filter(Chats=obj.id).order_by('-id')[0]
            if CurrentUser.userprofile == Message.From:
                return Message.To.user.username
            else:
                return Message.From.user.username
    def _OtherDudeProfilePic(self, obj):
        request = self.context.get('request', None)
        CurrentUser = request.auth.user
        if request:
            Message = Chat.objects.filter(Chats=obj.id).order_by('-id')[0]
            if CurrentUser.userprofile == Message.From:
                return Message.To.ProfilePicture.url
            else:
                return Message.From.ProfilePicture.url
    def _Text(self, obj):
        Message = Chat.objects.filter(Chats=obj.id).order_by('-id')[0]
        return Message.Text
    def _Read(self, obj):
        Message = Chat.objects.filter(Chats=obj.id).order_by('-id')[0]
        return Message.Read








    class Meta:
        model = Chats
        fields = ['Me', 'Name', 'UserName', 'Text', 'ProfilePicture', 'Read']


class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Votes
        fields = ['Poll']

class CollectionSerializer(serializers.ModelSerializer):
    Following = serializers.SerializerMethodField('_following')
    CreatedBy = PostedBySerializer(many = False, read_only = True)
    Me = serializers.SerializerMethodField('_me')
    def _me(self, obj):
        request = self.context.get('request', None)
        if request:
            if request.auth.user.userprofile == obj.CreatedBy:
                return True
            else:
                return False
        else:
            return None
    def _following(self, obj):
        request = self.context.get('request', None)
        if request:
            try:
                following = FollowCollection.objects.get(Collection = obj, User = request.auth.user.userprofile)
                return True
            except exceptions.ObjectDoesNotExist:
                return False
        else:
            return None
    class Meta:
        model = Collections
        fields = '__all__'

class CollectionSerializerAdd(serializers.ModelSerializer):
    Status = serializers.SerializerMethodField('_status')
    CreatedBy = PostedBySerializer(many = False, read_only = True)
    def _status(self, obj):
        request = self.context.get('request', None)
        UserToView = self.context.get('UserToView', None)
        if request:
            try:
                following = CollectionPosts.objects.get(Collection = obj, User = UserToView)
                return True
            except exceptions.ObjectDoesNotExist:
                return False
        else:
            return None
    class Meta:
        model = Collections
        fields = '__all__'

class ModToolsUserSerializer(serializers.ModelSerializer):
    UserName = serializers.ReadOnlyField(source='user.username')
    NotificationsEnabled = serializers.SerializerMethodField('_notify')
    Following = serializers.SerializerMethodField('_following')
    Joined = serializers.SerializerMethodField('_joined')
    Status = serializers.SerializerMethodField('_status')
    def _joined(self, obj):
        return datetime.now(timezone.utc) - obj.user.date_joined

    def _following(self, obj):
        request = self.context.get('request', None)
        if request:
            try:
                Users = Following.objects.get(GettingFollowed = obj, Follower = request.auth.user.userprofile)
                return Users.Status
            except exceptions.ObjectDoesNotExist:
                return None
        else:
            return None
    def _notify(self, obj):
        request = self.context.get('request', None)
        if request:
            try:
                Users = Following.objects.get(GettingFollowed = obj.id, Follower = request.auth.user.userprofile)
                NotifyPosts.objects.get(Users = Users)
                return True
            except exceptions.ObjectDoesNotExist:
                return False
        else:
            return None



    def _status(self, obj):
        Group = self.context.get('Group', None)
        try:
            Stat = GroupMembers.objects.get(User=obj.id, Group=Group)
            return Stat.Status
        except exceptions.ObjectDoesNotExist:
            return None

    class Meta:
        model = UserProfile
        fields = ['UserName', 'Name', 'Location', 'ProfilePicture', 'Bio', 'RequirePermissionToFollow', 'Followers', 'Banner', 'NotificationsEnabled','Following', 'Joined', 'PostCount', 'Link', 'BirthDay', 'Status', 'FollowingCount', 'UserType', 'Points']
        read_only_fields = fields


class ResetPasswordSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['password']

class ResetEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email']

class ResetPhoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email']

class ChangeUserNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email']

class NotificationTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = FireBaseNotificationTokens
        fields = ['Token']

class PostUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Posts
        fields = ['Vote', 'CommentCount', 'id']