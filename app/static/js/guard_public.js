// /static/js/guard_public.js

const path = window.location.pathname.toLowerCase();
const hash = window.location.hash || "";

// 1) If we just arrived from a Supabase recovery email,
// Supabase dumps us on "/" with a hash like:
//   #access_token=...&type=recovery&...
// Detect that and MOVE to /auth/reset while keeping the hash.
if (path === "/" && hash.includes("type=recovery")) {
  console.log("guard_public: detected recovery link on '/', redirecting to /auth/reset");
  // Use replace so back button doesn't go back to "/" and loop
  window.location.replace("/auth/reset" + hash);
  // Stop here – don't check session or anything else
  throw new Error("redirecting to /auth/reset"); // just hard-stop this script (optional)
}

// 2) If we're already on a reset page, do NOT redirect to dashboard.
if (path.includes("reset")) {
  console.log("guard_public: on reset page, not redirecting");
  return;
}

// 3) Normal behavior: on other public pages, if logged in, go to dashboard
const { data } = await window.sb.auth.getSession();

if (data?.session) {
  console.log("guard_public: logged in on public page, redirecting to /dashboard");
  window.location.href = "/dashboard";
} else {
  console.log("guard_public: no session, staying on public page:", path);
}
