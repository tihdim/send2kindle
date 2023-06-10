import os
import logging
import shutil
from datetime import datetime
import zipfile


def unpack(unique_id):
    # Создание логгера для модуля
    logger = logging.getLogger(__name__)

    # Проверка и создание директорий при необходимости
    os.makedirs('./zip_archive', exist_ok=True)
    os.makedirs('./archive', exist_ok=True)

    zip_file_path = os.path.join("./archive", unique_id)
    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zip_file:
            zip_file.extractall('zip_archive')
            file_names = zip_file.namelist()

        if os.path.isfile(zip_file_path):
            logger.info(f"{datetime.now()} (remove zip) unique_id: archive/{unique_id}")
            os.remove(zip_file_path)

        if file_names:
            unique_id_new = file_names[-1]
            base_name, _ = os.path.splitext(unique_id_new)  # Получение базового имени файла без расширения
            logger.info(f"unique_id_new = {base_name}, unique_id = {unique_id}")
            shutil.move(os.path.join("./zip_archive", unique_id_new), os.path.join("./archive", base_name + ".fb2"))
            return unique_id_new
    except (zipfile.BadZipFile, FileNotFoundError) as e:
        logger.error(f"Error occurred: {e}")
    except Exception as e:
        logger.exception("An error occurred")

