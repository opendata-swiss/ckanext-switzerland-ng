"""utils for terms of use"""
import logging
log = logging.getLogger(__name__)

TERMS_OF_USE_OPEN = 'https://opendata.swiss/terms-of-use#terms_open'
TERMS_OF_USE_BY = 'https://opendata.swiss/terms-of-use#terms_by'
TERMS_OF_USE_ASK = 'https://opendata.swiss/terms-of-use#terms_ask'
TERMS_OF_USE_BY_ASK = 'https://opendata.swiss/terms-of-use#terms_by_ask'
TERMS_OF_USE_CLOSED = 'ClosedData'

OPEN_TERMS = [
    TERMS_OF_USE_OPEN,
    TERMS_OF_USE_BY,
    TERMS_OF_USE_ASK,
    TERMS_OF_USE_BY_ASK,
]


def get_resource_terms_of_use(resource):
    if resource.get("license") in OPEN_TERMS:
        return resource.get("license")

    if resource.get("rights") in OPEN_TERMS:
        return resource.get("rights")

    return TERMS_OF_USE_CLOSED


def get_dataset_terms_of_use(dataset):
    least_open = None

    for resource in dataset["resources"]:
        if (
            resource.get("license") not in OPEN_TERMS
            and resource.get("rights") not in OPEN_TERMS
        ):
            least_open = TERMS_OF_USE_CLOSED
            break

        for field_name in ["license", "rights"]:
            if resource.get(field_name) in OPEN_TERMS:
                if least_open is None:
                    least_open = resource.get(field_name)
                    break

                if OPEN_TERMS.index(
                    resource.get(field_name)
                ) > OPEN_TERMS.index(least_open):
                    least_open = resource.get(field_name)
                    break

                # if the resource license is in OPEN_TERMS, we don't need to
                # look at the resource rights
                break

    return least_open
