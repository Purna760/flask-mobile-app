document.addEventListener("DOMContentLoaded", () => {
  const path = window.location.pathname;

  if (path === "/") {
    setupAuthPage();
  } else if (path === "/dashboard") {
    setupDashboardPage();
  }
});

// ---------- AUTH PAGE ----------

function setupAuthPage() {
  const tabs = document.querySelectorAll(".tab-button");
  const panels = document.querySelectorAll(".tab-panel");
  const msg = document.getElementById("auth-message");

  tabs.forEach(btn => {
    btn.addEventListener("click", () => {
      tabs.forEach(b => b.classList.remove("active"));
      panels.forEach(p => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(btn.dataset.tab).classList.add("active");
      msg.textContent = "";
      msg.classList.remove("error");
    });
  });

  document.getElementById("login-btn").addEventListener("click", async () => {
    msg.textContent = "";
    msg.classList.remove("error");
    const username = document.getElementById("login-username").value.trim();
    const password = document.getElementById("login-password").value;

    const res = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });

    const data = await res.json();
    if (!res.ok) {
      msg.textContent = data.error || "Login failed";
      msg.classList.add("error");
    } else {
      window.location.href = "/dashboard";
    }
  });

  document.getElementById("register-btn").addEventListener("click", async () => {
    msg.textContent = "";
    msg.classList.remove("error");
    const username = document.getElementById("reg-username").value.trim();
    const password = document.getElementById("reg-password").value;

    const res = await fetch("/api/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });

    const data = await res.json();
    if (!res.ok) {
      msg.textContent = data.error || "Registration failed";
      msg.classList.add("error");
    } else {
      msg.textContent = "Registered! You can now log in.";
    }
  });
}

// ---------- DASHBOARD PAGE ----------

function setupDashboardPage() {
  const notesList = document.getElementById("notes-list");
  const msg = document.getElementById("notes-message");

  document.getElementById("logout-btn").addEventListener("click", async () => {
    await fetch("/api/logout", { method: "POST" });
    window.location.href = "/";
  });

  document.getElementById("add-note-btn").addEventListener("click", async () => {
    const textarea = document.getElementById("note-input");
    const content = textarea.value.trim();
    if (!content) {
      msg.textContent = "Note cannot be empty.";
      msg.classList.add("error");
      return;
    }

    const res = await fetch("/api/notes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content })
    });

    const data = await res.json();
    if (!res.ok) {
      msg.textContent = data.error || "Could not add note";
      msg.classList.add("error");
    } else {
      textarea.value = "";
      msg.textContent = "";
      msg.classList.remove("error");
      prependNote(notesList, data.note);
    }
  });

  // Load notes initially
  loadNotes(notesList, msg);
}

async function loadNotes(listEl, msgEl) {
  listEl.innerHTML = "";
  const res = await fetch("/api/notes");
  if (!res.ok) {
    msgEl.textContent = "Failed to load notes.";
    msgEl.classList.add("error");
    return;
  }
  const data = await res.json();
  if (!data.notes.length) {
    msgEl.textContent = "No notes yet. Add your first one!";
    msgEl.classList.remove("error");
  } else {
    msgEl.textContent = "";
    msgEl.classList.remove("error");
  }
  data.notes.forEach(note => prependNote(listEl, note, false));
}

function prependNote(listEl, note, toTop = true) {
  const li = document.createElement("li");
  li.className = "note-item";
  li.dataset.id = note.id;

  const content = document.createElement("div");
  content.className = "note-content";
  content.textContent = note.content;

  const meta = document.createElement("div");
  meta.className = "note-meta";
  meta.textContent = note.created_at;

  const delBtn = document.createElement("button");
  delBtn.className = "small danger";
  delBtn.textContent = "Delete";
  delBtn.addEventListener("click", () => deleteNote(li, note.id));

  li.appendChild(content);
  li.appendChild(meta);
  li.appendChild(delBtn);

  if (toTop) {
    listEl.prepend(li);
  } else {
    listEl.appendChild(li);
  }
}

async function deleteNote(li, id) {
  const res = await fetch(`/api/notes/${id}`, { method: "DELETE" });
  if (res.ok) {
    li.remove();
  }
}
