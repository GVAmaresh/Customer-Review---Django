from django.shortcuts import render, HttpResponse
from django.shortcuts import render
from .mongodb import get_user_collection, get_review_collection
from django.http import HttpResponse, JsonResponse
from subprocess import Popen, DEVNULL
from myapp.hashing import (
    hash_password,
    verify_password,
    generate_jwt_token,
    verify_jwt_token,
)
from django.views.decorators.csrf import csrf_exempt
from pathlib import Path
import pandas as pd
import json

def home(request):
    return HttpResponse("Running Successfully")

@csrf_exempt
def login(request):
    if request.method == "POST":
        try:
            if isinstance(request.body, bytes):
                body = json.loads(request.body.decode('utf-8'))
            else:
                body = json.loads(request.body)

            username = body.get("username")
            password = body.get("password")
            if not username or not password:
                return JsonResponse(
                    {"status": 400, "message": "Invalid Authentication", "data": None},
                    status=400,
                )

            user_collection = get_user_collection()
            user = user_collection.find_one({"username": username})

            if user:
                salt = user.get("salt")
                stored_hashed_password = user.get("password")

                if verify_password(password, stored_hashed_password, salt):
                    user_id = str(user.get("_id"))
                    token = generate_jwt_token(user_id)
                    return JsonResponse(
                        {
                            "status": 200,
                            "message": "Successfully logged in",
                            "token": token,
                        },
                        status=200,
                    )
                else:
                    return JsonResponse(
                        {
                            "status": 401,
                            "message": "Invalid Authentication",
                            "data": None,
                        },
                        status=401,
                    )
            else:
                return JsonResponse(
                    {"status": 404, "message": "User not found", "data": None},
                    status=404,
                )

        except Exception as e:
            return JsonResponse(
                {
                    "status": 500,
                    "message": f"Internal Server Error: {str(e)}",
                    "data": None,
                },
                status=500,
            )
    return JsonResponse(
        {"status": 405, "message": "Method Not Allowed", "data": None}, status=405
    )

@csrf_exempt
def signup(request):
    if request.method == "POST":
        try:
            if isinstance(request.body, bytes):
                body = json.loads(request.body.decode('utf-8'))
            else:
                body = json.loads(request.body)

            username = body.get("username")
            password = body.get("password")
            email = body.get("email")

            if not username or not password or not email:
                return JsonResponse(
                    {"status": 400, "message": "Invalid Signup: Missing fields", "data": None},
                    status=400,
                )
            user_collection = get_user_collection()
            if user_collection.find_one({"email": email}):
                return JsonResponse(
                    {"status": 400, "message": "Email already in use", "data": None},
                    status=400,
                )
            hash_pass, salt = hash_password(password)

            user = user_collection.insert_one(
                {"username": username, "password": hash_pass, "salt": salt, "email": email}
            )
            token = generate_jwt_token(str(user.inserted_id))

            return JsonResponse(
                {"status": 201, "message": "Signup successful", "token": token},
                status=201,
            )

        except Exception as e:
            return JsonResponse(
                {
                    "status": 500,
                    "message": f"Internal Server Error: {str(e)}",
                    "data": None,
                },
                status=500,
            )

    return JsonResponse(
        {"status": 405, "message": "Method Not Allowed", "data": None}, status=405
    )


# def protected_view(request):
#     if request.method == "GET":
#         auth_header = request.headers.get("Authorization", "")
        
#         if not auth_header.startswith("Bearer "):
#             return JsonResponse({"error": "Token is missing or invalid"}, status=401)
        
#         token = auth_header.split(" ")[1]

#         try:
#             user_id = verify_jwt_token(token)
#         except Exception as e:  
#             return JsonResponse({"error": str(e)}, status=401)
        
#         if get_user_collection().find_one({"_id": user_id}) is not None:
#             return JsonResponse({"message": "Authorized request", "user_id": user_id}, status=200)
#         else:
#             return JsonResponse({"error": "Invalid token"}, status=401)

#     return JsonResponse({"error": "Method not allowed"}, status=405)


def add_review(user_id, review_text):
    review_collection = get_review_collection()
    review_data = {
        "user_id": user_id,
        "review": review_text,
        "is_proceed": False,
    }
    result = review_collection.insert_one(review_data)
    review_data["_id"] = str(result.inserted_id)
    return review_data

@csrf_exempt
def review(request):
    if request.method == "POST":
        authorization_header = request.headers.get("Authorization")
        
        if not authorization_header or not authorization_header.startswith("Bearer "):
            return JsonResponse(
                {"status": 400, "message": "Authorization header with Bearer token is required", "data": None},
                status=400,
            )
        
        token = authorization_header.split("Bearer ")[1].strip()
        if isinstance(request.body, bytes):
            body = json.loads(request.body.decode('utf-8'))
        else:
            body = json.loads(request.body)

        review_text = body.get("review")
       

        try:
            if not token or not review_text:
                return JsonResponse(
                    {
                        "status": 400,
                        "message": "Token and review text are required",
                        "data": None,
                    },
                    status=400,
                )

            user_id = verify_jwt_token(token)
            # return JsonResponse({"token": token, "review": review_text, "user_id": user_id}, status=200)
            if not user_id:
                return JsonResponse({"error": "Invalid token"}, status=401)
            review_data = add_review(user_id=user_id, review_text=review_text)

            return JsonResponse(
                {
                    "status": 200,
                    "message": "Review submitted successfully",
                    "data": review_data,
                    "token": token,
                },
                status=200,
            )

        except Exception as e:
            return JsonResponse(
                {"status": 500, "message": "Internal Server Error", "error": str(e)},
                status=500,
            )

    return JsonResponse({"status": 405, "message": "Method Not Allowed"}, status=405)

@csrf_exempt
def file_upload(request):
    if request.method == "POST" and request.FILES.get("file"):
        csv_file = request.FILES.get("file")
        authorization_header = request.headers.get("Authorization")
        
        if not authorization_header or not authorization_header.startswith("Bearer "):
            return JsonResponse(
                {"status": 400, "message": "Authorization header with Bearer token is required", "data": None},
                status=400,
            )
        
        token = authorization_header.split("Bearer ")[1].strip()
        
        if not csv_file.name.endswith(".csv"):
            return JsonResponse(
                {"status": 422, "message": "File format is not CSV"}, status=422
            )

        try:
            df = pd.read_csv(csv_file)
            data = None
            if df.shape[0] == 0 or not token:
                return JsonResponse(
                    {
                        "status": 400,
                        "message": "Token and review text are required",
                        "data": None,
                    },
                    status=400,
                )
                
            user_id = verify_jwt_token(token)
            
            if not user_id:
                return JsonResponse({"status":401, "error": "Invalid token"}, status=401)

            if df.shape[1] == 1:
                data = df.iloc[:, 0].tolist()
            elif "review" in df.columns:
                data = df["review"].squeeze().tolist()
            else:
                return JsonResponse(
                    {
                        "status": 400,
                        "message": "The DataFrame does not contain a 'review' column",
                    },
                    status=400,
                )
            review_data = [add_review(review_data=text, user_id=user_id) for text in data]
            
            return JsonResponse({"status": 200, "data": review_data, "token": token }, status=200)

        except Exception as e:
            return JsonResponse(
                {"status": 400, "message": f"An error occurred: {e}"}, status=400
            )
    return JsonResponse(
        {"status": 400, "message": "Invalid request method or no file provided"},
        status=400,
    )
