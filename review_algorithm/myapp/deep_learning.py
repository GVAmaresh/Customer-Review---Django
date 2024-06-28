import requests
import json
from django.http import JsonResponse
from django.conf import settings
from .mongodb import get_precess_review_collection

def operation_review(review_text, user_id, review_id):
    headers = {
        "Content-Type": "application/json",
    }
    payload = {"review": [review_text]}
    try:
        response = requests.post("http://127.0.0.1:5000/api/v1/review", headers=headers, json=payload)
        response.raise_for_status()  # Ensure we raise an error for bad responses
        data = response.json()

        if data["status"] != 200:
            return JsonResponse({"status": 400, "message": "Data could not be parsed"}, status=400)
        
        print("data = ", data)
        data = data["data"]
        process_review = get_precess_review_collection()
        if not data:
            return JsonResponse({"status": 400, "message": "No data received"}, status=400)

        for output in data:
            for label, value in output.items():
                try:
                    print(f"Processing output: {output}")  # Debug statement to print output
                    review = value[0]
                    sentimental = value[1]
                except KeyError as e:
                    print(f"KeyError: {e}")  # Debug statement for KeyError
                    return JsonResponse({"status": 500, "message": f"Missing key: {e}"}, status=500)

                process_data = process_review.find_one({"label": label})
                if not process_data:
                    process_review.insert_one(
                        {
                            "user_id": user_id,
                            "review_id": review_id,
                            "label": label,
                            "review": review,
                            "sentimental": sentimental,
                            "frequency": 0
                        }
                    )

                all_reviews = list(process_review.find({"label": label}))
                all_reviews_texts = [r["review"] for r in all_reviews]

                compare_payload = {"texts": all_reviews_texts, "text": review}
                print("--------------Run 1-----------------")
                response = requests.post("http://127.0.0.1:5000/api/v1/compare_text", headers=headers, json=compare_payload)
                print("--------------Run 2-----------------")
                response.raise_for_status()
                compare_data = response.json()

                if compare_data["status"] != 200:
                    return JsonResponse({"status": 400, "message": "Data could not be parsed"}, status=400)

                if compare_data["data"] is None:
                    process_review.insert_one(
                        {
                            "user_id": user_id,
                            "review_id": review_id,
                            "label": label,
                            "review": review,
                            "sentimental": sentimental,
                            "frequency": 0
                        }
                    )
                else:
                    query = {"review": review}
                    update = {"$inc": {"frequency": 1}}
                    result = process_review.update_one(query, update)
                    if result.modified_count == 0:
                        return JsonResponse({"status": 400, "message": "Error updating review"}, status=400)
        return JsonResponse({"status": 200, "message": "Review processed successfully"})
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return JsonResponse({"status": 500, "message": str(http_err)}, status=500)
    except Exception as err:
        print(f"Other error occurred: {err}")
        return JsonResponse({"status": 500, "message": str(err)}, status=500)
