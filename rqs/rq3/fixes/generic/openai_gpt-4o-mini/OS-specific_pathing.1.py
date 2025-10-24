import unittest
import oe, oe.path
import tempfile
import os
import shutil

class TestRealPath(unittest.TestCase):
    DIRS = [ "a", "b", "etc", "sbin", "usr", "usr/bin", "usr/binX", "usr/sbin", "usr/include", "usr/include/gdbm" ]
    FILES = [ "etc/passwd", "b/file" ]
    LINKS = [
        ( "bin",             os.path.join("usr", "bin"),             os.path.join("usr", "bin") ),
        ( "binX",            os.path.join("usr", "binX"),            os.path.join("usr", "binX") ),
        ( "c",               "broken",               "/broken" ),
        ( "etc/passwd-1",    "passwd",               os.path.join("etc", "passwd") ),
        ( "etc/passwd-2",    "passwd-1",             os.path.join("etc", "passwd") ),
        ( "etc/passwd-3",    os.path.join("etc", "passwd-1"),        os.path.join("etc", "passwd") ),
        ( "etc/shadow-1",    os.path.join("etc", "shadow"),          os.path.join("etc", "shadow") ),
        ( "etc/shadow-2",    os.path.join("etc", "shadow-1"),        os.path.join("etc", "shadow") ),
        ( "prog-A",          os.path.join("bin", "prog-A"),           os.path.join("usr", "bin", "prog-A") ),
        ( "prog-B",          os.path.join("bin", "prog-B"),           os.path.join("usr", "bin", "prog-B") ),
        ( os.path.join("usr", "bin", "prog-C"),  os.path.join("..", "sbin", "prog-C"),    os.path.join("sbin", "prog-C") ),
        ( os.path.join("usr", "bin", "prog-D"),  os.path.join("sbin", "prog-D"),         os.path.join("sbin", "prog-D") ),
        ( os.path.join("usr", "binX", "prog-E"), os.path.join("..", "sbin", "prog-E"),       None ),
        ( os.path.join("usr", "bin", "prog-F"),  os.path.join("..", "..", "..", "sbin", "prog-F"), os.path.join("sbin", "prog-F") ),
        ( "loop",            os.path.join("a", "loop"),               None ),
        ( os.path.join("a", "loop"),          os.path.join("..", "loop"),              None ),
        ( os.path.join("b", "test"),          os.path.join("file", "foo"),             os.path.join("b", "file", "foo") ),
    ]

    LINKS_PHYS = [
        ( "./",          "/",                "" ),
        ( os.path.join("binX", "prog-E"), os.path.join("usr", "sbin", "prog-E"), os.path.join("sbin", "prog-E") ),
    ]

    EXCEPTIONS = [
        ( "loop",   OSError(errno.ELOOP) ),
        ( os.path.join("b", "test"), OSError(errno.ENOENT) ),
    ]

    def __del__(self):
        try:
            shutil.rmtree(self.tmpdir)
        except:
            pass

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix = "oe-test_path")
        self.root = os.path.join(self.tmpdir, "R")

        os.mkdir(os.path.join(self.tmpdir, "_real"))
        os.symlink("_real", self.root)

        for d in self.DIRS:
            os.mkdir(os.path.join(self.root, d))
        for f in self.FILES:
            open(os.path.join(self.root, f), "w").close()
        for l in self.LINKS:
            os.symlink(l[1], os.path.join(self.root, l[0]))

    def __realpath(self, file, use_physdir, assume_dir = True):
        return oe.path.realpath(os.path.join(self.root, file), self.root,
                                use_physdir, assume_dir = assume_dir)

    def test_norm(self):
        for l in self.LINKS:
            if l[2] is None:
                continue

            target_p = self.__realpath(l[0], True)
            target_l = self.__realpath(l[0], False)

            if l[2] is not False:
                self.assertEqual(target_p, target_l)
                self.assertEqual(l[2], target_p[len(self.root):])

    def test_phys(self):
        for l in self.LINKS_PHYS:
            target_p = self.__realpath(l[0], True)
            target_l = self.__realpath(l[0], False)

            self.assertEqual(l[1], target_p[len(self.root):])
            self.assertEqual(l[2], target_l[len(self.root):])

    def test_loop(self):
        for e in self.EXCEPTIONS:
            self.assertRaisesRegex(OSError, r'\[Errno %u\]' % e[1].errno,
                                    self.__realpath, e[0], False, False)