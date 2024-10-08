import openai
from django.http import JsonResponse, StreamingHttpResponse, HttpResponse
from chat_bot import settings
from openai import OpenAI, AssistantEventHandler, AzureOpenAI
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from . import models, crawl_url
import re
from typing_extensions import override
from uuid import uuid4
import os
import time
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import (
    api_view,
)
# client = OpenAI(api_key=settings.OPENAI_API_KEY)
from django.shortcuts import get_object_or_404
import random
client_azure = AzureOpenAI(
    api_key=settings.AZURE_API_KEY,
    azure_endpoint=settings.AZURE_END_POINT,
    api_version="2024-05-01-preview",
)
client = client_azure


def prepare_company_file(company_name):
    assistant_model, created = models.SummariserAssistant.objects.get_or_create(id=1)

    if assistant_model.assistant_id == "" or assistant_model.assistant_id == None:
        assistant = client_azure.beta.assistants.create(
            name="Text Assistant",
            instructions=(
                "You are a professional writer tasked with creating a comprehensive and detailed text about a company based on the provided files. Your goal is to extract and include all relevant information, ensuring that the text answers any conceivable questions about the company. Your text should cover: Products and Services: Describe the company's products and services, including their key features and benefits Contact Information: Provide all relevant contact details, such as address, phone number, email address, and website Advantages: Highlight the unique benefits and competitive advantages of the company Team: Include information about the team, focusing on key members and their roles Pricing: If available, include information on pricing or pricing models Testimonials: Share any customer or client testimonials that reflect the company’s reputation and client satisfaction Achievements: Detail notable achievements, awards, or recognitions that the company has received History: Outline the company’s founding history, including its origin, milestones, and growth over time Locations: List the company's locations, including headquarters and any additional offices or branches Your text should be at least 600 words long and provide a thorough overview of the company, ensuring that all important aspects are covered. "
            ),
            model="gpt-4o",
            tools=[{"type": "file_search"}],
        )
        print(assistant)
        assistant_model.assistant_id = assistant.id
        assistant_model.save()
    assistant_model.assistant_id = assistant.id
    assistant_model.save()
    file_paths = [
        f"customer_files/{company_name}.txt",
        "customer_files/chat_bot_creator_laxout.txt",
    ]
    file_streams = []
    for path in file_paths:
        if os.path.getsize(path) == 0:
            print(f"The file {path} is empty or not valid.")
            continue
        with open(path, "rb") as file:
            content = file.read()
            if not content:
                raise ValueError(f"The file {path} is empty or not valid.")
            file_ext = path.split(".")[-1]
            file_streams.append(open(path, "rb"))
    message_files = [
        client.files.create(file=open(path, "rb"), purpose="assistants")
        for path in file_paths
        if os.path.getsize(path) > 0
    ]
    attachments = [
        {"file_id": message_file.id, "tools": [{"type": "file_search"}]}
        for message_file in message_files
    ]
    thread = client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": "Summarise the information of this company. Return at least 300 words. Cover all important information!",
                "attachments": attachments,
            }
        ]
    )
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id, assistant_id=assistant_model.assistant_id
    )
    messages = list(
        client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id)
    )
    message_content = messages[0].content[0].text
    new_text_content = message_content.value
    crawl_url.save_text_to_file(new_text_content, f"customer_files/{company_name}.txt")
    return HttpResponse("OK")



def create_assistant(company_name, customer_object, file_path, category_name):

    assistant = client_azure.beta.assistants.create(
        name="Business Assistant",
        instructions=(
            f"You are a helpful chat assistant for {company_name} and you answer questions of their customers and help them. Don't mention your sources or any uploaded file ! If you don't know the answer due to lack of information just say: I'm sry but I cant respond to that question and refer to contact info."
            f"Answer in the same language as the chat partner and be very polite and nice."
        ),
        model="gpt-4o-mini",
        tools=[{"type": "file_search"}],
    )

    vector_store = client_azure.beta.vector_stores.create(name=company_name)

    print("Ausgeführt")
    print(assistant)

    file_streams = []
    
    print(file_path)
    with open(file_path, "rb") as file:
        content = file.read()
        if not content:
            raise ValueError(f"The file {file_path} is empty or not valid.")
        file_ext = file_path.split(".")[-1]
        file_streams.append(open(file_path, "rb"))

    if not file_streams:
        raise ValueError("No valid files to process.")

    file_batch = client_azure.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id, files=file_streams
    )

    assistant = client_azure.beta.assistants.update(
        assistant_id=assistant.id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
    )

    print(f"Assistant ID: {assistant.id}")
    chat_assistant= models.ChatAssistant.objects.create(created_for=customer_object)
    chat_assistant.vector_store_id = vector_store.id
    chat_assistant.assistant_id = assistant.id
    chat_assistant.partner_name = customer_object.company_name
    chat_assistant.category_name = category_name
    chat_assistant.save()
    
    customer_object.chatbot_url = f"/api/{company_name}/assistant-chat/"
    customer_object.save()
    return HttpResponse("OK")

