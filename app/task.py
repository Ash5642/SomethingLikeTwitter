import re
from django.core import exceptions
from celery import shared_task
from time import process_time, sleep
from django.core.mail import send_mail
from pyfcm import FCMNotification
from bs4 import BeautifulSoup
from . import models
import requests
from urllib.parse import urljoin
import urllib
from PIL import Image
import os
from django.core.files.storage import default_storage as storage
from django.conf import settings
import mimetypes
from io import BytesIO

from PIL import Image as PillowImage
from PIL import ImageEnhance, ImageFilter
import boto3
from io import StringIO
from django.utils.crypto import get_random_string
import cld3
import easyocr
import json
import cv2
from . import utilities
from datetime import datetime, timezone


@shared_task
def sleepy(duration):
    sleep(20)
   #print('ANUS')
    return None

@shared_task
def SendReplyNotification(To, From, Title):
    push_service = FCMNotification(
        api_key="AAAAmXGO-qo:APA91bGkUWq9yzilRaE5qfHqojhhMT8pFaGn1BOEa5U35z8yop5bQflTCothVc490BVDegJ8FTEE8O_6rvtpaPH7drzlBOpc6eOrn-fm6j-dJZHNHQYtwiKN_s9_bfdvIna4-9DvIAjx")
    Notification = push_service.notify_multiple_devices(
        To,
        message_title='@' + From + ' replied to you',
        message_body=f'"{Title}"'
    )
    return None

@shared_task
def SendChatNotification(To, From, Body):
    try:
        From = models.User.objects.get(id = From)

        push_service = FCMNotification(
            api_key="AAAAmXGO-qo:APA91bGkUWq9yzilRaE5qfHqojhhMT8pFaGn1BOEa5U35z8yop5bQflTCothVc490BVDegJ8FTEE8O_6rvtpaPH7drzlBOpc6eOrn-fm6j-dJZHNHQYtwiKN_s9_bfdvIna4-9DvIAjx")
        Notification = push_service.notify_multiple_devices(
            To,
            message_title='@' + From.username + ' sent you a message',
            message_body=f'"{Body}"',
            click_action= '',
        )
        print(Notification)
    except Exception as exception:
        print(exception)
    return None

@shared_task
def SendMentionNotification(To, Post_Id):
    try:
        Post = models.Posts.objects.get(id = Post_Id)
        push_service = FCMNotification(
            api_key="AAAAmXGO-qo:APA91bGkUWq9yzilRaE5qfHqojhhMT8pFaGn1BOEa5U35z8yop5bQflTCothVc490BVDegJ8FTEE8O_6rvtpaPH7drzlBOpc6eOrn-fm6j-dJZHNHQYtwiKN_s9_bfdvIna4-9DvIAjx")
        FromProfilePicture = Post.PostedBy.ProfilePicture.url
        extra_notification_kwargs = {
            'image':  FromProfilePicture
        }
        Notification = push_service.notify_multiple_devices(
            To,
            message_title='@' + Post.PostedBy.user.username + ' mentioned to you',
            message_body=f'"{Post.Title}"',
            extra_notification_kwargs=extra_notification_kwargss
        )
    except Exception as exception:
        print(exception)
    #print(Notification)

@shared_task
def SendFollowNotification(To,From):
    To = models.UserProfile.objects.get(id = To)
    From = models.UserProfile.objects.get(id = From)
    models.Notifications.objects.create(
        User = To,
        Type='flwrrq',
        From = From
    )
    Tokens = list(models.FireBaseNotificationTokens.objects.filter(User = To).values_list('Token', flat=True))
    if Tokens[0]:
        push_service = FCMNotification(
            api_key="AAAAmXGO-qo:APA91bGkUWq9yzilRaE5qfHqojhhMT8pFaGn1BOEa5U35z8yop5bQflTCothVc490BVDegJ8FTEE8O_6rvtpaPH7drzlBOpc6eOrn-fm6j-dJZHNHQYtwiKN_s9_bfdvIna4-9DvIAjx")
        FromProfilePicture = From.ProfilePicture.url
        extra_notification_kwargs = {
            'image':  FromProfilePicture
        }
        Notification = push_service.notify_multiple_devices(
            Tokens,
            message_title='@' + From.user.username + ' sent you a follow request.',
            message_body=f'@' + From.user.username + ' sent you a follow request. You can either accept or reject this.',
            extra_notification_kwargs=extra_notification_kwargs
        )

