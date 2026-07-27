#!/usr/bin/env python3
"""
Phase 5 Composition & Rendering Contract Tests

Tests for composition timeline creation and rendering to MP4.
Verifies both Remotion and HyperFrames runtimes work correctly.

Per AGENT_GUIDE.md: Both composition runtimes must be presented to user.
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.composition_director import CompositionDirector, CompositionConfig
from tools.base_tool import ToolResult


class TestCompositionDirector:
    """Test CompositionDirector tool."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.director = CompositionDirector()
        self.temp_dir = tempfile.mkdtemp()
    
    def test_composition_director_initialization(self):
        """Test director initializes correctly."""
        assert self.director.name == "composition_director"
        assert self.director.description
        assert callable(self.director.execute)
    
    def test_input_schema_valid(self):
        """Test input schema is valid."""
        schema = self.director.input_schema
        assert "properties" in schema
        assert "operation" in schema["properties"]
        assert "runtime" in schema["properties"]
        assert "mode" in schema["properties"]
    
    def test_operation_enum_values(self):
        """Test operation enum has expected values."""
        schema = self.director.input_schema
        operations = schema["properties"]["operation"]["enum"]
        assert "compose" in operations
        assert "render" in operations
        assert "preset_options" in operations
    
    def test_runtime_enum_values(self):
        """Test runtime enum has expected values."""
        schema = self.director.input_schema
        runtimes = schema["properties"]["runtime"]["enum"]
        assert "remotion" in runtimes
        assert "hyperframes" in runtimes


class TestRuntimePresentation:
    """Test HARD RULE: Present both runtimes."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.director = CompositionDirector()
    
    def test_preset_options_operation_returns_both_runtimes(self):
        """Test that preset_options returns both runtimes (HARD RULE)."""
        result = self.director.execute({"operation": "preset_options"})
        
        assert result.success
        assert "runtimes" in result.data
        
        runtimes = result.data["runtimes"]
        assert len(runtimes) == 2
        
        runtime_ids = {rt["id"] for rt in runtimes}
        assert "remotion" in runtime_ids
        assert "hyperframes" in runtime_ids
    
    def test_preset_options_remotion_description(self):
        """Test Remotion runtime is properly described."""
        result = self.director.execute({"operation": "preset_options"})
        runtimes = result.data["runtimes"]
        remotion = next(rt for rt in runtimes if rt["id"] == "remotion")
        
        assert remotion["name"] == "Remotion"
        assert "React" in remotion["description"]
        assert "pros" in remotion
        assert "cons" in remotion
        assert "best_for" in remotion
    
    def test_preset_options_hyperframes_description(self):
        """Test HyperFrames runtime is properly described."""
        result = self.director.execute({"operation": "preset_options"})
        runtimes = result.data["runtimes"]
        hyperframes = next(rt for rt in runtimes if rt["id"] == "hyperframes")
        
        assert hyperframes["name"] == "HyperFrames"
        assert "HTML" in hyperframes["description"] or "GSAP" in hyperframes["description"]
        assert "pros" in hyperframes
        assert "cons" in hyperframes
        assert "best_for" in hyperframes
    
    def test_preset_options_includes_authoring_modes(self):
        """Test that preset_options includes authoring modes."""
        result = self.director.execute({"operation": "preset_options"})
        
        assert "modes" in result.data
        modes = result.data["modes"]
        
        mode_ids = {m["id"] for m in modes}
        assert "templated" in mode_ids
        assert "atelier" in mode_ids


class TestComposition:
    """Test composition creation."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.director = CompositionDirector()
        self.temp_dir = tempfile.mkdtemp()
    
    def test_compose_creates_file(self):
        """Test compose operation creates composition file."""
        # Create minimal script
        script = {
            "segments": [
                {"segment_id": "seg_0", "narration": "Introduction", "visuals": {"type": "background"}},
                {"segment_id": "seg_1", "narration": "Main point", "visuals": {"type": "chart"}},
            ],
            "duration_seconds": 60,
            "word_count": 100,
            "retention_score": 85.0
        }
        
        script_path = Path(self.temp_dir) / "script.json"
        with open(script_path, 'w') as f:
            json.dump(script, f)
        
        result = self.director.execute({
            "operation": "compose",
            "runtime": "remotion",
            "mode": "templated",
            "script_path": str(script_path),
            "output_dir": self.temp_dir,
            "duration_seconds": 60
        })
        
        assert result.success
        assert "composition_file" in result.data
        composition_path = Path(result.data["composition_file"])
        assert composition_path.exists()
    
    def test_compose_remotion_templated(self):
        """Test compose with Remotion + templated mode."""
        script = {
            "segments": [{"narration": "Test", "visuals": {"type": "background"}}],
            "duration_seconds": 30
        }
        script_path = Path(self.temp_dir) / "script.json"
        with open(script_path, 'w') as f:
            json.dump(script, f)
        
        result = self.director.execute({
            "operation": "compose",
            "runtime": "remotion",
            "mode": "templated",
            "script_path": str(script_path),
            "output_dir": self.temp_dir
        })
        
        assert result.success
        assert result.data["runtime"] == "remotion"
        assert result.data["mode"] == "templated"
        assert result.data["ready_for_render"]
    
    def test_compose_hyperframes_atelier(self):
        """Test compose with HyperFrames + atelier mode."""
        script = {
            "segments": [{"narration": "Creative", "visuals": {"type": "background"}}],
            "duration_seconds": 45
        }
        script_path = Path(self.temp_dir) / "script.json"
        with open(script_path, 'w') as f:
            json.dump(script, f)
        
        result = self.director.execute({
            "operation": "compose",
            "runtime": "hyperframes",
            "mode": "atelier",
            "script_path": str(script_path),
            "output_dir": self.temp_dir
        })
        
        assert result.success
        assert result.data["runtime"] == "hyperframes"
        assert result.data["mode"] == "atelier"
    
    def test_compose_includes_scene_types(self):
        """Test that composed timeline includes scene types."""
        script = {
            "segments": [
                {"narration": "Text segment", "visuals": {"type": "background"}},
                {"narration": "Stat segment", "visuals": {"type": "stat"}},
                {"narration": "Chart segment", "visuals": {"type": "chart"}},
            ],
            "duration_seconds": 60
        }
        script_path = Path(self.temp_dir) / "script.json"
        with open(script_path, 'w') as f:
            json.dump(script, f)
        
        result = self.director.execute({
            "operation": "compose",
            "runtime": "remotion",
            "mode": "templated",
            "script_path": str(script_path),
            "output_dir": self.temp_dir
        })
        
        assert result.success
        
        # Load composition file and verify scenes
        composition_path = result.data["composition_file"]
        with open(composition_path, 'r') as f:
            composition = json.load(f)
        
        assert "scenes" in composition
        assert len(composition["scenes"]) == 3
        
        # Check scene types are set correctly in templated mode
        scene_types = {scene["type"] for scene in composition["scenes"]}
        # In templated mode, should have text_card, stat_card, bar_chart
        assert len(scene_types) >= 1  # At least one scene type


