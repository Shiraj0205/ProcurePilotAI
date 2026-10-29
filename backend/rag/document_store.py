import os
import shutil
from collections.abc import Iterator
from config.settings import settings
from exceptions import LLMNotConfiguredException


def location() -> str:
    """Get the local vector store path based on the settings."""
    if settings.app_mode == "local":
        return settings.local_upload_dir
    else:
        raise LLMNotConfiguredException("Local vector store path is only available in local mode.")


def save(file_path: str, filename: str) -> str:
    """Save the uploaded file to the local upload directory. Return the path to the saved file."""
    filename = os.path.basename(filename)

    if settings.app_mode != "local":
        raise LLMNotConfiguredException("File upload is only available in local mode.")

    os.makedirs(settings.local_upload_dir, exist_ok=True)
    stored_at = os.path.join(settings.local_upload_dir, filename)
    shutil.copyfile(file_path, stored_at)
    return stored_at


def pdfs() -> Iterator[Iterator[tuple[str, str]]]:
    """Yield (local_path, source) for every stored PDF.

    Used as a context manager because cloud files are downloaded to a temp folder
    that must be cleaned up afterwards.
    """
    if not settings.is_cloud:
        folder = settings.local_upload_dir
        os.makedirs(folder, exist_ok=True)
        yield (
            (os.path.join(folder, name), f"local://{name}")
            for name in sorted(os.listdir(folder))
            if name.lower().endswith(".pdf")
        )
        return
    