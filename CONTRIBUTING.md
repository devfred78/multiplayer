# How to Contribute to Multiplayer

We're thrilled that you're interested in contributing to the `multiplayer` project! Your help is greatly appreciated. By contributing, you can help make this library even better.

Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

## Table of Contents
* [Reporting Bugs](#reporting-bugs)
* [Suggesting Enhancements](#suggesting-enhancements)
* [Your First Code Contribution](#your-first-code-contribution)
* [Pull Request Process](#pull-request-process)

## Reporting Bugs

If you find a bug, please ensure the bug was not already reported by searching on GitHub under [Issues](https://github.com/devfred78/multiplayer/issues).

If you're unable to find an open issue addressing the problem, [open a new one](https://github.com/devfred78/multiplayer/issues/new). Be sure to include a **title and clear description**, as much relevant information as possible, and a **code sample** or an **executable test case** demonstrating the expected behavior that is not occurring.

## Suggesting Enhancements

If you have an idea for a new feature or an improvement to an existing one, please open an issue to discuss it. This allows us to coordinate our efforts and avoid duplicated work.

1.  Search the [issues](https://github.com/devfred78/multiplayer/issues) to see if the enhancement has already been suggested.
2.  If not, [open a new issue](https://github.com/devfred78/multiplayer/issues/new), providing a clear and detailed description of the proposed enhancement and its benefits.

## Your First Code Contribution

Ready to contribute code? Here’s how to set up `multiplayer` for local development.

1.  **Fork the repository** on GitHub.
2.  **Clone your fork** locally:
    ```sh
    git clone https://github.com/devfred78/multiplayer.git
    ```
3.  **Set up your environment.** We recommend using a virtual environment:
    ```sh
    cd multiplayer
    python -m venv .venv
    source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
    ```
4.  **Install the dependencies**, including the development and testing tools:
    ```sh
    pip install -e .[dev]
    ```
5.  **Create a new branch** for your changes:
    ```sh
    git checkout -b name-of-your-feature-or-fix
    ```
6.  Make your changes!

## Pull Request Process

1.  Ensure that your code adheres to the existing style to maintain consistency.
2.  Run the tests to make sure your changes don't break anything:
    ```sh
    pytest
    ```
3.  Add new tests for your feature if applicable.
4.  Update the documentation (`README.md`, `REFERENCE.md`, etc.) if you've changed the API or added new features.
5.  Commit your changes with a clear and descriptive commit message.
6.  Push your branch to your fork on GitHub:
    ```sh
    git push origin name-of-your-feature-or-fix
    ```
7.  **Submit a Pull Request** to the `main` branch of the original `multiplayer` repository. Provide a clear title and description for your PR, explaining the "what" and "why" of your changes.

Thank you for your contribution!
