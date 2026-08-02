"""A small orchestrator with a dry-run preflight that enforces Rule Zero.

This is intentionally conservative: it performs discovery and validation only,
and never executes expensive generation steps. It is the canonical place to
run the "provider menu" + pipeline manifest checks before production starts.
"""
import os
from typing import Dict, Any


def _read_file_if_exists(path: str) -> bool:
    return os.path.exists(path)


class Orchestrator:
    def __init__(self, registry=None):
        # registry is expected to be the existing registry object from the repo
        self.registry = registry
        # lazy imports
        self._pipeline_loader = None
        self._health = None

    def _load_helpers(self):
        if self._health is None:
            try:
                from runtime import health

                self._health = health
            except Exception:
                self._health = None
        if self._pipeline_loader is None:
            try:
                from lib import pipeline_loader

                self._pipeline_loader = pipeline_loader
            except Exception:
                self._pipeline_loader = None

    def dry_run_preflight(self, pipeline_name: str, project_id: str = "dryrun") -> Dict[str, Any]:
        """
        Perform discovery and preflight checks for a given pipeline manifest name.
        Returns a dict with:
          - environment
          - capability_report
          - pipeline_manifest_exists (bool)
          - missing_stage_skills: list
          - provider_menu_summary (if registry available)
          - verdict: 'passed'|'degraded'|'blocked'
        """
        self._load_helpers()
        report: Dict[str, Any] = {}
        # environment
        if self._health:
            report["environment"] = self._health.check_environment()
        else:
            report["environment"] = {"note": "runtime.health not importable"}
        # registry / provider menu
        if self.registry is not None:
            try:
                if hasattr(self.registry, "discover"):
                    self.registry.discover()
                if hasattr(self.registry, "provider_menu_summary"):
                    report["provider_menu_summary"] = self.registry.provider_menu_summary()
                elif hasattr(self.registry, "capability_catalog"):
                    report["capability_catalog"] = self.registry.capability_catalog()
                else:
                    report["provider_menu_summary"] = {"note": "registry has no provider menu methods"}
                # capability readiness (best-effort)
                if self._health:
                    report["capability_report"] = self._health.check_capabilities(self.registry)
            except Exception as e:
                report["registry_error"] = str(e)
        else:
            report["registry"] = {"note": "no registry passed to Orchestrator"}

        # pipeline manifest presence & stage skills
        pipeline_path = os.path.join("pipeline_defs", f"{pipeline_name}.yaml")
        report["pipeline_manifest_exists"] = _read_file_if_exists(pipeline_path)
        missing_skills = []
        if report["pipeline_manifest_exists"]:
            # best-effort: look for skills/pipelines/<pipeline> directory and stage md files
            skills_dir = os.path.join("skills", "pipelines", pipeline_name)
            if not os.path.isdir(skills_dir):
                missing_skills.append(f"skills directory missing: {skills_dir}")
            else:
                # list files and check for .md presence (simple heuristic)
                has_md = any(f.endswith(".md") for f in os.listdir(skills_dir))
                if not has_md:
                    missing_skills.append(f"no .md director skills in {skills_dir}")
        report["missing_stage_skills"] = missing_skills

        # verdict logic (conservative)
        if report.get("registry") and report["registry"].get("note") == "no registry passed to Orchestrator":
            report["verdict"] = "degraded"
        elif report["pipeline_manifest_exists"] and not missing_skills:
            report["verdict"] = "passed"
        else:
            report["verdict"] = "degraded" if report["pipeline_manifest_exists"] else "blocked"

        return report

    def present_preflight_summary(self, preflight_report: Dict[str, Any]) -> str:
        """Return a human-friendly summary string for logs / UI."""
        lines = []
        env = preflight_report.get("environment", {})
        ffmpeg = env.get("ffmpeg", {}).get("available", False) if isinstance(env, dict) else False
        lines.append(f"FFmpeg: {'✓' if ffmpeg else '✗'}")
        provider_summary = preflight_report.get("provider_menu_summary")
        if provider_summary:
            caps = provider_summary.get("capabilities", {})
            for cap, info in caps.items():
                lines.append(f"{cap}: {info.get('configured', 'unknown')}/{info.get('total', '?')} configured")
        lines.append(f"Pipeline manifest present: {preflight_report.get('pipeline_manifest_exists')}")
        lines.append(f"Missing skills: {len(preflight_report.get('missing_stage_skills', []))}")
        lines.append(f"VERDICT: {preflight_report.get('verdict')}")
        return "\n".join(lines)