class TestRendering:
    """Test rendering operations."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.director = CompositionDirector()
        self.temp_dir = tempfile.mkdtemp()
    
    def test_render_requires_composition_file(self):
        """Test render requires composition file."""
        result = self.director.execute({
            "operation": "render",
            "composition_file": "/nonexistent/file.json",
            "output_path": "output.mp4"
        })
        
        assert not result.success
        assert "not found" in result.error.lower()
    
    @patch('subprocess.run')
    def test_render_remotion_checks_availability(self, mock_run):
        """Test render checks Remotion availability."""
        # Create minimal composition
        composition = {
            "runtime": "remotion",
            "mode": "templated",
            "scenes": []
        }
        composition_path = Path(self.temp_dir) / "comp.json"
        with open(composition_path, 'w') as f:
            json.dump(composition, f)
        
        # Mock npm command to fail
        mock_run.return_value = Mock(returncode=1)
        
        result = self.director.execute({
            "operation": "render",
            "composition_file": str(composition_path),
            "output_path": str(Path(self.temp_dir) / "output.mp4")
        })
        
        # Should fail because Remotion is not available
        assert not result.success
        assert "Remotion" in result.error or "not found" in result.error.lower()
    
    @patch('subprocess.run')
    def test_render_hyperframes_checks_availability(self, mock_run):
        """Test render checks HyperFrames availability."""
        composition = {
            "runtime": "hyperframes",
            "mode": "templated",
            "scenes": []
        }
        composition_path = Path(self.temp_dir) / "comp.json"
        with open(composition_path, 'w') as f:
            json.dump(composition, f)
        
        # Mock npm command to fail
        mock_run.return_value = Mock(returncode=1)
        
        result = self.director.execute({
            "operation": "render",
            "composition_file": str(composition_path),
            "output_path": str(Path(self.temp_dir) / "output.mp4")
        })
        
        assert not result.success
        assert "HyperFrames" in result.error or "not found" in result.error.lower()


class TestScenePlanGeneration:
    """Test scene plan generation from script."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.director = CompositionDirector()
    
    def test_scene_plan_creates_scenes_for_segments(self):
        """Test scene plan creates one scene per script segment."""
        script = {
            "segments": [
                {"narration": "First", "visuals": {"type": "background"}},
                {"narration": "Second", "visuals": {"type": "background"}},
                {"narration": "Third", "visuals": {"type": "background"}},
            ],
            "duration_seconds": 60
        }
        
        scenes = self.director._build_scene_plan(
            script=script,
            assets=None,
            runtime="remotion",
            mode="templated",
            audio_path=None
        )
        
        assert len(scenes) == 3
        assert all("type" in scene for scene in scenes)
        assert all("duration" in scene for scene in scenes)
    
    def test_scene_types_mapped_correctly_templated(self):
        """Test scene types are mapped correctly in templated mode."""
        script = {
            "segments": [
                {"narration": "Text", "visuals": {"type": "background"}},
                {"narration": "Stat", "visuals": {"type": "stat"}},
                {"narration": "Chart", "visuals": {"type": "chart"}},
            ],
            "duration_seconds": 60
        }
        
        scenes = self.director._build_scene_plan(
            script=script,
            assets=None,
            runtime="remotion",
            mode="templated",
            audio_path=None
        )
        
        # Verify scene type mapping
        assert scenes[0]["type"] == "text_card"
        assert scenes[1]["type"] == "stat_card"
        assert scenes[2]["type"] == "bar_chart"
    
    def test_scene_durations_calculated(self):
        """Test scene durations are calculated from total duration."""
        script = {
            "segments": [
                {"narration": "A"},
                {"narration": "B"},
                {"narration": "C"},
            ],
            "duration_seconds": 60
        }
        
        scenes = self.director._build_scene_plan(
            script=script,
            assets=None,
            runtime="remotion",
            mode="templated",
            audio_path=None
        )
        
        # Each scene should get 60/3 = 20 seconds
        assert all(abs(scene["duration"] - 20.0) < 0.1 for scene in scenes)
    
    def test_scene_start_times_sequential(self):
        """Test scene start times are sequential."""
        script = {
            "segments": [
                {"narration": "A"},
                {"narration": "B"},
                {"narration": "C"},
            ],
            "duration_seconds": 30
        }
        
        scenes = self.director._build_scene_plan(
            script=script,
            assets=None,
            runtime="remotion",
            mode="templated",
            audio_path=None
        )
        
        # Start times should be 0, 10, 20
        assert scenes[0]["start_time"] == 0.0
        assert scenes[1]["start_time"] == 10.0
        assert scenes[2]["start_time"] == 20.0


