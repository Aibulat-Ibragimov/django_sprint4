import datetime

from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.views.generic import DetailView
from django.views import View
from django.urls import reverse_lazy
from django.http import HttpResponseForbidden
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from .forms import PostForm
from .models import Post, Category, User, Comment
from .forms import CommentForm
from .constants import NUMBER_OF_POSTS


class PostListView(ListView):
    model = Post
    paginate_by = NUMBER_OF_POSTS
    template_name = 'blog/index.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=datetime.datetime.now()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts = context['page_obj']
        for post in posts:
            post.comment_count = post.get_comment_count()
        return context


class ProfileView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    context_object_name = 'page_obj'
    paginate_by = NUMBER_OF_POSTS

    def get_queryset(self):
        username = self.kwargs['username']
        profile = get_object_or_404(User, username=username)

        if self.request.user == profile:
            return Post.objects.filter(author=profile)
        else:
            return Post.objects.filter(
                author=profile,
                is_published=True,
                pub_date__lte=datetime.datetime.now()
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = get_object_or_404(User, username=self.kwargs['username'])
        context['profile'] = profile
        for post in context['page_obj']:
            post.comment_count = post.get_comment_count()
        return context


class UserEditProfileView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'blog/user.html'
    fields = ['first_name', 'last_name', 'username', 'email']
    context_object_name = 'username'

    def get_object(self, queryset=None):
        username = self.kwargs.get('username')
        return get_object_or_404(User, username=username)

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True,
    )
    post_list = category.posts.filter_posts()
    paginator = Paginator(post_list, NUMBER_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'paginator': paginator,
        'category': category
    }
    return render(request, 'blog/category.html', context)


class PostCreateView(CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile', kwargs={'username': self.request.user.username}
        )

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def get_object(self, queryset=None):
        return Post.objects.get(pk=self.kwargs.get("post_id"))

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile', kwargs={'username': self.request.user.username}
        )

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        else:
            return False


class PostDeleteView(DeleteView):
    model = Post
    pk_url_kwarg = 'post_id'
    context_object_name = 'post'
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')


class PostDetailView(DetailView):
    model = Post
    pk_url_kwarg = 'post_id'
    context_object_name = 'post'

    def get(self, request, post_id):
        post = Post.objects.get(pk=post_id)
        comments = Comment.objects.filter(post=post).order_by('created_at')
        form = CommentForm()
        comment_count = post.get_comment_count()
        return render(
            request, 'blog/post_detail.html', {
                'post': post, 'comments': comments,
                'form': form, 'comment_count': comment_count
            }
        )

    def post(self, request, post_id):
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = Post.objects.get(pk=post_id)
            comment.save()
            return redirect('post_detail.html', post_id=post_id)
        else:
            post = Post.objects.get(pk=post_id)
            comments = Comment.objects.filter(post=post)
            return render(request, 'post_detail.html', {
                'post': post, 'comments': comments, 'form': form
            })


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', post_id=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id, post=post_id)
    if request.user != comment.author:
        return HttpResponseForbidden(
            'У вас нет прав на изменения этого комментария.'
        )
    form = CommentForm(request.POST or None, instance=comment)
    context = {'form': form, 'comment': comment}
    if request.method == 'POST' and form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = get_object_or_404(Post, pk=post_id)
        comment.save()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/comment.html', context)


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id, post=post_id)
    if request.user != comment.author:
        return HttpResponseForbidden(
            'У вас нет прав на удаление этого комментария.'
        )
    context = {'comment': comment}
    if request.method == 'POST':
        post_id = comment.post.id
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/comment.html', context)
