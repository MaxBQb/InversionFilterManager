from dataclasses import dataclass


@dataclass
class ReleaseArchiveInfo:
    name: str
    size: int
    download_link: str


@dataclass
class VersionInfo:
    version_text: str
    description: str
    release_info: ReleaseArchiveInfo = None

    @property
    def version(self):
        return get_version(self.version_text)


def get_version(version: str):
    """ str("1.0.0") -> tuple(1, 0, 0)
    """
    return tuple(int(i) for i in version.split("."))
