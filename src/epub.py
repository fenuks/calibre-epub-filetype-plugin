from zipfile import ZipFile
from xml.etree import ElementTree
import sys
from pathlib import Path
from fnmatch import fnmatch
import subprocess
from typing import Iterable
import re

class Epub:
    def __init__(self, epub: str):
        self.epub_path = epub
        self.zipfile = ZipFile(epub, "r")
        self.todelete = []
        self.opf_path = Path(self._package())
        self.opf = ElementTree.fromstring(self[str(self.opf_path)])
        self.opf_namespaces = {"": "http://www.idpf.org/2007/opf"}
        self.ncx_path = self._ncx()
        self.ncx = ElementTree.fromstring(self[self.ncx_path])

    def files(self):
        cwd = self.opf_path.parent
        for item in self.opf.findall(".//item", namespaces=self.opf_namespaces):
            yield f"{cwd}/{item.attrib['href']}"

    def glob(self, glob: str) -> Iterable[str]:
        for f in self.files():
            if fnmatch(f, glob):
                yield f

    def fmatch(self, re_pattern) -> Iterable[str]:
        for full_path in self.files():
            filename = Path(full_path).name
            if re.fullmatch(re_pattern, filename):
                yield full_path

    def delete(self, f: str):
        self.todelete.append(f)

    @property
    def is_modified(self):
        return bool(self.todelete)

    def save(self, output: str):
        self.zipfile.close()
        opf_parent = self.opf_path.parent
        manifest = self.opf.find(".//manifest", namespaces=self.opf_namespaces)
        spine = self.opf.find(".//spine", namespaces=self.opf_namespaces)
        for path in self.todelete:
            relative_path = str(Path(path).relative_to(opf_parent))
            for item in manifest.findall(
                f'.//item[@href="{relative_path}"]', namespaces=self.opf_namespaces
            ):
                manifest.remove(item)
                for itemref in spine.findall(
                    f'./itemref[@idref="{item.attrib["id"]}"]',
                    namespaces=self.opf_namespaces,
                ):
                    spine.remove(itemref)
            subprocess.run(["zip", "-d", output, path], check=True)
        subprocess.run(["zip", "-d", output, str(self.opf_path)], check=True)
        opf_bytes = ElementTree.tostring(self.opf, "utf-8", xml_declaration=True)
        tmp_path = "/tmp/epubpy.opf"
        with open(tmp_path, "wb") as fp:
            fp.write(opf_bytes)

        subprocess.run(["zip", "-u", output, tmp_path], check=True)
        subprocess.run(
            ["zipnote", "-w", output],
            input=f"@ {tmp_path[1:]}\n@={self.opf_path}\n".encode("utf8"),
        )

    def _package(self):
        container = self.zipfile.read("META-INF/container.xml").decode("utf8")
        element = ElementTree.fromstring(container)
        matches = element.findall(
            './/rootfile[@media-type="application/oebps-package+xml"]',
            namespaces={"": "urn:oasis:names:tc:opendocument:xmlns:container"},
        )

        if len(matches) != 1:
            print(matches)
            sys.exit(1)

        package = matches[0]
        return package.attrib["full-path"]

    def _ncx(self):
        ncx = self.opf.find(
            './/item[@media-type="application/x-dtbncx+xml"]',
            namespaces=self.opf_namespaces,
        ).attrib["href"]
        return str(self.opf_path.parent / ncx)

    def __getitem__(self, key):
        return self.zipfile.read(key).decode("utf8")

    @property
    def nav(self) -> str:
        path = self._package()
        return self[path]


def main():
    p = "/home/fenuks/Pobrane/test.epub"
    e = Epub(p)
    for i in e.glob("**/*fund*.xhtml"):
        e.delete(i)
    e.save()
    return e


if __name__ == "__main__":
    p = main()
