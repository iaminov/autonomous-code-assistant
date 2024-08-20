# Autonomous Code Assistant

## Overview

The **Autonomous Code Assistant** is an advanced AI-powered coding companion designed to enhance developer productivity with intelligent code generation, analysis, review, refactoring, and documentation capabilities. Built with modern Python practices, it supports multiple LLM (Large Language Model) providers like OpenAI, ensuring flexible and comprehensive coding aid.

## Features

- **Code Generation**: Generate code snippets or entire functions from contextual instructions.
- **Code Review**: Analyze code files for best practices, performance improvements, and security vulnerabilities.
- **Refactoring**: Refactor code following specific instructions to enhance readability and maintainability.
- **Documentation**: Automatically generate comprehensive documentation for code, following standard conventions.
- **File Operations**: Secure reading and writing with auto-backup and smart encoding detection.
- **Advanced CLI**: Rich, interactive command-line interface with progress tracking, syntax highlighting, and helpful outputs.

## Installation

Clone the repository and navigate into it:

```bash
$ git clone https://github.com/iaminov/autonomous-code-assistant.git
$ cd autonomous-code-assistant
```

Install using pip:

```bash
$ pip install .
```

## Usage

### CLI Interface

The assistant can be used directly via a modern command-line interface:

```bash
$ aca --provider openai generate "Calculate Fibonacci series."
$ aca review path/to/file.py
$ aca refactor path/to/file.py "Use list comprehension for looping."
$ aca analyze --include "*.py"
$ aca document path/to/module.py
```

### Help

Run the following for a full list of commands:

```bash
$ aca --help
```

## Configuration

Create a `.env` file to manage environment variables such as API keys:

```ini
OPENAI_API_KEY=your_openai_api_key_here
```

Ensure the API key is set for the provider you intend to use.

## Development

Install development dependencies:

```bash
$ pip install .[dev]
```
Run tests:

```bash
$ pytest
```

## Contributing

Feel free to submit issues and enhancement requests. Pull requests are also welcome.

## License

[MIT License](LICENSE)

## Acknowledgments
- Developed and maintained by [iaminov](mailto:alexeaminov@gmail.com).
- Utilizes OpenAI's GPT models for natural language processing capabilities.

