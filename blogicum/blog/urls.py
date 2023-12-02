from django.urls import path
from django.conf.urls.static import static
from django.conf import settings

from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.PostListView.as_view(), name='index'),
    path(
        'posts/<int:post_id>/',
        views.PostDetailView.as_view(),
        name='post_detail'
    ),
    path('category/<slug:category_slug>/', views.CategoryView.as_view(),
         name='category_posts'),
    path('profile/<str:username>/', views.ProfileView.as_view(), name='profile'),
    path(
        'profile/<str:username>/edit/',
        views.UserEditProfileView.as_view(),
        name='edit_profile'
    ),
    path('posts/create/', views.PostCreateView.as_view(),
         name='create_post'),
    path(
        'posts/<int:post_id>/delete/',
        views.PostDeleteView.as_view(),
        name='delete_post'
    ),
    path(
        'posts/<int:post_id>/edit/',
        views.PostUpdateView.as_view(),
        name='edit_post'
    ),
    path(
        'posts/<int:post_id>/comment/',
        views.add_comment,
        name='add_comment'
    ),
    path(
        'posts/<int:post_id>/edit_comment/<int:comment_id>/',
        views.edit_comment,
        name='edit_comment'
    ),
    path(
        'posts/<int:post_id>/delete_comment/<int:comment_id>/',
        views.delete_comment,
        name='delete_comment'
    )
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
