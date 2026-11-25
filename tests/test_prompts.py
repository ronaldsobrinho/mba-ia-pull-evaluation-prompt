"""
Testes automatizados para validação de prompts.
"""
import re
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


@pytest.fixture(scope="module")
def prompt():
    """Dados do prompt otimizado (v2)."""
    data = load_prompts(str(PROMPT_FILE))
    assert PROMPT_KEY in data, f"Chave '{PROMPT_KEY}' ausente em {PROMPT_FILE.name}"
    return data[PROMPT_KEY]


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt
        assert isinstance(prompt["system_prompt"], str)
        assert prompt["system_prompt"].strip()

    def test_prompt_has_role_definition(self, prompt):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        system_prompt = prompt["system_prompt"]
        assert re.search(r"\bVocê é uma? ", system_prompt), "Persona ausente ('Você é um ...')"
        assert "Product Manager" in system_prompt

    def test_prompt_mentions_format(self, prompt):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system_prompt = prompt["system_prompt"]
        # Formato da User Story: "Como um <persona>, eu quero <objetivo>, para que <benefício>"
        for trecho in ("Como um", "eu quero", "para que"):
            assert trecho in system_prompt, f"Formato da User Story sem '{trecho}'"
        # Critérios de aceitação em Given/When/Then
        assert "Critérios de Aceitação" in system_prompt
        for trecho in ("Dado que", "Quando", "Então"):
            assert trecho in system_prompt, f"Critérios sem '{trecho}'"

    def test_prompt_has_few_shot_examples(self, prompt):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system_prompt = prompt["system_prompt"]
        entradas = system_prompt.count("Entrada:")
        saidas = system_prompt.count("Saída:")
        assert entradas >= 2, f"Few-shot pede pelo menos 2 exemplos; encontrados {entradas}"
        assert entradas == saidas, "Todo exemplo precisa de Entrada e Saída"

    def test_prompt_no_todos(self, prompt):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        for campo in ("description", "system_prompt", "user_prompt"):
            assert "TODO" not in str(prompt.get(campo, "")), f"TODO encontrado em '{campo}'"

    def test_minimum_techniques(self, prompt):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt.get("techniques_applied", [])
        assert len(techniques) >= 2, f"Mínimo de 2 técnicas; encontradas {len(techniques)}"
        assert "Few-shot Learning" in techniques, "Few-shot é obrigatório no desafio"

        is_valid, errors = validate_prompt_structure(prompt)
        assert is_valid, f"Estrutura inválida: {errors}"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])