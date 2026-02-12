const BASE_URL = "http://127.0.0.1:8000/api/accounts/";

function showSignup() {
  document.getElementById("loginForm").classList.add("hidden");
  document.getElementById("signupForm").classList.remove("hidden");
  document.getElementById("message").innerText = "";
}

function showLogin() {
  document.getElementById("signupForm").classList.add("hidden");
  document.getElementById("loginForm").classList.remove("hidden");
  document.getElementById("message").innerText = "";
}


// SIGNUP
async function signup(event) {
  event.preventDefault();

  const username = document.getElementById("loginUsername").value;

  const password = document.getElementById("signupPassword").value;

  try {
    const response = await fetch(BASE_URL + "signup/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        username: username,
        password: password,
      }),
    });

    const data = await response.json();

    if (response.ok) {
      document.getElementById("message").innerText =
        "Account created successfully 🎉 Please login.";
      showLogin();
    } else {
      document.getElementById("message").innerText =
        data.error || "Signup failed";
    }

  } catch (error) {
    document.getElementById("message").innerText =
      "Server error. Is backend running?";
  }
}


// LOGIN
async function login(event) {
  event.preventDefault();

  const username = document.getElementById("loginEmail").value;
  const password = document.getElementById("loginPassword").value;

  try {
    const response = await fetch(BASE_URL + "login/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        username: username,
        password: password,
      }),
    });

    const data = await response.json();

    if (response.ok) {
      // Save tokens
      localStorage.setItem("access_token", data.access);
      localStorage.setItem("refresh_token", data.refresh);

      // Redirect to index page
      window.location.href = "index.html";
    } else {
      document.getElementById("message").innerText =
        data.error || "Invalid credentials";
    }

  } catch (error) {
    document.getElementById("message").innerText =
      "Server error. Is backend running?";
  }
}
