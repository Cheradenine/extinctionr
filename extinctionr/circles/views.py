from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django import forms
from django.views import generic
from extinctionr.utils import get_contact
from .models import Circle, Contact
from dal import autocomplete


class ContactForm(forms.Form):
    contact = forms.ModelChoiceField(
        required=False,
        queryset=Contact.objects.all(),
        label='Lookup',
        widget=autocomplete.ModelSelect2(url='circles:person-autocomplete', attrs={'class': 'form-control'}))
    email = forms.EmailField(label="Email", required=False, widget=forms.EmailInput(attrs={'class': 'form-control text-center', 'placeholder': 'Email Address'}))
    name = forms.CharField(required=False, label="Name", widget=forms.TextInput(attrs={'class': 'form-control text-center', 'placeholder': 'Your Name'}))

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data['contact']:
            if not (cleaned_data['email'] and cleaned_data['name']):
                raise forms.ValidationError('email or contact required')
        return cleaned_data


@login_required
def add_member(request, pk):
    circle = get_object_or_404(Circle, pk=pk)
    form = ContactForm(request.POST)
    if form.is_valid():
        data = form.cleaned_data
        email = data['email'].lower()
        name = data['name']
        contact = data['contact']
        circle.add_member(email, name, contact=contact)
    return redirect(circle.get_absolute_url())


@login_required
def person_view(request, contact_id):
    contact = get_object_or_404(Contact, pk=contact_id)
    ctx = {'contact': contact}
    response = render(request, 'circles/person.html', ctx)
    response['Cache-Control'] = 'private'
    return response


class CircleView(generic.DetailView):
    template_name = 'circles/circle.html'
    def get_queryset(self):
        return Circle.objects.select_related('parent').prefetch_related('leads', 'members')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['can_see_members'] = self.request.user.has_perm('circles.view_circle')
            context['is_lead'] = self.request.user.has_perm('circles.change_circle') or context['object'].leads.filter(pk=get_contact(email=self.request.user.email).id).exists()
            context['members'] = list(context['object'].members.all())
            context['form'] = ContactForm()
        return context

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        response['Cache-Control'] = 'private'
        return response


class TopLevelView(generic.ListView):
    template_name = 'circles/outer.html'

    def get_queryset(self):
        return  Circle.objects.filter(parent__isnull=True).prefetch_related('leads', 'members')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_see_members'] = self.request.user.has_perm('circles.view_circle')
        return context

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        response['Cache-Control'] = 'private'
        return response


class ContactAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Contact.objects.none()

        qs = Contact.objects.all()

        if self.q:
            qs = qs.filter(email__istartswith=self.q)

        return qs

