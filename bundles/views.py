from django.shortcuts import render, get_object_or_404
from .models import Bundle

# Create your views here.

def bundle_list(request):
    bundles = Bundle.objects.all()
    return render(request, 'bundles/bundle_list.html', {'bundles': bundles})

def bundle_detail(request, pk):
    bundle = get_object_or_404(Bundle, pk=pk)
    return render(request, 'bundles/bundle_detail.html', {'bundle': bundle})
