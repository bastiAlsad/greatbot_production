var id_count = 0;
var uid = "";
var chatbotResponses = 0;
var token = document.querySelector('meta[name="csrf-token-greatbot-ai"]').getAttribute('content');
var company_name = document.querySelector('meta[name="company-name-greatbot-ai"]').getAttribute('content');
// var save_user_data_url = document.querySelector('meta[name="save-user-data-url-greatbot-ai"]').getAttribute('content');
// var send_message_url = document.querySelector('meta[name="send-message-url-greatbot-ai"]').getAttribute('content');

function sendPersonalData() {
  var name = document.getElementById("chatbot_user_name").value;
  var email = document.getElementById("chatbot_user_email").value;

  if (name.trim() !== "" && email.trim() !== "") {
    // Prepare and send the request
    let token = document.querySelector('meta[name="csrf-token-chatbot"]').getAttribute('content');
    let formedData = new FormData();
    formedData.append("name", name);
    formedData.append("email", email);
    formedData.append("uid", uid);

    fetch("https://greatbot.eu.pythonanywhere.com/api/"+company_name+"/assistant-chat/saveuserdata/", {
      method: "POST",
      headers: {
        'X-CSRFToken': token,
      },
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

    fetch("https://greatbot.eu.pythonanywhere.com/api/"+company_name+"/assistant-chat/sendmessage/", {
      method: "POST",
      headers: {
        'X-CSRFToken': token,
      },
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