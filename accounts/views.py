from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView

from .forms import UserRegistrationForm
from .models import AppUser


class RegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = 'registration/register.html'
    success_url = '/'

    def form_valid(self, form):
        user = form.save()
        # Save in our app's 'users' table (not auth_user)
        AppUser.objects.get_or_create(user=user)
        login(self.request, user)
        return redirect(self.success_url)


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'


class CustomLogoutView(LogoutView):
    next_page = '/'
