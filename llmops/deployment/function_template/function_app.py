import azure.functions as func

# Import blueprints
from function_processor.function_orchestrator import bp as orchestration_executor

# Create the function app
app = func.FunctionApp()

# Register blueprints
app.register_functions(orchestration_executor)
