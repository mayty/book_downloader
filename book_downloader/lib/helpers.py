ConfigDict = dict[str, 'str | int | float | list[object] | ConfigDict']


def merge_configs(source: ConfigDict, override: ConfigDict) -> None:
    for key, value in override.items():
        source_value = source.get(key)

        if not source_value:
            source[key] = value
            continue

        if type(source_value) is not type(value):
            msg = f'Type mismatch for key {key}'
            raise ValueError(msg)

        if isinstance(value, dict):
            assert isinstance(source_value, dict)
            merge_configs(source_value, value)
        else:
            source[key] = value


def url_from_parts(*parts: str) -> str:
    return '/'.join(x.strip('/') for x in parts)
