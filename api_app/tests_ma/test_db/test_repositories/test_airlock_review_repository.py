from unittest.mock import MagicMock
from mock import patch
import pytest
from db.repositories.airlock_reviews import AirlockReviewRepository
from models.domain.airlock_review import AirlockReview, AirlockReviewDecision
from models.schemas.airlock_review import AirlockReviewInCreate
from models.domain.airlock_resource import AirlockResourceType

WORKSPACE_ID = "abc000d3-82da-4bfc-b6e9-9a7853ef753e"
AIRLOCK_REQUEST_ID = "abc000d3-82da-4bfc-b6e9-9a7853ef753e"
AIRLOCK_REVIEW_ID = "abc000d3-82da-4bfc-b6e9-9a7853ef753e"


@pytest.fixture
def airlock_review_repo():
    with patch('azure.cosmos.CosmosClient') as cosmos_client_mock:
        yield AirlockReviewRepository(cosmos_client_mock)


@pytest.fixture
def sample_airlock_review_mock():
    airlock_review = AirlockReview(
        id=AIRLOCK_REVIEW_ID,
        resourceType=AirlockResourceType.AirlockReview,
        workspaceId=WORKSPACE_ID,
        requestId=AIRLOCK_REQUEST_ID,
        reviewDecision=AirlockReviewDecision.Approved,
        decisionExplanation="test explaination"
    )
    return airlock_review


@pytest.fixture
def sample_airlock_review_input():
    return AirlockReviewInCreate(reviewDecision=AirlockReviewDecision.Approved, decisionExplanation="some decision")


@pytest.fixture
def sample_airlock_review_input_malformed():
    airlock_review_input_mock = MagicMock()
    airlock_review_input_mock.reviewDecision = "not sure"
    airlock_review_input_mock.decisionExplanation = "xyz"
    return airlock_review_input_mock


def test_create_airlock_review_item_with_the_right_values(sample_airlock_review_input, airlock_review_repo):
    airlock__review = airlock_review_repo.create_airlock_review_item(sample_airlock_review_input, WORKSPACE_ID, AIRLOCK_REQUEST_ID)

    assert airlock__review.resourceType == AirlockResourceType.AirlockReview
    assert airlock__review.workspaceId == WORKSPACE_ID
    assert airlock__review.requestId == AIRLOCK_REQUEST_ID
