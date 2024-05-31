import argparse
import os

from devtools import pprint
from magentic import OpenaiChatModel, prompt

from autoproject import functions
from autoproject.models import Project


@prompt(
    """
This is the list of goals for the project: {goals}
Break the goals down into tasks to create a project plan.
Create unique assistants with roles, skills and backstory necessary to complete the tasks.
Create a number of assistants with efficiency in mind, do not create more assistants than tasks.
The backstory must be written as if speaking to that assistant (it will be a prompt for an LLM).
Assign tasks to assistants with efficiency in mind.
These are the functions that can be used by tasks: {function_list}
If the task will require external resources or API functions that you cannot provide,
list them as requirements for the project.
When thinking about requirements, be aware that you are an LLM without access to
the Internet and will need various functions to be able to see, view and interact
with the project and Internet.
"""
)
# pylint: disable=unused-argument, missing-function-docstring
def create_project(goals: list[str], function_list: dict) -> Project: ...


def main():
    """The main function that executes the project plan."""
    parser = argparse.ArgumentParser(description="Create a project plan.")
    parser.add_argument("-l", "--load", help="Load a project from a file.")
    parser.add_argument(
        "-s", "--save", help="Save the project to a file before execution."
    )
    parser.add_argument("goals", nargs="*", help="The goals for the project.")

    args = parser.parse_args()

    if args.load:
        print(f"Loading project from projects/{args.load}.json")
        project = Project.load(f"projects/{args.load}.json")
    else:
        with OpenaiChatModel(
            os.getenv("PLANNER_MODEL", "gpt-4o"),
            temperature=float(os.getenv("PLANNER_TEMPERATURE", "0.2")),
        ):
            project = create_project(
                args.goals, function_list=functions.get_function_list()
            )

            if args.save:
                print(f"Saving project to projects/{args.save}.json")
                project.save(f"projects/{args.save}.json")

    pprint(project)

    project.execute()
    print("All tasks are done!")


if __name__ == "__main__":
    main()
