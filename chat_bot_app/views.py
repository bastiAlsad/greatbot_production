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

import PyPDF2

def extract_text_from_pdf(file_path):
    with open(file_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text

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
    lead_amount = 0
    for customer in customers:
        lead_amount += len(models.Lead.objects.filter(created_for=customer.id))

    return render(
        request,
        "chat_bot_app/home.html",
        {
            "customers": customers,
            "lead_amount": lead_amount,
            "user_amount": len(customers),
        },
    )


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

        css_url = f"/api/{company_name}/dynamic-css/"
        js_url = f"/api/{company_name}/dynamic-js/"
        token = "{{csrf_token}}"

        customer = models.Customer.objects.create(
            subscription_model=subscription_model,
            company_name=company_name,
            lead_email=lead_email,
            # color_code=color_code,
            logo_url=logo_url,
            # accent_color=accent_color,
            created_by=request.user,
            code=f"""
<div id="chatbot-container">
    <meta name="company-name-greatbot-ai" content="{company_name}">
    <link rel="stylesheet" type="text/css" href="https://greatbot.eu.pythonanywhere.com{css_url}">
    <div id="chatbot">
        <div id="chatbot-button" onclick="toggleChat()"><svg style="width: 50px; height: 50px;" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M121.74 67.3201C123.591 67.3201 125.401 67.8691 126.94 68.8976C128.479 69.926 129.679 71.3879 130.388 73.0982C131.096 74.8085 131.281 76.6905 130.92 78.5062C130.559 80.3218 129.668 81.9896 128.359 83.2986C127.049 84.6077 125.382 85.4991 123.566 85.8603C121.75 86.2214 119.868 86.0361 118.158 85.3276C116.448 84.6192 114.986 83.4195 113.957 81.8802C112.929 80.341 112.38 78.5313 112.38 76.6801C112.38 74.1977 113.366 71.8169 115.121 70.0616C116.877 68.3063 119.258 67.3201 121.74 67.3201Z" fill="#B59CFF"/>
            <path d="M79.16 67.3201C81.0112 67.3201 82.8209 67.8691 84.3601 68.8976C85.8994 69.926 87.0991 71.3879 87.8075 73.0982C88.5159 74.8085 88.7013 76.6905 88.3401 78.5062C87.979 80.3218 87.0875 81.9896 85.7785 83.2986C84.4695 84.6077 82.8017 85.4991 80.986 85.8603C79.1704 86.2214 77.2884 86.0361 75.5781 85.3276C73.8678 84.6192 72.4059 83.4195 71.3774 81.8802C70.349 80.341 69.8 78.5313 69.8 76.6801C69.8 74.1977 70.7861 71.8169 72.5415 70.0616C74.2968 68.3063 76.6776 67.3201 79.16 67.3201Z" fill="#B59CFF"/>
            <path fill-rule="evenodd" clip-rule="evenodd" d="M96.49 43.5301V49.2001H67.57C63.4845 49.2107 59.5696 50.839 56.6816 53.7288C53.7937 56.6186 52.1679 60.5346 52.16 64.6201V66.9201H46.9C44.8055 66.928 42.7992 67.7643 41.3191 69.2462C39.839 70.7282 39.0053 72.7356 39 74.8301V93.2001C39.0053 95.2963 39.8403 97.3052 41.3226 98.7875C42.8049 100.27 44.8138 101.105 46.91 101.11H52.16V103.18C52.1732 107.262 53.8013 111.173 56.6887 114.059C59.576 116.944 63.488 118.57 67.57 118.58H67.78L66.53 136.58C66.4946 137.255 66.7202 137.917 67.16 138.43C67.3799 138.69 67.6491 138.904 67.9519 139.059C68.2548 139.214 68.5854 139.308 68.9246 139.335C69.2639 139.362 69.6052 139.321 69.9287 139.216C70.2523 139.11 70.5518 138.942 70.81 138.72L94.23 118.61H133.3C137.392 118.602 141.314 116.975 144.209 114.083C147.104 111.192 148.737 107.272 148.75 103.18V101.11H154C156.095 101.102 158.101 100.266 159.581 98.784C161.061 97.302 161.895 95.2946 161.9 93.2001V74.8301C161.895 72.7356 161.061 70.7282 159.581 69.2462C158.101 67.7643 156.095 66.928 154 66.9201H148.72V64.6301C148.709 60.5428 147.082 56.6258 144.193 53.7346C141.303 50.8435 137.387 49.2133 133.3 49.2001H104.82V43.5301C105.515 43.2863 106.185 42.9748 106.82 42.6001C107.676 42.0847 108.468 41.4705 109.18 40.7701L109.24 40.7101C110.372 39.5841 111.269 38.245 111.88 36.7701C113.106 33.8018 113.106 30.4685 111.88 27.5001C110.962 25.2801 109.406 23.3824 107.408 22.0473C105.411 20.7122 103.062 19.9998 100.66 20.0001C99.0609 19.9932 97.4765 20.306 96 20.9201C94.5347 21.5334 93.2032 22.4268 92.08 23.5501C90.9534 24.6842 90.057 26.0255 89.44 27.5001C88.3297 30.2042 88.229 33.2173 89.1561 35.9895C90.0832 38.7617 91.9764 41.108 94.49 42.6001C95.1319 42.9608 95.8006 43.2717 96.49 43.5301ZM67.57 54.4001H133.29C135.997 54.408 138.591 55.4876 140.504 57.4028C142.418 59.318 143.495 61.9129 143.5 64.6201V103.17C143.492 105.879 142.413 108.475 140.499 110.392C138.584 112.308 135.989 113.39 133.28 113.4H93.28C92.9405 113.398 92.6038 113.462 92.2896 113.591C91.9755 113.72 91.6901 113.91 91.45 114.15L72.15 130.76L73.15 116.18C73.1941 115.494 72.9657 114.818 72.5144 114.3C72.0632 113.781 71.4255 113.461 70.74 113.41H67.57C64.861 113.4 62.2661 112.318 60.3515 110.402C58.4369 108.485 57.3579 105.889 57.35 103.18V64.6301C57.3579 61.9211 58.4369 59.3252 60.3515 57.4087C62.2661 55.4922 64.861 54.4107 67.57 54.4001Z" fill="#F5F5F5"/>
            <path d="M85.54 98.6801C85.3988 98.5689 85.2712 98.4413 85.16 98.3001C84.8359 97.9198 84.6523 97.4397 84.64 96.9401C84.6309 96.438 84.7932 95.9477 85.1 95.5501C85.2146 95.4056 85.3454 95.2747 85.49 95.1601C86.0401 94.7267 86.7164 94.4844 87.4166 94.4699C88.1168 94.4555 88.8025 94.6697 89.37 95.0801C91.079 96.4284 92.9756 97.5199 95 98.3201C96.7442 98.9947 98.6 99.3339 100.47 99.3201C102.364 99.2799 104.235 98.9076 106 98.2201C108.048 97.4011 109.981 96.3187 111.75 95.0001C112.33 94.6044 113.023 94.408 113.725 94.4405C114.427 94.473 115.099 94.7325 115.64 95.1801C115.776 95.3051 115.9 95.4424 116.01 95.5901C116.304 95.996 116.452 96.4894 116.43 96.9901C116.387 97.4909 116.184 97.9644 115.85 98.3401C115.723 98.4843 115.579 98.612 115.42 98.7201C113.171 100.382 110.705 101.728 108.09 102.72C105.681 103.628 103.134 104.112 100.56 104.15C97.9832 104.186 95.4214 103.752 93 102.87C90.3313 101.872 87.832 100.469 85.59 98.7101L85.54 98.6801Z" fill="#B59CFF"/>
            <path d="M33.15 165.85V165.45C33.15 164.15 33.4083 163.042 33.925 162.125C34.4417 161.192 35.125 160.483 35.975 160C36.8417 159.5 37.7833 159.25 38.8 159.25C39.9333 159.25 40.7917 159.45 41.375 159.85C41.9583 160.25 42.3833 160.667 42.65 161.1H43.1V159.6H46.2V174.2C46.2 175.05 45.95 175.725 45.45 176.225C44.95 176.742 44.2833 177 43.45 177H35.15V174.25H42.35C42.8167 174.25 43.05 174 43.05 173.5V170.275H42.6C42.4333 170.542 42.2 170.817 41.9 171.1C41.6 171.367 41.2 171.592 40.7 171.775C40.2 171.958 39.5667 172.05 38.8 172.05C37.7833 172.05 36.8417 171.808 35.975 171.325C35.125 170.825 34.4417 170.117 33.925 169.2C33.4083 168.267 33.15 167.15 33.15 165.85ZM39.7 169.3C40.6667 169.3 41.475 168.992 42.125 168.375C42.775 167.758 43.1 166.892 43.1 165.775V165.525C43.1 164.392 42.775 163.525 42.125 162.925C41.4917 162.308 40.6833 162 39.7 162C38.7333 162 37.925 162.308 37.275 162.925C36.625 163.525 36.3 164.392 36.3 165.525V165.775C36.3 166.892 36.625 167.758 37.275 168.375C37.925 168.992 38.7333 169.3 39.7 169.3ZM49.6924 172V159.6H52.7924V161H53.2424C53.4257 160.5 53.7257 160.133 54.1424 159.9C54.5757 159.667 55.0757 159.55 55.6424 159.55H57.1424V162.35H55.5924C54.7924 162.35 54.134 162.567 53.6174 163C53.1007 163.417 52.8424 164.067 52.8424 164.95V172H49.6924ZM64.815 172.35C63.5817 172.35 62.49 172.092 61.54 171.575C60.6067 171.042 59.8734 170.3 59.34 169.35C58.8234 168.383 58.565 167.25 58.565 165.95V165.65C58.565 164.35 58.8234 163.225 59.34 162.275C59.8567 161.308 60.5817 160.567 61.515 160.05C62.4484 159.517 63.5317 159.25 64.765 159.25C65.9817 159.25 67.04 159.525 67.94 160.075C68.84 160.608 69.54 161.358 70.04 162.325C70.54 163.275 70.79 164.383 70.79 165.65V166.725H61.765C61.7984 167.575 62.115 168.267 62.715 168.8C63.315 169.333 64.0484 169.6 64.915 169.6C65.7984 169.6 66.4484 169.408 66.865 169.025C67.2817 168.642 67.5984 168.217 67.815 167.75L70.39 169.1C70.1567 169.533 69.815 170.008 69.365 170.525C68.9317 171.025 68.3484 171.458 67.615 171.825C66.8817 172.175 65.9484 172.35 64.815 172.35ZM61.79 164.375H67.59C67.5234 163.658 67.2317 163.083 66.715 162.65C66.215 162.217 65.5567 162 64.74 162C63.89 162 63.215 162.217 62.715 162.65C62.215 163.083 61.9067 163.658 61.79 164.375ZM77.4438 172.35C76.5604 172.35 75.7688 172.2 75.0688 171.9C74.3688 171.583 73.8104 171.133 73.3938 170.55C72.9938 169.95 72.7938 169.225 72.7938 168.375C72.7938 167.525 72.9938 166.817 73.3938 166.25C73.8104 165.667 74.3771 165.233 75.0938 164.95C75.8271 164.65 76.6604 164.5 77.5938 164.5H80.9938V163.8C80.9938 163.217 80.8104 162.742 80.4438 162.375C80.0771 161.992 79.4938 161.8 78.6938 161.8C77.9104 161.8 77.3271 161.983 76.9438 162.35C76.5604 162.7 76.3104 163.158 76.1938 163.725L73.2938 162.75C73.4938 162.117 73.8104 161.542 74.2438 161.025C74.6938 160.492 75.2854 160.067 76.0188 159.75C76.7688 159.417 77.6771 159.25 78.7438 159.25C80.3771 159.25 81.6688 159.658 82.6188 160.475C83.5688 161.292 84.0438 162.475 84.0438 164.025V168.65C84.0438 169.15 84.2771 169.4 84.7438 169.4H85.7438V172H83.6438C83.0271 172 82.5188 171.85 82.1188 171.55C81.7188 171.25 81.5188 170.85 81.5188 170.35V170.325H81.0438C80.9771 170.525 80.8271 170.792 80.5938 171.125C80.3604 171.442 79.9938 171.725 79.4938 171.975C78.9938 172.225 78.3104 172.35 77.4438 172.35ZM77.9938 169.8C78.8771 169.8 79.5938 169.558 80.1438 169.075C80.7104 168.575 80.9938 167.917 80.9938 167.1V166.85H77.8188C77.2354 166.85 76.7771 166.975 76.4438 167.225C76.1104 167.475 75.9438 167.825 75.9438 168.275C75.9438 168.725 76.1188 169.092 76.4688 169.375C76.8188 169.658 77.3271 169.8 77.9938 169.8ZM91.8936 172C91.0769 172 90.4102 171.75 89.8936 171.25C89.3936 170.733 89.1436 170.05 89.1436 169.2V162.2H86.0436V159.6H89.1436V155.75H92.2936V159.6H95.6936V162.2H92.2936V168.65C92.2936 169.15 92.5269 169.4 92.9936 169.4H95.3936V172H91.8936ZM105.995 172.35C104.878 172.35 104.02 172.158 103.42 171.775C102.82 171.392 102.378 170.967 102.095 170.5H101.645V172H98.5449V154.5H101.695V161.025H102.145C102.328 160.725 102.57 160.442 102.87 160.175C103.187 159.908 103.595 159.692 104.095 159.525C104.612 159.342 105.245 159.25 105.995 159.25C106.995 159.25 107.92 159.5 108.77 160C109.62 160.483 110.303 161.2 110.82 162.15C111.337 163.1 111.595 164.25 111.595 165.6V166C111.595 167.35 111.337 168.5 110.82 169.45C110.303 170.4 109.62 171.125 108.77 171.625C107.92 172.108 106.995 172.35 105.995 172.35ZM105.045 169.6C106.012 169.6 106.82 169.292 107.47 168.675C108.12 168.042 108.445 167.125 108.445 165.925V165.675C108.445 164.475 108.12 163.567 107.47 162.95C106.837 162.317 106.028 162 105.045 162C104.078 162 103.27 162.317 102.62 162.95C101.97 163.567 101.645 164.475 101.645 165.675V165.925C101.645 167.125 101.97 168.042 102.62 168.675C103.27 169.292 104.078 169.6 105.045 169.6ZM120.387 172.35C119.154 172.35 118.046 172.1 117.062 171.6C116.079 171.1 115.304 170.375 114.737 169.425C114.171 168.475 113.887 167.333 113.887 166V165.6C113.887 164.267 114.171 163.125 114.737 162.175C115.304 161.225 116.079 160.5 117.062 160C118.046 159.5 119.154 159.25 120.387 159.25C121.621 159.25 122.729 159.5 123.712 160C124.696 160.5 125.471 161.225 126.037 162.175C126.604 163.125 126.887 164.267 126.887 165.6V166C126.887 167.333 126.604 168.475 126.037 169.425C125.471 170.375 124.696 171.1 123.712 171.6C122.729 172.1 121.621 172.35 120.387 172.35ZM120.387 169.55C121.354 169.55 122.154 169.242 122.787 168.625C123.421 167.992 123.737 167.092 123.737 165.925V165.675C123.737 164.508 123.421 163.617 122.787 163C122.171 162.367 121.371 162.05 120.387 162.05C119.421 162.05 118.621 162.367 117.987 163C117.354 163.617 117.037 164.508 117.037 165.675V165.925C117.037 167.092 117.354 167.992 117.987 168.625C118.621 169.242 119.421 169.55 120.387 169.55ZM134.13 172C133.313 172 132.647 171.75 132.13 171.25C131.63 170.733 131.38 170.05 131.38 169.2V162.2H128.28V159.6H131.38V155.75H134.53V159.6H137.93V162.2H134.53V168.65C134.53 169.15 134.763 169.4 135.23 169.4H137.63V172H134.13ZM142.756 172.35C142.09 172.35 141.523 172.133 141.056 171.7C140.606 171.25 140.381 170.675 140.381 169.975C140.381 169.275 140.606 168.708 141.056 168.275C141.523 167.825 142.09 167.6 142.756 167.6C143.44 167.6 144.006 167.825 144.456 168.275C144.906 168.708 145.131 169.275 145.131 169.975C145.131 170.675 144.906 171.25 144.456 171.7C144.006 172.133 143.44 172.35 142.756 172.35ZM152.078 172.35C151.194 172.35 150.403 172.2 149.703 171.9C149.003 171.583 148.444 171.133 148.028 170.55C147.628 169.95 147.428 169.225 147.428 168.375C147.428 167.525 147.628 166.817 148.028 166.25C148.444 165.667 149.011 165.233 149.728 164.95C150.461 164.65 151.294 164.5 152.228 164.5H155.628V163.8C155.628 163.217 155.444 162.742 155.078 162.375C154.711 161.992 154.128 161.8 153.328 161.8C152.544 161.8 151.961 161.983 151.578 162.35C151.194 162.7 150.944 163.158 150.828 163.725L147.928 162.75C148.128 162.117 148.444 161.542 148.878 161.025C149.328 160.492 149.919 160.067 150.653 159.75C151.403 159.417 152.311 159.25 153.378 159.25C155.011 159.25 156.303 159.658 157.253 160.475C158.203 161.292 158.678 162.475 158.678 164.025V168.65C158.678 169.15 158.911 169.4 159.378 169.4H160.378V172H158.278C157.661 172 157.153 171.85 156.753 171.55C156.353 171.25 156.153 170.85 156.153 170.35V170.325H155.678C155.611 170.525 155.461 170.792 155.228 171.125C154.994 171.442 154.628 171.725 154.128 171.975C153.628 172.225 152.944 172.35 152.078 172.35ZM152.628 169.8C153.511 169.8 154.228 169.558 154.778 169.075C155.344 168.575 155.628 167.917 155.628 167.1V166.85H152.453C151.869 166.85 151.411 166.975 151.078 167.225C150.744 167.475 150.578 167.825 150.578 168.275C150.578 168.725 150.753 169.092 151.103 169.375C151.453 169.658 151.961 169.8 152.628 169.8ZM162.681 172V159.6H165.831V172H162.681ZM164.256 158.15C163.689 158.15 163.206 157.967 162.806 157.6C162.422 157.233 162.231 156.75 162.231 156.15C162.231 155.55 162.422 155.067 162.806 154.7C163.206 154.333 163.689 154.15 164.256 154.15C164.839 154.15 165.322 154.333 165.706 154.7C166.089 155.067 166.281 155.55 166.281 156.15C166.281 156.75 166.089 157.233 165.706 157.6C165.322 157.967 164.839 158.15 164.256 158.15Z" fill="#F5F5F5"/>
            </svg></div>
        <div id="chatbot-window">
            <div class="chat-header">
                <button class="back-button" onclick="toggleChat()">X</button>
                Chat Assistant
            </div>
            <div class="chat-messages" id="chatMessages">
                <div class="message received">
                    <div class="text">
                        <h4>Hey, Herzlich willkommen!</h4> Wobei kann ich Ihnen helfen?
                        <div id="categorySelection" style="display: none;">
                            <div id="categories" style="display: flex; flex-direction: column;"></div>
                        </div>
                        <p style="font-size: 7;">*Hinweis: Bei Verwendung des Chatbots akzeptieren Sie <a href="https://greatbot.eu.pythonanywhere.com/datenschutzerklaerung/">Datenschutzbestimmungen</a> und <a href="https://greatbot.eu.pythonanywhere.com/agb/">AGB.</a></p>
                    </div>
                </div>
            </div>
            <div class="chat-input">
                <input type="text" id="messageInput" placeholder="Fragen Sie etwas...">
                <button onclick="sendMessage()">Senden</button>
            </div>
        </div>
    </div>
    <script type="text/javascript" src="https://greatbot.eu.pythonanywhere.com{js_url}"></script>
</div> 
""",
            css_code=f"""
    :root {{
    --primary-color-dark: #060606;
    --primary-color-bright: whitesmoke;
    --secondary-color: #14ca74;
    --header-color: #15221a;
}}

/* Link Styling */
a {{
    color: var(--primary-color-dark);
}}

/* Default: Base Styles for Desktop (Webflow default 992px+) */

#chatbot {{
    position: fixed;
    bottom: 3rem;
    right: 3rem;
    z-index: 9999;
}}

#chatbot-container {{
    font-family: Urbanist, sans-serif;
    background-color: var(--primary-color-dark);
    margin: 0rem;
    padding: 0rem;
}}

#chatbot-button {{
    background-color: var(--primary-color-dark);
    border: solid 0.1rem var(--secondary-color);
    color: var(--primary-color-bright);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0.75rem;
    width: 4.5rem;
    height: 4.5rem;
    border-radius: 100vw;
    cursor: pointer;
}}

#chatbot-window {{
    display: none;
    width: 25rem;
    height: 72.5vh;
    background-color: transparent;
    border-radius: 1.25rem;
    border: solid 0.1rem var(--secondary-color);
    position: absolute;
    bottom: 6.75rem;
    right: 3rem;
    overflow: hidden;
    flex-direction: column;
    justify-content: space-between;
    transform: scale(0);
    transform-origin: bottom right;
    transition: transform 0.33s ease-out;
}}

#chatbot-window.open {{
    transform: scale(1);
}}

#chatbot-container .chat-header {{
    display: flex;
    justify-content: center;
    align-items: center;
    background-color: var(--header-color);
    color: var(--primary-color-bright);
    padding: 0.5rem 1rem;
    text-align: center;
    position: relative;
    min-height: 10%;
}}

#chatbot-container .chat-header .back-button {{
    display: flex;
    align-items: center;
    justify-items: center;
    position: absolute;
    left: 1rem;
    background-color: var(--primary-color-bright);
    color: var(--primary-color-dark);
    border: none;
    border-radius: 100vw;
    height: 1.75rem;
    width: 1.75rem;
    cursor: pointer;
}}

#chatbot-container .chat-messages {{
    display: flex;
    flex-direction: column;
    row-gap: 1rem;
    padding: 1rem;
    height: 100%;
    width: 100%;
    overflow-y: auto;
    background-color: var(--primary-color-dark);
}}

#chatbot-container .chat-input {{
    display: flex;
    padding: 1rem;
    background-color: var(--primary-color-bright);
}}

#chatbot-container .chat-input input {{
    flex: 1;
    padding: 0.75rem 1rem;
    border: solid 0.1rem var(--secondary-color);
    color: var(--primary-color-dark);
    border-radius: 1.25rem;
    background-color: var(--primary-color-bright);
    margin-right: 1rem;
    outline: none;
}}

#chatbot-container .chat-input button {{
    background-color: var(--primary-color-dark);
    border: solid 0.1rem var(--secondary-color);
    color: var(--primary-color-bright);
    padding: 0.75rem 1rem;
    border-radius: 1rem;
    cursor: pointer;
    outline: none;
}}

#chatbot-container .message.sent .text {{
    background-color: var(--primary-color-dark);
    color: var(--primary-color-bright);
    border: solid 0.1rem var(--secondary-color);
    border-radius: 1rem 1rem 0rem 1rem;
    margin-left: auto;
}}

#chatbot-container .message.received .text {{
    background-color: var(--primary-color-bright);
    color: var(--primary-color-dark);
    border: 0.1em solid var(--secondary-color);
    border-radius: 1rem 1rem 1rem 0rem;
}}

#chatbot-container .message .text {{
    max-width: 75%;
    padding: 1rem 1rem;
    line-height: 1.25;
    font-size: 0.75rem;
}}

/* Webflow Tablet (991px and below) */
@media (max-width: 991px) {{

    #chatbot {{
        position: fixed;
        bottom: 1.5rem;
        right: 2rem;
        z-index: 9999;
    }}

    #chatbot-window {{
        width: 40vw;
        height: 33rem;  
        bottom: 5.75rem;
        right: 2rem;
    }}

    #chatbot-button {{
        width: 3.5rem;
        height: 3.5rem;
    }}

    #chatbot-container .chat-header {{
        padding: 0.5rem 1rem;
    }}

    #chatbot-container .chat-header .back-button {{
        left: 1rem;
        height: 1.75rem;
        width: 1.75rem;
    }}

    #chatbot-container .chat-input {{
        padding: 1em;
    }}

    #chatbot-container .chat-messages {{
        padding: 0.75rem;
    }}
}}

/* Webflow Mobile Landscape (767px and below) */
@media (max-width: 767px) {{
    #chatbot-button {{
        display: none;
    }}
}}

/* Webflow Mobile Portrait (479px and below) */
@media (max-width: 479px) {{

    #chatbot {{
        position: fixed;
        bottom: 2.5vw;
        right: 3.5vw;
        z-index: 9999;
    }}

    #chatbot-window {{
        width: 95svw;
        height: 97.5svh;
        bottom: 0rem;
        right: 0rem;
    }}

    #chatbot-button {{
        display: flex;
        width: 3.25rem;
        height: 3.25rem;
        padding: 0.5rem;
    }}

    #chatbot-container .chat-header {{
        padding: 0.5rem 0.75rem;
    }}

    #chatbot-container .chat-header .back-button {{
        left: 0.5rem;
        padding: 0.25rem;
        height: 1.5rem;
        width: 1.5rem;
    }}

    #chatbot-container .chat-input {{
        padding: 0.5rem;
    }}

    #chatbot-container .chat-messages {{
        padding: 0.5rem;
    }}
    }}
    """,
            js_code="""
var id_count = 0;
var uid = "";
var api_registration_token = "";
var chatbotResponses = 0;
var company_name = document.querySelector('meta[name="company-name-greatbot-ai"]').getAttribute('content');
var selectedCategory = "";
var categories = []; 

function showCategorySelection(categoryList) {
  const categorySelection = document.getElementById("categorySelection");
  const categoriesContainer = document.getElementById("categories");

  categoriesContainer.innerHTML = "";

  categoryList.forEach(category => {
    const categoryDiv = document.createElement("div");
    categoryDiv.className = "category-item";
    categoryDiv.innerText = category;
    categoryDiv.onclick = function () {
      selectCategory(category);
    };
    categoriesContainer.appendChild(categoryDiv);
  });

  if (categoryList.length > 1) {
    categorySelection.style.display = "block";
  }
}

function selectCategory(category) {
  selectedCategory = category;
  console.log("Selected category:", selectedCategory);
  document.getElementById("categorySelection").style.display = "none";
}


function sendPersonalData() {
  var name = document.getElementById("chatbot_user_name").value;
  var email = document.getElementById("chatbot_user_email").value;

  if (name.trim() !== "" && email.trim() !== "") {
    // Prepare and send the request
    let formedData = new FormData();
    formedData.append("name", name);
    formedData.append("email", email);
    formedData.append("uid", uid);
    formedData.append("api_registration_token", api_registration_token);

    fetch("https://greatbot.eu.pythonanywhere.com/api/" + company_name + "/assistant-chat/saveuserdata/", {
      method: "POST",
      body: formedData
    })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          // Show thank you message
          const chatMessages = document.getElementById("chatMessages");
          const thankYouMessageElement = document.createElement("div");
          thankYouMessageElement.classList.add("message", "received");
          thankYouMessageElement.innerHTML = '<div class="text">Vielen Dank ! Es wird sich zeitnah jemand bei Ihnen melden. Wenn ich Ihnen sonst noch behilflich sein kann, fragen Sie gerne weiter.</div>';
          chatMessages.appendChild(thankYouMessageElement);
          chatMessages.scrollTop = chatMessages.scrollHeight;
        }
      })
      .catch(error => {
        console.error("Error:", error);
      });
  }
}

function toggleChat() {
  const chatWindow = document.getElementById("chatbot-window");
  const chatbutton = document.getElementById("chatbot");
  fetch("https://greatbot.eu.pythonanywhere.com/api/" + company_name + "/assistant-chat/getapiregistrationtoken", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",  // JSON als Content-Type
      // "X-CSRFToken": token, // Falls du CSRF-Token benötigst
    },
    body: JSON.stringify({})  // Leerer Body, wenn nichts übergeben wird
  })
    .then(response => {
      if (!response.ok) {
        throw new Error("API Request failed");
      }
      return response.json();  // Die Antwort in JSON umwandeln
    })
    .then(data => {
      uid = data.uid;
      api_registration_token = data.api_registration_token;
      categories = data.categorys;
      if (categories.length > 1) {
        showCategorySelection(categories);
        console.log("select a category choice");
      }else{
        selectedCategory = "general_info";
      }
    })
    .catch(error => {
      console.error("Error fetching the API data:", error);
    });
  if (chatWindow.classList.contains("open")) {
    chatWindow.classList.remove("open");
    chatbutton.classList.remove("open");
    setTimeout(() => chatWindow.style.display = "none", 300);
  } else {
    chatWindow.style.display = "flex";
    setTimeout(() => chatWindow.classList.add("open"), 10);
    setTimeout(() => chatbutton.classList.add("open"), 10);
  }
}

function sendMessage() {
  var messageInput = document.getElementById("messageInput");
  var message = messageInput.value;
  if (message.trim() !== "") {
    if (selectedCategory === ""){
      alert("Bitte wählen Sie eine Kategorie aus, zu der Sie Ihre Frage stellen möchten.");
    }
    const chatMessages = document.getElementById("chatMessages");
    const messageId = id_count;

    const userMessageElement = createMessageElement(message, "sent");
    chatMessages.appendChild(userMessageElement);

    const assistantMessageElement = createMessageElement("...", "received", "loading_message" + messageId);
    chatMessages.appendChild(assistantMessageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    messageInput.value = "";


    let formedData = new FormData();
    formedData.append("message", message);
    formedData.append("chatbotResponses", chatbotResponses);
    formedData.append("uid", uid);
    formedData.append("api_registration_token", api_registration_token);
    formedData.append("selectedCategory", selectedCategory);

    fetch("https://greatbot.eu.pythonanywhere.com/api/" + company_name + "/assistant-chat/sendmessage/", {
      method: "POST",
      body: formedData
    })
      .then(response => response.json())
      .then(data => {
        if (data.answer_chat_assistant) {
          const loadingMessageElement = document.getElementById("loading_message" + messageId);
          if (loadingMessageElement) {
            loadingMessageElement.innerHTML = createMessageElement(data.answer_chat_assistant, "received").innerHTML;
            loadingMessageElement.removeAttribute("id");
            chatMessages.scrollTop = chatMessages.scrollHeight;
          }
        }
        id_count++;
        chatbotResponses++;
        if (chatbotResponses == 2) {
          addContactForm();
        }
      })
      .catch(error => {
        console.error("Error:", error);
        const loadingMessageElement = document.getElementById("loading_message" + messageId);
        if (loadingMessageElement) {
          loadingMessageElement.innerHTML = "Fehler bei der Verarbeitung der Anfrage";
          loadingMessageElement.removeAttribute("id");
        }
      });
  }
}

function createMessageElement(text, type, id = null) {
  var messageElement = document.createElement("div");
  if (id) {
    messageElement.id = id;
  }
  messageElement.classList.add("message", type);

  var textElement = document.createElement("div");
  textElement.classList.add("text");
  textElement.innerHTML = text;

  messageElement.appendChild(textElement);
  return messageElement;
}
function addContactForm() {
  const chatMessages = document.getElementById("chatMessages");
  const contactFormElement = document.createElement("div");
  contactFormElement.classList.add("message", "received");
  contactFormElement.innerHTML = `
                <div class="text form-container">
                    Wenn Sie möchten, kontaktieren wir Sie gerne persönlich und geben Ihnen weitere Informationen:
                    <form style="margin-top: 15px;">
                        <label for="chatbot_user_name">Vor und Nachname</label>
                         <div class="chat-input">
                        <input type="text" id="chatbot_user_name" name="chatbot_user_name" required>
                        </div>
                        <label for="chatbot_user_email">Email-adresse</label>
                         <div class="chat-input">
                        <input type="email" id="chatbot_user_email" name="chatbot_user_email" required>
                        </div>
                    </form>
                    <div class="chat-input">
                        <button type="button" onclick="sendPersonalData()">Bestätigen</button>
                    </div>
                </div>
            `;
  chatMessages.appendChild(contactFormElement);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}
""",
        )

        if "diverse_category" in request.POST:
            category_names = request.POST.getlist("category_names")
            category_files = request.FILES.getlist("category_files")

            if len(category_names) != len(category_files):
                return HttpResponse("Jede Kategorie muss eine Datei haben.")

            for category_name, category_file in zip(category_names, category_files):
                if not category_file.name.endswith((".txt", ".pdf")):
                    return HttpResponse(
                        f"Die Datei {category_file.name} muss eine .txt-Datei oder .pdf-Datei sein."
                    )

                # Speichern der Datei
                upload_dir = os.path.join("uploaded_files", company_name, category_name)
                os.makedirs(upload_dir, exist_ok=True)

                file_path = os.path.join(upload_dir, category_file.name)
                with open(file_path, "wb+") as destination:
                    for chunk in category_file.chunks():
                        destination.write(chunk)
                customer.file_paths.add(
                    models.Path.objects.create(training_file_path=file_path)
                )
                openAi.create_assistant(
                    company_name, customer, file_path, category_name
                )

        # Einzelne Unternehmensinformationen (falls keine Kategorien ausgewählt sind)
        else:
            uploaded_file = request.FILES.get("file_upload")
            if uploaded_file:
                if not uploaded_file.name.endswith((".txt", ".pdf")):
                    return HttpResponse(
                        f"Die Datei {category_file.name} muss eine .txt-Datei oder .pdf-Datei sein."
                    )

                upload_dir = os.path.join("uploaded_files", company_name)
                os.makedirs(upload_dir, exist_ok=True)

                # Speichern der Datei
                file_path = os.path.join(upload_dir, uploaded_file.name)
                with open(file_path, "wb+") as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)
                customer.file_paths.add(
                    models.Path.objects.create(training_file_path=file_path)
                )
                openAi.create_assistant(
                    company_name, customer, file_path, "general_info"
                )

        customer.save()

        # openAi.prepare_company_file(company_name)
        # openAi.create_fine_tuning_model(company_name, customer)
        # openAi.prepare_company_file(company_name)

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


def datenschutzerklaerung(request):
    return render(request, "chat_bot_app/privacy_policy.html")


def agb(request):
    return render(request, "chat_bot_app/agb.html")


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
