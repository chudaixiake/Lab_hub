def user_profile(request):
    """传递用户头像到所有模板"""
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
            return {
                'user_avatar': profile.avatar.url if profile.avatar else None,
                'user_profile': profile
            }
        except:
            pass
    return {'user_avatar': None, 'user_profile': None}


def unread_messages(request):
    """传递未读消息数量"""
    if request.user.is_authenticated:
        from .models import Message
        unread_count = Message.objects.filter(receiver=request.user, is_read=False).count()
        return {'unread_message_count': unread_count}
    return {'unread_message_count': 0}
