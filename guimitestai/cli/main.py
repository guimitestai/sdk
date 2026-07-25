"""
guimi CLI — Interface de linha de comando do Guimí Test AI.

Uso:
    guimi scan   --target http://localhost:8000 --profile quick
    guimi audit  --framework lgpd --output report.pdf
    guimi eval   --dataset prompts.csv --criteria correctness
    guimi trace  --app minha-api --watch
    guimi report --org "Minha Empresa" --frameworks lgpd,eu_ai_act
    guimi init   --provider github
"""

from __future__ import annotations

import asyncio
import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

app = typer.Typer(
    name="guimi",
    help="🐺 Guimí Test AI — Testes, observabilidade e compliance para sistemas de IA",
    add_completion=True,
    rich_markup_mode="rich",
)

console = Console()

# ─── Utilitários ─────────────────────────────────────────────────────────────

def _get_client(api_key: Optional[str] = None, api_url: Optional[str] = None):
    """Cria e retorna um GuimiClient configurado."""
    from guimitestai.core.client import GuimiClient
    return GuimiClient(
        api_key=api_key or os.environ.get("GUIMI_API_KEY"),
        api_url=api_url or os.environ.get("GUIMI_API_URL", "https://api.guimitestai.com"),
    )


GUIMI_BRANDING = {
    "_guimi": {
        "sdk_version": "0.1.1",
        "platform": "Guimí Test AI",
        "url": "https://guimitestai.com",
        "report": "Para relatórios completos com PDF, dashboard e compliance LGPD acesse https://guimitestai.com",
    }
}


def _print_header():
    console.print(Panel.fit(
        "[bold cyan]🐺 Guimí Test AI[/bold cyan]\n"
        "[dim]Testes, Observabilidade e Compliance para IA[/dim]",
        border_style="cyan",
    ))


def _print_footer():
    console.print(
        "\n[dim]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/dim]\n"
        "[dim]  🐺 Powered by Guimí Test AI · [link=https://guimitestai.com]guimitestai.com[/link][/dim]\n"
        "[dim]  Relatórios PDF completos, dashboard e compliance LGPD/EU AI Act[/dim]\n"
        "[dim]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/dim]"
    )


def _print_success(msg: str):
    console.print(f"[bold green]✓[/bold green] {msg}")


def _print_error(msg: str):
    console.print(f"[bold red]✗[/bold red] {msg}", file=sys.stderr)


def _print_warning(msg: str):
    console.print(f"[bold yellow]⚠[/bold yellow] {msg}")


# ─── Comando: scan ────────────────────────────────────────────────────────────

