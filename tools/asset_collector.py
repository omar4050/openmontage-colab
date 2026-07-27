"""
Asset collection engine for zero-cost video production.

Orchestrates parallel asset collection from:
- Pexels API (video footage, images)
- Pixabay API (images, videos)
- Internet Archive (public domain video/audio)
- Gemini (asset search strategy)

All free tier APIs. Caches results to avoid re-fetching.
Automatically downloads and organizes assets by scene/segment.
"""

import json
import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime
import hashlib
import logging
from dataclasses import dataclass, asdict

import aiohttp
import requests
from tools.production_config import config, credentials

logger = logging.getLogger(__name__)


@dataclass
class AssetMetadata:
    """Metadata for a collected asset."""
    asset_id: str
    type: str  # "video", "image", "audio"
    source: str  # "pexels", "pixabay", "internet_archive", "gemini_generated"
    filename: str
    path: str
    width: int
    height: int
    duration_seconds: Optional[float] = None  # For video/audio
    url: str = ""
    license: str = ""
    attribution: str = ""
    search_query: str = ""
    timestamp: str = ""
    cost_usd: float = 0.0


@dataclass
class AssetSearchRequest:
    """Request to find assets for a scene."""
    scene_id: str
    scene_description: str
    type: str  # "video", "image", "mixed"
    duration_seconds: int
    style: str  # "cinematic", "documentary", "educational", "abstract"


@dataclass
class AssetManifest:
    """Complete manifest of collected assets for a video."""
    video_title: str
    total_assets: int
    assets: List[AssetMetadata]
    organized_by_segment: Dict[str, List[AssetMetadata]]
    total_cost_usd: float
    timestamp: str


class AssetCache:
    """File-based cache for asset metadata."""
    
    def __init__(self, cache_dir: Path = config.CACHE_DIR / "assets"):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _hash_query(self, query: str, asset_type: str, source: str) -> str:
        """Generate cache key from query."""
        key = f"{source}:{asset_type}:{query}".lower()
        return hashlib.md5(key.encode()).hexdigest()
    
    def get(self, query: str, asset_type: str, source: str) -> Optional[List[Dict[str, Any]]]:
        """Retrieve cached asset metadata."""
        cache_file = self.cache_dir / f"{self._hash_query(query, asset_type, source)}.json"
        if cache_file.exists():
            with open(cache_file) as f:
                return json.load(f)
        return None
    
    def save(self, query: str, asset_type: str, source: str, data: List[Dict[str, Any]]) -> None:
        """Save asset metadata to cache."""
        cache_file = self.cache_dir / f"{self._hash_query(query, asset_type, source)}.json"
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)


