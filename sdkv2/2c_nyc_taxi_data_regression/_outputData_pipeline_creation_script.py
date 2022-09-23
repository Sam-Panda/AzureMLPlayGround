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


# creation of the pipeline 

# 1. data prep

data_prep_src_dir = "./prep_src"
os.makedirs(data_prep_src_dir, exist_ok=True)

data_prep_component = command(
    name="data_prep_nyc_taxi",
    display_name="Data preparation (prepare_taxi_data)",
    description="read the input data, and creates the red and yellow data",
    inputs={
        "raw_data" : Input(type="uri_folder")
    },
    outputs=dict(
        prep_data=Output(type="uri_folder", mode="rw_mount", path = "azureml://datastores/blob_example/paths/nyctaxiexample/output1" )
    ),
    # The source folder of the component
    code=data_prep_src_dir,
    command="""python prep.py \
            --raw_data ${{inputs.raw_data}}  \
            --prep_data ${{outputs.prep_data}} \
            """,
    environment=f"AzureML-sklearn-0.24-ubuntu18.04-py37-cpu@latest",
    is_deterministic= False
)

# the dsl decorator tells the sdk that we are defining an Azure ML pipeline
@pipeline(
    compute="cpu-cluster",
    description="E2E data_perp-train pipeline",
)
def nyc_taxi_data_regression(
    
):
    # using data_prep_function like a python call with its own inputs
    data_prep_input = Input(type=AssetTypes.URI_FOLDER, path="azureml://datastores/blob_example/paths/nyctaxiexample")
    prepare_sample_data = data_prep_component(
        raw_data=data_prep_input
        )
    
    # a pipeline returns a dictionary of outputs
    # keys will code for the pipeline output identifier
    return {
         "pipeline_job_prepped_data": prepare_sample_data.outputs.prep_data
        
    }

pipeline_job = nyc_taxi_data_regression()
pipeline_job.settings.default_datastore = "blob_example"
# submit job to workspace
pipeline_job = ml_client.jobs.create_or_update(
    pipeline_job, experiment_name="pipeline_samples Output 1"
)
pipeline_job