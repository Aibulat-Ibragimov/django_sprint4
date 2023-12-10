from django.shortcuts import render
from django.views.generic import TemplateView


class About(TemplateView):
    template_name = 'pages/about.html'


class Rules(TemplateView):
    template_name = 'pages/rules.html'


def page_not_found_404(request, exception):
    return render(request, 'pages/404.html', status=404)


def csrf_403(request, exception):
    return render(request, 'pages/403csrf.html', status=403)


def server_error_500(request):
    return render(request, 'pages/500.html', status=500)
