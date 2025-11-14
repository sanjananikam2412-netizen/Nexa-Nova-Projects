import json
import traceback
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404, render
from django.forms.models import model_to_dict
from django.core.paginator import Paginator
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Subject, Trainer
from django.db import IntegrityError
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.http import JsonResponse, Http404


# def index_page(request):
#     return render(request, 'index.html')

# ==============================================
# TRAINER CRUD
# ==============================================
@csrf_exempt
@require_http_methods(["POST", "GET"])
def create_trainer(request):
    """Create or List Trainers"""

    if request.method == "POST":
        try:
            # 📦 Parse JSON or form data
            if request.content_type.startswith("application/json"):
                data = json.loads(request.body.decode("utf-8"))
            else:
                data = request.POST.dict()

            name = data.get("name", "").strip()
            email = data.get("email", "").strip()
            phone = data.get("phone", "").strip()
            subject_id = data.get("subject")

            # ✅ Validation
            if not name or len(name) < 2:
                return JsonResponse({
                    "status": "error",
                    "message": "Trainer name must be at least 2 characters"
                }, status=400)

            if len(name) > 100:
                return JsonResponse({
                    "status": "error",
                    "message": "Trainer name cannot exceed 100 characters"
                }, status=400)

            if email and Trainer.objects.filter(email=email).exists():
                return JsonResponse({
                    "status": "error",
                    "message": f"Email '{email}' already exists"
                }, status=400)

            # ✅ Validate subject
            subject = None
            if subject_id:
                try:
                    subject = Subject.objects.get(pk=subject_id)
                except Subject.DoesNotExist:
                    return JsonResponse({
                        "status": "error",
                        "message": "Invalid subject ID"
                    }, status=400)

            # ✅ Auto-generate Trainer Code (e.g., T01, T02, ...)
            last_trainer = Trainer.objects.order_by('-trainer_code').first()
            if last_trainer and last_trainer.trainer_code:
                last_number = int(last_trainer.trainer_code.replace("T", ""))
                new_code = f"T{last_number + 1:02d}"
            else:
                new_code = "T01"

            # ✅ Create Trainer
            trainer = Trainer.objects.create(
                trainer_code=new_code,
                name=name,
                email=email,
                phone=phone,
                subject=subject,
                created_at=timezone.now(),
            )

            # ✅ Prepare response data
            trainer_data = model_to_dict(trainer)
            trainer_data["subject_name"] = subject.subject_name if subject else "-"

            return JsonResponse({
                "status": "success",
                "message": "Trainer created successfully!",
                "trainer": trainer_data
            }, status=201)

        except Exception as e:
            traceback.print_exc()
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)

    # ✅ GET → Render Trainer HTML Page
    trainers = Trainer.objects.all().select_related("subject")
    subjects = Subject.objects.all()
    return render(request, "create_trainer.html", {
        "trainers": trainers,
        "subjects": subjects
    })


@csrf_exempt
def get_all_trainers(request):
    """📋 List all trainers with pagination"""
    if request.method == "GET":
        try:
            # 🔢 Pagination parameters (defaults)
            page = int(request.GET.get("page", 1))
            page_size = int(request.GET.get("page_size", 50))

            # 🧩 Query all trainers with subject relation
            trainers_qs = Trainer.objects.all().select_related("subject").order_by("trainer_code")
            paginator = Paginator(trainers_qs, page_size)

            # 📄 Get specific page
            trainers_page = paginator.page(page)

            # 🧠 Format trainer data
            trainers = []
            for t in trainers_page:
                t_data = model_to_dict(t)
                t_data["subject_name"] = t.subject.subject_name if t.subject else "-"
                trainers.append(t_data)

            # ✅ Return paginated response
            return JsonResponse({
                "status": "success",
                "trainers": trainers,
                "page": page,
                "total_pages": paginator.num_pages,
                "total_trainers": paginator.count
            }, status=200)

        except Exception as e:
            # 🚫 Handle invalid page number or other issues
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=400)

    # ❌ If not GET
    return JsonResponse({
        "status": "error",
        "message": "Method not allowed"
    }, status=405)



