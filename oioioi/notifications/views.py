from oioioi.base.utils import jsonify

@jsonify
def notifications_authenticate_view(request):
    user = request.user
    if request.real_user:
        user = request.real_user
    if user and user.username:
        return {'user': user.username, 'status': 'OK'}
    else:
        return {'status': 'UNAUTHORIZED'}
