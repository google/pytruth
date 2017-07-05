# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests convert module."""

import hashlib
import os
import subprocess
import tempfile
import unittest

os.environ.setdefault('PBR_VERSION', '1.10.0')
import truth


AssertThat = truth.AssertThat     # pylint: disable=invalid-name


class ConvertTest(unittest.TestCase):

  TRUTH_DIR = os.path.join(
      os.environ['TEST_SRCDIR'], os.environ['TEST_WORKSPACE'], 'truth')
  TESTDATA = os.path.join(TRUTH_DIR, 'testdata')

  @classmethod
  def _Checksum(cls, path):
    with open(path, 'rb') as f:
      return hashlib.sha512(f.read()).hexdigest()

  def setUp(self):
    self.temp_file = tempfile.NamedTemporaryFile(
        prefix='truth-', suffix='.py', delete=False)

  def tearDown(self):
    os.unlink(self.temp_file.name)

  def _Test(self, name, expected_return_code=0):
    """Verifies that the input file is converted as expected."""

    # Copy the contents of the input file to a temporary file.
    with open(os.path.join(self.TESTDATA, '{0}-input.py'.format(name))) as f:
      input_contents = f.read()

    self.temp_file.write(input_contents)
    self.temp_file.close()

    # Convert the temporary file in-place.
    convert_bin = os.path.join(self.TRUTH_DIR, 'convert')
    convert = subprocess.Popen((convert_bin, self.temp_file.name))
    convert.communicate()

    # Check the return code.
    AssertThat(convert.returncode).IsEqualTo(expected_return_code)

    # Check the contents line by line.
    # This is not strictly necessary given the SHA-512 verification, but it
    # makes debugging test failures easier.
    expected_path = os.path.join(self.TESTDATA, '{0}-expected.py'.format(name))
    line = 0
    with open(self.temp_file.name) as converted_file:
      with open(expected_path) as expected_file:
        for converted_line in converted_file:
          line += 1
          name = 'at line {0}'.format(line)
          expected_line = expected_file.readline()
          AssertThat(converted_line).Named(name).IsEqualTo(expected_line)

    # Verify the contents are exactly identical.
    actual_hash = self._Checksum(self.temp_file.name)
    expected_hash = self._Checksum(expected_path)
    AssertThat(actual_hash).IsEqualTo(expected_hash)

  def testConvertEverything(self):
    self._Test('everything')

  def testUnbalancedParanthesesDoesNotOverwriteFile(self):
    self._Test('unbalanced', 1)


if __name__ == '__main__':
  unittest.main()