class AssetCollector:
    """Orchestrates asset collection from all sources."""
    
    def __init__(self):
        self.cache = AssetCache()
        self.session: Optional[aiohttp.ClientSession] = None
        
        # API endpoints
        self.pexels_base = "https://api.pexels.com/v1"
        self.pixabay_base = "https://pixabay.com/api"
        self.archive_base = "https://archive.org/advancedsearch.php"
        
        # Rate limits (free tier conservative)
        self.pexels_rate_limit = 1  # requests per second
        self.pixabay_rate_limit = 1
        self.archive_rate_limit = 1
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    # ==================== PEXELS ====================
    
    async def search_pexels_videos(
        self, 
        query: str, 
        duration_seconds: int = 30,
        max_results: int = 5
    ) -> List[AssetMetadata]:
        """Search Pexels for video footage."""
        if not credentials.PEXELS_API_KEY:
            logger.warning("Pexels API key not configured")
            return []
        
        # Check cache first
        cached = self.cache.get(query, "video", "pexels")
        if cached:
            logger.info(f"[CACHE HIT] Pexels videos for '{query}'")
            return [AssetMetadata(**item) for item in cached]
        
        logger.info(f"[PEXELS] Searching for video: '{query}'")
        
        try:
            url = f"{self.pexels_base}/videos"
            headers = {"Authorization": credentials.PEXELS_API_KEY}
            params = {
                "query": query,
                "per_page": max_results,
                "page": 1
            }
            
            async with self.session.get(url, headers=headers, params=params) as resp:
                if resp.status != 200:
                    logger.warning(f"Pexels API error: {resp.status}")
                    return []
                
                data = await resp.json()
                videos = data.get("videos", [])
                
                assets = []
                for video in videos:
                    # Find best video file (highest quality)
                    best_video_file = None
                    for vf in video.get("video_files", []):
                        if vf.get("type") == "video/mp4":
                            if not best_video_file or vf.get("width", 0) > best_video_file.get("width", 0):
                                best_video_file = vf
                    
                    if best_video_file:
                        asset = AssetMetadata(
                            asset_id=f"pexels_{video['id']}",
                            type="video",
                            source="pexels",
                            filename=f"pexels_{video['id']}.mp4",
                            path=str(config.ASSETS_DIR / "video" / f"pexels_{video['id']}.mp4"),
                            width=best_video_file.get("width", 1280),
                            height=best_video_file.get("height", 720),
                            duration_seconds=best_video_file.get("duration", 30),
                            url=best_video_file.get("link", ""),
                            license="Creative Commons CC0",
                            attribution=f"© {video.get('user', {}).get('name', 'Pexels')}",
                            search_query=query,
                            timestamp=datetime.now().isoformat(),
                            cost_usd=0.0
                        )
                        assets.append(asset)
                
                # Cache results
                self.cache.save(
                    query, "video", "pexels",
                    [asdict(a) for a in assets]
                )
                
                logger.info(f"[PEXELS] Found {len(assets)} videos for '{query}'")
                return assets
        
        except Exception as e:
            logger.error(f"Pexels search error: {e}")
            return []
    
    async def search_pexels_images(
        self,
        query: str,
        max_results: int = 5
    ) -> List[AssetMetadata]:
        """Search Pexels for images."""
        if not credentials.PEXELS_API_KEY:
            logger.warning("Pexels API key not configured")
            return []
        
        cached = self.cache.get(query, "image", "pexels")
        if cached:
            logger.info(f"[CACHE HIT] Pexels images for '{query}'")
            return [AssetMetadata(**item) for item in cached]
        
        logger.info(f"[PEXELS] Searching for image: '{query}'")
        
        try:
            url = f"{self.pexels_base}/search"
            headers = {"Authorization": credentials.PEXELS_API_KEY}
            params = {
                "query": query,
                "per_page": max_results,
                "page": 1
            }
            
            async with self.session.get(url, headers=headers, params=params) as resp:
                if resp.status != 200:
                    logger.warning(f"Pexels API error: {resp.status}")
                    return []
                
                data = await resp.json()
                photos = data.get("photos", [])
                
                assets = []
                for photo in photos:
                    asset = AssetMetadata(
                        asset_id=f"pexels_{photo['id']}",
                        type="image",
                        source="pexels",
                        filename=f"pexels_{photo['id']}.jpg",
                        path=str(config.ASSETS_DIR / "image" / f"pexels_{photo['id']}.jpg"),
                        width=photo.get("width", 1280),
                        height=photo.get("height", 720),
                        url=photo.get("src", {}).get("medium", ""),
                        license="Creative Commons CC0",
                        attribution=f"© {photo.get('photographer', 'Pexels')}",
                        search_query=query,
                        timestamp=datetime.now().isoformat(),
                        cost_usd=0.0
                    )
                    assets.append(asset)
                
                self.cache.save(
                    query, "image", "pexels",
                    [asdict(a) for a in assets]
                )
                
                logger.info(f"[PEXELS] Found {len(assets)} images for '{query}'")
                return assets
        
        except Exception as e:
            logger.error(f"Pexels search error: {e}")
            return []
    
    # ==================== PIXABAY ====================
    
    async def search_pixabay_videos(
        self,
        query: str,
        max_results: int = 5
    ) -> List[AssetMetadata]:
        """Search Pixabay for video footage."""
        if not credentials.PIXABAY_API_KEY:
            logger.warning("Pixabay API key not configured")
            return []
        
        cached = self.cache.get(query, "video", "pixabay")
        if cached:
            logger.info(f"[CACHE HIT] Pixabay videos for '{query}'")
            return [AssetMetadata(**item) for item in cached]
        
        logger.info(f"[PIXABAY] Searching for video: '{query}'")
        
        try:
            params = {
                "key": credentials.PIXABAY_API_KEY,
                "q": query,
                "video_type": "film",
                "per_page": max_results,
                "page": 1
            }
            
            async with self.session.get(f"{self.pixabay_base}/videos", params=params) as resp:
                if resp.status != 200:
                    logger.warning(f"Pixabay API error: {resp.status}")
                    return []
                
                data = await resp.json()
                hits = data.get("hits", [])
                
                assets = []
                for video in hits:
                    # Use largest available video
                    video_file = video.get("videos", {})
                    best_video = video_file.get("large") or video_file.get("medium") or video_file.get("small")
                    
                    if best_video:
                        asset = AssetMetadata(
                            asset_id=f"pixabay_{video['id']}",
                            type="video",
                            source="pixabay",
                            filename=f"pixabay_{video['id']}.mp4",
                            path=str(config.ASSETS_DIR / "video" / f"pixabay_{video['id']}.mp4"),
                            width=best_video.get("width", 1280),
                            height=best_video.get("height", 720),
                            duration_seconds=best_video.get("duration", 30),
                            url=best_video.get("url", ""),
                            license="Creative Commons CC0 / Pixabay License",
                            attribution=f"© {video.get('user', 'Pixabay')}",
                            search_query=query,
                            timestamp=datetime.now().isoformat(),
                            cost_usd=0.0
                        )
                        assets.append(asset)
                
                self.cache.save(
                    query, "video", "pixabay",
                    [asdict(a) for a in assets]
                )
                
                logger.info(f"[PIXABAY] Found {len(assets)} videos for '{query}'")
                return assets
        
        except Exception as e:
            logger.error(f"Pixabay search error: {e}")
            return []
    
    async def search_pixabay_images(
        self,
        query: str,
        max_results: int = 5
    ) -> List[AssetMetadata]:
        """Search Pixabay for images."""
        if not credentials.PIXABAY_API_KEY:
            logger.warning("Pixabay API key not configured")
            return []
        
        cached = self.cache.get(query, "image", "pixabay")
        if cached:
            logger.info(f"[CACHE HIT] Pixabay images for '{query}'")
            return [AssetMetadata(**item) for item in cached]
        
        logger.info(f"[PIXABAY] Searching for image: '{query}'")
        
        try:
            params = {
                "key": credentials.PIXABAY_API_KEY,
                "q": query,
                "image_type": "photo",
                "per_page": max_results,
                "page": 1
            }
            
            async with self.session.get(f"{self.pixabay_base}", params=params) as resp:
                if resp.status != 200:
                    logger.warning(f"Pixabay API error: {resp.status}")
                    return []
                
                data = await resp.json()
                hits = data.get("hits", [])
                
                assets = []
                for image in hits:
                    asset = AssetMetadata(
                        asset_id=f"pixabay_{image['id']}",
                        type="image",
                        source="pixabay",
                        filename=f"pixabay_{image['id']}.jpg",
                        path=str(config.ASSETS_DIR / "image" / f"pixabay_{image['id']}.jpg"),
                        width=image.get("imageWidth", 1280),
                        height=image.get("imageHeight", 720),
                        url=image.get("largeImageURL", ""),
                        license="Creative Commons CC0 / Pixabay License",
                        attribution=f"© {image.get('user', 'Pixabay')}",
                        search_query=query,
                        timestamp=datetime.now().isoformat(),
                        cost_usd=0.0
                    )
                    assets.append(asset)
                
                self.cache.save(
                    query, "image", "pixabay",
                    [asdict(a) for a in assets]
                )
                
                logger.info(f"[PIXABAY] Found {len(assets)} images for '{query}'")
                return assets
        
        except Exception as e:
            logger.error(f"Pixabay search error: {e}")
            return []
    
    # ==================== INTERNET ARCHIVE ====================
    
    async def search_internet_archive(
        self,
        query: str,
        media_type: str = "movies",
        max_results: int = 3
    ) -> List[AssetMetadata]:
        """Search Internet Archive for public domain media."""
        cached = self.cache.get(query, media_type, "internet_archive")
        if cached:
            logger.info(f"[CACHE HIT] Internet Archive {media_type} for '{query}'")
            return [AssetMetadata(**item) for item in cached]
        
        logger.info(f"[ARCHIVE] Searching for {media_type}: '{query}'")
        
        try:
            # Build search query
            search_query = f"({query}) AND mediatype:({media_type})"
            params = {
                "q": search_query,
                "fl": "identifier,title,description,format,duration",
                "output": "json",
                "rows": max_results
            }
            
            async with self.session.get(self.archive_base, params=params) as resp:
                if resp.status != 200:
                    logger.warning(f"Internet Archive API error: {resp.status}")
                    return []
                
                data = await resp.json()
                docs = data.get("response", {}).get("docs", [])
                
                assets = []
                for doc in docs:
                    # Determine media type from formats
                    formats = doc.get("format", [])
                    asset_type = "video" if any("MP4" in f or "WebM" in f for f in formats) else "image"
                    
                    asset = AssetMetadata(
                        asset_id=f"archive_{doc['identifier']}",
                        type=asset_type,
                        source="internet_archive",
                        filename=f"archive_{doc['identifier']}",
                        path=str(config.ASSETS_DIR / asset_type / f"archive_{doc['identifier']}"),
                        width=1920,
                        height=1080,
                        url=f"https://archive.org/details/{doc['identifier']}",
                        license="Public Domain",
                        attribution=f"Internet Archive: {doc.get('title', 'Unknown')}",
                        search_query=query,
                        timestamp=datetime.now().isoformat(),
                        cost_usd=0.0
                    )
                    assets.append(asset)
                
                self.cache.save(
                    query, media_type, "internet_archive",
                    [asdict(a) for a in assets]
                )
                
                logger.info(f"[ARCHIVE] Found {len(assets)} items for '{query}'")
                return assets
        
        except Exception as e:
            logger.error(f"Internet Archive search error: {e}")
            return []
    
    # ==================== PARALLEL COLLECTION ====================
    
    async def collect_for_scene(
        self,
        scene_request: AssetSearchRequest,
        include_sources: List[str] = None
    ) -> List[AssetMetadata]:
        """Collect assets for a single scene from multiple sources in parallel."""
        if include_sources is None:
            include_sources = ["pexels", "pixabay", "internet_archive"]
        
        logger.info(f"[COLLECT] Gathering assets for scene: {scene_request.scene_id}")
        logger.info(f"  Query: {scene_request.scene_description}")
        logger.info(f"  Type: {scene_request.type}")
        
        tasks = []
        
        if scene_request.type in ["video", "mixed"] and "pexels" in include_sources:
            tasks.append(self.search_pexels_videos(scene_request.scene_description, max_results=3))
        
        if scene_request.type in ["video", "mixed"] and "pixabay" in include_sources:
            tasks.append(self.search_pixabay_videos(scene_request.scene_description, max_results=3))
        
        if scene_request.type in ["video", "mixed"] and "internet_archive" in include_sources:
            tasks.append(self.search_internet_archive(scene_request.scene_description, max_results=2))
        
        if scene_request.type in ["image", "mixed"] and "pexels" in include_sources:
            tasks.append(self.search_pexels_images(scene_request.scene_description, max_results=3))
        
        if scene_request.type in ["image", "mixed"] and "pixabay" in include_sources:
            tasks.append(self.search_pixabay_images(scene_request.scene_description, max_results=3))
        
        # Run all searches in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten and deduplicate by asset_id
        all_assets = []
        seen_ids = set()
        
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Asset search error: {result}")
                continue
            
            for asset in result:
                if asset.asset_id not in seen_ids:
                    all_assets.append(asset)
                    seen_ids.add(asset.asset_id)
        
        logger.info(f"[COLLECT] Found {len(all_assets)} unique assets for {scene_request.scene_id}")
        return all_assets
    
    async def collect_for_script(
        self,
        script_json: Dict[str, Any],
        video_title: str
    ) -> AssetManifest:
        """Collect all assets for a complete video script."""
        logger.info(f"[MANIFEST] Creating asset manifest for '{video_title}'")
        
        segments = script_json.get("segments", [])
        all_assets = []
        organized = {}
        total_cost = 0.0
        
        # Process each segment in parallel
        scene_tasks = []
        for i, segment in enumerate(segments):
            scene_id = f"segment_{i:02d}"
            b_roll_items = segment.get("suggested_broll", [])
            
            # Create a search request per B-roll item
            for broll in b_roll_items:
                if isinstance(broll, str):
                    scene_type = "video" if "footage" in broll.lower() or "clip" in broll.lower() else "image"
                else:
                    scene_type = broll.get("type", "video") if isinstance(broll, dict) else "video"
                    broll = broll.get("description", str(broll))
                
                request = AssetSearchRequest(
                    scene_id=scene_id,
                    scene_description=broll,
                    type=scene_type,
                    duration_seconds=segment.get("duration_seconds", 10),
                    style="documentary"
                )
                scene_tasks.append((scene_id, self.collect_for_scene(request)))
        
        # Run all parallel
        if scene_tasks:
            scene_results = await asyncio.gather(
                *[task for _, task in scene_tasks],
                return_exceptions=True
            )
            
            # Organize by segment
            for (scene_id, _), result in zip(scene_tasks, scene_results):
                if isinstance(result, Exception):
                    logger.warning(f"Failed to collect for {scene_id}: {result}")
                    continue
                
                organized[scene_id] = result
                all_assets.extend(result)
                total_cost += sum(a.cost_usd for a in result)
        
        manifest = AssetManifest(
            video_title=video_title,
            total_assets=len(all_assets),
            assets=all_assets,
            organized_by_segment=organized,
            total_cost_usd=total_cost,
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"[MANIFEST] Complete: {len(all_assets)} assets, ${total_cost:.4f}")
        return manifest
    
    async def download_asset(
        self,
        asset: AssetMetadata,
        output_path: Optional[Path] = None
    ) -> bool:
        """Download a single asset to disk."""
        if not asset.url:
            logger.warning(f"No URL for asset {asset.asset_id}")
            return False
        
        if output_path is None:
            output_path = Path(asset.path)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"[DOWNLOAD] {asset.asset_id} → {output_path}")
        
        try:
            async with self.session.get(asset.url, timeout=aiohttp.ClientTimeout(total=300)) as resp:
                if resp.status != 200:
                    logger.warning(f"Download failed: {asset.asset_id} ({resp.status})")
                    return False
                
                with open(output_path, 'wb') as f:
                    f.write(await resp.read())
                
                logger.info(f"[DOWNLOAD] Complete: {output_path.stat().st_size / 1024 / 1024:.1f} MB")
                return True
        
        except asyncio.TimeoutError:
            logger.error(f"Download timeout: {asset.asset_id}")
            return False
        except Exception as e:
            logger.error(f"Download error: {asset.asset_id} - {e}")
            return False
    
    async def download_manifest(
        self,
        manifest: AssetManifest,
        parallel: int = 2
    ) -> Dict[str, bool]:
        """Download all assets from a manifest (with concurrency limit)."""
        logger.info(f"[BATCH DOWNLOAD] Starting {len(manifest.assets)} downloads")
        
        results = {}
        semaphore = asyncio.Semaphore(parallel)
        
        async def bounded_download(asset):
            async with semaphore:
                return asset.asset_id, await self.download_asset(asset)
        
        tasks = [bounded_download(a) for a in manifest.assets]
        download_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in download_results:
            if isinstance(result, Exception):
                logger.warning(f"Download task error: {result}")
                continue
            
            asset_id, success = result
            results[asset_id] = success
        
        successful = sum(1 for v in results.values() if v)
        logger.info(f"[BATCH DOWNLOAD] Complete: {successful}/{len(manifest.assets)} succeeded")
        
        return results


