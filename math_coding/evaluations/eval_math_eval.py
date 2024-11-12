import os
import sys
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
from azure.ai.projects.models import Evaluation, Dataset, EvaluatorConfiguration, ConnectionType
from pathlib import Path
from azure.ai.evaluation import evaluate
import json
from azure.ai.evaluation import F1ScoreEvaluator
from azure.identity import DefaultAzureCredential

current_dir = os.path.dirname(os.path.abspath(__file__))  # evaluations folder
parent_dir = os.path.dirname(current_dir)  # math_coding folder
sys.path.insert(0, parent_dir)


from orchestration.python.pure_python_flow import get_math_response
from dotenv import load_dotenv


sys.path.append(current_dir)

load_dotenv()



def eval_run_eval(name, data_path, column_mapping, output_path ):
    project = AIProjectClient.from_connection_string(conn_str= os.environ["CONNECTION_STRING"], credential=DefaultAzureCredential())
    f1score = F1ScoreEvaluator()
    result = evaluate(
        data="math_coding/data/math_data.jsonl",
        target=get_math_response,
        evaluation_name="evaluate_chat_with_products",
        evaluators={
            "f1_score": f1score,
        },
        evaluator_config={
            "default": {
                "column_mapping": dict(column_mapping)
            }
        },
        azure_ai_project=project.scope,
        output_path=f"{output_path}/{name}.json",
    )
    print(result)
    return result
    
