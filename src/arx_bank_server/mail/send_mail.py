import aiosmtplib
from email.message import EmailMessage
from arx_bank_server.setup import settings, logger

login_html = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Login Notification</title>
    <style>
      body {
        font-family: Arial, sans-serif;
        background-color: #f4f4f4;
        margin: 0;
        padding: 0;
        color: #333;
      }
      .email-container {
        width: 100%;
        max-width: 600px;
        margin: 20px auto;
        background-color: #ffffff;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
      }
      .email-header {
        text-align: center;
        padding-bottom: 20px;
      }
      .email-header img {
        width: 150px; /* Adjust logo size as necessary */
        height: auto;
      }
      .email-header h2 {
        color: #4caf50;
      }
      .email-content {
        font-size: 16px;
        line-height: 1.6;
        color: #555;
      }
      .email-footer {
        font-size: 14px;
        color: #888;
        text-align: center;
        padding-top: 20px;
      }
      a {
        color: #4caf50;
        text-decoration: none;
      }
    </style>
  </head>
  <body>
    <div class="email-container">
      <div class="email-header">
        <h2>Login Notification</h2>
      </div>
      <div class="email-content">
        <p>Dear %NAME%,</p>
        <p>
          We wanted to let you know that your account was successfully logged in
          to at %DATE%.
        </p>
        <p>If this was you, you can safely ignore this message.</p>
        <p>Thank you for using ARX!</p>
      </div>
      <div class="email-footer">
        <p>&copy; 2024 ARX. All Rights Reserved.</p>
      </div>
    </div>
  </body>
</html>
"""

register_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Registration Confirmation</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
            color: #333;
        }
        .email-container {
            width: 100%;
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        .email-header {
            text-align: center;
            padding-bottom: 20px;
        }
        .email-header img {
            width: 150px; /* Adjust logo size as necessary */
            height: auto;
        }
        .email-header h2 {
            color: #4CAF50;
        }
        .email-content {
            font-size: 16px;
            line-height: 1.6;
            color: #555;
        }
        .email-footer {
            font-size: 14px;
            color: #888;
            text-align: center;
            padding-top: 20px;
        }
        a {
            color: #4CAF50;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="email-container">
        <div class="email-header">
            <h2>Welcome to ARX!</h2>
        </div>
        <div class="email-content">
            <p>Dear %NAME%,</p>
            <p>Thank you for registering with ARX! We're excited to have you onboard.</p>
            <p>Your registration was successful, and your account is now active. You can now access all the features available to you.</p>
            <p>If you have any questions or need help getting started, feel free to reach out to us.</p>
            <p>Thank you for choosing ARX!</p>
        </div>
        <div class="email-footer">
            <p>&copy; 2024 ARX. All Rights Reserved.</p>
        </div>
    </div>
</body>
</html>
"""


async def send_register_email(to: str, name: str) -> bool:
    subject = "Welcome to ARX!"
    body = register_html.replace("%NAME%", name)
    email = create_email(to, subject, body)
    return await send_email(email)


async def send_login_email(to: str, name: str, date: str) -> bool:
    subject = "Login Notification"
    body = login_html.replace("%NAME%", name).replace("%DATE%", date)
    email = create_email(to, subject, body)
    return await send_email(email)


def create_email(to: str, subject: str, body: str) -> EmailMessage:
    email = EmailMessage()
    email["From"] = settings.SMTP_USER
    email["To"] = to
    email["Subject"] = subject
    email.set_content(body, subtype="html")
    return email


async def send_email(email: EmailMessage):
    try:
        response = await aiosmtplib.send(
            email,
            sender="contact@stuckinaloop.ro",
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            use_tls=True,
        )
        logger.info(response)
        return True
    except Exception as e:
        logger.error(e)
        return False
