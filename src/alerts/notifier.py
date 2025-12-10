from smtplib import SMTP
from email.mime.text import MIMEText
import logging

class Notifier:
    def __init__(self, smtp_server, smtp_port, sender_email, recipient_email):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.recipient_email = recipient_email
        self.logger = logging.getLogger(__name__)

    def send_alert(self, subject, message):
        try:
            msg = MIMEText(message)
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email

            with SMTP(self.smtp_server, self.smtp_port) as server:
                server.sendmail(self.sender_email, self.recipient_email, msg.as_string())
            self.logger.info("Alert sent successfully.")
        except Exception as e:
            self.logger.error(f"Failed to send alert: {e}")