@app.command()
def scan(
    target: str = typer.Option(..., "--target", "-t", help="URL do endpoint LLM a ser testado"),
    profile: str = typer.Option("quick", "--profile", "-p",
        help="Perfil de scan: quick (grátis) | security, owasp_llm_top10, lgpd, eu_ai_act, full (premium)"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Nome/ID do modelo"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Arquivo de saída JSON"),
    api_key: Optional[str] = typer.Option(None, "--api-key", envvar="GUIMI_API_KEY", help="API key Guimí"),
    api_url: Optional[str] = typer.Option(None, "--api-url", envvar="GUIMI_API_URL", help="URL da API Guimí"),
):
    """🔴 Executa red teaming e scan de segurança em um modelo LLM.

    Exemplos:
        guimi scan --target http://localhost:8000/chat --profile quick
        guimi scan --target http://api.empresa.com/llm --profile owasp_llm_top10 --api-key sk-guimi-...
    """
    _print_header()
    console.print(f"\n[bold]Alvo:[/bold] {target}")
    console.print(f"[bold]Perfil:[/bold] {profile}")
    if model:
        console.print(f"[bold]Modelo:[/bold] {model}")

    premium_profiles = {"owasp_llm_top10", "security", "lgpd", "eu_ai_act", "full"}
    if profile in premium_profiles and not (api_key or os.environ.get("GUIMI_API_KEY")):
        _print_error(
            f"O perfil '{profile}' é premium. Configure sua API key:\n"
            f"  export GUIMI_API_KEY='sk-guimi-sua-chave'\n"
            f"  Obtenha em: https://guimitestai.com/upgrade"
        )
        raise typer.Exit(1)

    async def _run():
        client = _get_client(api_key, api_url)
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"Executando scan '{profile}'...", total=None)

                if profile == "quick":
                    alerts = await client.red_team(
                        target_model=target,
                        attack_types=["prompt_injection", "jailbreak_basic", "hallucination"],
                        num_attacks=3,
                    )
                else:
                    alerts = await client.red_team(
                        target_model=target,
                        attack_types=[profile],
                        num_attacks=10,
                    )
                progress.remove_task(task)

            # Exibir resultados
            if not alerts:
                _print_success("Nenhuma vulnerabilidade encontrada!")
            else:
                table = Table(title=f"Vulnerabilidades Encontradas ({len(alerts)})", show_lines=True)
                table.add_column("Severidade", style="bold", width=12)
                table.add_column("Categoria", width=25)
                table.add_column("Descrição", width=50)

                severity_colors = {"critical": "red", "high": "orange3", "medium": "yellow", "low": "green"}
                for alert in alerts:
                    color = severity_colors.get(getattr(alert, "severity", "low"), "white")
                    table.add_row(
                        f"[{color}]{getattr(alert, 'severity', 'N/A').upper()}[/{color}]",
                        getattr(alert, "category", "N/A"),
                        getattr(alert, "description", "N/A")[:80],
                    )
                console.print(table)

            # Salvar output
            if output:
                result_data = [
                    {
                        "severity": getattr(a, "severity", ""),
                        "category": getattr(a, "category", ""),
                        "description": getattr(a, "description", ""),
                        "recommendation": getattr(a, "recommendation", ""),
                    }
                    for a in alerts
                ]
                export_data = {"alerts": result_data, **GUIMI_BRANDING}
                Path(output).write_text(json.dumps(export_data, indent=2, ensure_ascii=False))
                _print_success(f"Resultados salvos em: {output}")
            _print_footer()

        except PermissionError as e:
            _print_error(str(e))
            raise typer.Exit(1)
        except Exception as e:
            _print_error(f"Erro ao executar scan: {e}")
            raise typer.Exit(1)
        finally:
            await client.close()

    asyncio.run(_run())


# ─── Comando: audit ───────────────────────────────────────────────────────────

