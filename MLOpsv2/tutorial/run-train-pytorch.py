# run-pytorch.py
from azure.ai.ml import MLClient, command, Input
from azure.identity import DefaultAzureCredential
from azure.ai.ml.entities import Environment
from azureml.core import Workspace

if __name__ == "__main__":
    # get details of the current Azure ML workspace
    ws = Workspace.from_config()

    # default authentication flow for Azure applications
    default_azure_credential = DefaultAzureCredential()
    subscription_id = ws.subscription_id
    resource_group = ws.resource_group
    workspace = ws.name

    # client class to interact with Azure ML services and resources, e.g. workspaces, jobs, models and so on.
    ml_client = MLClient(
        default_azure_credential,
        subscription_id,
        resource_group,
        workspace)

    env_name = "pytorch-env"
    env_docker_image = Environment(
        image="pytorch/pytorch:latest",
        name=env_name,
        conda_file="pytorch-env.yml",
    )
    ml_client.environments.create_or_update(env_docker_image)

    # target name of compute where job will be executed
    computeName="cpu-cluster"
    job = command(
        code="./src",
        command="python train_pytorch.py",
        environment=f"{env_name}@latest",
        compute=computeName,
        display_name="day1-experiment-train",
    )

    returned_job = ml_client.create_or_update(job)
    aml_url = returned_job.studio_url
    print("Monitor your job at", aml_url)