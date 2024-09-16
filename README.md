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