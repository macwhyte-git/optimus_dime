# What does this doc do?

The .gitignore file is saved in your project root and is a text file. 

In this text file, writing the folder & file names that you want git to ignore keeps git from picking them up in staging, push, and pull requests

# Example 

# Virtual environment
.venv/

# Secrets
.env

# Python cache
__pycache__/
*.pyc

# Bot data and logs
data/
logs/