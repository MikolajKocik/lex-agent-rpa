#!/bin/bash
export TAVILY_API_KEY=$(az keyvault secret show --name "TavilyApiKey" --vault-name "lex-rpa-keyvault" --query "value" -o tsv)
