import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from queue import Queue
from time import sleep
import inject
from configobj import ConfigObj
from app_close import AppCloseManager
from interaction import InteractionManager


@dataclass
class ReleaseArchiveInfo:
    name: str
    size: int
    download_link: str


@dataclass
class VersionInfo:
    version_text: str
    release_info: ReleaseArchiveInfo = None

    @property
    def version(self):
        return get_version(self.version_text)


class AutoUpdater:
    config = inject.attr(ConfigObj)
    im = inject.attr(InteractionManager)
    close_manager = inject.attr(AppCloseManager)

    def __init__(self):
        from threading import Thread
        from datetime import timedelta
        self.delay = timedelta(days=1).total_seconds()
        self.response = Queue()
        self.developer_mode = sys.argv[0].endswith(".py")
        if not self.developer_mode:
            self.thread = Thread(
                name="Update Checker",
                target=self.check_loop,
                daemon=True
            )
        self.update_in_progress = False

    def on_update_applied(self,
                          new_path: Path,
                          current_path: Path,
                          backup_filename: str):
        pass

    def run_check_loop(self):
        if self.developer_mode:
            return
        self.thread.start()
        return self.thread

    def check_loop(self):
        while True:
            if self.config["update"]["check_for_updates"]:
                self.check_for_updates()
            sleep(self.delay)

    def check_for_updates(self):
        try:
            if self.update_in_progress:
                return

            import _meta as app
            client_version = get_version(app.__version__)
            print("Current version:", app.__version__)
            last_version_info = get_latest_version_info(
                app.__author__,
                app.__product_name__
            )

            if last_version_info.version <= client_version or \
                    not last_version_info.release_info:
                print("No updates found")
                return

            print("Latest version:", last_version_info.version_text)

            if not self.request_update(last_version_info):
                print("Update canceled")
                return

            self.update(last_version_info.release_info)
        except Exception as e:
            self.update_in_progress = False
            print("Update failed:", e)

    def request_update(self, version_info):
        if not self.config["update"]["ask_before_update"]:
            return True
        self.im.request_update(
            version_info.version_text,
            version_info.release_info.size,
            self.developer_mode,
            self.response
        )
        return self.response.get()

    def update(self, release_info: ReleaseArchiveInfo):
        if self.update_in_progress:
            return
        self.update_in_progress = True
        app_path = os.path.dirname(sys.argv[0])

        if not check_write_access(app_path):
            return

        update_path = app_path + "_new"
        parent_path, app_dir = os.path.split(app_path)

        if not check_write_access(parent_path):
            return

        backup_name = app_dir + "_old"
        backup_path = app_path + "_old"

        rmdir(update_path)
        os.mkdir(update_path)
        print("Download latest release:", release_info.download_link)
        from pretty_downloader import pretty_downloader
        release_archive_path = pretty_downloader.download(release_info.download_link, update_path, block_size=8192)
        unpack_once(release_archive_path, update_path)
        make_backup(app_path, backup_path, backup_name)
        shutil.move(os.path.join(os.path.realpath(app_path), backup_name + ".zip"), parent_path)

        self.on_update_applied(
            Path(update_path),
            Path(app_path),
            backup_name + ".zip"
        )

        if sys.platform == "win32":
            self.complete_update_win32(app_path, update_path)
        else:
            raise NotImplementedError()

    def complete_update_win32(self, current_path, new_path):
        update_script_path = "..\\update.bat"
        try_remove_file(update_script_path)
        shutil.move(".\\update.bat", "..\\")
        import subprocess
        subprocess.Popen([
                update_script_path,
                os.path.basename(current_path),
                os.path.basename(new_path)
            ], creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
        self.close_manager.close()


def get_latest_version_info(user, repo) -> VersionInfo:
    import json
    import requests
    check_link = f"https://api.github.com/repos/{user}/{repo}/releases/latest"
    data = json.loads(requests.get(check_link).text)
    version_info = VersionInfo(
        data.get('tag_name', "v0.0.0")[1:]
    )
    assets = data.get('assets', [])
    for asset in assets:
        if asset.get("content_type") == "application/zip":
            version_info.release_info = ReleaseArchiveInfo(
                asset.get("name"),
                asset.get("size"),
                asset.get("browser_download_url")
            )
            break
    return version_info


def get_version(version: str):
    """ str("1.0.0") -> tuple(1, 0, 0)
    """
    return tuple(int(i) for i in version.split("."))


def make_backup(origin_path, backup_path, backup_name):
    backup_filename = backup_name + ".zip"
    archive_path = os.path.join(os.path.split(backup_path)[0], backup_filename)
    rmdir(backup_path)
    shutil.copytree(origin_path, backup_path)
    try_remove_file(archive_path)
    shutil.make_archive(backup_name, "zip", backup_path)
    shutil.rmtree(backup_path)
    return archive_path


def unpack_once(filename, extract_dir):
    shutil.unpack_archive(filename, extract_dir)
    os.remove(filename)


def rmdir(path):
    if os.path.isdir(path):
        shutil.rmtree(path, True)


def check_write_access(path):
    access = os.access(path, os.W_OK)
    if not access:
        print("Unable to write to", path)
    return access


def try_remove_file(path):
    if os.path.exists(path):
        os.remove(path)
