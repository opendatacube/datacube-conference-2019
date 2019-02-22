"""
LCCS Level 3 Classification

| Class name | Code | Numeric code |
|----------------------------------|-----|-----|
| Cultivated Terrestrial Vegetated | A11 | 111 |
| Natural Terrestrial Vegetated    | A12 | 112 |
| Cultivated Aquatic Vegetated     | A23 | 123 |
| Natural Aquatic Vegetated        | A24 | 124 |
| Artificial Surface               | B15 | 215 |
| Natural Surface                  | B16 | 216 |
| Artificial Water                 | B27 | 227 |
| Natural Water                    | B28 | 228 |


"""

import logging
import numpy

#: Required input variables
LCCS_L3_REQUIRED_VARIABLES = ["vegetat_veg_cat",
                              "aquatic_wat_cat",
                              "cultman_agr_cat",
                              "artific_urb_cat",
                              "artwatr_wat_cat"]

#: LCCS Level 3 Colour Scheme
LCCS_L3_COLOUR_SCHEME = {111 : (192, 255, 0, 255),
                         112 : (0, 128, 0, 255),
                         123 : (0, 255, 245, 255),
                         124 : (0, 192, 122, 255),
                         215 : (255, 0, 255, 255),
                         216 : (255, 192, 160, 255),
                         227 : (0, 155, 255, 255),
                         228 : (0, 0, 255, 255)}

def colour_lccs_level3(classification_array):
    """"
    Colour classification array using LCCS Level 3 standard
    colour scheme. Returns four arays:

    * red
    * green
    * blue
    * alpha
    """
    red = numpy.zeros_like(classification_array, dtype=numpy.uint8)
    green = numpy.zeros_like(red)
    blue = numpy.zeros_like(red)
    alpha = numpy.zeros_like(red)

    for class_id, colours in LCCS_L3_COLOUR_SCHEME.items():
        subset = (classification_array == class_id)
        red[subset], green[subset], blue[subset], alpha[subset] = colours

    return red, green, blue, alpha

def _check_required_variables(classification_data):
    """
    Check requited variables are in xarray
    """
    # Check all input variable exist - warning if they don't
    for var in LCCS_L3_REQUIRED_VARIABLES:
        if var not in classification_data.data_vars:
            logging.warning("Required variable {0} not found".format(var))

def classify_lccs_level3(classification_data):
    """
    Apply Level 3 LCCS Classification

    Requires xarray containing the following variables

    * vegetat_veg_cat - Binary mask 1=vegetation, 0=non-vegetation
    * aquatic_wat_cat - Binary mask 1=aquatic, 0=non-aquatic
    * cultman_agr_cat - Binary mask 1=cultivated/managed, 0=natural
    * artific_urb_cat - Binary mask 1=urban, 0=non-urban
    * artwatr_wat_cat - Binary mask 1=artificial water, 0=natural water

    Returns three arrays:

    * level1
    * level2
    * level3

    """

    # Check required input and output variables exist.
    _check_required_variables(classification_data)

    # Set up arrays for outputs
    try:
        vegetation = classification_data["vegetat_veg_cat"].values == 1
    except KeyError:
        raise Exception("No data available for first level of classification "
                        "(vegetation / non-vegetation), can not proceed")

    level3 = numpy.zeros(vegetation.shape, dtype=numpy.uint8)

    # Level 1
    # Assign level 1 class of primarily vegetated (A,100) or primarily non-vegetated (B,200)
    level1 = numpy.where(vegetation, numpy.uint8(100), numpy.uint8(200))

    # Level 2
    # Assign level 2 class of terrestrial (10) or aquatic (20)
    try:
        aquatic = classification_data["aquatic_wat_cat"].values == 1
        level2 = numpy.where(aquatic, numpy.uint8(20), numpy.uint8(10))
    except KeyError:
        raise Exception("No data available for second level of classification "
                        "(aquatic / non-aquatic), can not proceed")

    # Level 3

    # Assign level 3 (Supercategory) class based on cultivated or artificial
    try:
        cultivated = classification_data["cultman_agr_cat"].values == 1

        # Cultivated Terrestrial Vegetation (A11)
        level3[vegetation & ~aquatic & cultivated] = 111

        # Cultivated Aquatic Vegetation (A23)
        level3[vegetation & aquatic & cultivated] = 123

        # Natural Terrestrial Vegetation (A12)
        level3[vegetation & ~aquatic & ~cultivated] = 112

        # Natural Aquatic Vegetation (A24)
        level3[vegetation & aquatic & ~cultivated] = 124

    except KeyError:
        logging.warning("No cultivated vegetation layer available. Skipping "
                        "assigning level 3 catergories for vegetation")

    try:
        urban = classification_data["artific_urb_cat"].values == 1

        # Artificial Surface (B15)
        level3[~vegetation & ~aquatic & urban] = 215

        # Natural Surface (B16)
        level3[~vegetation & ~aquatic & ~urban] = 216

    except KeyError:
        logging.warning("No urban layer available. Skipping assigning "
                        "level 3 for terrestrial non-vegetation")

    try:
        artificial_water = classification_data["artwatr_wat_cat"].values == 1

        # Artificial Water (B27)
        level3[~vegetation & aquatic & artificial_water] = 227

        # Natural Water (B28)
        level3[~vegetation & aquatic & ~artificial_water] = 228

    except KeyError:
        logging.warning("No artificial water layer available. Skipping assigning "
                        "level 3 for aquatic non-vegetation (water)")

    return level1, level2, level3