@shared_task
def SayHello():
    print('Hello!')

    
@shared_task
def GeneratePostThumbNail(image_id):
    try:
        ImageObject = models.Images.objects.get(id=image_id)
    except Exception as error:
       pass
    try:
        filename, ext = os.path.splitext(ImageObject.Image.name)
        random_str = models.get_random_string(length=4, allowed_chars='abcdefghijklmnopqrstuvwxyz1234567890') #avoid conflict in file names
        filename = filename +'_'+random_str + '_thumbnail' + ext
        #print(filename)
        i = storage.open(filename, 'w+')
        i_read = storage.open(ImageObject.Image.name, 'rb')
        OriginalImage = Image.open(i_read)
        if OriginalImage.width>720 or OriginalImage.height>720:
            if OriginalImage.height>OriginalImage.width:
                NewWidth = round(OriginalImage.width/(OriginalImage.height/720))
                thumbnail_size = (NewWidth, 720)
            elif OriginalImage.width>OriginalImage.height:
                NewHeight = round(OriginalImage.height / (OriginalImage.width / 720))
                thumbnail_size = (720, NewHeight)
            elif OriginalImage.height == OriginalImage.width:
                thumbnail_size = (720, 720)
            m = storage.open(ImageObject.Image.name, 'rb')
            im = Image.open(m)
            if im.mode in ("RGBA", "P"):
                im = im.convert("RGB")
            im = im.resize(thumbnail_size)
            sfile = BytesIO()  # cStringIO works too
            im.save(sfile, format="JPEG")
            CreatedObj = i.write(sfile.getvalue())
            m.close()
            ImageObject.ThumbNail = filename
        try:
            '''pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'
            if ImageObject.Post.Language == 'en':
                Imagetext = pytesseract.image_to_string(OriginalImage, lang="eng")
            elif ImageObject.Post.Language == 'hi':
                Imagetext = pytesseract.image_to_string(OriginalImage, lang="hin")
            elif ImageObject.Post.Language == 'te':
                Imagetext = pytesseract.image_to_string(OriginalImage, lang="tel")
            elif ImageObject.Post.Language == 'te':
                Imagetext = pytesseract.image_to_string(OriginalImage, lang="tam")
            elif ImageObject.Post.Language == 'bn':
                Imagetext = pytesseract.image_to_string(OriginalImage, lang="ben")
            elif ImageObject.Post.Language == 'kn':
                Imagetext = pytesseract.image_to_string(OriginalImage, lang="kan")
            else:
                Imagetext = pytesseract.image_to_string(OriginalImage, lang="hin+eng+tam+tel+ben+pan+kan")
            print(Imagetext)
            ImageObject.Caption = Imagetext'''
            Languages =  utilities.LanguageCodesToStr(ImageObject.Post.Language)
            ImageToScan = Image.open(storage.open(ImageObject.Image.name, 'rb'))
            '''
            if ImageToScan.width<720 or ImageToScan.height<720:
                if ImageToScan.height<ImageToScan.width:
                    NewWidth = round(ImageToScan.width*(720/ImageToScan.height))
                    BigSize = (NewWidth, 720)
                elif ImageToScan.width<ImageToScan.height:
                    NewHeight = round(ImageToScan.height * (720/ImageToScan.width))
                    BigSize = (720, NewHeight)
                elif ImageToScan.height == ImageToScan.width:
                    BigSize = (720, 1080)
                ImageToScan = ImageToScan.resize(BigSize)
            '''
               

            img_byte_arr = BytesIO()
            ImageToScan.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
        
            ResultObject =  {
                'data':[
                    
                ]
            }
            if ImageObject.Post.Language == models.te:
                Language = ['en', 'te']
            if ImageObject.Post.Language == models.ta:
                Language = ['en', 'te']
            if ImageObject.Post.Language == models.kn:
                Language = ['en', 'kn']
            if ImageObject.Post.Language == models.bn:
                Language = ['en', 'bn']
            else:
                Language = ['en']


            reader = easyocr.Reader(Language, gpu = False)
            result = reader.readtext(img_byte_arr, paragraph = True, y_ths = 0.5, x_ths = 0.5, height_ths = 0, width_ths = 0, ycenter_ths = 0)
            for TextObject in result:
                TextObject1 = {
                    'Text':TextObject[1],
                    'TopLeftX': int(TextObject[0][0][0]),
                    'TopLeftY': int(TextObject[0][0][1]),
                    'Height': int(TextObject[0][2][1]) - int(TextObject[0][1][1]),
                    'Width': int(int(TextObject[0][1][0]) - int(TextObject[0][3][0])),
                    'TextHeight': 10
                }
                ResultObject['data'].append(TextObject1)
            print('PIRATES')


            '''
            d = pytesseract.image_to_data(ImageToScan, output_type=pytesseract.Output.DICT, lang = 'hin+eng')
            print(d)
            n_boxes = len(d['block_num'])
            StartLeft = 0
            StartTop = 0
            MaxWidth = 0
            MinLeft = 0
            prev_par = 0
            text_par = ''
            text_par = ''
            FontSize = 0
            for thing in range(n_boxes):
                (Text, left, top, width, height, Paragraph, Confidence) = (d['text'][thing], d['left'][thing], d['top'][thing], d['width'][thing], d['height'][thing], d['par_num'][thing], d['conf'][thing])
                
                if Text.strip() != '' and int(Confidence) > 60:
                    print(Text, left, top, width, height, f'Word {thing} out of {n_boxes}')  
                    if thing == n_boxes:
                        TextObject1 = {
                            'Text':text_par,
                            'TopLeftX': MinLeft,
                            'TopLeftY': StartTop,
                            'Height': FullHeight,
                            'Width': MaxWidth,
                            'TextHeight':FontSize
                        }
                        ResultObject['data'].append(TextObject1)
                        break
                    if prev_par == Paragraph and thing != n_boxes-1:
                        print('AAAAAAAaa')
                        if Paragraph == d['par_num'][thing + 1]:
                            text_par += ' ' + Text
                            if left + width > MaxWidth:
                                MaxWidth = width + left
                            if int(left) < int(MinLeft):
                                print("DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD")
                                MinLeft = left
                        else:
                            text_par += ' ' + Text
                            if left + width > MaxWidth:
                                MaxWidth = width + left
                            if int(left) < int(MinLeft):
                                print("DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD")
                                MinLeft = left
                            FullHeight = top - StartTop
                            TextObject1 = {
                                'Text':text_par,
                                'TopLeftX': MinLeft,
                                'TopLeftY': StartTop,
                                'Height': FullHeight,
                                'Width': MaxWidth,
                                'TextHeight':FontSize
                            }
                            ResultObject['data'].append(TextObject1)
                    else:
                        prev_par = Paragraph
                        text_par = ''
                        text_par += ' ' + Text
                        MinLeft = left
                        FontSize = height
                        prev_par = Paragraph
                        StartTop = top
                        StartLeft = MinLeft
                        MaxWidth = 0
            '''
            ResultObject = json.dumps(ResultObject)
            print(ResultObject)
            ImageCaptionJSONFileName = ImageObject.Image.name +'_'+random_str + '_caption' + '.json'
            JSONFile = storage.open(ImageCaptionJSONFileName, 'w+')
            sfile = BytesIO()  # cStringIO works too
            CreatedObj = JSONFile.write(ResultObject)
            JSONFile.close()
            ImageObject.Caption = ResultObject
          
        except Exception as exc:
            print(exc)
        i.close()
        ImageObject.Height = OriginalImage.height
        ImageObject.Width = OriginalImage.width
        ImageObject.save()
    except Exception as error:
       print(error)
    print("Yarr")
    return None

