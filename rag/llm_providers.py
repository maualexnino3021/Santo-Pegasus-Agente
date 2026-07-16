"""
llm_providers.py
----------------
Capa de abstracción sobre el proveedor de modelo de lenguaje, para poder
usar Claude (Anthropic) u OpenAI de forma intercambiable, seleccionado por
la variable de entorno LLM_PROVIDER.

Ambos providers exponen la misma interfaz:
    complete(system_prompt: str, user_message: str, max_tokens: int) -> str
"""
import os


class AnthropicProvider:
    """Usa la API de Anthropic (Claude)."""

    def __init__(self):
        import anthropic

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Falta la variable de entorno ANTHROPIC_API_KEY. "
                "Configúrala en tu .env local o en las variables de entorno de Render."
            )
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-5")

    def complete(self, system_prompt: str, user_message: str, max_tokens: int = 1024) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return "".join(block.text for block in response.content if block.type == "text")


class OpenAIProvider:
    """Usa la API de OpenAI (GPT)."""

    def __init__(self):
        from openai import OpenAI

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Falta la variable de entorno OPENAI_API_KEY. "
                "Configúrala en tu .env local o en las variables de entorno de Render."
            )
        self.client = OpenAI(api_key=api_key)
        self.model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    def complete(self, system_prompt: str, user_message: str, max_tokens: int = 1024) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        return response.choices[0].message.content or ""


def get_llm_provider():
    """
    Devuelve la instancia del provider configurado vía la variable de entorno
    LLM_PROVIDER ('anthropic' u 'openai'). Por defecto usa 'anthropic'.
    """
    provider_name = os.environ.get("LLM_PROVIDER", "anthropic").strip().lower()

    if provider_name == "openai":
        return OpenAIProvider()
    elif provider_name == "anthropic":
        return AnthropicProvider()
    else:
        raise RuntimeError(
            f"LLM_PROVIDER='{provider_name}' no es válido. Usa 'anthropic' u 'openai'."
        )
