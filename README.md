## Setup WSL2 environment

#### Install ollama

```sh
curl -fsSL https://ollama.com/install.sh | sh
```

#### Pull LLMs

```sh
ollama pull deepseek-r1:7b
ollama pull deepseek-r1:8b
ollama pull qwen2.5-coder:7b
ollama pull qwen3:8b
ollama pull gemma3:4b
```

#### Install mailpit

```sh
curl -sL https://raw.githubusercontent.com/axllent/mailpit/develop/install.sh | sh
```

#### Start mailpit

```sh
nohup mailpit --database /var/lib/mailpit/mailpit.db --pop3-auth-file /var/lib/mailpit/passwords > /var/log/mailpit/mailpit.log 2>&1 &
```

#### Send mail

```sh
mailpit sendmail << EOF
Subject: NEW PROJECT: <<<Put the project name here>>>
From: cto@human.local
To: manager@ai-crew.local

<<<Put the project description here>>>

EOF
```
