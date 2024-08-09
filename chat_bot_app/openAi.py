import openai
from django.http import JsonResponse, StreamingHttpResponse, HttpResponse
from chat_bot import settings
from openai import OpenAI, AssistantEventHandler, AzureOpenAI
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from . import models, crawl_url
import json
from typing_extensions import override
from uuid import uuid4
import os

client = OpenAI(api_key=settings.OPENAI_API_KEY)

client_azure = AzureOpenAI(
    api_key=settings.AZURE_API_KEY,
    api_version="2024-05-01-preview",
    azure_endpoint=settings.AZURE_END_POINT,
)


def prepare_company_file(company_name):
    assistant_model, created = models.SummariserAssistant.objects.get_or_create(id=1)
    if created:
        assistant = client.beta.assistants.create(
            name="Text Assistant",
            instructions=(
                "You are a professional writer tasked with creating a comprehensive and detailed text about a company based on the provided files. Your goal is to extract and include all relevant information, ensuring that the text answers any conceivable questions about the company. Your text should cover: Products and Services: Describe the company's products and services, including their key features and benefits Contact Information: Provide all relevant contact details, such as address, phone number, email address, and website Advantages: Highlight the unique benefits and competitive advantages of the company Team: Include information about the team, focusing on key members and their roles Pricing: If available, include information on pricing or pricing models Testimonials: Share any customer or client testimonials that reflect the company’s reputation and client satisfaction Achievements: Detail notable achievements, awards, or recognitions that the company has received History: Outline the company’s founding history, including its origin, milestones, and growth over time Locations: List the company's locations, including headquarters and any additional offices or branches Your text should be at least 600 words long and provide a thorough overview of the company, ensuring that all important aspects are covered. "
            ),
            model="gpt-4o",
            tools=[{"type": "file_search"}],
        )
        assistant_model.assistant_id = assistant.id
        assistant_model.save()
    file_paths = [f"{company_name}.txt", "chat_bot_creator_laxout.txt"]
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
    crawl_url.save_text_to_file(new_text_content, f"{company_name}.txt")
    return HttpResponse("OK")


def create_assistant(company_name, customer_object):
    assistant = client.beta.assistants.create(
        name="Business Assistant",
        instructions=(
            f"You are a helpful chat assistant for {company_name} and you answer questions of their customers and help them. Don't mention any uploaded files or sources in your responses and if you don't know an answer just refer to the contact informations."
            f"Answer in the same language as the chat partner and be very polite and nice."
        ),
        model="gpt-4o-mini",
        tools=[{"type": "file_search"}],
    )

    vector_store = client.beta.vector_stores.create(name=company_name)

    print("Ausgeführt")

    file_paths = [f"{company_name}.txt"]

    file_streams = []
    for path in file_paths:
        with open(path, "rb") as file:
            content = file.read()
            if not content:
                raise ValueError(f"The file {path} is empty or not valid.")
            file_ext = path.split(".")[-1]
            file_streams.append(open(path, "rb"))

    if not file_streams:
        raise ValueError("No valid files to process.")

    file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id, files=file_streams
    )

    assistant = client.beta.assistants.update(
        assistant_id=assistant.id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
    )

    # message_files = [
    #     client.files.create(file=open(path, "rb"), purpose="assistants")
    #     for path in file_paths
    #     if os.path.getsize(path) > 0
    # ]

    # attachments = [
    #     {"file_id": message_file.id, "tools": [{"type": "file_search"}]}
    #     for message_file in message_files
    # ]

    # thread = client.beta.threads.create(
    #     messages=[
    #         {
    #             "role": "user",
    #             "content": "Wer ist Inhaber von Proviral?",
    #             "attachments": attachments,
    #         }
    #     ]
    # )

    # run = client.beta.threads.runs.create_and_poll(
    #     thread_id=thread.id, assistant_id=assistant.id
    # )

    # messages = list(
    #     client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id)
    # )

    # message_content = messages[0].content[0].text
    # annotations = message_content.annotations
    # citations = []
    # for index, annotation in enumerate(annotations):
    #     message_content.value = message_content.value.replace(
    #         annotation.text, f"[{index}]"
    #     )
    #     if file_citation := getattr(annotation, "file_citation", None):
    #         cited_file = client.files.retrieve(file_citation.file_id)
    #         citations.append(f"[{index}] {cited_file.filename}")

    # print(message_content.value)
    # print("\n".join(citations))

    print(f"Assistant ID: {assistant.id}")

    customer_object.chatbot_url = f"/api/{company_name}/assistant-chat/"
    customer_object.css_url = f"/api/{company_name}/dynamic-css/"
    customer_object.js_url = f"/api/{company_name}/dynamic-js/"
    customer_object.save_user_data_url = f"/api/{company_name}/saveuserdata/"
    customer_object.send_message_url = f"/api/{company_name}/sendmessage/"
    customer_object.save()

    chat_assistant = models.ChatAssistant.objects.create(created_for=customer_object)
    chat_assistant.vector_store_id = vector_store.id
    chat_assistant.assistant_id = assistant.id
    chat_assistant.partner_name = customer_object.company_name
    chat_assistant.save()

    return HttpResponse("OK")


def save_user_data(request, partner=None):
    customer = models.Customer.objects.get(company_name=partner)

    if request.method == "POST":
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


def chatApplication(request, partner=None):
    customer = models.Customer.objects.get(company_name=partner)

    if request.method == "POST":
        print("POST Bedingung")
        uid = request.POST.get("uid")
        if uid is None or uid == "":
            uid = str(uuid4())
            while models.ChatbotUser.objects.filter(uid=uid).exists():
                uid = str(uuid4())

        print("HÄ")
        chat = models.ChatbotUser.objects.create(uid=uid, created_for=customer.id)

        try:
            assistant_instance = models.ChatAssistant.objects.get(partner_name=partner)
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

            # Hier erzeugst du eine neue Thread-ID für jeden neuen Chat
            thread = client.beta.threads.create(
                messages=[
                    {
                        "role": "user",
                        "content": question,
                    }
                ]
            )

            run = client.beta.threads.runs.create_and_poll(
                thread_id=thread.id, assistant_id=assistant_instance.assistant_id
            )

            messages = list(
                client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id)
            )

            message_content = messages[0].content[0].text

            message_object = models.ChatMessage.objects.create(
                message=message_content.value,
                bot_message=True,
            )
            chat.messages.add(message_object)
            chat.save()

            return JsonResponse(
                {"answer_chat_assistant": message_content.value, "uid": uid}
            )

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return render(
        request,
        "chat_bot_app/index.html",
        {"customer": customer, "partner_name": partner},
    )


def generate_interest_email(question_string, name, language):
    response = client.chat.completions.create(
        model="gpt-4o",
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
   
    css_url = "test"
    js_url = "test"