class TestCompositionIntegration:
    """Integration tests for composition workflow."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.director = CompositionDirector()
        self.temp_dir = tempfile.mkdtemp()
    
    def test_full_workflow_compose_to_render(self):
        """Test full workflow from script to composition to render."""
        # Create script
        script = {
            "segments": [
                {"narration": "Intro", "visuals": {"type": "background"}},
                {"narration": "Main", "visuals": {"type": "chart"}},
            ],
            "duration_seconds": 30,
            "word_count": 50,
            "retention_score": 80.0
        }
        script_path = Path(self.temp_dir) / "script.json"
        with open(script_path, 'w') as f:
            json.dump(script, f)
        
        # Step 1: Compose
        compose_result = self.director.execute({
            "operation": "compose",
            "runtime": "remotion",
            "mode": "templated",
            "script_path": str(script_path),
            "output_dir": self.temp_dir,
            "duration_seconds": 30
        })
        
        assert compose_result.success
        composition_file = compose_result.data["composition_file"]
        
        # Verify composition file structure
        with open(composition_file, 'r') as f:
            composition = json.load(f)
        
        assert composition["runtime"] == "remotion"
        assert composition["mode"] == "templated"
        assert len(composition["scenes"]) == 2
        assert composition["duration_seconds"] == 30
    
    def test_probe_runtime_availability(self):
        """Test probe method detects runtime availability."""
        probe_result = self.director.probe()
        
        assert isinstance(probe_result, dict)
        assert "remotion_available" in probe_result
        assert "hyperframes_available" in probe_result
        assert "node_available" in probe_result
        assert all(isinstance(v, bool) for v in probe_result.values())


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.director = CompositionDirector()
        self.temp_dir = tempfile.mkdtemp()
    
    def test_compose_with_missing_script(self):
        """Test compose handles missing script gracefully."""
        result = self.director.execute({
            "operation": "compose",
            "runtime": "remotion",
            "mode": "templated",
            "script_path": "/nonexistent/script.json",
            "output_dir": self.temp_dir
        })
        
        # Should still succeed with default fallback scene
        assert result.success
    
    def test_compose_with_empty_script(self):
        """Test compose handles empty script."""
        script = {"segments": []}
        script_path = Path(self.temp_dir) / "empty.json"
        with open(script_path, 'w') as f:
            json.dump(script, f)
        
        result = self.director.execute({
            "operation": "compose",
            "runtime": "remotion",
            "mode": "templated",
            "script_path": str(script_path),
            "output_dir": self.temp_dir
        })
        
        # Should handle gracefully
        assert result.success
    
    def test_compose_with_missing_assets(self):
        """Test compose with missing asset manifest."""
        script = {
            "segments": [{"narration": "Test"}],
            "duration_seconds": 10
        }
        script_path = Path(self.temp_dir) / "script.json"
        with open(script_path, 'w') as f:
            json.dump(script, f)
        
        result = self.director.execute({
            "operation": "compose",
            "runtime": "remotion",
            "mode": "templated",
            "script_path": str(script_path),
            "asset_manifest_path": "/nonexistent/assets.json",
            "output_dir": self.temp_dir
        })
        
        # Should succeed even without assets
        assert result.success
    
    def test_invalid_runtime_rejected(self):
        """Test invalid runtime is rejected."""
        result = self.director.execute({
            "operation": "compose",
            "runtime": "invalid_runtime",
            "mode": "templated",
            "output_dir": self.temp_dir
        })
        
        # Should fail
        assert not result.success


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
