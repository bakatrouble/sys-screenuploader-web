import json
import os
from io import BytesIO
from tempfile import TemporaryDirectory

from PIL import Image
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpRequest, HttpResponseRedirect, Http404
from django.contrib.auth.views import LoginView as BaseLoginView
from django.shortcuts import redirect, get_object_or_404
from django.utils.text import slugify
from django.views import View
from django.views.generic import FormView, ListView, TemplateView, UpdateView
from django.views.generic.detail import SingleObjectMixin
from jsonview.views import JsonView
from moviepy.video.io.VideoFileClip import VideoFileClip

from users.models import User
from .forms import LoginForm, SignupForm, ConfigForm
from .models import Destination, UploadedMedia
from .modules import DESTINATION_MODULES
from .tasks import process_upload
from .utils import BaseDestinationView


class UploadView(JsonView):
    def post(self, request: HttpRequest, *args, **kwargs):
        filename = self.request.GET.get('filename')
        if not filename:
            return {'status': 'error', 'message': 'filename is missing'}, 400

        if filename.endswith('.jpg'):
            is_video = False
            mime = 'image/jpeg'
        elif filename.endswith('.mp4'):
            is_video = True
            mime = 'video/mp4'
        else:
            return {'status': 'error', 'message': 'incorrect file extension'}, 400

        try:
            if self.kwargs['destination_id'] == 'undefined':
                destination = Destination.objects.filter(shared=True).first()
                if not destination:
                    raise Destination.DoesNotExist
            else:
                destination = Destination.objects.get(pk=self.kwargs['destination_id'])
        except Destination.DoesNotExist:
            return {'status': 'error', 'message': 'wrong destination id'}, 404

        uploaded_media = UploadedMedia(destination=destination, is_video=is_video)
        uploaded_media.file.save(filename, SimpleUploadedFile(filename, request.body, mime), save=False)

        if is_video:
            with TemporaryDirectory() as d:
                fpath = os.path.join(d, filename)
                with open(fpath, 'wb') as f:
                    f.write(request.body)
                thumb_name = filename + '.thumb.jpg'
                thumb = os.path.join(d, thumb_name)
                clip = VideoFileClip(fpath)
                if clip.size != [1280, 720]:
                    clip.close()
                    return {'status': 'error', 'message': 'invalid video file'}
                clip.save_frame(thumb, t=1)
                uploaded_media.video_length = clip.duration
                uploaded_media.video_width = clip.size[0]
                uploaded_media.video_height = clip.size[1]
                clip.close()
                with open(thumb, 'rb') as f:
                    uploaded_media.thumb.save(thumb_name,
                                              SimpleUploadedFile(thumb_name, f.read(), 'image/jpeg'), save=False)
        else:
            try:
                imf = BytesIO(request.body)
                imf.name = 'im.jpg'
                imf.seek(0)
                im = Image.open(imf)  # type: Image.Image
                if im.format != 'JPEG':
                    raise IOError()
            except IOError:
                return {'status': 'error', 'message': 'invalid image file'}

        uploaded_media.save()
        process_upload.apply_async(args=(uploaded_media.pk,), shadow=str(uploaded_media))
        return {'status': 'ok'}


class LoginView(BaseLoginView):
    template_name = 'cabinet/login.html'
    redirect_authenticated_user = True
    form_class = LoginForm

    def form_valid(self, form):
        if not form.cleaned_data['remember']:
            self.request.session.set_expiry(0)
            self.request.session.modified = True
        return super().form_valid(form)


class SignupView(FormView):
    template_name = 'cabinet/signup.html'
    form_class = SignupForm

    def form_valid(self, form):
        user = User(email=form.cleaned_data['username'])
        user.set_password(form.cleaned_data['password1'])
        user.save()
        messages.success(self.request, 'You have signed up successfully')
        return redirect('login')


class DestinationListView(LoginRequiredMixin, ListView):
    template_name = 'cabinet/destination_list.html'

    def get_queryset(self):
        return Destination.get_user_destinations(self.request.user)

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx['modules'] = DESTINATION_MODULES
        return ctx


class DestinationHistoryView(LoginRequiredMixin, ListView):
    template_name = 'cabinet/destination_history.html'
    paginate_by = 10

    def get_object(self):
        try:
            return Destination.get_user_destinations(self.request.user).get(pk=self.kwargs['pk'])
        except Destination.DoesNotExist:
            raise Http404('Destination does not exist')

    def get_queryset(self):
        return self.get_object().media.order_by('-datetime')

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx['object'] = self.get_object()
        return ctx


class DestinationEditView(LoginRequiredMixin, BaseDestinationView, SingleObjectMixin):
    def get_queryset(self):
        return Destination.objects.filter(owner=self.request.user)

    def form_valid(self, destination_form, config_form):
        destination_form.save()
        config_form.save()
        messages.success(self.request, 'Destination was successfully saved')
        return HttpResponseRedirect('')

    def get_content_type(self):
        return self.get_object().config_type


class DestinationCreateView(LoginRequiredMixin, BaseDestinationView):
    def get_object(self):
        return None

    def form_valid(self, destination_form, config_form):
        config_form.save()
        destination_form.instance.owner = self.request.user
        destination_form.instance.config_type = self.get_content_type()
        destination_form.instance.config_id = config_form.instance.pk
        destination_form.save()
        messages.success(self.request, 'Destination was successfully saved')
        return redirect('destination_edit', pk=destination_form.instance.pk)

    def get_content_type(self):
        return get_object_or_404(ContentType, model=self.kwargs['content_type'])


class DestinationDeleteView(LoginRequiredMixin, SingleObjectMixin, View):
    def get_queryset(self):
        return Destination.objects.filter(owner=self.request.user)

    def post(self, request, *args, **kwargs):
        destination = self.get_object()
        messages.success(self.request, 'Destination "{}" was successfully deleted'.format(destination.title))
        destination.delete()
        return redirect('destination_list')


class ConfigurationView(LoginRequiredMixin, UpdateView):
    template_name = 'cabinet/configuration.html'
    form_class = ConfigForm

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        destinations = {}
        for destination in Destination.get_user_destinations(self.request.user):
            slug = slugify(destination.title)
            if slug in destinations:
                suffix = 2
                while f'{slug}{suffix}' in destinations:
                    suffix += 1
                slug = f'{slug}{suffix}'
            destinations[str(destination.pk)] = {'slug': slug, 'title': destination.title}

        ctx['destinations'] = json.dumps(destinations)
        default_destination = Destination.objects.filter(shared=True).first()
        ctx['default_destination'] = json.dumps(str(default_destination.pk) if default_destination else None)
        return ctx

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Config was successfully stored')
        return HttpResponseRedirect('.')
