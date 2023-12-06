from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.views.generic import View
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect, Http404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from django.utils import timezone

from .models import Post, Category, User, Comment
from .forms import CommentForm
from .constants import NUMBER_OF_POSTS


class AuthorMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user == self.get_object().author


class PostMixin(LoginRequiredMixin, AuthorMixin):
    def handle_no_permission(self):
        return HttpResponseRedirect(
            reverse_lazy(
                'blog:post_detail', kwargs={'post_id': self.kwargs['post_id']}
            )
        )

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile', kwargs={'username': self.request.user.username}
        )

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context['form'] = self.get_form()
    #     return context


class CommentMixin(LoginRequiredMixin):
    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail', kwargs={'post_id': self.kwargs['post_id']}
        )


class PostListView(ListView):
    model = Post
    paginate_by = NUMBER_OF_POSTS
    template_name = 'blog/index.html'

    def get_queryset(self):
        return self.model.objects.filter_posts()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts = context['page_obj']
        for post in posts:
            post.comment_count = post.comments.count()
        return context


class ProfileView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = NUMBER_OF_POSTS

    def get_object(self, queryset=None):
        return self.request.user

    def get_queryset(self):
        username = self.kwargs['username']
        profile = get_object_or_404(User, username=username)
        if self.request.user != profile:
            posts = Post.objects.filter(
                author=profile,
                is_published=True,
                pub_date__lte=timezone.now()
            )
            posts = posts.annotate(comment_count=Count('comments'))
            return posts
        else:
            posts = Post.objects.filter(author=profile)
            posts = posts.annotate(comment_count=Count('comments'))
            return posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = get_object_or_404(User, username=self.kwargs['username'])
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

    def get_queryset(self):
        category_slug = self.kwargs['category_slug']
        category = get_object_or_404(
            Category,
            slug=category_slug,
            is_published=True
        )
        return category.posts.filter_posts()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = self.kwargs['category_slug']
        category = get_object_or_404(
            Category,
            slug=category_slug,
            is_published=True
        )
        paginator = context['paginator']
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['category'] = category
        context['page_obj'] = page_obj
        for post in page_obj:
            post.comment_count = post.comments.count()
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

    def get_object(self, queryset=None):
        return get_object_or_404(Post, pk=self.kwargs.get('post_id'))

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostDeleteView(PostMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'

    def get_object(self, queryset=None):
        return get_object_or_404(Post, pk=self.kwargs.get('post_id'))

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class PostDetailView(ListView):
    model = Post
    pk_url_kwarg = 'post_id'
    context_object_name = 'post'

    def get(self, request, post_id):
        post = get_object_or_404(Post, pk=self.kwargs.get('post_id'))
        if (
            post.is_published and post.category.is_published
            and post.pub_date <= timezone.now()
            or (
                self.request.user.is_authenticated
                and self.request.user == post.author
            )
        ):
            comments = Comment.objects.filter(post=post).order_by('created_at')
            form = CommentForm()
            comment_count = Post.objects.get_comments_count()
            return render(
                request, 'blog/post_detail.html', {
                    'post': post, 'comments': comments,
                    'form': form, 'comment_count': comment_count
                }
            )
        else:
            raise Http404

    def post(self, request, post_id):
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = get_object_or_404(Post, pk=post_id)
            comment.save()
            return redirect('post_detail.html', post_id=post_id)
        else:
            post = get_object_or_404(Post, pk=post_id)
            comments = Comment.objects.filter(post=post)
            return render(request, 'post_detail.html', {
                'post': post, 'comments': comments, 'form': form
            })


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


class EditCommentView(CommentMixin, View):
    def get(self, request, post_id, comment_id):
        comment = get_object_or_404(Comment, pk=comment_id, post=post_id)
        if request.user != comment.author:
            return redirect('blog:post_detail', post_id=post_id)
        form = CommentForm(instance=comment)
        context = {'form': form, 'comment': comment}
        return render(request, 'blog/comment.html', context)

    def post(self, request, post_id, comment_id):
        comment = get_object_or_404(Comment, pk=comment_id, post=post_id)
        if request.user != comment.author:
            return redirect('blog:post_detail', post_id=post_id)
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.save()
            return redirect('blog:post_detail', post_id=post_id)
        context = {'form': form, 'comment': comment}
        return render(request, 'blog/comment.html', context)


class DeleteCommentView(LoginRequiredMixin, View):
    def get(self, request, post_id, comment_id):
        comment = get_object_or_404(Comment, pk=comment_id, post=post_id)
        if request.user != comment.author:
            return redirect('blog:post_detail', post_id=post_id)
        context = {'comment': comment}
        return render(request, 'blog/comment.html', context)

    def post(self, request, post_id, comment_id):
        comment = get_object_or_404(Comment, pk=comment_id, post=post_id)
        if request.user != comment.author:
            return redirect('blog:post_detail', post_id=post_id)
        post_id = comment.post.id
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)
