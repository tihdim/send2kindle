import os
import logging


def file_clear(unique_id):
    current_directory = os.path.dirname(os.path.abspath(__file__))
    archive_path = os.path.join(current_directory, "archive")

    # Удаляем расширение файла с помощью os.path.splitext()
    base_filename = os.path.splitext(unique_id)[0]
    file_extensions = [".epub", ".fb2", ".shtml"]

    logger = logging.getLogger(__name__)
    logger.info(f"File Clear Job start for: {unique_id}")

    for extension in file_extensions:
        file_path = os.path.join(archive_path, f"{base_filename}{extension}")
        if os.path.isfile(file_path):
            os.remove(file_path)
            logger.info(f"Removed file: {file_path}")

    archive_file = os.path.join(archive_path, unique_id)
    if os.path.isfile(archive_file):
        os.remove(archive_file)
        logger.info(f"Removed archive file: {archive_file}")

    logger.info("File Clear Job: Success")
