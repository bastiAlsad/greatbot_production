from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.db.models.functions import TruncDay, TruncMonth
from django.contrib.auth.decorators import login_required
from . import forms, crawl_url, openAi
from . import models
from django.http import HttpResponse
from django.http import JsonResponse
import json
import os
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
import datetime
from django.core.serializers.json import DjangoJSONEncoder
from django.http import FileResponse

class CustomJSONEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super().default(obj)

def login_view(request):
    if request.method == "POST":
        form = forms.LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("/hub/")  # Replace 'home' with your home page URL name
    else:
        form = forms.LoginForm()
    return render(request, "registration/login.html", {"form": form})


@login_required(login_url="login")
def logout_view(request):
    logout(request)
    return redirect("login")  # Hier 'login' durch den Namen deiner Login-URL ersetzen


@login_required(login_url="login")
def home(request):
    customers = models.Customer.objects.filter(created_by = request.user)
    return render(request, "chat_bot_app/home.html", {"customers": customers})

@login_required(login_url="login")
def create_customer(request):
    if request.method == "POST":
        company_name = request.POST.get("company_name").lower()
        lead_email = request.POST.get("lead_email")
        color_code = request.POST.get("color_code")
        accent_color = request.POST.get("accent_color")
        website_url = request.POST.get("website_url")
        logo_url = request.POST.get("logo_url")
        subscription_model = request.POST.get("subscription_model")
        uploaded_files = request.FILES.getlist("file_upload")

        customer = models.Customer.objects.create(
            subscription_model=subscription_model,
            company_name=company_name,
            lead_email=lead_email,
            color_code=color_code,
            website_url=website_url,
            logo_url=logo_url,
            accent_color = accent_color,
            created_by=request.user
        )

        crawl_url.crawl_website(website_url, company_name)

        # Save the uploaded files
        if uploaded_files:
            
            upload_dir = os.path.join('uploaded_files', company_name)
            os.makedirs(upload_dir, exist_ok=True)
            for file in uploaded_files:
                file_path = os.path.join(upload_dir, file.name)
                with open(file_path, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)
        
        openAi.prepare_company_file(company_name)
        openAi.create_assistant(company_name, customer)

        return redirect(f"/edit-customer/{customer.id}/")
    
    return render(request, "chat_bot_app/create_customer.html")

@login_required(login_url="login")
def edit_customer(request, id=None):
    openAi.save_custom_embedding_code()
    customer = models.Customer.objects.get(id=id)
    if customer is None:
        return HttpResponse("Invalid Request")

    # Counts
    request_count = models.Request.objects.filter(created_for=customer.id).count()
    user_count = models.ChatbotUser.objects.filter(created_for=customer.id).count()
    leads_count = models.Lead.objects.filter(created_for=customer.id).count()
    conversion_rate = round(leads_count / user_count * 100, 2) if user_count > 0 else 0

    # Helper function to generate data for the charts
    def get_data(model, customer_id, field_name='created_at'):
        now = timezone.now()
        seven_days_ago = now - timedelta(days=7)
        one_month_ago = now - timedelta(days=30)
        one_year_ago = now - timedelta(days=365)

        total_data = model.objects.filter(created_for=customer_id).annotate(day=TruncDay(field_name)).values('day').annotate(count=Count('id')).order_by('day')
        week_data = model.objects.filter(created_for=customer_id, **{field_name + '__gte': seven_days_ago}).annotate(day=TruncDay(field_name)).values('day').annotate(count=Count('id')).order_by('day')
        month_data = model.objects.filter(created_for=customer_id, **{field_name + '__gte': one_month_ago}).annotate(day=TruncDay(field_name)).values('day').annotate(count=Count('id')).order_by('day')
        year_data = model.objects.filter(created_for=customer_id, **{field_name + '__gte': one_year_ago}).annotate(month=TruncMonth(field_name)).values('month').annotate(count=Count('id')).order_by('month')

        return {
            'total': list(total_data),
            'week': list(week_data),
            'month': list(month_data),
            'year': list(year_data),
        }

    request_data = get_data(models.Request, customer.id)
    user_data = get_data(models.ChatbotUser, customer.id)
    lead_data = get_data(models.Lead, customer.id)
    top_questions = (models.Themengebiet.objects
                     .filter(created_for=customer.id)
                     .values('themenbereich')
                     .annotate(amount=Count('id'))
                     .order_by('-amount')[:7])

    print(lead_data)
    
    context = {
        "customer": customer,
        "leads_count": leads_count,
        "request_count": request_count,
        "user_count": user_count,
        "conversion_rate": conversion_rate,
        "request_data": json.dumps(request_data, cls=CustomJSONEncoder),
        "user_data": json.dumps(user_data, cls=CustomJSONEncoder),
        "lead_data": json.dumps(lead_data, cls=CustomJSONEncoder),
        "top_questions_data": json.dumps(list(top_questions), cls=CustomJSONEncoder),
    }

    return render(request, 'chat_bot_app/edit_customer.html', context)



