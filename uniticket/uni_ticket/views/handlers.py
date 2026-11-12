from django.shortcuts import render

from ..utils import base_context


def error_404(request, exception):
    """
    Renders the 404 page.

    Args:
        request: The current HttpRequest.
        exception: The raised exception.

    Returns:
        The rendered page.
    """
    return render(request,'404.html', base_context({}))
