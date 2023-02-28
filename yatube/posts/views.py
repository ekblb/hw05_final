from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
# from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Comment, Group, Follow, Post, User
from .utils import paginator


# @cache_page(60 * 20)
def index(request):
    posts = Post.objects.select_related('group', 'author')
    page_obj = paginator(posts, request)
    return render(request, 'posts/index.html', {'page_obj': page_obj})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('group', 'author')
    page_obj = paginator(posts, request)
    context = {
        'page_obj': page_obj,
        'group': group,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = User.objects.get(username=username)
    author_posts = author.posts.select_related('group', 'author')
    page_obj = paginator(author_posts, request)
    following = True
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related('group', 'author'), id=post_id
    )
    form = CommentForm(request.POST or None)
    comment_post = Comment.objects.select_related('post', 'author')
    context = {
        'post': post,
        'form': form,
        'comment_post': comment_post,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related('group', 'author'), id=post_id
    )
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post.id)
    form = PostForm(
        request.POST or None,
        instance=post,
        files=request.FILES or None,)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save()
    return redirect('posts:post_detail', post_id=post.id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author=request.user)
    page_obj = paginator(posts, request)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    following = get_object_or_404(User, username=username)
    if request.user != following:
        Follow.objects.get_or_create(user=request.user, author=following)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    following = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=following).delete()
    return redirect('posts:profile', username=username)
