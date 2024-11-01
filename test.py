from archive import *

for file_name in [
  # Archives
  'tests/files/test_content.tar.gz',
  'tests/files/test_content.zip',
  # Files
  'tests/files/temp_test_txt.bz2',
]:

  print()
  print(file_name, end='')

  try:
    a = Archive(file_name)
    print(f" is a {a}")

    a.list()
    for name in a.filenames():
      print('\t', name)
      f = a.read_file(name)
      if f:
        print('\t', f.read())
    continue

  except ArchiveException as e:
    print(f" ** ERROR: {e}")


  try:
    f = CompressedFile(file_name)
    print(f" is a {f}")
    print(f)
    print(f.read(10))

  except CompressionException as e:
    print(f" ** ERROR {e}")
