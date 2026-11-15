from rag_knowledge_engine import (
    create_document_metadata,
    is_policy_active,
    is_authorized,
    select_latest_applicable_policy,
)


class MockDocument:
    def __init__(self, content, metadata):
        self.page_content = content
        self.metadata = metadata


def test_metadata_creation():
    metadata = create_document_metadata(
        version="1",
        product="Premium Plan",
        region="IN",
        access_level="customer",
        effective_date="2026-01-01",
        expiry_date="2026-12-31"
    )

    assert metadata["version"] == "1"
    assert metadata["product"] == "Premium Plan"
    assert metadata["region"] == "IN"
    assert metadata["access_level"] == "customer"
    assert metadata["effective_date"] == "2026-01-01"
    assert metadata["expiry_date"] == "2026-12-31"

    print("PASS: Metadata creation")


def test_current_policy():
    metadata = create_document_metadata(
        version="1",
        product="Premium Plan",
        region="IN",
        access_level="customer",
        effective_date="2026-01-01",
        expiry_date="2026-12-31"
    )

    assert is_policy_active(
        metadata,
        "2026-11-15"
    )

    print("PASS: Current policy")


def test_future_policy():
    metadata = create_document_metadata(
        version="2",
        product="Premium Plan",
        region="IN",
        access_level="customer",
        effective_date="2027-01-01"
    )

    assert not is_policy_active(
        metadata,
        "2026-11-15"
    )

    print("PASS: Future policy rejected")


def test_expired_policy():
    metadata = create_document_metadata(
        version="1",
        product="Premium Plan",
        region="IN",
        access_level="customer",
        effective_date="2025-01-01",
        expiry_date="2025-12-31"
    )

    assert not is_policy_active(
        metadata,
        "2026-11-15"
    )

    print("PASS: Expired policy rejected")


def test_authorization():
    public_document = create_document_metadata(
        version="1",
        product="Basic Plan",
        region="IN",
        access_level="public",
        effective_date="2026-01-01"
    )

    admin_document = create_document_metadata(
        version="1",
        product="Basic Plan",
        region="IN",
        access_level="admin",
        effective_date="2026-01-01"
    )

    assert is_authorized(
        public_document,
        "customer"
    )

    assert not is_authorized(
        admin_document,
        "customer"
    )

    print("PASS: Access control")


def test_latest_applicable_policy():
    old_policy = MockDocument(
        "Old refund policy",
        create_document_metadata(
            version="1",
            product="Premium Plan",
            region="IN",
            access_level="customer",
            effective_date="2026-01-01"
        )
    )

    new_policy = MockDocument(
        "New refund policy",
        create_document_metadata(
            version="2",
            product="Premium Plan",
            region="IN",
            access_level="customer",
            effective_date="2026-06-01"
        )
    )

    future_policy = MockDocument(
        "Future refund policy",
        create_document_metadata(
            version="3",
            product="Premium Plan",
            region="IN",
            access_level="customer",
            effective_date="2027-01-01"
        )
    )

    selected = select_latest_applicable_policy(
        [
            old_policy,
            new_policy,
            future_policy
        ],
        customer_access_level="customer",
        target_date="2026-11-15"
    )

    assert selected is new_policy

    print("PASS: Latest applicable policy selected")


def test_historical_policy():
    old_policy = MockDocument(
        "Old policy",
        create_document_metadata(
            version="1",
            product="Premium Plan",
            region="IN",
            access_level="customer",
            effective_date="2025-01-01",
            expiry_date="2025-12-31"
        )
    )

    new_policy = MockDocument(
        "New policy",
        create_document_metadata(
            version="2",
            product="Premium Plan",
            region="IN",
            access_level="customer",
            effective_date="2026-01-01"
        )
    )

    selected = select_latest_applicable_policy(
        [
            old_policy,
            new_policy
        ],
        customer_access_level="customer",
        target_date="2025-06-01"
    )

    assert selected is old_policy

    print("PASS: Historical policy selected")


if __name__ == "__main__":
    test_metadata_creation()
    test_current_policy()
    test_future_policy()
    test_expired_policy()
    test_authorization()
    test_latest_applicable_policy()
    test_historical_policy()

    print("\nALL TASK 4 RAG TESTS PASSED")