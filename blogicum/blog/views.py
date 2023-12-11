from django.shortcuts import get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.views.generic import DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormView

from .models import Post, Category, User
from .forms import CommentForm
from .constants import NUMBER_OF_POSTS
from .mixins import AuthorMixin, PostMixin, CommentMixin


class PostListView(ListView):
    paginate_by = NUMBER_OF_POSTS
    template_name = 'blog/index.html'
    queryset = Post.objects.get_comments_count().filter_posts()


class ProfileView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = NUMBER_OF_POSTS

    def get_profile(self, queryset=None):
        return get_object_or_404(User, username=self.kwargs['username'])

    def get_queryset(self):
        profile = self.get_profile()
        user_posts = profile.posts.get_comments_count()
        if self.request.user != profile:
            user_posts = user_posts.filter_posts()
        return user_posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.get_profile()
        return context


class UserEditProfileView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'blog/user.html'
    fields = ('first_name', 'last_name', 'username', 'email')

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class CategoryPostsView(ListView):
    template_name = 'blog/category.html'
    context_object_name = 'page_obj'
    paginate_by = NUMBER_OF_POSTS

    def get_category(self, quryset=None):
        return get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )

    def get_queryset(self):
        category_posts = self.get_category().posts.get_comments_count(
        ).filter_posts()
        return category_posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.get_category()
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    template_name = 'blog/create.html'
    fields = (
        'title', 'text', 'pub_date', 'image',
        'location', 'category', 'is_published',
    )

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile', kwargs={'username': self.request.user.username}
        )

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(PostMixin, UpdateView):
    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail', kwargs={'post_id': self.object.id}
        )


class PostDeleteView(PostMixin, DeleteView):
    pass


class PostDetailView(DetailView):
    model = Post
    pk_url_kwarg = 'post_id'
    context_object_name = 'post'

    def get_object(self, queryset=None):
        post = get_object_or_404(Post, pk=self.kwargs.get('post_id'))
        if (
            self.request.user.is_authenticated
            and self.request.user == post.author
        ):
            return post
        return get_object_or_404(
            Post.objects.get_comments_count().filter_posts(
            ).filter(pk=self.kwargs.get('post_id'))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.get_object().comments.all(
        ).order_by('created_at')
        return context


class AddCommentView(CommentMixin, FormView):
    def form_valid(self, form):
        post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        form.instance.author = self.request.user
        form.instance.post = post
        form.instance.save()
        return super(AddCommentView, self).form_valid(form)


class EditCommentView(CommentMixin, AuthorMixin, UpdateView):

    pass


class DeleteCommentView(CommentMixin, AuthorMixin, DeleteView):

    pass
