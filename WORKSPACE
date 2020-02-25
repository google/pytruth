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

workspace(name = "pytruth")

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

http_archive(
    name = "appdirs_1_4_3",
    build_file = "//third_party/appdirs:BUILD",
    sha256 = "9e5896d1372858f8dd3344faf4e5014d21849c756c8d5701f78f8a103b372d92",
    strip_prefix = "appdirs-1.4.3",
    urls = [
        "https://files.pythonhosted.org/packages/48/69/d87c60746b393309ca30761f8e2b49473d43450b150cb08f3c6df5c11be5/appdirs-1.4.3.tar.gz",
    ],
)

http_archive(
    name = "funcsigs_1_0_2",
    build_file = "//third_party/funcsigs:BUILD",
    sha256 = "a7bb0f2cf3a3fd1ab2732cb49eba4252c2af4240442415b4abce3b87022a8f50",
    strip_prefix = "funcsigs-1.0.2",
    urls = [
        "https://files.pythonhosted.org/packages/94/4a/db842e7a0545de1cdb0439bb80e6e42dfe82aaeaadd4072f2263a4fbed23/funcsigs-1.0.2.tar.gz",
    ],
)

http_archive(
    name = "absl_py",
    urls = [
        "https://github.com/abseil/abseil-py/archive/pypi-v0.9.0.tar.gz",
    ],
    sha256 = "603febc9b95a8f2979a7bdb77d2f5e4d9b30d4e0d59579f88eba67d4e4cc5462",
    strip_prefix = "abseil-py-pypi-v0.9.0",
)

http_archive(
    name = "enum34_archive",
    build_file = "//third_party/enum34:BUILD",
    sha256 = "8ad8c4783bf61ded74527bffb48ed9b54166685e4230386a9ed9b1279e2df5b1",
    strip_prefix = "enum34-1.1.6",
    urls = [
        "https://files.pythonhosted.org/packages/bf/3e/31d502c25302814a7c2f1d3959d2a3b3f78e509002ba91aea64993936876/enum34-1.1.6.tar.gz",
    ],
)

http_archive(
    name = "mock_2_0_0",
    build_file = "//third_party/mock:BUILD",
    sha256 = "b158b6df76edd239b8208d481dc46b6afd45a846b7812ff0ce58971cf5bc8bba",
    strip_prefix = "mock-2.0.0",
    urls = [
        "https://files.pythonhosted.org/packages/0c/53/014354fc93c591ccc4abff12c473ad565a2eb24dcd82490fae33dbf2539f/mock-2.0.0.tar.gz",
    ],
)

http_archive(
    name = "packaging_19_0",
    build_file = "//third_party/packaging:BUILD",
    sha256 = "0c98a5d0be38ed775798ece1b9727178c4469d9c3b4ada66e8e6b7849f8732af",
    strip_prefix = "packaging-19.0",
    urls = [
        "https://files.pythonhosted.org/packages/16/51/d72654dbbaa4a4ffbf7cb0ecd7d12222979e0a660bf3f42acc47550bf098/packaging-19.0.tar.gz",
    ],
)

http_archive(
    name = "pbr_5_1_3",
    build_file = "//third_party/pbr:BUILD",
    sha256 = "8c361cc353d988e4f5b998555c88098b9d5964c2e11acf7b0d21925a66bb5824",
    strip_prefix = "pbr-5.1.3",
    urls = [
        "https://files.pythonhosted.org/packages/97/76/c151aa4a3054ce63bb6bbd32f3541e4ae068534ed8b74ee2687f6773b013/pbr-5.1.3.tar.gz",
    ],
)

http_archive(
    name = "pyparsing_2_3_1",
    build_file = "//third_party/pyparsing:BUILD",
    sha256 = "66c9268862641abcac4a96ba74506e594c884e3f57690a696d21ad8210ed667a",
    strip_prefix = "pyparsing-2.3.1",
    urls = [
        "https://files.pythonhosted.org/packages/b9/b8/6b32b3e84014148dcd60dd05795e35c2e7f4b72f918616c61fdce83d27fc/pyparsing-2.3.1.tar.gz",
    ],
)

http_archive(
    name = "setuptools_40_8_0",
    build_file = "//third_party/setuptools:BUILD",
    sha256 = "6e4eec90337e849ade7103723b9a99631c1f0d19990d6e8412dc42f5ae8b304d",
    strip_prefix = "setuptools-40.8.0",
    urls = [
        "https://files.pythonhosted.org/packages/c2/f7/c7b501b783e5a74cf1768bc174ee4fb0a8a6ee5af6afa92274ff964703e0/setuptools-40.8.0.zip",
    ],
)

http_archive(
    name = "six_archive",
    build_file = "//third_party/six:BUILD",
    sha256 = "d16a0141ec1a18405cd4ce8b4613101da75da0e9a7aec5bdd4fa804d0e0eba73",
    strip_prefix = "six-1.12.0",
    urls = [
        "https://files.pythonhosted.org/packages/dd/bf/4138e7bfb757de47d1f4b6994648ec67a51efe58fa907c1e11e350cddfca/six-1.12.0.tar.gz",
    ],
)
