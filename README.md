# autoproject

Automatically generate and execute a project plan given a list of goals.
The project planner will create assistants for each goal, and will create tasks for each assistant to achieve the goal.
Tasks can depend on other tasks.

WIP.

# installation

```bash
gh repo clone datashaman/autoproject
cd autoproject
cp .env.example .env
pip install -r requirements.txt
```

Edit your `.env` file to taste. I recommend using a virtual environment.

# usage

```bash
> python -m autoproject --help
usage: __main__.py [-h] [-l LOAD] [-s SAVE] [goals ...]

Create a project plan.

positional arguments:
  goals                 The goals for the project.

options:
  -h, --help            show this help message and exit
  -l LOAD, --load LOAD  Load a project from a file.
  -s SAVE, --save SAVE  Save the project to a file before execution.
```

## project files

Projects are saved and loaded from the projects folder. Don't include the `.json` extension in the filename.

If you are loading a project, the goals will be ignored in favour of the goals in the project file.

The project files are simple JSON, so customizing the generated project plan is easy.

## goals

The goals should generally be quoted. Otherwise each word will become a goal.

For example:

```bash
> python -m autoproject "bake me a cake" "chop me some firewood"
```

# roadmap

- [x] Create a project plan.
- [x] Save and load project plans.
- [x] Create or update OpenAI assistants.
- [ ] Execute project plans.
