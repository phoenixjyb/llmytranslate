"""
Streaming Text-to-Speech Service for Real-time Audio Generation

This service generates audio chunks as text is being streamed from the LLM,
reducing perceived latency and providing a more fluid conversation experience.
"""

import asyncio
import time
import re
import json
import base64
from typing import AsyncGenerator, Dict, Any, List, Optional
from dataclasses import dataclass
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class TextChunk:
    """Represents a chunk of text ready for TTS conversion."""
    text: str
    index: int
    is_final: bool = False
    priority: str = "normal"  # "high", "normal", "low"

@dataclass 
class AudioChunk:
    """Represents a generated audio chunk."""
    audio_data: bytes
    text: str
    index: int
    total_chunks: Optional[int] = None
    content_type: str = "audio/wav"
    processing_time: float = 0.0

class StreamingTTSService:
    """
    Advanced streaming TTS service that converts text chunks to audio
    as they arrive, enabling real-time speech synthesis.
    """
    
    def __init__(self, tts_service, chunk_size: int = 100, overlap_words: int = 2):
        """
        Initialize streaming TTS service.
        
        Args:
            tts_service: Base TTS service for audio generation
            chunk_size: Target characters per chunk
            overlap_words: Words to overlap between chunks for smoothness
        """
        self.tts_service = tts_service
        self.chunk_size = chunk_size
        self.overlap_words = overlap_words
        self.processing_queue = asyncio.Queue()
        self.active_sessions = {}
        
    async def stream_tts_from_llm(
        self,
        llm_text_stream: AsyncGenerator[str, None],
        session_id: str,
        language: str = "en",
        voice: str = "default",
        speed: float = 1.0,
        tts_mode: str = "fast"
    ) -> AsyncGenerator[AudioChunk, None]:
        """
        Convert streaming LLM text to streaming audio chunks.
        
        Args:
            llm_text_stream: Async generator yielding text chunks from LLM
            session_id: Unique session identifier
            language: Target language for TTS
            voice: Voice to use for TTS
            speed: Speech speed
            tts_mode: TTS quality mode
            
        Yields:
            AudioChunk: Generated audio chunks ready for playback
        """
        logger.info(f"🎵 Starting streaming TTS for session {session_id}")
        
        # Initialize session state
        session_state = {
            "text_buffer": "",
            "chunk_index": 0,
            "total_text": "",
            "last_overlap": "",
            "is_complete": False
        }
        self.active_sessions[session_id] = session_state
        
        try:
            # Process LLM text stream in chunks
            async for text_chunk in llm_text_stream:
                session_state["text_buffer"] += text_chunk
                session_state["total_text"] += text_chunk
                
                # Extract complete sentences/phrases for TTS
                tts_chunks = self._extract_tts_chunks(
                    session_state["text_buffer"], 
                    session_state["last_overlap"]
                )
                
                for chunk in tts_chunks:
                    # Generate audio for this chunk
                    audio_chunk = await self._generate_audio_chunk(
                        chunk, session_state["chunk_index"], 
                        language, voice, speed, tts_mode
                    )
                    
                    if audio_chunk:
                        yield audio_chunk
                        session_state["chunk_index"] += 1
                        
                    # Update overlap for smooth transitions
                    session_state["last_overlap"] = self._get_overlap_text(chunk.text)
                
                # Update text buffer (remove processed text)
                session_state["text_buffer"] = self._update_text_buffer(
                    session_state["text_buffer"], tts_chunks
                )
            
            # Process any remaining text
            if session_state["text_buffer"].strip():
                final_chunk = TextChunk(
                    text=session_state["text_buffer"].strip(),
                    index=session_state["chunk_index"],
                    is_final=True
                )
                
                audio_chunk = await self._generate_audio_chunk(
                    final_chunk, session_state["chunk_index"],
                    language, voice, speed, tts_mode
                )
                
                if audio_chunk:
                    audio_chunk.total_chunks = session_state["chunk_index"] + 1
                    yield audio_chunk
            
            session_state["is_complete"] = True
            logger.info(f"✅ Streaming TTS completed for session {session_id}")
            
        except Exception as e:
            logger.error(f"❌ Streaming TTS error for session {session_id}: {e}")
            raise
        finally:
            # Cleanup session
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
    
    def _extract_tts_chunks(self, text_buffer: str, last_overlap: str) -> List[TextChunk]:
        """
        Extract complete text chunks suitable for TTS from the buffer.
        
        Args:
            text_buffer: Current text buffer
            last_overlap: Text from previous chunk for smooth transitions
            
        Returns:
            List of TextChunk objects ready for TTS
        """
        chunks = []
        
        # Don't process if buffer is too small
        if len(text_buffer) < self.chunk_size and not self._has_sentence_end(text_buffer):
            return chunks
        
        # Split by sentence boundaries for natural breaks
        sentences = self._split_into_sentences(text_buffer)
        current_chunk = last_overlap
        
        for sentence in sentences:
            # Add sentence to current chunk
            test_chunk = current_chunk + " " + sentence if current_chunk else sentence
            
            # If chunk is getting too long, finalize it
            if len(test_chunk) >= self.chunk_size:
                if current_chunk.strip():  # Only add non-empty chunks
                    chunks.append(TextChunk(
                        text=current_chunk.strip(),
                        index=len(chunks)
                    ))
                current_chunk = sentence
            else:
                current_chunk = test_chunk
        
        # Handle remaining text
        if current_chunk.strip() and self._has_sentence_end(current_chunk):
            chunks.append(TextChunk(
                text=current_chunk.strip(),
                index=len(chunks)
            ))
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences for natural TTS breaks."""
        # Improved sentence splitting with common abbreviations handling
        sentence_endings = r'[.!?]+(?:\s+|$)'
        sentences = re.split(sentence_endings, text)
        
        # Filter out empty sentences and rejoin with punctuation
        result = []
        for i, sentence in enumerate(sentences[:-1]):  # Exclude last empty split
            if sentence.strip():
                # Add back the punctuation (simple approach)
                punctuation = "." if not any(p in sentence for p in '.!?') else ""
                result.append(sentence.strip() + punctuation)
        
        # Handle last sentence if it doesn't end with punctuation
        if sentences[-1].strip():
            result.append(sentences[-1].strip())
        
        return result
    
    def _has_sentence_end(self, text: str) -> bool:
        """Check if text ends with sentence punctuation."""
        return bool(re.search(r'[.!?]\s*$', text.strip()))
    
    def _get_overlap_text(self, text: str) -> str:
        """Get last few words for smooth chunk transitions."""
        words = text.split()
        if len(words) <= self.overlap_words:
            return text
        return " ".join(words[-self.overlap_words:])
    
    def _update_text_buffer(self, text_buffer: str, processed_chunks: List[TextChunk]) -> str:
        """Update text buffer by removing processed text."""
        if not processed_chunks:
            return text_buffer
        
        # Calculate total processed text length
        total_processed = sum(len(chunk.text) for chunk in processed_chunks)
        
        # Remove processed text from buffer (with some safety margin)
        remaining_text = text_buffer[total_processed:].lstrip()
        return remaining_text
    
    async def _generate_audio_chunk(
        self,
        text_chunk: TextChunk,
        chunk_index: int,
        language: str,
        voice: str,
        speed: float,
        tts_mode: str
    ) -> Optional[AudioChunk]:
        """
        Generate audio for a single text chunk.
        
        Args:
            text_chunk: Text chunk to convert
            chunk_index: Index of this chunk
            language: Target language
            voice: Voice to use
            speed: Speech speed
            tts_mode: TTS quality mode
            
        Returns:
            AudioChunk with generated audio data
        """
        start_time = time.time()
        
        try:
            # Skip empty or very short chunks
            if not text_chunk.text or len(text_chunk.text.strip()) < 3:
                return None
            
            logger.debug(f"🎵 Generating audio for chunk {chunk_index}: '{text_chunk.text[:50]}...'")
            
            # Generate audio using the base TTS service
            tts_result = await self.tts_service.synthesize_speech_api(
                text=text_chunk.text,
                language=language,
                voice=voice,
                speed=speed,
                tts_mode=tts_mode
            )
            
            if not tts_result.get("success"):
                logger.warning(f"⚠️ TTS failed for chunk {chunk_index}: {tts_result.get('error')}")
                return None
            
            # Create audio chunk
            audio_chunk = AudioChunk(
                audio_data=base64.b64decode(tts_result["audio_data"]),
                text=text_chunk.text,
                index=chunk_index,
                content_type=tts_result.get("content_type", "audio/wav"),
                processing_time=time.time() - start_time
            )
            
            logger.debug(f"✅ Audio chunk {chunk_index} generated in {audio_chunk.processing_time:.2f}s")
            return audio_chunk
            
        except Exception as e:
            logger.error(f"❌ Error generating audio for chunk {chunk_index}: {e}")
            return None

class LLMTextStreamSimulator:
    """
    Simulates streaming LLM text generation for testing.
    In production, this would be replaced by actual LLM streaming.
    """
    
    @staticmethod
    async def simulate_llm_stream(text: str, chunk_delay: float = 0.1) -> AsyncGenerator[str, None]:
        """
        Simulate LLM text streaming by yielding characters/words gradually.
        
        Args:
            text: Complete text to stream
            chunk_delay: Delay between chunks to simulate typing
            
        Yields:
            str: Text chunks as they would come from LLM
        """
        words = text.split()
        current_chunk = ""
        
        for i, word in enumerate(words):
            current_chunk += word + " "
            
            # Yield chunks of varying sizes to simulate real LLM behavior
            if (i + 1) % 3 == 0 or i == len(words) - 1:  # Every 3 words or last word
                yield current_chunk
                current_chunk = ""
                await asyncio.sleep(chunk_delay)

# Example usage and testing
async def test_streaming_tts():
    """Test the streaming TTS service."""
    from src.services.tts_service import CachedTTSService
    
    # Initialize services
    base_tts = CachedTTSService()
    streaming_tts = StreamingTTSService(base_tts, chunk_size=80)
    
    # Test text
    test_text = """
    Hello there! I'm going to demonstrate the new streaming text-to-speech feature. 
    This system generates audio chunks as the text is being written, rather than waiting 
    for the complete response. This creates a much more fluid and natural conversation 
    experience. You'll notice that the audio starts playing almost immediately, 
    and continues as more text becomes available. This is particularly useful for 
    long responses where waiting for the complete text would create significant delays.
    """
    
    # Simulate LLM streaming
    llm_stream = LLMTextStreamSimulator.simulate_llm_stream(test_text, chunk_delay=0.2)
    
    # Process with streaming TTS
    session_id = "test_session_001"
    audio_chunks = []
    
    logger.info("🎵 Starting streaming TTS test...")
    
    async for audio_chunk in streaming_tts.stream_tts_from_llm(
        llm_stream, session_id, language="en", tts_mode="fast"
    ):
        audio_chunks.append(audio_chunk)
        logger.info(
            f"📦 Generated audio chunk {audio_chunk.index}: "
            f"{len(audio_chunk.audio_data)} bytes, "
            f"'{audio_chunk.text[:30]}...', "
            f"({audio_chunk.processing_time:.2f}s)"
        )
    
    logger.info(f"✅ Streaming TTS test completed: {len(audio_chunks)} chunks generated")
    return audio_chunks

if __name__ == "__main__":
    # Run test
    asyncio.run(test_streaming_tts())