@login_required(login_url="login")
def update_customer(request):
    try:
        data = json.loads(request.body)
        customer_id = data['customer_id']
        field = data['field']
        value = data['value']

        customer = models.Customer.objects.get(id=customer_id)
        setattr(customer, field, value)
        customer.save()

        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
    
@login_required(login_url="login")
def delete_customer(request, id = None):
    customer = models.Customer.objects.get(id = id)
    if customer.created_by == request.user:
        customer.delete()
        return redirect("/hub/")
    return redirect("/hub/")


def dynamic_js(request, partner=None):
    file_path = "D:/DEV/chat_bot/chat_bot/chat_bot_app/templates/chat_bot_app/webflow.js"  # in production ändern !
    return FileResponse(open(file_path, 'rb'), content_type='application/javascript')


def dynamic_css(request, partner=None):
    customer = models.Customer.objects.get(company_name=partner)

    print(customer.color_code)
    print(customer.accent_color)
    
    css = f"""
    :root {{
        --is-dark: #060606; /* background color */
        --dark-accent: {customer.accent_color}; /* top color bottom color */
        --is-bright: #f5f5f5; /* background color white mode */
        --brand-accent: {customer.color_code}; /* color of user sent message and border color */
        --is-transparent: transparent;
        --customer-color: {customer.color_code};
        --customer-accent: {customer.color_code};  /* Additional color if needed */
    }}

    body {{
        font-family: Arial, sans-serif;
        background-color: #e6e6e6;
        margin: 0;
        padding: 0;
        height: 100%;
    }}

    .chat-container {{
        height: 100%;
        background-color: var(--is-bright);
        border-radius: 20px;
        overflow: hidden;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
    }}

    .chat-header {{
        background-color: var(--customer-color);
        color: white;
        padding: 20px;
        text-align: center;
        position: relative;
    }}

    .chat-header .back-button {{
        position: absolute;
        left: 30px;
        top: 13px;
        height: 50px;
        width: 50px;
        background-color: white;
        border-radius: 40px;
        align-content: center;
    }}

    .chat-header .back-button img {{
        height: 30px;
        width: 30px;
    }}

    .chat-header .status {{
        font-size: 14px;
        color: #ffffff;
    }}

    .chat-messages {{
        padding: 20px;
        height: 500px;
        overflow-y: auto;
        background-color: var(--is-dark);
    }}

    .form-container {{
        display: flex;
        flex-direction: column;
    }}

    .form-container form {{
        display: flex;
        flex-direction: column;
    }}

    .form-container label {{
        margin-bottom: 5px;
        font-size: 14px;
        color: var(--is-dark);
    }}

    .form-container input {{
        padding: 10px;
        margin-bottom: 15px;
        border: 1px solid var(--dark-accent);
        border-radius: 5px;
        font-size: 14px;
    }}

    .message {{
        margin-bottom: 20px;
        display: flex;
        align-items: flex-end;
    }}

    .message.sent .text {{
        background-color: var(--customer-color);
        color: white;
        margin-left: auto;
    }}

    .message.received .text {{
        background-color: var(--is-bright);
        color: var(--is-dark);
        border: 1px solid var(--dark-accent);
    }}

    .message .text {{
        max-width: 60%;
        padding: 10px 15px;
        border-radius: 15px;
        line-height: 1.4;
        font-size: 14px;
        position: relative;
    }}

    .message.sent .text::after {{
        right: 15px;
        border-left: 8px solid transparent;
        border-right: 8px solid var(--customer-color);
        border-top: 8px solid var(--customer-color);
        border-bottom: 8px solid transparent;
    }}

    .message.received .text::after {{
        left: 15px;
        border-left: 8px solid transparent;
        border-right: 8px solid var(--dark-accent);
        border-top: 8px solid var(--dark-accent);
        border-bottom: 8px solid transparent;
    }}

    .chat-input {{
        display: flex;
        padding: 10px;
        border-top: 1px solid var(--dark-accent);
        background-color: var(--is-bright);
    }}

    .chat-input input {{
        flex: 1;
        padding: 10px;
        border: none;
        border-radius: 20px;
        background-color: var(--dark-accent);
        color: var(--is-bright);
        margin-right: 10px;
        outline: none;
    }}

    .chat-input button {{
        background-color: var(--customer-color);
        color: white;
        padding: 10px 20px;
        border: none;
        border-radius: 20px;
        cursor: pointer;
        outline: none;
    }}

    @keyframes bounce {{
        0%, 100% {{
            transform: translateY(0);
        }}
        50% {{
            transform: translateY(-10px);
        }}
    }}

    .loading-dots {{
        display: inline-block;
        font-size: 24px;
    }}

    .loading-dots span {{
        display: inline-block;
        animation: bounce 1s infinite;
    }}

    .loading-dots span:nth-child(2) {{
        animation-delay: 0.2s;
    }}

    .loading-dots span:nth-child(3) {{
        animation-delay: 0.4s;
    }}

    .open-chat-btn {{
        z-index: 999;
        aspect-ratio: 1;
        background-image: radial-gradient(circle farthest-corner at 50% 50%, var(--dark-accent), var(--is-dark) 33%, #142019 75%);
        cursor: pointer;
        border: .1rem solid var(--brand-accent);
        border-radius: 100vw;
        justify-content: center;
        align-items: center;
        width: 4.5rem;
        height: 4.5rem;
        line-height: 1.5;
        display: flex;
        position: fixed;
        inset: auto 3rem 3rem auto;
    }}

    .icon-chat {{
        aspect-ratio: 1;
        width: 2.25rem;
        height: 2.25rem;
        display: block;
    }}

    .open-chat-wrapper {{
        z-index: 999;
        background-color: var(--is-dark);
        border: .1rem solid var(--brand-accent);
        border-radius: 1.25rem;
        width: 25rem;
        height: 40rem;
        position: fixed;
        inset: auto 3rem 8rem auto;
        overflow: clip;
    }}

    .top-open-widget {{
        grid-column-gap: 1rem;
        grid-row-gap: 1rem;
        background-color: var(--dark-accent);
        box-shadow: 0 2px 5px 0 var(--dark-accent);
        justify-content: flex-start;
        align-items: center;
        width: 100%;
        height: 4rem;
        padding: .5rem 1rem;
        display: flex;
        position: relative;
    }}

    .mid-open-chat {{
        box-sizing: border-box;
        grid-column-gap: 1rem;
        grid-row-gap: 1rem;
        background-color: var(--is-dark);
        flex-flow: column;
        justify-content: flex-start;
        align-items: flex-start;
        width: 100%;
        height: 31.5rem;
        padding: 1rem;
        display: flex;
        overflow: hidden scroll;
    }}

    .btm-open-chat {{
        background-color: var(--dark-accent);
        box-shadow: 0 -2px 5px 0 var(--dark-accent);
        width: 100%;
        height: 4.5rem;
        padding: 1rem 1rem .5rem;
    }}

    .txt-top-wrapper {{
        color: var(--is-bright);
        flex-flow: column;
        justify-content: center;
        align-items: flex-start;
        width: 100%;
        display: flex;
    }}

    .chat-h-small {{
        margin-bottom: .25rem;
    }}

    .chat-sub-h {{
        opacity: .75;
        font-size: 12px;
    }}

    .form-field-horizontal {{
        grid-column-gap: 1rem;
        grid-row-gap: 1rem;
        justify-content: center;
        align-items: center;
        display: flex;
    }}
###################################################################
    .input-field {{
        border: .1rem solid var(--brand-accent);
        background-color: var(--is-bright);
        color: var(--is-dark);
        border-radius: .5rem;
        align-self: flex-start;
        height: 2rem;
        margin-bottom: 0;
    }}

    .submit-btn {{
        grid-column-gap: .5rem;
        grid-row-gap: .5rem;
        border: .1rem solid var(--brand-accent);
        background-color: var(--is-dark);
        color: var(--is-bright);
        border-radius: .5rem;
        justify-content: center;
        align-self: center;
        align-items: center;
        height: 2rem;
        padding: .25rem 1rem;
        transition: all .35s cubic-bezier(.445, .05, .55, .95);
        display: flex;
    }}

    .submit-btn:hover {{
        background-color: var(--brand-accent);
        color: var(--is-dark);
    }}

    .submit-btn.is-left {{
        align-self: flex-start;
    }}

    .btn-txt {{
        font-size: 12px;
    }}

    .open-icon-chat {{
        aspect-ratio: 1;
        width: 2.5rem;
        height: 2.5rem;
        display: block;
        position: absolute;
        inset: auto;
    }}

    .msg-bot {{
        border: .1rem solid var(--dark-accent);
        background-color: var(--is-bright);
        color: var(--is-dark);
        border-radius: 1rem;
        align-self: flex-start;
        max-width: 75%;
        padding: 1rem;
    }}

    .txt-bot-msg {{
        margin-bottom: 0;
        font-size: 12px;
    }}

    .txt-bot-msg.is-h {{
        font-weight: 700;
    }}

    .msg-user {{
        border: .1rem solid var(--dark-accent);
        background-color: var(--brand-accent);
        color: var(--is-dark);
        border-radius: 1rem;
        align-self: flex-end;
        max-width: 75%;
        padding: 1rem;
        display: flex;
    }}

    .txt-user-msg {{
        font-size: 12px;
    }}

    .msg-initial {{
        grid-column-gap: .5rem;
        grid-row-gap: .5rem;
        border: .1rem solid var(--dark-accent);
        background-color: var(--is-bright);
        color: var(--is-dark);
        border-radius: 1rem;
        flex-flow: column;
        align-self: flex-start;
        max-width: 75%;
        padding: 1rem;
        display: flex;
    }}

    .form-fields-vertical {{
        grid-column-gap: .5rem;
        grid-row-gap: .5rem;
        flex-flow: column;
        justify-content: flex-start;
        align-items: flex-start;
        display: flex;
    }}

    .bot-profile-svg {{
        aspect-ratio: 1;
        object-fit: cover;
        border-radius: 100vw;
        width: 2.75rem;
        height: 2.75rem;
    }}

    .msg-form {{
        border: .1rem solid var(--dark-accent);
        background-color: var(--is-bright);
        color: var(--is-dark);
        border-radius: 1rem;
        align-self: flex-start;
        max-width: 75%;
        padding: 1rem;
    }}

    .mobile-close, .mob-clo {{
        z-index: 999;
        aspect-ratio: 1;
        background-image: radial-gradient(circle farthest-corner at 50% 50%, var(--dark-accent), var(--is-dark) 33%, #142019 75%);
        cursor: pointer;
        border: .1rem solid var(--brand-accent);
        border-radius: 100vw;
        justify-content: center;
        align-items: center;
        width: 4.5rem;
        height: 4.5rem;
        line-height: 1.5;
        display: flex;
        position: fixed;
        inset: auto 3rem 3rem auto;
    }}

    .close-chat-btn {{
        cursor: pointer;
        display: none;
    }}

    @media screen and (max-width: 991px) {{
        .open-chat-btn {{
            width: 3.5rem;
            height: 3.5rem;
            bottom: 1.5rem;
            right: 2rem;
        }}

        .icon-chat {{
            width: 2rem;
            height: 2rem;
        }}

        .open-chat-wrapper {{
            width: 20rem;
            height: 33rem;
            bottom: 5.75rem;
            right: 2rem;
        }}

        .top-open-widget {{
            height: 3rem;
        }}

        .mid-open-chat {{
            height: 25.5rem;
        }}

        .btm-open-chat {{
            height: 4.5rem;
        }}

        .chat-h-small {{
            font-size: 14px;
        }}

        .chat-sub-h {{
            font-size: 10px;
        }}

        .form-wrapper {{
            margin-bottom: 0;
        }}

        .open-icon-chat {{
            width: 2.5rem;
            height: 2.5rem;
        }}

        .bot-profile-svg {{
            width: 2.33rem;
            height: 2.33rem;
        }}

        .mobile-close, .mob-clo {{
            width: 3.5rem;
            height: 3.5rem;
            bottom: 1.5rem;
            right: 2rem;
        }}
    }}

    @media screen and (max-width: 479px) {{
        .open-chat-btn {{
            right: .75rem;
        }}

        .open-chat-btn.is-mobile {{
            height: auto;
            position: static;
        }}

        .open-chat-wrapper {{
            width: 100%;
            height: 100%;
            bottom: 0;
            right: 0;
        }}

        .top-open-widget {{
            height: 10%;
        }}

        .mid-open-chat {{
            grid-column-gap: .75rem;
            grid-row-gap: .75rem;
            height: 80%;
        }}

        .btm-open-chat {{
            justify-content: center;
            align-items: center;
            height: 10%;
            padding-bottom: 1rem;
            display: flex;
        }}

        .chat-h-small {{
            font-size: 12px;
        }}

        .form-field-horizontal {{
            justify-content: center;
            align-items: center;
        }}

        .form-wrapper {{
            width: 100%;
        }}

        .open-icon-chat {{
            width: 2rem;
            height: 2rem;
        }}

        .mobile-close, .mob-clo {{
            height: auto;
            position: static;
            right: .75rem;
        }}

        .close-chat-trigger, .close-chat-btn {{
            aspect-ratio: 1;
            border: .1rem solid var(--brand-accent);
            border-radius: 100vw;
            justify-content: center;
            align-items: center;
            width: 3.5rem;
            display: flex;
        }}
    }}
    """
    return HttpResponse(css, content_type='text/css')
