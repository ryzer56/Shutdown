from flask import (
    Flask, render_template_string,
    request, redirect, url_for, session, flash
)
from functools import wraps
from datetime import datetime
import os

# ----------------- CONFIG -----------------

app = Flask(__name__)
app.secret_key = "CHANGE_ME_TO_A_RANDOM_SECRET_KEY"  # change this!

# Login credentials (simple version)
ADMIN_USERNAME = "teacher"
ADMIN_PASSWORD = "lab123"   # change this!

# List of lab PCs
LAB_MACHINES = [
    {"name": "Lab-PC-01", "ip": "192.168.9.37"},
    {"name": "Lab-PC-02", "ip": "192.168.1.11"},
    {"name": "Lab-PC-03", "ip": "192.168.1.12"},
    {"name": "Lab-PC-04", "ip": "192.168.1.13"},
]

LOG_FILE = "lab_actions.log"

# -------------- HELPER FUNCTIONS ----------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def log_action(user, action, target):
    """Append action info to a log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] user={user} action={action} target={target}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)


def execute_command(ip, mode):
    """
    mode: 'shutdown' or 'restart'
    Uses Windows 'shutdown' command with remote machine.
    """
    if mode == "shutdown":
        cmd = f"shutdown /s /m \\\\{ip} /t 0 /f"
    elif mode == "restart":
        cmd = f"shutdown /r /m \\\\{ip} /t 0 /f"
    else:
        return

    # Actually run the command
    os.system(cmd)


# -------------- HTML TEMPLATE -------------

BASE_TEMPLATE = r"""
<!doctype html>
<html>
<head>
    <title>Lab Control Panel</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <style>
        body {
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: #0f172a;
            color: #e5e7eb;
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 960px;
            margin: 2rem auto;
            padding: 1.5rem;
            background: #020617;
            border-radius: 16px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.4);
        }
        h1 {
            margin-top: 0;
            font-size: 1.6rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: #f9fafb;
        }
        .subtitle {
            font-size: 0.9rem;
            color: #9ca3af;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
            font-size: 0.9rem;
        }
        th, td {
            padding: 0.7rem 0.5rem;
            text-align: left;
        }
        th {
            border-bottom: 1px solid #1f2933;
            color: #9ca3af;
        }
        tr:nth-child(even) {
            background: #020617;
        }
        tr:nth-child(odd) {
            background: #020617;
        }
        .badge {
            display: inline-block;
            padding: 0.15rem 0.5rem;
            border-radius: 999px;
            font-size: 0.7rem;
            background: #1e293b;
            color: #e5e7eb;
        }
        .btn {
            border: none;
            border-radius: 999px;
            padding: 0.4rem 0.9rem;
            font-size: 0.8rem;
            cursor: pointer;
            margin: 0.1rem;
            transition: transform 0.08s ease;
        }
        .btn:active {
            transform: scale(0.96);
        }
        .btn-small {
            padding: 0.25rem 0.7rem;
            font-size: 0.75rem;
        }
        .btn-shutdown {
            background: #b91c1c;
            color: white;
        }
        .btn-restart {
            background: #0f766e;
            color: white;
        }
        .btn-all {
            background: #2563eb;
            color: white;
        }
        .header-actions {
            display: flex;
            gap: 0.4rem;
        }
        .flash {
            margin-bottom: 0.6rem;
            padding: 0.5rem 0.8rem;
            border-radius: 999px;
            font-size: 0.8rem;
        }
        .flash-ok {
            background: rgba(22,163,74,0.12);
            color: #bbf7d0;
        }
        .flash-error {
            background: rgba(220,38,38,0.12);
            color: #fecaca;
        }
        .login-box {
            max-width: 420px;
            margin: 5rem auto;
            padding: 2rem 1.8rem;
            background: #020617;
            border-radius: 16px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.4);
        }
        .login-box h2 {
            margin-top: 0;
            margin-bottom: 0.3rem;
        }
        .login-box label {
            display: block;
            font-size: 0.8rem;
            margin-bottom: 0.25rem;
            color: #9ca3af;
        }
        .login-box input {
            width: 100%;
            padding: 0.55rem 0.6rem;
            border-radius: 999px;
            border: 1px solid #1f2937;
            background: #020617;
            color: #e5e7eb;
            margin-bottom: 0.7rem;
            font-size: 0.85rem;
        }
        .login-box button {
            width: 100%;
            padding: 0.6rem;
            border-radius: 999px;
            border: none;
            background: #2563eb;
            color: white;
            font-size: 0.9rem;
            cursor: pointer;
        }
        .top-right {
            font-size: 0.75rem;
            color: #9ca3af;
        }
        .top-right a {
            color: #f97316;
            text-decoration: none;
        }
        @media (max-width: 600px) {
            .container {
                margin: 1rem;
                padding: 1rem;
            }
            h1 {
                flex-direction: column;
                align-items: flex-start;
                gap: 0.4rem;
            }
            .header-actions {
                width: 100%;
                flex-wrap: wrap;
            }
        }
    </style>
</head>
<body>

