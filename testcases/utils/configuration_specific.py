class DocumentationProcessing(BaseException):
    pass


class JdkConfiguration():
    pass

    def __init__(self):
        self.documenting = False

    def _document(self, message):
        """Documentation used to generate specification-specific lines"""
        if self.documenting:
            raise DocumentationProcessing(message)