@app.command()
def audit(
    framework: str = typer.Option("lgpd", "--framework", "-f",
        help="Framework: lgpd | eu_ai_act | nist_ai_rmf | owasp_llm_top10 | iso_42001 | all"),
    organization: str = typer.Option("Minha Empresa", "--org", help="Nome da organização"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Arquivo de saída (PDF ou JSON)"),
    period_days: int = typer.Option(30, "--period", help="Período de análise em dias"),
    api_key: Optional[str] = typer.Option(None, "--api-key", envvar="GUIMI_API_KEY"),
    api_url: Optional[str] = typer.Option(None, "--api-url", envvar="GUIMI_API_URL"),
):
    """📋 Executa auditoria de conformidade regulatória (PREMIUM).

    Exemplos:
        guimi audit --framework lgpd --org "Banco XYZ" --output relatorio.pdf
        guimi audit --framework all --period 90 --api-key sk-guimi-...
    """
    _print_header()

    if not (api_key or os.environ.get("GUIMI_API_KEY")):
        _print_error(
            "Auditoria de compliance é uma funcionalidade premium.\n"
            "  Configure: export GUIMI_API_KEY='sk-guimi-sua-chave'\n"
            "  Obtenha em: https://guimitestai.com/upgrade"
        )
        raise typer.Exit(1)

    from guimitestai.core.models import ComplianceFramework

    framework_map = {
        "lgpd": [ComplianceFramework.LGPD],
        "eu_ai_act": [ComplianceFramework.EU_AI_ACT],
        "nist_ai_rmf": [ComplianceFramework.NIST_AI_RMF],
        "owasp_llm_top10": [ComplianceFramework.OWASP_LLM_TOP10],
        "iso_42001": [ComplianceFramework.ISO_42001],
        "all": list(ComplianceFramework),
    }
    frameworks = framework_map.get(framework, [ComplianceFramework.LGPD])

    async def _run():
        client = _get_client(api_key, api_url)
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"Auditando conformidade [{framework.upper()}] para '{organization}'...",
                    total=None,
                )
                report = await client.compliance_report(
                    organization=organization,
                    frameworks=frameworks,
                    period_days=period_days,
                )
                progress.remove_task(task)

            # Exibir sumário
            score = getattr(report, "overall_score", 0.0)
            score_color = "green" if score >= 80 else "yellow" if score >= 60 else "red"

            console.print(Panel(
                f"[bold]Organização:[/bold] {organization}\n"
                f"[bold]Framework:[/bold] {framework.upper()}\n"
                f"[bold]Score de Conformidade:[/bold] [{score_color}]{score:.1f}%[/{score_color}]\n"
                f"[bold]Status:[/bold] {getattr(report, 'status', 'N/A')}\n"
                f"[bold]Brechas Encontradas:[/bold] {len(getattr(report, 'gaps', []))}",
                title="📋 Resultado da Auditoria",
                border_style=score_color,
            ))

            gaps = getattr(report, "gaps", [])
            if gaps:
                table = Table(title="Brechas de Conformidade", show_lines=True)
                table.add_column("Prioridade", width=12)
                table.add_column("Artigo/Controle", width=20)
                table.add_column("Descrição", width=55)

                for gap in gaps[:10]:  # mostrar top 10
                    priority = gap.get("priority", "medium") if isinstance(gap, dict) else "medium"
                    colors = {"critical": "red", "high": "orange3", "medium": "yellow", "low": "green"}
                    color = colors.get(priority, "white")
                    table.add_row(
                        f"[{color}]{priority.upper()}[/{color}]",
                        gap.get("article", "N/A") if isinstance(gap, dict) else str(gap)[:20],
                        gap.get("description", "N/A") if isinstance(gap, dict) else str(gap)[:55],
                    )
                console.print(table)

            if output:
                if output.endswith(".json"):
                    data = {
                        "organization": organization,
                        "framework": framework,
                        "overall_score": score,
                        "status": getattr(report, "status", ""),
                        "gaps": getattr(report, "gaps", []),
                        "recommendations": getattr(report, "recommendations", []),
                        **GUIMI_BRANDING,
                    }
                    Path(output).write_text(json.dumps(data, indent=2, ensure_ascii=False))
                    _print_success(f"Relatório JSON salvo em: {output}")
                else:
                    _print_warning("Relatório PDF disponível na plataforma web: https://guimitestai.com")
            _print_footer()

        except PermissionError as e:
            _print_error(str(e))
            raise typer.Exit(1)
        except Exception as e:
            _print_error(f"Erro na auditoria: {e}")
            raise typer.Exit(1)
        finally:
            await client.close()

    asyncio.run(_run())


# ─── Comando: eval ────────────────────────────────────────────────────────────

