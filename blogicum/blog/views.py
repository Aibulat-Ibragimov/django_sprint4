from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.views.generic import DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic.edit import FormView

from .models import Post, Category, User, Comment
from .forms import CommentForm
from .constants import NUMBER_OF_POSTS
from .mixins import AuthorMixin, PostMixin, CommentMixin


class PostListView(ListView):
    paginate_by = NUMBER_OF_POSTS
    template_name = 'blog/index.html'
    queryset = Post.objects.filter_posts()


class ProfileView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = NUMBER_OF_POSTS

    def get_profile(self, queryset=None):
        return get_object_or_404(User, username=self.kwargs['username'])

    def get_queryset(self):
        profile = self.get_profile()
        user_posts = profile.posts.get_comments_count().filter(author=profile)
        if self.request.user != profile:
            user_posts = profile.posts.filter_posts()
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
        category_posts = self.get_category().posts.filter_posts().filter(
            category=self.get_category()
        )
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


# Я оставил PostMixin, так как я не нашел решения:
# проверки что пользователь, это автор поста;
# редиректа на сам пост, если неавторизованный пользователь
class PostUpdateView(PostMixin, UpdateView):
    model = Post
    template_name = 'blog/create.html'
    fields = (
        'title', 'text', 'pub_date', 'image',
        'location', 'category', 'is_published',
    )
    pk_url_kwarg = 'post_id'

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail', kwargs={'post_id': self.object.id}
        )


class PostDeleteView(PostMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'

    pass


class PostDetailView(DetailView):
    model = Post
    pk_url_kwarg = 'post_id'
    context_object_name = 'post'

    def get_queryset(self):
        post = self.get_object()
        comments = Comment.objects.filter(post=post).order_by('created_at')
        return comments

    def get_object(self, queryset=None):
        post = get_object_or_404(Post, pk=self.kwargs.get('post_id'))
        if (
            self.request.user.is_authenticated
            and self.request.user == post.author
        ):
            return post
        return get_object_or_404(
            Post,
            pk=self.kwargs.get('post_id'),
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.get_queryset()
        return context


class AddCommentView(CommentMixin, FormView):
    form_class = CommentForm

    def form_valid(self, form):
        post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        comment = form.save(commit=False)
        comment.author = self.request.user
        comment.post = post
        comment.save()
        return redirect('blog:post_detail', post_id=self.kwargs['post_id'])


class EditCommentView(CommentMixin, AuthorMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    context_object_name = 'comment'
    pk_url_kwarg = 'comment_id'

    pass


class DeleteCommentView(CommentMixin, AuthorMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'
    context_object_name = 'comment'
    pk_url_kwarg = 'comment_id'

    pass
