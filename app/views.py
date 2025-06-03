from django.db.models.fields.related import OneToOneField
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.translation import pgettext
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import *
from datetime import datetime, timedelta
from .models import *
from .exceptions import *
from django.core import exceptions
from rest_framework.exceptions import APIException
from rest_framework.generics import ListAPIView
from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, manager
from django.db.models import Count, F, Value
from django.db.models import Avg, Count, Min, Sum
from django.db.models import DateTimeField, ExpressionWrapper, F, IntegerField, DurationField
from django.utils.timezone import utc
from itertools import chain
from datetime import datetime, timezone
from django.utils.crypto import get_random_string
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
import random
import re
from django.contrib.postgres.search import SearchVector
import boto3
from .task import *
from django.db.models import Case, When


# Create your views here.


def LanguageCodes(code):
    if code == 'en':
        return en
    if code == 'hi':
        return hi
    if code == 'bn':
        return bn
    if code == 'mr':
        return mr
    if code == 'pa':
        return pa
    if code == 'te':
        return te
    if code == 'ta':
        return ta
    if code == 'kn':
        return kn
    if code == 'pa':
        return pa
    

@csrf_exempt
@api_view(["GET"])
def apiOverView(request):
    api_urls = {
        "Post Feed": "Posts",
        "View single post": "/Posts/<str:pk>",
        "Edit post with id pk": "/Posts/<str:pk>/Edit",
        "Delete post": "/Posts/<str:pk>/Delete",
        "Vote on post": "/Posts/<str:pk>/Vote",
        "View comments associated with post": "/Posts/<str:pk>/Comments",
        "Create comment to post": "/Posts/<str:pk>/CreateComment",
        "Delete comment with id pk": "Comment/<str:pk>/Delete",
        "Edit comment with id pk": "Comment/<str:pk>/Edit",
        "Get account details with username pk": "u/<str:pk>",
        "Get posts associated with account wuth username pk": "u/<str:pk>/Posts",
        "Edit account that is currently signed in": "EditMyProfile",
    }
    return Response(api_urls)


########################################################################################################################


@api_view(["POST"])
@csrf_exempt
def Register(request):

    data = {}
    username = request.data.get('username')
    ##print(username)
    try:
        User.objects.get(username__iexact= username)
        ##print('AAAAAAAAAAAAAAa')
        raise UserAlreadyExists
    except exceptions.ObjectDoesNotExist:
        pass
    email = request.data.pop('email')
    password = request.data.pop('password')
    if len(username) > 35:
        raise Invalid
    if '@' in username:
        raise Invalid
    if '!' in username:
        raise Invalid
    if '.' in username:
        raise Invalid
    if '+' in username:
        raise Invalid
    if re.match('[a-zA-Z0-9_-]', username):
        pass
    else:
        raise Invalid
    serializer = RegisterationSerializer(data={'username':username, 'email':email, 'password':password})

    if serializer.is_valid():
        account = serializer.save()
        data["response"] = "User created successfully"
        data["username"] = account.username
        data["email"] = account.email
        token = Token.objects.get(user=account).key
        data["token"] = token
        response = Response(data)
        response.set_cookie('authentication', token, samesite='strict', secure=True, expires=None)
        return response
    else:
        raise Invalid


@csrf_exempt
@api_view(['POST'])
def Auth_PhoneNumber(request):
    PhoneNumber = request.data.get('phone_number')

    try:
        UserPhoneNumberObject = UserPhoneNumber.objects.get(PhoneNumber = PhoneNumber)
        if UserPhoneNumberObject.user:
            New = False
        else:
            New = True
    except exceptions.ObjectDoesNotExist:
        UserPhoneNumberObject = UserPhoneNumber.objects.create(
            PhoneNumber = PhoneNumber,
            user = None
        )
        New = True

    OldOTPs = UserOTPToken.objects.filter(Phone = UserPhoneNumberObject)
    try:
        time_threshold = datetime.now(timezone.utc) - timedelta(seconds=20)
        OTPsSentInLast20Seconds = UserOTPToken.objects.get(Phone = UserPhoneNumberObject, Created__gt = time_threshold)
        raise Wait
    except exceptions.ObjectDoesNotExist:
        pass


    OldOTPs.delete()

    OTP = get_random_string(length=4, allowed_chars='1234567890')
    
    UserOTPToken.objects.create(
        Phone = UserPhoneNumberObject,
        Key = OTP,
        OTPType = AUTh
    )

    from . import sns
    sns.client.publish(
        PhoneNumber = PhoneNumber,
        Message = f'Your verification code is: {OTP}'
    )

    return Response(data={'New':New})


@csrf_exempt
@api_view(['POST'])
def Auth_Register_VerifyOTP(request):
    PhoneNumber = request.data.get('phone_number')
    UserName = request.data.get('username')
    Key = request.data.get('Key')

    try:
        UserPhoneNumberObject = UserPhoneNumber.objects.get(
            PhoneNumber = PhoneNumber,
            user = None
        )
    except exceptions.ObjectDoesNotExist:
        raise Unauthorised

    try:
        CurrentUserPhoneNumber = UserPhoneNumber.objects.get(PhoneNumber = PhoneNumber, user = None)
        time_threshold = datetime.now(timezone.utc) - timedelta(minutes=10)
        UserOTPObject = UserOTPToken.objects.get(
            Phone = UserPhoneNumberObject,
            Key = Key,
            OTPType = AUTh,
            Created__gt=time_threshold
        ).delete()
    except exceptions.ObjectDoesNotExist:
        try:
            CurrentUserPhoneNumber = UserPhoneNumber.objects.get(PhoneNumber = PhoneNumber, user = None)
            time_threshold = datetime.now(timezone.utc) - timedelta(minutes=10)
            UserOTPObject = UserOTPToken.objects.get(
                Phone = UserPhoneNumberObject,
                Key = Key,
                OTPType = AUTh,
                Created__lt=time_threshold
            ).delete()
            raise OTPTimeoUT
        except exceptions.ObjectDoesNotExist:
            raise Unauthorised
    
    CurrentUser = User.objects.create(username = UserName)      
    CurrentUserPhoneNumber.user = CurrentUser
    CurrentUserPhoneNumber.save()

    try:
        Key = Token.objects.get(user = CurrentUser).key
    except exceptions.ObjectDoesNotExist:
        Key = Token.objects.create(user=CurrentUser).key
        ##print(Key)
    return Response(data={'token':Key})

    



    
@api_view(['POST'])
def Auth_LogIn_VerifyOTP(request):
    PhoneNumber = request.data.get('phone_number')
    Key = request.data.get('Key')

    try:
        UserPhoneNumberObject = UserPhoneNumber.objects.get(
            PhoneNumber = PhoneNumber,
            user__isnull = False
        )
    except exceptions.ObjectDoesNotExist:
        raise Unauthorised

    try:
        time_threshold = datetime.now(timezone.utc) - timedelta(minutes=10)
        UserOTPObject = UserOTPToken.objects.get(
            Phone = UserPhoneNumberObject,
            Key = Key,
            OTPType = AUTh,
            Created__gt=time_threshold
        ).delete()
    except exceptions.ObjectDoesNotExist:
        try:
            time_threshold = datetime.now(timezone.utc) - timedelta(minutes=10)
            UserOTPObject = UserOTPToken.objects.get(
                Phone = UserPhoneNumberObject,
                Key = Key,
                OTPType = AUTh,
                Created__lt=time_threshold
            ).delete()
            raise OTPTimeoUT
        except exceptions.ObjectDoesNotExist:
            raise Unauthorised

    try:
        Key = Token.objects.get(user = UserPhoneNumberObject.user).key
    except exceptions.ObjectDoesNotExist:
        Key = Token.objects.create(user=UserPhoneNumberObject.user).key
        ##print(Key)
    return Response(data={'token':Key})

@api_view(['POST'])
@csrf_exempt
def LogIn(request):
    ##print('PENIS')
    ##print(request.data)
    UserName = request.data.pop('username')
    PassWord = request.data.pop('password')
    try:
        UserToView = User.objects.get(username__iexact= UserName)
    except exceptions.ObjectDoesNotExist:
        raise UserDoesNotExist
    if UserToView.check_password(PassWord) == True:
        try:
            Key = Token.objects.get(user = UserToView).key
        except exceptions.ObjectDoesNotExist:
            Key = Token.objects.create(user=UserToView).key
            ##print(Key)
        return Response(data={'token':Key})
    else:
        raise WrongPassword

@api_view(["POST"])
def LogOutOfAll(request):
    CurrentUser = request.auth.user
    NotificationTokens = FireBaseNotificationTokens.objects.filter(User = CurrentUser.userprofile)
    for NotificationToken in NotificationTokens:
        NotificationToken.delete()
    Key = Token.objects.get(user=CurrentUser).delete()
    raise Success


@api_view(['POST'])
def ResetPasswordNoAuth(request):
    UserName = request.data.get('username')
    Key = request.data.get('key')
    NewPassowrd = request.data.get('password')
    try:
        USerToView = User.objects.get(username__iexact=UserName)
    except exceptions.ObjectDoesNotExist:
        raise UserDoesNotExist
    try:
        time_threshold = datetime.now(timezone.utc) - timedelta(minutes=5)
        ##print('BoOGie')
        Token = Change_Password_Token.objects.get(User=USerToView, Key=Key, Created__gt=time_threshold)
    except exceptions.ObjectDoesNotExist:
        raise InvalidKey
    Change_Password_Token.objects.get(User = USerToView, Key = Key)
    USerToView.set_password(NewPassowrd)
    USerToView.save()
    raise Success

@csrf_exempt
@api_view(['POST'])
def ResetPasswordNoToken(request):
    UserName = request.data.get('username', None)
    if User:
        try:
            UserToView = User.objects.get(username__iexact= UserName)
        except exceptions.ObjectDoesNotExist:
            raise UserDoesNotExist
        try:
            time_threshold = datetime.now(timezone.utc) - timedelta(seconds=20)
            Token = Change_Password_Token.objects.get(User=UserToView, Created__gt=time_threshold)
            raise Unauthorised
        except exceptions.ObjectDoesNotExist:
            pass
        GenerateResetToken.delay(UserToView.id)
        email = UserToView.email
        email_domain = email.split('@')[1]
        email_name = email.split('@')[0][-2:]
        hidden_email = email_name + '@' + email_domain
        return Response(data={'email': hidden_email})


@api_view(['POST'])
def ChangeEmail(request):
    CurrentUser = request.auth.user
    ##print(request.data)
    NewEmail = request.data.pop('email')
    PassWord = request.data.pop('password')
    serializer = ResetEmailSerializer(data = request.data, instance = CurrentUser)
    if CurrentUser.check_password(PassWord) == True:
        if serializer.is_valid():
            serializer.save(email = NewEmail)
            raise Success
        else:
            raise Invalid
    else:
        raise Unauthorised

@api_view(['POST'])
def ChangeUserHandle(request):
    CurrentUser = request.auth.user
    ##print(request.data)
    Name = request.data.pop('username')
    PassWord = request.data.pop('password')
    try:
        User.objects.get(username__iexact= Name)
        raise UserAlreadyExists
    except exceptions.ObjectDoesNotExist:
        pass
    serializer = ChangeUserNameSerializer(data=request.data, instance=CurrentUser)
    if CurrentUser.check_password(PassWord) == True:
        try:
            time_threshold = datetime.now(timezone.utc) - timedelta(hours=720)
            LastHandleChange.objects.get(Time__gt = time_threshold)
            return Response(data={'detail':'wait'})
        except exceptions.ObjectDoesNotExist:
            if serializer.is_valid():
                serializer.save(username=Name)
                LastHandleChange.objects.create(User = CurrentUser)
                raise Success
            else:
                raise Invalid
    else:
        raise WrongPassword

@api_view(["DELETE"])
def DeleteAccount(request):
    CurrentUser = request.auth.user
    Key = task.DeleteUser.delay(CurrentUser.id)
    raise Success

@api_view(['GET', "POST"])
def Me(request):
    if request.method == 'GET':
        if request.auth == None:
            raise PleaseSignIn
        CurrentUser = request.auth.user
        serializer = MeUserProfileSerializer(CurrentUser.userprofile, many=False)
        return Response(serializer.data)
    if request.method == "POST":
        CurrentUser = request.auth.user
        ##print(request.data)
        serializer = UserProfileCRUD(
            instance=CurrentUser.userprofile, data=request.data
        )
        if serializer.is_valid():
            serializer.save()
            raise Success
        else:
            raise Invalid

@api_view(["GET", "POST"])
def ViewUserProfile(request, pk):
    try:
        UserToView = User.objects.get(username__iexact=pk)
    except exceptions.ObjectDoesNotExist:
        raise UserDoesNotExist
    if request.method == "GET":
        if request.auth == None:
            serializer = UserProfileSerializer(UserToView.userprofile, many=False)
            return Response(serializer.data)
        CurrentUser = request.auth.user
        try:
            Following.objects.get(Follower=UserToView.userprofile, GettingFollowed=CurrentUser.userprofile, Status=2)
            raise Blocked
        except exceptions.ObjectDoesNotExist:
            pass
        serializer = UserProfileSerializer(UserToView.userprofile, many=False, context={'request':request})
        return Response(serializer.data)



########################################################################################################################



@api_view(['GET'])
def SearchUser(request):
    if request.auth == None:
        SearchTerm = request.GET.get('search')
        Users = UserProfile.objects.filter(Q(Name__contains=SearchTerm) | Q(user__username__contains=SearchTerm))[:25]
        serializer = UserProfileSerializer(Users, many=True)
        return Response(serializer.data)
    SearchTerm = request.GET.get('search')
    Users = UserProfile.objects.filter(Q(Name__contains = SearchTerm)|Q(user__username__contains = SearchTerm))[:25]
    serializer = UserProfileSerializer(Users, many = True, context={'request':request})
    return Response(serializer.data)

@api_view(['GET'])
def SearchGroup(request):
    if request.auth == None:
        SearchTerm = request.GET.get('search')
        Group = Groups.objects.filter(Q(Name__contains=SearchTerm))[:25]
        serializer = GroupSerializer(Group, many=True)
        return Response(serializer.data)

    SearchTerm = request.GET.get('search')
    Group = Groups.objects.filter(Q(Name__contains=SearchTerm))[:25]
    serializer = GroupSerializer(Group, many=True, context={'request': request})
    return Response(serializer.data)

class SearchCollection(ListAPIView):
    queryset = Collections.objects.all()
    serializer_class = CollectionSerializer
    filter_backends = (SearchFilter, OrderingFilter)
    search_fields = ('Name', 'Description')

@api_view(['GET'])
def SearchCollections(request):
    Search = request.GET.get('search')
    Collection = Collections.objects.filter(Name__contains=Search)
    serializer = CollectionSerializer(Collection, many = True)
    return Response(serializer.data)




########################################################################################################################
@api_view(['GET', "POST"]) 
def ViewGroupPosts(request, pk):
    try:
        Group = Groups.objects.get(Name=pk)
    except exceptions.ObjectDoesNotExist:
        return UserDoesNotExist

    if request.method == "GET":
        if request.GET.get('order') == 'best':
            OrderBy = '-Vote'
        elif request.GET.get('order') == 'new':
            OrderBy = '-id'
        if request.auth == None:
            if Group.PostsArePublic:
                limit = int(request.GET.get('limit', 32))
                offset = int(request.GET.get('offset', 0))
                if limit > 64:
                    limit = 64
                Post = Posts.objects.filter(Group=Group, ParentPost=None, Group__PostsArePublic=True).order_by(
                    '-id').prefetch_related('PostImages', 'Poll', 'ParentPost', 'RePost', 'ParentPost', 'ReplyingTo',
                                            'ParentPost', 'PostImages', 'Group', 'Likes').order_by(OrderBy).select_related('Video',
                                                                                                         'PostBody',
                                                                                                         'PostLink',
                                                                                                         'OverWatchFinalOutcome')[
                       offset:offset + limit]
                serializer = PostSerializer(Post, many=True)
                return Response(serializer.data)
            else:
                raise PleaseSignIn
        CurrentUser = request.auth.user
        limit = int(request.GET.get('limit', 32))
        offset = int(request.GET.get('offset', 0))
        if limit>64:
            limit=64
        Post = Posts.objects.filter(Group = Group, ParentPost = None).order_by('-id').prefetch_related('PostImages', 'Poll', 'ParentPost', 'RePost', 'ParentPost', 'ReplyingTo', 'ParentPost', 'PostImages', 'Group', 'Likes').select_related('Video', 'PostBody', 'PostLink', 'OverWatchFinalOutcome').order_by(OrderBy)[offset:offset+limit]
        ##print(Post.query)
        serializer = PostSerializer(Post, context={'request': request}, many=True)
        try:
            Status = GroupMembers.objects.get(User=CurrentUser.userprofile, Group= Group)
            if Status.Status == 1:
                return Response(serializer.data)
            if Status.Status == 2:
                ##print('PENIS')
                serializer = PostSerializer(Post, context={'request': request, 'auth': True}, many=True)
                return Response(serializer.data)
            else:
                raise ServiceUnavailable
        except exceptions.ObjectDoesNotExist:
            if Group.PostsArePublic:
                return Response(serializer.data)
            else:
                raise ServiceUnavailable


    if request.method == 'POST':

        CurrentUser = request.auth.user
        Title = request.data.get('Title')
        try:
            time_threshold = datetime.now(timezone.utc) - timedelta(minutes=5)
            Posts.objects.get(PostedBy=CurrentUser.userprofile, Title__iexact=Title, PostedOn__gt=time_threshold)
            raise Spam
        except exceptions.ObjectDoesNotExist:
            pass
        try:
            Status = GroupMembers.objects.get(User = CurrentUser.userprofile, Group = Group)
            if Status.Status == 1:
                if request.data.get('Poll'):
                    #print('AYY')
                    serializer = PostCRUD(data=request.data, context={'request': request, 'Group': Group, 'PostBody':request.data.pop('PostBody'),  'Link':request.data.get('Link', None)})
                    if serializer.is_valid():
                        serializer.save(
                        )
                        raise Success
                    else:
                        raise Invalid
                if request.data.get('Video'):
                    serializer = PostCRUDVideo(data=request.data, context={'request': request, 'Group': Group, 'PostBody':request.data.pop('PostBody'),  'Link':request.data.get('Link', None)})
                    #print('GAYY')
                    #print(request.data)
                    if serializer.is_valid():
                        serializer.save(
                        )
                        raise Success
                    else:
                        raise Invalid
                else:
                    serializer = PostCRUD_Image(data=request.data, context={'request': request,'Group': Group, 'PostBody':request.data.pop('PostBody'),  'Link':request.data.get('Link', None)})
                    #print('NAYY')
                    #print(request.data)
                    if serializer.is_valid():
                        serializer.save(
                            PostedBy=CurrentUser.userprofile,
                        )
                        raise Success
                    else:
                        raise Invalid
            elif Status.Status == 2:
                if request.data.get('Poll'):
                    serializer = PostCRUD(data=request.data, context={'request': request, 'Group': Group, 'by_mod':True, 'PostBody':request.data.pop('PostBody'),  'Link':request.data.get('Link', None)})
                    if serializer.is_valid():
                        serializer.save(
                        )
                        raise Success
                    else:
                        raise Invalid
                if request.data.get('Video'):
                    serializer = PostCRUDVideo(data=request.data, context={'request': request, 'Group': Group, 'by_mod':True, 'PostBody':request.data.pop('PostBody'),  'Link':request.data.get('Link', None)})
                    #print(request.data)
                    if serializer.is_valid():
                        serializer.save(
                        )
                        raise Success
                    else:
                        raise Invalid
                else:
                    serializer = PostCRUD_Image(data=request.data, context={'request': request,'Group': Group, 'by_mod':True, 'PostBody':request.data.pop('PostBody'),  'Link':request.data.get('Link', None)})
                    #print(request.data)
                    if serializer.is_valid():
                        serializer.save(
                            PostedBy=CurrentUser.userprofile,
                        )
                        raise Success
                    else:
                        raise Invalid
            else:
                raise Blocked
        except exceptions.ObjectDoesNotExist:
            raise Unauthorised

