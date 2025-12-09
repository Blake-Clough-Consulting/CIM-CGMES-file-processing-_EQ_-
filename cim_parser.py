import os

EXCLUDE = {"__pycache__", ".git", ".venv"}

def print_tree(root, prefix=""):
    items = [i for i in os.listdir(root) if i not in EXCLUDE]
    for i, name in enumerate(sorted(items)):
        path = os.path.join(root, name)
        is_last = i == len(items) - 1
        branch = "└── " if is_last else "├── "
        print(prefix + branch + name)
        if os.path.isdir(path):
            new_prefix = prefix + ("    " if is_last else "│   ")
            print_tree(path, new_prefix)

print_tree(".")