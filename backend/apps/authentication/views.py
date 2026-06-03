from django.shortcuts import render


def login_view(request):
    # Esto busca el archivo en templates/autenticacion/login.html
    return render(request, 'authentication/login.html')
