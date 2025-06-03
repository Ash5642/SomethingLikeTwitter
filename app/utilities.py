from . import models

def LanguageCodes(code):
    if code == 'en':
        return models.en
    if code == 'hi':
        return models.hi
    if code == 'bn':
        return models.bn
    if code == 'mr':
        return models.mr
    if code == 'pa':
        return models.pa
    if code == 'te':
        return models.te
    if code == 'ta':
        return models.ta
    if code == 'kn':
        return models.kn
    if code == 'pa':
        return models.pa

def LanguageCodesToStr(code):
    if code == None:
        return None
    if code == models.en:
        return 'en'
    if code == models.hi:
        return 'hi'
    if code == models.bn:
        return 'bn'
    if code == models.mr:
        return 'mr'
    if code == models.pa:
        return 'pa'
    
    if code == models.te:
        return 'te'
    if code == models.ta:
        return 'ta'
    if code == models.kn:
        return 'kn'
    if code == models.pa:
        return 'pa'


def MergeCloseBoxes(data):
    for TextObject in data:
        for OtherTextObject in data:
            if (int(TextObject[0][2][1])-int(OtherTextObject[0][1][1])) < 400:
                print(TextObject[1] + OtherTextObject[1])
 
            else:
                print('ASSSS')