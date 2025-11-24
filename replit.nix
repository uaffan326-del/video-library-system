run = "python web_ui.py"
modules = ["python-3.11"]

[nix]
channel = "stable-24_05"

[deployment]
run = ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT web_ui:app"]
deploymentTarget = "cloudrun"

[[ports]]
localPort = 5000
externalPort = 80
