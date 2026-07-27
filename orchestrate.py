#!/usr/bin/env python3
"""
Production orchestrator: coordinates research → script → composition → rendering.

This is the "control center" for your video production.
Run this to automate the entire pipeline for a single video or batch.

Usage:
    python orchestrate.py --topic "AI in filmmaking" --type educational
    python orchestrate.py --batch topics.json
"""

import json
import asyncio
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.production_config import config, credentials, APICredentials
from tools.research_engine import ResearchEngine
from tools.script_generator import ScriptGenerator
from tools.asset_collector import AssetCollector, collect_assets_for_video
from tools.audio.tts_selector import TTSSelector
from tools.audio.kokoro_tts import KokoroTTS
from tools.audio.piper_tts import PiperTTS
from tools.audio.google_music import GoogleMusic
from tools.audio.suno_music import SunoMusic
from tools.audio.pixabay_music import PixabayMusic
from tools.audio.music_library import MusicLibrary
from tools.audio.audio_mixer import AudioMixer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


class ProductionOrchestrator:
    """Orchestrates entire production pipeline."""
    
    def __init__(self):
        self.research_engine = ResearchEngine()
        self.script_generator = ScriptGenerator()
        self.start_time = datetime.now()
        self.total_cost = 0.0
    
    async def produce_video(
        self,
        title: str,
        topic: str,
        video_type: str = "educational",
        target_duration: int = 600,
        research_topics: Optional[Dict[str, Dict[str, Any]]] = None,
        skip_research: bool = False,
        skip_script: bool = False,
        skip_assets: bool = False,
        skip_audio: bool = False,
        output_dir: Optional[Path] = None
    ) -> Dict[str, Path]:
        """
        Produce a complete video from topic to assets.
        
        Returns:
            {
                "research": Path,
                "script_json": Path,
                "script_voiceover": Path,
                "asset_manifest": Path
            }
        """
        
        if not output_dir:
            output_dir = config.OUTPUT_DIR
        
        logger.info("=" * 70)
        logger.info(f"🚀 STARTING PRODUCTION: {title}")
        logger.info("=" * 70)
        
        outputs = {}
        
        # ====================================================================
        # PHASE 1: RESEARCH
        # ====================================================================
        
        if not skip_research:
            logger.info("\n📚 PHASE 1: RESEARCH")
            logger.info("-" * 70)
            
            if not research_topics:
                # Auto-generate research topics from title/topic
                research_topics = self._generate_research_topics(title, topic)
            
            logger.info(f"Researching {len(research_topics)} topics...")
            research_results = await self.research_engine.batch_research(research_topics)
            
            research_file = self.research_engine.export_research(research_results)
            outputs["research"] = research_file
            
            # Consolidate research for script generation
            consolidated_research = {}
            for result in research_results:
                consolidated_research[result.topic] = result.data
            
            research_cost = sum(r.cost_usd for r in research_results)
            self.total_cost += research_cost
            logger.info(f"✓ Research complete. Cost: ${research_cost:.4f}")
        
        else:
            consolidated_research = {}
            logger.info("⊘ Skipping research (--skip-research)")
        
        # ====================================================================
        # PHASE 2: SCRIPT GENERATION
        # ====================================================================
        
        if not skip_script:
            logger.info("\n✍️  PHASE 2: SCRIPT GENERATION")
            logger.info("-" * 70)
            
            script = await self.script_generator.generate_script(
                title=title,
                topic=topic,
                research_data=consolidated_research,
                video_type=video_type,
                target_duration=target_duration
            )
            
            script_json_file = self.script_generator.export_script(script)
            script_vo_file = self.script_generator.export_voiceover_text(script)
            
            outputs["script_json"] = script_json_file
            outputs["script_voiceover"] = script_vo_file
            
            self.total_cost += script.cost_usd
            logger.info(f"✓ Script generated:")
            logger.info(f"  Duration: {script.duration_seconds}s ({script.duration_seconds/60:.1f}m)")
            logger.info(f"  Words: {script.word_count}")
            logger.info(f"  Retention score: {script.retention_score:.1f}/100")
            logger.info(f"  Cost: ${script.cost_usd:.4f}")
        
        else:
            logger.info("⊘ Skipping script generation (--skip-script)")
        
        # ====================================================================
        # PHASE 3: ASSET COLLECTION
        # ====================================================================
        
        if not skip_assets and "script_json" in outputs:
            logger.info("\n🎬 PHASE 3: ASSET COLLECTION")
            logger.info("-" * 70)
            
            try:
                manifest = await collect_assets_for_video(
                    script_path=outputs["script_json"],
                    video_title=title,
                    output_dir=output_dir,
                    download=True
                )
                
                outputs["asset_manifest"] = output_dir / "manifests" / f"{title}_asset_manifest.json"
                
                self.total_cost += manifest.total_cost_usd
                logger.info(f"✓ Assets collected:")
                logger.info(f"  Total assets: {manifest.total_assets}")
                logger.info(f"  By segment: {len(manifest.organized_by_segment)}")
                logger.info(f"  Cost: ${manifest.total_cost_usd:.4f}")
            
            except Exception as e:
                logger.error(f"✗ Asset collection failed: {e}")
                logger.info("⊘ Skipping asset collection due to error")
        
        elif skip_assets:
            logger.info("⊘ Skipping asset collection (--skip-assets)")
        
        elif "script_json" not in outputs:
            logger.info("⊘ Skipping asset collection (no script generated)")
        
        # ====================================================================
        # PHASE 4: VOICE & AUDIO GENERATION
        # ====================================================================
        
        if not skip_audio and "script_voiceover" in outputs:
            logger.info("\n🎤 PHASE 4: VOICE & AUDIO GENERATION")
            logger.info("-" * 70)
            
            # Ensure audio output directory exists
            audio_dir = output_dir / "audio"
            audio_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                # Read voiceover script
                voiceover_path = outputs["script_voiceover"]
                with open(voiceover_path, 'r', encoding='utf-8') as f:
                    voiceover_text = f.read()
                
                # Phase 4a: Generate/select narration (TTS)
                logger.info("📢 Generating narration via TTS...")
                
                # Try Kokoro TTS first (open source, free, decent quality)
                narration_path = None
                tts_tool = KokoroTTS()
                
                logger.info("  Trying Kokoro TTS (open-source, free)...")
                tts_result = tts_tool.execute({
                    "text": voiceover_text,
                    "voice": "en",
                    "speed": 1.0,
                    "output_path": str(audio_dir / f"{title}_narration_kokoro.wav")
                })
                
                if tts_result.success:
                    narration_path = Path(tts_result.data.get("audio_path", ""))
                    logger.info(f"✓ Narration generated with Kokoro: {narration_path}")
                    outputs["narration"] = narration_path
                    self.total_cost += float(tts_result.data.get("cost_usd", 0))
                else:
                    logger.info(f"  Kokoro unavailable, falling back to Piper...")
                    # Fall back to Piper (offline, free)
                    piper_tool = PiperTTS()
                    tts_result = piper_tool.execute({
                        "text": voiceover_text,
                        "output_path": str(audio_dir / f"{title}_narration_piper.wav")
                    })
                    
                    if tts_result.success:
                        narration_path = Path(tts_result.data.get("audio_path", ""))
                        logger.info(f"✓ Narration generated with Piper: {narration_path}")
                        outputs["narration"] = narration_path
                        self.total_cost += float(tts_result.data.get("cost_usd", 0))
                    else:
                        logger.warning(f"⚠ TTS generation failed: {tts_result.error}")
                
                # Phase 4b: Select background music
                logger.info("🎵 Selecting background music...")
                
                # First check user's music library
                music_library_tool = MusicLibrary()
                library_result = music_library_tool.execute({"operation": "list"})
                
                music_path = None
                if library_result.success and library_result.data.get("tracks"):
                    # Use first track from music library
                    track = library_result.data["tracks"][0]
                    music_path = track.get("path")
                    logger.info(f"✓ Using music from library: {track.get('filename')}")
                else:
                    # Fall back to generating music via Google Lyria or Pixabay
                    logger.info("  No music library found, generating music...")
                    
                    # Try Google Music first
                    music_prompt = f"Background music for {video_type} video about {topic}. Mood: professional, engaging. Tempo: moderate."
                    
                    try:
                        music_tool = GoogleMusic()
                        music_result = music_tool.execute({
                            "prompt": music_prompt,
                            "duration_seconds": target_duration,
                            "output_path": str(output_dir / "audio" / f"{title}_music.mp3")
                        })
                        
                        if music_result.success:
                            music_path = music_result.data.get("audio_path")
                            logger.info(f"✓ Music generated: {music_path}")
                            self.total_cost += float(music_result.data.get("cost_usd", 0))
                        else:
                            logger.warning(f"⚠ Music generation failed: {music_result.error}")
                    except Exception as e:
                        logger.warning(f"⚠ Google Music unavailable: {e}")
                
                # Phase 4c: Mix narration + music using audio_mixer
                if "narration" in outputs and music_path:
                    logger.info("🔊 Mixing narration + music...")
                    
                    mixer = AudioMixer()
                    mix_result = mixer.execute({
                        "operation": "full_mix",
                        "primary_audio": str(outputs["narration"]),
                        "secondary_audio": str(music_path),
                        "output_path": str(output_dir / "audio" / f"{title}_final_mix.wav")
                    })
                    
                    if mix_result.success:
                        final_audio_path = mix_result.data.get("output_path")
                        logger.info(f"✓ Audio mix complete: {final_audio_path}")
                        outputs["final_audio"] = Path(final_audio_path)
                        self.total_cost += float(mix_result.data.get("cost_usd", 0))
                    else:
                        logger.warning(f"⚠ Audio mixing failed: {mix_result.error}")
                
                logger.info(f"✓ Phase 4 complete. Cost: ${self.total_cost:.4f}")
            
            except Exception as e:
                logger.error(f"✗ Audio generation failed: {e}")
                logger.info("⊘ Skipping audio generation due to error")
        
        elif skip_audio:
            logger.info("⊘ Skipping audio generation (--skip-audio)")
        
        elif "script_voiceover" not in outputs:
            logger.info("⊘ Skipping audio generation (no voiceover script generated)")
        
        # ====================================================================
        # SUMMARY
        # ====================================================================
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        logger.info("\n" + "=" * 70)
        logger.info("✓ PRODUCTION PHASE COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Elapsed time: {elapsed:.1f}s")
        logger.info(f"Total cost: ${self.total_cost:.4f}")
        logger.info(f"\nOutputs:")
        for name, path in outputs.items():
            logger.info(f"  {name}: {path}")
        
        return outputs
    
    def _generate_research_topics(self, title: str, topic: str) -> Dict[str, Dict[str, Any]]:
        """Auto-generate research topics from title."""
        
        # Extract key terms from title/topic
        topics = {}
        
        # General topic research
        topics[topic] = {
            "type": "general",
            "focus_areas": ["current trends", "key players", "impact and significance"]
        }
        
        # If it looks like a movie title, add TMDB research
        if any(word in title.lower() for word in ["film", "movie", "cinematic", "analysis"]):
            # Try to extract movie name (first part before ":")
            movie_name = title.split(":")[0].strip()
            topics[movie_name] = {"type": "tmdb_movie"}
        
        return topics
    
    async def close(self):
        """Cleanup resources."""
        await self.research_engine.close()


