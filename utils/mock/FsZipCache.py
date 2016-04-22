# based on
# http://stackoverflow.com/questions/2463770/python-in-memory-zip-library
# http://stackoverflow.com/questions/32910099/create-zip-file-object-from-bytestring-in-python

import zipfile
from io import BytesIO
from io import FileIO

import outputControl.logging_access
import utils.test_utils


class InMemoryZip(object):
    def __init__(self):
        # Create the in-memory file-like object
        self.in_memory_zip = BytesIO()

    def init(self):
        return zipfile.ZipFile(self.in_memory_zip, "a", zipfile.ZIP_DEFLATED, False)

    def append(self, filename):
        """Appends a file with name filename_in_zip and contents of
        file_contents to the in-memory zip."""
        # Get a handle to the in-memory zip in append mode
        zf = self.init()
        # Write the file to the in-memory zip
        zf.write(filename)
        return self

    def appendFiles(self, filenames):
        """List override of above for speedup"""
        zf = self.init()
        for file in filenames:
            try:
                zf.write(file)
            except BaseException:
                outputControl.logging_access.LoggingAccess().log("Skipped "+file)
        return self

    def read(self):
        """Returns contents of the in-memory zip."""
        self.in_memory_zip.seek(0)
        return self.in_memory_zip.read()

    def writetofile(self, filename):
        """Writes the in-memory zip to a file"""
        f = FileIO(filename, "w")
        f.write(self.read())
        f.close()

    def unpack(self):
        z = zipfile.ZipFile(self.in_memory_zip)
        z.extractall()


def createInMemoryArchive(dirs):
    xall = []
    for ldir in dirs:
        xall = xall + utils.test_utils.get_files(ldir, "", False)
    archive = InMemoryZip()
    archive.appendFiles(xall)
    return archive
