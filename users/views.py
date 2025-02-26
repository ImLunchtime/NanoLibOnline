from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile

# Create your views here.

@login_required
def profile_view(request):
    return render(request, 'users/profile.html', {'profile': request.user.profile})

@login_required
def profile_edit(request):
    if request.method == 'POST':
        # Add form handling logic here
        pass
    return render(request, 'users/profile_edit.html', {'profile': request.user.profile})