async def main():
    parser = argparse.ArgumentParser(description="AI Video Production Orchestrator")
    
    # Single video mode
    parser.add_argument("--title", type=str, help="Video title")
    parser.add_argument("--topic", type=str, help="Main topic")
    parser.add_argument("--type", default="educational", type=str, help="Video type")
    parser.add_argument("--duration", default=600, type=int, help="Target duration in seconds")
    
    # Batch mode
    parser.add_argument("--batch", type=str, help="JSON file with batch of videos")
    
    # Skip phases
    parser.add_argument("--skip-research", action="store_true", help="Skip research phase")
    parser.add_argument("--skip-script", action="store_true", help="Skip script generation")
    parser.add_argument("--skip-audio", action="store_true", help="Skip audio generation")
    
    args = parser.parse_args()
    
    # Validate API configuration
    logger.info("🔐 Checking API configuration...")
    api_status = credentials.validate()
    
    required_apis = {
        "gemini": "Gemini API (for research & scripting)",
    }
    
    missing = [name for name, required in required_apis.items() if not api_status.get(name)]
    if missing:
        logger.error(f"❌ Missing required APIs: {missing}")
        logger.error("   Add API keys to .env file")
        return 1
    
    logger.info(f"✓ APIs configured: {', '.join(k for k, v in api_status.items() if v)}")
    
    orchestrator = ProductionOrchestrator()
    
    try:
        if args.batch:
            # Batch mode: read videos from JSON
            logger.info(f"\n📂 Loading batch from: {args.batch}")
            with open(args.batch) as f:
                batch = json.load(f)
            
            for video in batch.get("videos", []):
                await orchestrator.produce_video(
                    title=video["title"],
                    topic=video["topic"],
                    video_type=video.get("type", "educational"),
                    target_duration=video.get("duration", 600),
                    skip_research=args.skip_research,
                    skip_script=args.skip_script,
                    skip_audio=args.skip_audio
                )
        
        else:
            # Single video mode
            if not args.title or not args.topic:
                parser.print_help()
                logger.error("❌ Must provide --title and --topic for single video mode, or --batch for batch mode")
                return 1
            
            await orchestrator.produce_video(
                title=args.title,
                topic=args.topic,
                video_type=args.type,
                target_duration=args.duration,
                skip_research=args.skip_research,
                skip_script=args.skip_script,
                skip_audio=args.skip_audio
            )
    
    finally:
        await orchestrator.close()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
