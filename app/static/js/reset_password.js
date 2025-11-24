// /static/js/reset_password.js

document.addEventListener("DOMContentLoaded", () => {
  const supabase = window.supabaseClient;
  const statusText = document.getElementById("status-text");
  const form = document.getElementById("reset-form");
  const newPwInput = document.getElementById("new-password");
  const confirmPwInput = document.getElementById("confirm-password");

  if (!supabase) {
    console.error("Supabase client missing on window");
    statusText.textContent =
      "Internal error: Supabase client not available. Contact support.";
    return;
  }

  // Listen for PASSWORD_RECOVERY event once the user hits this page
  supabase.auth.onAuthStateChange(async (event, session) => {
    console.log("Auth event:", event, session);

    if (event === "PASSWORD_RECOVERY") {
      statusText.textContent = "Enter your new password below.";
      form.style.display = "flex";
    } else if (event === "SIGNED_IN" && session) {
      // Sometimes reset flow emits SIGNED_IN as well; still fine
      statusText.textContent = "Enter your new password below.";
      form.style.display = "flex";
    }
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const newPassword = newPwInput.value.trim();
    const confirmPassword = confirmPwInput.value.trim();

    if (newPassword.length < 8) {
      statusText.textContent = "Password must be at least 8 characters.";
      return;
    }

    if (newPassword !== confirmPassword) {
      statusText.textContent = "Passwords do not match.";
      return;
    }

    statusText.textContent = "Updating password...";

    const { data, error } = await supabase.auth.updateUser({
      password: newPassword,
    });

    if (error) {
      console.error("Error updating password:", error);
      statusText.textContent = "Error updating password: " + error.message;
      return;
    }

    statusText.textContent = "Password updated! You can now log in.";
    form.reset();
  });
});
