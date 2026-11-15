import re
from copy import copy
from datetime import datetime
from typing import Optional


SUPPORTED_ACCESS_LEVELS = {
    "public": 0,
    "customer": 1,
    "agent": 2,
    "admin": 3
}


PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(?:all\s+)?previous\s+instructions",
    r"ignore\s+(?:all\s+)?instructions",
    r"disregard\s+(?:all\s+)?instructions",
    r"forget\s+(?:all\s+)?previous\s+instructions",
    r"override\s+(?:the\s+)?(?:system|developer|assistant)",
    r"reveal\s+(?:the\s+)?system\s+prompt",
    r"reveal\s+(?:your\s+)?instructions",
    r"show\s+(?:the\s+)?system\s+message",
    r"developer\s+message",
    r"system\s+prompt",
    r"you\s+must\s+follow\s+these\s+instructions",
    r"do\s+not\s+follow\s+the\s+system",
    r"bypass\s+(?:security|access\s+control)",
    r"give\s+me\s+restricted\s+information"
]


def parse_date(date_value):
    """
    Convert supported date values to a date object.
    """

    if not date_value:
        return None

    if hasattr(date_value, "date"):
        return date_value.date()

    if hasattr(date_value, "isoformat") and not isinstance(
        date_value,
        str
    ):
        return date_value

    return datetime.strptime(
        str(date_value),
        "%Y-%m-%d"
    ).date()


def create_document_metadata(
    version,
    product,
    region,
    access_level,
    effective_date,
    expiry_date=None,
    document_type="general",
    policy_id=None
):
    """
    Create validated metadata for a knowledge-base document.
    """

    access_level = str(access_level).lower()

    if access_level not in SUPPORTED_ACCESS_LEVELS:
        raise ValueError(
            f"Invalid access level: {access_level}"
        )

    effective = parse_date(effective_date)
    expiry = parse_date(expiry_date)

    if not effective:
        raise ValueError(
            "Effective date is required."
        )

    if expiry and expiry < effective:
        raise ValueError(
            "Expiry date cannot be earlier than effective date."
        )

    return {
        "version": str(version),
        "product": str(product),
        "region": str(region),
        "access_level": access_level,
        "effective_date": effective.isoformat(),
        "expiry_date": (
            expiry.isoformat()
            if expiry
            else None
        ),
        "document_type": str(document_type).lower(),
        "policy_id": (
            str(policy_id)
            if policy_id
            else None
        )
    }


def normalize_document_metadata(metadata):
    """
    Ensure every document has the required metadata fields.
    """

    metadata = dict(metadata or {})

    metadata.setdefault("version", "1")
    metadata.setdefault("product", "General")
    metadata.setdefault("region", "IN")
    metadata.setdefault("access_level", "public")
    metadata.setdefault("effective_date", "2000-01-01")
    metadata.setdefault("expiry_date", None)
    metadata.setdefault("document_type", "general")
    metadata.setdefault("policy_id", None)

    metadata["access_level"] = str(
        metadata["access_level"]
    ).lower()

    if metadata["access_level"] not in SUPPORTED_ACCESS_LEVELS:
        metadata["access_level"] = "public"

    return metadata


def enrich_document_metadata(
    document,
    version,
    product,
    region,
    access_level,
    effective_date,
    expiry_date=None,
    document_type="general",
    policy_id=None
):
    """
    Attach validated Task 4 metadata to a LangChain document.
    """

    metadata = create_document_metadata(
        version=version,
        product=product,
        region=region,
        access_level=access_level,
        effective_date=effective_date,
        expiry_date=expiry_date,
        document_type=document_type,
        policy_id=policy_id
    )

    document.metadata.update(metadata)

    return document


def is_policy_document(document):
    """
    Determine whether a document represents a policy.

    A document is treated as a policy when it is explicitly
    marked as one, has a policy ID, or contains the complete
    Task 4 policy metadata required for date/access evaluation.
    """

    metadata = normalize_document_metadata(
        getattr(document, "metadata", {})
    )

    document_type = str(
        metadata.get("document_type", "")
    ).lower()

    source = str(
        metadata.get("source", "")
    ).lower()

    policy_id = metadata.get("policy_id")

    has_policy_metadata = all(
        metadata.get(field) is not None
        for field in [
            "version",
            "product",
            "region",
            "access_level",
            "effective_date"
        ]
    )

    return (
        document_type == "policy"
        or bool(policy_id)
        or "policy" in source
        or has_policy_metadata
    )
def is_policy_active(
    metadata,
    target_date=None
):
    """
    Check whether a document is active on the requested date.

    A document is active when:
    - the target date is on or after its effective date
    - the target date is on or before its expiry date
    - documents without an expiry date remain active
    """

    metadata = normalize_document_metadata(
        metadata
    )

    if target_date is None:
        target_date = datetime.now().date()
    else:
        target_date = parse_date(target_date)

    effective_date = parse_date(
        metadata.get("effective_date")
    )

    expiry_date = parse_date(
        metadata.get("expiry_date")
    )

    if not effective_date:
        return False

    if target_date < effective_date:
        return False

    if expiry_date and target_date > expiry_date:
        return False

    return True

