const chat = document.getElementById("chat");
const emptyState = document.getElementById("empty-state");
const messages = document.getElementById("messages");
const form = document.getElementById("ask-form");
const input = document.getElementById("question-input");
const suggestions = document.getElementById("suggestions");

async function ask(question) {
  emptyState.style.display = "none";
  addUserMessage(question);
  const thinking = addThinkingMessage();

  try {
    const response = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    thinking.remove();

    if (!response.ok) {
      const body = await response.json();
      addErrorMessage(body.detail || "Something went wrong.");
      return;
    }

    const data = await response.json();
    addAnswerMessage(data.sql, data.columns, data.rows);
  } catch (err) {
    thinking.remove();
    addErrorMessage("Could not reach the server.");
  }
}

function scrollToBottom() {
  chat.scrollTop = chat.scrollHeight;
}

function addUserMessage(text) {
  const message = document.createElement("div");
  message.className = "message user";
  const content = document.createElement("div");
  content.className = "content";
  content.textContent = text;
  message.appendChild(content);
  messages.appendChild(message);
  scrollToBottom();
}

function addThinkingMessage() {
  const message = document.createElement("div");
  message.className = "message assistant";
  const content = document.createElement("div");
  content.className = "content";
  content.textContent = "Thinking...";
  message.appendChild(content);
  messages.appendChild(message);
  scrollToBottom();
  return message;
}

function addAnswerMessage(sql, columns, rows) {
  const message = document.createElement("div");
  message.className = "message assistant";
  const content = document.createElement("div");
  content.className = "content";

  const pre = document.createElement("pre");
  pre.textContent = sql;
  content.appendChild(pre);

  if (rows.length === 0) {
    const empty = document.createElement("p");
    empty.textContent = "No rows returned.";
    content.appendChild(empty);
  } else {
    content.appendChild(buildTable(columns, rows));
  }

  message.appendChild(content);
  messages.appendChild(message);
  scrollToBottom();
}

function buildTable(columns, rows) {
  const table = document.createElement("table");

  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  columns.forEach((column) => {
    const th = document.createElement("th");
    th.textContent = column;
    headRow.appendChild(th);
  });
  thead.appendChild(headRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    row.forEach((value) => {
      const td = document.createElement("td");
      td.textContent = value;
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);

  return table;
}

function addErrorMessage(text) {
  const message = document.createElement("div");
  message.className = "message assistant";
  const content = document.createElement("div");
  content.className = "content error";
  content.textContent = text;
  message.appendChild(content);
  messages.appendChild(message);
  scrollToBottom();
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const question = input.value.trim();
  if (!question) return;
  input.value = "";
  ask(question);
});

suggestions.querySelectorAll(".suggestion").forEach((button) => {
  button.addEventListener("click", () => ask(button.dataset.question));
});

const libraryBtn = document.getElementById("library-btn");
const libraryBackdrop = document.getElementById("library-backdrop");
const libraryClose = document.getElementById("library-close");
const libraryBody = document.getElementById("library-body");

function openLibrary() {
  libraryBackdrop.classList.add("open");
}

function closeLibrary() {
  libraryBackdrop.classList.remove("open");
}

libraryBtn.addEventListener("click", openLibrary);
libraryClose.addEventListener("click", closeLibrary);
libraryBackdrop.addEventListener("click", (event) => {
  if (event.target === libraryBackdrop) closeLibrary();
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeLibrary();
});

libraryBody.querySelectorAll(".library-item").forEach((button) => {
  button.addEventListener("click", () => {
    closeLibrary();
    ask(button.dataset.question);
  });
});
