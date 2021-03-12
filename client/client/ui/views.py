from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse

from .forms import RegisterForm
from .elgamal import *

def s1(request):
    g4powg2powP = modexp(request['g4'], request['g2powP'], request['p'])
    g4pow2powP_str = str(g4pow2powP)
    length = len(g4pow2powP_str)
    length_for_x = length // 9
    rem = length - length_for_x
    vertex = []
    for i in range(9):
        x = int(g4pow2powP_str[i*length_for_x: i*length_for_x + length_for_x])
        vertex.append(x)
    u4 = int(g4pow2powP_str[length_for_x*9: ])
    x4 = (vertex[0] + vertex[3] + vertex[6]) / 3 + u4
    y4 = (vertex[1] + vertex[4] + vertex[7]) / 3 + u4
    z4 = (vertex[2] + vertex[5] + vertex[8]) / 3 + u4
    vertex.append(x4)
    vertex.append(y4)
    vertex.append(z4)
    


def index(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data['user_name']
            password = form.cleaned_data['password']

            res = generate_keys(password)           

            s1(res)
            
            #Sending confirmation mail 
            """ current_site = get_current_site(request)
            mail_subject = 'Activate your account.'
            message = render_to_string('user/acc_active_email.html', {
                    'user': post,
                    'domain': current_site.domain,
                    'uid':urlsafe_base64_encode(force_bytes(post.pk)),
                    'token':account_activation_token.make_token(post),
            })
            to_email = form.cleaned_data.get('email_id')
            email = EmailMessage(
                mail_subject, message, to=[to_email]
            )
            email.send()
            return HttpResponse('Please confirm your email address to complete the registration') """
            return redirect('ui:login')
        else:
            message = 'Username is already registered.'
            form = RegisterForm()
            return render(request, 'ui/index.html', {'form': form, 'message':message})
    else:
        form = RegisterForm()
        return render(request, 'ui/index.html', {'form': form})