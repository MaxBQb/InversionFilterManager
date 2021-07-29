def field_names_to_values(*args, **kwargs):
    def _field_names_to_values(format: str = "{}"):
        def __field_names_to_values(cls):
            for field in cls.__annotations__:
                if not field.startswith('_'):
                    setattr(cls, field, format.format(field))
            return cls
        return __field_names_to_values

    if len(args) == 1 and len(kwargs) == 0 and not isinstance(args[0], str):
        # for @field_names_to_values
        return _field_names_to_values()(args[0])

    # for @field_names_to_values(format="left_mid{}dle_right")
    return _field_names_to_values(*args, **kwargs)


def ellipsis_trunc(text: str, width=12):
    if len(text) <= width or width < 1:
        return text
    return text[:width-1].rstrip() + "…"


def rename_key(container: dict, old_key, new_key, override=True) -> bool:
    if old_key not in container:
        return False

    if new_key in container and not override:
        return False

    value = container[old_key]
    del container[old_key]
    container[new_key] = value
    return True


