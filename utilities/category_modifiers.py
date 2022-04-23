#!/usr/bin/env python

import json
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
@click.option(
    "-c",
    "--category",
    required=True,
    default=None,
    help="Name of the expense category.",
)
@click.option(
    "-s",
    "--match-string",
    "match_string",
    default=None,
    help="String to match in the previous category",
)
# TODO: add option and logic for add / remove
def main(
    file_path: str,
    category: str,
    match_string: str,
):
    with open(file_path) as file:
        categories = json.load(file)

    # TODO: Consider refactoring this into its own function
    cat_index = next(
        (i for i, item in enumerate(categories) if item["name"] == category), None
    )

    # TODO: Consider refactoring this into its own function
    if cat_index != None:
        strings = categories[cat_index].get("match_strings")
        
        if match_string:
            if match_string.lower() in [string.lower() for string in strings]:
                click.echo("Already in the list")
            else:
                strings.append(match_string)
                categories[cat_index]["match_strings"] = strings

                with open(file_path, "w") as file:
                    file.write(json.dumps(categories, indent=4))
                    file.close()


if __name__ == "__main__":
    main()
