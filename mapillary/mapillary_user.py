import mapillary_requests

image_id = 235824665415128

access_token=mapillary_requests.load_mapillary_token()

data = mapillary_requests.request_image_data_from_image_entity(image_id=image_id, access_token=access_token, url=False, detections=False, creator=True)
print(data)