const welcomePanel = document.querySelector("#welcome-panel");
const welcomeStatus = document.querySelector("#welcome-status");
const signInLink = document.querySelector("#sign-in");
const retrySignIn = document.querySelector("#retry-sign-in");
const chatPanel = document.querySelector("#chat-panel");
const conversation = document.querySelector("#conversation");
const emptyState = document.querySelector("#empty-state");
const messages = document.querySelector("#messages");
const newChat = document.querySelector("#new-chat");
const form = document.querySelector("#chat-form");
const question = document.querySelector("#question");
const sendMessage = document.querySelector("#send-message");
const chatStatus = document.querySelector("#chat-status");

let sessionId = null;

function setChatStatus(message, isError = false) {
  chatStatus.textContent = message;
  chatStatus.dataset.error = String(isError);
}

function resetConversation() {
  sessionId = null;
  messages.replaceChildren();
  emptyState.hidden = false;
  question.value = "";
  setChatStatus("");
}

function showSignIn(message) {
  resetConversation();
  chatPanel.hidden = true;
  welcomePanel.hidden = false;
  welcomeStatus.textContent = message;
  signInLink.hidden = false;
}

async function checkSignIn() {
  welcomeStatus.textContent = "Checking sign-in…";
  retrySignIn.hidden = true;

  try {
    const response = await fetch("/me");

    if (response.status === 401) {
      showSignIn("Sign in to ask questions and start a conversation.");
      return;
    }

    if (!response.ok) {
      throw new Error("Sign-in check failed.");
    }

    welcomePanel.hidden = true;
    chatPanel.hidden = false;
  } catch {
    welcomeStatus.textContent = "Could not check your sign-in. Try again.";
    retrySignIn.hidden = false;
    retrySignIn.focus();
  }
}

function addMessage(role, content) {
  const message = document.createElement("article");
  message.classList.add("message", `message-${role}`);

  const name = document.createElement("strong");
  name.className = "message-label";
  name.textContent = role === "user" ? "You" : "Ternwell";

  const text = document.createElement("p");
  text.textContent = content;

  message.append(name, text);
  messages.append(message);
  emptyState.hidden = true;
  conversation.scrollTop = conversation.scrollHeight;
  return message;
}

async function submitQuestion(event) {
  event.preventDefault();

  if (sendMessage.disabled) {
    return;
  }

  const query = question.value.trim();
  if (!query) {
    setChatStatus("Enter a question.", true);
    question.focus();
    return;
  }

  sendMessage.disabled = true;
  newChat.disabled = true;
  question.readOnly = true;
  setChatStatus("Waiting for a reply…");

  const pendingMessage = addMessage("user", query);
  let receivedReply = false;

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, session_id: sessionId }),
    });

    if (response.status === 401) {
      showSignIn("Sign in again to continue.");
      signInLink.focus();
      return;
    }

    if (response.status === 404) {
      setChatStatus("This conversation is unavailable. Select New chat to start again.", true);
      return;
    }

    if (!response.ok) {
      setChatStatus(`Could not get a reply (HTTP ${response.status}). Try again.`, true);
      return;
    }

    const reply = await response.json();
    addMessage("assistant", reply.content);
    sessionId = reply.session_id;
    question.value = "";
    receivedReply = true;
    setChatStatus("");
  } catch {
    setChatStatus("Could not reach the chat API. Try again.", true);
  } finally {
    if (!receivedReply) {
      pendingMessage.remove();
      emptyState.hidden = messages.childElementCount > 0;
    }
    sendMessage.disabled = false;
    newChat.disabled = false;
    question.readOnly = false;
    if (!chatPanel.hidden) {
      question.focus();
    }
  }
}

retrySignIn.addEventListener("click", checkSignIn);
newChat.addEventListener("click", () => {
  resetConversation();
  question.focus();
});
form.addEventListener("submit", submitQuestion);
question.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    form.requestSubmit();
  }
});

checkSignIn();
