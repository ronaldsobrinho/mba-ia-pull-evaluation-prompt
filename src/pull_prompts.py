"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull do prompt semente do desafio
3. Salva localmente em prompts/bug_to_user_story_v1.yml

DICAS DE IMPLEMENTAÇÃO:

- O pull é feito pelo cliente do LangSmith:

      from langsmith import Client
      client = Client()
      prompt = client.pull_prompt(
          "leonanluppi/bug_to_user_story_v1",
          dangerously_pull_public_prompt=True,
      )

- O parâmetro `dangerously_pull_public_prompt=True` é obrigatório sempre que o
  identificador tem dono explícito ("owner/nome"). O LangSmith bloqueia esse pull
  por padrão porque um prompt do Hub é um objeto LangChain serializado, que pode
  vir de terceiros. Aqui o prompt é o do desafio, então o risco é conhecido.

- O retorno é um ChatPromptTemplate. Para extrair o conteúdo das mensagens,
  use a serialização nativa do LangChain (`prompt.messages`, e o atributo
  `.prompt.template` de cada mensagem).

- Use `save_yaml` de utils.py para gravar o resultado no arquivo .yml.
"""

import sys
from pathlib import Path
import yaml
from dotenv import load_dotenv
from langsmith import Client
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()


PROMPT_ID = "leonanluppi/bug_to_user_story_v1"
PROMPT_KEY = "bug_to_user_story_v1"
# O prompt no Hub não tem descrição; usa a do YAML original do repositório
DEFAULT_DESCRIPTION = "Prompt para converter relatos de bugs em User Stories"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "prompts" / f"{PROMPT_KEY}.yml"

# Tipo da mensagem no LangChain -> campo no YAML
MESSAGE_FIELDS = {
    "SystemMessagePromptTemplate": "system_prompt",
    "HumanMessagePromptTemplate": "user_prompt",
}


def _str_representer(dumper, value):
    """Grava textos de várias linhas em bloco (|), legível no arquivo."""
    style = "|" if "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


# save_yaml (utils.py) usa yaml.dump; o representer vale para essa chamada
yaml.add_representer(str, _str_representer)


def pull_prompts_from_langsmith():
    """
    Faz o pull do prompt semente no LangSmith Hub e devolve os dados no
    formato do YAML ({PROMPT_KEY: {description, system_prompt, user_prompt, ...}}).
    """
    client = Client()

    print(f"Puxando prompt do LangSmith Hub: {PROMPT_ID}")
    prompt = client.pull_prompt(PROMPT_ID, dangerously_pull_public_prompt=True)

    data = {}
    for message in prompt.messages:
        field = MESSAGE_FIELDS.get(type(message).__name__)
        if field is None:
            print(f"⚠️  Mensagem ignorada (tipo não suportado): {type(message).__name__}")
            continue
        data[field] = message.prompt.template

    # Descrição e tags vêm do registro do prompt no Hub (não do template)
    description = ""
    tags = []
    try:
        hub_prompt = client.get_prompt(PROMPT_ID)
        if hub_prompt is not None:
            description = hub_prompt.description or ""
            tags = list(hub_prompt.tags or [])
    except Exception as e:
        print(f"⚠️  Não foi possível ler descrição/tags do Hub: {e}")

    prompt_data = {
        "description": description or DEFAULT_DESCRIPTION,
        "system_prompt": data.get("system_prompt", ""),
        "user_prompt": data.get("user_prompt", ""),
        "input_variables": list(prompt.input_variables),
        "version": "v1",
        "source": PROMPT_ID,
        "tags": tags,
    }
    return {PROMPT_KEY: prompt_data}


def main():
    """Função principal"""
    print_section_header("PULL DO PROMPT SEMENTE (LangSmith Hub)")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    try:
        prompts = pull_prompts_from_langsmith()
    except Exception as e:
        print(f"❌ Erro ao fazer pull do prompt: {e}")
        return 1

    prompt_data = prompts[PROMPT_KEY]
    if not prompt_data["system_prompt"]:
        print("❌ O prompt veio sem system prompt — nada foi gravado.")
        return 1

    if not save_yaml(prompts, str(OUTPUT_PATH)):
        return 1

    print(f"✓ Prompt salvo em {OUTPUT_PATH.relative_to(OUTPUT_PATH.parent.parent)}")
    print(f"  Variáveis: {', '.join(prompt_data['input_variables'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