def is_authorized(
    metadata,
    customer_access_level="customer"
):
    """
    Check whether the requester is allowed to access
    the document.
    """

    metadata = normalize_document_metadata(metadata)

    requested_level = str(
        customer_access_level
    ).lower()

    document_level = str(
        metadata.get("access_level", "public")
    ).lower()

    if requested_level not in SUPPORTED_ACCESS_LEVELS:
        return False

    if document_level not in SUPPORTED_ACCESS_LEVELS:
        return False

    return (
        SUPPORTED_ACCESS_LEVELS[requested_level]
        >= SUPPORTED_ACCESS_LEVELS[document_level]
    )


def filter_authorized_documents(
    documents,
    customer_access_level="customer",
    target_date=None
):
    """
    Filter documents according to:
    - access level
    - effective date
    - expiry date

    Legacy training documents are treated as public
    knowledge so the original chatbot continues working.
    """

    filtered = []

    for document in documents:

        metadata = normalize_document_metadata(
            getattr(document, "metadata", {})
        )

        # Preserve legacy training dataset behavior.
        if not getattr(document, "metadata", {}).get(
            "effective_date"
        ):
            metadata["version"] = "1"
            metadata["product"] = "General"
            metadata["region"] = "IN"
            metadata["access_level"] = "public"
            metadata["effective_date"] = "2000-01-01"
            metadata["expiry_date"] = None
            metadata["document_type"] = "faq"

        document.metadata.update(metadata)

        if not is_authorized(
            metadata,
            customer_access_level
        ):
            continue

        if not is_policy_active(
            metadata,
            target_date
        ):
            continue

        filtered.append(document)

    return filtered


def detect_prompt_injection(text):
    """
    Detect malicious instructions embedded inside
    retrieved documents or customer-provided content.
    """

    if not text:
        return {
            "safe": True,
            "patterns": []
        }

    detected = []

    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(
            pattern,
            text,
            re.IGNORECASE
        ):
            detected.append(pattern)

    return {
        "safe": len(detected) == 0,
        "patterns": detected
    }


def sanitize_document_content(document):
    """
    Remove instruction-like content from a retrieved
    document before it reaches the LLM.

    Normal factual content is preserved.
    """

    content = getattr(
        document,
        "page_content",
        ""
    )

    if not content:
        return document

    injection_check = detect_prompt_injection(content)

    if injection_check["safe"]:
        return document

    cleaned_content = content

    for pattern in PROMPT_INJECTION_PATTERNS:
        cleaned_content = re.sub(
            pattern,
            "[REMOVED_MALICIOUS_INSTRUCTION]",
            cleaned_content,
            flags=re.IGNORECASE
        )

    cleaned_document = copy(document)
    cleaned_document.page_content = cleaned_content

    cleaned_document.metadata = dict(
        getattr(document, "metadata", {})
    )

    cleaned_document.metadata[
        "prompt_injection_detected"
    ] = True

    return cleaned_document


def sanitize_documents(documents):
    """
    Sanitize all retrieved documents.

    Documents containing malicious instructions are
    not discarded entirely because they may still contain
    legitimate factual evidence.
    """

    sanitized = []

    for document in documents:
        cleaned = sanitize_document_content(
            document
        )

        sanitized.append(cleaned)

    return sanitized


def get_document_version_number(
    metadata
):
    """
    Convert document version into a sortable number.
    """

    version = str(
        metadata.get("version", "0")
    )

    match = re.search(
        r"\d+(?:\.\d+)?",
        version
    )

    if not match:
        return 0

    try:
        return float(match.group(0))
    except ValueError:
        return 0


def select_latest_applicable_policy(
    documents,
    customer_access_level="customer",
    target_date=None
):
    """
    Select the latest applicable policy from the
    already-retrieved relevant documents.
    """

    applicable = filter_authorized_documents(
        documents,
        customer_access_level,
        target_date
    )

    policies = [
        document
        for document in applicable
        if is_policy_document(document)
    ]

    if not policies:
        return None

    policies.sort(
        key=lambda document: (
            parse_date(
                document.metadata.get(
                    "effective_date"
                )
            ) or datetime.min.date(),

            get_document_version_number(
                document.metadata
            )
        ),
        reverse=True
    )

    return policies[0]


