// FILE: static/js/group.js
// Read-only group detail page.

async function fetchJson(url, options = {}) {
  const res = await fetch(url, {
    credentials: "include",
    headers: { Accept: "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`HTTP ${res.status} for ${url}`);
  }
  return res.json();
}

function pickMemberName(u) {
  return (
    u.name ??
    u.full_name ??
    u.username ??
    u.email ??
    "Member"
  );
}

async function initGroupPage() {
  const params = new URLSearchParams(window.location.search);
  const groupId = params.get("group_id");

  if (!groupId) {
    window.location.href = "/groups";
    return;
  }

  const nameEl = document.getElementById("group-name");
  const descEl = document.getElementById("group-desc");
  const dateEl = document.getElementById("group-date");
  const membersEl = document.getElementById("group-members");

  try {
    const group = await fetchJson(`/api/groups/${encodeURIComponent(groupId)}`);
    if (nameEl) nameEl.textContent = group.name ?? "Group";
    if (descEl) descEl.textContent = group.description || "";
    if (dateEl && group.created_at) {
      dateEl.textContent = new Date(group.created_at).toLocaleDateString();
    }
  } catch (err) {
    console.error("Failed to load group:", err);
    alert("Group not found.");
    window.location.href = "/groups";
    return;
  }

  if (!membersEl) return;

  try {
    const data = await fetchJson(`/api/groups/${encodeURIComponent(groupId)}/members`);
    const members = Array.isArray(data?.members) ? data.members : (data.data || []);
    if (!members.length) {
      membersEl.innerHTML = '<li class="muted">No members found for this group.</li>';
      return;
    }

    membersEl.innerHTML = "";
    members.forEach(u => {
      const li = document.createElement("li");
      li.textContent = pickMemberName(u);
      membersEl.appendChild(li);
    });
  } catch (err) {
    console.error("Failed to load members:", err);
    membersEl.innerHTML = '<li class="muted">Error loading members.</li>';
  }
}

// ---- AI SUMMARY FEATURE ----

async function setupAISummary(groupId) {
  const btn = document.getElementById("ai-summary-btn");
  const msg = document.getElementById("ai-summary-msg");
  const box = document.getElementById("ai-summary-box");

  if (!btn) return;

  btn.addEventListener("click", async () => {
    msg.textContent = "Generating summary…";
    box.style.display = "none";
    box.textContent = "";

    try {
      const res = await fetch(`/api/groups/${groupId}/generate_summary`, {
        method: "POST",
        credentials: "include",
        headers: { "Accept": "application/json" }
      });

      const data = await res.json();

      if (!res.ok) {
        msg.textContent = data.detail || "Error generating summary.";
        return;
      }

      msg.textContent = "";
      box.textContent = data.summary;
      box.style.display = "block";

    } catch (err) {
      msg.textContent = "Unexpected error accessing AI service.";
      console.error(err);
    }
  });
}

// On page load
document.addEventListener("DOMContentLoaded", async () => {
  await initGroupPage();

  const params = new URLSearchParams(window.location.search);
  const groupId = params.get("group_id");

  setupAISummary(groupId);
});
