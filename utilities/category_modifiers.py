#!/usr/bin/env python

import json
import click


def update_match_strings(match_string, strings, categories, cat_index, file_path):
    if match_string.lower() in [string.lower() for string in strings]:
        click.echo("Already in the list")
    else:
        strings.append(match_string)
        categories[cat_index]["match_strings"] = strings

        with open(file_path, "w") as file:
            file.write(json.dumps(categories, indent=4))
            file.close()


def update_budget_goal(budget_goal, categories, cat_index, file_path):
    categories[cat_index]["budget_goal"] = budget_goal

    with open(file_path, "w") as file:
        file.write(json.dumps(categories, indent=4))
        file.close()


def update_current_budget(current_budget, categories, cat_index, file_path):
    categories[cat_index]["current_budget"] = current_budget

    with open(file_path, "w") as file:
        file.write(json.dumps(categories, indent=4))
        file.close()


def update_item_type(item_type, categories, cat_index, file_path):
    categories[cat_index]["Classification"] = item_type

    with open(file_path, "w") as file:
        file.write(json.dumps(categories, indent=4))
        file.close()


@click.command()
@click.option(
    "-f",
    "--file-path",
    "file_path",
    # required=True,
    default=None,
    help="Path to the category file.",
)
@click.option(
    "-c",
    "--category",
    #    required=True,
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
@click.option(
    "-b",
    "--current-budget",
    "current_budget",
    default=None,
    help="String to match in the previous category",
)
@click.option(
    "-g",
    "--budget-goal",
    "budget_goal",
    default=None,
    help="String to match in the previous category",
)
@click.option(
    "-t",
    "--item-type",
    "item_type",
    default=None,
    help="What is the type of this category? Income, Expense, Top-Line Deduction, Bottom-Line Deduction?",
)
# TODO: add option and logic for add / remove
def main(
    file_path: str,
    category: str,
    match_string: str,
    current_budget: float,
    budget_goal: float,
    item_type: str,
):
    print(budget_goal)
    with open(file_path) as file:
        categories = json.load(file)

    # TODO: Consider refactoring this into its own function
    cat_index = next(
        (i for i, item in enumerate(categories) if item["name"] == category), None
    )

    if cat_index is not None:
        strings = categories[cat_index].get("match_strings")

        if match_string:
            update_match_strings(
                match_string, strings, categories, cat_index, file_path
            )

        if budget_goal:
            update_budget_goal(budget_goal, categories, cat_index, file_path)

        if current_budget:
            update_current_budget(current_budget, categories, cat_index, file_path)

        if item_type:
            update_item_type(item_type, categories, cat_index, file_path)


if __name__ == "__main__":
    main()
