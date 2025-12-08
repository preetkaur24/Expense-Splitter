// FILE: static/js/group.js
// Read-only group detail page.

async function fetchJson(url, options = {}) {
  const res = await fetch(url, {
    credentials: "include",
    headers: { Accept: "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
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

  // Load members
  try {
    const data = await fetchJson(`/api/groups/${encodeURIComponent(groupId)}/members`);
    const members = Array.isArray(data?.members) ? data.members : (data.data || []);
    membersEl.innerHTML = "";

    if (!members.length) {
      membersEl.innerHTML = '<li class="muted">No members found for this group.</li>';
    } else {
      members.forEach(u => {
        const li = document.createElement("li");
        li.textContent = pickMemberName(u);
        membersEl.appendChild(li);
      });
    }
  } catch (err) {
    console.error("Failed to load members:", err);
    membersEl.innerHTML = '<li class="muted">Error loading members.</li>';
  }

  // ---------------------------
  // Trip summary generation
  // ---------------------------

  const summaryBtn = document.getElementById("generate-summary-btn");
  const summaryBox = document.getElementById("trip-summary-box");
  const loadingEl = document.getElementById("summary-loading");

  summaryBtn.addEventListener("click", async () => {
    summaryBox.style.display = "none";
    loadingEl.style.display = "block";
    loadingEl.textContent = "Generating summary…";

    try {
      const res = await fetchJson(`/api/groups/${groupId}/generate-summary`, {
        method: "POST",
      });

      summaryBox.textContent = res.summary;
      summaryBox.style.display = "block";

    } catch (err) {
      console.error("Summary error:", err);
      alert("Error generating summary: " + err.message);
    } finally {
      loadingEl.style.display = "none";
    }
  });
}

document.addEventListener("DOMContentLoaded", initGroupPage);
