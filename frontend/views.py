from django.shortcuts import render
import re

# Create your views here.

def UserPage(request, pk):
    UserToView = pk
    context = {'UserToView':pk}
    return render(request, 'MainPage.html')

def Chat(request, pk):
    UserToView = pk
    context = {'UserToView':pk}
    return render(request, 'Chat.html', context)

def PostPage(request, pk, pk2):
    UserToView = pk
    return render(request, 'MainPage.html')

def ReportPostPage(request, pk, pk2):
    UserToView = pk
    return render(request, 'ReportPost.html')

def GroupPage(request, pk):
    return render(request, 'MainPage.html')

def GroupPostPage(request,pk,pk2):
    GroupToView = pk
    id=pk2
    context = {'GroupToView': GroupToView, 'id':id}
    return render(request, 'GroupPostPage.html', context)

def CreateGroupPost(request, pk):
    GroupToView = pk
    context = {'GroupToView': GroupToView}
    return render(request, 'CreateGroupPost.html', context)

def SignUp(request):
    return render(request, 'Register.html')

def SignIn(request):
    return render(request, 'SignIn.html')

def CreateProfile(request):
    return render(request, 'CreateProfile.html')

def Home(request):
    return render(request, 'Home.html')

def Discover(request):
    return render(request, 'Discover.html')

def Connections(request):
    return render(request, 'Connections.html')

def CreatePost(request):
    return render(request, 'CreatePostPage.html')

def Search(request):
    return render(request, 'SearchMain.html')

def MyMentions(request):
    return render(request, 'Mentions.html')

def MyCommentReplies(request):
    return render(request, 'Comments.html')

def MyReples(request):
    return render(request, 'Replies.html')

def Trending(request, pk):
    context = {'Search':pk}
    return render(request, 'Trending.html', context)

def Followers(request):
    return render(request, 'Friends.html')
def Following(request):
    return render(request, 'Following.html')
def Chats(request):
    return render(request, 'Chats.html')
def Me(request):
    return render(request, 'Me.html')
def ReportPost(request, pk, pk2):
    context = {'UserToView': pk, 'id': pk2}
    return render(request, 'PostReport.html', context)
def PostComments(request, pk, pk2, pk3, pk4):
    return render(request, 'MainPage.html')
def Notifications(request):
    contex = {}
    return render(request, 'Notifications.html', contex)
def UserFollowers(request, pk):
    context = {'UserToView': pk}
    return render(request, 'UserFollowers.html', context)


def LikedBy(request, pk, pk2):
    return render(request, 'MainPage.html')

def ReplyLikedBy(request, pk, pk2, pk3, pk4):
    return render(request, 'MainPage.html')

def RePostedBy(request, pk, pk2):
    return render(request, 'MainPage.html')
def Main(request):
    MOBILE_AGENT_RE = re.compile(r".*(iphone|mobile|androidtouch)", re.IGNORECASE)
    if MOBILE_AGENT_RE.match(request.META['HTTP_USER_AGENT']):
        return render(request, 'MainPage.html')
    else:
        #print('ANUS')
        return render(request, 'MainPage.html')

def Settings(request):
    MOBILE_AGENT_RE = re.compile(r".*(iphone|mobile|androidtouch)", re.IGNORECASE)
    if MOBILE_AGENT_RE.match(request.META['HTTP_USER_AGENT']):
        return render(request, 'MainPage.html')
    else:
        pass
    return render(request, 'MainPage.html')
def ResetPassword(request):
    return render(request, 'ResetPassword.html')
def ResetEmail(request):
    return render(request, 'ResetEmail.html')
def ResetHandle(request):
    return render(request, 'ResetHandle.html')

def UserAgreement(request):
    return render(request, 'agreement.html')

def PasswordReset(request):
    return render(request, 'PasswordReset.html')
def DeleteAccount(request):
    return render(request, 'Delete.html')