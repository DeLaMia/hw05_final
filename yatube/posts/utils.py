from django.core.paginator import Paginator

LAST_10_POSTS: int = 10


def paginator_create(request, list):
    paginator = Paginator(list, LAST_10_POSTS)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
