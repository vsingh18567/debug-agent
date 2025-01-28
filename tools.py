from dataclasses import dataclass
import subprocess


@dataclass
class Property:
    description: str
    type: str
    required: bool

    def to_dict(self):
        return {
            "description": self.description,
            "type": self.type,
        }


@dataclass
class Tool:
    name: str
    description: str
    function: callable
    properties: dict[str, Property]

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {k: v.to_dict() for k, v in self.properties.items()},
                "required": [k for k, v in self.properties.items() if v.required],
            },
        }

    def call(self, input: dict):
        return self.function(**input)


def subproc_tool(command: str):
    print(f"TOOL: Running command: {command}")
    process = subprocess.run(command, shell=True, capture_output=True, text=True)
    if process.returncode != 0:
        print(f"TOOL: Command failed with return code {process.returncode}")
        print(f"TOOL: Command output: {process.stdout}")
        print(f"TOOL: Command error: {process.stderr}")
    return {
        "stdout": process.stdout,
        "stderr": process.stderr,
        "returncode": process.returncode,
    }


def python_tool(file_path: str, args: str):
    COMMAND = f"python {file_path} {args}"
    print(f"Agent is trying to run {COMMAND}. Do you want to proceed? [y/N]")
    if input() == "y":
        return subproc_tool(COMMAND)
    else:
        return {"error": "User declined to run command"}


def ls_tool(path: str = "."):
    return subproc_tool(f"ls {path}")


def read_tool(file_path: str):
    with open(file_path, "r") as file:
        return file.read()


def write_tool(file_path: str, content: str):
    with open(file_path, "w") as file:
        file.write(content)
    return {"returncode": 0}


def pip_tool(package: str):
    print(f"Agent is trying to install {package}. Do you want to proceed? [y/N]")
    if input() == "y":
        return subproc_tool(f"pip install {package}")
    else:
        return {"error": "User declined to install package"}


TOOLS = [
    Tool(
        name="python_tool",
        description="Run a python script with arguments. The script will be executed in the current working directory in the format python <file_path> <args>. The user will be prompted to confirm the execution.",
        function=python_tool,
        properties={
            "file_path": Property(
                description="The path to the python script",
                type="string",
                required=True,
            ),
            "args": Property(
                description="The arguments to pass to the python script",
                type="string",
                required=True,
            ),
        },
    ),
    Tool(
        name="ls_tool",
        description="Run the ls command from the current working directory",
        function=ls_tool,
        properties={
            "path": Property(
                description="The path to list files from", type="string", required=False
            )
        },
    ),
    Tool(
        name="read_tool",
        description="Read the contents of a file from the current working directory",
        function=read_tool,
        properties={
            "file_path": Property(
                description="The path to the file", type="string", required=True
            )
        },
    ),
    Tool(
        name="write_tool",
        description="Write to a file in the current working directory",
        function=write_tool,
        properties={
            "file_path": Property(
                description="The path to the file", type="string", required=True
            ),
            "content": Property(
                description="The content to write to the file",
                type="string",
                required=True,
            ),
        },
    ),
    Tool(
        name="pip_tool",
        description="Install a python package in the current environment. The user will be prompted to confirm the installation.",
        function=pip_tool,
        properties={
            "package": Property(
                description="The name of the package", type="string", required=True
            )
        },
    ),
]
