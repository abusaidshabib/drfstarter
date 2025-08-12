from rest_framework.exceptions import AuthenticationFailed


def check_permission(request):

    if request.user.is_owner:
        from apps.users.models import Branch
        feature_ids = Branch.objects.filter(company=request.user.company).values_list(
            'features__id', flat=True).distinct()

        return list(feature_ids)
    user_allowed_feature_ids = set(
        request.user.features.values_list('id', flat=True))

    return user_allowed_feature_ids


def check_branch_permission(request, branch_id=None):
    from rest_framework.exceptions import NotFound, ValidationError

    from apps.users.models import Branch, Company

    user = request.user
    branch = Branch.objects.none()

    if not user or not user.is_authenticated:
        raise AuthenticationFailed("User is not authenticated.")

    company = user.company
    branches = user.assigned_branches.all()

    if user.is_superuser:
        company = Company.objects.filter(name="starter").first()
        branches = Branch.objects.all()
    elif user.is_owner:
        branches = Branch.objects.filter(company=company)

    if branch_id:
        try:
            branch = Branch.objects.get(id=int(branch_id))
        except Branch.DoesNotExist:
            raise NotFound("Branch not found.")
    else:
        raise ValidationError({"branch": "A branch must required"})

    if branch not in branches:
        raise ValidationError(
            {"branch": "This is not valid branch for you to request"})
    return branch


def check_camera_permission(request):
    from rest_framework.exceptions import NotFound, ValidationError

    from apps.cameras.models import Camera
    from apps.users.models import Branch, Company

    def parse_id_list(param: str) -> list[int]:
        return [int(i) for i in param.split(',') if i.strip().isdigit()]

    user = request.user

    if not user or not user.is_authenticated:
        raise AuthenticationFailed("User is not authenticated.")

    company = user.company
    branches = user.assigned_branches.all()

    if user.is_superuser:
        company = Company.objects.filter(name="starter").first()
        branches = Branch.objects.all()
    elif user.is_owner:
        branches = Branch.objects.filter(company=company)

    camera_ids_qr = request.GET.get('camera_ids', None)
    camera_ids = None
    cameras = Camera.objects.none()
    allowed_branch_ids = branches.values_list('id', flat=True)

    if camera_ids_qr:
        camera_ids = parse_id_list(camera_ids_qr)

    if camera_ids:
        try:
            cameras = Camera.objects.filter(
                id__in=camera_ids
            )
        except Camera.DoesNotExist:
            raise NotFound("Camera not found.")
    else:
        return []

    if cameras:
        if cameras.exclude(branch_id__in=allowed_branch_ids).exists():
            raise ValidationError(
                {"camera": "You don't have permission to this camera"})
        return cameras.values_list('id', flat=True)
    return []
