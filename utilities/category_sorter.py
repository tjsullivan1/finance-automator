#!/usr/bin/env python

import json
import operator

import click


@click.command()
@click.option(
    "-f",
    "--file-path",
    "file_path",
    required=True,
    default=None,
    help="Path to the category file.",
)
def main(file_path: str):
    with open(file_path) as file:
        categories = json.load(file)

    categories.sort(key=operator.itemgetter("name"))

    with open(file_path, "w") as file:
        file.write(json.dumps(categories, indent=2))
        file.close()


if __name__ == "__main__":
    main()