@csrf_exempt
@require_http_methods(["PUT", "POST"])
def update_trainer_by_code(request, trainer_code):
    """Update a trainer using trainer_code instead of ID"""
    try:
        try:
            trainer = get_object_or_404(Trainer, trainer_code=trainer_code)
        except Http404:
            return JsonResponse(
                {"status": "error", "message": f"No trainer found with code '{trainer_code}'"},
                status=404
            )

        # 📦 Parse incoming data
        if request.content_type.startswith("application/json"):
            data = json.loads(request.body.decode("utf-8"))
        else:
            data = request.POST.dict()

        # ✅ Validate & update name
        if "name" in data:
            name = data["name"].strip()
            if len(name) < 2:
                return JsonResponse({"status": "error", "message": "Trainer name must be at least 2 characters"}, status=400)
            trainer.name = name

        # ✅ Update email
        if "email" in data:
            trainer.email = data["email"].strip()

        # ✅ Validate & update phone
        if "phone" in data:
            phone = data["phone"].strip()
            if not phone.isdigit() or len(phone) != 10:
                return JsonResponse({"status": "error", "message": "Phone number must be exactly 10 digits"}, status=400)
            trainer.phone = phone

        # ✅ Update subject
        if "subject" in data:
            subject_id = data["subject"]
            if subject_id:
                try:
                    subject = Subject.objects.get(pk=subject_id)
                    trainer.subject = subject
                except Subject.DoesNotExist:
                    return JsonResponse({"status": "error", "message": "Invalid subject ID"}, status=400)
            else:
                trainer.subject = None

        # ✅ Save updates
        trainer.updated_at = timezone.now()
        trainer.save()

        trainer_data = model_to_dict(trainer)
        trainer_data["subject_name"] = trainer.subject.subject_name if trainer.subject else None

        return JsonResponse({
            "status": "success",
            "message": f"Trainer '{trainer.trainer_code}' updated successfully",
            "trainer": trainer_data
        })

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON format"}, status=400)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_trainer(request, trainer_code):
    """Delete a trainer by trainer_code"""
    try:
        trainer = Trainer.objects.get(trainer_code=trainer_code)
        trainer.delete()
        return JsonResponse({
            "status": "success",
            "message": f"Trainer '{trainer_code}' deleted successfully"
        }, status=200)

    except Trainer.DoesNotExist:
        return JsonResponse({
            "status": "error",
            "message": f"Trainer with code '{trainer_code}' not found"
        }, status=404)

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)


# ==============================================
# SUBJECT CRUD
# ==============================================

@csrf_exempt
@require_http_methods(["POST", "GET"])
def create_subject(request):
    """Create a new subject or render form"""
    if request.method == "POST":
        try:
            if request.content_type == "application/json":
                data = json.loads(request.body.decode("utf-8"))
            else:
                data = request.POST.dict()

            subject_name = data.get("subject_name")
            description = data.get("description", "")

            # ✅ Validation
            if not subject_name or len(subject_name.strip()) == 0:
                return JsonResponse({"status": "error", "message": "Subject name is required"}, status=400)

            if Subject.objects.filter(subject_name__iexact=subject_name).exists():
                return JsonResponse({
                    "status": "error",
                    "message": f"Subject '{subject_name}' already exists."
                }, status=400)

            # ✅ Create
            subject = Subject.objects.create(
                subject_name=subject_name.strip(),
                description=description.strip() if description else None,
                created_at=timezone.now(),
            )

            return JsonResponse({
                "status": "success",
                "message": "Subject created successfully!",
                "subject": model_to_dict(subject)
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    # GET → return list
    subjects = Subject.objects.all().order_by("subject_id")
    return render(request, "create_subject.html", {"subjects": subjects})


# @csrf_exempt
# def get_all_subjects(request):
#     """List all subjects with pagination"""
#     if request.method == "GET":
#         page = int(request.GET.get("page", 1))
#         page_size = int(request.GET.get("page_size", 50))

#         subjects_qs = Subject.objects.all().order_by("subject_id")
#         paginator = Paginator(subjects_qs, page_size)

#         try:
#             subjects_page = paginator.page(page)
#         except Exception:
#             return JsonResponse({"status": "error", "message": "Invalid page number"}, status=400)

#         subjects = [model_to_dict(s) for s in subjects_page]

#         return JsonResponse({
#             "status": "success",
#             "subjects": subjects,
#             "page": page,
#             "total_pages": paginator.num_pages
#         }, status=200)

#     return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)


@csrf_exempt
def get_all_subjects(request):
    if request.method == "GET":
        subjects = Subject.objects.all().values()
        return JsonResponse(list(subjects), safe=False)
    else:
        return JsonResponse({"error": "Invalid method"}, status=405)


@csrf_exempt
def get_subject_by_id(request, subject_id):
    """Fetch subject by ID"""
    if request.method == "GET":
        try:
            subject = Subject.objects.get(subject_id=subject_id)
            return JsonResponse({"status": "success", "subject": model_to_dict(subject)}, status=200)
        except Subject.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Subject not found"}, status=404)
    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)


@csrf_exempt
@require_http_methods(["PUT", "POST"])
def update_subject(request, subject_id):
    """Update subject"""
    try:
        subject = get_object_or_404(Subject, subject_id=subject_id)
        data = json.loads(request.body.decode("utf-8")) if request.content_type == "application/json" else request.POST.dict()

        subject.subject_name = data.get("subject_name", subject.subject_name)
        subject.description = data.get("description", subject.description)
        subject.updated_at = timezone.now()
        subject.save()

        return JsonResponse({"status": "success", "message": "Subject updated successfully", "subject": model_to_dict(subject)})

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_subject(request, subject_id):
    """Delete subject"""
    try:
        subject = Subject.objects.get(subject_id=subject_id)
        subject.delete()
        return JsonResponse({"status": "success", "message": f"Subject '{subject.subject_name}' deleted successfully"})
    except Subject.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Subject not found"}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)