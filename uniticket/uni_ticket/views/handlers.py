from django.shortcuts import render

from ..utils import base_context


def error_404(request, exception):
    return render(request,'404.html', base_context({}))
