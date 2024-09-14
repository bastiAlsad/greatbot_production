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
    customers = models.Customer.objects.filter(created_by=request.user)
    return render(request, "chat_bot_app/home.html", {"customers": customers})


def validate_jsonl_file(file):
    file.seek(0)  # Stelle sicher, dass der Datei-Zeiger am Anfang ist
    lines = file.readlines()

    # Zähle die Zeilen (Trainingseinträge)
    if len(lines) < 2:
        return False
    return True


@login_required(login_url="login")
def create_customer(request):
    if request.method == "POST":
        company_name = request.POST.get("company_name").lower()
        lead_email = request.POST.get("lead_email")
        # color_code = request.POST.get("color_code")
        # accent_color = request.POST.get("accent_color")
        logo_url = request.POST.get("logo_url")
        subscription_model = request.POST.get("subscription_model")
        # website_url = request.POST.get("website_url")

        # Erhalte die hochgeladene Datei
        uploaded_file = request.FILES.get("file_upload")
        if uploaded_file is None:
            return HttpResponse("Es muss eine Datei hochgeladen werden.")
        if not validate_jsonl_file(uploaded_file):
            return HttpResponse("Die Datei muss mindestens 2 Zeilen Lang sein.")

        css_url = f"/api/{company_name}/dynamic-css/"
        js_url = f"/api/{company_name}/dynamic-js/"

        customer = models.Customer.objects.create(
            subscription_model=subscription_model,
            company_name=company_name,
            lead_email=lead_email,
            # color_code=color_code,
            logo_url=logo_url,
            # accent_color=accent_color,
            created_by=request.user,
            code=f"""<div id="chatbot-container">
    <meta name="csrf-token-greatbot-ai" content="{{ csrf_token }}">
    <meta name="save-user-data-url-greatbot-ai" content="saveuserdata"> -->

    <link rel="stylesheet" type="text/css" href="greatbot.eu.pythonanywhere.com{css_url}">
    <div id="chatbot">
        <div id="chatbot-button" onclick="toggleChat()">💬</div>
        <div id="chatbot-window">
            <div class="chat-header">
                <button class="back-button" onclick="toggleChat()">X</button>
                Chat Assistant
            </div>
            <div class="chat-messages" id="chatMessages">
                <div class="message received">
                    <div class="text">
                        <h4>Hey! Herzlich willkommen 👋🏼</h4>
                        Ich bin Greatbot und beantworte Ihnen gerne alle Fragen zu unseren Leistungen und unserem
                        Unternehmen laxout - wie kann ich Ihnen helfen?
                    </div>
                </div>
            </div>
            <div class="chat-input">
                <input type="text" id="messageInput" placeholder="Fragen Sie etwas...">
                <button onclick="sendMessage()">Senden</button>
            </div>
        </div>
    </div>
    <script type="text/javascript" src="greatbot.eu.pythonanywhere.com{js_url}"></script>

</div>""",
            css_code=f"""
    :root {{
/* Senden Button*/
            --button-text-color: white;
            --button-color: #4ec0c2;
            --button-border-color: #4ec0c2;

/* Cheat header wo assistant chat und x button drin sind*/
            --header-color: #4ec0c2;
            --header-text-color:white;

/* X Button links oben*/
            --back-button-color: white;
            --back-button-text-color: black;

/* Input Feld der User Nachricht*/
            --input-field-color: #F2F0F7;
            --input-field-text-color: black;
            --input-field-border-color: #F2F0F7;
            
/* Section ganz unten wo das input field und der button drin sind*/
            --footer-color: white;  
          
/* Bot Nachricht*/
            --bot-message-color: white;
            --bot-message-text-color: black;
            --bot-message-border-color: #DDD;

/*  User Nachricht*/
            --user-message-color: #4ec0c2;
            --user-message-text-color: white;
            --user-message-border-color: #4ec0c2;

/*  Button der den Chat aus und einklappt*/
            --chat-button-color: #4ec0c2;
            --chat-button-text-color: white;
            --chat-button-border-color: #4ec0c2;

/*  Chat Hintergrund*/
            --chat-background-color: #F2F0F7 ;
            
        }}
        #chatbot-container {{
            font-family: Arial, sans-serif;
            background-color: var(--chat-background-color);
            border-color: var(--chat-border-color);
            margin: 0;
            padding: 0;
        }}

        #chatbot {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 9999;
        }}

        #chatbot-button {{
            background-color: var(--chat-button-color);
            border: solid 2px var(--chat-button-border-color);
            color: var(--chat-button-text-color);
            padding: 15px;
            border-radius: 50%;
            cursor: pointer;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
        }}

        #form-container {{
            display: flex;
            flex-direction: column;
        }}

        #chatbot-window {{
            display: none;
            width: 400px;
            height: 500px;
            background-color: white;
            border-radius: 20px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
            position: absolute;
            bottom: 60px;
            right: 0;
            overflow: hidden;
            flex-direction: column;
            justify-content: space-between;
            transform: scale(0);
            transform-origin: bottom right;
            transition: transform 0.3s ease;
        }}

        #chatbot-window.open {{
            transform: scale(1);
        }}

        @media screen and (max-width: 600px) {{
            #chatbot {{
                bottom: 20px;
                right: 20px;
            }}

            #chatbot-window {{
                width: 100vw;
                height: 100vh;
                bottom: 0;
                right: 0;
                border-radius: 0;
                transform-origin: bottom right;
            }}

            #chatbot.open {{
                bottom: 0;
                right: 0;
            }}
        }}

        #chatbot-container .chat-header {{
            background-color: var(--header-color);
            color: var(--header-text-color);
            padding: 15px;
            text-align: center;
            position: relative;
        }}

        #chatbot-container .chat-header .back-button {{
            position: absolute;
            left: 10px;
            top: 10px;
            background-color: var(--back-button-color);
            color: var(--back-button-text-color);
            border: none;
            border-radius: 50%;
            height: 30px;
            width: 30px;
            cursor: pointer;
        }}

        #chatbot-container .chat-messages {{
            padding: 20px;
            height: calc(100% - 100px);
            overflow-y: auto;
            background-color: var(--chat-background-color);
        }}

        #chatbot-container .chat-input {{
            display: flex;
            padding: 10px;
            background-color: var(--footer-color);
        }}

        #chatbot-container .chat-input input {{
            flex: 1;
            padding: 10px;
            border: solid 2px var(--input-field-border-color);
            color: var(--input-field-text-color);
            border-radius: 20px;
            background-color: var(--input-field-color);
            margin-right: 10px;
            outline: none;
        }}

        #chatbot-container .chat-input button {{
            background-color: var(--button-color);
            border: solid 2px var(--button-border-color);
            color: var(--button-text-color);
            padding: 10px 20px;
            border-radius: 20px;
            cursor: pointer;
            outline: none;
        }}

        #chatbot-container .message {{
            margin-bottom: 10px;
            display: flex;
            align-items: flex-end;
        }}

        #chatbot-container .message.sent .text {{
            background-color: var(--user-message-color);
            color: var(--user-message-text-color);
            border: solid 2px var(--user-message-border-color);
            margin-left: auto;
            border-radius: 15px 15px 0 15px;
        }}

        #chatbot-container .message.received .text {{
            background-color: var(--bot-message-color);
            color: var(--bot-message-text-color);
            border: 1px solid var(--bot-message-border-color);
            border-radius: 15px 15px 15px 0;
        }}

        #chatbot-container .message .text {{
            max-width: 60%;
            padding: 10px 15px;
            line-height: 1.4;
            font-size: 14px;
        }}
    """,
            # website_url=website_url,
        )
        print(customer.code)
        # crawl_url.crawl_website(website_url, company_name)

        # Überprüfe, ob eine Datei hochgeladen wurde
        if uploaded_file:
            upload_dir = os.path.join("uploaded_files", company_name)
            os.makedirs(upload_dir, exist_ok=True)

            # Speichern der Datei
            file_path = os.path.join(upload_dir, uploaded_file.name)
            with open(file_path, "wb+") as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            # Speichere den Dateipfad in der Datenbank
            customer.training_file_path = file_path
        customer.save()

        # openAi.prepare_company_file(company_name)
        # openAi.create_fine_tuning_model(company_name, customer)
        # openAi.prepare_company_file(company_name)
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
    def get_data(model, customer_id, field_name="created_at"):
        now = timezone.now()
        seven_days_ago = now - timedelta(days=7)
        one_month_ago = now - timedelta(days=30)
        one_year_ago = now - timedelta(days=365)

        total_data = (
            model.objects.filter(created_for=customer_id)
            .annotate(day=TruncDay(field_name))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
        week_data = (
            model.objects.filter(
                created_for=customer_id, **{field_name + "__gte": seven_days_ago}
            )
            .annotate(day=TruncDay(field_name))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
        month_data = (
            model.objects.filter(
                created_for=customer_id, **{field_name + "__gte": one_month_ago}
            )
            .annotate(day=TruncDay(field_name))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
        year_data = (
            model.objects.filter(
                created_for=customer_id, **{field_name + "__gte": one_year_ago}
            )
            .annotate(month=TruncMonth(field_name))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )

        return {
            "total": list(total_data),
            "week": list(week_data),
            "month": list(month_data),
            "year": list(year_data),
        }

    request_data = get_data(models.Request, customer.id)
    user_data = get_data(models.ChatbotUser, customer.id)
    lead_data = get_data(models.Lead, customer.id)
    top_questions = (
        models.Themengebiet.objects.filter(created_for=customer.id)
        .values("themenbereich")
        .annotate(amount=Count("id"))
        .order_by("-amount")[:7]
    )

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

    return render(request, "chat_bot_app/edit_customer.html", context)


@login_required(login_url="login")
def update_customer(request):
    try:
        data = json.loads(request.body)
        customer_id = data["customer_id"]
        field = data["field"]
        value = data["value"]

        customer = models.Customer.objects.get(id=customer_id)
        setattr(customer, field, value)
        customer.save()

        return JsonResponse({"status": "success"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})


@login_required(login_url="login")
def delete_customer(request, id=None):
    customer = models.Customer.objects.get(id=id)
    if customer.created_by == request.user:
        customer.delete()
        return redirect("/hub/")
    return redirect("/hub/")


def dynamic_js(request, partner=None):
    file_path = "/home/greatbot/greatbot_production/chat_bot_app/templates/chat_bot_app/greatbot.js"  # in production ändern !
    return FileResponse(open(file_path, "rb"), content_type="application/javascript")


def dynamic_css(request, partner=None):
    customer = models.Customer.objects.get(company_name=partner)
    css = customer.css_code
    return HttpResponse(css, content_type="text/css")
