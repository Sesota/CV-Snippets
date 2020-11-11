import redis
from datetime import datetime, timezone

from django.http import JsonResponse

from celery import group
from celery.result import GroupResult

from src.celery_conf import app
from src.bucket import Bucket

# TODO Maybe better modularization?


def admin_export_json(model):
    """Export data in `model` to cloud bucket

    This function will store celery signatures in a list and
    run then asynchronously as a group. this function will be called
    from admin.py in every app if needed.

    Args:
        model(object): model name

    Returns:
        data(dict):
    """

    sig_list = []
    try:
        sig = model.objects.get_export_to_cloud_task_sig()
    except Exception as e:
        sig = async_exception.signature((str(e),), immutable=True)
    sig_list.append(sig)

    if len(sig_list) == 0:
        return JsonResponse({"detail": "No tasks to be done"}, status=404)

    g_res = group(sig_list).apply_async(queue="Z_lopri_Q")
    g_res.save()
    # Choronometer for task evaluation
    cache = redis.Redis()
    key = str(g_res.id) + "_timestart"
    if not cache.exists(key):
        cache.set(key, datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f %z"))
    data = {"group_id": g_res.id, "should_update_version": 1}
    return data


def admin_download_logo(queryset):
    """Download logos to local

    This function will store celery signatures in a list and
    run then asynchronously as a group. this function will be called
    from admin.py from every app if needed.

    Args:
        queryset(Iterable): an iterable model object of logos

    Returns:
        data(dict):

    TODO this method can become async (?)
    """

    sig_list = []
    for q in queryset:
        try:
            sig = q.get_download_logo_task_sig()
        except Exception as e:
            sig = async_exception.signature((str(e),), immutable=True)
        sig_list.append(sig)

    g_res = group(sig_list).apply_async(queue="Z_lopri_Q")
    g_res.save()
    # Choronometer for task evaluation
    cache = redis.Redis()
    key = str(g_res.id) + "_timestart"
    if not cache.exists(key):
        cache.set(key, datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f %z"))
    data = {"group_id": g_res.id, "should_update_version": 0}
    return data


def admin_upload_logo(queryset):
    """Upload logos to cloud bucket

    This function will store celery signatures in a list and
    run then asynchronously as a group. this function will be called
    from admin.py from every app if needed.

    Args:
        queryset(Iterable): an iterable model objects of logos

    Returns:
        data(dict):
    """
    sig_list = []
    for q in queryset:
        try:
            sig = q.get_upload_logo_task_sig()
        except Exception as e:
            sig = async_exception.signature((str(e),), immutable=True)
        sig_list.append(sig)

    g_res = group(sig_list).apply_async(queue="Z_lopri_Q")
    g_res.save()
    # Choronometer for task evaluation
    cache = redis.Redis()
    key = str(g_res.id) + "_timestart"
    if not cache.exists(key):
        cache.set(key, datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f %z"))
    data = {"group_id": g_res.id, "should_update_version": 0}
    return data


def admin_download_map(queryset):
    """Download maps to local

    This function will store celery signatures in a list and
    run then asynchronously as a group. this function will be called
    from admin.py from every app if needed.

    Args:
        queryset(Iterable): an iterable model object of maps

    Returns:
        data(dict):
    """
    sig_list = []
    for q in queryset:
        try:
            sig = q.get_download_map_task_sig()
        except Exception as e:
            sig = async_exception.signature((str(e),), immutable=True)
        sig_list.append(sig)

    g_res = group(sig_list).apply_async(queue="Z_lopri_Q")
    g_res.save()
    # Choronometer for task evaluation
    cache = redis.Redis()
    key = str(g_res.id) + "_timestart"
    if not cache.exists(key):
        cache.set(key, datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f %z"))
    data = {"group_id": g_res.id, "should_update_version": 0}
    return data


def admin_upload_map(queryset):
    """Upload maps to cloud bucket

    This function will store celery signatures in a list and
    run then asynchronously as a group. this function will be called
    from admin.py from every app if needed.

    Args:
        queryset(Iterable): an iterable model objects of maps

    Returns:
        data(dict):
    """
    sig_list = []
    for q in queryset:
        try:
            sig = q.get_upload_map_task_sig()
        except Exception as e:
            sig = async_exception.signature((str(e),), immutable=True)
        sig_list.append(sig)

    g_res = group(sig_list).apply_async(queue="Z_lopri_Q")
    g_res.save()
    # Choronometer for task evaluation
    cache = redis.Redis()
    key = str(g_res.id) + "_timestart"
    if not cache.exists(key):
        cache.set(key, datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f %z"))
    data = {"group_id": g_res.id, "should_update_version": 0}
    return data


# TODO Add another variable "mode" and therefore
#   alternate between fast and reliable functionality
def index_file(path, pattern, max_index):
    cache = redis.Redis()
    cache_key = path + "_indexedfile"
    index = cache.incr(cache_key)
    path = path.replace(pattern, str(index))
    if index == max_index:
        cache.delete(cache_key)

    return path


@app.task(name="tools.async_exception")
def async_exception(exception_str):
    raise RuntimeError(exception_str)


# NOTE This function has it's own path defined in the main urls.py
def group_task_progress_bar(request, group_id, should_update_version):
    g_res = GroupResult.restore(group_id)
    if g_res is None:
        return JsonResponse({"detail": "Notfound"}, status=404)
    if g_res.waiting():
        done_count = len(g_res) - [res.state for res in g_res].count("PENDING")
        percent_str = "%.2f" % (done_count / len(g_res))
        data = {"percent": percent_str}
        return JsonResponse(data)

    # Summarize the results and send
    key = str(g_res.id) + "_timestart"
    try:
        cache = redis.Redis()
        delta = (
            (
                datetime.now(timezone.utc)
                - datetime.strptime(cache.get(key).decode(), "%Y-%m-%d %H:%M:%S.%f %z")
            ).seconds
            if cache.exists(key)
            else "Not calculated"
        )
        results = g_res.join_native(propagate=False)
        states = [res.state for res in g_res]
        errors = [str(res) for res in results if isinstance(res, Exception)]
        results = [str(res) for res in results if not isinstance(res, Exception)]
        data = {
            "percent": 1,
            "successful": states.count("SUCCESS"),
            "failed": states.count("FAILURE"),
            "exec_time": delta,
            "error_messages": [
                {"type": error_type, "num": errors.count(error_type)}
                for error_type in set(errors)
            ],
            "results": [
                {"type": result_type, "num": results.count(result_type)}
                for result_type in set(results)
            ],
        }
    finally:
        if should_update_version:
            Bucket().update_version()
        cache.delete(key)
        g_res.forget()
    return JsonResponse(data, safe=False)


# TODO Fix this
# def terminate_task(request, group_id):
#     g_res = GroupResult.restore(group_id)
#     if g_res is None:
#         return JsonResponse({"detail": "Notfound"}, status=404)
#     if not g_res.waiting():
#         return JsonResponse({"detail": "Bad request"}, status=400)

#     key = str(g_res.id) + "_timestart"
#     try:
#         g_res.revoke()

#         cache = redis.Redis()
#         delta = (
#             (
#                 datetime.now(timezone.utc)
#                 - datetime.strptime(cache.get(key).decode(), "%Y-%m-%d %H:%M:%S.%f %z")
#             ).seconds
#             if cache.exists(key)
#             else "Not calculated"
#         )
#         # TODO Fix this also, pending tasks don't have results
#         results = g_res.join_native(propagate=False)
#         states = [res.state for res in g_res]
#         errors = [str(res) for res in results if isinstance(res, Exception)]
#         results = [str(res) for res in results if not isinstance(res, Exception)]
#         data = {
#             "percent": 1,
#             "successful": states.count("SUCCESS"),
#             "failed": states.count("FAILURE"),
#             "exec_time": delta,
#             "error_messages": [
#                 {"type": str(error_type), "num": str(errors.count(error_type))}
#                 for error_type in set(errors)
#             ],
#             "results": [
#                 {"type": str(result_type), "num": str(results.count(result_type))}
#                 for result_type in set(results)
#             ],
#         }
#     finally:
#         cache.delete(key)
#         g_res.forget()
#     return JsonResponse(data, safe=False)
