import ctypes
import datetime
import os.path
import sys
import textwrap

import inject
import win32con
import win32console
import win32gui
import win32security

import _meta

_shell = ctypes.windll.shell32


class Console:
    def __init__(self):
        self.handle: int = win32console.GetConsoleWindow()
        self._visible = True

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, value):
        self._visible = value
        win32gui.ShowWindow(
            self.handle,
            self.get_visibility_code(value)
        )

    def hide(self):
        self.visible = False

    def show(self):
        self.visible = True

    @staticmethod
    def get_visibility_code(show_console: bool):
        return win32con.SW_SHOW if show_console else win32con.SW_HIDE


def has_admin_rights():
    return _shell.IsUserAnAdmin()


class StartupTaskGenerator:
    def __init__(self,):
        self.script_path = str(_meta.APP_PATH)
        self.task_name = _meta.__product_name__ + "_Startup"
        self.template_path = os.path.abspath("StartupTaskTemplate.xml")
        self.result_path = os.path.abspath("StartupTask.xml")

    def build_task(self):
        encoding = 'utf-16le'
        with open(self.template_path, encoding=encoding) as f:
            template_content = f.read()
        template_content = template_content.format(
            script_path=self.script_path,
            user_id=self.user_id,
            author=self.author,
            task_name=self.task_name,
            date_now=self.date_now,
            description=self.description
        )
        with open(self.result_path, 'w', encoding=encoding) as f:
            f.write(template_content)

    @property
    def date_now(self):
        return datetime.datetime.now().isoformat()

    @property
    def description(self):
        description = f"""
        Starts {_meta.__product_name__} at system start,
        use this app to automatically toggle color inversion
        on blinding-white windows occurs.
        This task generated by {_meta.__product_name__} v{_meta.__version__}
        (author {_meta.__author__})
        """
        description = textwrap.dedent(description).strip()
        description = description.replace('\n', ' \n')
        return description

    @property
    def author(self):
        return f"{os.environ['userdomain']}\\{os.environ['username']}"

    @property
    def user_id(self) -> str:
        security_descriptor = win32security.GetFileSecurity(
            ".", win32security.OWNER_SECURITY_INFORMATION
        )
        sid = security_descriptor.GetSecurityDescriptorOwner()
        return win32security.ConvertSidToStringSid(sid)


class SystemStartupHandler:
    _TASK_COMMAND = "schtasks {args} > nul 2> nul"
    _TASK_CREATE_COMMAND = _TASK_COMMAND.format(args="/Create /XML \"{path}\" /TN \"{name}\"")
    _TASK_DELETE_COMMAND = _TASK_COMMAND.format(args="/Delete /F /TN \"{name}\"")
    _TASK_QUERY_COMMAND = _TASK_COMMAND.format(args="/Query /TN \"{name}\"")
    task_file = inject.attr(StartupTaskGenerator)

    def subscribe(self):
        self.task_file.build_task()
        os.system(self._TASK_CREATE_COMMAND.format(
            path=self.task_file.result_path,
            name=self.task_file.task_name
        ))

    def unsubscribe(self):
        os.system(self._TASK_DELETE_COMMAND.format(
            name=self.task_file.task_name
        ))

    @property
    def is_subscribed(self):
        error_code = os.system(self._TASK_QUERY_COMMAND.format(
            name=self.task_file.task_name
        ))
        return error_code == 0

    @is_subscribed.setter
    def is_subscribed(self, value):
        if value:
            self.subscribe()
        else:
            self.unsubscribe()


def start_with_admin_rights(show_console=False):
    # https://msdn.microsoft.com/en-us/library/windows/desktop/bb762153(v=vs.85).aspx
    if has_admin_rights():
        return
    return_code = _shell.ShellExecuteW(
        None, 'runas', sys.executable, sys.argv[0]+' -m', None,
        Console.get_visibility_code(show_console)
    )
    return return_code > 32
