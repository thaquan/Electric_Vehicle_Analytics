import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location('phase12_restore', Path(__file__).resolve().parents[1] / 'scripts/phase12_restore.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Phase12Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def bundle(self):
        root = self.root / 'bundle'
        root.mkdir()
        source = root / 'data.txt'
        source.write_text('original')
        module.write_json(root / 'manifest.json', {'files': {'data.txt': {'bytes': source.stat().st_size, 'sha256': module.digest(source)}}})
        (root / 'manifest.sha256').write_text(module.digest(root / 'manifest.json'))
        return root

    def test_tampered_data_rejected(self):
        root = self.bundle()
        module.verify(root)
        (root / 'data.txt').write_text('modified')
        with self.assertRaisesRegex(ValueError, 'checksum'):
            module.verify(root)

    def test_unexpected_file_rejected(self):
        root = self.bundle()
        (root / 'extra.txt').touch()
        with self.assertRaisesRegex(ValueError, 'unexpected'):
            module.verify(root)

    def test_zip_traversal_rejected(self):
        archive = self.root / 'bad.zip'
        with zipfile.ZipFile(archive, 'w') as z:
            z.writestr('../escaped.txt', 'bad')
        with self.assertRaisesRegex(ValueError, 'Unsafe ZIP'):
            module.extract(archive, self.root / 'extract')
        self.assertFalse((self.root / 'escaped.txt').exists())

    def test_existing_restore_directory_preserved(self):
        destination = self.root / 'existing'
        destination.mkdir()
        with self.assertRaisesRegex(ValueError, 'must be new'):
            module.extract(self.root / 'unused.zip', destination)


if __name__ == '__main__':
    unittest.main()
