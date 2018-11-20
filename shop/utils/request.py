import json
from django.core.exceptions import SuspiciousOperation
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.conf import settings


def get_client_ip(request):
    if "HTTP_X_REAL_IP" in request.META:
        return request.META['HTTP_X_REAL_IP']
    else:
        return request.META.get('REMOTE_ADDR')


def secure_required_cloudflare(view_func):
    def _wrapped_view_func(request, *args, **kwargs):
        if json.loads(request.META.get("HTTP_CF_VISITOR", "{}")).get("scheme") != "https":
            if getattr(settings, 'HTTPS_SUPPORT', True):
                request_url = request.build_absolute_uri(request.get_full_path())
                secure_url = request_url.replace('http://', 'https://')
                return HttpResponseRedirect(secure_url)
        return view_func(request, *args, **kwargs)

    return _wrapped_view_func


def optional_parameters(POST=None, GET=None):
    def decorator(func):
        def wrapped(request, *args, **kwargs):
            err = []
            if POST is not None:
                post_iter = []
                for param, param_type in POST.items():
                    try:
                        val = request.POST.get(param)
                        if val is not None:
                            param_type(val)
                    except (ValueError, TypeError):
                        post_iter.append(param)
                if len(post_iter) > 0:
                    err.append("%s POST parameters is missing or invalid format" % ", ".join(post_iter))

            if GET is not None:
                get_iter = []
                for param, param_type in GET.items():
                    try:
                        val = request.GET.get(param)
                        if val is not None:
                            param_type(val)
                    except (ValueError, TypeError):
                        get_iter.append(param)
                if len(get_iter) > 0:
                    err.append("%s GET parameters is missing or invalid format" % ", ".join(get_iter))

            if len(err) > 0:
                if settings.DEBUG is False:
                    raise SuspiciousOperation(". ".join(err))
                else:
                    return HttpResponse(". ".join(err), status=400)

            return func(request, *args, **kwargs)

        return wrapped

    return decorator


def required_parameters(POST=None, GET=None):
    def decorator(func):
        def wrapped(request, *args, **kwargs):
            err = []
            if POST is not None:
                post_iter = []
                for param, param_type in POST.items():
                    try:
                        val = request.POST.get(param)
                        if val is None:
                            post_iter.append(param)
                        else:
                            param_type(val)
                    except (ValueError, TypeError):
                        post_iter.append(param)
                if len(post_iter) > 0:
                    err.append("%s POST parameters is missing or invalid format" % ", ".join(post_iter))

            if GET is not None:
                get_iter = []
                for param, param_type in GET.items():
                    try:
                        val = request.GET.get(param)
                        if val is None:
                            get_iter.append(param)
                        else:
                            param_type(val)
                    except (ValueError, TypeError):
                        get_iter.append(param)
                if len(get_iter) > 0:
                    err.append("%s GET parameters is missing or invalid format" % ", ".join(get_iter))

            if len(err) > 0:
                if settings.DEBUG is False:
                    raise SuspiciousOperation(". ".join(err))
                else:
                    return HttpResponse(". ".join(err), status=400)

            return func(request, *args, **kwargs)

        return wrapped

    return decorator


def secure_required(view_func):
    """Decorator makes sure URL is accessed over https."""

    def _wrapped_view_func(request, *args, **kwargs):
        if not request.is_secure():
            if getattr(settings, 'HTTPS_SUPPORT', True):
                request_url = request.build_absolute_uri(request.get_full_path())
                secure_url = request_url.replace('http://', 'https://')
                return HttpResponseRedirect(secure_url)
        return view_func(request, *args, **kwargs)

    return _wrapped_view_func