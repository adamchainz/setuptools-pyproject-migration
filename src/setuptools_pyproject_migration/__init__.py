import itertools
import distutils
import setuptools
import sys
import tomlkit
import json
from pep508_parser import parser as pep508
from typing import Any, Dict, List, Optional, Tuple, Type, Union

# After we drop support for Python <3.10, we can import TypeAlias directly from typing
from typing_extensions import Required, TypedDict


# PEP 518
BuildSystem: Type = TypedDict("BuildSystem", {"requires": List[str], "build-backend": str}, total=True)

# https://packaging.python.org/en/latest/specifications/declaring-project-metadata/
Contributor: Type = TypedDict("Contributor", {"name": str, "email": str}, total=False)
LicenseFile: Type = TypedDict("LicenseFile", {"file": str})
LicenseText: Type = TypedDict("LicenseText", {"text": str})
ReadmeInfo: Type = TypedDict("ReadmeInfo", {"file": str, "content-type": str})


def _parse_entry_point(entry_point: str) -> Tuple[str, str]:
    """
    Extract the entry point and name from the string.

    >>> _parse_entry_point("hello-world = timmins:hello_world")
    ('hello-world', 'timmins:hello_world')
    >>> _parse_entry_point("hello-world=timmins:hello_world")
    ('hello-world', 'timmins:hello_world')
    >>> _parse_entry_point("  hello-world  =  timmins:hello_world  ")
    ('hello-world', 'timmins:hello_world')
    >>> _parse_entry_point("hello-world")
    Traceback (most recent call last):
        ...
    ValueError: Entry point 'hello-world' is not of the form 'name = module:function'

    :param: entry_point The entry point string, of the form
                        "entry_point = module:function" (whitespace optional)
    :returns:           A two-element `tuple`, first element is the entry point name, second element is the target
                        (module and function name) as a string.
    :raises ValueError: An equals (`=`) character was not present in the entry point string.
    """
    if "=" not in entry_point:
        raise ValueError("Entry point %r is not of the form 'name = module:function'" % entry_point)

    (name, target) = entry_point.split("=", 1)
    return (name.strip(), target.strip())


def _generate_entry_points(entry_points: Optional[Dict[str, List[str]]]) -> Dict[str, Dict[str, str]]:
    """
    Dump the entry points given, if any.

    >>> _generate_entry_points(None)
    {}
    >>> _generate_entry_points({"type1": ["ep1=mod:fn1", "ep2=mod:fn2"],
    ...                        "type2": ["ep3=mod:fn3", "ep4=mod:fn4"]})
    {'type1': {'ep1': 'mod:fn1', 'ep2': 'mod:fn2'}, 'type2': {'ep3': 'mod:fn3', 'ep4': 'mod:fn4'}}

    :param: entry_points The `entry_points` property from the
                        :py:class:setuptools.dist.Distribution being examined.
    :returns:           The entry points, split up as per
                        :py:func:_parse_entry_point and grouped by entry point type.
    """
    if not entry_points:
        return {}

    parsed_entry_points: Dict[str, Dict[str, str]] = {}

    for eptype, raweps in entry_points.items():
        parsed_entry_points[eptype] = dict(map(_parse_entry_point, raweps))

    return parsed_entry_points


Project: Type = TypedDict(
    "Project",
    {
        "authors": List[Contributor],
        "classifiers": List[str],
        "dependencies": List[str],
        "description": str,
        "dynamic": List[str],
        "entry-points": Dict[str, Dict[str, str]],
        "gui-scripts": Dict[str, str],
        "keywords": List[str],
        "license": Union[LicenseFile, LicenseText],
        "maintainers": List[Contributor],
        "name": Required[str],
        "optional-dependencies": Dict[str, List[str]],
        "readme": Union[str, ReadmeInfo],
        "requires-python": str,
        "scripts": Dict[str, str],
        "urls": Dict[str, str],
        "version": str,
    },
    total=False,
)

Pyproject: Type = TypedDict("Pyproject", {"build-system": BuildSystem, "project": Project}, total=False)


class DumpMetadata(setuptools.Command):  # pragma: no cover
    """
    Dump the metadata provided in the setup package.  This is a debugging tool
    primarily to figure out what fields are exposed and where they may be
    hiding.
    """

    # Note: excluded from coverage, as this is meant as a debugging fixture.

    # Each option tuple contains (long name, short name, help string)
    user_options: List[Tuple[str, Optional[str], str]] = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        metadata: Dict[str, Dict[str, Any]] = {}

        for attr in dir(self.distribution):
            if attr.startswith("_"):
                # Ignore 'protected' members
                continue

            value: Any = getattr(self.distribution, attr)
            if hasattr(value, "__call__"):
                if not attr.startswith("get_"):
                    # Ignore methods that are not "getters"
                    continue

                try:
                    value = value()
                    metadata.setdefault("methods", {})[attr] = self._to_json(value)
                except:
                    continue
            else:
                metadata.setdefault("properties", {})[attr] = self._to_json(value)

        try:
            metadata["metadata"] = self.distribution.command_options["metadata"]
        except KeyError:
            # This is not present if it's embedded in the setup.py file!
            pass

        print(json.dumps(metadata, indent=4, sort_keys=True))

    def _to_json(self, v: Any) -> Any:
        if (v is None) or isinstance(v, (bool, int, str)):
            return v
        elif isinstance(v, (list, tuple)):
            return [self._to_json(e) for e in v]
        elif isinstance(v, dict):
            return dict([(self._to_json(k), self._to_json(e)) for k, e in v.items()])
        elif isinstance(v, distutils.dist.DistributionMetadata):
            return dict(
                [
                    (a, getattr(v, a))
                    for a in getattr(  # Dodgy: relies on internal parameter
                        v,
                        "_METHOD_BASENAMES",
                        # In case they remove _METHOD_BASENAMES
                        (
                            "name",
                            "version",
                            "author",
                            "author_email",
                            "maintainer",
                            "maintainer_email",
                            "url",
                            "license",
                            "description",
                            "long_description",
                            "keywords",
                            "platforms",
                            "fullname",
                            "contact",
                            "contact_email",
                            "classifiers",
                            "download_url",
                            # PEP 314
                            "provides",
                            "requires",
                            "obsoletes",
                        ),
                    )
                    if hasattr(v, a)
                ]
            )
        else:
            return repr(v)


