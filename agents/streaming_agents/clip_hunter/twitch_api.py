"""Kleiner Twitch-Helix-Client für VOD-Startzeit und Zuschauer-Clips.

Benötigt eine kostenlose Twitch-Entwickler-App (Client-ID + Client-Secret) und nutzt ein
App-Token (Client-Credentials). Zugangsdaten kommen aus Umgebungsvariablen und werden
nie ausgegeben oder gespeichert.
"""
import json
import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from pydantic import BaseModel, Field

TOKEN_URL = "https://id.twitch.tv/oauth2/token"
HELIX_URL = "https://api.twitch.tv/helix"
VIDEO_ID_PATTERN = re.compile(r"^\d{5,15}$")
_DURATION = re.compile(r"^(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$")


class TwitchApiError(RuntimeError):
    """Fehler bei der Twitch-API ohne Zugangsdaten im Text."""


class ViewerClip(BaseModel):
    id: str = ""
    title: str = ""
    url: str = ""
    vod_offset: float = Field(ge=0, description="Start des Clips in Sekunden ab VOD-Beginn")
    duration: float = Field(gt=0, le=120)
    view_count: int = Field(default=0, ge=0)
    created_at: str = ""


@dataclass(frozen=True)
class VideoInfo:
    id: str
    user_id: str
    user_login: str
    title: str
    created_at: datetime
    duration_seconds: int
    url: str

    @property
    def started_at(self) -> float:
        return self.created_at.timestamp()


def parse_twitch_duration(text: str) -> int:
    match = _DURATION.fullmatch(text.strip())
    if not text.strip() or not match:
        raise TwitchApiError(f"Unbekanntes Dauer-Format: {text!r}")
    hours, minutes, seconds = (int(part) if part else 0 for part in match.groups())
    return hours * 3600 + minutes * 60 + seconds


def parse_video_id(value: str) -> str:
    """Akzeptiert eine VOD-ID oder einen Link wie https://www.twitch.tv/videos/123456789."""
    candidate = value.strip().rstrip("/")
    if "/videos/" in candidate:
        candidate = candidate.split("/videos/", 1)[1].split("?", 1)[0]
    candidate = candidate.lstrip("v")
    if not VIDEO_ID_PATTERN.fullmatch(candidate):
        raise TwitchApiError("Ungültige Twitch-VOD-ID oder -Link.")
    return candidate


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class HelixClient:
    def __init__(self, client_id: str, client_secret: str, *,
                 opener: Callable[..., object] = urlopen, timeout: float = 20):
        if not client_id or not client_secret:
            raise TwitchApiError("Twitch-Client-ID und -Secret fehlen.")
        self._client_id = client_id
        self._client_secret = client_secret
        self._open = opener
        self._timeout = timeout
        self._token: str | None = None

    @classmethod
    def from_env(cls, **kwargs) -> "HelixClient":
        client_id = os.environ.get("TWITCH_CLIENT_ID", "").strip()
        secret = os.environ.get("TWITCH_CLIENT_SECRET", "").strip()
        if not client_id or not secret:
            raise TwitchApiError(
                "Bitte TWITCH_CLIENT_ID und TWITCH_CLIENT_SECRET als Umgebungsvariablen setzen "
                "(kostenlose App unter https://dev.twitch.tv/console)."
            )
        return cls(client_id, secret, **kwargs)

    def _request(self, request: Request) -> dict:
        try:
            with self._open(request, timeout=self._timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code in (401, 403):
                raise TwitchApiError(
                    "Twitch hat die Anmeldung abgelehnt (Client-ID/Secret prüfen)."
                ) from None
            if exc.code == 429:
                raise TwitchApiError("Twitch-Anfragelimit erreicht; später erneut versuchen.") \
                    from None
            raise TwitchApiError(f"Twitch-API-Fehler (HTTP {exc.code}).") from None
        except (URLError, TimeoutError, OSError) as exc:
            raise TwitchApiError(f"Twitch nicht erreichbar ({type(exc).__name__}).") from None
        except json.JSONDecodeError:
            raise TwitchApiError("Unerwartete Antwort von Twitch.") from None

    def _token_value(self) -> str:
        if self._token is None:
            body = urlencode({"client_id": self._client_id, "client_secret": self._client_secret,
                              "grant_type": "client_credentials"}).encode()
            payload = self._request(Request(TOKEN_URL, data=body, method="POST", headers={
                "Content-Type": "application/x-www-form-urlencoded"}))
            token = payload.get("access_token")
            if not isinstance(token, str) or not token:
                raise TwitchApiError("Twitch hat kein Zugriffstoken geliefert.")
            self._token = token
        return self._token

    def get(self, path: str, params: list[tuple[str, str]]) -> dict:
        url = f"{HELIX_URL}/{path}?{urlencode(params)}"
        return self._request(Request(url, headers={
            "Authorization": f"Bearer {self._token_value()}",
            "Client-Id": self._client_id,
        }))

    def get_video(self, video_id: str) -> VideoInfo:
        video_id = parse_video_id(video_id)
        data = self.get("videos", [("id", video_id)]).get("data") or []
        if not data:
            raise TwitchApiError("VOD nicht gefunden (gelöscht, privat oder falsche ID).")
        item = data[0]
        try:
            return VideoInfo(
                id=str(item["id"]), user_id=str(item["user_id"]),
                user_login=str(item.get("user_login", "")), title=str(item.get("title", "")),
                created_at=_parse_time(item["created_at"]),
                duration_seconds=parse_twitch_duration(item["duration"]),
                url=str(item.get("url", "")),
            )
        except (KeyError, ValueError, TypeError) as exc:
            raise TwitchApiError("Unerwartete VOD-Daten von Twitch.") from exc

    def get_viewer_clips(self, video: VideoInfo, *, max_pages: int = 20,
                         days_after: int = 14) -> list[ViewerClip]:
        """Alle Clips des Kanals, die aus diesem VOD stammen und eine VOD-Position haben."""
        started = video.created_at
        stream_end = started + timedelta(seconds=video.duration_seconds)
        # Auch Clips, die nach dem Stream aus dem VOD erstellt wurden, aber kein Datum
        # in der Zukunft an Twitch schicken.
        ended = max(stream_end, min(stream_end + timedelta(days=days_after), datetime.now(UTC)))
        params = [("broadcaster_id", video.user_id), ("started_at", _iso(started)),
                  ("ended_at", _iso(ended)), ("first", "100")]
        clips: list[ViewerClip] = []
        cursor = None
        for _ in range(max_pages):
            page = self.get("clips", params + ([("after", cursor)] if cursor else []))
            for item in page.get("data") or []:
                if str(item.get("video_id")) != video.id or item.get("vod_offset") is None:
                    continue
                try:
                    clips.append(ViewerClip(
                        id=str(item.get("id", "")), title=str(item.get("title", ""))[:200],
                        url=str(item.get("url", "")), vod_offset=float(item["vod_offset"]),
                        duration=float(item.get("duration") or 30),
                        view_count=int(item.get("view_count") or 0),
                        created_at=str(item.get("created_at", "")),
                    ))
                except (ValueError, TypeError):
                    continue
            cursor = (page.get("pagination") or {}).get("cursor")
            if not cursor:
                break
        unique = {clip.id or f"{clip.vod_offset}:{clip.duration}": clip for clip in clips}
        return sorted(unique.values(), key=lambda clip: clip.vod_offset)
