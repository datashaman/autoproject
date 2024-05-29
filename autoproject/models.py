import json
import os

from typing import Optional

from devtools import pprint
from openai import OpenAI
from pydantic import BaseModel, PrivateAttr


class Assistant(BaseModel):
    """Assistant model that mimics the OpenAI assistant model."""

    name: str
    role: str
    instructions: str
    tools: list[str] = []


class Requirement(BaseModel):
    """
    Requirement model that describes a missing requirement of a project.
    These are functions that the planner has decided it needs to complete the task.
    """

    title: str
    description: str


class Task(BaseModel):
    """Task model that describes a task that needs to be completed by an assistant."""

    title: str
    instructions: str
    assigned_to: Assistant
    done: bool = False
    depends_on: list[str] = []
    functions: list[str] = []


class Project(BaseModel):
    """Project model that describes a project that needs to be completed."""

    reference: str
    goals: list[str]
    assistants: list[Assistant]
    tasks: list[Task]
    requirements: list[Requirement] = []

    _client: Optional[OpenAI] = PrivateAttr(None)

    def execute(self, client: Optional[OpenAI] = None) -> None:
        """Execute the project."""
        if not client:
            client = OpenAI()

        self._client = client

        for assistant in self.assistants:
            print(
                f"Creating/updating assistant {assistant.name} with role "
                + f"{assistant.role} for project {self.reference}."
            )
            self.update_or_create_assistant(assistant)

        thread = client.beta.threads.create()

        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"I would like to complete project {self.reference} with goals {self.goals}.",
        )

        done_count = 0
        tasks = dict((task.title, task) for task in self.tasks)

        while done_count < len(tasks):
            for task in tasks.values():
                if task.done:
                    continue
                if all(tasks[depend_on].done for depend_on in task.depends_on):
                    print(f"{task.assigned_to.role}: {task.instructions}")

                    openai_assistant = self.get_openai_assistant(task.assigned_to)

                    run = client.beta.threads.runs.create_and_poll(
                        thread_id=thread.id,
                        assistant_id=openai_assistant.id,
                        instructions=f"{task.assigned_to.name}, please {task.instructions}",
                    )

                    messages = list(client.beta.threads.messages.list(
                        thread_id=thread.id,
                    ))

                    most_recent_message = messages[0]

                    if most_recent_message.role == "assistant":
                        print(f"{task.assigned_to.name}: {most_recent_message.content[0].text.value}")

                    user_input = input("> ")

                    task.done = True
                    done_count += 1

    def wait_on_run(self, run):
        while run.status == "queued" or run.status == "in_progress":
            run = client.beta.threads.runs.retrieve(
                thread_id=run.thread_id,
                run_id=run.id,
            )
            time.sleep(0.5)
        return run

    @classmethod
    def load(cls, filename: str) -> "Project":
        """Load a project from a JSON file."""
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)
            return cls.model_validate(data)

    def save(self, filename: str) -> None:
        """Save the project to a JSON file."""
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(self.model_dump(), file, indent=4)

    def get_assistant_list(self) -> list:
        """Get a list of OpenAI assistants."""
        return self._client.beta.assistants.list()

    def get_openai_assistant(self, assistant: Assistant) -> Optional[dict]:
        """Get an OpenAI assistant given an assistant model."""
        name = self.generate_assistant_name(assistant)
        return next(
            (
                assistant
                for assistant in self.get_assistant_list()
                if assistant.name == name
            ),
            None,
        )

    def generate_assistant_name(self, assistant: Assistant) -> str:
        """Generate an OpenAI assistant name given an assistant model."""
        return f"{self.reference}-{assistant.name}-{assistant.role}"

    def update_or_create_assistant(self, assistant: Assistant) -> dict:
        """Update or create an OpenAI assistant given an assistant model."""
        name = self.generate_assistant_name(assistant)

        params = {
            "description": f"{assistant.role} for project {self.reference}.",
            "instructions": f"Your name is {assistant.name}. "
            + f"You are a {assistant.role}. {assistant.instructions}",
            "model": os.getenv("ASSISTANT_MODEL", "gpt-4o"),
            "name": name,
            "temperature": float(os.getenv("ASSISTANT_TEMPERATURE", "0.2")),
        }

        openai_assistant = self.get_openai_assistant(assistant)

        if openai_assistant:
            return self._client.beta.assistants.update(openai_assistant.id, **params)

        return self._client.beta.assistants.create(**params)