class WritePyproject(setuptools.Command):
    # Each option tuple contains (long name, short name, help string)
    user_options: List[Tuple[str, Optional[str], str]] = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    @staticmethod
    def _strip_and_canonicalize(s: str) -> str:
        """
        Strip whitespace from around a string, but replace the sentinel value
        ``"UNKNOWN"`` (used by setuptools<62.2) with an empty string.

        >>> WritePyproject._strip_and_canonicalize("        ooh, you lucky bastard")
        'ooh, you lucky bastard'
        >>> WritePyproject._strip_and_canonicalize("UNKNOWN")
        ''
        >>> WritePyproject._strip_and_canonicalize("")
        ''
        """
        s = s.strip()
        if s == "UNKNOWN":
            return ""
        else:
            return s

    @staticmethod
    def _transform_contributors(name_string: Optional[str], email_string: Optional[str]) -> List[Contributor]:
        """
        Transform the name and email strings that setuptools uses to specify
        contributors (either authors or maintainers) into a list of dicts of
        the form that should be written into ``pyproject.toml``.

        >>> WritePyproject._transform_contributors("John Cleese", "john@python.example.com")
        [{'name': 'John Cleese', 'email': 'john@python.example.com'}]

        Missing entries will be replaced with the empty string.

        >>> WritePyproject._transform_contributors("John Cleese, Graham Chapman", "john@python.example.com")
        [{'name': 'John Cleese', 'email': 'john@python.example.com'}, {'name': 'Graham Chapman', 'email': ''}]

        :param: name_string  A string giving a comma-separated list of contributor
                             names.
        :param: email_string A string giving a comma-separated list of contributor
                             email addresses which correspond to the names.
        :returns:            A list of dicts containing corresponding names and
                             email addresses parsed from the strings.
        """
        names = map(WritePyproject._strip_and_canonicalize, (name_string or "").split(","))
        emails = map(WritePyproject._strip_and_canonicalize, (email_string or "").split(","))
        return [{"name": n, "email": e} for n, e in itertools.zip_longest(names, emails, fillvalue="") if n or e]

    def _generate(self) -> Pyproject:
        """
        Create the raw data structure containing the information from
        a pyproject.toml file.
        """
        dist: setuptools.dist.Distribution = self.distribution

        # pyproject.toml schema:
        # https://packaging.python.org/en/latest/specifications/declaring-project-metadata/#declaring-project-metadata

        # Enumerate all set-up and build requirements, ensure there are no duplicates
        setup_requirements = set(dist.setup_requires)

        # Is 'setuptools' already there?
        has_setuptools = any(pep508.parse(dep)[0] == "setuptools" for dep in setup_requirements)

        if not has_setuptools:
            # We will need it here
            setup_requirements.add("setuptools")

        pyproject: Pyproject = {
            "build-system": {
                "requires": sorted(setup_requirements),
                "build-backend": "setuptools.build_meta",
            }
        }

        pyproject["project"] = {
            "name": dist.get_name(),
            "version": dist.get_version(),  # TODO try to reverse-engineer dynamic version
        }

        authors: List[Contributor] = self._transform_contributors(dist.get_author(), dist.get_author_email())
        if authors:
            pyproject["project"]["authors"] = authors

        maintainers: List[Contributor] = self._transform_contributors(
            dist.get_maintainer(), dist.get_maintainer_email()
        )
        if maintainers:
            pyproject["project"]["maintainers"] = maintainers

        classifiers: List[str] = dist.get_classifiers()
        if classifiers:
            pyproject["project"]["classifiers"] = classifiers

        description: str = dist.get_description()
        # "UNKNOWN" is used by setuptools<62.2 when the description in setup.cfg is empty or absent
        if description and description != "UNKNOWN":
            pyproject["project"]["description"] = description

        # NB: ensure a consistent alphabetical ordering of dependencies
        dependencies = sorted(set(dist.install_requires))
        if dependencies:
            pyproject["project"]["dependencies"] = dependencies

        entry_points = _generate_entry_points(dist.entry_points)

        # GUI scripts and console scripts go separate in dedicated locations.
        if "console_scripts" in entry_points:
            pyproject["project"]["scripts"] = entry_points.pop("console_scripts")

        if "gui_scripts" in entry_points:
            pyproject["project"]["gui-scripts"] = entry_points.pop("gui_scripts")

        # Anything left over gets put in entry-points
        if entry_points:
            pyproject["project"]["entry-points"] = entry_points

        return pyproject

    def run(self):
        """
        Write out the contents of a pyproject.toml file containing information
        ingested from ``setup.py`` and/or ``setup.cfg``.
        """
        tomlkit.dump(self._generate(), sys.stdout)


__all__ = ["WritePyproject", "DumpMetadata"]
