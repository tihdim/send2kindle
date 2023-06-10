#!/usr/bin/env python
import os
import subprocess
import sys
import time
import logging
from datetime import datetime
import csv

import telebot
import wget

import config
import take_file
import url_validation
from file_clear import file_clear
from zip_unpack import unpack

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(module)s - Line %(lineno)d - %(message)s',
    level=logging.INFO,
    filename='py_log.log'
)

logger = logging.getLogger(__name__)


def main():
    bot = telebot.TeleBot(config.token, parse_mode=None)

    file_formats = {'.DOC', '.DOCX', '.HTML', '.HTM', '.RTF',
                    '.PNG', '.BMP', '.EPUB', '.AZW', '.PDF', '.JPEG', '.JPG', '.GIF'}
    additional_file_formats = {'.FB2', '.FB2.ZIP', '.FB2.XML', '.SHTML'}

    # Определение имени файла CSV для хранения адресов электронной почты пользователей
    user_emails_file = "user_emails.csv"

    @bot.message_handler(commands=['start'])
    def welcome_start(message):
        user_id = message.from_user.id
        username = message.from_user.username
        current_time = datetime.now()

        # Отправляем приветственное сообщение
        bot.send_message(message.chat.id, f'Приветствую тебя, {username}')
        bot.send_message(message.chat.id, 'Для использования бота сделайте следующее:')
        text = '[ссылке](https://www.amazon.com/hz/mycd/myx#/home/settings/payment)'
        bot.send_message(message.chat.id, f'Перейдите в раздел Personal Document Settings по {text}',
                         parse_mode='MarkdownV2')
        bot.send_message(message.chat.id, 'Добавьте адрес sendtokindlebot@gmail.com в список разрешённых')
        bot.send_message(message.chat.id, 'Введите в чат ваш Amazon Email (в формате "/email_add user@kindle.com")')

        # Логирование информации
        logger.info(f"(0){current_time} (start) user_id: {user_id} by {username}")

    @bot.message_handler(commands=['email_add'])
    def email_add(message):
        current_time = datetime.now()
        username = message.from_user.username

        # Логирование информации о команде email_add
        logger.info(f"{current_time} (email_add) message_text: {message.text} by {username}")

        if str.lower(message.text).endswith('@kindle.com'):
            email = str.lower(message.text.rsplit(None, 1)[1])
            bot.send_message(message.chat.id, "Адрес сохранён. Теперь вы можете отправить боту файл или ссылку на него")

            user_id = message.from_user.id

            # Запись адреса электронной почты в файл CSV
            with open(user_emails_file, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([user_id, email])

            # Отправка списка адресов
            with open(user_emails_file, 'r') as file:
                reader = csv.reader(file)
                bot.send_message(message.chat.id, "Список адресов:")
                for row in reader:
                    if row[0] == str(user_id):
                        bot.send_message(message.chat.id, f"{row[1]}")
        else:
            bot.send_message(message.chat.id, 'Введите ваш email в формате "/email_add user@kindle.com"')

    @bot.message_handler(commands=['email_remove'])
    def email_remove(message):
        current_time = datetime.now()
        username = message.from_user.username

        # Логирование информации о команде email_remove
        logger.info(f"{current_time} (email remove) message_text: {message.text} by {username}")

        bot.send_message(message.chat.id, 'Все email адреса удалены')

        user_id = message.from_user.id
        user_emails = []

        if os.path.isfile(user_emails_file):
            # Чтение адресов электронной почты из файла CSV и удаление файла
            with open(user_emails_file, 'r') as file:
                reader = csv.reader(file)
                next(reader)  # Пропуск заголовков колонок

                for row in reader:
                    if row[0] != str(user_id):
                        user_emails.append(row)

            os.remove(user_emails_file)  # Удаление файла с адресами электронной почты

        if user_emails:
            # Создание нового файла CSV с оставшимися адресами электронной почты
            with open(user_emails_file, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['user_id', 'user_email'])
                writer.writerows(user_emails)

    @bot.message_handler(content_types=["text"])
    def content_text(message):
        user_id = message.from_user.id
        username = message.from_user.username
        text = message.text.strip()

        logger.info(f"Message: {text} by {username}")

        if url_validation.is_valid(text):
            process_url_message(message, user_id)
        else:
            if text.endswith("!") and str(user_id) == config.admin_id:
                execute_command(message)

            if text == "/restart" and str(user_id) == config.admin_id:
                logger.warning("Restart")
                bot.send_message(message.chat.id, f"Restart!")
                os.system("systemctl restart sendtokindle.service")

            if text.endswith(" load") and str(user_id) == config.admin_id:
                send_document(message)

    def execute_command(message):
        output = subprocess.check_output(message.text[:-1], shell=True)
        if output:
            os.system(message.text[:-1])
            bot.send_message(message.chat.id, output)

    def send_document(message):
        bot.send_document(message.chat.id, open(message.text[:-5], 'rb'))

    def process_url_message(message, user_id):
        bot.send_message(message.chat.id, "Ссылка на скачивание принята")
        document_name = wget.detect_filename(message.text)
        file_format = is_file_format(document_name, user_id, None)
        logger.info(f"File format: {file_format}")

        if file_format is None:
            handle_wrong_file_format(message, document_name)
        elif file_format is False:  # usual
            download_file(message, document_name)
            take_file.send_file(message, document_name, user_id)
            file_clear(document_name)
        elif file_format is True:  # additional
            download_file(message, document_name)
            document_name = convert_additional_format_to_epub(message, document_name)
            take_file.send_file(message, document_name, user_id)
            file_clear(document_name)

    def handle_wrong_file_format(message, document_name):
        logger.info(f"Wrong File Format {document_name} by {message.from_user.username}")
        bot.send_message(message.chat.id, f"Некорректный формат файла: {document_name}")

    def download_file(message, document_name):
        file_clear(document_name)
        wget.download(message.text, os.path.join("archive", document_name))
        logger.info(f"{datetime.now()} document_name + .file_ext: {document_name}")

    def convert_additional_format_to_epub(message, document_name):
        if document_name.lower().endswith(".shtml"):
            wget.download(message.text[:-5] + "fb2.zip", os.path.join("archive", document_name[:-5] + "fb2.zip"))
            document_name = document_name[:-5] + "fb2.zip"
        else:
            wget.download(message.text, os.path.join("archive", document_name))

        bot.send_message(message.chat.id, f"Файл {document_name} получен")
        bot.send_message(message.chat.id, "Файл fb2 конвертируется")

        if document_name.lower().endswith(".fb2.xml"):
            os.rename(os.path.join("archive", document_name), os.path.join("archive", document_name[:-4]))
            document_name = document_name[:-4]
        elif document_name.lower().endswith(".fb2.zip") or document_name.lower().endswith(".shtml"):
            unpack(document_name)
            document_name = document_name[:-4]

        logger.info(f"{datetime.now()} document_name= {document_name}\n")
        os.system(
            f"./fb2c -c configuration.toml convert --to epub {os.path.join('./archive', document_name)} ./archive &")
        return get_epub_file(message, document_name)

    def get_epub_file(message, document_name):
        timer = 0
        epub_file_path = os.path.join("./archive", document_name[:-4] + ".epub")
        logger.info(f"Checking for EPUB file: {epub_file_path}")

        while not (os.path.isfile(epub_file_path) or timer >= 30):
            sys.stdout.write("\r" + "Wait " + str(timer * 5) + "sec. ")
            time.sleep(5)
            sys.stdout.flush()
            timer += 1

            if timer >= 30:
                bot.send_message(message.chat.id, "Ошибка конвертации файла " + document_name)

            if os.path.isfile(epub_file_path):
                logger.info("EPUB file found")
                return document_name[:-4] + ".epub"
        return document_name[:-4] + ".epub"

    @bot.message_handler(content_types=["document"])
    def content_document(message):
        user_id = message.from_user.id
        username = message.from_user.username
        current_time = datetime.now()
        document_name = message.document.file_name

        logger.info(f"{current_time} (doc) message_text: {document_name} by {username}")

        if is_file_too_large(message, document_name):
            return

        is_file_format(document_name, user_id, message)

        file_clear(document_name)

    def is_file_too_large(message, document_name):
        if message.document.file_size > 20 * 1024 * 1024:
            bot.send_message(message.chat.id,
                             "Файл " + document_name + " слишком большой для Telegram API")
            logger.info(f"The file is very large for telegram api")
            return True
        return False

    def handle_file_format(document_name, message, user_id, is_additional):
        file_path = bot.get_file(message.document.file_id).file_path
        download_url = f'http://api.telegram.org/file/bot{config.token}/{file_path}'
        download_path = os.path.join("archive", document_name)

        wget.download(download_url, download_path)

        bot.send_message(message.chat.id, f"Файл {document_name} получен")

        if is_additional:
            bot.send_message(message.chat.id, "Файл fb2 конвертируется")
            if document_name.endswith(str.lower('.fb2.xml')):
                document_name = handle_fb2_xml(document_name)
            elif document_name.endswith(str.lower('.fb2.zip')):
                document_name = handle_fb2_zip(document_name)

            convert_to_epub(document_name)
            get_epub_file(message, document_name)
            document_name = document_name[:-4] + ".epub"

        take_file.send_file(message, document_name, user_id)
        file_clear(document_name)

    def is_file_format(document_name, user_id, message=None):
        logger.info("is_file_format")
        if message is None:
            for key in file_formats:
                if document_name.endswith(key) or document_name.endswith(key.lower()):
                    logger.info("Usual format")
                    return False
            for key in additional_file_formats:
                if document_name.endswith(key) or document_name.endswith(key.lower()):
                    logger.info("Additional format")
                    return True
        else:
            for key in file_formats:
                if document_name.endswith(key) or document_name.endswith(key.lower()):
                    logger.info("Usual format")
                    return handle_file_format(document_name, message, user_id, is_additional=False)
            for key in additional_file_formats:
                if document_name.endswith(key.lower()) and key == '.SHTML':
                    logger.info(f"Wrong File Format {document_name} by {message.from_user.username}")
                    handle_wrong_file_format(message, document_name)
                    return
                if document_name.endswith(key) or document_name.endswith(key.lower()):
                    logger.info("Additional format")
                    return handle_file_format(document_name, message, user_id, is_additional=True)
        logger.info(f"Invalid file format {document_name} by {message.from_user.username}")
        handle_wrong_file_format(message, document_name)
        return

    def handle_fb2_xml(document_name):
        logger.info("Handling .fb2.xml")
        os.rename(os.path.join("./archive", document_name), os.path.join("./archive", document_name[:-4]))
        document_name = document_name[:-4]
        return document_name

    def handle_fb2_zip(document_name):
        logger.info("Handling .fb2.zip")
        return unpack(document_name)

    def convert_to_epub(document_name):
        logger.info("Converting to EPUB")
        os.system('./fb2c -c configuration.toml convert --to epub "./archive/' + document_name + '" "./archive" &')
        return

    bot.infinity_polling()


if __name__ == '__main__':
    main()
