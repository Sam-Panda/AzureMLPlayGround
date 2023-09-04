import os 
import json
from dotenv import load_dotenv

load_dotenv()

subscription_id = os.environ['AZURE_SUBSCRIPTION_ID']
resource_group = os.environ['AZURE_RESOURCE_GROUP']+"new040923"


# get a handle to the subscription

from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential

ml_client = MLClient(DefaultAzureCredential(), subscription_id, resource_group)

# Creating a unique workspace name with current datetime to avoid conflicts
from azure.ai.ml.entities import Workspace
import datetime

basic_workspace_name = "mlw-basic-prod-" + datetime.datetime.now().strftime(
    "%Y%m%d%H%M"
)

ws_basic = Workspace(
    name=basic_workspace_name,
    location="eastus",
    display_name="Basic workspace-example",
    description="This example shows how to create a basic workspace",
    hbi_workspace=False,
    tags=dict(purpose="demo"),
)

ws_basic = ml_client.workspaces.begin_create(ws_basic).result()
print(ws_basic)