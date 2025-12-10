from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import models
from django.http import JsonResponse
from .forms import EnquiryForm
from .models import Enquiry
import requests
import logging

logger = logging.getLogger(__name__)

EXTERNAL_POST_ENDPOINT = 'https://www.gyaagl.app/goldvault_api/enquiry'
EXTERNAL_GET_ENDPOINT = 'https://www.gyaagl.app/goldvault_api/getEnquiry'
EXTERNAL_DELETE_BASE = 'https://www.gyaagl.app/goldvault_api/deleteEnquiry/'



def index(request):
    """
    Handles public enquiry form:
     - posts to external API
     - saves a local copy (optional)
     - returns JSON for AJAX requests so the front-end can show a popup modal
     - falls back to thankyou.html for non-AJAX
    """
    if request.method == 'POST':
        form = EnquiryForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            resp = None
            resp_json = {'message_code': -1, 'message_text': 'No response from external API', 'message_data': []}

            try:
                headers = {
                    'Accept': 'application/json, text/plain, */*',
                    'Content-Type': 'application/json; charset=utf-8',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                }

                try:
                    phone_val = int(data['phone'])
                except Exception:
                    phone_val = data['phone']

                json_payload = {
                    'Firstname': data['first_name'],
                    'Lastname': data.get('last_name', ''),
                    'PhoneNo': phone_val,
                    'Email': data['email'],
                }

                resp = requests.post(EXTERNAL_POST_ENDPOINT, json=json_payload, headers=headers, timeout=15)

                if getattr(resp, 'status_code', None) == 406:
                    resp = requests.post(
                        EXTERNAL_POST_ENDPOINT,
                        data={
                            'Firstname': data['first_name'],
                            'Lastname': data.get('last_name', ''),
                            'PhoneNo': data['phone'],
                            'Email': data['email'],
                        },
                        headers={'User-Agent': headers['User-Agent']},
                        timeout=15
                    )

                try:
                    resp_json = resp.json()
                except Exception:
                    resp_json = {
                        'message_code': None,
                        'message_text': getattr(resp, 'text', str(resp)),
                        'message_data': []
                    }

            except Exception as e:
                logger.exception('EXTERNAL API POST FAILED')
                resp_json = {
                    'message_code': -1,
                    'message_text': f'Failed to send enquiry: {str(e)}',
                    'message_data': []
                }

            try:
                enquiry = form.save(commit=False)
                try:
                    enquiry.response_code = int(resp_json.get('message_code')) if resp_json.get('message_code') is not None else None
                except Exception:
                    enquiry.response_code = None
                enquiry.response_text = resp_json.get('message_text', '')
                enquiry.save()
            except Exception:
                logger.exception('Failed to save local enquiry (non-fatal)')

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                external_status = getattr(resp, 'status_code', None) if resp is not None else None
                out = {
                    'message_code': resp_json.get('message_code'),
                    'message_text': resp_json.get('message_text'),
                    'message_data': resp_json.get('message_data', []),
                    'external_status': external_status,
                }
                status_code = 200 if not external_status or external_status < 400 else 502
                return JsonResponse(out, status=status_code)

            return render(request, 'enquiries/thankyou.html', {'resp': resp_json})
        else:
            messages.error(request, 'Please correct the errors.')
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                errors = {k: [str(x) for x in v] for k, v in form.errors.items()}
                return JsonResponse({'ok': False, 'errors': errors}, status=400)
    else:
        form = EnquiryForm()

    return render(request, 'enquiries/index.html', {'form': form})



def admin_login(request):
    if request.user.is_authenticated:
        return redirect('enquiry_list')

    if request.method == 'POST':
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return redirect('enquiry_list')
        else:
            messages.error(request, "Invalid login credentials")

    return render(request, 'enquiries/admin_login.html')



def admin_logout(request):
    logout(request)
    return redirect('admin_login')



@login_required
def enquiry_list(request):
    external_enquiries = None
    ext_error = None

    try:
        resp = requests.get(EXTERNAL_GET_ENDPOINT, timeout=15)
        resp.raise_for_status()
        resp_json = resp.json()

        if isinstance(resp_json, dict) and "message_data" in resp_json:
            external_enquiries = resp_json["message_data"] or []
        elif isinstance(resp_json, list):
            external_enquiries = resp_json
        else:
            external_enquiries = resp_json.get("data") if isinstance(resp_json, dict) else []

    except Exception as e:
        ext_error = str(e)
        logger.exception("FAILED TO FETCH EXTERNAL ENQUIRIES")

    q = request.GET.get("q", "")
    try:
        per_page = int(request.GET.get("per_page", 10))
    except Exception:
        per_page = 10
    page = request.GET.get("page", 1)

    if external_enquiries is not None:
        def matches(e):
            if not q:
                return True
            lower_q = q.lower()
            for k in ("Firstname","Lastname","PhoneNo","Email","first_name","last_name","phone","email"):
                v = e.get(k) or e.get(k.lower())
                if v and lower_q in str(v).lower():
                    return True
            return False

        filtered = [e for e in external_enquiries if matches(e)]

        paginator = Paginator(filtered, per_page)
        try:
            page_obj = paginator.page(page)
        except Exception:
            page_obj = paginator.page(1)

        return render(request, "enquiries/admin_list.html", {
            "enquiries": page_obj,
            "from_external": True,
            "q": q,
            "paginator": paginator,
            "per_page": per_page,
            "external_error": ext_error
        })

    qs = Enquiry.objects.all().order_by("-created_at")
    if q:
        qs = qs.filter(
            models.Q(first_name__icontains=q) |
            models.Q(last_name__icontains=q) |
            models.Q(phone__icontains=q) |
            models.Q(email__icontains=q)
        )

    paginator = Paginator(qs, per_page)
    try:
        page_obj = paginator.page(page)
    except Exception:
        page_obj = paginator.page(1)

    return render(request, "enquiries/admin_list.html", {
        "enquiries": page_obj,
        "from_external": False,
        "q": q,
        "paginator": paginator,
        "per_page": per_page,
        "external_error": ext_error
    })



@login_required
def enquiry_delete(request, pk=None):

    ext_id = request.POST.get("ext_id") or request.GET.get("ext_id")
    if ext_id:
        url = EXTERNAL_DELETE_BASE + str(ext_id)
        success = False
        resp_text = ""

        try:
            resp = requests.delete(url, timeout=15)
            if not (200 <= resp.status_code < 300):
                resp = requests.get(url, timeout=15)
            if not (200 <= resp.status_code < 300):
                resp = requests.post(url, timeout=15)

            if 200 <= resp.status_code < 300:
                success = True
                resp_text = resp.text

        except Exception as e:
            logger.exception("EXTERNAL DELETE FAILED")
            messages.error(request, f"External delete failed: {e}")
            return redirect("enquiry_list")

        if success:
            messages.success(request, f"External enquiry {ext_id} deleted. Response: {resp_text}")
        else:
            messages.error(request, f"Delete failed. Response: {resp_text}")

        return redirect("enquiry_list")

    if pk:
        obj = get_object_or_404(Enquiry, pk=pk)
        if request.method == "POST":
            obj.delete()
            messages.success(request, "Enquiry deleted.")
            return redirect("enquiry_list")

        return render(request, "enquiries/admin_confirm_delete.html", {"obj": obj})

    messages.error(request, "No ID provided to delete.")
    return redirect("enquiry_list")
