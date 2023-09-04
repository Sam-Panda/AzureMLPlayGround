from azure.ai.ml import MLClient
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
import os
load_dotenv()

subscription_id = os.environ['AZURE_SUBSCRIPTION_ID']
resource_group = os.environ['AZURE_RESOURCE_GROUP']
workspace = os.environ['AZURE_ML_WORKSPACE']


ml_client = MLClient(
    DefaultAzureCredential(), subscription_id, resource_group, workspace
)
ml_client