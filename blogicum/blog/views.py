from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.views.generic import View, DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone

from .models import Post, Category, User, Comment
from .forms import CommentForm
from .constants import NUMBER_OF_POSTS
from .mixins import AuthorMixin, PostMixin, CommentMixin


class PostListView(ListView):
    model = Post
    paginate_by = NUMBER_OF_POSTS
    template_name = 'blog/index.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = Post.objects.filter_posts()
        for post in queryset:
            post.comment_count = post.comments.count()
        return queryset


class ProfileView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = NUMBER_OF_POSTS

    def get_profile(self, queryset=None):
        return get_object_or_404(User, username=self.kwargs['username'])

    def get_queryset(self):
        profile = self.get_profile()
        posts = Post.objects.filter(author=profile).order_by('-pub_date')
        if self.request.user != profile:
            posts = Post.objects.filter_posts().filter(author=profile)
        for post in posts:
            post.comment_count = post.comments.count()
        return posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.get_profile()
        context['profile'] = profile
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
            Category, slug=self.kwargs['category_slug']
        )

    def get_queryset(self):
        category = self.get_category()
        posts = Post.objects.filter(category=category)
        for post in posts:
            post.comment_count = post.comments.count()
        return posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.get_category()
        context['category'] = category
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
    model = Post
    template_name = 'blog/create.html'
    fields = (
        'title', 'text', 'pub_date', 'image',
        'location', 'category', 'is_published',
    )

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail', kwargs={'post_id': self.kwargs['post_id']}
        )


class PostDeleteView(PostMixin, AuthorMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'

    pass


class PostDetailView(PostMixin, DetailView):
    model = Post
    pk_url_kwarg = 'post_id'
    context_object_name = 'post'

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object
        comments = Comment.objects.filter(post=post).order_by('created_at')
        form = CommentForm()
        comment_count = Comment.objects.count()
        context['comments'] = comments
        context['form'] = form
        context['comment_count'] = comment_count
        return context

    def post(self, request, *args, **kwargs):
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = self.object
            comment.save()
            return redirect('blog:post_detail', post_id=self.object.pk)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class AddCommentView(CommentMixin, View):
    def post(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
        return redirect('blog:post_detail', post_id=post_id)


class EditCommentView(CommentMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    context_object_name = 'comment'
    pass


class DeleteCommentView(CommentMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'
    context_object_name = 'comment'
    pass