@api_view(['GET'])
def GetGroupMods(request, pk):
    try:
        Group = Groups.objects.get(Name=pk)
    except exceptions.ObjectDoesNotExist:
        return UserDoesNotExist
    ModsList = GroupMembers.objects.filter(Group = Group, Status = MOD).values_list('User_id', flat=True)
    Mods = UserProfile.objects.filter(id__in = ModsList)
    serializer = UserProfileSerializer(Mods, many = True, context={'request':request})
    return Response(serializer.data)

@api_view(['POST'])
def CreateCommunity(request):
    #print(request.data)
    CurrentUser = request.auth.user
    serializer = GroupCRUD(data = request.data)
    ##print(request.data)
    Name = request.data.get('Name')
    NameRegex = '^[\w.@+-]+\Z'
    if re.match(NameRegex, Name):
        pass
    else:
        raise Invalid
    if serializer.is_valid():
        Group = serializer.save()
        GroupMembers.objects.create(
            User = CurrentUser.userprofile,
            Group = Group,
            Status = 2
        )
        raise Success
    else:
        raise Invalid

@api_view(['POST'])
def CreateCollection(request):
    CurrentUser = request.auth.user
    serializer = CollectionCRUD(data = request.data)
    Name = request.data.get('Name')
    NameRegex = '^[\w.@+-]+\Z'
    if re.match(NameRegex, Name):
        pass
    else:
        raise Invalid
    ##print(request.data)
    if serializer.is_valid():
        Group = serializer.save(CreatedBy = CurrentUser.userprofile)
        raise Success
    else:
        raise Invalid

@api_view(["GET", "POST"])
def ViewPosts(request, pk):
    try:
        UserToView = User.objects.get(username__iexact=pk)
    except exceptions.ObjectDoesNotExist:
        raise UserDoesNotExist
    if request.method == "GET":
        limit = int(request.GET.get('limit', 0))
        offset = int(request.GET.get('offset', 32))
        if request.GET.get('order') == 'best':
            OrderBy = '-Vote'
        elif request.GET.get('order') == 'new':
            OrderBy = '-id'
        if limit > 64:
            limit = 64
        if request.auth == None:
            Post = Posts.objects.filter(Q(PostedBy = UserToView.userprofile, Public = True, ParentPost = None, Group = None)|Q(PostedBy = UserToView.userprofile, Group__PostsArePublic=True, ParentPost=None)|Q(PostedBy = UserToView.userprofile, ParentPost__Public = True, ParentPost__Group = None)|Q(PostedBy = UserToView.userprofile, ParentPost__Public = True, ParentPost__Group__PostsArePublic = True)).order_by('-id').prefetch_related('PostImages',
                                                                                                          'Poll',
                                                                                                          'ParentPost',
                                                                                                          'RePost',
                                                                                                          'ParentPost',
                                                                                                          'ReplyingTo',
                                                                                                          'ParentPost',
                                                                                                          'PostImages',
                                                                                                          'Group',
                                                                                                          'Likes').select_related(
                'Video', 'PostBody', 'PostLink', 'OverWatchFinalOutcome').order_by(OrderBy)[offset:offset + limit]
            serializer = PostSerializer(Post, many=True)
            return Response(serializer.data)

        CurrentUser = request.auth.user
        try:
            Following.objects.get(GettingFollowed=CurrentUser.userprofile, Follower=UserToView.userprofile, Status=2)
            raise Blocked
        except exceptions.ObjectDoesNotExist:
            pass
        limit = int(request.GET.get('limit', 0))
        offset = int(request.GET.get('offset', 32))
        if UserToView == request.auth.user:
            Post = Posts.objects.filter(PostedBy=UserToView.userprofile).order_by('-id').prefetch_related('PostImages', 'Poll', 'ParentPost', 'RePost', 'ParentPost', 'ReplyingTo', 'ParentPost', 'PostImages', 'Group', 'Likes').select_related('Video', 'PostBody', 'PostLink', 'OverWatchFinalOutcome').order_by(OrderBy)[offset:offset+limit]
            serializer = PostSerializer(Post, context={'request': request}, many=True)
            return Response(serializer.data)
        else:

            try:
                Status = Following.objects.get(Follower = CurrentUser.userprofile, GettingFollowed = UserToView.userprofile)
                if Status.Status == 0:
                    Post = Posts.objects.filter(Q(PostedBy = UserToView.userprofile, Public = True, ParentPost = None, Group = None)|Q(PostedBy = UserToView.userprofile, Group__PostsArePublic=True, ParentPost=None)|Q(PostedBy = UserToView.userprofile, ParentPost__Public = True, ParentPost__Group = None)|Q(PostedBy = UserToView.userprofile, ParentPost__Group__PostsArePublic = True)).order_by('-id').prefetch_related('PostImages', 'Poll', 'ParentPost', 'RePost', 'ParentPost', 'ReplyingTo', 'ParentPost', 'PostImages', 'Group', 'Likes').order_by(OrderBy)[offset:offset+limit]
                    serializer = PostSerializer(Post, context={'request': request}, many=True)
                    ##print(Post.query)
                    return Response(serializer.data)
                elif Status.Status == 1:
                    Post = Posts.objects.filter(Q(PostedBy = UserToView.userprofile, ParentPost = None, Group = None)|Q(PostedBy = UserToView.userprofile, Group__PostsArePublic=True, ParentPost=None)|Q(PostedBy = UserToView.userprofile, ParentPost__Public = True, ParentPost__Group = None)|Q(PostedBy = UserToView.userprofile, ParentPost__Group__PostsArePublic = True)).order_by('-id').prefetch_related('PostImages', 'Poll', 'ParentPost', 'RePost', 'ParentPost', 'ReplyingTo', 'ParentPost', 'PostImages', 'Group', 'Likes').order_by(OrderBy)[offset:offset+limit]
                    serializer = PostSerializer(Post, context={'request': request}, many=True)
                    ##print(Post.query)
                    return Response(serializer.data)
                elif Status.Status == 2:
                    raise Block
            except exceptions.ObjectDoesNotExist:
                Post = Posts.objects.filter(Q(PostedBy = UserToView.userprofile, Public = True, ParentPost = None, Group = None)|Q(PostedBy = UserToView.userprofile, Group__PostsArePublic=True, ParentPost=None)|Q(PostedBy = UserToView.userprofile, ParentPost__Public = True, ParentPost__Group = None)|Q(PostedBy = UserToView.userprofile, ParentPost__Public = True, ParentPost__Group__PostsArePublic = True)).order_by('-id').prefetch_related('PostImages', 'Poll', 'ParentPost', 'RePost', 'ParentPost', 'ReplyingTo', 'ParentPost', 'PostImages', 'Group', 'Likes').order_by(OrderBy)[offset:offset+limit]
                serializer = PostSerializer(Post, context={'request': request}, many=True)
                return Response(serializer.data)

    if request.method == "POST":
        CurrentUser = request.auth.user
        if CurrentUser == UserToView:
            if request.data.get('Poll'):
                ##print('AYY')
                serializer = PostCRUD(data=request.data, context={'request': request})
                if serializer.is_valid():
                    serializer.save(
                    )
                    raise Success
                else:
                    raise Invalid
            if request.data.get('Video'):
                serializer = PostCRUDVideo(data=request.data, context={'request': request})
                ##print('GAYY')
                ##print(request.data)
                if serializer.is_valid():
                    serializer.save(
                    )
                    raise Success
                else:
                    raise Invalid
            else:
                serializer = PostCRUD_Image(data=request.data, context={'request': request})
                ##print('NAYY')
                ##print(request.data)
                if serializer.is_valid():
                    serializer.save(
                        PostedBy=CurrentUser.userprofile,
                    )
                    raise Success
                else:
                    raise Invalid

@api_view(['GET'])
def GetUserCommunityPosts(request, pk):
    try:
        UserToView = User.objects.get(username__iexact=pk)
    except exceptions.ObjectDoesNotExist:
        raise UserDoesNotExist


    limit = int(request.GET.get('limit', 0))
    offset = int(request.GET.get('offset', 32))
    Post = Posts.objects.filter(PostedBy=UserToView.userprofile, Group__isnull=False, Group__PostsArePublic=True, ParentPost=None).order_by('-id').prefetch_related('PostImages', 'Poll', 'ParentPost', 'RePost', 'ParentPost', 'ReplyingTo', 'ParentPost', 'PostImages', 'Group', 'Likes').select_related('Video', 'PostBody', 'PostLink', 'OverWatchFinalOutcome')[offset:limit+offset]
    serializer = PostSerializer(Post, context={'request': request}, many=True)

    if request.auth == None:
        serializer = PostSerializer(Post, many=True)
        return Response(serializer.data)
    CurrentUser = request.auth.user
    try:
        Following.objects.get(GettingFollowed=CurrentUser.userprofile, Follower=UserToView.userprofile, Status=2)
        raise Blocked
    except exceptions.ObjectDoesNotExist:
        pass
    if UserToView == request.auth.user:
        return Response(serializer.data)
    else:
        try:
            CurrentUser = request.auth.user
            try:
                Following.objects.get(Follower=CurrentUser.userprofile, GettingFollowed=UserToView.userprofile)
                return Response(serializer.data)
            except exceptions.ObjectDoesNotExist:
                return Response(serializer.data)
        except exceptions.ObjectDoesNotExist:
            return Response(serializer.data)


@api_view(['GET'])
def GetUserReplies(request, pk):
    try:
        UserToView = User.objects.get(username__iexact=pk)
    except exceptions.ObjectDoesNotExist:
        raise UserDoesNotExist
    limit = int(request.GET.get('limit', 0))
    offset = int(request.GET.get('offset', 32))
    Post = Posts.objects.filter(Q(PostedBy=UserToView.userprofile, ParentPost__isnull=False, Group = None)|Q(PostedBy=UserToView.userprofile, Group__PostsArePublic=True, ParentPost__isnull=False)).order_by(
        '-id').prefetch_related('PostImages', 'Poll', 'ParentPost', 'RePost', 'ParentPost', 'ReplyingTo', 'ParentPost',
                                'PostImages', 'Group', 'Likes').select_related('Video', 'PostBody', 'PostLink',
                                                                               'OverWatchFinalOutcome')[
           offset:offset + limit]
    serializer = PostSerializer(Post, context={'request': request}, many=True)
    if request.auth == None:
        serializer = PostSerializer(Post, many=True)
        return Response(serializer.data)
    CurrentUser = request.auth.user
    try:
        Following.objects.get(GettingFollowed=CurrentUser.userprofile, Follower=UserToView.userprofile, Status=2)
        raise Blocked
    except exceptions.ObjectDoesNotExist:
        pass
    if UserToView == request.auth.user:
        return Response(serializer.data)
    else:
        CurrentUser = request.auth.user
        try:
            Status = Following.objects.get(Follower=CurrentUser.userprofile, GettingFollowed=UserToView.userprofile)
            if Status.Status == 0:
                Post = Posts.objects.filter(Q(PostedBy=UserToView.userprofile,ParentPost__isnull=False, ParentPost__Public = True, Group = None)|Q(PostedBy=UserToView.userprofile,ParentPost__isnull=False, ParentPost__Group__PostsArePublic = True, Group__isnull=False))[offset:offset + limit]
                serializer = PostSerializer(Post, context={'request': request}, many=True)
                return Response(serializer.data)
            elif Status.Status == 1:
                Post = Posts.objects.filter(Q(PostedBy=UserToView.userprofile,ParentPost__isnull=False, ParentPost__Public = True, Group = None)|Q(PostedBy=UserToView.userprofile,ParentPost__isnull=False, ParentPost__Group__PostsArePublic = True, Group__isnull=False))[offset:offset + limit]
                serializer = PostSerializer(Post, context={'request': request}, many=True)
                return Response(serializer.data)
            elif Status.Status == 2:
                raise Blocked
        except exceptions.ObjectDoesNotExist:
            Post = Posts.objects.filter(Q(PostedBy=UserToView.userprofile,ParentPost__isnull=False, ParentPost__Public = True, Group = None)|Q(PostedBy=UserToView.userprofile,ParentPost__isnull=False, ParentPost__Group__PostsArePublic = True, Group__isnull=False))[offset:offset + limit]
            serializer = PostSerializer(Post, context={'request': request}, many=True)
            return Response(serializer.data)
@api_view(['GET'])
def GetUserSelfPosts(request, pk):
    try:
        UserToView = User.objects.get(username__iexact=pk)
    except exceptions.ObjectDoesNotExist:
        raise UserDoesNotExist
    limit = int(request.GET.get('limit', 0))
    offset = int(request.GET.get('offset', 32))
    Post = Posts.objects.filter(PostedBy=UserToView.userprofile, Group = None, ParentPost=None, Public = True).order_by('-id').prefetch_related('PostImages', 'Poll', 'ParentPost', 'RePost', 'ParentPost', 'ReplyingTo', 'ParentPost', 'PostImages', 'Group', 'Likes').select_related('Video', 'PostBody', 'PostLink', 'OverWatchFinalOutcome')[offset:limit+offset]
    serializer = PostSerializer(Post, context={'request': request}, many=True)
    if request.auth == None:
        serializer = PostSerializer(Post, many=True)
        return Response(serializer.data)
    CurrentUser = request.auth.user
    try:
        Following.objects.get(GettingFollowed=CurrentUser.userprofile, Follower=UserToView.userprofile, Status=2)
        raise Blocked
    except exceptions.ObjectDoesNotExist:
        pass
    if UserToView == request.auth.user:
        Post = Posts.objects.filter(PostedBy=UserToView.userprofile, Group = None, ParentPost=None).order_by('-id').prefetch_related('PostImages', 'Poll', 'ParentPost', 'RePost', 'ParentPost', 'ReplyingTo', 'ParentPost', 'PostImages', 'Group', 'Likes').select_related('Video', 'PostBody', 'PostLink', 'OverWatchFinalOutcome')[offset:limit+offset]
        return Response(serializer.data)
    else:
        try:
            CurrentUser = request.auth.user
            try:
                Following.objects.get(Follower=CurrentUser.userprofile, GettingFollowed=UserToView.userprofile)
                return Response(serializer.data)
            except exceptions.ObjectDoesNotExist:
                return Response(serializer.data)
        except exceptions.ObjectDoesNotExist:
            return Response(serializer.data)

@api_view(['POST', 'GET'])
def CreatePost(request):
    CurrentUser = request.auth.user
    if request.method == "POST":
        Title = request.data.get('Title')
        '''
        try:
            time_threshold = datetime.now(timezone.utc) - timedelta(minutes=5)
            Posts.objects.get(PostedBy = CurrentUser.userprofile, Title__iexact=Title, PostedOn__gt=time_threshold)
            raise Spam
        except exceptions.ObjectDoesNotExist:
            pass
        '''
        #print(request.data)
        ##print(request.data)
        if request.data.get('base_64'):
            serializer = PostCRUD(data=request.data, context={'request': request, 'PostBody':request.data.pop('PostBody'), 'Link':request.data.get('Link', None)})
            if serializer.is_valid():
                serializer.save(
                )
                raise Success
            else:
                raise Invalid

        if request.data.get('Poll'):
            ##print('AYY')
            ##print(request.data)
            serializer = PostCRUD(data=request.data, context={'request': request, 'PostBody':request.data.pop('PostBody'), 'Link':request.data.get('Link', None)})
            if serializer.is_valid():
                serializer.save(
                )
                raise Success
            else:
                raise Invalid
        elif request.data.get('Video'):
            serializer = PostCRUDVideo(data=request.data, context={'request': request, 'PostBody':request.data.pop('PostBody'), 'Link':request.data.get('Link', None)})
            ##print('GAYY')
            ##print(request.data)
            if serializer.is_valid():
                serializer.save(
                )
                raise Success
            else:
                raise Invalid
        else:
            serializer = PostCRUD_Image(data=request.data, context={'request': request, 'PostBody':request.data.pop('PostBody'), 'Link':request.data.get('Link', None)})
            ##print('NAYY')
            ##print(request.data)
        
            if serializer.is_valid():
                serializer.save(
                    PostedBy=CurrentUser.userprofile,
                )
                raise Success
            else:
                raise Invalid

    if request.method == 'GET':
        limit = int(request.GET.get('limit', 32))
        offset = int(request.GET.get('offset', 0))
        if limit>64:
            limit=64
        Post = Posts.objects.filter(PostedBy = CurrentUser.userprofile).prefetch_related('PostImages', 'Poll', 'ParentPost', 'RePost', 'ParentPost', 'ReplyingTo', 'ParentPost', 'PostImages', 'Group', 'Likes').select_related('Video', 'PostBody', 'PostLink', 'OverWatchFinalOutcome')[limit:limit+offset]
        serializer = PostSerializer(Post, context={'request': request}, many=True)
        return Response(serializer.data)


@api_view(["GET", "POST", "DELETE"])
def ViewPostDetails(request, pk, pk2):
    try:
        UserToView = User.objects.get(username__iexact=pk)
        Post = Posts.objects.get(PostedBy=UserToView.userprofile, id=pk2, ParentPost = None)
    except exceptions.ObjectDoesNotExist:
        raise PostDoesNotExist
    if request.auth == None:
        if Post.Group:
            if Post.Group.PostsArePublic:
                serializer = PostSerializerFull(Post, many=False)
                return Response(serializer.data)
            else:
                raise PleaseSignIn
        else:
            if Post.Public:
                serializer = PostSerializerFull(Post, many=False)
                return Response(serializer.data)
    CurrentUser = request.auth.user
    if request.method == "GET":
        serializer = PostSerializerFull(Post, context={'request': request}, many=False)
        if Post.Group:
            try:
                Status = GroupMembers.objects.get(User = CurrentUser.userprofile, Group = Post.Group)
                if Status.Status == 1:
                    return Response(serializer.data)
                elif Status.Status == 2:
                    serializer = PostSerializerFull(Post, context={'request': request, 'auth':True}, many=False)
                    return Response(serializer.data)
                else:
                    if Post.Group.PostsArePublic:
                        return Response(serializer.data)
                    else:
                        try:
                            Mentions.objects.get(User=CurrentUser.userprofile, Post=Post)
                            return Response(serializer.data)
                        except exceptions.ObjectDoesNotExist:
                            raise Unauthorised
            except exceptions.ObjectDoesNotExist:
                if CurrentUser == UserToView:
                    return Response(serializer.data)
                else:
                    if Post.Group.PostsArePublic:
                        return Response(serializer.data)
                    else:
                         raise Unauthorised
        else:
            if CurrentUser == UserToView:
                return Response(serializer.data)
            else:
                if Post.Public:
                    return Response(serializer.data)
                else:
                    try:
                        Following.objects.get(Follower = CurrentUser.userprofile, GettingFollowed = UserToView.userprofile)
                        return Response(serializer.data)
                    except exceptions.ObjectDoesNotExist:
                        try:
                            Mentions.objects.get(User = CurrentUser.userprofile, Post = Post)
                            return Response(serializer.data)
                        except exceptions.ObjectDoesNotExist:
                            ##print('PENIS')
                            raise ServiceUnavailable


    if request.method == "DELETE":
        if Post.PostedBy == CurrentUser.userprofile:
            Post.delete()
            raise Success
        else:
            if Post.Group:
                try:
                    Status = GroupMembers.objects.get(User = CurrentUser.userprofile, Group = Post.Group)
                    if Status.Status == 2:
                        Post.delete()
                        raise Success
                except exceptions.ObjectDoesNotExist:
                    raise Unauthorised
            else:
                raise Unauthorised


