from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .context_processors import unread_counts


@login_required
def badges(request):
    return JsonResponse(unread_counts(request.user))
