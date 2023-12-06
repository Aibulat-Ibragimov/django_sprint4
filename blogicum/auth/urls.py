from django.urls import path

from . import views

urlpatterns = [
    path(
        'auth/registration/',
        views.CreateUserView.as_view(),
        name='registration',
    ),
]
