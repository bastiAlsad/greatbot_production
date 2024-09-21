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