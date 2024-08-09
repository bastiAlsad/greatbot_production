import os
from django.core.management.base import BaseCommand
from django.conf import settings
from chat_bot_app import models, crawl_url
from openai import OpenAI


class Command(BaseCommand):
    help = "Manages Crawling and Updates Vector Store"

    def handle(self, *args, **kwargs):
        customers = models.Customer.objects.all()

        for customer in customers:
            chat_assistant = models.ChatAssistant.objects.get(
                created_for=models.Customer.objects.get(
                    company_name=customer.company_name
                )
            )
            # Crawl the website
            crawl_url.crawl_website(customer.website_url, customer.company_name)

            # Update vector store logic
            company_name = customer.company_name
            vector_store_id = self.update_vector_store(company_name,chat_assistant)

            # Update the assistant
            assistant_id = self.update_assistant(chat_assistant, vector_store_id)

            # Update the chat assistant model
            chat_assistant.vector_store_id = vector_store_id
            chat_assistant.assistant_id = assistant_id
            chat_assistant.partner_name = customer.company_name
            chat_assistant.save()

            print(f"Assistant for {company_name} updated successfully.")

    def update_vector_store(self, company_name, chat_assistant):
            client = OpenAI(api_key=settings.OPENAI_API_KEY)

            # Check if vector store exists and delete it

            client.beta.vector_stores.delete(
                vector_store_id=chat_assistant.vector_store_id
            )

            # Create new vector store
            vector_store = client.beta.vector_stores.create(name=company_name)
            print(f"Vector store for {company_name} created with ID: {vector_store.id}")

            file_paths = [f"{company_name}.txt", "chat_bot_creator_laxout.txt"]
            uploaded_files_dir = os.path.join("uploaded_files", company_name)
            if os.path.exists(uploaded_files_dir):
                file_paths += [
                    os.path.join(uploaded_files_dir, file)
                    for file in os.listdir(uploaded_files_dir)
                ]

            supported_formats = [
                "c",
                "cpp",
                "css",
                "csv",
                "docx",
                "gif",
                "html",
                "java",
                "jpeg",
                "jpg",
                "js",
                "json",
                "md",
                "pdf",
                "php",
                "png",
                "pptx",
                "py",
                "rb",
                "tar",
                "tex",
                "ts",
                "txt",
                "webp",
                "xlsx",
                "xml",
                "zip",
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
                    if file_ext not in supported_formats:
                        raise ValueError(f"The file {path} has an unsupported format.")
                    file_streams.append(open(path, "rb"))

            if not file_streams:
                raise ValueError("No valid files to process.")

            file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store.id, files=file_streams
            )

            return vector_store.id

    def update_assistant(self, chat_assistant, vector_store_id):
            client = OpenAI(api_key=settings.OPENAI_API_KEY)

            assistant = client.beta.assistants.update(
                assistant_id=chat_assistant.assistant_id,
                tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},
            )
            return assistant.id
