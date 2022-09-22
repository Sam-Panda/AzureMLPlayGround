# import required libraries
import os
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential
from azure.ai.ml import MLClient, Input, Output, command, load_component
from azure.ai.ml.dsl import pipeline
from azure.ai.ml.constants import AssetTypes
from setuptools import Command



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

# 2 transforming the data


transform_data_component = command(
    name="taxi data feature engineering",
    display_name="TaxiFeatureEngineering",
    inputs={
        "clean_data" : Input(type="uri_folder")
    },
    outputs=dict(
        transformed_data=Output(type="uri_folder", mode="rw_mount")
    ),
    # The source folder of the component
    code="./transform_src",
    command="""python transform.py \
            --clean_data ${{inputs.clean_data}}  \
            --transformed_data ${{outputs.transformed_data}} \
            """,
    environment=f"AzureML-sklearn-0.24-ubuntu18.04-py37-cpu@latest",
    is_deterministic= False    

)

# 3 train model with the transformeed data

train_model = command(
    name="taxi_feature_engineering",
    display_name="TaxiFeatureEngineering",
    inputs={
        "training_data" : Input(type="uri_folder")
    },
    outputs=dict(
        model_output= Output(type="mlflow_model", mode="rw_mount"),
        test_data= Output(type="uri_folder", mode="rw_mount")
    ),
    # The source folder of the component
    code="./train_src",
    command="""python train.py \
            --training_data ${{inputs.training_data}}  \
            --test_data ${{outputs.test_data}}  \
            --model_output ${{outputs.model_output}} \
            """,
    environment=f"AzureML-sklearn-0.24-ubuntu18.04-py37-cpu@latest",
    is_deterministic= False   
)

# 4. prediction 

predict_result = command(
    name="predict_taxi_fares",
    display_name="PredictTaxiFares",
    version="1",
    inputs={
        "test_data" : Input(type="uri_folder"),
        "model_input" : Input(type="mlflow_model")
    },
    outputs=dict(
        predictions= Output(type="uri_folder", mode="rw_mount")
    ),
    # The source folder of the component
    code="./predict_src",
    command="""python predict.py \
            --test_data ${{inputs.test_data}}  \
            --model_input ${{inputs.model_input}}  \
            --predictions ${{outputs.predictions}} \
            """,
    environment=f"AzureML-sklearn-0.24-ubuntu18.04-py37-cpu@latest",
    is_deterministic= False  
)

# 5. Scoring
score_data = command(

    name="score_model",
    display_name="ScoreModel",
    version="1",
    inputs={
        "predictions" : Input(type="uri_folder"),
        "model" : Input(type="mlflow_model")
    },
    outputs=dict(
        score_report= Output(type="uri_folder", mode="rw_mount")
    ),
    # The source folder of the component
    code="./score_src",
    command="""python score.py \
            --predictions ${{inputs.predictions}}  \
            --model ${{inputs.model}}  \
            --score_report ${{outputs.score_report}} \
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
    transform_sample_data = transform_data_component(
        clean_data=prepare_sample_data.outputs.prep_data
        )
    train_with_sample_data = train_model(
        training_data=transform_sample_data.outputs.transformed_data
    )
    predict_with_sample_data = predict_result(
        model_input=train_with_sample_data.outputs.model_output,
        test_data=train_with_sample_data.outputs.test_data,
    )
    score_with_sample_data = score_data(
        predictions=predict_with_sample_data.outputs.predictions,
        model=train_with_sample_data.outputs.model_output,
    )
    # a pipeline returns a dictionary of outputs
    # keys will code for the pipeline output identifier
    return {
         "pipeline_job_prepped_data": prepare_sample_data.outputs.prep_data,
         "pipeline_job_transformed_data": transform_sample_data.outputs.transformed_data,
         "pipeline_job_trained_model": train_with_sample_data.outputs.model_output,
         "pipeline_job_test_data": train_with_sample_data.outputs.test_data,
         "pipeline_job_predictions": predict_with_sample_data.outputs.predictions,
         "pipeline_job_score_report": score_with_sample_data.outputs.score_report
        
    }

pipeline_job = nyc_taxi_data_regression()
pipeline_job.settings.default_datastore = "blob_example"
# submit job to workspace
pipeline_job = ml_client.jobs.create_or_update(
    pipeline_job, experiment_name="pipeline_samples 1"
)
pipeline_job