const welcomePanel = document.querySelector("#welcome-panel");
const welcomeStatus = document.querySelector("#welcome-status");
const signInLink = document.querySelector("#sign-in");
const retrySignIn = document.querySelector("#retry-sign-in");
const chatPanel = document.querySelector("#chat-panel");
const chatList = document.querySelector("#chat-list");
const historyStatus = document.querySelector("#history-status");
const conversation = document.querySelector("#conversation");
const emptyState = document.querySelector("#empty-state");
const messages = document.querySelector("#messages");
const newChat = document.querySelector("#new-chat");
const form = document.querySelector("#chat-form");
const question = document.querySelector("#question");
const sendMessage = document.querySelector("#send-message");
const chatStatus = document.querySelector("#chat-status");
const accountControls = document.querySelector("#account-controls");
const accountEmail = document.querySelector("#account-email");
const logoutButton = document.querySelector("#logout");

let sessionId = null;

function setChatStatus(message, isError = false) {
  chatStatus.textContent = message;
  chatStatus.dataset.error = String(isError);
}

function markActiveChat() {
  for (const button of chatList.querySelectorAll("button")) {
    button.setAttribute("aria-current", String(button.dataset.sessionId === sessionId));
  }
}

function setActiveSession(id) {
  sessionId = id;
  const url = new URL(window.location.href);
  if (id === null) {
    url.searchParams.delete("session");
  } else {
    url.searchParams.set("session", id);
  }
  window.history.replaceState(null, "", url);
  markActiveChat();
}

function setChatBusy(busy) {
  sendMessage.disabled = busy;
  newChat.disabled = busy;
  logoutButton.disabled = busy;
  question.readOnly = busy;
  chatList.inert = busy;
}

function resetConversation() {
  setActiveSession(null);
  messages.replaceChildren();
  emptyState.hidden = false;
  question.value = "";
  setChatStatus("");
}

function showSignIn(message) {
  resetConversation();
  chatList.replaceChildren();
  accountControls.hidden = true;
  accountEmail.textContent = "";
  chatPanel.hidden = true;
  welcomePanel.hidden = false;
  welcomeStatus.textContent = message;
  signInLink.hidden = false;
}

async function checkSignIn() {
  welcomeStatus.textContent = "Checking sign-in…";
  retrySignIn.hidden = true;

  try {
    const response = await fetch("/me", { cache: "no-store" });

    if (response.status === 401) {
      showSignIn("Sign in to ask questions and start a conversation.");
      return;
    }

    if (!response.ok) {
      throw new Error("Sign-in check failed.");
    }

    const account = await response.json();
    accountEmail.textContent = account.email || "Signed in";
    accountControls.hidden = false;
    welcomePanel.hidden = true;
    chatPanel.hidden = false;
  } catch {
    welcomeStatus.textContent = "Could not check your sign-in. Try again.";
    retrySignIn.hidden = false;
    retrySignIn.focus();
    return;
  }

  const savedSessionId = new URLSearchParams(window.location.search).get("session");
  if (savedSessionId) {
    await openConversation(savedSessionId);
  }
  if (!chatPanel.hidden) {
    setChatBusy(true);
    await loadChatList();
    setChatBusy(false);
  }
}

async function signOut() {
  setChatBusy(true);

  try {
    const response = await fetch("/logout", { method: "POST" });
    if (!response.ok) {
      throw new Error("Sign-out request failed.");
    }
    window.location.replace("/");
  } catch {
    setChatBusy(false);
    setChatStatus("Could not sign out. Try again.", true);
    logoutButton.focus();
  }
}

async function loadChatList() {
  historyStatus.textContent = "Loading chats…";

  try {
    const response = await fetch("/chats", { cache: "no-store" });
    if (response.status === 401) {
      showSignIn("Sign in again to continue.");
      signInLink.focus();
      return;
    }
    if (!response.ok) {
      throw new Error("Chat list request failed.");
    }

    const sessions = await response.json();
    chatList.replaceChildren();
    for (const chat of sessions) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "chat-link";
      button.dataset.sessionId = chat.session_id;
      button.textContent = chat.title;
      button.addEventListener("click", () => openConversation(chat.session_id));
      chatList.append(button);
    }
    markActiveChat();
    historyStatus.textContent = sessions.length === 0 ? "No saved chats yet." : "";
  } catch {
    historyStatus.textContent = "Could not load saved chats. Refresh to retry.";
  }
}

async function openConversation(id) {
  if (sendMessage.disabled || id === sessionId) {
    return;
  }
  setChatBusy(true);
  setChatStatus("Loading conversation…");

  try {
    const response = await fetch(`/chat/${encodeURIComponent(id)}/messages`, { cache: "no-store" });
    if (response.status === 401) {
      showSignIn("Sign in again to continue.");
      signInLink.focus();
      return;
    }
    if (response.status === 404 || response.status === 422) {
      if (sessionId === null) {
        setActiveSession(null);
      }
      setChatStatus("This conversation is unavailable.", true);
      return;
    }
    if (!response.ok) {
      throw new Error("Conversation request failed.");
    }

    const savedMessages = await response.json();
    messages.replaceChildren();
    emptyState.hidden = savedMessages.length > 0;
    for (const message of savedMessages) {
      addMessage(message.role, message.content);
    }
    scrollToLatest();
    setActiveSession(id);
    question.value = "";
    setChatStatus("");
  } catch {
    setChatStatus("Could not load the conversation. Try again.", true);
  } finally {
    setChatBusy(false);
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
  return message;
}

function scrollToLatest() {
  conversation.scrollTop = conversation.scrollHeight;
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

  setChatBusy(true);
  setChatStatus("Waiting for a reply…");

  const pendingMessage = addMessage("user", query);
  scrollToLatest();
  const isNewChat = sessionId === null;
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
    scrollToLatest();
    setActiveSession(reply.session_id);
    question.value = "";
    receivedReply = true;
    setChatStatus("");
    if (isNewChat) {
      await loadChatList();
    }
  } catch {
    setChatStatus("Could not reach the chat API. Try again.", true);
  } finally {
    if (!receivedReply) {
      pendingMessage.remove();
      emptyState.hidden = messages.childElementCount > 0;
    }
    setChatBusy(false);
    if (!chatPanel.hidden) {
      question.focus();
    }
  }
}

retrySignIn.addEventListener("click", checkSignIn);
logoutButton.addEventListener("click", signOut);
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