def generate_code():
    return ''.join([str(random.randint(0, 9)) for _ in range(14)])

@csrf_exempt
@api_view(["POST"])
def get_api_registration_token(request, partner = None):
    customer = models.Customer.objects.get(company_name = partner)
    categorys= [category.category_name for category in models.ChatAssistant.objects.filter(created_for = customer)]
    uid = str(uuid4())
    while models.ChatbotUser.objects.filter(uid=uid).exists():
        uid = str(uuid4())
    chat = models.ChatbotUser.objects.create(uid=uid, created_for=customer.id)
    api_registration_token = generate_code()
    while models.RegistrationToken.objects.filter(api_registration_token=api_registration_token).exists():
        api_registration_token = generate_code()
    api_registration_token_object = models.RegistrationToken.objects.create(api_registration_token = api_registration_token, created_for = chat.id)
    customer.api_registration_tokens.add(api_registration_token_object)
    customer.save()
    print("New Chatbot User")
    return JsonResponse({"api_registration_token":api_registration_token, "uid":uid, "categorys": categorys})


@csrf_exempt
@api_view(["POST"])
def save_user_data(request, partner=None):
    customer = models.Customer.objects.get(company_name=partner)
    if request.method == "POST":
        api_registration_token = request.POST.get("api_registration_token")
        if not api_registration_token or api_registration_token == "":
            return JsonResponse({"error": "Permission Error"}, status=403)
        get_object_or_404(models.RegistrationToken, api_registration_token=api_registration_token)
        uid = request.POST.get("uid")
        # Generiere eine neue UID, falls keine vorhanden ist
        if not uid or uid == "":
            return JsonResponse({"error": "Permission Error"}, status=403)

        chat = models.ChatbotUser.objects.get(uid=uid, created_for=customer.id)
        name = request.POST.get("name")
        email = request.POST.get("email")

        try:
            chat.name = name
            chat.email = email
            chat.save()
            return JsonResponse({"success": True, "uid": uid})
        except models.ChatbotUser.DoesNotExist:
            return JsonResponse({"error": "Chat session not found"}, status=404)
    return JsonResponse({"error": "Invalid request method"}, status=405)


def upload_file_to_azure(file_path, max_wait_time=300):
    # Lade die Datei hoch
    response = client_azure.files.create(
        file=open(file_path, "rb"), purpose="fine-tune"
    )
    file_id = response.id
    return file_id


def create_fine_tuning_model(company_name, customer_object):
    # Hole den Dateipfad des hochgeladenen Trainingsdaten-Files
    training_file_path = customer_object.training_file_path

    # Beispielhafter Aufruf, um das File bei Azure hochzuladen
    uploaded_training_file_id = upload_file_to_azure(training_file_path)

    # Überprüfe den Status des hochgeladenen Files
    while True:
        file_status = client_azure.files.retrieve(uploaded_training_file_id)
        if file_status.status == "processed":
            # Erstelle den Fine-Tuning-Job
            response = client_azure.fine_tuning.jobs.create(
                training_file=uploaded_training_file_id,
                model="gpt-4o-mini",
            )
            job_id = response.id

            # Überwache den Status des Fine-Tuning-Jobs
            while True:
                job_status = client_azure.fine_tuning.jobs.retrieve(job_id)
                if job_status.status == "succeeded":
                    fine_tuned_model_id = job_status.fine_tuned_model
                    print(
                        f"Fine-tuning erfolgreich abgeschlossen. Modell-ID: {fine_tuned_model_id}"
                    )
                    models.ChatFineTuneModel.objects.create(
                        created_for=customer_object,
                        partner_name=company_name,
                        fine_tuned_model_id=fine_tuned_model_id,
                    )
                    break
                elif job_status.status == "failed":
                    print("Fine-tuning ist fehlgeschlagen.")
                    break
                elif job_status.status == "cancelled":
                    print("Fine-tuning wurde abgebrochen.")
                    break
                else:
                    print(
                        f"Der Jobstatus ist: {job_status.status}. Warte auf Abschluss..."
                    )
                time.sleep(450)  # Warten, bevor der Status erneut überprüft wird
            break
        elif file_status.status == "error":
            print("Fehler beim Hochladen der Datei.")
            break
        else:
            print(f"Dateistatus: {file_status.status}. Warte auf Abschluss...")

        time.sleep(30)  # Warten, bevor der Status erneut überprüft wird

    # URLs für den Kunden aktualisieren
    customer_object.chatbot_url = f"/api/{company_name}/assistant-chat/"
    customer_object.css_url = f"/api/{company_name}/dynamic-css/"
    customer_object.js_url = f"/api/{company_name}/dynamic-js/"
    customer_object.save_user_data_url = f"/api/{company_name}/saveuserdata/"
    customer_object.send_message_url = f"/api/{company_name}/sendmessage/"
    customer_object.save()

    return HttpResponse("OK")


