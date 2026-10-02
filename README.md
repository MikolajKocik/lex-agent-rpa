# lex-agent-rpa

## Description
...

> [!NOTE]
> If you have a machine with a dedicated GPU (16+ GB VRAM), you can self-host an NVIDIA NIM model locally via Docker Compose.
> For details, see the [NVIDIA Compose Reference](https://docs.nvidia.com/ai-workbench/user-guide/latest/reference/projects/compose-reference.html).

### Configure Docker registry authentication (Linux)
> [!IMPORTANT]
> By default on Linux, Docker stores credentials in plain text (unencrypted base64) inside `~/.docker/config.json`.
> If you are a Linux user, run the helper script to securely store your registry credentials in an encrypted `pass` (GPG) credential store:

```bash
chmod +x setup-docker-pass.sh
./setup-docker-pass.sh
```

### Export secrets from Azure Key Vault
```bash
source ./nvidia-secret-export.sh
source ./postgres-secret-export.sh
```

### Delete azure resources with IaC approach
```bash
cd src/infrastructure/templates 
terraform destroy
```

### Run application stack (API + PostgreSQL)
```bash
docker compose up -d
```

### Run tests in Docker
```bash
docker compose run --rm tests
```

