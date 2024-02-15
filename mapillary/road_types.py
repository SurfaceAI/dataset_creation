# from enum import Enum, auto

# class RoadTypes(Enum):
#     CAR = auto()
#     BIKE = auto() # cycle
#     PEDESTRIAN = auto() # foot

class RoadTypes():
    car = 'car'
    bike = 'bike'
    pedestrian = 'pedestrian'

road_types = {
    RoadTypes.car: {
        'detections': ['construction--flat--road',
                       ],
    },
    RoadTypes.bike: {
        'detections': ['construction--flat--bike-lane',
                       ],
    },
    RoadTypes.pedestrian: {
        'detections': ['construction--flat--sidewalk',
                       ],
    },
}