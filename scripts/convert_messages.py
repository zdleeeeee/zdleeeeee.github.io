"""Convert a configured battle log to Hugo message shortcodes."""

import argparse
import json
import re
from pathlib import Path


def convert(source: str) -> str:
    lines = source.splitlines()
    try:
        separator = lines.index("---")
    except ValueError as exc:
        raise ValueError("Missing '---' between settings and body") from exc

    settings = []
    fields = {}
    for line in [*lines[:separator], ""]:
        if not line.strip():
            if fields:
                if "name" not in fields:
                    raise ValueError("A settings block is missing name")
                settings.append((re.compile(fields.pop("name")), fields))
                fields = {}
            continue
        key, equals, value = line.partition("=")
        if not equals or len(value) < 2 or not value.startswith('"') or not value.endswith('"'):
            raise ValueError(f"Invalid setting: {line}")
        fields[key] = value[1:-1]

    if not settings:
        raise ValueError("No name patterns configured")

    output = []
    content = []
    active = None

    def flush():
        block = "\n".join(content).strip("\n")
        if active is None:
            if block:
                output.append(block)
        else:
            name, options = active
            attrs = {"name": name, **{key: value for key, value in options.items() if value}}
            args = " ".join(f"{key}={json.dumps(value, ensure_ascii=False)}" for key, value in attrs.items())
            output.append(f"{{{{< message {args} >}}}}\n{block}\n{{{{< /message >}}}}")

    for line in lines[separator + 1:]:
        match = next(((line, options) for pattern, options in settings if pattern.fullmatch(line)), None)
        if match:
            flush()
            active = match
            content = []
        else:
            content.append(line)
    flush()
    return "\n\n".join(output) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Source TXT with settings before ---")
    parser.add_argument("-o", "--output", type=Path, help="Output TXT path")
    args = parser.parse_args()
    output = args.output or args.input.with_name(f"{args.input.stem}_message.txt")
    output.write_text(convert(args.input.read_text(encoding="utf-8")), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
