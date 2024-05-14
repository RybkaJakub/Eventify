from django.shortcuts import render

def index(request):
    user = request.user
    divider_rendered = False
    for group in user.groups.all():
        if group.name == "eventer" or group.name == "admin":
            divider_rendered = True
            break

    context = {
        'divider_rendered': divider_rendered,
    }
    return render(request, 'index.html', context=context)