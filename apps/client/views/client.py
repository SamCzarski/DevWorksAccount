from devworks_hydra.rest import Clients, HydraRequestError
from django.contrib.admin.views.decorators import staff_member_required
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from apps.client.forms import ClientForm
from apps.client.utils import for_hydra, from_hydra
from apps.client.views.utils import hydra_error_msg


@staff_member_required
def client_list(request):
    clients = Clients()
    all_clients = list(clients.all())
    """
    This is odd cause there is no filter on the hydra server for listing clients
    so we get them ALL then, filter them in python
    """
    client_types = list({", ".join(i['grant_types']) for i in all_clients})
    filter = request.GET.get('filter')
    if filter:
        all_clients = [x for x in all_clients if ", ".join(x['grant_types']) == filter]
    return render(
        request,
        'client/list.html',
        {
            'clients': all_clients,
            'client_types': client_types
        })


@staff_member_required
def client_delete(request, clientid):
    clients = Clients()
    clients.delete(clientid)
    return HttpResponseRedirect(reverse('clients'))


@staff_member_required
def web_client_create(request):
    form = ClientForm()
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            data = for_hydra(form.cleaned_data)
            data['grant_types'] = ['implicit']
            data['response_types'] = ['token id_token']
            clients = Clients()
            # @todo: catch exceptions and errors
            try:
                clients.create(data)
            except HydraRequestError as exc:
                error = hydra_error_msg(exc)
                return render(
                    request,
                    'client/modify.html',
                    {'form': form, 'error': error}
                )
            return HttpResponseRedirect(reverse('clients'))
    return render(
        request,
        'client/modify.html',
        {'form': form}
    )


@staff_member_required
def web_client_edit(request, clientid):
    clients = Clients()
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            data = for_hydra(form.cleaned_data)
            data['client_id'] = clientid
            data['grant_types'] = ['implicit']
            data['response_types'] = ['token id_token']
            # @todo: catch exceptions and errors
            try:
                clients.update(clientid, data)
            except HydraRequestError as exc:
                error = hydra_error_msg(exc)
                return render(
                    request,
                    'client/modify.html',
                    {'form': form, 'error': error}
                )
            return HttpResponseRedirect(reverse('clients'))

    data = clients.get(clientid)
    form = ClientForm(from_hydra(data))
    return render(
        request,
        'client/modify.html',
        {'form': form}
    )


@staff_member_required
def mobile_client_create(request):
    form = ClientForm()
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            data = for_hydra(form.cleaned_data)
            data['grant_types'] = ['refresh_token', 'authorization_code']
            data['response_types'] = ['code', 'id_token']
            data["token_endpoint_auth_method"] = "none"
            clients = Clients()
            try:
                clients.create(data)
            except HydraRequestError as exc:
                error = hydra_error_msg(exc)
                return render(
                    request,
                    'client/modify.html',
                    {'form': form, 'error': error}
                )
            return HttpResponseRedirect(reverse('clients'))
    return render(
        request,
        'client/modify.html',
        {'form': form, }
    )


@staff_member_required
def mobile_client_edit(request, clientid):
    clients = Clients()
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            data = for_hydra(form.cleaned_data)
            data['client_id'] = clientid
            data['grant_types'] = ['refresh_token', 'authorization_code']
            data["token_endpoint_auth_method"] = "none"
            try:
                clients.update(clientid, data)
            except HydraRequestError as exc:
                error = hydra_error_msg(exc)
                return render(
                    request,
                    'client/modify.html',
                    {'form': form, 'error': error}
                )
            return HttpResponseRedirect(reverse('clients'))

    data = clients.get(clientid)
    form = ClientForm(from_hydra(data))
    return render(
        request,
        'client/modify.html',
        {'form': form, }
    )
