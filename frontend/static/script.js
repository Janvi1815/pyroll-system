const API = "http://127.0.0.1:5000";

function signup() {
  fetch(API + "/signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username: document.getElementById("susername").value,
      password: document.getElementById("spassword").value,
      role: document.getElementById("srole").value
    })
  }).then(r => r.json()).then(d => {
    alert(JSON.stringify(d));
    if (d.msg && d.msg.includes("Signup success")) {
      showLogin();
      document.getElementById("loginBtn").classList.add("active");
      document.getElementById("signupBtn").classList.remove("active");
    }
  });
}

function login() {
  fetch(API + "/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username: document.getElementById("username").value,
      password: document.getElementById("password").value,
      role: document.getElementById("lrole").value   // 👈 role bhi send kare chhe
    })
  }).then(r => r.json()).then(d => {
    if (d.token) {
      localStorage.setItem("token", d.token);
      localStorage.setItem("role", d.role);
      localStorage.setItem("username", document.getElementById("username").value);
      window.location = "/dashboard";
    } else {
      alert(d.error || "Invalid login");
    }
  });
}

function logout() {
  localStorage.clear();
  window.location = "/";
}

// -------- Dashboard Loading --------
function initDashboard() {
  const role = localStorage.getItem("role");
  const user = localStorage.getItem("username");
  if (!role) { window.location = "/"; return; }

  if (role === "employee") {
    document.getElementById("dashboard-content").innerHTML = `
      <h3>Submit Expense</h3>
      <input id="expTitle" placeholder="Title"><br>
      <input id="expAmt" placeholder="Amount"><br>
      <button onclick="submitExpense()">Add Expense</button>
      <h3>Your Expenses</h3>
      <div id="expenses"></div>
      <div class="chart-container"><canvas id="expenseChart"></canvas></div>
      <h3>Your Salary Slips</h3>
      <div id="slips"></div>
      <div class="chart-container"><canvas id="salaryChart"></canvas></div>
    `;
    loadExpenses();
    loadSlips(user);
  } else {
    document.getElementById("dashboard-content").innerHTML = `
      <h3>Create Salary Slip</h3>
      <input id="empName" placeholder="Employee"><br>
      <input id="month" placeholder="Month"><br>
      <input id="salary" placeholder="Salary"><br>
      <button onclick="createSlip()">Save Slip</button>
      <h3>View Employee Slips</h3>
      <input id="viewEmp" placeholder="Employee Username"><br>
      <button onclick="adminViewSlips()">Load Slips</button>
      <div id="empSlips"></div>
      <div class="chart-container"><canvas id="adminSalaryChart"></canvas></div>
    `;
  }
}

// -------- Expenses --------
function submitExpense() {
  fetch(API + "/expenses", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": "Bearer " + localStorage.getItem("token")
    },
    body: JSON.stringify({
      title: document.getElementById("expTitle").value,
      amount: document.getElementById("expAmt").value
    })
  }).then(r => r.json()).then(d => {
    alert(d.msg);
    loadExpenses();
  });
}

function loadExpenses() {
  fetch(API + "/expenses", {
    headers: { "Authorization": "Bearer " + localStorage.getItem("token") }
  }).then(r => r.json()).then(data => {
    let html = "<table><tr><th>Title</th><th>Amount</th></tr>";
    let labels = [], values = [];
    data.forEach(e => {
      html += `<tr><td>${e.title}</td><td>${e.amount}</td></tr>`;
      labels.push(e.title);
      values.push(e.amount);
    });
    html += "</table>";
    document.getElementById("expenses").innerHTML = html;
    renderExpenseChart(labels, values);
  });
}

// -------- Salary Slips --------
function createSlip() {
  fetch(API + "/slips", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": "Bearer " + localStorage.getItem("token")
    },
    body: JSON.stringify({
      employee: document.getElementById("empName").value,
      month: document.getElementById("month").value,
      salary: document.getElementById("salary").value
    })
  }).then(r => r.json()).then(d => alert(d.msg));
}

function loadSlips(user) {
  fetch(API + "/slips/" + user, {
    headers: { "Authorization": "Bearer " + localStorage.getItem("token") }
  }).then(r => r.json()).then(data => {
    let html = "<table><tr><th>Month</th><th>Salary</th></tr>";
    let labels = [], values = [];
    data.forEach(s => {
      html += `<tr><td>${s.month}</td><td>${s.salary}</td></tr>`;
      labels.push(s.month);
      values.push(s.salary);
    });
    html += "</table>";
    document.getElementById("slips").innerHTML = html;
    renderSalaryChart(labels, values, "salaryChart");
  });
}

function adminViewSlips() {
  const emp = document.getElementById("viewEmp").value;
  fetch(API + "/slips/" + emp, {
    headers: { "Authorization": "Bearer " + localStorage.getItem("token") }
  }).then(r => r.json()).then(data => {
    let html = "<table><tr><th>Month</th><th>Salary</th></tr>";
    let labels = [], values = [];
    data.forEach(s => {
      html += `<tr><td>${s.month}</td><td>${s.salary}</td></tr>`;
      labels.push(s.month);
      values.push(s.salary);
    });
    html += "</table>";
    document.getElementById("empSlips").innerHTML = html;
    renderSalaryChart(labels, values, "adminSalaryChart");
  });
}

// -------- UI Toggle (Login / Signup) --------
function showLogin() {
  document.getElementById("loginForm").style.display = "block";
  document.getElementById("signupForm").style.display = "none";
}

function showSignup() {
  document.getElementById("loginForm").style.display = "none";
  document.getElementById("signupForm").style.display = "block";
}

// -------- Chart.js Rendering --------
function renderExpenseChart(labels, values) {
  if (!document.getElementById("expenseChart")) return;

  new Chart(document.getElementById("expenseChart"), {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: "Expenses",
        data: values,
        backgroundColor: "rgba(102,126,234,0.8)",
        borderRadius: 10,
        borderSkipped: false,
        hoverBackgroundColor: "rgba(102,126,234,1)"
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: true, position: "top" } },
      scales: { y: { beginAtZero: true } }
    }
  });
}

function renderSalaryChart(labels, values, canvasId) {
  if (!document.getElementById(canvasId)) return;

  new Chart(document.getElementById(canvasId), {
    type: "line",
    data: {
      labels: labels,
      datasets: [{
        label: "Salary",
        data: values,
        borderColor: "rgba(118,75,162,1)",
        backgroundColor: "rgba(118,75,162,0.2)",
        fill: true,
        tension: 0.4,
        pointBackgroundColor: "#764ba2",
        pointRadius: 5
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: true, position: "top" } },
      scales: { y: { beginAtZero: true } }
    }
  });
}

// -------- Form Reset on Refresh --------
window.addEventListener("pageshow", function () {
  // Clear login form
  if (document.getElementById("loginForm")) {
    document.getElementById("username").value = "";
    document.getElementById("password").value = "";
    if (document.getElementById("lrole")) {
      document.getElementById("lrole").selectedIndex = 0;
    }
  }

  // Clear signup form
  if (document.getElementById("signupForm")) {
    document.getElementById("susername").value = "";
    document.getElementById("spassword").value = "";
    if (document.getElementById("srole")) {
      document.getElementById("srole").selectedIndex = 0;
    }
  }

  // Dashboard init
  if (window.location.pathname.includes("dashboard")) {
    initDashboard();
  }
});