async def collect_assets_for_video(
    script_path: Path,
    video_title: str,
    output_dir: Optional[Path] = None,
    download: bool = True
) -> AssetManifest:
    """
    High-level API: Load script → collect → download assets.
    
    Returns AssetManifest with all asset metadata.
    """
    if output_dir is None:
        output_dir = config.PRODUCTION_OUTPUT_DIR
    
    # Load script
    logger.info(f"[PIPELINE] Loading script from {script_path}")
    with open(script_path) as f:
        script = json.load(f)
    
    # Collect assets
    async with AssetCollector() as collector:
        manifest = await collector.collect_for_script(script, video_title)
        
        # Save manifest
        manifest_path = output_dir / "manifests" / f"{video_title}_asset_manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        
        manifest_data = {
            "video_title": manifest.video_title,
            "total_assets": manifest.total_assets,
            "assets": [asdict(a) for a in manifest.assets],
            "organized_by_segment": {
                seg: [asdict(a) for a in assets]
                for seg, assets in manifest.organized_by_segment.items()
            },
            "total_cost_usd": manifest.total_cost_usd,
            "timestamp": manifest.timestamp
        }
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f, indent=2)
        
        logger.info(f"[PIPELINE] Manifest saved to {manifest_path}")
        
        # Download assets if requested
        if download:
            async with AssetCollector() as downloader:
                await downloader.download_manifest(manifest, parallel=2)
        
        return manifest
