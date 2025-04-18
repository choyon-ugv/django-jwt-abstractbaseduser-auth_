from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from .forms import RegisterForm, LoginForm, PasswordChangeForm, UserUpdateForm, ProfileUpdateForm
from .models import User, Movie, Comic, Blog, Comment, Like, Profile, WatchHistory
from django.utils import timezone

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                email=form.cleaned_data['email'],
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            messages.success(request, 'Registration successful! Please login.')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            if user is not None:
                auth_login(request, user)
                messages.success(request, 'Login successful!')
                # Redirect to 'next' parameter if present, else home
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid credentials')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


def logout(request):
    auth_logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('login')

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your password was successfully updated!')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'change_password.html', {'form': form})

def home(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    blogs = Blog.objects.all()[:3]
    comics = Comic.objects.all()[:6]
    return render(request, 'home.html', {'username': request.user.username,'blogs': blogs, 'comics': comics})

def movies(request):
    movies = Movie.objects.all()
    return render(request, 'movies.html', {'movies': movies})

# def movie_detail(request, pk):
#     movie = get_object_or_404(Movie, pk=pk)
#     return render(request, 'movie_detail.html', {'movie': movie})

def about(request):
    return render(request, 'about.html')


def comic(request):
    comics = Comic.objects.all()
    return render(request, 'comics.html', {'comics': comics})

def comic_detail_view(request, pk):
    comic = get_object_or_404(Comic, pk=pk)
    # Force fresh query to avoid caching
    comic = Comic.objects.get(pk=pk)
    return render(request, 'comic_detail.html', {'comic': comic})

@login_required
def comic_purchase(request, pk):
    comic = get_object_or_404(Comic, pk=pk)
    if request.user in comic.purchased_by.all():
        messages.warning(request, "You have already purchased this comic.")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': "You have already purchased this comic."})
    else:
        comic.purchased_by.add(request.user)
        messages.success(request, f"Successfully purchased {comic.title}!")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f"Successfully purchased {comic.title}!"})
    return redirect('comic_detail', pk=pk)

@login_required
def comic_favorite(request, pk):
    comic = get_object_or_404(Comic, pk=pk)
    if request.method == 'POST':
        if request.user in comic.favorited_by.all():
            messages.warning(request, "This comic is already in your favorites.")
            return JsonResponse({'success': False, 'message': "This comic is already in your favorites."})
        else:
            comic.favorited_by.add(request.user)
            messages.success(request, f"Added {comic.title} to favorites!")
            return JsonResponse({'success': True, 'message': f"Added {comic.title} to favorites!"})
    return redirect('comic_detail', pk=pk)

@login_required
def comic_unfavorite(request, pk):
    comic = get_object_or_404(Comic, pk=pk)
    if request.method == 'POST':
        if request.user not in comic.favorited_by.all():
            messages.warning(request, "This comic is not in your favorites.")
            return JsonResponse({'success': False, 'message': "This comic is not in your favorites."})
        else:
            comic.favorited_by.remove(request.user)
            messages.success(request, f"Removed {comic.title} from favorites!")
            return JsonResponse({'success': True, 'message': f"Removed {comic.title} from favorites!"})
    return redirect('comic_detail', pk=pk)

@login_required
def comic_read(request, pk):
    comic = get_object_or_404(Comic, pk=pk)
    if request.user not in comic.purchased_by.all():
        messages.error(request, "You must purchase this comic to read it.")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': "You must purchase this comic to read it."})
    else:
        if request.user not in comic.read_by.all():
            comic.read_by.add(request.user)
            messages.success(request, f"You have read {comic.title}!")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': f"You have read {comic.title}!"})
        messages.info(request, f"Reading {comic.title}.")  # Placeholder
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f"Reading {comic.title}."})
    return redirect('comic_detail', pk=pk)

