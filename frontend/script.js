const form = document.querySelector("#chat-form");
const question = document.querySelector("#question");
const output = document.querySelector("#output");

let sessionId = null;

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: question.value,
        session_id: sessionId,
      }),
    });

    if (!response.ok) {
      output.textContent = `Request failed (${response.status}).`;
      return;
    }

    const reply = await response.json();
    output.textContent = reply.content;
    sessionId = reply.session_id;
  } catch {
    output.textContent = "Could not get a reply from the server.";
  }
});
