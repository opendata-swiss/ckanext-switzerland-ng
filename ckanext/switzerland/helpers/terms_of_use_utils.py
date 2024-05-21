"""utils for terms of use"""
import logging
log = logging.getLogger(__name__)

TERMS_OF_USE_OPEN = 'NonCommercialAllowed-CommercialAllowed-ReferenceNotRequired' # noqa
TERMS_OF_USE_BY = 'NonCommercialAllowed-CommercialAllowed-ReferenceRequired' # noqa
TERMS_OF_USE_ASK = 'NonCommercialAllowed-CommercialWithPermission-ReferenceNotRequired' # noqa
TERMS_OF_USE_BY_ASK = 'NonCommercialAllowed-CommercialWithPermission-ReferenceRequired' # noqa
TERMS_OF_USE_CLOSED = 'ClosedData'

OPEN_TERMS = [
    TERMS_OF_USE_OPEN,
    TERMS_OF_USE_BY,
    TERMS_OF_USE_ASK,
    TERMS_OF_USE_BY_ASK,
]


def simplify_terms_of_use(term_id):
    if term_id in OPEN_TERMS:
        return term_id
    return TERMS_OF_USE_CLOSED


def get_dataset_terms_of_use(dataset):
    least_open = None

    for resource in dataset["resources"]:
        if least_open == TERMS_OF_USE_CLOSED:
            break

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
                    continue

                if OPEN_TERMS.index(
                    resource.get(field_name)
                ) > OPEN_TERMS.index(least_open):
                    least_open = resource.get(field_name)
                    continue

                # if the resource license is in OPEN_TERMS, we don't need to
                # look at the resource rights
                continue

    return least_open