@api_view(["GET", "POST"])
def PostComments(request, pk, pk2):
    try:
        UserToView = User.objects.get(username__iexact=pk)
        Post = Posts.objects.get(PostedBy=UserToView.userprofile, id=pk2)
    except exceptions.ObjectDoesNotExist:
        raise PostDoesNotExist
    if request.method == "GET":
        limit = int(request.GET.get('limit', 0))
        offset = int(request.GET.get('offset', 32))
        if request.GET.get('order') == 'best':
            OrderBy = '-Vote'
        elif request.GET.get('order') == 'new':
            OrderBy = '-id'

        if request.auth == None:
            if Post.Group:
                if Post.Group.PostsArePublic:
                   Comments = Posts.objects.filter(ParentPost=Post, ReplyingTo=None).order_by('-id').prefetch_related(
                            'PostImages', 'Poll', 'ParentPost', 'RePost', 'ParentPost', 'ReplyingTo', 'ParentPost',
                            'PostImages', 'Group', 'Likes').select_related('Video', 'PostBody', 'PostLink', 'OverWatchFinalOutcome').order_by(OrderBy)[offset:limit + offset]
                   serializer = PostSerializer(Comments, many=True)
                   return Response(serializer.data)
                else:
                    raise PleaseSignIn
            else:
                if Post.Public:
                    Comments = Posts.objects.filter(ParentPost=Post, ReplyingTo=None).order_by('-id').prefetch_related(
                        'PostImages', 'Poll', 'ParentPost', 'RePost', 'ParentPost', 'ReplyingTo', 'ParentPost',
                        'PostImages', 'Group', 'Likes').select_related('Video', 'PostBody', 'PostLink',
                                                                    'OverWatchFinalOutcome').order_by(OrderBy)[offset:limit + offset]
                    serializer = PostSerializerFull(Comments, many=True)
                    return Response(serializer.data)
                else:
                    raise PleaseSignIn
        CurrentUser = request.auth.user    
        Comments = Posts.objects.filter(ParentPost=Post, ReplyingTo=None).order_by(OrderBy).prefetch_related('PostImages', 'Poll', 'ParentPost', 'RePost', 'ParentPost', 'ReplyingTo', 'ParentPost', 'PostImages', 'Group', 'Likes').select_related('Video', 'PostBody', 'PostLink', 'OverWatchFinalOutcome').order_by(OrderBy)[offset:limit+offset]
        serializer = PostSerializer(Comments, context={'request': request}, many=True)
        if Post.Group:
            try:
                Status = GroupMembers.objects.get(User=CurrentUser.userprofile, Group=Post.Group)
                if Status.Status == 1:
                    return Response(serializer.data)
                elif Status.Status == 2:
                    serializer = PostSerializer(Comments, context={'request': request, 'auth':True}, many=True)
                    return Response(serializer.data)
                else:
                    raise Unauthorised
            except exceptions.ObjectDoesNotExist:
                if CurrentUser == UserToView:
                    return Response(serializer.data)
                if Post.Group.PostsArePublic:
                    return Response(serializer.data)
                else:
                    raise Unauthorised
        else:
            if CurrentUser == UserToView:
                return Response(serializer.data)
            else:
                if Post.Public:
                    return Response(serializer.data)
                else:
                    try:
                        Following.objects.get(Follower = CurrentUser.userprofile, GettingFollowed = UserToView.userprofile)
                        return Response(serializer.data)
                    except exceptions.ObjectDoesNotExist:
                        try:
                            Mentions.objects.get(User = CurrentUser.userprofile, Post = Post)
                            return Response(serializer.data)
                        except exceptions.ObjectDoesNotExist:
                            raise Unauthorised

    if request.method == "POST":
        CurrentUser = request.auth.user
        Title = request.data.get('Title')
        try:
            time_threshold = datetime.now(timezone.utc) - timedelta(minutes=5)
            Posts.objects.get(PostedBy=CurrentUser.userprofile, Title__iexact=Title, PostedOn__gt=time_threshold)
            raise Spam
        except exceptions.ObjectDoesNotExist:
            pass
        try:
            Following.objects.get(Follower=UserToView.userprofile, GettingFollowed=CurrentUser.userprofile, Status=2)
            raise Blocked
        except exceptions.ObjectDoesNotExist:
            pass
        if Post.Group:
            try:
                Status = GroupMembers.objects.get(
                    User = CurrentUser.userprofile,
                    Group = Post.Group
                )
                if Status.Status == 1:
                    pass
                elif Status.Status ==2:
                    pass
            except exceptions.ObjectDoesNotExist:
                raise Unauthorised
        else:
            if UserToView == CurrentUser:
                pass
            else:
                if Post.WhoCanComment == 2:
                    pass
                if Post.WhoCanComment == 1:
                    try:
                        Mentions.objects.get(User = CurrentUser.userprofile, Post = Post)
                        pass
                    except exceptions.ObjectDoesNotExist:
                        raise Unauthorised
                if Post.WhoCanComment == 0:
                    try:
                        Following.objects.get(Follower = CurrentUser.userprofile, GettingFollowed = UserToView.userprofile)
                        pass
                    except exceptions.ObjectDoesNotExist:
                        try:
                            Mentions.objects.get(User=CurrentUser.userprofile, Post=Post)
                            pass
                        except exceptions.ObjectDoesNotExist:
                            raise Unauthorised
        if request.data.get('Poll'):
            ##print('AYY')
            ##print(request.data)
            serializer = PostCRUD(data=request.data,context={'request': request,'Link': request.data.get('Link', None), 'ParentPost':Post})
            if serializer.is_valid():
                serializer.save()
                raise Success
            else:
                raise Invalid
        if request.data.get('Video'):
            serializer = PostCRUDVideo(data=request.data,context={'request': request,'Link': request.data.get('Link', None), 'ParentPost':Post})
            ##print('GAYY')
            ##print(request.data)
            if serializer.is_valid():
                serializer.save()
                raise Success
            else:
                raise Invalid
        else:
            serializer = PostCRUD_Image(data=request.data,context={'request': request,'Link': request.data.get('Link', None), 'ParentPost':Post})
            ##print('NAYY')
            ##print(request.data)
            if serializer.is_valid():
                serializer.save(
                    PostedBy=CurrentUser.userprofile,
                )
                raise Success
            else:
                raise Invalid


@api_view(["POST"])
def LikePost(request, pk, pk2):
    SayHello.delay()
    if request.auth == None:
        raise PleaseSignIn
    CurrentUser = request.auth.user
    try:
        UserToView = User.objects.get(username__iexact=pk)
        Post = Posts.objects.get(PostedBy=UserToView.userprofile, id=pk2)
    except exceptions.ObjectDoesNotExist:
        raise PostDoesNotExist
    try:
        Following.objects.get(Follower=UserToView.userprofile, GettingFollowed=CurrentUser.userprofile, Status=2)
        raise Blocked
    except exceptions.ObjectDoesNotExist:
        pass
    if Post.ParentPost:
        ParentPost = Post.ParentPost
        if ParentPost.Group:
            if CurrentUser == UserToView:
                pass
            else:
                if ParentPost.Group.PostsArePublic:
                    pass
                else:
                    try:
                        Status = GroupMembers.objects.get(User=CurrentUser.userprofile, Group=ParentPost.Group)
                        if Status.Status == 1 or Status.Status == 2:
                            pass
                        else:
                            raise Unauthorised
                    except exceptions.ObjectDoesNotExist:
                        raise Unauthorised
        else:
            if CurrentUser==ParentPost.PostedBy:
                pass
            else:

                if Post.ParentPost.Public:
                    pass
                else:
                    try:
                        Following.objects.get(Follower = CurrentUser.userprofile, GettingFollowed = Post.ParentPost.PostedBy)
                        pass
                    except exceptions.ObjectDoesNotExist:
                        try:
                            Mentions.objects.get(User = CurrentUser.userprofile, Post = Post.ParentPost)
                            pass
                        except exceptions.ObjectDoesNotExist:
                            raise Unauthorised

    else:
        if Post.Group:
            if CurrentUser == UserToView:
                pass
            else:
                if Post.Group.PostsArePublic:
                    pass
                else:
                    try:
                        Status = GroupMembers.objects.get(User=CurrentUser.userprofile, Group=Post.Group)
                        if Status.Status == 1 or Status.Status == 2:
                           pass
                        else:
                            raise Unauthorised
                    except exceptions.ObjectDoesNotExist:
                        raise Unauthorised
        else:
            if CurrentUser==UserToView:
                pass
            else:
                if request.method == 'POST':
                    if Post.Public:
                        pass
                    else:
                        try:
                            Following.objects.get(Follower = CurrentUser.userprofile, GettingFollowed = UserToView.userprofile)
                            pass
                        except exceptions.ObjectDoesNotExist:
                            try:
                                Mentions.objects.get(User = CurrentUser.userprofile, Post = Post)
                                pass
                            except exceptions.ObjectDoesNotExist:
                                raise Unauthorised
    try:
        LikeStatus = PostLikes.objects.get(User=CurrentUser.userprofile, Post=Post)
        if LikeStatus.Status == True:
            LikeStatus.delete()
            Post.Vote = Post.Vote - 1
            Post.save()
            return Response(data={"Liked": None, "VoteCount": Post.Vote})
        elif LikeStatus.Status == False:
            LikeStatus.delete()
            Post.Vote = Post.Vote + 2
            Post.save()
            PostLikes.objects.create(Post=Post, User=CurrentUser.userprofile, Status=True)
            return Response(data={"Liked": True, "VoteCount": Post.Vote})
    except exceptions.ObjectDoesNotExist:
        PostLikes.objects.create(Post=Post, User=CurrentUser.userprofile, Status=True)
        Post.Vote = Post.Vote + 1
        Post.save()
        return Response(data={"Liked": True, "VoteCount": Post.Vote})


@api_view(["POST"])
def DisLikePost(request, pk, pk2):
    if request.auth == None:
        raise PleaseSignIn
    CurrentUser = request.auth.user
    try:
        UserToView = User.objects.get(username__iexact=pk)
        Post = Posts.objects.get(PostedBy=UserToView.userprofile, id=pk2)
    except exceptions.ObjectDoesNotExist:
        raise PostDoesNotExist
    try:
        Following.objects.get(Follower=UserToView.userprofile, GettingFollowed=CurrentUser.userprofile, Status=2)
        raise Blocked
    except exceptions.ObjectDoesNotExist:
        pass
    if Post.ParentPost:
        ParentPost = Post.ParentPost
        if ParentPost.Group:
            if CurrentUser == UserToView:
                pass
            else:
                if ParentPost.Group.PostsArePublic:
                    pass
                else:
                    try:
                        Status = GroupMembers.objects.get(User=CurrentUser.userprofile, Group=ParentPost.Group)
                        if Status.Status == 1 or Status.Status == 2:
                            pass
                        else:
                            raise Unauthorised
                    except exceptions.ObjectDoesNotExist:
                        raise Unauthorised
        else:
            if CurrentUser == ParentPost.PostedBy:
                pass
            else:

                if Post.ParentPost.Public:
                    pass
                else:
                    try:
                        Following.objects.get(Follower=CurrentUser.userprofile, GettingFollowed=Post.ParentPost.PostedBy)
                        pass
                    except exceptions.ObjectDoesNotExist:
                        try:
                            Mentions.objects.get(User=CurrentUser.userprofile, Post=Post.ParentPost)
                            pass
                        except exceptions.ObjectDoesNotExist:
                            raise Unauthorised

    else:
        if Post.Group:
            if CurrentUser == UserToView:
                pass
            else:
                if Post.Group.PostsArePublic:
                    pass
                else:
                    try:
                        Status = GroupMembers.objects.get(User=CurrentUser.userprofile, Group=Post.Group)
                        if Status.Status == 1 or Status.Status == 2:
                            pass
                        else:
                            raise Unauthorised
                    except exceptions.ObjectDoesNotExist:
                        raise Unauthorised
        else:
            if CurrentUser == UserToView:
                pass
            else:
                if request.method == 'POST':
                    if Post.Public:
                        pass
                    else:
                        try:
                            Following.objects.get(Follower=CurrentUser.userprofile,
                                                  GettingFollowed=UserToView.userprofile)
                            pass
                        except exceptions.ObjectDoesNotExist:
                            try:
                                Mentions.objects.get(User=CurrentUser.userprofile, Post=Post)
                                pass
                            except exceptions.ObjectDoesNotExist:
                                raise Unauthorised

    try:
        LikeStatus = PostLikes.objects.get(User=CurrentUser.userprofile, Post=Post)
        if LikeStatus.Status == False:
            LikeStatus.delete()
            Post.Vote = Post.Vote + 1
            Post.save()
            return Response(data={"Liked": None, "VoteCount": Post.Vote})
        elif LikeStatus.Status == True:
            LikeStatus.delete()
            Post.Vote = Post.Vote - 2
            Post.save()
            PostLikes.objects.create(Post=Post, User=CurrentUser.userprofile, Status=False)
            return Response(data={"Liked": False, "VoteCount": Post.Vote})
    except exceptions.ObjectDoesNotExist:
        PostLikes.objects.create(Post=Post, User=CurrentUser.userprofile, Status=False)
        Post.Vote = Post.Vote - 1
        Post.save()
        return Response(data={"Liked": False, "VoteCount": Post.Vote})




@api_view(["GET"])
def UserExists(request, pk):
    try:
        User.objects.get(username__iexact=pk)
        return Response(data={"Exists": True})
    except exceptions.ObjectDoesNotExist:
        return Response(data={"Exists": False})

@api_view(["GET"])
def CommunityExists(request):
    Name = request.GET.get('name', None)
    try:
        Groups.objects.get(Name__iexact=Name)
        return Response(data={"Exists": True})
    except exceptions.ObjectDoesNotExist:
        return Response(data={"Exists": False})

@api_view(["GET"])
def CollectionExists(request):
    Name = request.GET.get('name', None)
    try:
        Collections.objects.get(Name__iexact=Name)
       ##print('BBB')
        return Response(data={"Exists": True})
    except exceptions.ObjectDoesNotExist:
       ##print('AAA')
        return Response(data={"Exists": False})

@api_view(['GET'])
def LikedPosts(request):
    CurrentUser = request.auth.user
    limit = int(request.GET.get('limit', 32))
    offset = int(request.GET.get('offset', 0))
    if limit>64:
        limit=64
    Post = Posts.objects.filter(Likes__User = CurrentUser.userprofile, Likes__Status = True).order_by('-Likes').prefetch_related('PostImages', 'Poll', 'ParentPost', 'RePost', 'ParentPost', 'ReplyingTo', 'ParentPost', 'PostImages', 'Group', 'Likes').select_related('Video', 'PostBody', 'PostLink', 'OverWatchFinalOutcome')[offset:limit+offset]
    serializer = PostSerializer(Post, many=True,context={'request':request})
    return Response(serializer.data)

@api_view(['GET'])
def DisLikedPosts(request):
    CurrentUser = request.auth.user
    limit = int(request.GET.get('limit', 32))
    offset = int(request.GET.get('offset', 0))
    if limit>64:
        limit=64
    Post = Posts.objects.filter(Likes__User = CurrentUser.userprofile, Likes__Status = False).order_by('-Likes').prefetch_related('PostImages', 'Poll', 'ParentPost', 'RePost', 'ParentPost', 'ReplyingTo', 'ParentPost', 'PostImages', 'Group', 'Likes').select_related('Video', 'PostBody', 'PostLink', 'OverWatchFinalOutcome')[offset:limit+offset]
    serializer = PostSerializer(Post, many=True,context={'request':request})
    return Response(serializer.data)

@api_view(["GET"])
def PostFeed(request):
    if request.auth == None:
        limit = int(request.GET.get('limit', 16))
        offset = int(request.GET.get('offset', 0))
        if limit > 64:
            limit = 64
        PostLanguage = LanguageCodes(request.GET.get('lang'))
        time_threshold = datetime.now(timezone.utc) - timedelta(hours=72)
        limit = int(request.GET.get('limit', 16))
        offset = int(request.GET.get('offset', 0))
        Post = Posts.objects.filter(Q(Public = True, Group = None, ParentPost = None, PostedOn__gt=time_threshold, Language = PostLanguage)|Q(Group__PostsArePublic = True, ParentPost = None, PostedOn__gt=time_threshold, Language = PostLanguage)).order_by('-Vote')[offset:limit+offset]
        serializer = PostSerializer(Post, many=True)
        return Response(serializer.data)

    CurrentUser = request.auth.user
    Followings = Following.objects.filter(
        Follower=CurrentUser.userprofile, Status=ACCEPTED
    ).values_list("GettingFollowed_id", flat=True)
    MyGroups = GroupMembers.objects.filter(
        Q(User=CurrentUser.userprofile, Status=1)|
        Q(User=CurrentUser.userprofile, Status=2)
    ).values_list("Group_id", flat=True)
    time_now = datetime.utcnow().replace(tzinfo=utc)
    limit = int(request.GET.get('limit', 16))
    offset = int(request.GET.get('offset', 0))
    if limit>64:
        limit=64
    PostLanguage = LanguageCodes(request.GET.get('lang'))
    Post = Posts.objects.filter(Q(PostedBy__in=Followings, Group = None, ParentPost = None)|Q(Group__in = MyGroups, ParentPost = None)).order_by('-id').prefetch_related('PostImages', 'Poll', 'ParentPost', 'RePost', 'ParentPost', 'ReplyingTo', 'ParentPost', 'PostImages', 'Group', 'Likes').select_related('Video', 'PostBody', 'PostLink', 'OverWatchFinalOutcome')[offset:offset+limit]
    ##print(Post.query)
    serializer = PostSerializer(Post,context={'request':request}, many=True)
    return Response(serializer.data)

@api_view(["GET"])
def TrendingPosts(request):
    time_threshold = datetime.now(timezone.utc) - timedelta(hours=24)
    limit = int(request.GET.get('limit', 16))
    offset = int(request.GET.get('offset', 0))
    if limit>64:
        limit=64
    UserLanguage = LanguageCodes(request.GET.get('lang'))
    Post = Posts.objects.filter(Q(Public = True, Group = None, ParentPost = None, PostedOn__gt=time_threshold, Language = UserLanguage)|Q(Group__PostsArePublic = True, ParentPost = None, PostedOn__gt=time_threshold, Language = UserLanguage)).order_by('-Vote')[offset:limit+offset]
    if request.auth == None:
        serializer = PostSerializer(Post, many=True)
        return Response(serializer.data)
    serializer = PostSerializer(Post,context={'request':request}, many=True)
    return Response(serializer.data)

########################################################################################################################


