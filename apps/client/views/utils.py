import json

from django.shortcuts import render


def hydra_error_msg(exc):
    error = str(exc)
    try:
        error = json.loads(exc.raw[0])['error_hint']
    except Exception:
        pass
    return error


def client_error(request):
    title = request.GET.get('error')
    description = request.GET.get('error_description')
    hint = request.GET.get('error_hint')
    return render(request, 'client/error.html', {
        "title": title,
        "description": description,
        "hint": hint
    })
