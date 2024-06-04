    {
        "role": "system",
        "content": [
            {
                "type": "text",
                "text": "You are a data annotation expert trained to classify the quality level of road surfaces in images."
                },
        ]
    },
    {
        "role": "user",
        "content": [
                {
                "type": "text",
                "text": f"""
                        You need to determine the quality level of the road surface depicted in the image, following this defined scale:

                        Asphalt surfaces are graded from excellent to bad according to the following scale:
                        1) excellent: As good as new asphalt, on which a skateboard or rollerblades will have no problem.

                        2) good: Asphalt showing the first signs of wear, such as narrow, smaller than 1.5 cm cracks, or wider cracks filled up with tar, shallow dents in which rainwater may collect, which may cause trouble for rollerblades but not for racing bikes.

                        3) intermediate: Asphalt roads that shows signs of maintenance, such as patches of repaired surface, wider cracks larger than 2cm. Asphalt sidewalks may contain potholes, but these are small, shallow (<3cm deep) and can be easily avoided, asphalt driving lanes shows damage due to subsidence (depressions of a scale >50 cm) or heavy traffic (shallow ruts in asphalt caused by trucks in summer). This means that the road can be used by normal city bikes, wheelchairs and sports cars, but not by a racing bike.

                        4) bad: Damaged asphalt roads that show clear signs of maintenance: This might include potholes, some of them quite deep, which might decrease the average speed of cars.  However, it isn’t so rough that ground clearance becomes a problem. Meaning that the street causes trouble to normal city bike but not a trekking bike and a car.

                        Please adhere to the following instructions:
                        1) Step 1: If you detect multiple surface types, only consider the path, driving lane, cycleway or sidewalk in the focus area.

                        2) Step 2: Check if the road surface is worn off and if you can find any damages, like cracks.

                        3) Step 3: Check the quantity and the size of the damages.

                        3) Step 4: Then decide if you could ride on the surface with  a skateboard, rollerblades, racing bikes, city bike, or a normal car.

                        4) Step 5: If you detect characteristics of two classes, choose the worse class.

                        How would you rate this image using one of the four options of the defined scale:
                        1) excellent
                        2) good
                        3) intermediate
                        4) bad

                        Provide your rating in one word disregarding the bullet point numbers and brackets as a string using the four levels of the scale provided.
                        Make sure you have the same number of image urls as input as you have output values.

                        Do not provide any additional explanations for your rating; focus solely on the road surface quality."""
                },

                {
                "type": "image_url",
                "image_url": {
                            "url": f"data:image/jpeg;base64,{excellent_encoded_image}"
                            },
                },

                {
                "type": "text",
                "text": "This was an example for 'excellent'"
                },

                {
                "type": "image_url",
                "image_url": {
                            "url": f"data:image/jpeg;base64,{good_encoded_image}"
                            },
                },

                {
                "type": "text",
                "text": "This was an example for 'good'"
                },


                {
                "type": "image_url",
                "image_url": {
                            "url": f"data:image/jpeg;base64,{intermediate_encoded_image}"
                            },
                },

                {
                "type": "text",
                "text": "This was an example for 'intermediate'"
                },

                {
                "type": "image_url",
                "image_url": {
                            "url": f"data:image/jpeg;base64,{bad_encoded_image}"
                            },
                },

                {
                "type": "text",
                "text": "This was an example for 'bad'"
                },


                {
                "type": "text",
                "text": "Please decide now in one word which category the following picture belongs to as instructed in the beginning of the prompt. Then compare this image to the previous ones and decide whether this category is correct."
                },

                {
                "type": "image_url",
                "image_url": {
                            "url": f"data:image/jpeg;base64,{image}"
                            },
                },

                    ],
    },

    ]
