from rest_framework.exceptions import APIException

class InvalidToken(APIException):
    status_code = 401
    default_detail = 'The token provided in incorrect!'
    default_code = 'invalid_token'

class InvalidGroup(APIException):
    status_code = 404
    default_detail = 'That group does now exist, or has been deleted!'
    default_code = 'DoesNotExist'

class PostDoesNotExist(APIException):
    status_code = 404
    default_detail = 'post_does_no_exist'
    default_code = 'DoesNotExist'

class CommentDoesNotExist(APIException):
    status_code = 404
    default_detail = 'That comment does not exist, or has been deleted!'
    default_code = 'DoesNotExist'

class NotAGroupMemberYet(APIException):
    status_code = 403
    default_detail = 'You must be a member to view this group!'
    default_code = 'NotAMember!'

class Invalid(APIException):
    status_code = 422
    default_detail = 'This provided information is incorrect'
    default_code = 'Invalid'

class Spam(APIException):
    status_code = 422
    default_detail = 'Spam'
    default_code = 'Spam'

class InvalidKey(APIException):
    status_code = 422
    default_detail = 'invalid_key'
    default_code = 'Invalid'

class NameInValid(APIException):
    status_code = 422
    default_detail = 'NameInValid'
    default_code = 'NameInValid'

class UserDoesNotExist(APIException):
    status_code = 404
    default_detail = "UserDoesNotExist"
    default_code = "DoesNotExist!"

class NotFollowing(APIException):
    status_code = 403
    default_detail = 'You must followr to view this resource!'
    default_code = 'NotAFollower!'

class Unauthorised(APIException):
    status_code = 403
    default_detail = 'You are not the owner of this resource!'
    default_code = 'Unauthroiszd!'


class Banned(APIException):
    status_code = 403
    default_detail = 'banned'
    default_code = 'banned'

class Success(APIException):
    status_code = 200
    default_detail = 'Success- Posted Successfully'
    default_code = 'Success!'

class AlreadyFollowing(APIException):
    status_code = 409
    status_detail = 'You are already following this user!'
    default_code =  'Duplicate'

class Banned(APIException):
    status_code = 401
    status_detail = 'banned'
    default_code = 'Banned'

class AlreadyExists(APIException):
    status_code = 409
    status_detail = 'A group with the same anme already exists'
    default_code = 'AlreadyExists'

class UserAlreadyExists(APIException):
    status_code = 409
    status_detail = 'name_not_unique'
    default_code = 'AlreadyExists'

class AlreadyVoted(APIException):
    status_code = 409
    status_detail = 'AlreadyVoted'
    default_code = 'AlreadyVoted'

class ServiceUnavailable(APIException):
    status_code = 401
    default_detail = 'not_allowed'
    default_code = 'service_unavailable'

class Blocked(APIException):
    status_code = 401
    default_detail = 'blocked'
    default_code = 'blocked'

class Block(APIException):
    status_code = 401
    default_detail = 'block'
    default_code = 'block'

class NotAllowed(APIException):
    status_code = 401
    default_detail = 'notpublic'
    default_code = 'notpublic'

class WrongPassword(APIException):
    status_code = 401
    default_detail = 'wrong_password'
    default_code = 'wrong_password'

class Wait(APIException):
    status_code = 401
    default_detail = 'Wait'
    default_code = 'Wait'

class PleaseSignIn(APIException):
    status_code = 401
    default_detail = 'please_log_in'
    default_code = 'please_log_in'