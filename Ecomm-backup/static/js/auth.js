document.addEventListener("DOMContentLoaded", function () {
  // Login Form Handler
  const loginForm = document.getElementById("login-form");
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const loginBtn = document.querySelector(".login-btn");
      const alertEl = document.getElementById("login-alert");

      // Show loading state
      if (loginBtn) {
        loginBtn.classList.add("loading");
        loginBtn.disabled = true;
      }

      alertEl.innerHTML = "";

      const data = {
        email: document.getElementById("email").value.trim(),
        password: document.getElementById("password").value,
      };

      try {
        const res = await fetch("/api/accounts/token/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data),
        });

        const json = await res.json();

        if (res.ok) {
          localStorage.setItem("access_token", json.access);
          localStorage.setItem("refresh_token", json.refresh);

          // Show success message
          alertEl.innerHTML = `
            <div class="alert alert-success alert-dismissible fade show" role="alert">
              <i class="fas fa-check-circle me-2"></i>Welcome back! Redirecting...
              <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>`;

          // Redirect after short delay
          setTimeout(() => {
            window.location.href = "/accounts/profile/";
          }, 1500);
        } else {
          const errMsg =
            json.detail || "Invalid email or password. Please try again.";
          alertEl.innerHTML = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
              <i class="fas fa-exclamation-triangle me-2"></i>${errMsg}
              <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>`;
        }
      } catch (err) {
        alertEl.innerHTML = `
          <div class="alert alert-danger alert-dismissible fade show" role="alert">
            <i class="fas fa-wifi me-2"></i>Connection error. Please try again.
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
          </div>`;
      } finally {
        // Hide loading state
        if (loginBtn) {
          loginBtn.classList.remove("loading");
          loginBtn.disabled = false;
        }
      }
    });
  }

  // Register Form Handler (for API registration if needed)
  const registerForm = document.getElementById("register-form");
  if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const alertEl = document.getElementById("register-alert");
      alertEl.innerHTML = "";

      const data = {
        username: document.getElementById("username").value.trim(),
        email: document.getElementById("email").value.trim(),
        password: document.getElementById("password").value,
        password2: document.getElementById("password2").value,
      };

      try {
        const res = await fetch("/api/accounts/register/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data),
        });

        const json = await res.json();

        if (res.ok) {
          alertEl.innerHTML = `
            <div class="alert alert-success">
              Account created successfully! <a href="/accounts/login/">Sign in here</a>
            </div>`;
          registerForm.reset();
        } else {
          const errHtml = Object.entries(json)
            .map(
              ([k, v]) =>
                `<div><strong>${k}:</strong> ${
                  Array.isArray(v) ? v.join(", ") : v
                }</div>`
            )
            .join("");
          alertEl.innerHTML = `<div class="alert alert-danger">${errHtml}</div>`;
        }
      } catch (err) {
        alertEl.innerHTML = `<div class="alert alert-danger">Network error. Try again.</div>`;
      }
    });
  }

  // Profile Page Handler
  const profileJson = document.getElementById("profile-json");
  if (profileJson) {
    (async () => {
      const token = localStorage.getItem("access_token");
      if (!token) {
        profileJson.innerHTML = `
          <div class="alert alert-warning">
            <i class="fas fa-exclamation-triangle me-2"></i>
            Not logged in. <a href="/accounts/login/">Please sign in</a>.
          </div>`;
        return;
      }

      try {
        const res = await fetch("/api/accounts/me/", {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (res.ok) {
          const user = await res.json();
          profileJson.innerHTML = `
            <div class="card">
              <div class="card-body">
                <h5 class="card-title"><i class="fas fa-user me-2"></i>Profile Information</h5>
                <p><strong>Username:</strong> ${user.username}</p>
                <p><strong>Email:</strong> ${user.email}</p>
                <p><strong>User ID:</strong> ${user.id}</p>
                <p><strong>Member since:</strong> ${new Date(
                  user.date_joined
                ).toLocaleDateString()}</p>
              </div>
            </div>`;
        } else {
          profileJson.innerHTML = `
            <div class="alert alert-danger">
              <i class="fas fa-exclamation-triangle me-2"></i>
              Token invalid or expired. <a href="/accounts/login/">Please sign in again</a>.
            </div>`;
        }
      } catch (err) {
        profileJson.innerHTML = `
          <div class="alert alert-danger">
            <i class="fas fa-wifi me-2"></i>
            Network error while fetching profile.
          </div>`;
      }
    })();
  }

  // Logout Button Handler
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      const refresh = localStorage.getItem("refresh_token");

      // Show loading state
      logoutBtn.disabled = true;
      logoutBtn.innerHTML = `
        <span class="spinner-border spinner-border-sm me-2" role="status"></span>
        Logging out...`;

      // Try server-side blacklist logout (optional)
      if (refresh) {
        try {
          await fetch("/api/accounts/logout/", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${localStorage.getItem("access_token")}`,
            },
            body: JSON.stringify({ refresh }),
          });
        } catch (err) {
          console.warn(
            "Server-side logout failed, continuing with client-side logout"
          );
        }
      }

      // Clear local storage
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");

      // Show success message briefly
      const alertContainer = document.createElement("div");
      alertContainer.innerHTML = `
        <div class="alert alert-success alert-dismissible fade show" role="alert">
          <i class="fas fa-check-circle me-2"></i>Logged out successfully!
        </div>`;

      // Insert at top of page
      document
        .querySelector(".container")
        .insertBefore(
          alertContainer,
          document.querySelector(".container").firstChild
        );

      // Redirect after short delay
      setTimeout(() => {
        window.location.href = "/accounts/login/";
      }, 1500);
    });
  }

  // Token Refresh Helper (optional - for auto-refresh)
  const refreshToken = async () => {
    const refresh = localStorage.getItem("refresh_token");
    if (!refresh) return false;

    try {
      const res = await fetch("/api/accounts/token/refresh/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh }),
      });

      if (res.ok) {
        const data = await res.json();
        localStorage.setItem("access_token", data.access);
        return true;
      }
    } catch (err) {
      console.warn("Token refresh failed");
    }

    return false;
  };

  // Auto-refresh token before it expires (optional)
  const scheduleTokenRefresh = () => {
    const token = localStorage.getItem("access_token");
    if (!token) return;

    try {
      // Decode JWT to get expiration (basic parsing)
      const payload = JSON.parse(atob(token.split(".")[1]));
      const expiresIn = payload.exp * 1000 - Date.now();

      // Refresh 5 minutes before expiration
      const refreshIn = Math.max(expiresIn - 300000, 60000);

      setTimeout(async () => {
        const success = await refreshToken();
        if (success) {
          console.log("Token refreshed successfully");
          scheduleTokenRefresh(); // Schedule next refresh
        }
      }, refreshIn);
    } catch (err) {
      console.warn("Failed to schedule token refresh");
    }
  };

  // Initialize token refresh scheduling
  scheduleTokenRefresh();
});
