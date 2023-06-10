import os
import smtplib
import logging
import urllib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import csv

import telebot
import config


def get_user_emails(user_id):
    user_emails = []
    user_id = str(user_id)  # Преобразование user_id в строку
    with open("user_emails.csv", newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == user_id:
                user_emails.append(row[1].strip())
    return user_emails


def send_file(message, document_name, user_id):
    bot = telebot.TeleBot(config.token, parse_mode=None)
    logger = logging.getLogger(__name__)

    user_emails = get_user_emails(user_id)
    if not user_emails:
        logger.warning("Emails not found for the user")
        bot.send_message(message.chat.id, 'Введите в чат ваш Amazon Email (в формате "/email_add user@kindle.com")')
        return

    archive_folder = os.path.join(os.path.dirname(__file__), "archive")
    filename = os.path.join(archive_folder, document_name)
    encoded_filename = urllib.parse.quote(document_name)

    logger.info(f"Filename: {filename}")

    if not os.path.isfile(filename):
        logger.warning("File for sending not found")
        return

    from_addr = config.login
    my_password = config.password

    logger.info(f"{filename} exists")
    with open(filename, "rb") as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename*=UTF-8''{encoded_filename}")

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(from_addr, my_password)

            for email_to_send in user_emails:
                msg = MIMEMultipart()
                msg['From'] = from_addr
                msg['To'] = str(email_to_send)
                msg['Subject'] = "Book"

                body = "SendToMyAmazonKindleBot \n\n"
                msg.attach(MIMEText(body, 'plain'))
                msg.attach(part)

                logger.info(f"Sending file to email: {email_to_send}")
                server.sendmail(from_addr, email_to_send, msg.as_string())

    logger.info("File was sent")
    bot.send_message(message.chat.id, f"Файл отправлен на {len(user_emails)} адрес(а/ов) электронной почты")