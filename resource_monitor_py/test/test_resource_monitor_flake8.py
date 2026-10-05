# Copyright 2017 Open Source Robotics Foundation, Inc.
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

import pathlib

import pytest

from ament_flake8.main import main_with_errors


# modify the path to point to the package root so that it only check the package files

file_path = pathlib.Path(__file__).parent.resolve()
package_path = str(file_path).split('test')[0]


@pytest.mark.flake8
@pytest.mark.linter
def test_flake8():
    rc, errors = main_with_errors(argv=[package_path])
    assert rc == 0, f'Found {len(errors)} code style errors / warnings:\n{chr(10).join(errors)}'
