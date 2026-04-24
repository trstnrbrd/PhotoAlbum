from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from itertools import groupby
from .models import Category, Photo


# ── Auth ──────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('gallery')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('gallery')
        return render(request, 'photos/login.html', {'error': 'Invalid username or password.'})
    return render(request, 'photos/login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('gallery')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        password2 = request.POST.get('password2', '').strip()
        error = None
        if User.objects.count() >= 2:
            error = 'This space is already full. Only 2 accounts are allowed.'
        elif not username or not password:
            error = 'Please fill in all fields.'
        elif password != password2:
            error = 'Passwords do not match.'
        elif User.objects.filter(username=username).exists():
            error = 'That username is already taken.'
        else:
            user = User.objects.create_user(username=username, password=password)
            login(request, user)
            return redirect('gallery')
        return render(request, 'photos/register.html', {'error': error, 'username': username})
    return render(request, 'photos/register.html', {})


def logout_view(request):
    logout(request)
    return redirect('login')


# ── Gallery / Timeline ────────────────────────────────

@login_required(login_url='login')
def gallery(request):
    category_filter = request.GET.get('category')
    if category_filter:
        photos = Photo.objects.filter(category__name=category_filter).select_related('uploaded_by', 'category')
    else:
        photos = Photo.objects.all().select_related('uploaded_by', 'category')

    # Group by month-year for timeline
    grouped = {}
    for photo in photos:
        key = photo.created_at.strftime('%B %Y')
        grouped.setdefault(key, []).append(photo)

    categories = Category.objects.all()

    # Get partner
    partner = User.objects.exclude(id=request.user.id).first()

    context = {
        'grouped_photos': grouped,
        'categories': categories,
        'partner': partner,
        'category_filter': category_filter,
        'total': photos.count(),
    }
    return render(request, 'photos/gallery.html', context)


# ── Photo Detail ──────────────────────────────────────

@login_required(login_url='login')
def viewPhoto(request, pk):
    photo = get_object_or_404(Photo, id=pk)
    partner = User.objects.exclude(id=request.user.id).first()
    return render(request, 'photos/photo.html', {'photo': photo, 'partner': partner})


# ── Add Photo ─────────────────────────────────────────

@login_required(login_url='login')
def addPhoto(request):
    categories = Category.objects.all()

    if request.method == 'POST':
        data = request.POST
        image = request.FILES.get('image')

        if data['category'] != 'none':
            category = Category.objects.get(id=data['category'])
        elif data.get('category_new', '').strip():
            category, _ = Category.objects.get_or_create(name=data['category_new'].strip())
        else:
            category = None

        Photo.objects.create(
            category=category,
            description=data['description'],
            image=image,
            uploaded_by=request.user,
        )
        return redirect('gallery')

    partner = User.objects.exclude(id=request.user.id).first()
    return render(request, 'photos/add.html', {'categories': categories, 'partner': partner})


# ── Delete Photo ──────────────────────────────────────

@login_required(login_url='login')
def deletePhoto(request, pk):
    photo = get_object_or_404(Photo, id=pk)
    partner = User.objects.exclude(id=request.user.id).first()
    if request.method == 'POST':
        photo.image.delete(save=False)
        photo.delete()
        return redirect('gallery')
    return render(request, 'photos/delete_confirm.html', {'photo': photo, 'partner': partner})
