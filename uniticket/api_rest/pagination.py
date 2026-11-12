from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """Page number pagination whose page size can be set by the client, up to 1000."""
    # page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 1000
