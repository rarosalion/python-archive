import os
import sys
import tarfile
import zipfile
import bz2
import gzip
import py7zr


"""
Present a list of readable files from an
archive or compressed file
"""

def files_in_bundle(file):

    try:
        a = Archive(file)
        for sub_file in a.filenames():
            yield (sub_file, a.read_file(sub_file))
        return
    except ArchiveException as e:
        pass

    try:
        f = CompressedFile(file)
        yield (file, f)
        return
    except CompressionException as e:
        pass


"""
Classes to read files of various compression types
A File should be an individual file, not an archive that 
can contain multiple sub-files
"""

class CompressionException(Exception):
    """ Base exception class for all compression errors. """

class UnrecognizedCompressionFormat(CompressionException):
    """ Contents do not match any known compression type """
    
class CompressedFile(object):

    """
    The external API class that encapsulates an file implementation.
    """

    def __new__(self, file):
        """
        Arguments:
        * 'file' can be a string path to a file or a file-like object.
        """
        # Check known archive types
        for subclass in CompressedFile.__subclasses__():
            if subclass.is_compressed(file):
                return super().__new__(subclass)
        else:
            raise UnrecognizedCompressionFormat()

    def __init__(self, file):
        if isinstance(file, str):
            self._file = self._open(file, 'rb')
        else:
            self._file = file

    @classmethod
    def is_compressed(cls, file):
        if isinstance(file, str):
            f = open(file, 'rb')
        else:
            f = file

        try:
            header = f.read(len(cls.MAGIC_BYTES))
            return header == cls.MAGIC_BYTES
        except NameError:
            # Sub-classes must implement the MAGIC_BYTES value, or re-implement this method
            raise NotImplementedError()

    def _open(self, *args, **kwargs):
        raise NotImplementedError()
    
    def read(self, *args, **kwargs):
        return self._file.read(*args, **kwargs)


class BzFile(CompressedFile):
    MAGIC_BYTES = b'BZh'

    def _open(self, filename, mode='r'):
        self._file = bz2.BZ2File(filename, mode)
        return self._file


class GzFile(CompressedFile):
    MAGIC_BYTES = b'\x1f\x8b'

    def _open(self, filename, mode='r'):
        self._file = gzip.GzipFile(filename, mode)
        return self._file


"""
Classes to implement archives.
An archive should have multiple files within it.
"""

class ArchiveException(Exception):
    """Base exception class for all archive errors."""


class UnrecognizedArchiveFormat(ArchiveException):
    """Error raised when passed file is not a recognized archive format."""


class UnsafeArchive(ArchiveException):
    """
    Error raised when passed file contains paths that would be extracted
    outside of the target directory.
    """

class Archive(object):
    """
    The external API class that encapsulates an archive implementation.
    """

    def __new__(self, file):
        """
        Arguments:
        * 'file' can be a string path to a file or a file-like object.
        """
        # Check known archive types
        for subclass in Archive.__subclasses__():
            if subclass.is_archive(file):
                return super().__new__(subclass)
        else:
            raise UnrecognizedArchiveFormat("File object is not recognised by available archive libraries")

    def _extract(self, to_path):
        """
        Performs the actual extraction.  Separate from 'extract' method so that
        we don't recurse when subclasses don't declare their own 'extract'
        method.
        """
        self._archive.extractall(to_path)

    def extract(self, to_path='', method='safe'):
        if method == 'safe':
            self.check_files(to_path)
        elif method == 'insecure':
            pass
        else:
            raise ValueError("Invalid method option")
        self._extract(to_path)

    def check_files(self, to_path=None):
        """
        Check that all of the files contained in the archive are within the
        target directory.
        """
        if to_path:
            target_path = os.path.normpath(os.path.realpath(to_path))
        else:
            target_path = os.getcwd()
        for filename in self.filenames():
            extract_path = os.path.join(target_path, filename)
            extract_path = os.path.normpath(os.path.realpath(extract_path))
            if not extract_path.startswith(target_path):
                raise UnsafeArchive(
                    "Archive member destination is outside the target"
                    " directory.  member: %s" % filename)

    """
    Methods below must be implemented in the subclass
    """
    @staticmethod
    def is_archive(name):
        raise NotImplementedError()

    def list(self):
        raise NotImplementedError()

    def filenames(self):
        raise NotImplementedError()

    def read_file(self, name):
        raise NotImplementedError()



class TarArchive(Archive):

    def __init__(self, file):
        # tarfile's open uses different parameters for file path vs. file obj.
        if isinstance(file, str):
            self._archive = tarfile.open(name=file)
        else:
            self._archive = tarfile.open(fileobj=file)

    @staticmethod
    def is_archive(name):
        return tarfile.is_tarfile(name)

    def list(self, *args, **kwargs):
        self._archive.list(*args, **kwargs)

    def filenames(self):
        return self._archive.getnames()
    
    def read_file(self, name):
        return self._archive.extractfile(name)


class ZipArchive(Archive):

    def __init__(self, file):
        # ZipFile's 'file' parameter can be path (string) or file-like obj.
        self._archive = zipfile.ZipFile(file)

    @staticmethod
    def is_archive(name):
        return zipfile.is_zipfile(name)

    def list(self, *args, **kwargs):
        self._archive.printdir(*args, **kwargs)

    def filenames(self):
        return self._archive.namelist()
    
    def read_file(self, name):
        return self._archive.open(name)


class SevenZipArchive(Archive):

    def __init__(self, file):
        # SevenZip's 'file' parameter can be path (string) or file-like obj.
        self._archive = py7zr.SevenZipFile(file)

    @staticmethod
    def is_archive(name):
        return zipfile.is_zipfile(name)

    def list(self, *args, **kwargs):
        self._archive.printdir(*args, **kwargs)

    def filenames(self):
        return self._archive.namelist()
    
    def read_file(self, name):
        return self._archive.open(name)
