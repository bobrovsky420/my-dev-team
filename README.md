## Setup WSL2 environment

#### Install ollama

```sh
curl -fsSL https://ollama.com/install.sh | sh
```

#### Pull LLMs

```sh
ollama pull deepseek-r1:7b
ollama pull qwen2.5-coder:7b
ollama pull gemma3:4b
```

#### Install mailpit

```sh
curl -sL https://raw.githubusercontent.com/axllent/mailpit/develop/install.sh | bash
```

#### Start mailpit

```sh
nohup mailpit --database /var/lib/mailpit/mailpit.db > /var/log/mailpit/mailpit.log 2>&1 &
```
