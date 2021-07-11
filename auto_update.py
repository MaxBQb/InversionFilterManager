import os
import sys
import shutil


async def check_for_updates(on_update_applied=None):
    try:
        user, repo = "MaxBQb", "InversionFilterManager"
        client = get_current_version()
        check_link = f"https://api.github.com/repos/{user}/{repo}/releases/latest"
        server = get_latest_version(check_link)
        if server <= client:
            return
        download_link = f"https://github.com/{user}/{repo}/releases/latest/download/release.zip"
        update(download_link, on_update_applied)
    except Exception as e:
        print("Update failed:", e)


def get_current_version():
    from _meta import __version__
    return get_version(__version__)


def get_latest_version(check_link):
    import json
    import requests
    json_data = json.loads(requests.get(check_link).text)
    return get_version_from_tag(json_data['tag_name'])


def get_version_from_tag(tag: str):
    """ tag: format v1.1.1
    """
    return get_version(tag[1:])


def get_version(version: str):
    """ str("1.0.0") -> tuple(1, 0, 0)
    """
    return tuple(int(i) for i in version.split("."))


def update(download_link, on_update_applied):
    app_path = os.path.dirname(sys.argv[0])

    if not check_write_access(app_path):
        return

    update_path = app_path + "_new"
    parent_path, app_dir = os.path.split(app_path)

    if not check_write_access(parent_path):
        return

    backup_name = app_dir + "_old"
    backup_path = app_path + "_old"

    make_empty_dir(update_path)
    from pretty_downloader import pretty_downloader
    release_archive_path = pretty_downloader.download(download_link, update_path, block_size=8192)
    unpack_once(release_archive_path, update_path)
    make_backup(app_path, backup_path, backup_name)
    shutil.move(os.path.join(os.path.realpath(app_path), backup_name+".zip"), parent_path)

    if callable(on_update_applied):
        on_update_applied(
            update_path,
            app_path,
            backup_name + ".zip"
        )

    if sys.platform == "win32":
        complete_update_win32(app_path, update_path)
    else:
        raise NotImplementedError()


def make_backup(origin_path, backup_path, backup_name):
    backup_filename = backup_name + ".zip"
    archive_path = os.path.join(os.path.split(backup_path)[0], backup_filename)
    shutil.copytree(origin_path, backup_path)
    print(archive_path, os.path.exists(archive_path))
    if os.path.exists(archive_path):
        os.remove(archive_path)
    shutil.make_archive(backup_name, "zip", backup_path)
    shutil.rmtree(backup_path)
    return archive_path


def complete_update_win32(current_path, new_path):
    shutil.move(".\\update.bat", "..\\")
    import subprocess
    subprocess.Popen(["..\\update.bat",
                      os.path.basename(current_path),
                      os.path.basename(new_path)],
                     creationflags=subprocess.CREATE_NEW_CONSOLE,
                     )
    # Any alternative suggested! here is very bad solution
    os._exit(0)


def disable_exit_for_threadpool_executor():
    import atexit
    from concurrent.futures import thread
    atexit.unregister(thread._python_exit)


def safe_rename(old_filename, new_filename) -> bool:
    try:
        if os.path.isfile(new_filename):
            os.remove(new_filename)
        os.rename(old_filename, new_filename)
        return True
    except OSError as e:
        (errno, strerror) = e.args
        print(f"Unable to rename {old_filename} to {new_filename}:",
              f"({errno}) {strerror}")
        return False


def unpack_once(filename, extract_dir):
    shutil.unpack_archive(filename, extract_dir)
    os.remove(filename)


def make_empty_dir(path):
    if os.path.isdir(path):
        shutil.rmtree(path, True)
    os.mkdir(path)


def check_write_access(path):
    access = os.access(path, os.W_OK)
    if not access:
        print("Unable to write to", path)
    return access