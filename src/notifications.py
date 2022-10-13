import smtplib, ssl

class Mail:

    def __init__(self, server, port, login, password):
        self.port = port
        self.smtp_server_domain_name = server
        self.sender_mail = login
        self.password = password

    def send(self, emails, subject, content):
        ssl_context = ssl.create_default_context()
        service = smtplib.SMTP_SSL(self.smtp_server_domain_name, self.port, context=ssl_context)
        service.login(self.sender_mail, self.password)
        
        for email in emails:
            result = service.sendmail(self.sender_mail, email, f"Subject: {subject}\n{content}")

        service.quit()