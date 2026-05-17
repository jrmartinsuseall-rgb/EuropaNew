from django.core.paginator import Paginator

PER_PAGE = 25


def paginar(request, qs, per_page=PER_PAGE):
    """
    Retorna (page_obj, page_range, query_string) para uso nas views de lista.
    query_string contém todos os GET params exceto 'page', pronto para
    montar links como ?{{ query_string }}&page=N.
    """
    paginator  = Paginator(qs, per_page)
    page_obj   = paginator.get_page(request.GET.get('page', 1))
    page_range = list(paginator.get_elided_page_range(
        page_obj.number, on_each_side=2, on_ends=1
    ))
    params = request.GET.copy()
    params.pop('page', None)
    return page_obj, page_range, params.urlencode()