@login_required
def profile_view(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)

    comics_purchased = request.user.purchased_comics.count()
    comics_read = request.user.read_comics.count()
    comics_favorited = request.user.favorited_comics.count()
    # Annotate favorite comics with delays
    favorite_comics = [
        {'comic': comic, 'delay': index * 100}
        for index, comic in enumerate(request.user.favorited_comics.order_by('-id')[:3])
    ]

    watch_history = WatchHistory.objects.filter(user=request.user).select_related('movie')
    movies_watched = watch_history.count()
    hours_streamed = sum(history.movie.runtime for history in watch_history) / 60 if watch_history else 0
    recently_watched = watch_history.order_by('-watched_at').first()

    blogs_written = request.user.blogs_written.count()
    blogs_liked = Like.objects.filter(user=request.user).count()
    comments_posted = Comment.objects.filter(user=request.user, user__isnull=False).count()

    total_activity = comics_purchased + comics_read + comics_favorited + movies_watched + blogs_written + blogs_liked + comments_posted
    max_activities = 100
    progress = min(int((total_activity / max_activities) * 100), 100)

    if progress <= 33:
        level = "Sidekick"
    elif progress <= 66:
        level = "Hero"
    else:
        level = "Superhero"

    profile.progress = progress
    profile.level = level
    profile.save()

    context = {
        'profile': profile,
        'comics_purchased': comics_purchased,
        'comics_read': comics_read,
        'comics_favorited': comics_favorited,
        'favorite_comics': favorite_comics,
        'movies_watched': movies_watched,
        'hours_streamed': round(hours_streamed, 1),
        'recently_watched': recently_watched,
        'blogs_written': blogs_written,
        'blogs_liked': blogs_liked,
        'comments_posted': comments_posted,
    }
    return render(request, 'profile.html', context)


def blog(request):
    blogs = Blog.objects.all()
    return render(request, 'blogs.html', {'blogs': blogs})


def blog_detail(request, blog_id):
    blog = get_object_or_404(Blog, id=blog_id)
    comments = Comment.objects.filter(blog=blog).order_by('-created_at')
    recent_blogs = Blog.objects.exclude(id=blog_id)[:5]
    likes_count = Like.objects.filter(blog=blog).count()
    user_liked = False
    if request.user.is_authenticated:
        user_liked = Like.objects.filter(blog=blog, user=request.user).exists()
    
    context = {
        'blog': blog,
        'comments': comments,
        'recent_blogs': recent_blogs,
        'likes_count': likes_count,
        'user_liked': user_liked,
    }
    return render(request, 'blog_details.html', context)

@login_required
def like_blog(request, blog_id):
    blog = get_object_or_404(Blog, id=blog_id)
    user = request.user

    if request.method == 'POST':
        liked = Like.objects.filter(blog=blog, user=user).exists()
        if liked:
            Like.objects.filter(blog=blog, user=user).delete()
            liked = False
        else:
            Like.objects.create(blog=blog, user=user)
            liked = True

        likes_count = blog.likes.count()
        return JsonResponse({
            'success': True,
            'liked': liked,
            'likes_count': likes_count
        })
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

@login_required
def add_comment(request, blog_id):
    blog = get_object_or_404(Blog, id=blog_id)
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            comment = Comment.objects.create(
                blog=blog,
                user=request.user,
                content=content,
                created_at=timezone.now()
            )
            return JsonResponse({
                'success': True,
                'comment_id': comment.id,
                'content': comment.content,
                'user_username': comment.user.username,
                'created_at': comment.created_at.strftime('%B %d, %Y %H:%M'),
                'comments_count': blog.comments.count()
            })
        return JsonResponse({'success': False, 'message': 'Comment cannot be empty'}, status=400)
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

@login_required
def edit_comment(request, blog_id, comment_id):
    blog = get_object_or_404(Blog, id=blog_id)
    comment = get_object_or_404(Comment, id=comment_id, blog=blog)
    
    # Check if the user is the comment author
    if comment.user != request.user:
        messages.error(request, "You are not authorized to edit this comment.")
        return redirect('blog_detail', blog_id=blog.id)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            comment.content = content
            comment.save()
            messages.success(request, "Comment updated successfully.")
            return redirect('blog_detail', blog_id=blog.id)
        else:
            messages.error(request, "Comment content cannot be empty.")
    
    return redirect('blog_detail', blog_id=blog.id)

@login_required
def delete_comment(request, blog_id, comment_id):
    blog = get_object_or_404(Blog, id=blog_id)
    comment = get_object_or_404(Comment, id=comment_id, blog=blog)
    
    # Check if the user is the comment author
    if comment.user != request.user:
        messages.error(request, "You are not authorized to delete this comment.")
        return redirect('blog_detail', blog_id=blog.id)
    
    if request.method == 'POST':
        comment.delete()
        messages.success(request, "Comment deleted successfully.")
        return redirect('blog_detail', blog_id=blog.id)
    
    return redirect('blog_detail', blog_id=blog.id)

def contact(request):
    return render(request, 'contact.html')

@login_required
def profile_update(request):
    user = request.user
    profile = user.profile
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=user)
        p_form = ProfileUpdateForm(instance=profile)
    return render(request, 'profile_update.html', {'u_form': u_form, 'p_form': p_form})