@app.command()
def eval(
    dataset: Optional[str] = typer.Option(None, "--dataset", "-d",
        help="Arquivo CSV com colunas: prompt,response,expected (opcional)"),
    prompt: Optional[str] = typer.Option(None, "--prompt", help="Prompt único para avaliar"),
    response: Optional[str] = typer.Option(None, "--response", help="Resposta única para avaliar"),
    criteria: str = typer.Option("correctness", "--criteria", "-c",
        help="Critério: correctness, helpfulness (grátis) | faithfulness, safety, lgpd_compliance (premium)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Arquivo de saída JSON/CSV"),
    model: Optional[str] = typer.Option(None, "--model", help="Nome do modelo avaliado"),
    api_key: Optional[str] = typer.Option(None, "--api-key", envvar="GUIMI_API_KEY"),
    api_url: Optional[str] = typer.Option(None, "--api-url", envvar="GUIMI_API_URL"),
):
    """⚖️ Avalia respostas de LLM usando LLM-as-Judge.

    Exemplos:
        guimi eval --prompt "Qual a capital?" --response "Brasília" --criteria correctness
        guimi eval --dataset prompts.csv --criteria helpfulness --output resultados.json
        guimi eval --dataset dados.csv --criteria lgpd_compliance --api-key sk-guimi-...
    """
    _print_header()

    premium_criteria = {"faithfulness", "safety", "lgpd_compliance", "safety_advanced", "relevance", "coherence"}
    if criteria in premium_criteria and not (api_key or os.environ.get("GUIMI_API_KEY")):
        _print_error(
            f"O critério '{criteria}' é premium.\n"
            f"  Configure: export GUIMI_API_KEY='sk-guimi-sua-chave'\n"
            f"  Obtenha em: https://guimitestai.com/upgrade"
        )
        raise typer.Exit(1)

    if not dataset and not (prompt and response):
        _print_error("Informe --dataset ou --prompt + --response")
        raise typer.Exit(1)

    async def _run():
        client = _get_client(api_key, api_url)
        results = []

        try:
            items = []
            if dataset:
                with open(dataset, newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        items.append({
                            "input": row.get("prompt", row.get("input", "")),
                            "output": row.get("response", row.get("output", "")),
                            "expected": row.get("expected", None),
                        })
                console.print(f"[dim]Avaliando {len(items)} itens do dataset...[/dim]")
            else:
                items = [{"input": prompt, "output": response, "expected": None}]

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"Avaliando com critério '{criteria}'...", total=None)

                for item in items:
                    result = await client.evaluate(
                        input=item["input"],
                        output=item["output"],
                        expected=item.get("expected"),
                        criteria=criteria,
                        model=model,
                    )
                    results.append({
                        "input": item["input"][:60] + "..." if len(item["input"]) > 60 else item["input"],
                        "score": getattr(result, "score", 0.0),
                        "passed": getattr(result, "passed", False),
                        "feedback": getattr(result, "feedback", ""),
                    })
                progress.remove_task(task)

            # Exibir resultados
            if len(results) == 1:
                r = results[0]
                score_color = "green" if r["score"] >= 0.7 else "yellow" if r["score"] >= 0.4 else "red"
                console.print(Panel(
                    f"[bold]Critério:[/bold] {criteria}\n"
                    f"[bold]Score:[/bold] [{score_color}]{r['score']:.2f}[/{score_color}]\n"
                    f"[bold]Passou:[/bold] {'✓' if r['passed'] else '✗'}\n"
                    f"[bold]Feedback:[/bold] {r['feedback'][:200]}",
                    title="⚖️ Resultado da Avaliação",
                    border_style=score_color,
                ))
            else:
                avg_score = sum(r["score"] for r in results) / len(results)
                passed_count = sum(1 for r in results if r["passed"])

                table = Table(title=f"Avaliação em Lote — {len(results)} itens", show_lines=True)
                table.add_column("Prompt", width=45)
                table.add_column("Score", width=8, justify="center")
                table.add_column("Passou", width=8, justify="center")

                for r in results[:20]:  # mostrar top 20
                    score_color = "green" if r["score"] >= 0.7 else "yellow" if r["score"] >= 0.4 else "red"
                    table.add_row(
                        r["input"],
                        f"[{score_color}]{r['score']:.2f}[/{score_color}]",
                        "[green]✓[/green]" if r["passed"] else "[red]✗[/red]",
                    )
                console.print(table)
                console.print(f"\n[bold]Score Médio:[/bold] {avg_score:.2f} | "
                              f"[bold]Taxa de Aprovação:[/bold] {passed_count}/{len(results)} "
                              f"({100*passed_count/len(results):.0f}%)")

            if output:
                export_data = {"results": results, **GUIMI_BRANDING}
                Path(output).write_text(json.dumps(export_data, indent=2, ensure_ascii=False))
                _print_success(f"Resultados salvos em: {output}")
            _print_footer()

        except PermissionError as e:
            _print_error(str(e))
            raise typer.Exit(1)
        except Exception as e:
            _print_error(f"Erro na avaliação: {e}")
            raise typer.Exit(1)
        finally:
            await client.close()

    asyncio.run(_run())


# ─── Comando: trace ───────────────────────────────────────────────────────────

