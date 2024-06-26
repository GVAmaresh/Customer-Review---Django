import requests
import json
from django.http import JsonResponse
from mongodb import get_precess_review_collection


def operation_review(review_text, user_id, review_id):
    headers = {
        "Content-Type": "application/json",
    }
    payload = {"review": review_text}
    try:
        response = requests.post("api//", headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        data = response.json()
        if not data["status"] == 200:
            JsonResponse(
                {"status": 400, "message": "Data could not be parsed"}, status=400
            )
        data = data["data"]
        process_review = get_precess_review_collection()
        for output in data:
            process_data = process_review.find_one({"label": output})
            if not process_data:
                process_review.insert_one(
                    {
                        "user_id": user_id,
                        "review_id": review_id,
                        "label": output,
                        "review": output.values[0],
                        "sentimental": output.values[1],
                        "frequence": 0
                    }
                )
            all_review = process_review.find({"label": output})
            payload = {"texts": all_review, "text": output.values[0]}
            response = requests.post(
                "api2//", headers=headers, data=json.dumps(payload)
            )
            response.raise_for_status()
            data = response.json()
            if not data["status"] == 200:
                JsonResponse(
                    {"status": 400, "message": "Data could not be parsed"}, status=400
                )
            if data is None:
                process_review.insert_one(
                    {
                        "user_id": user_id,
                        "review_id": review_id,
                        "label": output,
                        "review": output.values[0],
                        "sentimental": output.values[1],
                        "frequency": 0
                    }
                )
            else: 
                query = {"review": output.values[0]}
                update = {"$inc": {"frequence": 1}}
                result = process_review.update_one(query, update)
                if not result:
                    return JsonResponse({"status": 400, "message": "Error updating review"}, status=400)
            return
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return None
    except Exception as err:
        print(f"Other error occurred: {err}")
        return None
