# Welcome to xRx
**Any modality input (x), reasoning (R), any modality output (x).**

xRx is a framework for building AI-powered applications that interact with users across multiple modalities.

This repository contains the reasoning applications built on top of the xRx framework.

The reasoning systems process input, generate responses and manage the overall conversation flow within the xRx framework. Each subdirectory in this folder represents a different application, including a specific reasoning agent and an UI.

## Available Reasoning Applications
1. [Simple App](./simple-app): A simple template for creating custom reasoning apps.
2. [Shopify App](./shopify-app): An app designed to handle app-based interactions with a Shopify store.
3. [Wolfram Assistant App](./wolfram-assistant-app): An app designed to handle math and physics-based interactions.
4. [Patient Information App](./patient-information-app): An app designed to collect and manage patient information before a doctor's visit.

## Usage
To get started with xRx, follow these steps:

1. Clone the repository with its submodules using the following command:

   ```
   git clone --recursive https://github.com/8090-inc/xrx-sample-apps.git
   ```
   It's crucial to include the `--recursive` flag when cloning, as each application is built on top of a git submodule called `xrx-core`. This submodule contains the fundamental building blocks for the xRx framework.

2. Navigate to the cloned repository:

   ```
   cd xrx-sample-apps
   ```

3. To use a specific reasoning application:
   - Navigate to the specific folder
   - Set the `.env` variables
   - Run the `docker compose` command
   - Each application has its own set of environment variables. Refer to the `.env.example` file in each application's directory for the required variables.

    > **Note:** We suggest opening only that specific folder in your IDE for a cleaner workspace.

4. Continue following the instructions in the README file of the specific application you are interested in.

For more detailed information on how to implement and use these reasoning systems, please refer to the README files within each application's subdirectory.

## Contributing
We welcome contributions to the xRx framework and its sample applications. If you have any suggestions or improvements, please follow these steps:

1. Open a new issue on GitHub describing the proposed change or improvement
2. Fork the repository
3. Create a new branch for your feature
4. Commit your changes
5. Push to your branch
6. Create a pull request, referencing the issue you created

> **Note:** Pull requests not backed by published issues will not be considered. This process ensures that all contributions are discussed and aligned with the project's goals before implementation.

## GitHub Actions Workflow

This project uses a GitHub Actions workflow to automatically build and test Docker Compose projects in each subdirectory of the repository.

### Workflow Details

The workflow is defined in `.github/workflows/build-docker-compose.yml` and does the following:

1. Triggers on:
   - Push to `main` or `test-workflow` branches
   - Pull requests to `main` branch
   - Manual dispatch

2. For each subdirectory in the repository root:
   - Builds the Docker Compose project
   - Starts the containers
   - Stops and removes the containers

### Testing the Workflow

To test the GitHub Actions workflow:

1. **Push to test-workflow branch**: Make changes and push to the `test-workflow` branch to trigger the workflow.

2. **Create a Pull Request**: Open a PR to the `main` branch to trigger the workflow.

3. **Manual Trigger**: 
   - Go to the Actions tab in the GitHub repository
   - Select "Build Docker Compose Projects" workflow
   - Click "Run workflow" and select the branch to run on

4. **Local Testing with Act**:
   If you have [Act](https://github.com/nektos/act) installed, you can test locally:
   ```
   act push
   ```

### Workflow Configuration

The workflow uses the following Docker Compose flags:
- `--build`: Build images before starting containers
- `--no-cache`: Do not use cache when building images
- `--force-recreate`: Recreate containers even if their configuration hasn't changed
- `--renew-anon-volumes`: Recreate anonymous volumes
- `--remove-orphans`: Remove containers for services not defined in the Compose file

### Debugging

The workflow has debug logging enabled. Check the workflow run logs in the GitHub Actions tab for detailed output.

## Project Structure

Ensure each subdirectory that should be built has a valid `docker-compose.yml` file.