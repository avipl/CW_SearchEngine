from django.shortcuts import render
from django.http import HttpResponse
from . import search_code
# Create your views here.

def index(response):
    return render(response,"imdb_app/search_home.html",{})


def search_results(request):
    search_query = request.GET.get('q')
    search_type = request.GET.get('search-type')
    s=search_code.Search(search_query,search_type)
    s_result=s.res_return()
    # Your search logic here

    return render(request, 'imdb_app/search_results.html', {
        'search_query': search_query,
        'search_type': search_type,
        'result' : s_result
    })
