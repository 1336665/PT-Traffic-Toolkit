from __future__ import annotations

from typing import Iterable

from app.services.downloader.base import TorrentInfo


def score_torrent(torrent: TorrentInfo) -> tuple[float, str]:
    ratio_score = min(torrent.ratio, 5.0) / 5.0
    activity_score = 1.0 if torrent.status == "downloading" else 0.3 if torrent.status == "seeding" else 0.1
    speed_score = min((torrent.upload_speed + torrent.download_speed) / (5 * 1024 * 1024), 1.0)
    seeding_score = min(torrent.seeding_time / (7 * 24 * 3600), 1.0)
    score = (ratio_score * 0.35) + (activity_score * 0.25) + (speed_score * 0.2) + (seeding_score * 0.2)

    if score >= 0.7:
        recommendation = "keep"
    elif score >= 0.45:
        recommendation = "watch"
    else:
        recommendation = "archive"

    return score, recommendation


def score_torrents(torrents: Iterable[TorrentInfo]) -> list[dict]:
    scored = []
    for torrent in torrents:
        score, recommendation = score_torrent(torrent)
        scored.append({
            "hash": torrent.hash,
            "name": torrent.name,
            "score": round(score * 100, 2),
            "ratio": torrent.ratio,
            "seeding_time": torrent.seeding_time,
            "upload_speed": torrent.upload_speed,
            "download_speed": torrent.download_speed,
            "status": torrent.status,
            "recommendation": recommendation,
        })
    return scored
