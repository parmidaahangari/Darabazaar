from .models import User

def user_context(request):
    return {
        'is_logged_in': request.user.is_authenticated
    }