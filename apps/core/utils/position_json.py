from apps.users.models import AppFeature, UserBranchLayout

def position_make_json(features, positions=None):
    """
    Create a list of dicts for layout, each with h, w, x, y, tag, and id.

    If feature.required == 'camera', automatically add the 'camera_live' feature too.

    Args:
        features (list): List of AppFeature instances.
        positions (list|None): Optional list of dicts with position info.

    Returns:
        list: List of layout dictionaries.
    """
    result = []
    added_tags = set()  # to prevent duplicates

    for idx, feature in enumerate(features):
        if feature.tag in added_tags:
            continue  # skip duplicates

        if positions and idx < len(positions):
            pos = positions[idx]
        else:
            pos = {
                "h": feature.h,
                "w": feature.w,
                "x": feature.x,
                "y": feature.y
            }

        result.append({
            "id": feature.id,
            "tag": feature.tag,
            "h": pos["h"],
            "w": pos["w"],
            "x": pos["x"],
            "y": pos["y"]
        })
        added_tags.add(feature.tag)

        # If required is 'camera', add 'camera_live' feature
        if feature.required == "camera" and "camera_live" not in added_tags:
            try:
                camera_live = AppFeature.objects.get(tag="camera_live")
                result.append({
                    "id": camera_live.id,
                    "tag": camera_live.tag,
                    "h": camera_live.h,
                    "w": camera_live.w,
                    "x": camera_live.x,
                    "y": camera_live.y
                })
                added_tags.add("camera_live")
            except AppFeature.DoesNotExist:
                # Skip if camera_live is not found
                continue

    return result


def store_user_layout_position(user, branch, features, positions=None):
    """
    Create and store layout JSON into UserBranchLayout for a user.

    Args:
        user (MyUser): The user instance.
        branch (Branch): The branch instance.
        features (list): List of AppFeature instances.
        positions (list|None): Optional list of position dicts.

    Returns:
        UserBranchLayout: The created or updated UserBranchLayout instance.
    """
    layout_data = position_make_json(features, positions)

    layout_obj, created = UserBranchLayout.objects.update_or_create(
        user=user,
        branch=branch,
        defaults={'position': layout_data}
    )

    return layout_obj
