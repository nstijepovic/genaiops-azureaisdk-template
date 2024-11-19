import logging
import os
import azure.functions as func
import json
from typing import Dict, Any


# Blueprint creation
bp = func.Blueprint()


@bp.route(route="process-math")
def process_math(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP Trigger handler that coordinates the request/response flow
    and delegates business logic to pure_python_flow.py
    """
    try:
        # 1. Request handling
        #enable_telemetry(True)
        question = req.params.get('question')
        
        # 2. Input validation
        if not question:
            return func.HttpResponse(
                body=json.dumps({"error": "Request body is required"}),
                mimetype="application/json",
                status_code=400
            )

        # 3. Import and execute business logic
        try:
            from . import pure_python_flow
            result = pure_python_flow.get_math_response(question)
        except ImportError as ie:
            logging.error(f"Failed to import pure_python_flow: {str(ie)}")
            return func.HttpResponse(
                body=json.dumps({"error": "Business logic module not available"}),
                mimetype="application/json",
                status_code=500
            )

        # 4. Response handling
        return func.HttpResponse(
            body=json.dumps(result),
            mimetype="application/json",
            status_code=200
        )

    except ValueError as ve:
        return func.HttpResponse(
            body=json.dumps({"error": f"Invalid request format: {str(ve)}"}),
            mimetype="application/json",
            status_code=400
        )
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"error": "Internal server error"}),
            mimetype="application/json",
            status_code=500
        )

