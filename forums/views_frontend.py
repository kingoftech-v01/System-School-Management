"""
Forums Frontend Views - Template-based HTML views.

This module provides frontend views for:
- Forum categories browsing
- Thread creation, viewing, and management
- Posting and replying to threads
- Voting on posts
- Thread subscriptions
- Content moderation and reporting

All views render HTML templates.
Frontend URL namespace: frontend:forums:view_name
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from accounts.decorators import tenant_required
from django.contrib.contenttypes.models import ContentType

from .models import (
    ForumCategory, Thread, Post, Vote, Tag,
    ThreadSubscription, Report
)
from accounts.decorators import direction_only
from .forms import (
    ThreadForm, PostForm, ReportForm, SearchForm, CategoryForm
)


# ============================================================================
# FORUM HOME AND CATEGORIES
# ============================================================================

@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def forum_home(request):
    """
    Forum homepage displaying categories and featured threads.
    """
    categories = ForumCategory.objects.filter(is_active=True).annotate(
        thread_count=Count('threads', filter=Q(threads__is_published=True))
    )

    # Featured threads
    featured_threads = Thread.objects.filter(
        is_featured=True,
        is_published=True
    ).select_related('author', 'category').prefetch_related('tags')[:5]

    # Recent activity
    recent_threads = Thread.objects.filter(
        is_published=True
    ).select_related('author', 'category').order_by('-last_activity_at')[:10]

    # Community stats
    total_threads = Thread.objects.filter(is_published=True).count()
    total_posts = Post.objects.filter(is_deleted=False).count()

    context = {
        'categories': categories,
        'featured_threads': featured_threads,
        'recent_threads': recent_threads,
        'total_threads': total_threads,
        'total_posts': total_posts,
        'title': _('Forum'),
        'meta_description': _('Discussion forums for students and faculty'),
    }

    return render(request, 'forums/home.html', context)


@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def category_list(request):
    """
    List all forum categories.
    """
    categories = ForumCategory.objects.filter(is_active=True).annotate(
        thread_count=Count('threads', filter=Q(threads__is_published=True))
    )

    context = {
        'categories': categories,
        'title': _('Forum Categories'),
    }

    return render(request, 'forums/category_list.html', context)


@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def category_detail(request, slug):
    """
    Display threads in a category.
    """
    category = get_object_or_404(ForumCategory, slug=slug, is_active=True)

    threads = Thread.objects.filter(
        category=category,
        is_published=True
    ).select_related('author').prefetch_related('tags').annotate(
        post_count=Count('posts', filter=Q(posts__is_deleted=False))
    ).order_by('-is_pinned', '-last_activity_at')

    # Filtering
    tag_slug = request.GET.get('tag')
    if tag_slug:
        threads = threads.filter(tags__slug=tag_slug)

    # Pagination
    paginator = Paginator(threads, 20)
    page_num = request.GET.get('page', 1)
    threads_page = paginator.get_page(page_num)

    # Category tags
    category_tags = Tag.objects.filter(threads__category=category).distinct()

    context = {
        'category': category,
        'threads': threads_page,
        'category_tags': category_tags,
        'total_count': paginator.count,
        'title': category.name,
    }

    return render(request, 'forums/category_detail.html', context)


# ============================================================================
# THREAD VIEWS
# ============================================================================

@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def thread_list(request):
    """
    List all threads across all categories.
    """
    threads = Thread.objects.filter(
        is_published=True
    ).select_related('author', 'category').prefetch_related('tags').annotate(
        post_count=Count('posts', filter=Q(posts__is_deleted=False))
    )

    # Filtering
    category_id = request.GET.get('category')
    if category_id:
        threads = threads.filter(category_id=category_id)

    tag_slug = request.GET.get('tag')
    if tag_slug:
        threads = threads.filter(tags__slug=tag_slug)

    # Sorting
    sort = request.GET.get('sort', 'recent')
    if sort == 'popular':
        threads = threads.order_by('-view_count')
    elif sort == 'active':
        threads = threads.order_by('-last_activity_at')
    else:  # recent
        threads = threads.order_by('-created_at')

    # Pagination
    paginator = Paginator(threads, 30)
    page_num = request.GET.get('page', 1)
    threads_page = paginator.get_page(page_num)

    categories = ForumCategory.objects.filter(is_active=True)
    tags = Tag.objects.all()

    context = {
        'threads': threads_page,
        'categories': categories,
        'tags': tags,
        'total_count': paginator.count,
        'title': _('All Threads'),
    }

    return render(request, 'forums/thread_list.html', context)


@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def thread_detail(request, slug):
    """
    Display thread with all posts.
    """
    thread = get_object_or_404(
        Thread.objects.select_related('author', 'category').prefetch_related('tags'),
        slug=slug,
        is_published=True
    )

    # Increment view count
    thread.increment_view_count()

    # Get posts
    posts = Post.objects.filter(
        thread=thread,
        is_deleted=False,
        parent__isnull=True  # Top-level posts only
    ).select_related('author').prefetch_related('replies').order_by('created_at')

    # Pagination
    paginator = Paginator(posts, 20)
    page_num = request.GET.get('page', 1)
    posts_page = paginator.get_page(page_num)

    # Check subscription
    is_subscribed = ThreadSubscription.objects.filter(
        thread=thread,
        user=request.user
    ).exists()

    # User votes (for displaying vote status)
    user_votes = {}
    if request.user.is_authenticated:
        votes = Vote.objects.filter(
            post__thread=thread,
            user=request.user
        ).values_list('post_id', 'vote_type')
        user_votes = dict(votes)

    context = {
        'thread': thread,
        'posts': posts_page,
        'is_subscribed': is_subscribed,
        'user_votes': user_votes,
        'total_posts': paginator.count,
        'title': thread.title,
    }

    return render(request, 'forums/thread_detail.html', context)


@login_required
@tenant_required
@ratelimit(key='user', rate='50/h')
def thread_create(request, category_slug=None):
    """
    Create new thread.
    """
    category = None
    if category_slug:
        category = get_object_or_404(ForumCategory, slug=category_slug, is_active=True)

    if request.method == 'POST':
        form = ThreadForm(request.POST)
        if form.is_valid():
            thread = form.save(commit=False)
            thread.author = request.user

            # Check if category requires approval
            if thread.category.requires_approval:
                thread.status = 'pending'
                thread.is_published = False
            else:
                thread.status = 'published'
                thread.is_published = True

            thread.save()
            form.save_m2m()  # Save tags

            # Auto-subscribe author to thread
            ThreadSubscription.objects.create(
                thread=thread,
                user=request.user,
                email_on_reply=True
            )

            messages.success(request, _('Thread created successfully.'))
            return redirect('frontend:forums:thread_detail', slug=thread.slug)
    else:
        initial = {}
        if category:
            initial['category'] = category
        form = ThreadForm(initial=initial)

    context = {
        'form': form,
        'category': category,
        'title': _('Create New Thread'),
    }

    return render(request, 'forums/thread_form.html', context)


@login_required
@tenant_required
@ratelimit(key='user', rate='50/h')
def thread_update(request, slug):
    """
    Update thread.
    Only author or moderators can edit.
    """
    thread = get_object_or_404(Thread, slug=slug)

    # Check permissions
    if thread.author != request.user and not request.user.has_perm('forums.can_moderate_threads'):
        messages.error(request, _('You do not have permission to edit this thread.'))
        return redirect('frontend:forums:thread_detail', slug=thread.slug)

    if request.method == 'POST':
        form = ThreadForm(request.POST, instance=thread)
        if form.is_valid():
            form.save()
            messages.success(request, _('Thread updated successfully.'))
            return redirect('frontend:forums:thread_detail', slug=thread.slug)
    else:
        form = ThreadForm(instance=thread)

    context = {
        'form': form,
        'thread': thread,
        'title': _('Edit Thread'),
    }

    return render(request, 'forums/thread_form.html', context)


@login_required
@tenant_required
@ratelimit(key='user', rate='50/h')
def thread_delete(request, slug):
    """
    Delete thread.
    Only author or moderators can delete.
    """
    thread = get_object_or_404(Thread, slug=slug)

    # Check permissions
    if thread.author != request.user and not request.user.has_perm('forums.can_moderate_threads'):
        messages.error(request, _('You do not have permission to delete this thread.'))
        return redirect('frontend:forums:thread_detail', slug=thread.slug)

    if request.method == 'POST':
        category_slug = thread.category.slug
        thread.delete()
        messages.success(request, _('Thread deleted successfully.'))
        return redirect('frontend:forums:category_detail', slug=category_slug)

    context = {
        'thread': thread,
        'title': _('Delete Thread'),
    }

    return render(request, 'forums/thread_confirm_delete.html', context)


# ============================================================================
# POST VIEWS
# ============================================================================

@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def post_create(request, thread_slug, parent_id=None):
    """
    Create new post or reply.
    """
    thread = get_object_or_404(Thread, slug=thread_slug, is_published=True)

    # Check if thread is locked
    if thread.is_locked:
        messages.error(request, _('This thread is locked. No new posts allowed.'))
        return redirect('frontend:forums:thread_detail', slug=thread.slug)

    parent = None
    if parent_id:
        parent = get_object_or_404(Post, pk=parent_id, thread=thread)

    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.thread = thread
            post.author = request.user
            if parent:
                post.parent = parent
            post.save()

            # Update thread activity
            thread.update_activity()

            messages.success(request, _('Post created successfully.'))
            return redirect('frontend:forums:thread_detail', slug=thread.slug)
    else:
        form = PostForm()

    context = {
        'form': form,
        'thread': thread,
        'parent': parent,
        'title': _('Reply to Thread') if not parent else _('Reply to Post'),
    }

    return render(request, 'forums/post_form.html', context)


@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def post_update(request, pk):
    """
    Update post.
    Only author can edit.
    """
    post = get_object_or_404(Post, pk=pk, is_deleted=False)

    # Check permissions
    if post.author != request.user:
        messages.error(request, _('You do not have permission to edit this post.'))
        return redirect('frontend:forums:thread_detail', slug=post.thread.slug)

    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.is_edited = True
            post.edited_at = timezone.now()
            post.save()
            messages.success(request, _('Post updated successfully.'))
            return redirect('frontend:forums:thread_detail', slug=post.thread.slug)
    else:
        form = PostForm(instance=post)

    context = {
        'form': form,
        'post': post,
        'title': _('Edit Post'),
    }

    return render(request, 'forums/post_form.html', context)


@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def post_delete(request, pk):
    """
    Delete post (soft delete).
    Only author or moderators can delete.
    """
    post = get_object_or_404(Post, pk=pk, is_deleted=False)

    # Check permissions
    if post.author != request.user and not request.user.has_perm('forums.can_moderate_threads'):
        messages.error(request, _('You do not have permission to delete this post.'))
        return redirect('frontend:forums:thread_detail', slug=post.thread.slug)

    if request.method == 'POST':
        thread_slug = post.thread.slug
        post.is_deleted = True
        post.save()
        messages.success(request, _('Post deleted successfully.'))
        return redirect('frontend:forums:thread_detail', slug=thread_slug)

    context = {
        'post': post,
        'title': _('Delete Post'),
    }

    return render(request, 'forums/post_confirm_delete.html', context)


@login_required
@tenant_required
@ratelimit(key='user', rate='200/h')
def post_vote(request, pk):
    """
    Vote on a post (upvote or downvote).
    """
    if request.method != 'POST':
        return redirect('frontend:forums:forum_home')

    post = get_object_or_404(Post, pk=pk, is_deleted=False)
    vote_type = int(request.POST.get('vote_type', 0))

    if vote_type not in [1, -1]:
        messages.error(request, _('Invalid vote type.'))
        return redirect('frontend:forums:thread_detail', slug=post.thread.slug)

    vote, created = Vote.objects.get_or_create(
        post=post,
        user=request.user,
        defaults={'vote_type': vote_type}
    )

    if not created:
        if vote.vote_type == vote_type:
            # Remove vote if same type
            vote.delete()
            messages.success(request, _('Vote removed.'))
        else:
            # Change vote
            vote.vote_type = vote_type
            vote.save()
            messages.success(request, _('Vote updated.'))
    else:
        messages.success(request, _('Vote recorded.'))

    return redirect('frontend:forums:thread_detail', slug=post.thread.slug)


# ============================================================================
# SUBSCRIPTION VIEWS
# ============================================================================

@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def thread_subscribe(request, slug):
    """
    Subscribe to thread notifications.
    """
    if request.method != 'POST':
        return redirect('frontend:forums:forum_home')

    thread = get_object_or_404(Thread, slug=slug, is_published=True)

    subscription, created = ThreadSubscription.objects.get_or_create(
        thread=thread,
        user=request.user,
        defaults={'email_on_reply': True}
    )

    if created:
        messages.success(request, _('Subscribed to thread notifications.'))
    else:
        messages.info(request, _('Already subscribed to this thread.'))

    return redirect('frontend:forums:thread_detail', slug=slug)


@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def thread_unsubscribe(request, slug):
    """
    Unsubscribe from thread notifications.
    """
    if request.method != 'POST':
        return redirect('frontend:forums:forum_home')

    thread = get_object_or_404(Thread, slug=slug, is_published=True)

    deleted_count, _ = ThreadSubscription.objects.filter(
        thread=thread,
        user=request.user
    ).delete()

    if deleted_count > 0:
        messages.success(request, _('Unsubscribed from thread notifications.'))
    else:
        messages.info(request, _('Not subscribed to this thread.'))

    return redirect('frontend:forums:thread_detail', slug=slug)


@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def my_subscriptions(request):
    """
    Display user's thread subscriptions.
    """
    subscriptions = ThreadSubscription.objects.filter(
        user=request.user
    ).select_related('thread', 'thread__author', 'thread__category')

    context = {
        'subscriptions': subscriptions,
        'title': _('My Subscriptions'),
    }

    return render(request, 'forums/my_subscriptions.html', context)


# ============================================================================
# MODERATION VIEWS
# ============================================================================

@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def report_content(request, content_type_id, object_id):
    """
    Report inappropriate content.
    """
    content_type = get_object_or_404(ContentType, pk=content_type_id)

    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reported_by = request.user
            report.content_type = content_type
            report.object_id = object_id
            report.save()

            messages.success(request, _('Content reported. Moderators will review it.'))
            return redirect('frontend:forums:forum_home')
    else:
        form = ReportForm()

    context = {
        'form': form,
        'title': _('Report Content'),
    }

    return render(request, 'forums/report_form.html', context)


# ============================================================================
# SEARCH
# ============================================================================

@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def search(request):
    """
    Search forums for threads and posts.
    """
    query = request.GET.get('q', '').strip()
    results = []

    if query and len(query) >= 3:
        # Search threads
        thread_results = Thread.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query),
            is_published=True
        ).select_related('author', 'category')[:20]

        results = thread_results

    context = {
        'query': query,
        'results': results,
        'title': _('Search Results'),
    }

    return render(request, 'forums/search.html', context)


# ============================================================================
# TAG VIEWS
# ============================================================================

@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def tag_list(request):
    """
    List all tags.
    """
    tags = Tag.objects.all().order_by('-use_count')

    context = {
        'tags': tags,
        'title': _('Forum Tags'),
    }

    return render(request, 'forums/tag_list.html', context)


@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def tag_threads(request, slug):
    """
    Display threads with a specific tag.
    """
    tag = get_object_or_404(Tag, slug=slug)

    threads = Thread.objects.filter(
        tags=tag,
        is_published=True
    ).select_related('author', 'category')

    # Pagination
    paginator = Paginator(threads, 20)
    page_num = request.GET.get('page', 1)
    threads_page = paginator.get_page(page_num)

    context = {
        'tag': tag,
        'threads': threads_page,
        'total_count': paginator.count,
        'title': f'Tag: {tag.name}',
    }

    return render(request, 'forums/tag_threads.html', context)


# ============================================================================
# USER ACTIVITY
# ============================================================================

@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def my_threads(request):
    """
    Display user's threads.
    """
    threads = Thread.objects.filter(
        author=request.user
    ).select_related('category').prefetch_related('tags').order_by('-created_at')

    # Pagination
    paginator = Paginator(threads, 20)
    page_num = request.GET.get('page', 1)
    threads_page = paginator.get_page(page_num)

    context = {
        'threads': threads_page,
        'total_count': paginator.count,
        'title': _('My Threads'),
    }

    return render(request, 'forums/my_threads.html', context)


@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def my_posts(request):
    """
    Display user's posts.
    """
    posts = Post.objects.filter(
        author=request.user,
        is_deleted=False
    ).select_related('thread', 'thread__category').order_by('-created_at')

    # Pagination
    paginator = Paginator(posts, 30)
    page_num = request.GET.get('page', 1)
    posts_page = paginator.get_page(page_num)

    context = {
        'posts': posts_page,
        'total_count': paginator.count,
        'title': _('My Posts'),
    }

    return render(request, 'forums/my_posts.html', context)


# ============================================================================
# CATEGORY MANAGEMENT (Direction only)
# ============================================================================

@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def category_create(request):
    """
    Create a new forum category.
    Direction only.
    """
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Category created successfully.'))
            return redirect('frontend:forums:category_list')
        else:
            messages.error(request, _('Please correct the errors below.'))
    else:
        form = CategoryForm()

    context = {
        'form': form,
        'title': _('Create Forum Category'),
    }

    return render(request, 'forums/category_form.html', context)


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def category_edit(request, pk):
    """
    Edit an existing forum category.
    Direction only.
    """
    category = get_object_or_404(ForumCategory, pk=pk)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, _('Category updated successfully.'))
            return redirect('frontend:forums:category_detail', slug=category.slug)
        else:
            messages.error(request, _('Please correct the errors below.'))
    else:
        form = CategoryForm(instance=category)

    context = {
        'form': form,
        'category': category,
        'title': _('Edit Category: %(name)s') % {'name': category.name},
    }

    return render(request, 'forums/category_form.html', context)


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def category_delete(request, pk):
    """
    Delete a forum category.
    Direction only. GET shows confirmation page, POST performs delete.
    """
    category = get_object_or_404(ForumCategory, pk=pk)

    if request.method == 'POST':
        category.delete()
        messages.success(request, _('Category deleted successfully.'))
        return redirect('frontend:forums:category_list')

    # GET: show confirmation page
    thread_count = category.threads.count()

    context = {
        'category': category,
        'thread_count': thread_count,
        'title': _('Delete Category: %(name)s') % {'name': category.name},
    }

    return render(request, 'forums/category_confirm_delete.html', context)


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def moderation_queue(request):
    """
    Moderation queue showing reported content, pending threads, and flagged posts.
    Direction only.
    """
    # Pending threads (awaiting approval)
    pending_threads = Thread.objects.filter(
        status='pending'
    ).select_related('author', 'category').order_by('-created_at')

    # Reported content (pending and under review)
    pending_reports = Report.objects.filter(
        status__in=['pending', 'reviewing']
    ).select_related('reported_by', 'reviewed_by').order_by('-created_at')

    # Flagged posts (soft-deleted posts that may need review)
    flagged_posts = Post.objects.filter(
        is_deleted=True
    ).select_related('author', 'thread').order_by('-updated_at')[:50]

    # Statistics
    total_pending_threads = pending_threads.count()
    total_pending_reports = pending_reports.count()
    total_flagged_posts = flagged_posts.count()

    context = {
        'pending_threads': pending_threads,
        'pending_reports': pending_reports,
        'flagged_posts': flagged_posts,
        'total_pending_threads': total_pending_threads,
        'total_pending_reports': total_pending_reports,
        'total_flagged_posts': total_flagged_posts,
        'title': _('Moderation Queue'),
    }

    return render(request, 'forums/moderation_queue.html', context)