@api_view(["POST"])
def SendFollowRequest(request, pk):
    if request.auth == None:
        raise PleaseSignIn
    try:
        UserToSendRequestTo = User.objects.get(username__iexact=pk)
    except exceptions.ObjectDoesNotExist:
        raise UserDoesNotExist
    CurrentUser = request.auth.user
    try:
        Following.objects.get(GettingFollowed=CurrentUser.userprofile, Follower=UserToSendRequestTo.userprofile, Status=2)
        raise Blocked
    except exceptions.ObjectDoesNotExist:
        pass
    if CurrentUser == UserToSendRequestTo:
        raise Unauthorised
    try:
        FollowStatus = Following.objects.get(
            Follower=CurrentUser.userprofile,
            GettingFollowed=UserToSendRequestTo.userprofile,
        )
        if FollowStatus.Status == ACCEPTED:
            raise AlreadyFollowing
        if FollowStatus.Status == PENDING:
            raise AlreadyFollowing
        else:
            return HttpResponse("This user has denied your request!")
    except exceptions.ObjectDoesNotExist:
        serializer = SendFollowRequestSerializer(data=request.data)
        if UserToSendRequestTo.userprofile.RequirePermissionToFollow == True:
            serializer = SendFollowRequestSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(
                    Follower=CurrentUser.userprofile,
                    GettingFollowed=UserToSendRequestTo.userprofile,
                    Status=PENDING,
                )
                SendFollowNotification.delay(UserToSendRequestTo.id, CurrentUser.id)
                return Response(data={"Status": 0})
            
            else:
                raise Invalid
        if UserToSendRequestTo.userprofile.RequirePermissionToFollow == False:
            serializer = SendFollowRequestSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(
                    Follower=CurrentUser.userprofile,
                    GettingFollowed=UserToSendRequestTo.userprofile,
                    Status=ACCEPTED,
                )
                return Response(data={"Status": 1})
            else:
                raise Invalid
        else:
            raise Unauthorised

@api_view(["GET"])
def FollowersAll(request):
    CurrentUser = request.auth.user
    Requests = Following.objects.filter(GettingFollowed=CurrentUser.userprofile).order_by('Status', '-id')[:64]
    serializer = FollowerSerializers(Requests, many = True, context={'request':request})

    return Response(serializer.data)

@api_view(["GET"])
def Followers(request):
    CurrentUser = request.auth.user
    Requests = Following.objects.filter(GettingFollowed=CurrentUser.userprofile, Status = ACCEPTED).order_by('Status', '-id')[:64]
    serializer = FollowerSerializers(Requests, many = True, context={'request':request})
    return Response(serializer.data)

@api_view(["GET"])
def FollowingsAll(request):
    CurrentUser = request.auth.user
    limit = int(request.GET.get('limit', 32))
    offset = int(request.GET.get('offset', 0))
    if limit>64:
        limit=64
    Requests = Following.objects.filter(Follower=CurrentUser.userprofile).values_list('GettingFollowed_id', flat=True).order_by('Status', '-id')[offset:limit+offset]
    preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(Requests)])
    UserList = UserProfile.objects.filter(id__in = Requests).order_by(preserved)
    serializer = UserProfileSerializer(UserList, many = True, context={'request':request})
    return Response(serializer.data)

@api_view(['GET'])
def MyGroups(request):
    CurrentUser = request.auth.user
    InGroups = GroupMembers.objects.filter(User=CurrentUser.userprofile).values_list('Group')
    Group = Groups.objects.filter(id__in = InGroups)
    serializer = GroupSerializer(Group, many=True, context={'request':request})
    return Response(serializer.data)
@api_view(["GET"])
def Followings(request):
    CurrentUser = request.auth.user
    Requests = Following.objects.filter(
        Follower=CurrentUser.userprofile, Status=ACCEPTED
    )
    serializer = FollowingSerializer(Requests, many=True)
    return Response(serializer.data)

@api_view(["GET"])
def NotifyFor(request):
    CurrentUser = request.auth.user
    limit = int(request.GET.get('limit', 32))
    offset = int(request.GET.get('offset', 0))
    if limit>64:
        limit=64
    Requests = Following.objects.filter(Follower=CurrentUser.userprofile, Notify__isnull=False,).order_by('Status', '-id').values_list('GettingFollowed_id', flat=True)[offset:limit+offset]
    UserList = UserProfile.objects.filter(id__in = Requests)
    serializer = UserProfileSerializer(UserList, many = True, context={'request':request})
    return Response(serializer.data)


@api_view(["GET", "POST", "DELETE"])
def FollowersPending(request):
    CurrentUser = request.auth.user
    if request.method == 'GET':
        Requests = Following.objects.filter(GettingFollowed=CurrentUser.userprofile, Status = PENDING).order_by('-id').values_list('GettingFollowed')[:64]
        Users = UserProfile.objects.filter(id__in = Requests)
        serializer = UserProfileSerializer(Users, many=True, context={'request':request})
        return Response(serializer.data)
    else:
        PendingRequests = Following.objects.filter(GettingFollowed = CurrentUser.userprofile, Status = PENDING)
        if request.method == 'POST':
            PendingRequests.update(Status = ACCEPTED)
            return Response(data={'Status':None})
        else:
            PendingRequests.delete()
            raise Success

@api_view(["POST", "DELETE"])
def ManagePending(request, pk):
    CurrentUser = request.auth.user
    try:
        UserToView = User.objects.get(username__iexact=pk)
        Follow = Following.objects.get(Follower = UserToView.userprofile, GettingFollowed = CurrentUser.userprofile, Status = NOTACCEPTED)
    except exceptions.ObjectDoesNotExist:
        raise UserDoesNotExist
    if request.method == 'POST':
        Follow.Status = 1
        Follow.save()

        ##print('SUCEXX')
        return Response(data={'Status':1})
    if request.method == 'DELETE':
        Follow.delete()
        raise Success




@api_view(["GET"])
def FollowingsPending(request):
    CurrentUser = request.auth.user
    Requests = Following.objects.filter(
        Follower=CurrentUser.userprofile, Status=PENDING
    )
    serializer = FollowingSerializer(Requests, many=True)
    return Response(serializer.data)


@api_view(["GET", "POST", "DELETE"])
def ModifyFollowing(request, pk):
    CurrentUser = request.auth.user
    try:
        UserToView = User.objects.get(username__iexact=pk)
        Follower = Following.objects.get(
            GettingFollowed=UserToView.userprofile, Follower=CurrentUser.userprofile
        )
    except exceptions.ObjectDoesNotExist:
        raise UserDoesNotExist
    if Follower.Status == 0:
        try:
            Notifications.objects.filter(User = UserToView.userprofile, From = CurrentUser.userprofile, Type = 'flwrrq')[0].delete()
        except exceptions.ObjectDoesNotExist:
            pass
        Follower.delete()
        return Response(data={"Status": None})
    if request.method == "DELETE":
        Follower.delete()
        return Response(data={"Status": None})
    if request.method == "GET":
        serializer = FollowingSerializer(Follower, many=False)
        return Response(serializer.data)
    else:
        return HttpResponse("You can only remove!")


########################################################################################################################



@api_view(['GET'])
def MyMentions(request):
    CurrentUser = request.auth.user
    Mention = Mentions.objects.filter(User = CurrentUser.userprofile).values_list('Post_id')
    Post = Posts.objects.filter(id__in=Mention).prefetch_related('PostImages', 'Poll', 'ParentPost', 'RePost', 'ParentPost', 'ReplyingTo', 'ParentPost', 'PostImages', 'Group', 'Likes').select_related('Video', 'PostBody', 'PostLink', 'OverWatchFinalOutcome')
    serializer = PostSerializer(Post, many=True, context={'request':request})

    return Response(serializer.data)

@api_view(['GET'])
def MyCommentReplies(request):
    CurrentUser = request.auth.user
    MyPosts = Posts.objects.filter(PostedBy = CurrentUser.userprofile)
    List = Posts.objects.filter(Q(ReplyingTo__in = MyPosts)|Q(ParentPost__in=MyPosts)).order_by('-id')
    serializer = PostSerializer(List, many=True, context={'request':request})
    return Response(serializer.data)



########################################################################################################################

@api_view(['GET'])
def Trending(request, pk):
    try:
        Tag = Tags.objects.get(Tag = pk)
    except exceptions.ObjectDoesNotExist:
        raise PostDoesNotExist
    ByFollowers = request.GET.get('by_following', '0')
    if request.auth == None:
        limit = int(request.GET.get('limit', 32))
        offset = int(request.GET.get('offset', 0))
        if limit > 64:
            limit = 64
        Post = Posts.objects.filter(
            Q(Tags__Tag=Tag, Public=True, Group=None, ParentPost=None) | Q(Tags__Tag=Tag, Group__PostsArePublic=True,
                                                                           ParentPost=None)).prefetch_related(
            'PostImages', 'Poll', 'ParentPost', 'RePost', 'ParentPost', 'ReplyingTo', 'ParentPost', 'PostImages',
            'Group', 'Likes').select_related('Video', 'PostBody', 'PostLink', 'OverWatchFinalOutcome')[
               offset:limit + offset]
        serializer = PostSerializer(Post, many=True)
        return Response(serializer.data)
    CurrentUser = request.auth.user
    if ByFollowers == '0':
        limit = int(request.GET.get('limit', 32))
        offset = int(request.GET.get('offset', 0))
        if limit>64:
            limit=64
        Post = Posts.objects.filter(Q(Tags__Tag = Tag, Public=True, Group = None, ParentPost=None)|Q(Tags__Tag = Tag,Group__PostsArePublic=True, ParentPost=None)).prefetch_related('PostImages', 'Poll', 'ParentPost', 'RePost', 'ParentPost', 'ReplyingTo', 'ParentPost', 'PostImages', 'Group', 'Likes').select_related('Video', 'PostBody', 'PostLink', 'OverWatchFinalOutcome')[offset:limit+offset]
        serializer = PostSerializer(Post, many=True, context={'request':request})
        return Response(serializer.data)
    if ByFollowers == '1':
        limit = int(request.GET.get('limit', 32))
        offset = int(request.GET.get('offset', 0))
        if limit>64:
            limit=64
        FollowingAll = Following.objects.filter(Follower  = CurrentUser.userprofile).values_list('GettingFollowed')
        Post = Posts.objects.filter(PostedBy__in = FollowingAll, Tags__Tag = Tag).prefetch_related('PostImages', 'Poll', 'ParentPost', 'RePost', 'ParentPost', 'ReplyingTo', 'ParentPost', 'PostImages', 'Group', 'Likes').select_related('Video', 'PostBody', 'PostLink', 'OverWatchFinalOutcome')[offset:limit+offset]
        serializer = PostSerializer(Post, many=True, context={'request': request})
        return Response(serializer.data)

