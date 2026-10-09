#!/bin/bash
export POSTGRES_PASSWORD=$(az keyvault secret show --name "PostgresPassword" --vault-name "lex-rpa-keyvault" --query "value" -o tsv)