@shared_task
def GenerateSmallProfilePicture(image_id):
    try:
        ImageObject = models.UserProfile.objects.get(id=image_id)
    except Exception as error:
       return
    try:
        filename, ext = os.path.splitext(ImageObject.ProfilePicture.name)
        random_str = models.get_random_string(length=4, allowed_chars='abcdefghijklmnopqrstuvwxyz1234567890') #avoid conflict in file names
        filename = filename +'_'+random_str + '_thumbnail' + ext
        #print(filename)
        i = storage.open(filename, 'w+')
        i_read = storage.open(ImageObject.ProfilePicture.name, 'rb')
        OriginalImage = Image.open(i_read)
        if OriginalImage.width>75 or OriginalImage.height>75:
            if OriginalImage.height>OriginalImage.width:
                NewWidth = round(OriginalImage.width/(OriginalImage.height/75))
                thumbnail_size = (NewWidth, 75)
            elif OriginalImage.width>OriginalImage.height:
                NewHeight = round(OriginalImage.height / (OriginalImage.width / 75))
                thumbnail_size = (75, NewHeight)
            elif OriginalImage.height == OriginalImage.width:
                thumbnail_size = (75, 75)
        else:
            return None
        m = storage.open(ImageObject.ProfilePicture.name, 'rb')
        im = Image.open(m)
        if im.mode in ("RGBA", "P"):
            im = im.convert("RGB")
        im = im.resize(thumbnail_size)
        sfile = BytesIO()  # cStringIO works too
        im.save(sfile, format="JPEG")
        CreatedObj = i.write(sfile.getvalue())
        i.close()
        m.close()
        ImageObject.ProfilePictureSmall = filename
        ImageObject.Save_Final()
    except Exception as error:
        ImageObject.ProfilePictureSmall = None
        ImageObject.Save_Final()
       #print(f"Error. No thumbnail generated for {image_id}. The error was {error}.")
    return None