def format_message(message):
    message = message.replace(
        "**",
        "*",
    )
    message = re.sub(r"【\d+:\d+†source】", "", message)
    message = re.sub(r"\s+", " ", message).strip()
    return message

@csrf_exempt
@api_view(["POST"])
def chatApplication(request, partner=None):
    customer = models.Customer.objects.get(company_name=partner)
    if request.method == "POST":
        api_registration_token = request.POST.get("api_registration_token")
        if not api_registration_token or api_registration_token == "":
            return JsonResponse({"error": "Permission Error"}, status=403)
        get_object_or_404(models.RegistrationToken, api_registration_token=api_registration_token)
        uid = request.POST.get("uid")
        if uid is None or uid == "":
            return JsonResponse({"error": "Permission Error"}, status=403)
        chat = models.ChatbotUser.objects.get(uid=uid, created_for=customer.id)
        try:
            selectedCategory = request.POST.get("selectedCategory")
            if selectedCategory != "general_info":
                assistant_instance =  models.ChatAssistant.objects.get(partner_name=partner, category_name = selectedCategory)
            else:
                assistant_instance = models.ChatAssistant.objects.get(partner_name=partner)
            # finetune_instance = models.ChatFineTuneModel.objects.get(partner_name = partner)
            models.Request.objects.create(created_for=customer.id)
            question = request.POST.get("message")

            themenbereich, created = models.Themengebiet.objects.get_or_create(
                created_for=customer, themenbereich=question
            )
            if not created:
                themenbereich.amount += 1
                themenbereich.save()

            message_object = models.ChatMessage.objects.create(
                message=question,
                bot_message=False,
            )
            chat.messages.add(message_object)

            # # Hier erzeugst du eine neue Thread-ID für jeden neuen Chat
            try:
                thread = client_azure.beta.threads.create(
                    messages=[
                        {
                            "role": "user",
                            "content": question,
                        }
                    ]
                )
                run = client_azure.beta.threads.runs.create_and_poll(
                    thread_id=thread.id, assistant_id=assistant_instance.assistant_id
                )

                messages = list(
                    client_azure.beta.threads.messages.list(
                        thread_id=thread.id, run_id=run.id
                    )
                )
            except Exception as e:
                print(e)

            message_content = messages[0].content[0].text
            # try:
            #     print("Vor API-Aufruf")
            #     print(finetune_instance.fine_tuned_model_id)
            #     completion = client_azure.chat.completions.create(
            #         model="gpt-4o-mini-2024-07-18-ft-ed863f5199e8459e8b1df8a56bd7eb4c",
            #         max_tokens = 500,
            #         messages=[
            #             {
            #                 "role": "system",
            #                 "content": f"Du bist ein hilfreicher Assistent, der Fragen zu {partner} beantwortet. Du darfst nur Informationen verwenden, die während des Trainings gegeben wurden. Nutze keine allgemeinen Informationen aus dem Internet oder anderen Quellen.",
            #             },
            #             {
            #                 "role": "user",
            #                 "content": question,
            #             },
            #         ],
            #     )
            #     print("API-Aufruf erfolgreich")
            # except Exception as e:
            #     print(f"API-Fehler: {e}")
            #     return JsonResponse({"error": f"API-Fehler: {e}"}, status=500)

            # message_content = completion.choices[0].message.content

            message_object = models.ChatMessage.objects.create(
                message=format_message(message_content.value),
                bot_message=True,
            )
            chat.messages.add(message_object)
            chat.save()

            return JsonResponse(
                {
                    "answer_chat_assistant": format_message(message_content.value)
                }
            )

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return render(
        request,
        "chat_bot_app/chat_ui_new.html",
        {"customer": customer, "partner_name": partner},
    )


def generate_interest_email(question_string, name, language):
    response = client_azure.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": f"You are an excellent salesperson and you summarize the interests of a potential customer based on questions or things asked in a chat with a ChatBot.  Write the mail in {language} language. ",
            },
            {
                "role": "user",
                "content": f"Questions, asked by customer: {question_string}",
            },
        ],
        stream=False,
    )

    return response.choices[0].message.content

def save_custom_embedding_code():
    pass

def delete_vector_store(vector_store_id):
    try:
        client_azure.beta.vector_stores.delete(vector_store_id=vector_store_id)
        print(f"Vector store {vector_store_id} deleted successfully.")
    except Exception as e:
        print(f"Error while deleting vector store: {str(e)}")

def delete_assistant(assistant_id):
    try:
        client_azure.beta.assistants.delete(assistant_id=assistant_id)
        print(f"Assistant {assistant_id} deleted successfully.")
    except Exception as e:
        print(f"Error while deleting assistant: {str(e)}")

def delete_uploaded_files(customer):
    for path in customer.file_paths.all():
        file_path = path.training_file_path
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"File {file_path} deleted successfully.")
            else:
                print(f"File {file_path} does not exist.")
        except Exception as e:
            print(f"Error while deleting file {file_path}: {str(e)}")
    customer.file_paths.all().delete()
