from django.urls import path
from django.conf.urls.static import static
from django.conf import settings

from . import views

app_name = 'pages'

urlpatterns = [
    path('about/', views.About.as_view(), name='about'),
    path('rules/', views.Rules.as_view(), name='rules')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