@shared_task
def GenerateSmallGroupImage(image_id):
    try:
        ImageObject = models.Groups.objects.get(id=image_id)
    except Exception as error:
       return
    try:
        filename, ext = os.path.splitext(ImageObject.Image.name)
        random_str = models.get_random_string(length=4, allowed_chars='abcdefghijklmnopqrstuvwxyz1234567890') #avoid conflict in file names
        filename = filename +'_'+random_str + '_thumbnail' + ext
        #print(filename)
        i = storage.open(filename, 'w+')
        i_read = storage.open(ImageObject.Image.name, 'rb')
        OriginalImage = Image.open(i_read)
        if OriginalImage.width>75 or OriginalImage.height>75:
            if OriginalImage.height>OriginalImage.width:
                NewWidth = round(OriginalImage.width/(OriginalImage.height/75))
                thumbnail_size = (NewWidth, 75)
            elif OriginalImage.width>OriginalImage.height:
                NewHeight = round(OriginalImage.height / (OriginalImage.width / 75))
                thumbnail_size = (75, NewHeight)
            elif OriginalImage.height == OriginalImage.width:
                thumbnail_size = (75, 75)
        else:
            return None
        m = storage.open(ImageObject.Image.name, 'rb')
        im = Image.open(m)
        if im.mode in ("RGBA", "P"):
            im = im.convert("RGB")
        im = im.resize(thumbnail_size)
        sfile = BytesIO()  # cStringIO works too
        im.save(sfile, format="JPEG")
        CreatedObj = i.write(sfile.getvalue())
        i.close()
        m.close()
        ImageObject.ImageSmall = filename
        ImageObject.Save_Final()
    except Exception as error:
        ImageObject.ProfilePictureSmall = None
        ImageObject.Save_Final()
    return None

