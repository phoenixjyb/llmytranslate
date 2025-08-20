#!/usr/bin/env python3
"""
Download REAL, production-ready models for TensorFlow Lite conversion.
Focus on models that are actually available and convertible in 2025.
"""

import os
import requests
import logging
from pathlib import Path
import subprocess
import tempfile
import zipfile
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealModelDownloader:
    def __init__(self):
        self.models_dir = Path("./models/")
        self.models_dir.mkdir(exist_ok=True)
        
        # Focus on models that are actually available without authentication
        self.available_models = {
            # Small, working LLMs
            "tinyllama_1b": {
                "type": "llm",
                "source": "huggingface",
                "model_id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                "description": "TinyLlama 1.1B Chat - Small but functional LLM",
                "no_auth_required": True,
                "convertible": True
            },
            
            # Text processing models that work well
            "universal_sentence_encoder": {
                "type": "text_processing", 
                "source": "tfhub",
                "url": "https://tfhub.dev/google/universal-sentence-encoder/4",
                "description": "Universal Sentence Encoder for text embeddings",
                "no_auth_required": True,
                "convertible": True
            },
            
            # Pre-converted TFLite models
            "bert_text_classifier": {
                "type": "text_classifier",
                "source": "direct",
                "url": "https://storage.googleapis.com/download.tensorflow.org/models/tflite/task_library/text_classification/nl_classifier.tflite",
                "description": "BERT-based text classifier (pre-converted)",
                "no_auth_required": True,
                "convertible": False  # Already TFLite
            },
            
            # TTS models - focus on available ones
            "tacotron2_wavernn": {
                "type": "tts",
                "source": "github",
                "url": "https://github.com/fatchord/WaveRNN/releases/download/v1.0/ljspeech_mol.wavernn.tar",
                "description": "WaveRNN vocoder for TTS",
                "no_auth_required": True,
                "convertible": True
            },
            
            # Alternative small LLM
            "distilbert_base": {
                "type": "llm",
                "source": "huggingface",
                "model_id": "distilbert-base-uncased",
                "description": "DistilBERT base model",
                "no_auth_required": True,
                "convertible": True
            }
        }
    
    def check_huggingface_cli(self) -> bool:
        """Check if huggingface_hub CLI is available."""
        try:
            result = subprocess.run(['huggingface-cli', '--help'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            logger.warning("huggingface-cli not found. Install with: pip install huggingface_hub[cli]")
            return False
    
    def download_huggingface_model(self, model_id: str, model_name: str) -> bool:
        """Download model from Hugging Face."""
        if not self.check_huggingface_cli():
            return False
            
        try:
            model_dir = self.models_dir / model_name
            model_dir.mkdir(exist_ok=True)
            
            logger.info(f"Downloading {model_id} from Hugging Face...")
            
            # Use huggingface-cli to download
            cmd = [
                'huggingface-cli', 'download', 
                model_id,
                '--local-dir', str(model_dir),
                '--local-dir-use-symlinks', 'False'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                logger.info(f"✅ Successfully downloaded {model_name}")
                return True
            else:
                logger.error(f"❌ Failed to download {model_name}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Download timeout for {model_name}")
            return False
        except Exception as e:
            logger.error(f"❌ Error downloading {model_name}: {e}")
            return False
    
    def download_direct_url(self, url: str, filename: str) -> bool:
        """Download file directly from URL."""
        try:
            filepath = self.models_dir / filename
            
            logger.info(f"Downloading from {url}...")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, stream=True, timeout=120)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(filepath, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\rProgress: {progress:.1f}%", end='', flush=True)
            
            print()  # New line
            
            size_mb = filepath.stat().st_size / (1024 * 1024)
            logger.info(f"✅ Downloaded {filename}: {size_mb:.1f}MB")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to download {filename}: {e}")
            return False
    
    def download_and_extract_archive(self, url: str, model_name: str) -> bool:
        """Download and extract archive files."""
        try:
            logger.info(f"Downloading archive from {url}...")
            
            with tempfile.NamedTemporaryFile(suffix='.tar', delete=False) as tmp_file:
                response = requests.get(url, timeout=120)
                response.raise_for_status()
                tmp_file.write(response.content)
                tmp_path = tmp_file.name
            
            # Extract to model directory
            model_dir = self.models_dir / model_name
            model_dir.mkdir(exist_ok=True)
            
            # Try to extract (assuming tar format)
            import tarfile
            try:
                with tarfile.open(tmp_path, 'r') as tar:
                    tar.extractall(path=model_dir)
                logger.info(f"✅ Extracted {model_name}")
                return True
            except tarfile.ReadError:
                # Maybe it's a different format
                logger.warning(f"Could not extract as tar file: {model_name}")
                return False
            finally:
                os.unlink(tmp_path)
                
        except Exception as e:
            logger.error(f"❌ Failed to download archive {model_name}: {e}")
            return False
    
    def download_available_models(self) -> Dict[str, bool]:
        """Download all available models that don't require authentication."""
        results = {}
        
        logger.info("🚀 Downloading REAL models without authentication requirements...")
        logger.info("="*60)
        
        for model_name, config in self.available_models.items():
            if not config.get("no_auth_required", False):
                logger.info(f"⏭️ Skipping {model_name} - requires authentication")
                results[model_name] = False
                continue
            
            logger.info(f"\n📥 Downloading {model_name}...")
            logger.info(f"   Description: {config['description']}")
            logger.info(f"   Type: {config['type']}")
            
            success = False
            
            if config['source'] == 'huggingface':
                success = self.download_huggingface_model(
                    config['model_id'], 
                    model_name
                )
            elif config['source'] == 'direct':
                filename = f"{model_name}.tflite"
                success = self.download_direct_url(config['url'], filename)
            elif config['source'] == 'github':
                success = self.download_and_extract_archive(config['url'], model_name)
            elif config['source'] == 'tfhub':
                # TensorFlow Hub models need special handling
                logger.info(f"   TensorFlow Hub models need manual conversion")
                success = False
            
            results[model_name] = success
            
            if success:
                logger.info(f"   ✅ {model_name} downloaded successfully")
            else:
                logger.info(f"   ❌ {model_name} download failed")
        
        return results
    
    def check_coqui_tts_availability(self) -> bool:
        """Check if we can install and use Coqui TTS."""
        try:
            import TTS
            logger.info("✅ Coqui TTS already installed")
            return True
        except ImportError:
            logger.info("⚠️ Coqui TTS not installed")
            logger.info("   Install with: pip install coqui-tts")
            return False
    
    def suggest_next_steps(self, results: Dict[str, bool]):
        """Suggest next steps based on download results."""
        logger.info("\n" + "="*60)
        logger.info("DOWNLOAD RESULTS & NEXT STEPS")
        logger.info("="*60)
        
        successful = [name for name, success in results.items() if success]
        failed = [name for name, success in results.items() if not success]
        
        logger.info(f"✅ Successful downloads: {len(successful)}")
        for name in successful:
            logger.info(f"   - {name}")
        
        logger.info(f"\n❌ Failed downloads: {len(failed)}")
        for name in failed:
            logger.info(f"   - {name}")
        
        if successful:
            logger.info(f"\n🔧 NEXT STEPS FOR SUCCESSFUL DOWNLOADS:")
            logger.info(f"1. Convert Hugging Face models to TensorFlow Lite format")
            logger.info(f"2. Test the pre-converted TFLite models")
            logger.info(f"3. Optimize models for mobile deployment")
            
            logger.info(f"\n📋 CONVERSION COMMANDS:")
            for name in successful:
                config = self.available_models[name]
                if config.get('convertible', False) and config['source'] == 'huggingface':
                    logger.info(f"   # Convert {name}")
                    logger.info(f"   python scripts/convert_to_tflite.py --model {name}")
        
        if failed:
            logger.info(f"\n💡 ALTERNATIVES FOR FAILED DOWNLOADS:")
            logger.info(f"1. Install Coqui TTS for real TTS models: pip install coqui-tts")
            logger.info(f"2. Use Google Colab for models requiring authentication")
            logger.info(f"3. Check TensorFlow Hub for pre-converted models")
        
        # Check for TTS options
        if not self.check_coqui_tts_availability():
            logger.info(f"\n🔊 FOR TTS MODELS:")
            logger.info(f"   pip install coqui-tts")
            logger.info(f"   tts --list_models  # See available models")
            logger.info(f"   # Then convert to TFLite format")

def main():
    """Download real models that are actually available."""
    downloader = RealModelDownloader()
    results = downloader.download_available_models()
    downloader.suggest_next_steps(results)

if __name__ == "__main__":
    main()
