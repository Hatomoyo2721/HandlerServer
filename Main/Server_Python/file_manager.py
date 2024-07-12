import json
import logging
import mimetypes
import pathlib
import socket


class FileManager:
    USERS_DIR = pathlib.Path(__file__).resolve().parent / 'users_directories'

    def __init__(self, user_manager):
        self.user_manager = user_manager

    def load_directory(self, s: socket.socket):
        try:
            raw_data = self.user_manager.endpoint_manager.readUTF(s)
            if not raw_data:
                return self.user_manager.endpoint_manager.writeUTF(s, json.dumps({"error": "Missing data"}))

            username = raw_data.strip()  # Remove ' ' or " "
            if not username:
                return self.user_manager.endpoint_manager.writeUTF(s, json.dumps({"error": "Missing username"}))
            
            user_dir = self.USERS_DIR / username
            try:
                if user_dir.exists() and user_dir.is_dir():
                    files_and_dirs = []
                    for entry in user_dir.iterdir():
                        if entry.is_file():
                            file_type = self.get_file_type(entry)
                            files_and_dirs.append({
                                "name": entry.name,
                                "type": file_type,
                                "path": str(entry.resolve())
                            })
                        elif entry.is_dir():
                            files_and_dirs.append({
                                "name": entry.name,
                                "type": "directory",
                                "path": str(entry.resolve())
                            })

                    response = json.dumps(files_and_dirs)
                    self.user_manager.endpoint_manager.writeUTF(s, response)
                else:
                    self.user_manager.endpoint_manager.writeUTF(s, "ERROR: Directory not found")
            except Exception as e:
                logging.error(f"Error loading directory: {e}\n")
                self.user_manager.endpoint_manager.writeUTF(s, f"ERROR: {e}")
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON data from client: {e.msg}\n")
            self.user_manager.endpoint_manager.writeUTF(s, f"ERROR: Invalid JSON format {e.msg}")

    def get_file_type(self, file_path):
        file_extension = file_path.suffix.lower()
        mime_type, _ = mimetypes.guess_type(file_path)
        return self.determine_file_type(file_extension, mime_type)

    def determine_file_type(self, file_extension, mime_type):
        if file_extension in FileManager.FILE_TYPES:
            return FileManager.FILE_TYPES[file_extension]
        elif mime_type is not None and mime_type.startswith('text'):
            return "text file"
        elif mime_type is not None and mime_type.startswith('image'):
            return "image"
        elif mime_type is not None and mime_type.startswith('video'):
            return "video file"
        elif mime_type is not None and mime_type.startswith('application/pdf'):
            return "document file"
        else:
            return "other file"

    FILE_TYPES = {
        ".txt": "text file",
        ".jpg": "image",
        ".jpeg": "image",
        ".png": "image",
        ".mp4": "video file",
        ".avi": "video file",
        ".mov": "video file",
        ".java": "code file",
        ".py": "code file",
        ".cpp": "code file",
        ".html": "web file",
        ".pdf": "document file",
        ".docx": "document file"
    }