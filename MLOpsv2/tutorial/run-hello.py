# get-started/run-hello.py
from azure.ai.ml import MLClient, command, Input
from azure.identity import DefaultAzureCredential
from azureml.core import Workspace

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

# target name of compute where job will be executed
computeName="cpu-cluster"
job = command(
    code="./src/hello.py",
    command="python hello.py",
    environment="AzureML-sklearn-0.24-ubuntu18.04-py37-cpu@latest",
    compute=computeName,
    display_name="hello-world-example",
)

returned_job = ml_client.create_or_update(job)
aml_url = returned_job.studio_url
print("Monitor your job at", aml_url)