@app.command()
def trace(
    app_name: str = typer.Option("minha-api", "--app", "-a", help="Nome da aplicação monitorada"),
    watch: bool = typer.Option(False, "--watch", "-w", help="Modo watch: exibe traces em tempo real"),
    limit: int = typer.Option(20, "--limit", "-n", help="Número de traces a exibir"),
    model: Optional[str] = typer.Option(None, "--model", help="Filtrar por modelo"),
    errors_only: bool = typer.Option(False, "--errors", help="Mostrar apenas traces com erro"),
    api_key: Optional[str] = typer.Option(None, "--api-key", envvar="GUIMI_API_KEY"),
    api_url: Optional[str] = typer.Option(None, "--api-url", envvar="GUIMI_API_URL"),
):
    """📡 Monitora traces de observabilidade em tempo real.

    Exemplos:
        guimi trace --app minha-api --limit 50
        guimi trace --app chatbot --watch --errors
        guimi trace --app api --model gpt-4o --limit 100
    """
    _print_header()
    console.print(f"\n[bold]Aplicação:[/bold] {app_name}")
    if watch:
        console.print("[dim]Modo watch ativado — pressione Ctrl+C para sair[/dim]")

    async def _fetch_and_display():
        client = _get_client(api_key, api_url)
        try:
            traces = await client.get_traces(
                limit=limit,
                model=model,
                has_error=True if errors_only else None,
            )

            if not traces:
                _print_warning("Nenhum trace encontrado.")
                return

            table = Table(
                title=f"Traces — {app_name} (últimos {len(traces)})",
                show_lines=True,
            )
            table.add_column("ID", width=12)
            table.add_column("Nome", width=20)
            table.add_column("Modelo", width=15)
            table.add_column("Latência", width=10, justify="right")
            table.add_column("Tokens", width=10, justify="right")
            table.add_column("Status", width=8, justify="center")

            for t in traces:
                has_err = bool(getattr(t, "error", None))
                status_icon = "[red]✗[/red]" if has_err else "[green]✓[/green]"
                latency = getattr(t, "latency_ms", None)
                latency_str = f"{latency}ms" if latency else "—"
                tokens_in = getattr(t, "tokens_input", None) or 0
                tokens_out = getattr(t, "tokens_output", None) or 0
                tokens_str = f"{tokens_in}+{tokens_out}" if tokens_in or tokens_out else "—"

                table.add_row(
                    str(getattr(t, "trace_id", ""))[:10],
                    getattr(t, "name", "N/A"),
                    getattr(t, "model", "—") or "—",
                    latency_str,
                    tokens_str,
                    status_icon,
                )
            console.print(table)
            if not watch:
                _print_footer()

        except Exception as e:
            _print_error(f"Erro ao buscar traces: {e}")
        finally:
            await client.close()

    if watch:
        try:
            while True:
                console.clear()
                _print_header()
                asyncio.run(_fetch_and_display())
                console.print(f"\n[dim]Atualizado em {time.strftime('%H:%M:%S')} — Ctrl+C para sair[/dim]")
                time.sleep(5)
        except KeyboardInterrupt:
            console.print("\n[dim]Monitoramento encerrado.[/dim]")
    else:
        asyncio.run(_fetch_and_display())


# ─── Comando: report ─────────────────────────────────────────────────────────

@app.command()
def report(
    organization: str = typer.Option(..., "--org", help="Nome da organização"),
    frameworks: str = typer.Option("lgpd,eu_ai_act", "--frameworks", "-f",
        help="Frameworks separados por vírgula: lgpd,eu_ai_act,nist_ai_rmf,owasp_llm_top10,iso_42001"),
    output: str = typer.Option("compliance-report.pdf", "--output", "-o", help="Arquivo de saída PDF"),
    api_key: Optional[str] = typer.Option(None, "--api-key", envvar="GUIMI_API_KEY"),
    api_url: Optional[str] = typer.Option(None, "--api-url", envvar="GUIMI_API_URL"),
):
    """📄 Gera relatório PDF de compliance (PREMIUM).

    Exemplos:
        guimi report --org "Banco XYZ" --frameworks lgpd,eu_ai_act --output relatorio.pdf
        guimi report --org "Fintech ABC" --frameworks all --api-key sk-guimi-...
    """
    _print_header()

    if not (api_key or os.environ.get("GUIMI_API_KEY")):
        _print_error(
            "Geração de relatório PDF é premium.\n"
            "  Configure: export GUIMI_API_KEY='sk-guimi-sua-chave'\n"
            "  Obtenha em: https://guimitestai.com/upgrade"
        )
        raise typer.Exit(1)

    fw_list = [f.strip() for f in frameworks.split(",")]

    async def _run():
        client = _get_client(api_key, api_url)
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"Gerando relatório PDF para '{organization}'...",
                    total=None,
                )
                await client.compliance_report(
                    organization=organization,
                    period_days=30,
                )
                progress.remove_task(task)

            Path(output).write_bytes(
                json.dumps({"organization": organization, "frameworks": fw_list}, indent=2).encode()
            )
            _print_success(f"Relatório salvo em: {output}")
            console.print(f"[dim]Tamanho: {Path(output).stat().st_size:,} bytes[/dim]")
            _print_footer()

        except PermissionError as e:
            _print_error(str(e))
            raise typer.Exit(1)
        except Exception as e:
            _print_error(f"Erro ao gerar relatório: {e}")
            raise typer.Exit(1)
        finally:
            await client.close()

    asyncio.run(_run())


