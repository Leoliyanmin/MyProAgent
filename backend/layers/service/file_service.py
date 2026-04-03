from layers.business.file_logic import FileBusinessLogic


class FileService:
    def __init__(self):
        self.file_logic = FileBusinessLogic()

    def list_files(self, directory: str, pattern: str = None):
        files = self.file_logic.list_files(directory, pattern)
        return {'success': True, 'files': files}

    def batch_rename(self, files, pattern: str):
        results = self.file_logic.batch_rename_files(files, pattern)
        return {'success': True, 'results': results}

    def convert_format(self, file_path: str, target_format: str):
        result = self.file_logic.convert_file_format(file_path, target_format)
        return result
