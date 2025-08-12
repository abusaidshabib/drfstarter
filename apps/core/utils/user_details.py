from rest_framework.exceptions import AuthenticationFailed


def user_branches_company(request):
    from apps.users.models import Branch, Company

    user = request.user

    if not user or not user.is_authenticated:
        raise AuthenticationFailed("User is not authenticated.")

    company = user.company
    branches = user.assigned_branches.all()

    if user.is_superuser:
        company = Company.objects.filter(name="tamayuz").first()
        branches = Branch.objects.all()
    elif user.is_owner:
        branches = Branch.objects.filter(company=company)
    return user, company, branches
