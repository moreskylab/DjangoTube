# core/recommendation.py
from django.db.models import Q, Count
from .models import Video, WatchHistory


def get_content_based_recommendations(current_video, limit=5):
    """
    Finds videos with similar words in the title.
    """
    # 1. Break title into keywords (remove short words)
    keywords = [word for word in current_video.title.split() if len(word) > 3]

    if not keywords:
        # Fallback: Return recent videos if no keywords found
        return Video.objects.exclude(id=current_video.id).order_by('-created_at')[:limit]

    # 2. Build a query that looks for any of these keywords in other titles
    query = Q()
    for word in keywords:
        query |= Q(title__icontains=word) | Q(description__icontains=word)

    # 3. Filter videos, exclude current one
    related_videos = Video.objects.filter(query).exclude(id=current_video.id).distinct()

    # 4. If we don't have enough matches, pad with recent videos
    if related_videos.count() < limit:
        remaining = limit - related_videos.count()
        recent_videos = Video.objects.exclude(id=current_video.id) \
            .exclude(id__in=related_videos.values_list('id', flat=True)) \
            .order_by('-created_at')[:remaining]
        # Combine querysets (using list conversion for simplicity)
        return list(related_videos) + list(recent_videos)

    return related_videos[:limit]


def get_user_recommendations(user, limit=8):
    """
    Finds videos based on user's watch history.
    """
    if not user.is_authenticated:
        # If not logged in, return most viewed videos
        return Video.objects.all().order_by('-views')[:limit]

    # 1. Get IDs of videos the user recently watched
    last_watched_ids = WatchHistory.objects.filter(user=user).values_list('video_id', flat=True)[:5]

    if not last_watched_ids:
        return Video.objects.all().order_by('-views')[:limit]

    # 2. Find videos from the SAME authors as the videos user watched
    # (Simple collaborative logic: if you like user X's video, show more from user X)
    suggested_videos = Video.objects.filter(
        user__videos__id__in=last_watched_ids
    ).exclude(
        id__in=last_watched_ids  # Don't recommend what they just watched
    ).distinct().order_by('?')[:limit]  # '?' orders randomly

    return suggested_videos