def resolve_policy_conflicts(
    documents,
    customer_access_level="customer",
    target_date=None
):
    """
    Resolve conflicting applicable policies.

    For each policy group, the newest applicable policy
    wins based on effective date and version.
    """

    applicable = filter_authorized_documents(
        documents,
        customer_access_level,
        target_date
    )

    policies = [
        document
        for document in applicable
        if is_policy_document(document)
    ]

    non_policies = [
        document
        for document in applicable
        if not is_policy_document(document)
    ]

    groups = {}

    for document in policies:

        metadata = normalize_document_metadata(
            document.metadata
        )

        group_key = (
            metadata.get("policy_id")
            or (
                metadata.get("product"),
                metadata.get("region")
            )
        )

        groups.setdefault(
            group_key,
            []
        ).append(document)

    resolved = []

    for group_documents in groups.values():

        group_documents.sort(
            key=lambda document: (
                parse_date(
                    document.metadata.get(
                        "effective_date"
                    )
                ) or datetime.min.date(),

                get_document_version_number(
                    document.metadata
                )
            ),
            reverse=True
        )

        resolved.append(
            group_documents[0]
        )

    # Policies are preferred when resolving policy conflicts,
    # while relevant non-policy documents remain available.
    return resolved + non_policies


def calculate_evidence_overlap(
    answer,
    source_documents
):
    """
    Deterministic grounding check.

    Every meaningful answer sentence must share
    evidence-bearing terms with the retrieved sources.
    """

    if not answer or not source_documents:
        return {
            "supported": False,
            "unsupported_sentences": []
        }

    source_text = " ".join(
        getattr(
            document,
            "page_content",
            ""
        )
        for document in source_documents
    ).lower()

    source_tokens = set(
        re.findall(
            r"\b[a-zA-Z0-9][a-zA-Z0-9_-]{2,}\b",
            source_text
        )
    )

    stop_words = {
        "the",
        "this",
        "that",
        "with",
        "from",
        "your",
        "you",
        "are",
        "can",
        "will",
        "have",
        "has",
        "for",
        "and",
        "but",
        "not",
        "what",
        "which",
        "about",
        "into",
        "they",
        "their",
        "there",
        "then",
        "than",
        "also",
        "only",
        "more",
        "some",
        "course",
        "customer"
    }

    sentences = re.split(
        r"(?<=[.!?])\s+",
        answer.strip()
    )

    unsupported = []

    for sentence in sentences:

        tokens = set(
            re.findall(
                r"\b[a-zA-Z0-9][a-zA-Z0-9_-]{2,}\b",
                sentence.lower()
            )
        )

        meaningful_tokens = (
            tokens - stop_words
        )

        if not meaningful_tokens:
            continue

        overlap = (
            meaningful_tokens
            & source_tokens
        )

        # Very short factual statements require
        # at least one evidence-bearing term.
        required_overlap = (
            1
            if len(meaningful_tokens) <= 3
            else 2
        )

        if len(overlap) < required_overlap:
            unsupported.append(sentence)

    return {
        "supported": len(unsupported) == 0,
        "unsupported_sentences": unsupported
    }


def detect_unsupported_claim(
    answer,
    source_documents
):
    """
    Detect whether the generated answer contains
    unsupported factual claims.
    """

    if not source_documents:
        return {
            "supported": False,
            "reason": (
                "No supporting source documents "
                "were retrieved."
            )
        }

    if not answer or not answer.strip():
        return {
            "supported": False,
            "reason": "The generated answer is empty."
        }

    grounding = calculate_evidence_overlap(
        answer,
        source_documents
    )

    if not grounding["supported"]:
        return {
            "supported": False,
            "reason": (
                "The answer contains claims that "
                "cannot be grounded in the retrieved "
                "evidence."
            ),
            "unsupported_sentences": (
                grounding["unsupported_sentences"]
            )
        }

    return {
        "supported": True,
        "reason": (
            "All meaningful answer claims have "
            "supporting evidence."
        ),
        "unsupported_sentences": []
    }


def build_source_citations(
    source_documents
):
    """
    Build citations containing the required metadata.
    """

    citations = []

    for index, document in enumerate(
        source_documents,
        start=1
    ):

        metadata = normalize_document_metadata(
            getattr(document, "metadata", {})
        )

        source = metadata.get(
            "source",
            f"Document {index}"
        )

        citations.append(
            (
                f"[Source {index}: {source}, "
                f"product={metadata['product']}, "
                f"region={metadata['region']}, "
                f"access_level={metadata['access_level']}, "
                f"version={metadata['version']}, "
                f"effective={metadata['effective_date']}, "
                f"expiry={metadata['expiry_date']}]"
            )
        )

    return citations


def build_grounded_response(
    answer,
    source_documents
):
    """
    Return only evidence-grounded answers.

    If evidence is missing or unsupported, refuse
    instead of inventing an answer.
    """

    sanitized_documents = sanitize_documents(
        source_documents
    )

    grounding = detect_unsupported_claim(
        answer,
        sanitized_documents
    )

    if not grounding["supported"]:

        return {
            "answer": (
                "I don't have enough reliable information "
                "to answer that. Please provide more details "
                "or clarify your question."
            ),
            "citations": [],
            "grounded": False,
            "reason": grounding["reason"],
            "unsupported_sentences": grounding.get(
                "unsupported_sentences",
                []
            )
        }

    citations = build_source_citations(
        sanitized_documents
    )

    return {
        "answer": answer,
        "citations": citations,
        "grounded": True,
        "reason": grounding["reason"],
        "unsupported_sentences": []
    }