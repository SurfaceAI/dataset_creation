
DEFINITION_ASPHALT = """Asphalt surfaces are graded from excellent to bad according to the following scale: 

1) excellent: As good as new asphalt, on which a skateboard or rollerblades will have no problem.

2) good: Asphalt showing the first signs of wear, such as narrow, smaller than 1.5 cm cracks, or wider cracks filled up with tar, shallow dents in which rainwater may collect, which may cause trouble for rollerblades but not for racing bikes. 

3) intermediate: Asphalt roads that shows signs of maintenance, such as patches of repaired surface, wider cracks larger than 2cm. Asphalt sidewalks may contain potholes, but these are small, shallow (<3cm deep) and can be easily avoided, asphalt driving lanes shows damage due to subsidence (depressions of a scale >50 cm) or heavy traffic (shallow ruts in asphalt caused by trucks in summer). This means that the road can be used by normal city bikes, wheelchairs and sports cars, but not by a racing bike.

4) bad: Damaged asphalt roads that show clear signs of maintenance: This might include potholes, some of them quite deep, which might decrease the average speed of cars.  However, it isn’t so rough that ground clearance becomes a problem. Meaning that the street causes trouble to normal city bike but not a trekking bike and a car

"""

DEFINITION_CONCRETE = """Concrete surfaces are graded from excellent to bad according to the following scale: 

1) excellent: As good as new concrete, on which a skateboard or rollerblades will have no problem.

2) good: Concrete road showing the first signs of wear, such as narrow, smaller than 1.5 cm cracks, or wider cracks filled up with tar, shallow dents in which rainwater may collect, which may cause trouble for rollerblades but not for racing bikes. 

3) intermediate: Concrete roads that shows signs of maintenance, such as patches of repaired surface, wider cracks larger than 2cm. Concrete sidewalks may contain potholes, but these are small, shallow (<3cm deep) and can be easily avoided, concrete driving lanes shows damage due to subsidence (depressions of a scale >50 cm) or heavy traffic (shallow ruts in asphalt caused by trucks in summer). This means that the road can be used by normal city bikes, wheelchairs and sports cars, but not by a racing bike.

4) bad: Heavily damaged concrete roads that badly need maintenance: many potholes, some of them quite deep. The average speed of cars is less than 50% of what it would be on a smooth road. However, it isn’t so rough that ground clearance becomes a problem. Meaning that the street causes trouble to normal city bike but not a trekking bike and a car

"""

DEFINITION_PAVING_STONES = """Paving surfaces are graded from excellent to bad according to the following scale: 

1) excellent: Newly installed and regularly laid paving stones that show no signs of wear. Gaps may be visible, but they are small and uniform and do not significantly affect the driving experience.

2) good: Paving stones showing first signs of wear or newly installed stones with visible but uniform gaps between them. While still suitable for most activities, these surfaces may pose minor challenges for rollerblades and skateboards but remain navigable for racing bikes.

3) intermediate: Characterized by paving stones exhibiting multiple signs of wear, such as shifted heights, potholes, or cracks. This grade allows for the comfortable passage of normal city bikes and standard vehicles but may prove challenging for racing bikes.

4) bad: Heavily uneven or damaged paving stones in dire need of maintenance, featuring significant height disparities and numerous deep potholes. While ground clearance remains sufficient for most vehicles, the surface severely impedes travel, particularly for standard city bikes.

"""

DEFINITION_SETT = """Sett surfaces are graded from good to bad according to the following scale: 

1) good: The best sett roads with flattened stones and gaps that are at most small or filled up. The surface might cause trouble for rollerblades but not for racing bikes. 

2) intermediate: The surfaces of the sett stones are not completely flat, or there may be slightly larger gaps between the stones, this causes problems for racing bikes and slows down city bikes and cars.

3) bad: Sett stones with large and possibly uneven gaps or uneven stone surfaces or damaged stones, resulting in an overall bumpy surface: This results in a highly uncomfortable driving experience for city bikes. The average speed of cars is less than 50% of what it would be on a smooth road. However, it isn’t so rough that ground clearance becomes a problem. 

"""


DEFINITION_UNPAVED = """Unpaved roads are graded from intermediate to very_bad according to the following scale: 

1) intermediate: The best unpaved roads that have a compacted surface. The surface might cause trouble for rollerblades but not for racing bikes or a wheelchair.  

2) bad: Unpaved roads that do not have a smooth and compacted surface but ones that can still be used with a car or trekking bike but not with a city bike. This category also includes hiking paths, which are too narrow for cars. 

3) very_bad: Unpaved roads with potholes, ruts or generally a highly uneven surface not safely passable with a regular passenger car but still passable with an average SUV that with higher ground clearance. This category also includes hihgly uneven hiking paths, which are too narrow for cars. 
"""


INSTRUCTIONS = """

1) Step 1: If you detect multiple surface types, only consider the path, driving lane, cycleway or sidewalk in the focus area.

2) Step 2: Check if the road surface is worn off and if you can find any damages, like cracks. 

3) Step 3: Check the quantity and the size of the damages. 

3) Step 4: Then decide if you could ride on the surface with  a skateboard, rollerblades, racing bikes, city bike, or a normal car. 

4) Step 5: If you detect characteristics of two classes, choose the worse class.


"""

INSTRUCTIONS_EXCLUDE_NO_FOCUS = """

1) Step 1: Check whether the focus are of the image depicts a road, cycleway or sidewalk. If not, do not choose any of the given classes but return the string 'no street'.

1) Step 2: If you detect multiple surface types, only consider the path, driving lane, cycleway or sidewalk in the focus area.

2) Step 3: Check if the road surface is worn off and if you can find any damages, like cracks. 

3) Step 4: Check the quantity and the size of the damages. 

3) Step 5: Then decide if you could ride on the surface with  a skateboard, rollerblades, racing bikes, city bike, or a normal car. 

4) Step 6: If you detect characteristics of two classes, choose the worse class.


"""