@api_view(['GET'])
def SearchTrending(request):
    SearchTerm = request.GET.get('search')
    Group = Tags.objects.filter(Q(Tag__contains=SearchTerm))[:25]
    serializer = TagSerializer(Group, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def SearchPosts(request):
    SearchTerms = request.GET.get('search')
    #SearchTerms = request.GET.get('search').strip().split(' ')

    ##print(SearchQuery)
    limit = int(request.GET.get('limit', 32))
    offset = int(request.GET.get('offset', 0))
    if limit>64:
        limit=64
    '''
    Post = Posts.objects.raw(
        f"""
        SELECT * FROM "app_posts" 
        LEFT OUTER JOIN "app_groups" ON ("app_posts".
        "Group_id" = "app_groups"."id")
        {SearchQuery}
        AND
        (
            "Public" = TRUE
            OR 
            "app_groups"."PostsArePublic" = true
        )
        LIMIT {limit} OFFSET {offset}

        
        """
    )[offset:limit+offset]
    '''
    Post = Posts.objects.annotate(search=SearchVector('Title')).filter(Q(search=SearchTerms, ParentPost=None, Public=True)|Q(Q(search=SearchTerms, ParentPost=None, Group__PostsArePublic=True))).distinct().prefetch_related('PostImages', 'Poll', 'ParentPost', 'RePost', 'ParentPost', 'ReplyingTo', 'ParentPost', 'PostImages', 'Group', 'Likes').select_related('Video', 'PostBody', 'PostLink', 'OverWatchFinalOutcome')[offset:limit+offset]
    ##print(Post)
    if request.auth == None:
        serializer = PostSerializer(Post, many=True)
        return Response(serializer.data)
    serializer = PostSerializer(Post, many = True, context={'request':request})
    return Response(serializer.data)

@api_view(['DELETE'])
def RemoveFollower(request, pk):
    CurrentUser = request.auth.user
    try:
        UserToView = User.objects.get(username__iexact=pk)
        Follow = Following.objects.get(Follower=UserToView.userprofile, GettingFollowed=CurrentUser.userprofile)
    except exceptions.ObjectDoesNotExist:
        raise UserDoesNotExist
    if request.method == 'DELETE':
        Follow.delete()
        raise Success

@api_view(['GET', 'POST'])
def GetGroupPage(request, pk):
    try:
        Group = Groups.objects.get(Name = pk)
    except exceptions.ObjectDoesNotExist:
        return UserDoesNotExist
    if request.method == 'GET':
        if request.auth == None:
            serializer = GroupSerializer(Group, many=False)
            return Response(serializer.data)
        CurrentUser = request.auth.user
        serializer = GroupSerializer(Group, many=False, context={'request':request})
        return Response(serializer.data)
    if request.method == 'POST':
        CurrentUser = request.auth.user
        try:
            Status = GroupMembers.objects.get(User = CurrentUser.userprofile, Group = Group, Status = 2)
        except exceptions.ObjectDoesNotExist:
            raise Unauthorised
        serializer = GroupEditSerializer(data = request.data, instance = Group)
        if serializer.is_valid():
            serializer.save()
            raise Success

@api_view(["GET"])
def GetTagPage(request, pk):
    try:
        TagToView = Tags.objects.get(Tag = pk)
    except exceptions.ObjectDoesNotExist:
        raise PostDoesNotExist
    serializer = TagSerializer(TagToView, many = False)
    return Response(serializer.data)

@api_view(['DELETE'])
def RemoveFollowing(request, pk):
    CurrentUser = request.auth.user
    try:
        UserToView = User.objects.get(username__iexact=pk)
        Follow = Following.objects.get(GettingFollowed=UserToView.userprofile, Follower=CurrentUser.userprofile)
    except exceptions.ObjectDoesNotExist:
        raise UserDoesNotExist
    if request.method == 'DELETE':
        Follow.delete()
        raise Success

@api_view(['POST', 'DELETE'])
def ModifyGroupMembership(request, pk):
    if request.auth == None:
        raise PleaseSignIn
    CurrentUser = request.auth.user
    if request.method == "POST":
        try:
            Group = Groups.objects.get(Name=pk)
        except exceptions.ObjectDoesNotExist:
            return UserDoesNotExist
        try:
            GroupMembers.objects.get(User = CurrentUser.userprofile, Group = Group)
            raise AlreadyExists
        except exceptions.ObjectDoesNotExist:
            if Group.AnyOneCanJoin:
                Status = GroupMembers.objects.create(
                    User = CurrentUser.userprofile,
                    Group = Group,
                    Status = 1
                )
                return Response(data = {"Status": Status.Status})
            else:
                Status = GroupMembers.objects.create(
                    User=CurrentUser.userprofile,
                    Group=Group,
                    Status=0
                )
                return Response(data={"Status": Status.Status})
    if request.method == "DELETE":
        CurrentUser = request.auth.user
        try:
            Group = Groups.objects.get(Name=pk)
        except exceptions.ObjectDoesNotExist:
            return UserDoesNotExist
        try:
            Status = GroupMembers.objects.get(User=CurrentUser.userprofile, Group=Group)
            Status.delete()
            return Response(data={"Status": None})
        except exceptions.ObjectDoesNotExist:
            raise Unauthorised


@api_view(['GET', 'POST'])
def ChatsAll(request, pk):
    CurrentUser = request.auth.user
    try:
        UserToView = User.objects.get(username__iexact=pk)
    except exceptions.ObjectDoesNotExist:
        raise UserDoesNotExist
    try:
        Following.objects.get(GettingFollowed=CurrentUser.userprofile, Follower=UserToView.userprofile, Status=2)
        raise Blocked
    except exceptions.ObjectDoesNotExist:
        pass
    if request.method == 'GET':
        UserToViewProfileSerializer = UserProfileSerializer(UserToView.userprofile, many=False, context={'request':request})
        Messages = Chat.objects.filter(Q(From = CurrentUser.userprofile, To = UserToView.userprofile)|Q(From = UserToView.userprofile, To=CurrentUser.userprofile)).order_by('-id')[:100]
        serializer = ChatSerializer(Messages, many=True, context={'request':request})
        try:
            return Response(data={'ChatData':serializer.data, 'UserData':UserToViewProfileSerializer.data})
        finally:
            Chat.objects.filter(Q(From = CurrentUser.userprofile, To = UserToView.userprofile)|Q(From = UserToView.userprofile, To=CurrentUser.userprofile)).order_by('-id').update(Read = True)
    if request.method == 'POST':
        try:
            Following.objects.get(GettingFollowed = CurrentUser.userprofile, Follower = UserToView.userprofile, Status = 2)
            raise Blocked
        except exceptions.ObjectDoesNotExist:
            pass
        serializer = ChatCRUD(data=request.data)
        #print(request.data)
        if serializer.is_valid():
            serializer.save(From = CurrentUser.userprofile, To = UserToView.userprofile)
            raise Success
        else:
            raise Invalid

@api_view(['GET'])
def ChatNew(request, pk):
    CurrentUser = request.auth.user
    try:
        UserToView = User.objects.get(username__iexact=pk)
    except exceptions.ObjectDoesNotExist:
        raise UserDoesNotExist
    if request.method == 'GET':
        Messages = Chat.objects.filter(From=UserToView.userprofile, To=CurrentUser.userprofile, Read = False).order_by('-id')
        ##print(Messages)
        serializer = ChatSerializer(Messages, many=True, context={'request': request})
        try:
            return Response(serializer.data)
        finally:
            Messages.filter(From = UserToView.userprofile).update(Read = True)


@api_view(['GET'])
def ChatPreview(request):
    if request.auth == None:
        raise PleaseSignIn
    CurrentUser = request.auth.user
    Messages = Chats.objects.filter(Q(User1 = CurrentUser.userprofile)|Q(User2 = CurrentUser.userprofile)).order_by('LastUpdated')[:100]
    serializer = ChatSummary(Messages, many=True,  context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def Trends(request):
    time_threshold = datetime.now(timezone.utc) - timedelta(hours=72)
    Trend = Tags.objects.filter(Created__gt = time_threshold).order_by('-Posts')[:25]
    #annotate(Average = Avg('posts__Vote'))
    UserLanguage = LanguageCodes(request.GET.get('lang'))
    serializer = TagSerializer(Trend, many = True)
    return Response(serializer.data) 

@api_view(['GET'])
def Popular(request):
    AlreadyFollowing = Following.objects.filter(Follower = request.auth.user.userprofile).values_list('GettingFollowed')
    Profiles = UserProfile.objects.filter(RequirePermissionToFollow=True).annotate(
        Rank=Sum(F('Followers') + 0.5 * F('PostCount'))).order_by('-Rank').exclude(id__in = AlreadyFollowing)[:25]
    serializer = UserProfileSerializer(Profiles, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def AlsoFollow(request, pk):
    CurrentUser = request.auth.user
    try:
        UserToView = User.objects.get(username__iexact=pk)
    except exceptions.ObjectDoesNotExist:
        raise UserDoesNotExist
    AllFollowers = Following.objects.filter(GettingFollowed = UserToView.userprofile).values_list('Follower')
    FollowersAlsoFollow = Following.objects.filter(Follower__in = AllFollowers).annotate(AlsoFollowing = Count('GettingFollowed')).order_by('-AlsoFollowing').values_list('GettingFollowed')
    UserAlradyFollow = Following.objects.filter(Follower = CurrentUser.userprofile).values_list('GettingFollowed_id', flat=True)
    Final = UserProfile.objects.filter(id__in = FollowersAlsoFollow).exclude(id__in = UserAlradyFollow).exclude(id = CurrentUser.userprofile.id)
    serializer = UserProfileSerializer(Final, many = True)
    return Response(serializer.data)


@api_view(['GET'])
def SuggestFollowing(request):

    UserLanguage = LanguageCodes(request.GET.get('lang'))
    if request.auth == None:
        Final = UserProfile.objects.filter(Language = UserLanguage).order_by('-Followers')[:25]
        serializer = UserProfileSerializer(Final, many=True)
        return Response(serializer.data)
    CurrentUser = request.auth.user
    UserFollows = Following.objects.filter(Follower = CurrentUser.userprofile).values_list('GettingFollowed', flat=True)[:25]
    if UserFollows.count()>1:
        OtherPeopleWhoFollow = Following.objects.filter(GettingFollowed__in = UserFollows).annotate(Suggestions = Count('GettingFollowed')).order_by('Suggestions').values_list('GettingFollowed')[:25]
        Final = UserProfile.objects.filter(id__in = OtherPeopleWhoFollow)
        ##print(UserFollows, 'PENIS')
        ##print(OtherPeopleWhoFollow)
        ##print(Final)
        serializer = UserProfileSerializer(Final, many = True, context={'request':request})
        return Response(serializer.data)
    else:
        #print('Cunts')
        AlreadyFollowing = Following.objects.filter(Follower=request.auth.user.userprofile).values_list(
            'GettingFollowed')
        Profiles = UserProfile.objects.filter(RequirePermissionToFollow=False, Language = UserLanguage).annotate(
            Rank=Sum(F('Followers') + 0.5 * F('PostCount'))).order_by('-Rank')[:25]
        serializer = UserProfileSerializer(Profiles, many=True, context={'request':request})
        return Response(serializer.data)


@api_view(['GET'])
def SugegstTrends(request): 
    UserLanguage = LanguageCodes(request.GET.get('lang'))
    if request.auth == None:
        time_threshold = datetime.now(timezone.utc) - timedelta(hours=72)
        AllPosts = Posts.objects.filter(PostedOn__gt = time_threshold, ParentPost = None, Language = UserLanguage).annotate(PopularTags = Count('Tags__Tag')).order_by('PopularTags').values_list('Tags__Tag')[:25]
        #print(AllPosts)
        Trend = Tags.objects.filter(id__in = AllPosts).order_by('-Posts')[:25]
        # annotate(Average = Avg('posts__Vote'))
        serializer = TagSerializer(Trend, many=True)
        return Response(serializer.data)
    CurrentUser = request.auth.user
    time_threshold = datetime.now() - timedelta(hours=36)
    UserFollows = Following.objects.filter(Follower=CurrentUser.userprofile).values_list('GettingFollowed')
    if UserFollows.count()>10:
        OtherPeopleWhoFollow = Following.objects.filter(GettingFollowed__in=UserFollows).values_list('Follower')
        PostsByFollows = Posts.objects.filter(Q(PostedBy__in = UserFollows, PostedOn__gt = time_threshold)|Q(PostedBy__in = OtherPeopleWhoFollow, PostedOn__gt = time_threshold)).annotate(PopularTags = Count('Tags__Tag')).order_by('PopularTags').values_list('Tags__Tag')[:25]

        Tag = Tags.objects.filter(id__in = PostsByFollows)[:25]
        serializer = TagSerializer(Tag, many = True)
        return Response(serializer.data)
    else:
        time_threshold = datetime.now(timezone.utc) - timedelta(hours=72)
        AllPosts = Posts.objects.filter(PostedOn__gt = time_threshold, ParentPost = None, Language = UserLanguage).annotate(PopularTags = Count('Tags__Tag')).order_by('PopularTags').values_list('Tags__Tag')[:25]
        Trend = Tags.objects.filter(id__in = AllPosts).order_by('-Posts')[:25]
        # annotate(Average = Avg('posts__Vote'))
        serializer = TagSerializer(Trend, many=True)
        return Response(serializer.data)

@api_view(['GET'])
def GrowingCommunities(request):
    time_threshold = datetime.now(timezone.utc) - timedelta(hours=24)
    UserLanguage = LanguageCodes(request.GET.get('lang'))
    Memebrs = GroupMembers.objects.filter(Time__gt = time_threshold, Group__AnyOneCanJoin = True).annotate(Rank=Count(F('Group'))).order_by('-Rank').values_list('Group_id', flat=True)
    if request.GET.get('lang'):
        Memebrs = GroupMembers.objects.filter(Time__gt = time_threshold, Group__AnyOneCanJoin = True, Group__Language = UserLanguage).annotate(Rank=Count(F('Group'))).order_by('-Rank').values_list('Group_id', flat=True)
    else:
        Memebrs = GroupMembers.objects.filter(Time__gt = time_threshold, Group__AnyOneCanJoin = True).annotate(Rank=Count(F('Group'))).order_by('-Rank').values_list('Group_id', flat=True)
    Group = Groups.objects.filter(id__in = Memebrs)
    if request.auth == None:
        serializer = GroupSerializer(Group, many=True)
        return Response(serializer.data)
    serializer = GroupSerializer(Group, many = True, context={'request':request})
    return Response(serializer.data)
@api_view(['GET', 'DELETE'])
def GetOnlyComment(request, pk, pk2, pk3, pk4):
    CurrentUser = request.auth.user
    try:
        UserToView = User.objects.get(username__iexact=pk)
        Post = Posts.objects.get(PostedBy=UserToView.userprofile, id=pk2)
        CommentBy = User.objects.get(username__iexact=pk3)
        Comment = Posts.objects.get(PostedBy=CommentBy.userprofile, id=pk4, ParentPost=Post)
    except exceptions.ObjectDoesNotExist:
        raise PostDoesNotExist
    if request.method == "GET":
        serializer = PostSerializerFull(Comment, many=False, context={'request': request})
        if Post.Group:
            try:
                Status = GroupMembers.objects.get(User=CurrentUser.userprofile, Group=Post.Group)
                if Status.Status == 1:
                    return Response(serializer.data)
                elif Status.Status == 2:
                    serializer = PostSerializerFull(Comment, many=False,  context={'request': request, 'auth':True})
                    return Response(serializer.data)
                else:
                    raise Unauthorised
            except exceptions.ObjectDoesNotExist:
                if CurrentUser == UserToView:
                    return Response(serializer.data)
                if Post.Group.PostsArePublic:
                    return Response(serializer.data)
                else:
                    raise Unauthorised
        else:
            if CurrentUser == UserToView:
                return Response(serializer.data)
            else:
                if Post.Public:
                    return Response(serializer.data)
                else:
                    try:
                        Following.objects.get(Follower = CurrentUser.userprofile, GettingFollowed = UserToView.userprofile)
                        return Response(serializer.data)
                    except exceptions.ObjectDoesNotExist:
                        try:
                            Mentions.objects.get(User = CurrentUser.userprofile, Post = Post)
                            return Response(serializer.data)
                        except exceptions.ObjectDoesNotExist:
                            raise Unauthorised
    if Post.PostedBy == CurrentUser.userprofile:
        Comment.delete()
        raise Success
    else:
        if Post.Group:
            try:
                Status = GroupMembers.objects.get(User=CurrentUser.userprofile, Group=Post.Group)
                if Status.Status == 2:
                    Comment.Title = '[REMOVED BY MODERATORS]'
                    Images.objects.filter(Post = Comment).delete()
                    PostBodyText.objects.filter(Post = Comment).delete()
                    PostLink.objects.filter(Post = Comment)
                    Videos.objects.filter(Post = Comment)
                    Comment.save()
                    raise Success
            except exceptions.ObjectDoesNotExist:
                raise Unauthorised
        else:
            raise Unauthorised

@api_view(['POST'])
def RePostComment(request, pk, pk2, pk3, pk4):
    CurrentUser = request.auth.user
    try:
        UserToView = User.objects.get(username__iexact=pk)
        Post = Posts.objects.get(PostedBy=UserToView.userprofile, id=pk2)
        CommentBy = User.objects.get(username__iexact=pk3)
        Comment = Posts.objects.get(PostedBy=CommentBy.userprofile, id=pk4, ParentPost=Post)
    except exceptions.ObjectDoesNotExist:
        raise PostDoesNotExist

    try:
        Following.objects.get(Follower=UserToView.userprofile, GettingFollowed=CurrentUser.userprofile, Status=2)
        raise Blocked
    except exceptions.ObjectDoesNotExist:
        pass
    if Post.Group:
        if Post.Group.PostsArePublic:
            pass
        else:
            raise ServiceUnavailable
    else:
        if Post.Public:
            pass
        else:
            raise Unauthorised
    try:
        Post = Posts.objects.get(PostedBy=CurrentUser.userprofile, RePost=Comment).delete()
        Comment.RePostCount = Comment.RePostCount - 1
        Comment.save()
        return Response(data={"Status": False})
    except exceptions.ObjectDoesNotExist:
        Posts.objects.create(
            PostedBy=CurrentUser.userprofile,
            Title='__Repost__',
            RePost=Comment
        )
        return Response(data={"Status": True})


@api_view(['POST'])
def MentionComment(request, pk, pk2, pk3, pk4):
    CurrentUser = request.auth.user
    Title = request.data.get('Title')
    try:
        time_threshold = datetime.now(timezone.utc) - timedelta(minutes=5)
        Posts.objects.get(PostedBy=CurrentUser.userprofile, Title__iexact=Title, PostedOn__gt=time_threshold)
        raise Spam
    except exceptions.ObjectDoesNotExist:
        pass
    try:
        UserToView = User.objects.get(username__iexact=pk)
        Post = Posts.objects.get(PostedBy=UserToView.userprofile, id=pk2)
        CommentBy = User.objects.get(username__iexact=pk3)
        Comment = Posts.objects.get(PostedBy=CommentBy.userprofile, id=pk4, ParentPost=Post)
    except exceptions.ObjectDoesNotExist:
        raise PostDoesNotExist

    try:
        Following.objects.get(Follower=UserToView.userprofile, GettingFollowed=CurrentUser.userprofile, Status=2)
        raise Blocked
    except exceptions.ObjectDoesNotExist:
        pass
    if Post.Group:
        if Post.Group.PostsArePublic:
            pass
        else:
            raise ServiceUnavailable
    else:
        if Post.Public:
            pass
        else:
            raise Unauthorised
    try:
        Post = Posts.objects.get(PostedBy=CurrentUser.userprofile, RePost=Comment).delete()
        Post.RePostCount = Post.RePostCount - 1
        Post.save()
        return Response(data={"Status": False})
    except exceptions.ObjectDoesNotExist:
        if request.GET.get('Group'):
            try:
                Group = Groups.objects.get(Name = request.GEt.get('Group'))
                try:
                    Status = GroupMembers.objects.get(User = CurrentUser.userprofile, Group = Group)
                    if Status.Status == 1 or Status.Status == 2:
                        pass
                    else:
                        raise Unauthorised
                except exceptions.ObjectDoesNotExist:
                    raise Unauthorised
            except exceptions.ObjectDoesNotExist:
                raise PostDoesNotExist
        else:
            Group = None
        if request.data.get('Poll'):
            serializer = PostCRUD(data=request.data,
                                  context={'request': request, 'PostBody': request.data.pop('PostBody'), 'Link': request.data.get('Link', None), 'Group': Group, 'RePost':Comment})
            if serializer.is_valid():
                serializer.save(
                )
                raise Success
            else:
                raise Invalid
        if request.data.get('Video'):
            serializer = PostCRUDVideo(data=request.data,
                                       context={'request': request, 'PostBody': request.data.pop('PostBody'), 'Link': request.data.get('Link', None), 'Group': Group, 'RePost':Comment})
            ##print('GAYY')
            ##print(request.data)
            if serializer.is_valid():
                serializer.save(
                )
                raise Success
            else:
                raise Invalid
        else:
            serializer = PostCRUD_Image(data=request.data,
                                        context={'request': request, 'PostBody': request.data.pop('PostBody'),
                                                 'Link': request.data.get('Link', None), 'Group': Group, 'RePost':Comment})
            ##print('NAYY')
            ##print(request.data)
            if serializer.is_valid():
                serializer.save(
                    PostedBy=CurrentUser.userprofile,
                )
                raise Success
            else:
                raise Invalid
@api_view(['GET'])
def GetComment(request, pk, pk2, pk3, pk4):
        try:
            UserToView = User.objects.get(username__iexact=pk)
            Post = Posts.objects.get(PostedBy=UserToView.userprofile, id=pk2)
            CommentBy = User.objects.get(username__iexact= pk3)
            Comment  = Posts.objects.get(PostedBy = CommentBy.userprofile, id=pk4, ParentPost = Post)
        except exceptions.ObjectDoesNotExist:
            raise PostDoesNotExist
        QuerySet = []
        QuerySet.append(Comment)
        ##print(Comment.ReplyingTo)
        ##print(QuerySet)
        while Comment.ReplyingTo:
            ##print('PENIS')
            Comment = Posts.objects.get(id=Comment.ReplyingTo.id)
            QuerySet.append(Comment)
        QuerySet.append(Post)

        if request.method == "GET":
            if request.auth == None:
                if Post.Group:
                    if Post.Group.PostsArePublic:
                        serializer = PostSerializerFull(QuerySet, many=True)
                        return Response(serializer.data)
                    else:
                        raise PleaseSignIn
                else:
                    if Post.Public:
                        serializer = PostSerializerFull(QuerySet, many=True)
                        return Response(serializer.data)
            CurrentUser = request.auth.user
            serializer = PostSerializerFull(QuerySet, context={'request': request}, many=True)
            if Post.Group:
                try:
                    Status = GroupMembers.objects.get(User=CurrentUser.userprofile, Group=Post.Group)
                    if Status.Status == 1:
                        return Response(serializer.data)
                    elif Status.Status == 2:
                        serializer = PostSerializerFull(QuerySet, context={'request': request, 'auth': True}, many=True)
                        return Response(serializer.data)
                    else:
                        raise Unauthorised
                except exceptions.ObjectDoesNotExist:
                    if CurrentUser == UserToView:
                        return Response(serializer.data)
                    if Post.Group.PostsArePublic:
                        return Response(serializer.data)
                    else:
                        raise Unauthorised
            else:
                if CurrentUser == UserToView:
                    return Response(serializer.data)
                else:
                    if Post.Public:
                        return Response(serializer.data)
                    else:
                        try:
                            Following.objects.get(Follower=CurrentUser.userprofile,
                                                  GettingFollowed=UserToView.userprofile)
                            return Response(serializer.data)
                        except exceptions.ObjectDoesNotExist:
                            try:
                                Mentions.objects.get(User=CurrentUser.userprofile, Post=Post)
                                return Response(serializer.data)
                            except exceptions.ObjectDoesNotExist:
                                raise Unauthorised

@api_view(['GET', 'POST'])
def GetCommentReplies(request, pk, pk2, pk3, pk4):

    try:
        UserToView = User.objects.get(username__iexact=pk)
        Post = Posts.objects.get(PostedBy=UserToView.userprofile, id=pk2)
        CommentBy = User.objects.get(username__iexact=pk3)
        Comment = Posts.objects.get(PostedBy=CommentBy.userprofile, id=pk4, ParentPost=Post)
    except exceptions.ObjectDoesNotExist:
        raise PostDoesNotExist
    if request.method == 'GET':

        limit = int(request.GET.get('limit', 32))
        offset = int(request.GET.get('offset', 0))
        if limit>64:
            limit=64
        if request.GET.get('order') == 'best':
            OrderBy = '-Vote'
        elif request.GET.get('order') == 'new':
            OrderBy = '-id'
        Replies = Posts.objects.filter(ReplyingTo=Comment).prefetch_related('PostImages', 'Poll', 'ParentPost', 'RePost', 'ParentPost', 'ReplyingTo', 'ParentPost', 'PostImages', 'Group', 'Likes').select_related('Video', 'PostBody', 'PostLink', 'OverWatchFinalOutcome').order_by(OrderBy)[offset:limit+offset]
        if Post.Group:
            if Post.Group.PostsArePublic:
                serializer = PostSerializerFull(Replies, many=True)
                return Response(serializer.data)
            else:
                raise PleaseSignIn
        else:
            if Post.Public:
                serializer = PostSerializerFull(Replies, many=True)
                return Response(serializer.data)

        CurrentUser = request.auth.user
        serializer = PostSerializer(Replies, many = True, context={'request': request})
        if Post.Group:
            try:
                Status = GroupMembers.objects.get(User=CurrentUser.userprofile, Group=Post.Group)
                if Status.Status == 1:
                    return Response(serializer.data)
                elif Status.Status == 2:
                    serializer = PostSerializer(Replies, context={'request': request, 'auth':True}, many=True)
                    return Response(serializer.data)
                else:
                    raise Unauthorised
            except exceptions.ObjectDoesNotExist:
                if CurrentUser == UserToView:
                    return Response(serializer.data)
                if Post.Group.PostsArePublic:
                    return Response(serializer.data)
                else:
                    raise Unauthorised
        else:
            if CurrentUser == UserToView:
                return Response(serializer.data)
            else:
                if Post.Public:
                    return Response(serializer.data)
                else:
                    try:
                        Following.objects.get(Follower = CurrentUser.userprofile, GettingFollowed = UserToView.userprofile)
                        return Response(serializer.data)
                    except exceptions.ObjectDoesNotExist:
                        try:
                            Mentions.objects.get(User = CurrentUser.userprofile, Post = Post)
                            return Response(serializer.data)
                        except exceptions.ObjectDoesNotExist:
                            raise Unauthorised
    if request.method == "POST":
        Title = request.data.get('Title')
        CurrentUser = request.auth.user
        try:
            time_threshold = datetime.now(timezone.utc) - timedelta(minutes=5)
            Posts.objects.get(PostedBy=CurrentUser.userprofile, Title__iexact=Title, PostedOn__gt=time_threshold)
            raise Spam
        except exceptions.ObjectDoesNotExist:
            pass
        try:
            Following.objects.get(Follower=UserToView.userprofile, GettingFollowed=CurrentUser.userprofile, Status=2)
            raise Blocked
        except exceptions.ObjectDoesNotExist:
            pass
        if Post.Group:
            try:
                Status = GroupMembers.objects.get(
                    User = CurrentUser.userprofile,
                    Group = Post.Group
                )
                if Status.Status == 1:
                    pass
                elif Status.Status ==2:
                    pass
            except exceptions.ObjectDoesNotExist:
                raise Unauthorised
        else:
            if UserToView == CurrentUser:
                pass
            else:
                if Post.WhoCanComment == 2:
                    pass
                if Post.WhoCanComment == 1:
                    try:
                        Mentions.objects.get(User = CurrentUser.userprofile, Post = Post)
                        pass
                    except exceptions.ObjectDoesNotExist:
                        raise Unauthorised
                if Post.WhoCanComment == 0:
                    try:
                        Following.objects.get(Follower = CurrentUser.userprofile, GettingFollowed = UserToView.userprofile)
                        pass
                    except exceptions.ObjectDoesNotExist:
                        try:
                            Mentions.objects.get(User=CurrentUser.userprofile, Post=Post)
                            pass
                        except exceptions.ObjectDoesNotExist:
                            raise Unauthorised
        if request.data.get('Poll'):
            ##print('AYY')
            ##print(request.data)
            serializer = PostCRUD(data=request.data,context={'request': request,'Link': request.data.get('Link', None), 'ParentPost':Post, 'ReplyingTo':Comment})
            if serializer.is_valid():
                serializer.save()
                raise Success
            else:
                raise Invalid
        if request.data.get('Video'):
            serializer = PostCRUDVideo(data=request.data,context={'request': request,'Link': request.data.get('Link', None), 'ParentPost':Post, 'ReplyingTo':Comment})
            ##print('GAYY')
            ##print(request.data)
            if serializer.is_valid():
                serializer.save()
                raise Success
            else:
                raise Invalid
        else:
            serializer = PostCRUD_Image(data=request.data,context={'request': request,'Link': request.data.get('Link', None), 'ParentPost':Post, 'ReplyingTo':Comment})
            ##print('NAYY')
            ##print(request.data)
            if serializer.is_valid():
                serializer.save(
                    PostedBy=CurrentUser.userprofile,
                )
                raise Success
            else:
                raise Invalid


@api_view(['POST'])
def VoteOnPoll(request, pk, pk2):
    ##print(request.auth.user)
    CurrentUser = request.auth.user
    try:
        UserToView = User.objects.get(username__iexact=pk)
        Post = Posts.objects.get(PostedBy=UserToView.userprofile, id=pk2)
    except exceptions.ObjectDoesNotExist:
        raise PostDoesNotExist
    try:
        Following.objects.get(Follower=UserToView.userprofile, GettingFollowed=CurrentUser.userprofile, Status=2)
        raise Blocked
    except exceptions.ObjectDoesNotExist:
        pass
    if Post.ParentPost:
        ParentPost = Post.ParentPost
        if ParentPost.Group:
            if CurrentUser == UserToView:
                pass
            else:
                if ParentPost.Group.PostsArePublic:
                    pass
                else:
                    try:
                        Status = GroupMembers.objects.get(User=CurrentUser.userprofile, Group=ParentPost.Group)
                        if Status.Status == 1 or Status.Status == 2:
                            pass
                        else:
                            raise Unauthorised
                    except exceptions.ObjectDoesNotExist:
                        raise Unauthorised
        else:
            if CurrentUser==ParentPost.PostedBy:
                pass
            else:

                if Post.ParentPost.Public:
                    pass
                else:
                    try:
                        Following.objects.get(Follower = CurrentUser.userprofile, GettingFollowed = Post.ParentPost.PostedBy)
                        pass
                    except exceptions.ObjectDoesNotExist:
                        try:
                            Mentions.objects.get(User = CurrentUser.userprofile, Post = Post.ParentPost)
                            pass
                        except exceptions.ObjectDoesNotExist:
                            raise Unauthorised

    else:
        if Post.Group:
            if CurrentUser == UserToView:
                pass
            else:
                if Post.Group.PostsArePublic:
                    pass
                else:
                    try:
                        Status = GroupMembers.objects.get(User=CurrentUser.userprofile, Group=Post.Group)
                        if Status.Status == 1 or Status.Status == 2:
                           pass
                        else:
                            raise Unauthorised
                    except exceptions.ObjectDoesNotExist:
                        raise Unauthorised
        else:
            if CurrentUser==UserToView:
                pass
            else:
                if request.method == 'POST':
                    if Post.Public:
                        pass
                    else:
                        try:
                            Following.objects.get(Follower = CurrentUser.userprofile, GettingFollowed = UserToView.userprofile)
                            pass
                        except exceptions.ObjectDoesNotExist:
                            try:
                                Mentions.objects.get(User = CurrentUser.userprofile, Post = Post)
                                pass
                            except exceptions.ObjectDoesNotExist:
                                raise Unauthorised
    try:
        Votes.objects.get(User = CurrentUser.userprofile, Post = Post)
        raise AlreadyVoted
    except exceptions.ObjectDoesNotExist:
        serializer = VoteSerializer(data = request.data)
        if serializer.is_valid():
            serializer.save(
                Post = Post,
                User = CurrentUser.userprofile
            )
            raise Success
        else:
            raise Invalid
@api_view(['POST'])
def RePost(request, pk, pk2):
    CurrentUser = request.auth.user
    try:
        UserToView = User.objects.get(username__iexact=pk)
        Post = Posts.objects.get(PostedBy=UserToView.userprofile, id=pk2)
    except exceptions.ObjectDoesNotExist:
        raise PostDoesNotExist
    try:
        Following.objects.get(Follower=UserToView.userprofile, GettingFollowed=CurrentUser.userprofile, Status=2)
        raise Blocked
    except exceptions.ObjectDoesNotExist:
        pass
    if Post.Group:
        if Post.Group.PostsArePublic:
            pass
        else:
            raise ServiceUnavailable
    else:
        if Post.Public:
            pass
        else:
            raise Unauthorised
    try:
        Posts.objects.get(PostedBy=CurrentUser.userprofile, RePost=Post).delete()
        Post.RePostCount = Post.RePostCount - 1
        Post.save()
        return Response(data={"Status": False})
    except exceptions.ObjectDoesNotExist:
        Posts.objects.create(
            PostedBy=CurrentUser.userprofile,
            Title='__Repost__',
            RePost=Post
        )
        return Response(data={"Status": True})

@api_view(['POST'])
def Mention(request, pk, pk2):
    CurrentUser = request.auth.user
    #print(request.data)
    Title = request.data.get('Title')
    try:
        time_threshold = datetime.now(timezone.utc) - timedelta(minutes=5)
        Posts.objects.get(PostedBy=CurrentUser.userprofile, Title__iexact=Title, PostedOn__gt=time_threshold)
        raise Spam
    except exceptions.ObjectDoesNotExist:
        pass
    try:
        UserToView = User.objects.get(username__iexact=pk)
        Post = Posts.objects.get(PostedBy=UserToView.userprofile, id=pk2)
    except exceptions.ObjectDoesNotExist:
        raise PostDoesNotExist
    try:
        Following.objects.get(Follower=UserToView.userprofile, GettingFollowed=CurrentUser.userprofile, Status=2)
        raise Blocked
    except exceptions.ObjectDoesNotExist:
        pass
    if Post.Group:
        if Post.Group.PostsArePublic:
            pass
        else:
            raise ServiceUnavailable
    else:
        if Post.Public:
            pass
        else:
            raise Unauthorised
    try:
        Posts.objects.get(PostedBy=CurrentUser.userprofile, RePost=Post).delete()
        Post.RePostCount = Post.RePostCount - 1
        Post.save()
        return Response(data={"Status": False})
    except exceptions.ObjectDoesNotExist:
        if request.GET.get('Group'):
            try:
                Group = Groups.objects.get(Name = request.GET.get('Group'))
                try:
                    Status = GroupMembers.objects.get(User = CurrentUser.userprofile, Group = Group)
                    if Status.Status == 1 or Status.Status == 2:
                        pass
                    else:
                        raise Unauthorised
                except exceptions.ObjectDoesNotExist:
                    raise Unauthorised
            except exceptions.ObjectDoesNotExist:
                raise PostDoesNotExist
        else:
            Group = None
        if request.data.get('Poll'):
            serializer = PostCRUD(data=request.data,
                                  context={'request': request, 'PostBody': request.data.pop('PostBody'), 'Link': request.data.get('Link', None), 'Group': Group, 'RePost':Post})
            if serializer.is_valid():
                serializer.save(
                )
                raise Success
            else:
                raise Invalid
        if request.data.get('Video'):
            serializer = PostCRUDVideo(data=request.data,
                                       context={'request': request, 'PostBody': request.data.pop('PostBody'), 'Link': request.data.get('Link', None), 'Group': Group, 'RePost':Post})
            ##print('GAYY')
            ##print(request.data)
            if serializer.is_valid():
                serializer.save(
                )
                raise Success
            else:
                raise Invalid
        else:
            serializer = PostCRUD_Image(data=request.data,
                                        context={'request': request, 'PostBody': request.data.pop('PostBody'),
                                                 'Link': request.data.get('Link', None), 'Group': Group, 'RePost':Post})
            ##print('NAYY')
            ##print(request.data)
            if serializer.is_valid():
                serializer.save(
                    PostedBy=CurrentUser.userprofile,
                )
                raise Success
            else:
                raise Invalid



@api_view(['GET'])
def GetNotifications(request):
    if request.auth == None:
        raise PleaseSignIn
    CurrentUser = request.auth.user
    limit = int(request.GET.get('limit', 32))
    offset = int(request.GET.get('offset', 0))
    if limit>64:
        limit=64
    Notification = Notifications.objects.filter(User = CurrentUser.userprofile).order_by('id')[offset:limit+offset]
    serializer = NotificationSerialzier(Notification, many = True)
    return Response(serializer.data)

@api_view(['POST'])
def Notify(request, pk):
    CurrentUser = request.auth.user
    try:
        UserToView = User.objects.get(username__iexact= pk)
    except exceptions.ObjectDoesNotExist:
        raise UserDoesNotExist
    try:
        rev = Following.objects.get(Follower = CurrentUser.userprofile, GettingFollowed = UserToView.userprofile)
        try:
            notif = NotifyPosts.objects.get(Users = rev)
            notif.delete()
            return Response(data={"Status": False})
        except exceptions.ObjectDoesNotExist:
            NotifyPosts.objects.create(
                Users = rev
            )
            return Response(data={"Status": True})
    except exceptions.ObjectDoesNotExist:
        raise Unauthorised

@api_view(['GET'])
def MyPosts(request):
    CurrentUser = request.auth.user
    Post = Posts.objects.filter(PostedBy = CurrentUser.userprofile).order_by('-id').prefetch_related('PostImages', 'Poll', 'ParentPost', 'RePost', 'ParentPost', 'ReplyingTo', 'ParentPost', 'PostImages', 'Group', 'Likes').select_related('Video', 'PostBody', 'PostLink', 'OverWatchFinalOutcome')
    serializer = PostSerializer(Post, many = True, context={'request':request})
    return Response(serializer.data)

@api_view(['POST'])
def SavePost(request, pk, pk2):
    try:
        UserToView = User.objects.get(username__iexact=pk)
        Post = Posts.objects.get(PostedBy=UserToView.userprofile, id=pk2, ParentPost = None)
    except exceptions.ObjectDoesNotExist:
        raise PostDoesNotExist
    CurrentUser = request.auth.user
    if Post.Group:
        try:
            Status = GroupMembers.objects.get(User=CurrentUser.userprofile, Group=Post.Group)
            if Status.Status == 1 or Status.Status == 2:
                pass
            else:
                if Post.Group.PostsArePublic:
                    pass
                else:
                    try:
                        Mentions.objects.get(User=CurrentUser.userprofile, Post=Post)
                        pass
                    except exceptions.ObjectDoesNotExist:
                        raise Unauthorised
        except exceptions.ObjectDoesNotExist:
            if CurrentUser == UserToView:
                pass
            else:
                if Post.Group.PostsArePublic:
                    pass
                else:
                    raise Unauthorised
    else:
        if CurrentUser == UserToView:
            pass
        else:
            if Post.Public:
                pass
            else:
                try:
                    Following.objects.get(Follower=CurrentUser.userprofile, GettingFollowed=UserToView.userprofile)
                    pass
                except exceptions.ObjectDoesNotExist:
                    try:
                        Mentions.objects.get(User=CurrentUser.userprofile, Post=Post)
                        pass
                    except exceptions.ObjectDoesNotExist:
                        ##print('PENIS')
                        raise ServiceUnavailable
    try:
        Saved.objects.get(Post = Post, User = CurrentUser.userprofile).delete()
        return Response(data={"Status": False})
    except exceptions.ObjectDoesNotExist:
        Saved.objects.create(
            Post = Post,
            User = CurrentUser.userprofile)
        return Response(data={"Status": True})

@api_view(['POST'])
def SaveComment(request, pk, pk2, pk3, pk4):
    CurrentUser = request.auth.user
    try:
        UserToView = User.objects.get(username__iexact=pk)
        Post = Posts.objects.get(PostedBy=UserToView.userprofile, id=pk2)
        CommentBy = User.objects.get(username__iexact=pk3)
        Comment = Posts.objects.get(PostedBy=CommentBy.userprofile, id=pk4, ParentPost=Post)
    except exceptions.ObjectDoesNotExist:
        raise PostDoesNotExist
    try:
        UserToView = User.objects.get(username__iexact=pk)
        Post = Posts.objects.get(PostedBy=UserToView.userprofile, id=pk2, ParentPost = None)
    except exceptions.ObjectDoesNotExist:
        raise PostDoesNotExist
    CurrentUser = request.auth.user
    if Post.Group:
        try:
            Status = GroupMembers.objects.get(User=CurrentUser.userprofile, Group=Post.Group)
            if Status.Status == 1 or Status.Status == 2:
                pass
            else:
                if Post.Group.PostsArePublic:
                    pass
                else:
                    try:
                        Mentions.objects.get(User=CurrentUser.userprofile, Post=Post)
                        pass
                    except exceptions.ObjectDoesNotExist:
                        raise Unauthorised
        except exceptions.ObjectDoesNotExist:
            if CurrentUser == UserToView:
                pass
            else:
                if Post.Group.PostsArePublic:
                    pass
                else:
                    raise Unauthorised
    else:
        if CurrentUser == UserToView:
            pass
        else:
            if Post.Public:
                pass
            else:
                try:
                    Following.objects.get(Follower=CurrentUser.userprofile, GettingFollowed=UserToView.userprofile)
                    pass
                except exceptions.ObjectDoesNotExist:
                    try:
                        Mentions.objects.get(User=CurrentUser.userprofile, Post=Post)
                        pass
                    except exceptions.ObjectDoesNotExist:
                        raise ServiceUnavailable
    try:
        Saved.objects.get(Post = Comment, User = CurrentUser.userprofile).delete()
        return Response(data={"Status": False})
    except exceptions.ObjectDoesNotExist:
        Saved.objects.create(
            Post = Comment,
            User = CurrentUser.userprofile)
        return Response(data={"Status": True})

@api_view(['DELETE'])
def DeletePost(request, pk):
    CurrentUser = request.auth.user
    try:
        Post = Posts.objects.get(id=pk)
    except exceptions.ObjectDoesNotExist:
        raise PostDoesNotExist
    if CurrentUser.userprofile == Post.PostedBy:
        Post.delete()
        raise Success
    else:
        raise Unauthorised

@api_view(['GET'])
def UsersFollowers(request, pk):
    try:
        UserToView = User.objects.get(username__iexact=pk)
    except exceptions.ObjectDoesNotExist:
        raise UserDoesNotExist
    Follower = Following.objects.filter(GettingFollowed = UserToView.userprofile).values_list('Follower')
    limit = int(request.GET.get('limit', 32))
    offset = int(request.GET.get('offset', 0))
    if limit>64:
        limit=64
    user = UserProfile.objects.filter(id__in = Follower)[offset:limit+offset]
    if request.auth == None:
        serializer = UserProfileSerializer(user, many=True)
        return Response(serializer.data)
    serializer = UserProfileSerializer(user, many = True, context={'request':request})
    return Response(serializer.data)

@api_view(['GET'])
def UserFollowsByPeopleIKnow(request, pk):
    try:
        UserToView = User.objects.get(username__iexact=pk)
    except exceptions.ObjectDoesNotExist:
        raise UserDoesNotExist
    CurrentUser = request.auth.user
    limit = int(request.GET.get('limit', 32))
    offset = int(request.GET.get('offset', 0))
    if limit>64:
        limit=64
    UserFollows = Following.objects.filter(Follower = CurrentUser.userprofile).values_list('GettingFollowed')
    Follower = Following.objects.filter(GettingFollowed=UserToView.userprofile, Follower__in = UserFollows).values_list('Follower')
    user = UserProfile.objects.filter(id__in=Follower)[offset:limit+offset]
    serializer = UserProfileSerializer(user, many=True,  context={'request':request} )
    return Response(serializer.data)


@api_view(['GET'])
def PostLikedBy(request, pk, pk2):
    limit = int(request.GET.get('limit', 32))
    offset = int(request.GET.get('offset', 0))
    try:
        UserToView = User.objects.get(username__iexact=  pk)
        Post = Posts.objects.get(PostedBy = UserToView.userprofile, id=pk2)
        LikedBy = PostLikes.objects.filter(Post = Post, Post__PostedBy = UserToView.userprofile , Post__ParentPost=None).order_by('-id').values_list('User_id', flat=True)[offset:limit+offset]
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(LikedBy)])
    except exceptions.ObjectDoesNotExist:
        raise PostDoesNotExist
    if limit>64:
        limit=64
    Users = UserProfile.objects.filter(id__in=LikedBy).order_by(preserved)
    serializer = UserProfileSerializer(Users, many = True, context={'request':request})
    if request.auth == None:
        serializer = UserProfileSerializer(Users, many=True)
        if Post.Group:
            if Post.Group.PostsArePublic:
                return Response(serializer.data)
            else:
                raise NotAllowed
        else:
            if Post.Public:
                return Response(serializer.data)
            else:
                raise NotAllowed
    serializer = UserProfileSerializer(Users, many=True, context={'request': request})
    if Post.Group:
        if Post.Group.PostsArePublic:
            return Response(serializer.data)
        else:
            raise NotAllowed
    else:
        if Post.Public:
            return Response(serializer.data)
        else:
            raise NotAllowed

@api_view(['GET'])
def ReplyLikedBy(request, pk, pk2, pk3, pk4):
    limit = int(request.GET.get('limit', 32))
    offset = int(request.GET.get('offset', 0))
    if limit>64:
        limit=64
    try:
        UserToView = User.objects.get(username__iexact= pk)
        Post = Posts.objects.get(id=pk2, PostedBy = UserToView.userprofile)
        LikedBy = PostLikes.objects.filter(Post__id = pk4, Post__ParentPost__PostedBy__user__username = pk, Post__PostedBy__user__username = pk3, Post__ParentPost=pk2).order_by('-id').values_list('User_id', flat=True)[offset:offset+limit]
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(LikedBy)])
    except exceptions.ObjectDoesNotExist:
        raise PostDoesNotExist
    Users = UserProfile.objects.filter(id__in=LikedBy).order_by(preserved)
    serializer = UserProfileSerializer(Users, many=True, context={'request': request})
    if request.auth == None:
        serializer = UserProfileSerializer(Users, many=True)
        if Post.Group:
            if Post.Group.PostsArePublic:
                return Response(serializer.data)
            else:
                raise NotAllowed
        else:
            if Post.Public:
                return Response(serializer.data)
            else:
                raise NotAllowed
    serializer = UserProfileSerializer(Users, many=True, context={'request': request})
    if Post.Group:
        if Post.Group.PostsArePublic:
            return Response(serializer.data)
        else:
            raise NotAllowed
    else:
        if Post.Public:
            return Response(serializer.data)
        else:
            raise NotAllowed

    if Post.Group:
        if Post.Group.PostsArePublic:
            return Response(serializer.data)
        else:
            raise NotAllowed
    else:
        if Post.Public:
            return Response(serializer.data)
        else:
            raise NotAllowed

