from django.shortcuts import redirect, render
from django.contrib import messages
from django.urls import reverse
from django.apps import apps


class ClientAdminAccessMiddleware:
   
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        
        if request.path.startswith('/admin/'):
            
            if 'client_id' in request.session and not request.user.is_authenticated:
                return render(request, 'restaurant/acces_refuse.html')

            if request.user.is_authenticated and not request.user.is_staff:
                messages.error(request, 'Accès interdit. Vous n\'avez pas les permissions d\'administration.')
                return redirect('restaurant:index')

        response = self.get_response(request)
        return response


class ClientSessionMiddleware:
    
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        
        if 'client_id' in request.session:
            try:
                
                Client = apps.get_model('restaurant', 'Client')
                client = Client.objects.get(id=request.session['client_id'])
                request.client = client
            except (Client.DoesNotExist, LookupError):
                if 'client_id' in request.session:
                    del request.session['client_id']
                request.client = None
        else:
            request.client = None

        response = self.get_response(request)
        return response
