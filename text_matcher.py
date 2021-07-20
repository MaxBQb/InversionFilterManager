from re import compile


def get_matcher(text: str, is_regex: bool):
    if text is None:
        return ignore_text
    if is_regex:
        return make_regex_matcher(text)
    return make_plain_text_matcher(text)


def make_regex_matcher(regex_text: str):
    regex = compile(regex_text)

    def check_regex_match(text: str):
        return regex.fullmatch(text) is not None

    return check_regex_match


def make_plain_text_matcher(plain_text: str):

    def check_text_match(text: str):
        return plain_text == text

    return check_text_match


def ignore_text(text: str):
    return True
