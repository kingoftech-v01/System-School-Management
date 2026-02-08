"""
Frontend views for the articles app.
Handles article listing, detail, creation, editing, comments, likes, and newsletter.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from accounts.decorators import lecturer_required
from .models import Article, Category, Comment, Like, Newsletter
from .forms import ArticleForm, CommentForm, NewsletterForm


@login_required
def article_list(request):
    """List published articles with pagination."""
    articles = (
        Article.objects.published()
        .select_related('author')
        .prefetch_related('categories')
    )

    paginator = Paginator(articles, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'articles/article_list.html', {
        'page_obj': page_obj,
        'title': _('Articles'),
    })


@login_required
def article_detail(request, slug):
    """Display a single article, its approved comments, and a comment form."""
    article = get_object_or_404(
        Article.objects.select_related('author').prefetch_related('categories'),
        slug=slug,
        status='published',
    )

    # Increment view count
    article.increment_views()

    # Reload the article to get the actual views_count value after F() expression
    article.refresh_from_db()

    # Approved comments for this article
    comments = (
        article.comments
        .filter(status='approved')
        .select_related('author')
        .order_by('-created_at')
    )

    # Check if the current user has liked this article
    has_liked = Like.objects.filter(article=article, user=request.user).exists()

    comment_form = CommentForm()

    return render(request, 'articles/article_detail.html', {
        'article': article,
        'comments': comments,
        'comment_form': comment_form,
        'has_liked': has_liked,
        'title': article.title,
    })


@login_required
def category_articles(request, category_slug):
    """List published articles filtered by category."""
    category = get_object_or_404(Category, slug=category_slug, is_active=True)

    articles = (
        Article.objects.published()
        .filter(categories=category)
        .select_related('author')
        .prefetch_related('categories')
    )

    paginator = Paginator(articles, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'articles/category_articles.html', {
        'category': category,
        'page_obj': page_obj,
        'title': _('Category: %(name)s') % {'name': category.name},
    })


def newsletter_subscribe(request):
    """Public newsletter subscription view (no login required)."""
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            frequency = form.cleaned_data['frequency']

            defaults = {
                'is_subscribed': True,
                'frequency': frequency,
            }

            # Link to user if they are authenticated
            if request.user.is_authenticated:
                defaults['user'] = request.user

            Newsletter.objects.update_or_create(
                email=email,
                defaults=defaults,
            )
            messages.success(request, _('You have been subscribed to the newsletter.'))
            return redirect('frontend:articles:newsletter')
    else:
        form = NewsletterForm()

    return render(request, 'articles/newsletter.html', {
        'form': form,
        'title': _('Newsletter'),
    })


@lecturer_required
def article_create(request):
    """Create a new article (lecturers/professors only)."""
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.save()
            form.save_m2m()  # Save M2M fields (categories, tags)
            messages.success(request, _('Article created successfully.'))
            return redirect('frontend:articles:article_detail', slug=article.slug)
    else:
        form = ArticleForm()

    return render(request, 'articles/article_form.html', {
        'form': form,
        'title': _('Create Article'),
    })


@lecturer_required
def article_edit(request, slug):
    """Edit an existing article (lecturers/professors only)."""
    article = get_object_or_404(Article, slug=slug)

    # Only allow the author or superusers to edit
    if article.author != request.user and not request.user.is_superuser:
        messages.error(request, _('You can only edit your own articles.'))
        return redirect('frontend:articles:article_detail', slug=article.slug)

    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, _('Article updated successfully.'))
            return redirect('frontend:articles:article_detail', slug=article.slug)
    else:
        form = ArticleForm(instance=article)

    return render(request, 'articles/article_form.html', {
        'form': form,
        'article': article,
        'title': _('Edit Article'),
    })


@login_required
@require_POST
def comment_submit(request, pk):
    """Submit a comment on an article (POST only)."""
    article = get_object_or_404(Article, pk=pk)

    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.article = article
        comment.author = request.user
        comment.save()
        messages.success(request, _('Your comment has been submitted and is pending moderation.'))
    else:
        messages.error(request, _('There was an error with your comment. Please try again.'))

    return redirect('frontend:articles:article_detail', slug=article.slug)


@login_required
@require_POST
def article_like_toggle(request, pk):
    """Toggle like/unlike on an article (POST only)."""
    article = get_object_or_404(Article, pk=pk)

    like, created = Like.objects.get_or_create(article=article, user=request.user)

    if not created:
        # User already liked it, so unlike
        like.delete()
        # Update the likes_count (recount for accuracy)
        article.likes_count = Like.objects.filter(article=article).count()
        article.save(update_fields=['likes_count'])
        messages.info(request, _('You unliked this article.'))
    else:
        # Like was just created; the Like.save() method already incremented likes_count
        # Refresh to get the actual value after F() expression
        article.refresh_from_db()
        messages.success(request, _('You liked this article.'))

    return redirect('frontend:articles:article_detail', slug=article.slug)
