import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from string import Template
from django.core.management.base import BaseCommand
from django.utils import timezone
from chat_bot_app import models, openAi, crawl_url
from django.conf import settings
from openai import OpenAI
import os
import calendar


class Command(BaseCommand):
    help = "Manages leads and sends emails"

    def handle(self, *args, **kwargs):
        def send_emails():
            port = 587
            password = "jezm nesb fhpj tvrv"
            username = "laxoutapp@gmail.com"
            subject = "Lead durch Chatbot"
            try:
                server = smtplib.SMTP("smtp.gmail.com", port)
                server.starttls()
                server.login(username, password)

                all_customers = [customer for customer in models.Customer.objects.all()]
                for customer in all_customers:
                    leads_customer = [
                        chatbot_bot_user
                        for chatbot_bot_user in models.ChatbotUser.objects.filter(
                            created_for=customer.id, lead_processed=False
                        )
                    ]
                    for lead in leads_customer:
                        chat_bot_user_name = lead.name
                        chat_bot_user_email = lead.email

                        if chat_bot_user_email != None and chat_bot_user_email != "":
                            if chat_bot_user_name == None:
                                chat_bot_user_name == ""
                            messages_questions = lead.messages.filter(bot_message=False)
                            question_string = " ".join(
                                [message.message for message in messages_questions]
                            )

                            chat_bot_user_interests_email = (
                                openAi.generate_interest_email(
                                    question_string, lead.name, "german"
                                )
                            )

                            html_template = Template(
                                """
                                <!DOCTYPE html>
<html lang="de">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lead email</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet"
        integrity="sha384-T3c6CoIi6uLrA9TneNEoa7RxnatzjcDSCmG1MXxSR1GAsXEV/Dwwykc2MPK8M2HN" crossorigin="anonymous">
    <style>
        body {
            padding-top: 90px;
            display: flex;
            flex-direction: column;
            justify-content: start;
            align-items: start;
            margin: 0;
            font-family: 'Arial', sans-serif;
            background-color: #f5f5f5;
        }

        .container {
            display: flex;
            flex-direction: column;
            width: 90%;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            border-radius: 10px;
            overflow: hidden;
            background-color: white;
            padding: 20px;
            margin-bottom: 20px;
        }

        .form-container {
            width: 100%;
            margin: auto;
            text-align: left;
        }

        .form-container h2 {
            margin-bottom: 20px;
            font-size: 24px;
            color: #333;
        }

        .form-container label {
            display: block;
            margin-bottom: 5px;
            text-align: left;
            color: #777;
        }

        .form-container input,
        .form-container select {
            width: 100%;
            padding: 10px;
            margin-bottom: 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
            box-sizing: border-box;
        }

        .form-container input:focus,
        .form-container select:focus {
            border-color: #6c63ff;
            outline: none;
            box-shadow: 0 0 8px rgba(108, 99, 255, 0.2);
        }

        .form-container button {
            width: 100%;
            padding: 10px;
            border: none;
            border-radius: 5px;
            background-color: #6c63ff;
            color: white;
            font-size: 16px;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }

        .form-container button:hover {
            background-color: #5753d8;
        }

        .text-field {
            display: flex;
            flex-direction: column;
            margin-bottom: 15px;
        }

        .text-field input {
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 10px;
            font-size: 16px;
        }

        .text-field label {
            margin-bottom: 5px;
            color: #777;
        }
    </style>
</head>

<body>
    <div class="container">
        <div class="form-container">
            <h2>Lead details:</h2>

            <div class="text-field">
                <label for="lead-name">Vor-Nachname</label>
                <input type="text" id="lead-name" name="lead_name" value="${chat_bot_user_name}" readonly>
            </div>

            <div class="text-field">
                <label for="lead-email">E-Mail-Adresse</label>
                <div style="display: flex; flex-direction: row; justify-content: space-between;">
                    <input type="email" id="lead-email" name="lead_email" value="${chat_bot_user_email}" readonly>
                    <div style="margin-left: 20px; margin-top: 5px; position: relative;">
                        <svg id="copy-btn" xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor"
                            class="bi bi-copy" viewBox="0 0 16 16" style="cursor: pointer;">
                            <path fill-rule="evenodd"
                                d="M4 2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2zm2-1a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1zM2 5a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1v-1h1v1a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h1v1z" />
                        </svg>
                        <div id="copy-confirmation"
                            style="display: none; position: absolute; top: -30px; left: 50%; transform: translateX(-50%); background-color: #6c63ff; color: white; padding: 5px 10px; border-radius: 5px; font-size: 14px;">
                            Kopiert!
                        </div>
                    </div>
                </div>
            </div>

            <div class="text-field">
                <label for="lead-interests">Interessen</label>
                <textarea style="height: 400px;" type="text" id="lead-interests" name="lead_interests">
                    ${chat_bot_user_interests_email}
                </textarea>
            </div>

        </div>
    </div>
</body>

</html>

                                """
                            )

                            msg = MIMEMultipart()
                            msg["From"] = username
                            msg["To"] = customer.lead_email
                            msg["Subject"] = subject

                            html_content = html_template.substitute(
                                chat_bot_user_name=chat_bot_user_name,
                                chat_bot_user_email=chat_bot_user_email,
                                chat_bot_user_interests_email=chat_bot_user_interests_email,
                            )
                            msg.attach(MIMEText(html_content, "html"))

                            server.sendmail(
                                username, customer.lead_email, msg.as_string()
                            )

                            models.Lead.objects.create(created_for=customer.id)
                        lead.lead_processed = True
                        lead.save()

                server.quit()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))

        send_emails()

        def send_stats_emails():
            today = timezone.now().date()

            last_day_of_month = calendar.monthrange(today.year, today.month)[1]

            if today.day ==today.day: # last_day_of_month:
                port = 587
                password = "jezm nesb fhpj tvrv"
                username = "laxoutapp@gmail.com"
                subject = "Monatliche Zusammenfassung"
                try:
                    server = smtplib.SMTP("smtp.gmail.com", port)
                    server.starttls()
                    server.login(username, password)

                    all_customers = models.Customer.objects.all()
                    for customer in all_customers:
                        html_template = Template(
                            """
                            <style>
                                .container {
                                    display: flex;
                                    width: 90%;
                                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                                    border-radius: 10px;
                                    overflow: hidden;
                                    background-color: white;
                                    padding: 20px;
                                    margin-bottom: 20px;
                                    font-family: sans-serif;
                                }
                                .form-container {
                                    width: 100%;
                                    margin: auto;
                                    text-align: left;
                                }
                            </style>
                            <div class="container">
                                <div class="form-container">
                                    <h2>Statistiken:</h2>
                                    <label for="monthly_requests">Anfragen (Monat):</label>
                                    <h3>${request_count}</h3>
        
                                    <label for="bot_users">Nutzer des Chatbots (Monat):</label>
                                    <h3>${user_count}</h3>
        
                                    <label for="generated_leads">Generierte Leads (Monat):</label>
                                    <h3>${leads_count}</h3>
        
                                    <label for="conversion_rate">Conversion Rate (Monat):</label>
                                    <h3>${conversion_rate}%</h3>
                                </div>
                            </div>
                            """
                        )

                        msg = MIMEMultipart()
                        msg["From"] = username
                        msg["To"] = customer.lead_email
                        msg["Subject"] = subject

                        current_year = timezone.now().year
                        current_month = timezone.now().month

                        request_count = models.Request.objects.filter(
                            created_for=customer.id,
                            created_at__year=current_year,
                            created_at__month=current_month,
                        ).count()
                        user_count = models.ChatbotUser.objects.filter(
                            created_for=customer.id,
                            created_at__year=current_year,
                            created_at__month=current_month,
                        ).count()
                        leads_count = models.Lead.objects.filter(
                            created_for=customer.id,
                            created_at__year=current_year,
                            created_at__month=current_month,
                        ).count()

                        # Fehlerbehandlung, falls user_count 0 ist, um Division durch 0 zu vermeiden
                        if user_count > 0:
                            conversion_rate = (leads_count / user_count) * 100
                        else:
                            conversion_rate = 0

                        html_content = html_template.substitute(
                            request_count=request_count,
                            user_count=user_count,
                            leads_count=leads_count,
                            conversion_rate=conversion_rate,
                        )

                        msg.attach(MIMEText(html_content, "html"))

                        server.sendmail(username, customer.lead_email, msg.as_string())

                    server.quit()
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
            else:
                self.stdout.write(
                    self.style.WARNING("Heute ist nicht der letzte Tag des Monats.")
                )
        send_stats_emails()

            #         chat_assistant = models.ChatAssistant.objects.get(

    #             created_for=models.Customer.objects.get(
    #                 company_name=customer.company_name
    #             )
    #         )
    #         # Crawl the website
    #         crawl_url.crawl_website(customer.website_url, customer.company_name)

    #         # Update vector store logic
    #         company_name = customer.company_name
    #         vector_store_id = self.update_vector_store(company_name,chat_assistant)

    #         # Update the assistant
    #         assistant_id = self.update_assistant(chat_assistant, vector_store_id)

    #         # Update the chat assistant model
    #         chat_assistant.vector_store_id = vector_store_id
    #         chat_assistant.assistant_id = assistant_id
    #         chat_assistant.partner_name = customer.company_name
    #         chat_assistant.save()

    #         print(f"Assistant for {company_name} updated successfully.")

    # def update_vector_store(self, company_name, chat_assistant):
    #         client = OpenAI(api_key=settings.OPENAI_API_KEY)

    #         # Check if vector store exists and delete it

    #         client.beta.vector_stores.delete(
    #             vector_store_id=chat_assistant.vector_store_id
    #         )

    #         # Create new vector store
    #         vector_store = client.beta.vector_stores.create(name=company_name)
    #         print(f"Vector store for {company_name} created with ID: {vector_store.id}")

    #         file_paths = [f"{company_name}.txt", "chat_bot_creator_laxout.txt"]
    #         uploaded_files_dir = os.path.join("uploaded_files", company_name)
    #         if os.path.exists(uploaded_files_dir):
    #             file_paths += [
    #                 os.path.join(uploaded_files_dir, file)
    #                 for file in os.listdir(uploaded_files_dir)
    #             ]

    #         supported_formats = [
    #             "c",
    #             "cpp",
    #             "css",
    #             "csv",
    #             "docx",
    #             "gif",
    #             "html",
    #             "java",
    #             "jpeg",
    #             "jpg",
    #             "js",
    #             "json",
    #             "md",
    #             "pdf",
    #             "php",
    #             "png",
    #             "pptx",
    #             "py",
    #             "rb",
    #             "tar",
    #             "tex",
    #             "ts",
    #             "txt",
    #             "webp",
    #             "xlsx",
    #             "xml",
    #             "zip",
    #         ]

    #         file_streams = []
    #         for path in file_paths:
    #             if os.path.getsize(path) == 0:
    #                 print(f"The file {path} is empty or not valid.")
    #                 continue
    #             with open(path, "rb") as file:
    #                 content = file.read()
    #                 if not content:
    #                     raise ValueError(f"The file {path} is empty or not valid.")
    #                 file_ext = path.split(".")[-1]
    #                 if file_ext not in supported_formats:
    #                     raise ValueError(f"The file {path} has an unsupported format.")
    #                 file_streams.append(open(path, "rb"))

    #         if not file_streams:
    #             raise ValueError("No valid files to process.")

    #         file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
    #             vector_store_id=vector_store.id, files=file_streams
    #         )

    #         return vector_store.id

    # def update_assistant(self, chat_assistant, vector_store_id):
    #         client = OpenAI(api_key=settings.OPENAI_API_KEY)

    #         assistant = client.beta.assistants.update(
    #             assistant_id=chat_assistant.assistant_id,
    #             tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},
    #         )
    #         return assistant.id
