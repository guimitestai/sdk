"""Integração com LangSmith para rastreamento e avaliação."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional


class LangSmithIntegration:
    """Integração com LangSmith para rastreamento e avaliação de LLMs.

    Permite sincronizar runs, datasets e avaliações do Guimí Test AI
    com o LangSmith, criando um ciclo completo de observabilidade.

    Exemplo:
        >>> from guimitestai.integrations import LangSmithIntegration
        >>> ls = LangSmithIntegration(api_key="ls__...")
        >>> # Decorar funções para rastreamento automático
        >>> @ls.traceable(name="my_chain")
        ... def my_chain(input: str) -> str:
        ...     return f"Resposta para: {input}"
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        project: str = "guimitestai",
        endpoint: str = "https://api.smith.langchain.com",
    ) -> None:
        self.api_key = api_key
        self.project = project
        self.endpoint = endpoint

    def _get_client(self) -> Any:
        """Inicializa o cliente LangSmith sob demanda."""
        try:
            from langsmith import Client  # type: ignore
            return Client(api_key=self.api_key, api_url=self.endpoint)
        except ImportError:
            raise ImportError(
                "LangSmith não instalado. Execute: pip install guimitestai[langsmith]"
            )

    def traceable(self, name: Optional[str] = None, **kwargs: Any) -> Callable:
        """Decorador para rastrear automaticamente funções no LangSmith."""
        try:
            from langsmith import traceable  # type: ignore
            return traceable(name=name, project_name=self.project, **kwargs)
        except ImportError:
            raise ImportError(
                "LangSmith não instalado. Execute: pip install guimitestai[langsmith]"
            )

    def create_dataset(
        self,
        name: str,
        description: Optional[str] = None,
        examples: Optional[List[Dict[str, Any]]] = None,
    ) -> Any:
        """Cria um dataset de avaliação no LangSmith.

        Args:
            name: Nome do dataset.
            description: Descrição do dataset.
            examples: Lista de exemplos com keys 'inputs' e 'outputs'.

        Returns:
            Dataset criado no LangSmith.
        """
        client = self._get_client()
        dataset = client.create_dataset(
            dataset_name=name,
            description=description or f"Dataset criado pelo Guimí Test AI",
        )
        if examples:
            client.create_examples(
                inputs=[e["inputs"] for e in examples],
                outputs=[e.get("outputs") for e in examples],
                dataset_id=dataset.id,
            )
        return dataset

    def run_evaluation(
        self,
        dataset_name: str,
        llm_function: Callable,
        evaluators: Optional[List[Any]] = None,
        experiment_prefix: str = "guimi",
    ) -> Any:
        """Executa avaliação de um dataset no LangSmith.

        Args:
            dataset_name: Nome do dataset a avaliar.
            llm_function: Função que recebe inputs e retorna outputs.
            evaluators: Lista de avaliadores LangSmith.
            experiment_prefix: Prefixo para o nome do experimento.

        Returns:
            Resultados da avaliação.
        """
        try:
            from langsmith.evaluation import evaluate  # type: ignore
            return evaluate(
                llm_function,
                data=dataset_name,
                evaluators=evaluators or [],
                experiment_prefix=experiment_prefix,
            )
        except ImportError:
            raise ImportError(
                "LangSmith não instalado. Execute: pip install guimitestai[langsmith]"
            )
