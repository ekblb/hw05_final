from django.conf import settings
from django.core.paginator import Paginator


def paginator(object, request):
    paginator = Paginator(object, settings.NUMBER_OF_POST)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
