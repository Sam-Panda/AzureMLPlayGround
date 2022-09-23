# import required libraries
import os
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential
from azure.ai.ml import MLClient, Input, Output, command, load_component
from azure.ai.ml.dsl import pipeline
from azure.ai.ml.constants import AssetTypes
from setuptools import Command
from azure.ai.ml.entities import Environment


# Configure Credential 

try:
    credential = DefaultAzureCredential()
    # Check if given credential can get token successfully.
    credential.get_token("https://management.azure.com/.default")
except Exception as ex:
    # Fall back to InteractiveBrowserCredential in case DefaultAzureCredential not work
    credential = InteractiveBrowserCredential()


# Get a handle to workspace
ml_client = MLClient.from_config(credential=credential)

# Retrieve an already attached Azure Machine Learning Compute.
cluster_name = "cpu-cluster"
print(ml_client.compute.get(cluster_name))


# create the environment



custom_env_name = "nyc-taxi-regression-env"

pipeline_job_env = Environment(
    name=custom_env_name,
    description="Custom environment for nyc taxi fare regression",
    tags={"scikit-learn": "0.24.2"},
    conda_file=os.path.join("./dependencies", "conda.yml"),
    image="mcr.microsoft.com/azureml/openmpi3.1.2-ubuntu18.04:latest",
    version="1.0",
)
pipeline_job_env = ml_client.environments.create_or_update(pipeline_job_env)

print(
    f"Environment with name {pipeline_job_env.name} is registered to workspace, the environment version is {pipeline_job_env.version}"
)

