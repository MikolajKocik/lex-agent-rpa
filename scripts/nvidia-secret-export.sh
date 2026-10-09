#!/bin/bash
export NVIDIA_API_KEY=$(az keyvault secret show --name "NvidiaApiKey" --vault-name "lex-rpa-keyvault" --query "value" -o tsv)
