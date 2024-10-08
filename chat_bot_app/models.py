from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Request(models.Model):
    created_at = models.DateTimeField(default=timezone.now())
    created_for = models.IntegerField(default=0)

class Lead(models.Model):
    created_at = models.DateTimeField(default=timezone.now())
    created_for = models.IntegerField(default=0)

class ChatMessage(models.Model):
    message = models.CharField(default= "", max_length= 12000)
    bot_message = models.BooleanField(default=True)

class ChatbotUser(models.Model):
    created_at = models.DateTimeField(default=timezone.now())
    created_for = models.IntegerField(default=0)
    name = models.CharField(default = "", max_length=300)
    email = models.CharField(default = "", max_length=300)
    uid = models.CharField(default = "", max_length=300)
    messages = models.ManyToManyField(ChatMessage)
    lead_processed = models.BooleanField(default=False)

class RegistrationToken(models.Model):
    api_registration_token = models.CharField(default="", max_length=200)
    created_at = models.DateTimeField(default=timezone.now())
    created_for = models.IntegerField(default=0)

class Path(models.Model):
    training_file_path = models.CharField(default="", max_length=300)

class Customer(models.Model):
    company_name = models.CharField(default="", max_length=300)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    lead_email = models.CharField(default="", max_length=300)
    color_code = models.CharField(default="", max_length=300)  # Hauptfarbe
    accent_color = models.CharField(default="", max_length=300)  # Akzentfarbe
    website_url = models.CharField(default="", max_length=300)
    logo_url = models.CharField(default="", max_length=300)
    subscription_model = models.CharField(default="", max_length=300)
    chatbot_url = models.CharField(default="", max_length=300)
    js_url = models.CharField(default="", max_length=300)
    css_url = models.CharField(default="", max_length=300)
    save_user_data_url = models.CharField(default="", max_length=300)
    send_message_url = models.CharField(default="", max_length=300)
    file_paths = models.ManyToManyField(Path)
    code = models.TextField(default="")
    css_code = models.TextField(default="")
    api_registration_tokens = models.ManyToManyField(RegistrationToken)
    js_code = models.TextField(default="")

class SummariserAssistant(models.Model):
    assistant_id = models.CharField(default = "", max_length=300)

class ChatAssistant(models.Model):
    created_for = models.ForeignKey(Customer, on_delete=models.CASCADE)
    partner_name = models.CharField(default = "", max_length=300)
    category_name = models.CharField(default = "", max_length=300)
    assistant_id = models.CharField(default = "", max_length=300)
    vector_store_id = models.CharField(default = "", max_length=300)

class ChatFineTuneModel(models.Model):
    created_for = models.ForeignKey(Customer, on_delete=models.CASCADE)
    partner_name = models.CharField(default = "", max_length=300)
    fine_tuned_model_id = models.CharField(default = "", max_length=300)

class Themengebiet(models.Model):
    created_for = models.ForeignKey(Customer, on_delete=models.CASCADE)
    themenbereich = models.CharField(max_length=1155)
    amount = models.PositiveIntegerField(default=1)

class FAQ(models.Model):
    created_for = models.ForeignKey(Customer, on_delete=models.CASCADE)
    question = models.CharField(default="", max_length= 8000)
    answer = models.CharField(default="", max_length=8000)