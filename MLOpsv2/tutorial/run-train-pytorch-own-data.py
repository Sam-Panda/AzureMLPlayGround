# run-pytorch-data.py
from azure.ai.ml import MLClient, command, Input
from azure.identity import DefaultAzureCredential
from azure.ai.ml.entities import Environment
from azure.ai.ml import command, Input
from azure.ai.ml.entities import Data
from azure.ai.ml.constants import AssetTypes
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

    # the key here should match the key passed to the command
    my_job_inputs = {
        "data_path": Input(type=AssetTypes.URI_FOLDER, path="./data")
    }

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
        # the parameter will match the training script argument name
        # inputs.data_path key should match the dictionary key
        command="python train_pytorch_own_data.py --data_path ${{inputs.data_path}}",
        inputs=my_job_inputs,
        environment=f"{env_name}@latest",
        compute=computeName,
        display_name="day1-experiment-data",
    )

    returned_job = ml_client.create_or_update(job)
    aml_url = returned_job.studio_url
    print("Monitor your job at", aml_url)