@shared_task
def GetLinkDetails(link, Post):
    URL = link
    Request = requests.get(URL)
    soup = BeautifulSoup(Request.text, 'html.parser')
    Description = ''
    #print('AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAa')
    try:
        for title in soup.find_all('title'):
            Description = Description + title.get_text()
            #print(title.get_text())
    except:
        Description = ''
    #print('AAAAAAAAAAAAAAAAAAAAAAAAAAA')
    Icon = soup.findAll('img')[0]['src']
    #print(Icon)
    Icon = urljoin(URL, Icon['src'])
    image_link = Icon
    #print(image_link)
    Post = models.Posts.objects.get(id=Post)
    Link = Post.PostLink
    Link.Description = Description[0:200]
    Link.Image = Icon
    Link.save()
    return None

@shared_task
def DetectPostLanguage(Post_id):
    try:
        Post = models.Posts.objects.get(id=Post_id)
        Title = Post.Title
        print(Title)
        try:
            pred = cld3.get_language(Title)
            print(pred)
            PredictedLanguage = pred.language.split('-')[0]
            Post.Language = PredictedLanguage
            Post.save()
        except Exception as exception:
            print(exception)
    except Exception as exception:
            print(exception)



@shared_task
def GenerateResetToken(user_id):
    try:
        User = models.User.objects.get(id=user_id)
    except:
        pass
    try:
        ResetToken = models.Change_Password_Token.objects.create(User=User, Key=get_random_string(length=7,
                                                                                                 allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@'))
        send_mail(
            f'Hello @{User.username}, your reset token is',
            f'{ResetToken.Key}',
            'sasurosh16@gmail.com',
            [User.email],
            fail_silently=False,
        )
        sleep(20)
        return
    except Exception as exception:
       return

@shared_task
def ManagePostNotifications(PostID):
    print(f'Sending notification for {PostID}')
    Now = datetime.now(timezone.utc)
    try:
        Post = models.Posts.objects.get(id = PostID)
    except exceptions.ObjectDoesNotExist:
        return
    push_service = FCMNotification(
        api_key="AAAAmXGO-qo:APA91bGkUWq9yzilRaE5qfHqojhhMT8pFaGn1BOEa5U35z8yop5bQflTCothVc490BVDegJ8FTEE8O_6rvtpaPH7drzlBOpc6eOrn-fm6j-dJZHNHQYtwiKN_s9_bfdvIna4-9DvIAjx"
    )
    if Post.RePost:
        User = Post.RePost.PostedBy
        Tokens = list(models.FireBaseNotificationTokens.objects.filter(User=User).values_list('Token', flat=True))
        if Post.Title == '__Repost__':
            models.Notifications.objects.create(
                User = User,
                Post = Post,
                Type = 'Repost',
                Created=Now
            )
            Notification = push_service.notify_multiple_devices(
                Tokens,
                message_title='@'+Post.PostedBy.user.username+' reposted ' + '"' + Post.RePost.Title + '"' ,
            )
        else:
            Now = datetime.now(timezone.utc)
            models.Notifications.objects.create(
                User=User,
                Post=Post,
                Type='PostMen',
                Created=Now
            )
            Notification = push_service.notify_multiple_devices(
                Tokens,
                message_title='@'+Post.PostedBy.user.username+' mentioned ' + '"' + Post.RePost.Title + '"' ,
                message_body=f'"{Post.Title}"'
            )

    else:   
        if Post.ParentPost:
            if Post.ReplyingTo:
                User = models.UserProfile.objects.get(id =  Post.ReplyingTo.PostedBy.id)

                models.Notifications.objects.create(
                    User= User,
                    Post = Post,
                    Type = 'Reply',
                    Created=Now
                )

                Tokens = list(models.FireBaseNotificationTokens.objects.filter(User=User).values_list('Token', flat=True))
                Notification = push_service.notify_multiple_devices(
                    Tokens,
                    message_title='@'+Post.PostedBy.user.username+' replied to ' + '"'  + Post.ReplyingTo.Title + '"' ,
                    message_body=f'"{Post.Title}"'
                )
            else:
                User = models.UserProfile.objects.get(id =  Post.ParentPost.PostedBy.id)

                models.Notifications.objects.create(
                    User= User,
                    Post = Post,
                    Type = 'Reply',
                    Created=Now
                )

                Tokens = list(models.FireBaseNotificationTokens.objects.filter(User=User).values_list('Token', flat=True))
                Notification = push_service.notify_multiple_devices(
                    Tokens,
                    message_title='@'+Post.PostedBy.user.username+' commented in ' + '"' + Post.ParentPost.Title + '"' ,
                    message_body=f'"{Post.Title}"'
                )
        else:
            UsersWhoHaveNotificationsEnabled = models.NotifyPosts.objects.filter(Users__GettingFollowed=Post.PostedBy).values_list('Users__Follower', flat=True)
            Users = models.UserProfile.objects.filter(id__in= UsersWhoHaveNotificationsEnabled)
            Tokens = list(models.FireBaseNotificationTokens.objects.filter(User__in=Users).values_list('Token', flat=True))
            Notification = push_service.notify_multiple_devices(
                Tokens,
                message_title='@'+Post.PostedBy.user.username+':',
                message_body=f'"{Post.Title}"'
            )

    return None


@shared_task
def UpdateUserScore_Like(LikeId):
    try:
        LikeObject = models.PostLikes.objects.get(id = LikeId)
    except exceptions.ObjectDoesNotExist:
        return
    
    LikedBy = LikeObject.User

    if LikeObject.Status == True:
        Score = 1
    else:
        Score = -2
    
    PointsAdded = Score * LikedBy.TrustFactor
    LikeObject.Post.PostedBy.Points = LikeObject.Post.PostedBy.Points + PointsAdded
    LikeObject.Post.PostedBy.save()
    return


@shared_task
def UpdateUserScore_Repost(PostID):
    try:
        RePostObject = models.Posts.objects.get(id = PostID)
        PostObject = RePostObject.RePost
    except exceptions.ObjectDoesNotExist:
        return
    
    RePostedBy = RePostObject.PostedBy

    
    PointsAdded = 3 * RePostedBy.TrustFactor
    PostObject.PostedBy.Points = PostObject.PostedBy.Points + PointsAdded
    PostObject.PostedBy.save()

    return

@shared_task
def DeleteUser(UserID):
    try:
        UserObject = models.User.objects.get(id = UserID)
    except exceptions.ObjectDoesNotExist:
        return

    Key = models.Token.objects.get(user=UserObject).delete()

    UserProfileObject = UserObject.userprofile
    UserProfileObject.Name = '[deleted]'
    UserProfileObject.ProfilePicture = '/images/icons/DefaultUserIcon.png'
    UserProfileObject.Bio = ''
    UserProfileObject.Location = None
    UserProfileObject.BirthDay = None
    UserProfileObject.Link = None
    UserProfileObject.UserType = models.Normal
    UserProfileObject.Banner = '/images/icons/DefaultUserBanner.jpg'

    UserProfileObject.save()

    UserPosts = models.Posts.objects.filter(PostedBy = UserProfileObject)

    UserPosts.update(
        Title = '[deleted]',
        Public = False,
    )

    postImages = models.Images.objects.filter(Post__in = UserPosts).delete()
    postPolls = models.Poll.objects.filter(Post__in = UserPosts).delete()
    postLink = models.PostLink.objects.filter(Post__in = UserPosts).delete()
    postBody = models.PostBodyText.objects.filter(Post__in = UserPosts).delete()


    UserLikes = models.PostLikes.objects.filter(User = UserProfileObject)

    for Like in UserLikes:
        Like.Post.Vote = Like.Post.Vote - 1
        Like.Post.save()

    UserLikes.delete()
    

    UserFollows = models.Following.objects.filter(GettingFollowed = UserProfileObject)

    for GettingFollowed in UserFollows:
        GettingFollowed.Follower.FollowingCount = GettingFollowed.Follower.FollowingCount - 1
        GettingFollowed.Follower.save()


    UserFollowedBy = models.Following.objects.filter(Follower = UserProfileObject)

    for Follower in UserFollowedBy:
        Follower.GettingFollowed.Followers = Follower.GettingFollowed.Followers - 1
        Follower.GettingFollowed.save()

    UserFollowedBy.delete()
    UserFollows.delete()