@api_view(['GET'])
def RePostedBy(request, pk, pk2):
    try:
        UserToView = User.objects.get(username__iexact= pk)
        Post = Posts.objects.get(id=pk2, PostedBy = UserToView.userprofile)
        RePost = Posts.objects.filter(RePost = Post, RePost__PostedBy__user__username = pk).values_list('PostedBy_id')
    except exceptions.ObjectDoesNotExist:
        raise PostDoesNotExist
    limit = int(request.GET.get('limit', 32))
    offset = int(request.GET.get('offset', 0))
    if limit>64:
        limit=64
    Users = UserProfile.objects.filter(id__in=RePost).order_by('-Followers')[offset:offset+limit]
    serializer = UserProfileSerializer(Users, many=True, context={'request': request})
    if request.auth == None:
        serializer = UserProfileSerializer(Users, many=True)
        if Post.Group:
            if Post.Group.PostsArePublic:
                return Response(serializer.data)
            else:
                raise NotAllowed
        else:
            if Post.Public:
                return Response(serializer.data)
            else:
                raise NotAllowed
    serializer = UserProfileSerializer(Users, many=True, context={'request': request})
    if Post.Group:
        if Post.Group.PostsArePublic:
            return Response(serializer.data)
        else:
            raise NotAllowed
    else:
        if Post.Public:
            return Response(serializer.data)
        else:
            raise NotAllowed
    if Post.Group:
        if Post.Group.PostsArePublic:
            return Response(serializer.data)
        else:
            raise NotAllowed
    else:
        if Post.Public:
            return Response(serializer.data)
        else:
            raise NotAllowed

