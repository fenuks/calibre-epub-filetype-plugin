__license__ = "GPL v3"
__copyright__ = "2022, fenuks"
__docformat__ = "markdown en"

import re
from calibre.customize import FileTypePlugin

from .epub import Epub


class EpubAdRemover(FileTypePlugin):
    name = "Wolne Lektury od reklam"
    description = "Usuwa natarczywe prośby o dotacje spomiędzy treści książki. Wymaga pakietu zip."
    supported_platforms = [
        "linux",
    ]
    author = "fenuks"
    version = (1, 0, 0)
    file_types = {"epub"}
    on_import = True
    minimum_calibre_version = (0, 7, 53)

    def run(self, path_to_ebook: str) -> str:
        ebook = Epub(path_to_ebook)
        for i in ebook.fmatch(re.compile(r'fund\d*\.xhtml')):
            ebook.delete(i)

        if not ebook.is_modified:
            return path_to_ebook

        ebook_copy_fp = self.temporary_file("_wolnelektury.epub")
        with open(path_to_ebook, "rb") as orig_fp:
            ebook_copy_fp.write(orig_fp.read())

        ebook.save(ebook_copy_fp.name)
        return ebook_copy_fp.name
