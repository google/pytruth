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

licenses(["notice"])  # Apache 2.0

py_library(
    name = "truth",
    srcs = ["truth.py"],
    srcs_version = "PY2AND3",
    visibility = ["//visibility:public"],
    deps = [
        "@mock_2_0_0//:mock",
        "@six_1_10_0//:six",
    ],
)

py_test(
    name = "truth_test",
    srcs = ["truth_test.py"],
    srcs_version = "PY2AND3",
    deps = [
        ":truth",
        "@mock_2_0_0//:mock",
        "@six_1_10_0//:six",
    ],
)

py_binary(
    name = "convert",
    srcs = ["convert.py"],
    srcs_version = "PY2AND3",
    visibility = ["//visibility:public"],
    deps = [
        ":convert_lib",
    ],
)

py_library(
    name = "convert_lib",
    srcs = ["convert.py"],
    srcs_version = "PY2AND3",
    visibility = ["//visibility:public"],
    deps = [
        "@gflags_3_1_1//:gflags",
        "@pyglib_0_1//:pyglib",
    ],
)

py_test(
    name = "convert_test",
    srcs = ["convert_test.py"],
    data = glob(["testdata/*.py"]),
    srcs_version = "PY2AND3",
    deps = [
        ":convert_lib",
        ":truth",
        "@gflags_3_1_1//:gflags",
        "@mock_2_0_0//:mock",
        "@pyglib_0_1//:pyglib",
    ],
)
