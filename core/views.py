from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.utils import timezone
from .models import Video, Comment, Like, Subscription, WatchHistory # Import WatchHistory
from .recommendation import get_content_based_recommendations, get_user_recommendations # Import logic
from .forms import VideoUploadForm, CommentForm, RegisterForm
from .utils import upload_to_imagekit


def home(request):
    # If user is logged in, use our new recommendation engine
    if request.user.is_authenticated:
        # Get personalized recommendations
        recommended_videos = get_user_recommendations(request.user)
        # Also get all videos for a "Latest" section if you want
        latest_videos = Video.objects.all().order_by('-created_at')[:8]

        context = {
            'videos': latest_videos,
            'recommended_videos': recommended_videos,
            'section_title': 'Recommended for You'
        }
    else:
        # Default behavior for anonymous users
        videos = Video.objects.all().order_by('-created_at')
        context = {'videos': videos, 'section_title': 'Latest Videos'}

    return render(request, 'home.html', context)


@login_required
def upload_video(request):
    if request.method == 'POST':
        form = VideoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # 1. Upload Video to ImageKit
                vid_file = request.FILES['video_file']
                vid_response = upload_to_imagekit(vid_file, vid_file.name)

                # 2. Upload Thumbnail to ImageKit
                thumb_file = request.FILES['thumbnail_file']
                thumb_response = upload_to_imagekit(thumb_file, thumb_file.name)

                # 3. Save to DB
                video = form.save(commit=False)
                video.user = request.user
                video.video_url = vid_response.url
                video.video_file_id = vid_response.file_id
                video.thumbnail_url = thumb_response.url
                video.save()

                messages.success(request, "Video uploaded successfully!")
                return redirect('home')
            except Exception as e:
                messages.error(request, f"Upload failed: {str(e)}")
    else:
        form = VideoUploadForm()
    return render(request, 'upload.html', {'form': form})

def video_detail(request, video_id):
    video = get_object_or_404(Video, pk=video_id)

    # 1. Record Watch History (if logged in)
    if request.user.is_authenticated:
        # Update timestamp if already exists, or create new
        WatchHistory.objects.update_or_create(
            user=request.user,
            video=video,
            defaults={'viewed_at': timezone.now()} # Import timezone from django.utils
        )

    # Simple View Counter (In production, use Redis/Session to prevent spam)
    video.views += 1
    video.save()

    # 3. Get Recommendations (The "Up Next" list)
    up_next_videos = get_content_based_recommendations(video)

    comments = video.comments.all().order_by('-created_at')
    comment_form = CommentForm()

    is_liked = False
    is_subscribed = False

    if request.user.is_authenticated:
        is_liked = Like.objects.filter(user=request.user, video=video).exists()
        is_subscribed = Subscription.objects.filter(subscriber=request.user, channel=video.user).exists()

        if request.method == 'POST' and 'comment_submit' in request.POST:
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.user = request.user
                comment.video = video
                comment.save()
                return redirect('video_detail', video_id=video_id)

    return render(request, 'video_detail.html', {
        'video': video,
        'comments': comments,
        'comment_form': comment_form,
        'is_liked': is_liked,
        'is_subscribed': is_subscribed,
        'likes_count': video.likes.count(),
        'subs_count': video.user.subscribers.count(),
        'up_next_videos': up_next_videos,  # Pass this to template
    })

@login_required
def like_video(request, video_id):
    video = get_object_or_404(Video, pk=video_id)
    like_qs = Like.objects.filter(user=request.user, video=video)
    if like_qs.exists():
        like_qs.delete()
    else:
        Like.objects.create(user=request.user, video=video)
    return redirect('video_detail', video_id=video_id)

@login_required
def subscribe_channel(request, channel_id):
    channel_user = get_object_or_404(User, pk=channel_id)
    if request.user != channel_user:
        sub_qs = Subscription.objects.filter(subscriber=request.user, channel=channel_user)
        if sub_qs.exists():
            sub_qs.delete()
        else:
            Subscription.objects.create(subscriber=request.user, channel=channel_user)
    return redirect('video_detail', video_id=request.META.get('HTTP_REFERER').split('/')[-2])

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(**form.cleaned_data)
            login(request, user)
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})