@api_view(['GET'])
def UserMentions(request, pk):
    try:
        UserToView = User.objects.get(username__iexact=pk)
    except exceptions.ObjectDoesNotExist:
        raise UserDoesNotExist
    Mention = Mentions.objects.filter(User = UserToView.userprofile).values_list('Post', flat=True)
    limit = int(request.GET.get('limit', 32))
    offset = int(request.GET.get('offset', 0))
    if limit>64:
        limit=64
    Post = Posts.objects.filter(Q(id__in = Mention, ParentPost = None, Public = True, Group = None)|Q(id__in = Mention, ParentPost__Public = True, Group = None)|Q(id__in = Mention, Group__PostsArePublic=True)).prefetch_related('PostImages', 'Poll', 'ParentPost', 'RePost', 'ParentPost', 'ReplyingTo', 'ParentPost', 'PostImages', 'Group', 'Likes').select_related('Video', 'PostBody', 'PostLink', 'OverWatchFinalOutcome')[offset: limit+offset]

    serializer = PostSerializer(Post, many=True, context={'request':request})
    return Response(serializer.data)



@api_view(['GET'])
def GetSavedPosts(request):
    CurrentUser = request.auth.user
    limit = int(request.GET.get('limit', 32))
    offset = int(request.GET.get('offset', 0))
    if limit>64:
        limit=64
    Post = Posts.objects.filter(
        Saves__User = CurrentUser.userprofile
    ).order_by('-Saves').prefetch_related('PostImages', 'Poll', 'ParentPost', 'RePost', 'ParentPost', 'ReplyingTo', 'ParentPost', 'PostImages', 'Group', 'Likes').select_related('Video', 'PostBody', 'PostLink', 'OverWatchFinalOutcome')[offset:limit+offset]
    serializer = PostSerializer(Post, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
def GetFollowing(request, pk):
    try:
        UserToView = User.objects.get(username__iexact=pk)
    except exceptions.ObjectDoesNotExist:
        raise UserDoesNotExist
    Followin = Following.objects.filter(Follower = UserToView.userprofile).values_list('GettingFollowed_id')
    limit = int(request.GET.get('limit', 32))
    offset = int(request.GET.get('offset', 0))
    if limit>64:
        limit=64
    Profiles = UserProfile.objects.filter(id__in = Followin)[offset:limit+offset]
    if request.auth == None:
        serializer = UserProfileSerializer(Profiles, many=True)
        return Response(serializer.data)
    serializer = UserProfileSerializer(Profiles, many = True, context={'request':request})
    return Response(serializer.data)

@api_view(['GET'])
def ReplyRePostedBy(request, pk, pk2, pk3, pk4):
    try:
        UserToView = User.objects.get(username__iexact= pk)
        Post = Posts.objects.get(PostedBy = UserToView.userprofile, id = pk2)
        ReplyPostedBy = User.objects.get(username__iexact= pk3)
        Reply = Posts.objects.get(PostedBy=ReplyPostedBy.userprofile, id=pk4, ParentPost = Post)
        RePost = Posts.objects.filter(RePost=Reply).values_list('PostedBy_id')

    except exceptions.ObjectDoesNotExist:
        raise PostDoesNotExist
    limit = int(request.GET.get('limit', 32))
    offset = int(request.GET.get('offset', 0))
    if limit>64:
        limit=64
    Users = UserProfile.objects.filter(id__in=RePost).order_by('-Followers')[offset:offset+limit]
    serializer = UserProfileSerializer(Users, many=True, context={'request': request})
    if request.auth == None:
        serializer = UserProfileSerializer(Users, many=True)
        if Post.Group:
            if Post.Group.PostsArePublic:
                return Response(serializer.data)
            else:
                raise NotAllowed
        else:
            if Post.Public:
                return Response(serializer.data)
            else:
                raise NotAllowed
    serializer = UserProfileSerializer(Users, many=True, context={'request': request})
    if Post.Group:
        if Post.Group.PostsArePublic:
            return Response(serializer.data)
        else:
            raise NotAllowed
    else:
        if Post.Public:
            return Response(serializer.data)
        else:
            raise NotAllowed
    if Post.Group:
        if Post.Group.PostsArePublic:
            return Response(serializer.data)
        else:
            raise NotAllowed
    else:
        if Post.Public:
            return Response(serializer.data)
        else:
            raise NotAllowed

@api_view(['GET'])
def ModToolsProfileOverView(request, pk, pk2):
    try:
        Group = Groups.objects.get(Name=pk)
        UserToView = User.objects.get(username__iexact=pk2)
    except exceptions.ObjectDoesNotExist:
        return UserDoesNotExist
    CurrentUser = request.auth.user
    try:
        GroupMembers.objects.get(Group = Group, User = CurrentUser.userprofile, Status=2)
    except exceptions.ObjectDoesNotExist:
        raise Unauthorised
    serializer = ModToolsUserSerializer(UserToView.userprofile, many = False,context={'request':request, 'Group':Group})
    return Response(serializer.data)

@api_view(['GET'])
def ModToolsProfileOverView_Posts(request, pk, pk2):
    try:
        Group = Groups.objects.get(Name=pk)
        UserToView = User.objects.get(username__iexact=pk2)
    except exceptions.ObjectDoesNotExist:
        return UserDoesNotExist
    CurrentUser = request.auth.user
    try:
        GroupMembers.objects.get(Group = Group, User = CurrentUser.userprofile)
    except exceptions.ObjectDoesNotExist:
        raise Unauthorised
    limit = int(request.GET.get('limit', 32))
    offset = int(request.GET.get('offset', 0))
    if limit>64:
        limit=64
    Post = Posts.objects.filter(Group = Group, PostedBy = UserToView.userprofile).prefetch_related('PostImages', 'Poll', 'ParentPost', 'RePost', 'ParentPost', 'ReplyingTo', 'ParentPost', 'PostImages', 'Group', 'Likes').select_related('Video', 'PostBody', 'PostLink', 'OverWatchFinalOutcome')[offset:limit+offset]
    serializer = PostSerializer(Post, many = True,context={'request':request, 'auth':True})
    return Response(serializer.data)

@api_view(['POST'])
def ModTools_Accept(request, pk, pk2):
    try:
        Group = Groups.objects.get(Name=pk)
        UserToView = User.objects.get(username__iexact=pk2)
    except exceptions.ObjectDoesNotExist:
        return UserDoesNotExist
    CurrentUser = request.auth.user
    try:
        GroupMembers.objects.get(Group = Group, User = CurrentUser.userprofile, Status = 2)
    except exceptions.ObjectDoesNotExist:
        raise Unauthorised
    try:
        Initial = GroupMembers.objects.get(Group = Group, User = UserToView.userprofile, Status = 0)
        Initial.Status = 1
        Initial.save()
        return Response(data={'Status': 1})
    except exceptions.ObjectDoesNotExist:
        raise Unauthorised


@api_view(['POST'])
def ModTools_Kick(request, pk, pk2):
    try:
        Group = Groups.objects.get(Name=pk)
        UserToView = User.objects.get(username__iexact=pk2)
    except exceptions.ObjectDoesNotExist:
        return UserDoesNotExist
    CurrentUser = request.auth.user
    try:
        GroupMembers.objects.get(Group = Group, User = CurrentUser.userprofile, Status = 2)
    except exceptions.ObjectDoesNotExist:
        raise Unauthorised
    try:
        Initial = GroupMembers.objects.filter(Group = Group, User = UserToView.userprofile, Status = 1)
        Initial.update(Status = 3)
        Notifications.objects.create(
            User=UserToView.userprofile,
            Type='Kick',
            Group=Group,
            Created=datetime.now(timezone.utc)
        )
    except exceptions.ObjectDoesNotExist:
        raise Unauthorised
    return Response(data={'Status':3})

@api_view(['POST'])
def ModTools_Makemod(request, pk, pk2):
    try:
        Group = Groups.objects.get(Name=pk)
        UserToView = User.objects.get(username__iexact=pk2)
    except exceptions.ObjectDoesNotExist:
        return UserDoesNotExist
    CurrentUser = request.auth.user
    try:
        GroupMembers.objects.get(Group = Group, User = CurrentUser.userprofile, Status = 2)
    except exceptions.ObjectDoesNotExist:
        raise Unauthorised
    try:
        Initial = GroupMembers.objects.filter(Group = Group, User = UserToView.userprofile, Status = 1)
        Initial.update(Status = 2)
    except exceptions.ObjectDoesNotExist:
        raise Unauthorised
    return Response(data={'Status':2})

@api_view(['POST'])
def ModTools_UnKick(request, pk, pk2):
    try:
        Group = Groups.objects.get(Name=pk)
        UserToView = User.objects.get(username__iexact=pk2)
    except exceptions.ObjectDoesNotExist:
        return UserDoesNotExist
    CurrentUser = request.auth.user
    try:
        GroupMembers.objects.get(Group = Group, User = CurrentUser.userprofile, Status = 2)
    except exceptions.ObjectDoesNotExist:
        raise Unauthorised
    try:
        Initial = GroupMembers.objects.get(Group = Group, User = UserToView.userprofile, Status = 3)
        Initial.Status = 1
        Initial.save()
    except exceptions.ObjectDoesNotExist:
        raise Unauthorised
    return Response(data={'Status':1})


@api_view(['GET'])
def ModTools_Members(request, pk):
    try:
        Group = Groups.objects.get(Name=pk)
    except exceptions.ObjectDoesNotExist:
        return UserDoesNotExist
    CurrentUser = request.auth.user
    try:
        Status = GroupMembers.objects.get(Group = Group, User = CurrentUser.userprofile, Status = 2)
    except exceptions.ObjectDoesNotExist:
        raise Unauthorised
    Type = request.GET.get('type', '')
    if Type == 'banned':
        MemebersList = GroupMembers.objects.filter(Group = Group, Status = 3)
        serializer = GroupMemberSerializer(MemebersList, many = True, context={'request':request})
        return Response(serializer.data)
    elif Type == 'pending':
        MemebersList = GroupMembers.objects.filter(Group=Group, Status=0)
        serializer = GroupMemberSerializer(MemebersList, many = True, context={'request':request})
        return Response(serializer.data)


@api_view(['GET'])
def GetCollection(request, pk):
    try:
        Collection = Collections.objects.get(Name = pk)
    except exceptions.ObjectDoesNotExist:
        raise UserDoesNotExist
    if request.auth == None:
        serializer = CollectionSerializer(Collection, many=False)
        return Response(serializer.data)
    serializer = CollectionSerializer(Collection, many = False, context = {'request':request})
    return Response(serializer.data)

@api_view(['GET'])
def GetCollectionMembers(request, pk):
    try:
        Collection = Collections.objects.get(Name = pk)
    except exceptions.ObjectDoesNotExist:
        raise Unauthorised
    limit = int(request.GET.get('limit', 32))
    offset = int(request.GET.get('offset', 0))
    if limit>64:
        limit=64

    Members = UserProfile.objects.filter(PartOf__Collection = Collection)[offset:offset+limit]
    if request.auth == None:
        serializer = UserProfileSerializer(Members, many=True)
        return Response(serializer.data)
    CurrentUser = request.auth.user
    serializer = UserProfileSerializer(Members, many = True, context = {'request':request})
    return Response(serializer.data)

@api_view(['POST'])
def AddCollectionMember(request, pk, pk2):
    CurrentUser = request.auth.user
    try:
        Collection = Collections.objects.get(Name = pk, CreatedBy = CurrentUser.userprofile)
        UserToView = User.objects.get(username__iexact= pk2)
    except exceptions.ObjectDoesNotExist:
        raise UserDoesNotExist
    if Collection.CreatedBy == CurrentUser.userprofile and UserToView.userprofile.RequirePermissionToFollow == False:
        CollectionPosts.objects.create(
            User = UserToView.userprofile,
            Collection = Collection
        )
        Collection.MemberCount = Collection.MemberCount + 1
        Collection.save()
        return Response(data={'Status':True})
    else:
        raise Unauthorised

@api_view(['POST'])
def RemoveCollectionMember(request, pk, pk2):
    CurrentUser = request.auth.user
    try:
        Collection = Collections.objects.get(Name = pk, CreatedBy = CurrentUser.userprofile)
        UserToView = User.objects.get(username__iexact= pk2)
    except exceptions.ObjectDoesNotExist:
        raise UserDoesNotExist
    try:
        Following.objects.get(Follower=UserToView.userprofile, GettingFollowed=CurrentUser.userprofile, Status=2)
        raise Blocked
    except exceptions.ObjectDoesNotExist:
        pass

    if Collection.CreatedBy == CurrentUser.userprofile:
        CollectionPosts.objects.get(
            User = UserToView.userprofile,
            Collection = Collection
        ).delete()
        Collection.MemberCount = Collection.MemberCount - 1
        Collection.save()
        return Response(data={'Status':False})
    else:
        raise Unauthorised

@api_view(['GET'])
def GetCollectionPosts(request, pk):
    try:
        Collection = Collections.objects.get(Name = pk)
    except exceptions.ObjectDoesNotExist:
        raise UserDoesNotExist
    limit = int(request.GET.get('limit', 32))
    offset = int(request.GET.get('offset', 0))
    if limit>64:
        limit=64
    if Collection.Show == ONLYPOSTS:
        Post = Posts.objects.filter(Q(PostedBy__PartOf__Collection = Collection, Public = True, ParentPost=None, Group = None)|Q(PostedBy__PartOf__Collection = Collection, ParentPost=None, Group__PostsArePublic = True)).prefetch_related('PostImages', 'Poll', 'ParentPost', 'RePost', 'ParentPost', 'ReplyingTo', 'ParentPost', 'PostImages', 'Group', 'Likes').select_related('Video', 'PostBody', 'PostLink', 'OverWatchFinalOutcome')[offset:limit+offset]
    elif Collection.Show == ONLYTOPCOMMENTS:
        Post = Posts.objects.filter(Q(PostedBy__PartOf__Collection = Collection, Public = True, ReplyingTo=None, Group = None)|Q(PostedBy__PartOf__Collection = Collection, ReplyingTo=None, Group__PostsArePublic = True))
    elif Collection.Show == ALL:
        Post = Posts.objects.filter(
            Q(PostedBy__PartOf__Collection=Collection, Public=True, Group=None) | Q(PostedBy__PartOf__Collection=Collection, Group__PostsArePublic=True))
    if request.auth == None:
        serializer = PostSerializer(Post, many=True)
        return Response(serializer.data)
    serializer = PostSerializer(Post, many = True, context = {'request':request})
    return Response(serializer.data)

@api_view(['GET'])
def MyCollections(requst):
    CurrentUser = requst.auth.user
    Member = FollowCollection.objects.filter(User = CurrentUser.userprofile).values_list('Collection')
    Collection = Collections.objects.filter(Q(id__in = Member)|Q(CreatedBy = CurrentUser.userprofile)).distinct()
    serializer = CollectionSerializer(Collection, many = True, context={'request':requst})
    return Response(serializer.data)

@api_view(['POST'])
def AddRemoveCollection(requst, pk):
    try:
        Collection = Collections.objects.get(Name=pk)
    except exceptions.ObjectDoesNotExist:
        raise UserDoesNotExist
    CurrentUser = requst.auth.user
    try:
        FollowCollection.objects.get(Collection = Collection, User = CurrentUser.userprofile).delete()
        return Response(data={'Status':True})
    except exceptions.ObjectDoesNotExist:
        FollowCollection.objects.create(Collection=Collection, User=CurrentUser.userprofile)
        return Response(data={'Status': False})


@api_view(['GET'])
def AddToCollection(request, pk):
    CurrentUser = request.auth.user.userprofile
    Collection = Collections.objects.filter(CreatedBy = CurrentUser)
    try:
        UserToView = User.objects.get(username__iexact= pk).userprofile
    except exceptions.ObjectDoesNotExist:
        raise UserDoesNotExist
    serializer = CollectionSerializerAdd(Collection, many = True, context={'request':request, 'UserToView':UserToView})
    return Response(serializer.data)
@api_view(['POST'])
def BlockUser(request, pk):
    CurrentUser = request.auth.user
    try:
        UserToView = User.objects.get(username__iexact= pk).userprofile
    except exceptions.ObjectDoesNotExist:
        raise UserDoesNotExist
    if UserToView == CurrentUser.userprofile:
        raise Unauthorised
    try:
        Status = Following.objects.get(Follower = CurrentUser.userprofile, GettingFollowed = UserToView)
        Status.Status = 2
        Status.save()
        try:
            try:
                Following.objects.get(GettingFollowed = CurrentUser.userprofile, Follower = UserToView).delete()
            except exceptions.ObjectDoesNotExist:
                pass
            NotifyPosts.objects.get(Users = Status).delete()
        except exceptions.ObjectDoesNotExist:
            pass
        return Response(data={'Status': Status.Status})
    except exceptions.ObjectDoesNotExist:
        try:
            Following.objects.get(GettingFollowed=CurrentUser.userprofile, Follower=UserToView).delete()
        except exceptions.ObjectDoesNotExist:
            pass
        Status = Following.objects.create(Follower=CurrentUser.userprofile, GettingFollowed = UserToView, Status = 2)
        return Response(data={'Status': Status.Status})

@api_view(['POST'])
def UnBlockUser(request, pk):
    CurrentUser = request.auth.user
    try:
        UserToView = User.objects.get(username__iexact= pk).userprofile
    except exceptions.ObjectDoesNotExist:
        raise UserDoesNotExist
    try:
        Status = Following.objects.get(Follower = CurrentUser.userprofile, GettingFollowed = UserToView, Status = 2)
        Status.Status = 2
        Status.delete()
        return Response(data={'Status': Status.Status})
    except exceptions.ObjectDoesNotExist:
        return Response(data={'Status': None})
@api_view(["GET"])
def BlockedUsers(request):
    CurrentUser = request.auth.user
    limit = int(request.GET.get('limit', 32))
    offset = int(request.GET.get('offset', 0))
    if limit>64:
        limit=64
    Requests = Following.objects.filter(Follower=CurrentUser.userprofile, Status = BLOCKED).order_by('-id').values_list('GettingFollowed')[offset:limit+offset]
    Users = UserProfile.objects.filter(id__in = Requests)
    serializer = UserProfileSerializer(Users, many=True, context={'request':request})
    return Response(serializer.data)


@api_view(['POST'])
def ReportPost(request, pk, pk2):
    CurrentUser = request.auth.user
    try:
        UserToView = User.objects.get(username__iexact=pk)
        Post = Posts.objects.get(PostedBy=UserToView.userprofile, id=pk2)

    except exceptions.ObjectDoesNotExist:
        raise PostDoesNotExist
    if UserToView == CurrentUser:
        raise Unauthorised
    if Post.Group:
        try:
            Status = GroupMembers.objects.get(User=CurrentUser.userprofile, Group=Post.Group)
            if Status.Status == 1:
                pass
            elif Status.Status == 2:
                pass
            else:
                if Post.Group.PostsArePublic:
                    pass
                else:
                    try:
                        Mentions.objects.get(User=CurrentUser.userprofile, Post=Post)
                        pass
                    except exceptions.ObjectDoesNotExist:
                        raise Unauthorised
        except exceptions.ObjectDoesNotExist:
            if CurrentUser == UserToView:
                pass
            else:
                if Post.Group.PostsArePublic:
                    pass
                else:
                    raise Unauthorised
    else:
        if CurrentUser == UserToView:
            pass
        else:
            if Post.Public:
                pass
            else:
                try:
                    Following.objects.get(Follower=CurrentUser.userprofile, GettingFollowed=UserToView.userprofile)
                    pass
                except exceptions.ObjectDoesNotExist:
                    try:
                        Mentions.objects.get(User=CurrentUser.userprofile, Post=Post)
                        pass
                    except exceptions.ObjectDoesNotExist:
                        raise ServiceUnavailable
    try:
        PostReports.objects.get(Post = Post, From = CurrentUser.userprofile)
        raise Unauthorised
    except exceptions.ObjectDoesNotExist:
        OffenseType = int(request.data.get('Type'))
        PostReports.objects.create(Post = Post, From = CurrentUser.userprofile, Type = OffenseType)
        Post.ReportCount = Post.ReportCount+1
        Post.save()
        raise Success

@api_view(['POST'])
def UndoPostReport(request, pk, pk2):
    CurrentUser = request.auth.user
    try:
        UserToView = User.objects.get(username__iexact=pk)
        Post = Posts.objects.get(PostedBy=UserToView.userprofile, id=pk2)
    except exceptions.ObjectDoesNotExist:
        raise PostDoesNotExist
    if Post.Group:
        try:
            Status = GroupMembers.objects.get(User=CurrentUser.userprofile, Group=Post.Group)
            if Status.Status == 1:
                pass
            elif Status.Status == 2:
                pass
            else:
                if Post.Group.PostsArePublic:
                    pass
                else:
                    try:
                        Mentions.objects.get(User=CurrentUser.userprofile, Post=Post)
                        pass
                    except exceptions.ObjectDoesNotExist:
                        raise Unauthorised
        except exceptions.ObjectDoesNotExist:
            if CurrentUser == UserToView:
                pass
            else:
                if Post.Group.PostsArePublic:
                    pass
                else:
                    raise Unauthorised
    else:
        if CurrentUser == UserToView:
            pass
        else:
            if Post.Public:
                pass
            else:
                try:
                    Following.objects.get(Follower=CurrentUser.userprofile, GettingFollowed=UserToView.userprofile)
                    pass
                except exceptions.ObjectDoesNotExist:
                    try:
                        Mentions.objects.get(User=CurrentUser.userprofile, Post=Post)
                        pass
                    except exceptions.ObjectDoesNotExist:
                        raise ServiceUnavailable
    try:
        PostReports.objects.get(Post = Post, From = CurrentUser.userprofile).delete()
        Post.ReportCount = Post.ReportCount - 1
        Post.save()
        raise Success
    except exceptions.ObjectDoesNotExist:
        raise Unauthorised

@api_view(['POST'])
def ReportComment(request, pk, pk2, pk3, pk4):
    CurrentUser = request.auth.user
    try:
        UserToView = User.objects.get(username__iexact=pk)
        Post = Posts.objects.get(PostedBy=UserToView.userprofile, id=pk2)
        CommentPostedBy = User.objects.get(username__iexact=pk3)
        Commment = Posts.objects.get(PostedBy=CommentPostedBy.userprofile, id=pk4)
    except exceptions.ObjectDoesNotExist:
        raise PostDoesNotExist
    if UserToView == CurrentUser:
        raise Unauthorised
    if Post.Group:
        try:
            Status = GroupMembers.objects.get(User=CurrentUser.userprofile, Group=Post.Group)
            if Status.Status == 1:
                pass
            elif Status.Status == 2:
                pass
            else:
                if Post.Group.PostsArePublic:
                    pass
                else:
                    try:
                        Mentions.objects.get(User=CurrentUser.userprofile, Post=Post)
                        pass
                    except exceptions.ObjectDoesNotExist:
                        raise Unauthorised
        except exceptions.ObjectDoesNotExist:
            if CurrentUser == UserToView:
                pass
            else:
                if Post.Group.PostsArePublic:
                    pass
                else:
                    raise Unauthorised
    else:
        if CurrentUser == UserToView:
            pass
        else:
            if Post.Public:
                pass
            else:
                try:
                    Following.objects.get(Follower=CurrentUser.userprofile, GettingFollowed=UserToView.userprofile)
                    pass
                except exceptions.ObjectDoesNotExist:
                    try:
                        Mentions.objects.get(User=CurrentUser.userprofile, Post=Post)
                        pass
                    except exceptions.ObjectDoesNotExist:
                        raise ServiceUnavailable
    try:
        PostReports.objects.get(Post = Commment, From = CurrentUser.userprofile)
        raise Unauthorised
    except exceptions.ObjectDoesNotExist:
        OffenseType = int(request.data.get('Type'))
        PostReports.objects.create(Post = Commment, From = CurrentUser.userprofile, Type = OffenseType)
        Commment.ReportCount = Post.ReportCount+1
        Commment.save()
        raise Success
@api_view(['POST'])
def UndoCommentReport(request, pk, pk2, pk3, pk4):
    CurrentUser = request.auth.user
    try:
        UserToView = User.objects.get(username__iexact=pk)
        Post = Posts.objects.get(PostedBy=UserToView.userprofile, id=pk2)
        CommentPostedBy = User.objects.get(username__iexact=pk3)
        Commment = Posts.objects.get(PostedBy=UserToView.userprofile, id=pk4)
    except exceptions.ObjectDoesNotExist:
        raise PostDoesNotExist
    if Post.Group:
        try:
            Status = GroupMembers.objects.get(User=CurrentUser.userprofile, Group=Post.Group)
            if Status.Status == 1:
                pass
            elif Status.Status == 2:
                pass
            else:
                if Post.Group.PostsArePublic:
                    pass
                else:
                    try:
                        Mentions.objects.get(User=CurrentUser.userprofile, Post=Post)
                        pass
                    except exceptions.ObjectDoesNotExist:
                        raise Unauthorised
        except exceptions.ObjectDoesNotExist:
            if CurrentUser == UserToView:
                pass
            else:
                if Post.Group.PostsArePublic:
                    pass
                else:
                    raise Unauthorised
    else:
        if CurrentUser == UserToView:
            pass
        else:
            if Post.Public:
                pass
            else:
                try:
                    Following.objects.get(Follower=CurrentUser.userprofile, GettingFollowed=UserToView.userprofile)
                    pass
                except exceptions.ObjectDoesNotExist:
                    try:
                        Mentions.objects.get(User=CurrentUser.userprofile, Post=Post)
                        pass
                    except exceptions.ObjectDoesNotExist:
                        raise ServiceUnavailable
    try:
        PostReports.objects.get(Post = Commment, From = CurrentUser.userprofile).delete()
        Commment.ReportCount = Post.ReportCount - 1
        Commment.save()
        raise Success
    except exceptions.ObjectDoesNotExist:
        raise Unauthorised


@api_view(['GET'])
def PendingPosts(request):
    CurrentUser = request.auth.user
    ##print('PENIS')
    if CurrentUser.userprofile.IsOverWatcher:
        MyOutcomes = OverWatchVotes.objects.filter(User = CurrentUser.userprofile.IsOverWatcher).values_list('Post', flat=True)
        PendingPosts = Posts.objects.all().exclude(ReportCount__lt = 3).exclude(id__in = MyOutcomes).order_by('-ReportCount')
        serializer = OverWatchSerializer(PendingPosts, many = True, context={'request':request})
        return Response(serializer.data)
    else:
        raise Unauthorised

@api_view(["POST"])
def OverWatchVote(request, pk):
    try:
        Post = Posts.objects.get(id=pk)
    except exceptions.ObjectDoesNotExist:
        raise PostDoesNotExist
    CurrentUser = request.auth.user

    if CurrentUser.userprofile.IsOverWatcher:
        ##print('PENIS')
        if Post.ReportCount == 0:
            raise Unauthorised
        else:
            try:
                OverWatchVotes.objects.get(User=CurrentUser.userprofile.IsOverWatcher, Post=Post)
                raise Unauthorised
            except exceptions.ObjectDoesNotExist:
                Result = int(request.data.get('Type'))
                OverWatchVotes.objects.create(User=CurrentUser.userprofile.IsOverWatcher, Post=Post, Outcome = Result)
                raise Success
    else:
        raise Unauthorised

        

@api_view(['GET'])
def MyReportedPosts(request):
    CurrentUser = request.auth.user
    MyReports = PostReports.objects.filter(From = CurrentUser.userprofile).values_list('Post', flat=True)
    Post = Posts.objects.filter(id__in = MyReports).prefetch_related('PostImages', 'Poll', 'ParentPost', 'RePost', 'ParentPost', 'ReplyingTo', 'ParentPost', 'PostImages', 'Group', 'Likes').select_related('Video', 'PostBody', 'PostLink', 'OverWatchFinalOutcome')
    serializer = PostSerializer(Post, many = True, context={'request':request})
    return Response(serializer.data)

@api_view(['POST', "DELETE"])
def AddNotificationToken(request):
    if request.method == 'POST':
        CurrentUser = request.auth.user.userprofile
        try:
            FireBaseNotificationTokens.objects.get(Token = request.data.get('Token')).delete()
        except exceptions.ObjectDoesNotExist:
            pass
        serializer = NotificationTokenSerializer(data = request.data)
        if serializer.is_valid():
            serializer.save(User = CurrentUser)
            raise Success
        else:
            raise Invalid

    if request.method == 'DELETE':
        CurrentUser = request.auth.user.userprofile
        Token = request.data.get('Token')
        try:
            Obj = FireBaseNotificationTokens.objects.get(Token = Token, User = CurrentUser).delete()
            raise Success
        except exceptions.ObjectDoesNotExist:
            raise Success

@api_view(['POST'])
def CheckNotificationStatus(request):
    if request.method == 'POST':
        CurrentUser = request.auth.user.userprofile
        Token = request.data.get('Token')
        try:
            FireBaseNotificationTokens.objects.get(Token = Token, User = CurrentUser)
            return Response(data={'Status':True})
        except exceptions.ObjectDoesNotExist:
            return Response(data={'Status':False})


@api_view(['POST'])
def GetPostUpdates(request):
    PostIDs = request.data.get('ids')
    Post = Posts.objects.filter(id__in = PostIDs)
    serializer = PostUpdateSerializer(Post, many = True)
    return Response(serializer.data)
    

@api_view(['POST'])
def TrashPosts(request):
    while True:
        NewUserName =  get_random_string(length=4, allowed_chars='ABCDENGHIJKLMNOPabcdefghijklmnopqrstuvwxyz')
        NewUser = User.objects.create(
            username = NewUserName
        )
        nouns = ("puppy", "car", "rabbit", "girl", "monkey")
        verbs = ("runs", "hits", "jumps", "drives", "barfs") 
        adv = ("crazily.", "dutifully.", "foolishly.", "merrily.", "occasionally.")
        adj = ("adorable", "clueless", "dirty", "odd", "stupid")
        num = random.randrange(0,5)
        Title = nouns[num] + ' ' + verbs[num] + ' ' + adv[num] + ' ' + adj[num] + ' ' + '#TestPost' + 'This is an english post. Hello there,'
        Post = Posts.objects.create(
            Title = Title,
            Public = True,
            WhoCanComment = EVERYONE,
            Language = 1,
            PostedBy = NewUser.userprofile
        )
        print(Title)




@api_view(['POST'])
def ResetPasswordUsingMobileOTP_Send(request):
    CurrentUser = request.auth.user
    if request.method == 'POST':
        UserOTP =  get_random_string(length=4, allowed_chars='1234567890')
        UserOTPToken.objects.create(
            Phone = CurrentUser.PhoneNumber,
            Key = UserOTP, 
            OTPType = RESET_PASSWORD
        )
        '''
        from . import Twilio
        Twilio.client.messages.create(
            from_='+12074125917',
            to=CurrentUser.PhoneNumber.PhoneNumber,
            body=f'Your verification code is: {UserOTP}'
        )
        '''
        return Response(data={'Sent':True, 'PhoneNumber':CurrentUser.PhoneNumber.PhoneNumber})

@csrf_exempt
@api_view(['POST'])
def ResetPasswordUsingMobileOTP_Verify(request):
    CurrentUser = request.auth.user
    Key = request.data.get('Key')
    NewPassword = request.data.get('password')

    try:
        UserPhoneNumberObject = UserPhoneNumber.objects.get(
            user = CurrentUser
        )
    except exceptions.ObjectDoesNotExist:
        raise Unauthorised

    try:
        time_threshold = datetime.now(timezone.utc) - timedelta(minutes=10)
        UserOTPObject = UserOTPToken.objects.get(
            Phone = UserPhoneNumberObject,
            Key = Key,
            OTPType = RESET_PASSWORD,
            Created__gt=time_threshold
        ).delete()
    except exceptions.ObjectDoesNotExist:
        try:
            time_threshold = datetime.now(timezone.utc) - timedelta(minutes=10)
            UserOTPObject = UserOTPToken.objects.get(
                Phone = UserPhoneNumberObject,
                Key = Key,
                OTPType = RESET_PASSWORD,
                Created__lt=time_threshold
            ).delete()
            raise OTPTimeoUT
        except exceptions.ObjectDoesNotExist:
            raise Unauthorised


    CurrentUser.set_password(NewPassword)
    CurrentUser.save()
    return Response(data={'updated':True})


@api_view(['POST'])
def ResetPasswordUsingEmailOTP_Send(request):
    CurrentUser = request.auth.user
    if request.method == 'POST':
        UserOTP =  get_random_string(length=4, allowed_chars='1234567890')
        UserOTPToken.objects.create(
            Phone = CurrentUser.PhoneNumber,
            Key = UserOTP, 
            OTPType = RESET_PASSWORD
        )
        '''
        from . import Twilio
        Twilio.client.messages.create(
            from_='+12074125917',
            to=CurrentUser.PhoneNumber.PhoneNumber,
            body=f'Your verification code is: {UserOTP}'
        )
        '''
        return Response(data={'Sent':True})

@api_view(['POST'])
def UpdateUserName(request):
    CurrentUser = request.auth.user
    Name = request.data.pop('username')
    try:
        User.objects.get(username = Name)
        raise UserAlreadyExists
    except exceptions.ObjectDoesNotExist:
        pass
    try:
        time_threshold = datetime.now(timezone.utc) - timedelta(hours=720)
        LastHandleChange.objects.get(Time__gt = time_threshold)
        return Response(data={'detail':'Wait'})
    except exceptions.ObjectDoesNotExist:
        CurrentUser.username = Name
        CurrentUser.save()
        LastHandleChange.objects.create(User = CurrentUser)
        return Response(data={'updated':True})

@api_view(['POST'])
def AddPhonbeNumber_SendOTp(request):
    CurrentUser = request.auth.user
    PhoneNumber = request.data.get('phone_number')

    try:
        UserPhoneNumberObject = UserPhoneNumber.objects.get(PhoneNumber = PhoneNumber)
        if UserPhoneNumberObject.user:
            raise UserAlreadyExists
    except exceptions.ObjectDoesNotExist:
        UserPhoneNumberObject = UserPhoneNumber.objects.create(
            PhoneNumber = PhoneNumber,
            user = None
        )
        New = True

    OldOTPs = UserOTPToken.objects.filter(Phone = UserPhoneNumberObject)
    try:
        time_threshold = datetime.now(timezone.utc) - timedelta(seconds=20)
        OTPsSentInLast20Seconds = UserOTPToken.objects.get(Phone = UserPhoneNumberObject, Created__gt = time_threshold)
        raise Wait
    except exceptions.ObjectDoesNotExist:
        pass


    OldOTPs.delete()

    OTP = get_random_string(length=4, allowed_chars='1234567890')
    
    UserOTPToken.objects.create(
        Phone = UserPhoneNumberObject,
        Key = OTP,
        OTPType = NUMBER_CONF
    )

    from . import sns
    sns.client.publish(
        PhoneNumber = PhoneNumber,
        Message = f'Your verification code is: {OTP}'
    )

    return Response(data={'New':True})


@api_view(['POST'])
def AddPhonbeNumber_VerifyOTP(request):

    PhoneNumber = request.data.get('phone_number')
    Key = request.data.get('Key')
    CurrentUser = request.auth.user

    try:
        UserPhoneNumberObject = UserPhoneNumber.objects.get(
            PhoneNumber = PhoneNumber,
            user = None
        )
    except exceptions.ObjectDoesNotExist:
        raise Unauthorised

    try:
        CurrentUserPhoneNumber = UserPhoneNumber.objects.get(PhoneNumber = PhoneNumber, user = None)
        time_threshold = datetime.now(timezone.utc) - timedelta(minutes=10)
        UserOTPObject = UserOTPToken.objects.get(
            Phone = UserPhoneNumberObject,
            Key = Key,
            OTPType = AUTh,
            Created__gt=time_threshold
        ).delete()
    except exceptions.ObjectDoesNotExist:
        try:
            CurrentUserPhoneNumber = UserPhoneNumber.objects.get(PhoneNumber = PhoneNumber, user = None)
            time_threshold = datetime.now(timezone.utc) - timedelta(minutes=10)
            UserOTPObject = UserOTPToken.objects.get(
                Phone = UserPhoneNumberObject,
                Key = Key,
                OTPType = AUTh,
                Created__lt=time_threshold
            ).delete()
            raise OTPTimeoUT
        except exceptions.ObjectDoesNotExist:
            raise Unauthorised
    
    CurrentUserPhoneNumber.user = CurrentUser
    CurrentUserPhoneNumber.save()

    return Response(data={'token':Key})


    CurrentUser = request.auth.user
    NewPhoneNumber = request.data.get('phone_number')
    Key = request.data.get('Key')

    try:
        NewPhoneNumberObject = UserPhoneNumber.objects.get(
            PhoneNumber = NewPhoneNumber,
            user = None
        )
        UserOTPToken.objects.get(
            Phone = NewPhoneNumberObject,
            Key = Key,
            OTPType = NUMBER_CONF
        ).delete()
        NewPhoneNumberObject.user = CurrentUser
        NewPhoneNumberObject.save()
        return Response(data={'updated':True})
    except exceptions.ObjectDoesNotExist:
        raise Unauthorised
