"""
Tests of the entire system, all the way out to writing TOML content to stdout.
These tests involve actually running the command `setup.py pyproject`.
"""

import tomlkit


def check_result(result, reference, prefix="running pyproject\n"):
    """
    Check the result succeeded, and matches the expected output.
    """
    assert result.returncode == 0
    assert result.stdout.startswith(prefix)

    reference_parsed = tomlkit.parse(reference)
    result_parsed = tomlkit.parse(result.stdout[len(prefix) :])

    assert result_parsed == reference_parsed


def test_name_and_version(project) -> None:
    """
    Test we can generate a basic project skeleton.
    """
    setup_cfg = """\
[metadata]
name = test-project
version = 0.0.1
"""
    pyproject_toml = """\
[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"

[project]
name = "test-project"
version = "0.0.1"
"""
    project.setup_cfg(setup_cfg)
    project.setup_py()
    result = project.run()
    check_result(result, pyproject_toml)


# This next test should be kept up to date as we add support for more fields.


def test_everything(project) -> None:
    """
    Test all fields that the project supports.
    """
    setup_cfg = """\
[metadata]
name = test-project
version = 0.0.1
author = David Zaslavsky, Stuart Longland
author_email = diazona@ellipsix.net, me@vk4msl.com
maintainer = David Zaslavsky, Stuart Longland
maintainer_email = diazona@ellipsix.net, me@vk4msl.com
description = A dummy project with a sophisticated setup.cfg file
long_description = file:README.md
long_description_content_type = text/markdown
url = https://example.com/test-project
classifiers =
        Development Status :: 1 - Planning
        Environment :: Console
        Intended Audience :: Developers
        License :: OSI Approved :: MIT License
        Operating System :: OS Independent
        Programming Language :: Python
        Programming Language :: Python :: 3
        Programming Language :: Python :: 3 :: Only
        Programming Language :: Python :: 3.6
        Programming Language :: Python :: 3.7
        Programming Language :: Python :: 3.8
        Programming Language :: Python :: 3.9
        Programming Language :: Python :: 3.10
        Programming Language :: Python :: 3.11
        Programming Language :: Python :: 3.12
        Topic :: Software Development :: Testing
keywords = setuptools testing
project_urls =
        Homepage = https://example.com/test-project
        Documentation = https://example.com/test-project/docs

[options]
packages = find:
package_dir =
        = src
include_package_data = true
python_requires = >= 3.6
install_requires =
        dependency1
        dependency2>=1.23
        dependency3<4.56
setup_requires =
        sphinx
        pytest>=6
        pytest-black<99.88.77

[options.packages.find]
where = src
exclude =
        build*
        dist*
        docs*
        tests*
        *.tests
        *.tests.*
        tools*

[options.extras_require]
testing =
        # taken from jaraco/skeleton (we just need an arbitrary list of packages)
        pytest >= 6
        pytest-checkdocs >= 2.4
        pytest-black >= 0.3.7; \
            python_implementation != "PyPy"
        pytest-cov; \
            python_implementation != "PyPy"
        pytest-mypy >= 0.9.1; \
            python_implementation != "PyPy"
        pytest-enabler >= 2.2
        pytest-ruff; sys_platform != "cygwin"

docs =
        # taken from jaraco/skeleton (we just need an arbitrary list of packages)
        sphinx >= 3.5
        jaraco.packaging >= 9
        rst.linker >= 1.9
        furo
        sphinx-lint

[options.entry_points]
console_scripts =
        cliep1 = test_project.cliep1
        cliep2 = test_project.cliep2

gui_scripts =
        guiep1 = test_project.guiep1
        guiep2 = test_project.guiep2

test_project.dummy =
        ep1 = test_project.ep1
        ep2 = test_project.ep2
"""
    readme_md = """\
# test-project

Lorem ipsum and all that
"""
    pyproject_toml = """\
[build-system]
requires = ["pytest-black<99.88.77", "pytest>=6", "setuptools", "sphinx"]
build-backend = "setuptools.build_meta"

[project]
name = "test-project"
version = "0.0.1"
description = "A dummy project with a sophisticated setup.cfg file"
dependencies = ["dependency1", "dependency2>=1.23", "dependency3<4.56"]
classifiers = [
    "Development Status :: 1 - Planning",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Testing",
]

[[project.authors]]
name = "David Zaslavsky"
email = "diazona@ellipsix.net"

[[project.authors]]
name = "Stuart Longland"
email = "me@vk4msl.com"

[[project.maintainers]]
name = "David Zaslavsky"
email = "diazona@ellipsix.net"

[[project.maintainers]]
name = "Stuart Longland"
email = "me@vk4msl.com"

[project.readme]
file = "README.md"
content-type = "text/markdown"

[project.scripts]
cliep1 = "test_project.cliep1"
cliep2 = "test_project.cliep2"

[project.gui-scripts]
guiep1 = "test_project.guiep1"
guiep2 = "test_project.guiep2"

[project.entry-points."test_project.dummy"]
ep1 = "test_project.ep1"
ep2 = "test_project.ep2"
"""
    project.setup_cfg(setup_cfg)
    project.write("README.md", readme_md)
    project.setup_py()
    result = project.run()
    check_result(result, pyproject_toml)
