from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect

from .models import Post, Comment
from .forms import PostForm


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = context['post']
        context['form'] = PostForm(instance=post)
        return context

    def get_object(self, queryset=None):
        return get_object_or_404(Post, pk=self.kwargs.get('post_id'))

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class CommentMixin(LoginRequiredMixin):
    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail', kwargs={'post_id': self.kwargs['post_id']}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment'] = self.get_object()
        return context

    def get_object(self, queryset=None):
        comment = get_object_or_404(
            Comment,
            pk=self.kwargs.get('comment_id'),
            post=self.kwargs.get('post_id')
        )
        if (
            comment.author == self.request.user
            or self.request.user.is_superuser
        ):
            return comment

    def form_valid(self, form):
        comment = self.get_object()
        if not (
            self.request.user.is_authenticated
            and self.request.user == comment.author
            or self.request.user.is_superuser
        ):
            return redirect('blog:post_detail', post_id=comment.post.id)
        else:
            return super().form_valid(form)
