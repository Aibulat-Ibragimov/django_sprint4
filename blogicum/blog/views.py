from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.views.generic import TemplateView, DetailView
from django.urls import reverse_lazy, reverse
from django.http import Http404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .forms import PostForm
from .models import Post, Category, User, Comment
from .forms import CommentForm


class PostListView(ListView):
    model = Post
    paginate_by = 10
    template_name = 'blog/index.html'


class UserProfileView(TemplateView):
    model = Post
    paginate_by = 10
    pk_url_kwarg = 'post_id'
    context_object_name = 'post'
    template_name = 'blog/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            user = get_object_or_404(
                User, username=self.kwargs.get('username')
            )
        except User.DoesNotExist:
            raise Http404("Пользователь не найден")
        context['user_profile'] = user
        context['user_posts'] = Post.objects.filter(author=user)
        context['title'] = f'Профиль пользователя {user}'
        return context


class UserEditProfileView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'blog/user.html'
    fields = ['first_name', 'last_name', 'username', 'email']
    success_url = reverse_lazy('user')

    def get_object(self, queryset=None):
        return self.request.user


class CategoryView(ListView):
    paginate_by = 10

    def get(self, request, category_slug):
        category = Category.objects.get(slug=category_slug, is_published=True)
        page_obj = category.posts.filter_posts()
        return render(
            request, 'blog/category.html', {
                'page_obj': page_obj, 'category': category
            }
        )


class PostCreateView(CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def test_func(self):
        return self.request.user.groups.filter(name='Автор').exists()

    def get_success_url(self):
        return reverse(
            'blog:profile', kwargs={'username': self.request.user.username}
        )

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')

    def get_object(self, queryset=None):
        return Post.objects.get(pk=self.kwargs.get("post_id"))

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.object.id})

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
        comments = Comment.objects.filter(post=post)
        form = CommentForm()
        comment_count = Post.objects.count
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


class CommentCreateView(LoginRequiredMixin, CreateView):
    post = None
    model = Comment
    form_class = CommentForm

    def dispatch(self, request, *args, **kwargs):
        self.post = get_object_or_404(Post, id=kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        post = Post.objects.get(id=self.kwargs['post_id'])
        form.instance.post = post
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.post.id})


class CommentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Comment
    form_class = CommentForm

    def dispatch(self, request, *args, **kwargs):
        self.post = get_object_or_404(Post, pk=kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        post = Post.objects.get(id=self.kwargs['post_id'])
        form.instance.post = post
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.post.id})


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = Comment
    pk_url_kwarg = 'comment_id'
    template_name = 'blog/comment.html'

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.post.pk})

    def test_func(self):
        comment = self.get_object()
        return comment.author == self.request.user
