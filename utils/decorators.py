from django_ratelimit.decorators import ratelimit


def hos_rate_limit(view_func):
    return ratelimit(
        key='user_or_ip',
        rate='50/hour',
        block=True,
        method=['POST', 'PUT', 'DELETE']
    )(view_func)

def user_or_ip(request):
    return str(request.user.id) if request.user.is_authenticated else request.META.get('REMOTE_ADDR', '')