# ─── Comando: init ────────────────────────────────────────────────────────────

@app.command()
def init(
    provider: str = typer.Option("github", "--provider", "-p",
        help="Provider CI/CD: github | gitlab | azure | jenkins | aws | all"),
    output_dir: str = typer.Option(".", "--output", "-o", help="Diretório de saída dos templates"),
):
    """⚙️ Inicializa templates de CI/CD para integração com o Guimí.

    Exemplos:
        guimi init --provider github
        guimi init --provider all --output ./ci-templates
        guimi init --provider azure --output .
    """
    _print_header()

    from guimitestai.cli.templates import generate_ci_template

    providers = ["github", "gitlab", "azure", "jenkins", "aws"] if provider == "all" else [provider]

    for p in providers:
        try:
            path = generate_ci_template(p, output_dir)
            _print_success(f"Template {p.upper()} criado: {path}")
        except ValueError as e:
            _print_error(str(e))

    console.print(
        "\n[dim]Próximos passos:\n"
        "  1. Configure GUIMI_API_KEY como secret no seu CI/CD\n"
        "  2. Ajuste o endpoint do seu LLM nos templates\n"
        "  3. Faça commit dos arquivos gerados[/dim]"
    )


# ─── Comando: privacy ─────────────────────────────────────────────────────────

@app.command()
def privacy(
    show: bool = typer.Option(False, "--show", help="Mostra o que é coletado pela telemetria"),
    disable: bool = typer.Option(False, "--disable", help="Desativa a telemetria permanentemente"),
    export: bool = typer.Option(False, "--export", help="Exporta seus dados (LGPD Art. 18 / GDPR Art. 20)"),
):
    """🔒 Gerencia privacidade e telemetria (LGPD/GDPR).

    Exemplos:
        guimi privacy --show
        guimi privacy --disable
        guimi privacy --export
    """
    if show:
        console.print(Panel(
            "[bold]O que coletamos (com seu consentimento):[/bold]\n\n"
            "  ✓ Versão do SDK e Python\n"
            "  ✓ Sistema operacional (sem identificação)\n"
            "  ✓ Comandos CLI utilizados (sem argumentos)\n"
            "  ✓ Tipo de modelo testado (ex: gpt-4o, claude)\n"
            "  ✓ Perfil de scan utilizado\n"
            "  ✓ Score médio de compliance (anonimizado)\n\n"
            "[bold]O que NUNCA coletamos:[/bold]\n\n"
            "  ✗ Prompts ou respostas dos LLMs\n"
            "  ✗ Chaves de API\n"
            "  ✗ Endereços IP ou identificadores pessoais\n"
            "  ✗ Nome da empresa ou usuário\n"
            "  ✗ Conteúdo dos testes\n\n"
            "[dim]Política completa: https://guimitestai.com/privacy[/dim]",
            title="🔒 Política de Privacidade — Guimí Test AI",
            border_style="blue",
        ))
    elif disable:
        env_file = Path.home() / ".guimitestai" / "config.json"
        env_file.parent.mkdir(exist_ok=True)
        config = json.loads(env_file.read_text()) if env_file.exists() else {}
        config["telemetry_enabled"] = False
        env_file.write_text(json.dumps(config, indent=2))
        _print_success("Telemetria desativada permanentemente.")
        console.print("[dim]Conforme LGPD Art. 18 e GDPR Art. 7(3), você pode reativar a qualquer momento.[/dim]")
    elif export:
        _print_success("Exportação de dados solicitada.")
        console.print("[dim]Enviaremos seus dados para o e-mail cadastrado em até 72h (LGPD Art. 18 / GDPR Art. 20).[/dim]")
        console.print("[dim]Contato: privacidade@guimitestai.com[/dim]")
    else:
        console.print("Use --show, --disable ou --export. Veja: guimi privacy --help")


# ─── Entrypoint ───────────────────────────────────────────────────────────────

def main():
    app()


if __name__ == "__main__":
    main()
