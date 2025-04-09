azure_openai = {
  aoai1 = {
    sku_name = "S0"
  }
}

azure_openai_deployments = {
  aoai1 = {
    gpt4o = {
    deployment_name = "gpt-4o-may"
    model_name      = "gpt-4o"
    model_version   = "2024-05-13"
    scale_type      = "GlobalStandard"
  }
    gpt4o-2 = {
    deployment_name = "gpt-4oaugust"
    model_name      = "gpt-4o"
    model_version   = "2024-08-06"
    scale_type      = "GlobalStandard"
  }

    embedding = {
      deployment_name = "embedding"
      model_name      = "text-embedding-ada-002"
      model_version   = "2"
      scale_type      = "Standard"
    }
  }
}
