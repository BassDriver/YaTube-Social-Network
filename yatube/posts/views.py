from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page


from .forms import CommentForm, PostForm
from .models import Comment, Follow, Post, Group, User


def page(object, request):
    return Paginator(
        object, settings.MAX_NUM_POSTS_PER_PAGE).get_page(
            request.GET.get('page')
    )


@cache_page(20, key_prefix='index_page')
def index(request):
    return render(request, 'posts/index.html', {
        'page_obj': page(Post.objects.all(), request)
    })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    return render(request, 'posts/group_list.html', {
        'group': group,
        'page_obj': page(group.posts.all(), request),
    })


def profile(request, username):
    author = get_object_or_404(User, username=username)
    context = {
        'author': author,
        'page_obj': page(author.posts.all(), request),
        'following': False,
    }
    if request.user.is_authenticated:
        if Follow.objects.filter(
            user=request.user,
            author=author,
        ).exists():
            context['following'] = True
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    comments = Comment.objects.filter(post_id=post_id)
    form = CommentForm(request.POST or None)
    return render(request, 'posts/post_detail.html', {
        'post': post,
        'form': form,
        'comments': comments
    })


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    new_post = form.save(commit=False)
    new_post.author = request.user
    new_post = new_post.save()
    return redirect('posts:profile', request.user)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {
            'post': post,
            'form': form
        })
    form.save()
    return redirect('posts:post_detail', post_id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user).all()
    return render(request, 'posts/follow.html', {
        'page_obj': page(posts.all(), request)
    })


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(
            user=request.user,
            author=author,
        )
        return redirect('posts:follow_index')
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if Follow.objects.filter(
        user=request.user,
        author=author,
    ).exists():
        Follow.objects.get(
            user=request.user,
            author=author,
        ).delete()
    return redirect('posts:profile', username)
