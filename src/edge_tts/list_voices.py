"""
list_voices package for edge_tts.
"""

import json
import ssl
from typing import Any, Dict, List, Optional

import aiohttp
import certifi

from .constants import VOICE_LIST


async def list_voices(*, proxy: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all available voices and their attributes from the Microsoft Edge URL.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing voice attributes.
    """
    ssl_ctx = ssl.create_default_context(cafile=certifi.where())

    async with aiohttp.ClientSession(trust_env=True) as session:
        try:
            async with session.get(
                VOICE_LIST,
                headers={
                    "Authority": "speech.platform.bing.com",
                    "Sec-CH-UA": '" Not;A Brand";v="99", "Microsoft Edge";v="91", "Chromium";v="91"',
                    "Sec-CH-UA-Mobile": "?0",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36 Edg/91.0.864.41",
                    "Accept": "*/*",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Dest": "empty",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept-Language": "en-US,en;q=0.9",
                },
                proxy=proxy,
                ssl=ssl_ctx,
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return data
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to fetch voice list: {e}")
        except json.JSONDecodeError:
            raise ValueError("Failed to decode the voice list response as JSON.")


class VoicesManager:
    """
    A class to manage and find voices based on their attributes.
    """

    def __init__(self, voices: Optional[List[Dict[str, Any]]] = None) -> None:
        """
        Initialize the VoicesManager with a list of voices.

        Args:
            voices (Optional[List[Dict[str, Any]]]): Optional list of voices to use.
        """
        self.voices: List[Dict[str, Any]] = voices or []
        self.is_initialized: bool = False

    @classmethod
    async def create(
        cls, custom_voices: Optional[List[Dict[str, Any]]] = None
    ) -> "VoicesManager":
        """
        Factory method to create a VoicesManager instance populated with available voices.

        Args:
            custom_voices (Optional[List[Dict[str, Any]]]): Optional pre-defined list of voices.

        Returns:
            VoicesManager: An instance of VoicesManager.
        """
        voices = await list_voices() if custom_voices is None else custom_voices
        manager = cls(voices)
        manager.voices = [
            {**voice, "Language": voice["Locale"].split("-")[0]}
            for voice in manager.voices
        ]
        manager.is_initialized = True
        return manager

    def find(self, **attributes: Any) -> List[Dict[str, Any]]:
        """
        Find all voices that match the provided attributes.

        Args:
            attributes (Dict[str, Any]): Key-value pairs of voice attributes to search for.

        Returns:
            List[Dict[str, Any]]: List of voices that match the provided attributes.
        """
        if not self.is_initialized:
            raise RuntimeError(
                "VoicesManager.find() called before VoicesManager.create()"
            )

        if not attributes:
            return self.voices

        matching_voices = [
            voice
            for voice in self.voices
            if all(voice.get(key) == value for key, value in attributes.items())
        ]
        return matching_voices
