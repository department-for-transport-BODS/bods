from zipfile import ZIP_STORED, ZipFile


def create_sparse_file(file_name, file_size):
    with open(file_name, "wb") as fout:
        fout.seek(file_size - 1)
        fout.write(b"/0")


def create_text_file(file_name, contents):
    with open(file_name, "w") as fout:
        fout.write(contents)


def create_zip_file(filename, files, compression=ZIP_STORED):
    with ZipFile(filename, mode="w", compression=compression) as zout:
        for file_ in files:
            zout.write(file_)
