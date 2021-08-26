from dataclasses import Field, MISSING
from io import StringIO
from types import GenericAlias

COMMENT = '#'


def get_comments_holder(class_, name='_comments_'):
    return getattr(class_, name, CommentsHolder())


def _get_last_key(source: dict[str]):
    return tuple(source)[-1]


def split_on_comment_lines(text: str):
    if text is None:
        return
    return tuple(
        f"{COMMENT} {line.strip()}\n"
        for line in text.strip().splitlines()
    )


def _get_key(line: str):
    if ':' not in line:
        return
    key = line.split(':')[0]
    if ' ' in key:
        key = key.split(' ')[-1]
    return key


class _VariableInfo:
    def __init__(self, data: dict[str]):
        self._data: dict[str] = data
        self.annotations = data.get('__annotations__', {})
        self.name = self._get_name()
        self.type = self.annotations.get(self.name)

    def _get_name(self):
        name = _get_last_key(self._data)
        if not isinstance(self._data[name],
                          self.__class__):
            return name
        return _get_last_key(self.annotations)

    @property
    def typename(self):
        if not self.type:
            return
        if not isinstance(self.type, GenericAlias):
            typename = getattr(self.type, '__name__', None)
            if typename:
                return typename
        return str(self.type).replace("typing.", "")

    @property
    def default_value(self):
        value = self._data.get(self.name)
        if value is None:
            return
        if not isinstance(value, Field):
            return value
        if value.default is not MISSING:
            return value.default
        if value.default_factory is not MISSING:
            return value.default_factory()


class CommentsHolder:
    def __init__(self):
        self.content: dict[str] = dict()

    def add(self, comment: str,
            outer_scope_locals: dict[str],
            include_docstring=False,
            inner_comments='_comments_'):
        info = _VariableInfo(outer_scope_locals)
        comment = self._get_comment_text(info, comment,
                                         include_docstring)
        if comment is not None:
            self.content[info.name] = split_on_comment_lines(comment)
        comments = getattr(info.type, inner_comments, None)
        if not comments:
            return
        self.content |= comments.content

    def _get_comment_text(self,
                          info: _VariableInfo,
                          text: str,
                          include_docstring: bool):
        if text:
            text = text.format(
                name=info.name,
                type=info.type,
                typename=info.typename,
                default=info.default_value
            )
        if not include_docstring:
            return text
        docstring = getattr(info.type, '__doc__', '').strip()
        if text is None:
            return docstring
        return text + docstring


class CommentsWriter:
    def __init__(self,
                 top_comment: str = None,
                 bottom_comment: str = None,
                 line_length_limit=60):
        self._stream = None
        self._top_comments = split_on_comment_lines(top_comment)
        self._bottom_comments = split_on_comment_lines(bottom_comment)
        self.line_length_limit = line_length_limit

    @property
    def input_stream(self):
        self._close_stream()
        self._stream = StringIO()
        return self._stream

    def _close_stream(self):
        if self._stream is None:
            return
        self._stream.close()
        self._stream = None

    def dump(self, stream, comments_map: CommentsHolder):
        lines = self._stream.getvalue().splitlines(True)
        comments_map = comments_map.content
        self._close_stream()

        i = -1
        while True:
            i += 1
            if i >= len(lines):
                break
            line = lines[i]

            if line.lstrip().startswith(COMMENT):
                continue

            comments = comments_map.get(_get_key(line))
            if comments is None or not len(comments):
                continue

            if len(comments) == 1 and self.line_length_limit:
                new_line = line.rstrip() + "  " + comments[0]
                if len(new_line) <= self.line_length_limit:
                    lines[i] = new_line
                    continue

            i += 1
            if i < len(lines):
                comments = list(comments)
                comments.append("\n")

            lines[i:i] = comments
            i += len(comments) - 1

        if self._top_comments:
            lines[0:0] = self._top_comments
            lines.insert(len(self._top_comments), '\n')

        if self._bottom_comments:
            lines.append('\n')
            lines += self._bottom_comments

        stream.writelines(lines)
