import re
import random
import unittest
import ConfigParser
from textwrap import dedent
from StringIO import StringIO
from iniparse import compat, ini

# TODO:
#  tabs
#  substitutions

def random_string(maxlen=200):
    length = random.randint(0, maxlen)
    s = []
    for i in range(length):
        s.append(chr(random.randint(32, 126)))

    return ''.join(s)

def random_space(maxlen=10):
    length = random.randint(0, maxlen)
    return ' '*length

def random_ini_file():
    num_lines = random.randint(0, 100)
    lines = []
    for i in range(num_lines):
        x = random.random()
        if x < 0.1:
            # empty line
            lines.append(random_space())
        elif x < 0.3:
            # comment
            sep = random.choice(['#', ';'])
            lines.append(sep + random_string())
        elif x < 0.5:
            # section
            if random.random() < 0.1:
                name = 'DEFAULT'
            else:
                name = random_string()
                name = re.sub(']', '' , name)
            l = '[' + name + ']'
            if random.randint(0,1):
                l += random_space()
            if random.randint(0,1):
                sep = random.choice(['#', ';'])
                l += sep + random_string()
            lines.append(l)
        elif x < 0.7:
            # option
            name = random_string()
            name = re.sub(':|=| |\[', '', name)
            sep = random.choice([':', '='])
            l = name + random_space() + sep + random_space() + random_string()
            if random.randint(0,1):
                l += ' ' + random_space() + ';'  +random_string()
            lines.append(l)
        elif x < 0.9:
            # continuation
            lines.append(' ' + random_space() + random_string())
        else:
            # junk
            lines.append(random_string())

    return '\n'.join(lines)

class test_fuzz(unittest.TestCase):
    def test_fuzz(self):
        random.seed(42)
        for i in range(100):
            # parse random file with errors disabled
            s = random_ini_file()
            c = ini.INIConfig(parse_exc=False)
            c._readfp(StringIO(s))
            # check that file is preserved, except for
            # commenting out erroneous lines
            l1 = s.split('\n')
            l2 = str(c).split('\n')
            self.assertEqual(len(l1), len(l2))
            good_lines = []
            for i in range(len(l1)):
                try:
                    self.assertEqual(l1[i], l2[i])
                    good_lines.append(l1[i])
                except AssertionError:
                    self.assertEqual('#'+l1[i], l2[i])
            # parse the good subset of the file
            # using ConfigParser
            s = '\n'.join(good_lines)
            cc = compat.RawConfigParser()
            cc.readfp(StringIO(s))
            cc_py = ConfigParser.RawConfigParser()
            cc_py.readfp(StringIO(s))
            # compare the two configparsers
            self.assertEqualSorted(cc_py.sections(), cc.sections())
            self.assertEqualSorted(cc_py.defaults().items(), cc.defaults().items())
            for sec in cc_py.sections():
                self.assertEqualSorted(cc_py.items(sec), cc.items(sec))

    def assertEqualSorted(self, l1, l2):
        l1.sort()
        l2.sort()
        self.assertEqual(l1, l2)

class suite(unittest.TestSuite):
    def __init__(self):
        unittest.TestSuite.__init__(self, [
                unittest.makeSuite(test_fuzz, 'test'),
    ])