{% if page == "login" %}
    <div class="login-box">
        <h2>Lab Control Login</h2>
        <p class="subtitle">Admin / Teacher access only</p>

        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, msg in messages %}
              <div class="flash {{ 'flash-error' if category == 'error' else 'flash-ok' }}">{{ msg }}</div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        <form method="post">
            <label>Username</label>
            <input type="text" name="username" autocomplete="off">

            <label>Password</label>
            <input type="password" name="password">

            <button type="submit">Login</button>
        </form>
    </div>

{% else %}

    <div class="container">
        <h1>
            <span>Lab Control Panel</span>
            <span class="top-right">
                Logged in as: <b>{{ user }}</b> &nbsp;•&nbsp;
                <a href="{{ url_for('logout') }}">Logout</a>
            </span>
        </h1>
        <p class="subtitle">
            Control all lab systems from one dashboard. Use responsibly. Actions apply instantly.
        </p>

        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, msg in messages %}
              <div class="flash {{ 'flash-error' if category == 'error' else 'flash-ok' }}">{{ msg }}</div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        <div class="header-actions">
            <form method="post" action="{{ url_for('do_action') }}">
                <input type="hidden" name="action" value="shutdown_all">
                <button class="btn btn-all" type="submit"
                        onclick="return confirm('Shutdown ALL lab machines? This cannot be undone.')">
                    Shutdown ALL
                </button>
            </form>
            <form method="post" action="{{ url_for('do_action') }}">
                <input type="hidden" name="action" value="restart_all">
                <button class="btn btn-restart" type="submit"
                        onclick="return confirm('Restart ALL lab machines?')">
                    Restart ALL
                </button>
            </form>
        </div>

        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>PC Name</th>
                    <th>IP Address</th>
                    <th>Controls</th>
                </tr>
            </thead>
            <tbody>
            {% for m in machines %}
                <tr>
                    <td>{{ loop.index }}</td>
                    <td>{{ m.name }}</td>
                    <td><span class="badge">{{ m.ip }}</span></td>
                    <td>
                        <form method="post" action="{{ url_for('do_action') }}" style="display:inline;">
                            <input type="hidden" name="action" value="shutdown_one">
                            <input type="hidden" name="ip" value="{{ m.ip }}">
                            <input type="hidden" name="name" value="{{ m.name }}">
                            <button class="btn btn-shutdown btn-small" type="submit"
                                    onclick="return confirm('Shutdown {{ m.name }} ?')">
                                Shutdown
                            </button>
                        </form>
                        <form method="post" action="{{ url_for('do_action') }}" style="display:inline;">
                            <input type="hidden" name="action" value="restart_one">
                            <input type="hidden" name="ip" value="{{ m.ip }}">
                            <input type="hidden" name="name" value="{{ m.name }}">
                            <button class="btn btn-restart btn-small" type="submit"
                                    onclick="return confirm('Restart {{ m.name }} ?')">
                                Restart
                            </button>
                        </form>
                    </td>
                </tr>
            {% endfor %}
            </tbody>
        </table>

        <p class="subtitle" style="margin-top:1rem;">
            Actions are logged in <code>{{ log_file }}</code> on this machine.
        </p>
    </div>

{% endif %}

</body>
</html>
"""

# -------------- ROUTES --------------------


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username", "").strip()
        p = request.form.get("password", "")

        if u == ADMIN_USERNAME and p == ADMIN_PASSWORD:
            session["user"] = u
            flash("Login successful.", "ok")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password.", "error")

    return render_template_string(BASE_TEMPLATE, page="login")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "ok")
    return redirect(url_for("login"))


@app.route("/")
@login_required
def dashboard():
    return render_template_string(
        BASE_TEMPLATE,
        page="dashboard",
        machines=LAB_MACHINES,
        user=session.get("user", "unknown"),
        log_file=LOG_FILE
    )


@app.route("/do_action", methods=["POST"])
@login_required
def do_action():
    action = request.form.get("action")
    user = session.get("user", "unknown")

    if action == "shutdown_all":
        for m in LAB_MACHINES:
            execute_command(m["ip"], "shutdown")
        log_action(user, "shutdown_all", "ALL")
        flash("Shutdown command sent to ALL machines.", "ok")

    elif action == "restart_all":
        for m in LAB_MACHINES:
            execute_command(m["ip"], "restart")
        log_action(user, "restart_all", "ALL")
        flash("Restart command sent to ALL machines.", "ok")

    elif action == "shutdown_one":
        ip = request.form.get("ip")
        name = request.form.get("name", ip)
        execute_command(ip, "shutdown")
        log_action(user, "shutdown_one", f"{name} ({ip})")
        flash(f"Shutdown command sent to {name}.", "ok")

    elif action == "restart_one":
        ip = request.form.get("ip")
        name = request.form.get("name", ip)
        execute_command(ip, "restart")
        log_action(user, "restart_one", f"{name} ({ip})")
        flash(f"Restart command sent to {name}.", "ok")

    else:
        flash("Unknown action.", "error")

    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    # host=0.0.0.0 allows access from phone on same network
    app.run(host="0.0.0.0", port=5000, debug=False)
