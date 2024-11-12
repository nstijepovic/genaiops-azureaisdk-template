import os
import sys
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.evaluation import evaluate
from azure.ai.evaluation import F1ScoreEvaluator
from dotenv import load_dotenv

load_dotenv()

current_dir = os.path.dirname(os.path.abspath(__file__))  
parent_dir = os.path.dirname(current_dir)  
sys.path.insert(0, parent_dir)
sys.path.append(current_dir)

from orchestration.python.pure_python_flow import get_math_response


def eval_run_eval(name, data_path, column_mapping, output_path ):
    """
    Evaluate the model using the given data and column mapping.
    """
    project = AIProjectClient.from_connection_string(
        conn_str=os.environ["CONNECTION_STRING"],
        credential=DefaultAzureCredential()
    )
    f1score = F1ScoreEvaluator()
    result = evaluate(
        data=data_path,
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
    return result
    
