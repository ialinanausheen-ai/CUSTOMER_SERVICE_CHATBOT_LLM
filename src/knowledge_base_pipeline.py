import os
import hashlib
import json
import shutil
from datetime import datetime


# ============================================================
# KNOWLEDGE BASE PRODUCTION PIPELINE
# ============================================================

KB_ROOT = "knowledge_base"
DOCUMENTS_DIR = os.path.join(KB_ROOT, "documents")
QUARANTINE_DIR = os.path.join(KB_ROOT, "quarantine")
VERSIONS_DIR = os.path.join(KB_ROOT, "versions")
METADATA_FILE = os.path.join(KB_ROOT, "metadata.json")


def initialize_knowledge_base():
    """
    Create the required knowledge-base directories
    and metadata file.
    """

    os.makedirs(DOCUMENTS_DIR, exist_ok=True)
    os.makedirs(QUARANTINE_DIR, exist_ok=True)
    os.makedirs(VERSIONS_DIR, exist_ok=True)

    if not os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "w", encoding="utf-8") as file:
            json.dump({}, file, indent=4)


def calculate_file_hash(file_path):
    """
    Calculate a SHA-256 hash for duplicate detection.
    """

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        while True:
            data = file.read(8192)

            if not data:
                break

            sha256.update(data)

    return sha256.hexdigest()


def load_metadata():
    """
    Load knowledge-base metadata.
    """

    initialize_knowledge_base()

    with open(METADATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_metadata(metadata):
    """
    Save knowledge-base metadata.
    """

    with open(METADATA_FILE, "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=4)


def detect_duplicate(file_path):
    """
    Detect whether a document already exists
    in the knowledge base using its file hash.
    """

    file_hash = calculate_file_hash(file_path)
    metadata = load_metadata()

    for document in metadata.values():

        if document.get("file_hash") == file_hash:
            return {
                "duplicate": True,
                "matched_document": document.get("filename")
            }

    return {
        "duplicate": False,
        "matched_document": None
    }


def validate_document(file_path):
    """
    Validate a document before processing.
    """

    if not os.path.exists(file_path):
        return {
            "valid": False,
            "reason": "File does not exist."
        }

    if os.path.getsize(file_path) == 0:
        return {
            "valid": False,
            "reason": "Document is empty."
        }

    allowed_extensions = [
        ".csv",
        ".txt",
        ".pdf"
    ]

    extension = os.path.splitext(file_path)[1].lower()

    if extension not in allowed_extensions:
        return {
            "valid": False,
            "reason": "Unsupported document type."
        }

    return {
        "valid": True,
        "reason": "Document passed validation."
    }


def quarantine_document(file_path, reason):
    """
    Move an invalid document into quarantine.
    """

    initialize_knowledge_base()

    filename = os.path.basename(file_path)
    quarantine_path = os.path.join(
        QUARANTINE_DIR,
        filename
    )

    shutil.move(file_path, quarantine_path)

    return {
        "status": "quarantined",
        "filename": filename,
        "reason": reason,
        "quarantine_path": quarantine_path
    }


def register_document(file_path):
    """
    Register a valid document in the knowledge base metadata.
    """

    initialize_knowledge_base()

    filename = os.path.basename(file_path)
    file_hash = calculate_file_hash(file_path)

    metadata = load_metadata()

    document_id = file_hash[:12]

    version = 1

    if document_id in metadata:
        version = metadata[document_id].get("version", 0) + 1

    metadata[document_id] = {
        "filename": filename,
        "file_hash": file_hash,
        "version": version,
        "status": "registered",
        "registered_at": datetime.now().isoformat()
    }

    save_metadata(metadata)

    return metadata[document_id]


def create_version_backup(file_path, document_id, version):
    """
    Store a versioned backup of a document.
    """

    initialize_knowledge_base()

    version_directory = os.path.join(
        VERSIONS_DIR,
        document_id
    )

    os.makedirs(version_directory, exist_ok=True)

    version_path = os.path.join(
        version_directory,
        f"v{version}_{os.path.basename(file_path)}"
    )

    shutil.copy2(file_path, version_path)

    return version_path


def rollback_document(document_id, version):
    """
    Restore a previous document version.
    """

    metadata = load_metadata()

    if document_id not in metadata:
        return {
            "status": "failed",
            "reason": "Document not found."
        }

    filename = metadata[document_id]["filename"]

    version_directory = os.path.join(
        VERSIONS_DIR,
        document_id
    )

    version_path = os.path.join(
        version_directory,
        f"v{version}_{filename}"
    )

    if not os.path.exists(version_path):
        return {
            "status": "failed",
            "reason": "Requested version does not exist."
        }

    target_path = os.path.join(
        DOCUMENTS_DIR,
        filename
    )

    shutil.copy2(version_path, target_path)

    metadata[document_id]["version"] = version
    metadata[document_id]["status"] = "rolled_back"

    save_metadata(metadata)

    return {
        "status": "rolled_back",
        "filename": filename,
        "version": version
    }
def process_document(file_path):
    """
    Process a document through the knowledge-base pipeline.
    """

    # Step 1: Validate document
    validation = validate_document(file_path)

    if not validation["valid"]:
        return quarantine_document(
            file_path,
            validation["reason"]
        )

    # Step 2: Check for duplicates
    duplicate_check = detect_duplicate(file_path)

    if duplicate_check["duplicate"]:
        return {
            "status": "duplicate",
            "filename": os.path.basename(file_path),
            "matched_document": duplicate_check["matched_document"]
        }

    # Step 3: Register document
    def register_document(file_path):
      """
      Register a valid document and maintain versions
      for the same filename.
      """

    initialize_knowledge_base()

    filename = os.path.basename(file_path)
    file_hash = calculate_file_hash(file_path)

    metadata = load_metadata()

    # Check whether this filename already exists.
    existing_document_id = None

    for document_id, document in metadata.items():
        if document.get("filename") == filename:
            existing_document_id = document_id
            break

    # Existing document -> create a new version.
    if existing_document_id:
        document_id = existing_document_id
        version = metadata[document_id].get("version", 0) + 1

    # New document -> create a stable document ID.
    else:
        document_id = hashlib.sha256(
            filename.encode("utf-8")
        ).hexdigest()[:12]
        version = 1

    metadata[document_id] = {
        "filename": filename,
        "file_hash": file_hash,
        "version": version,
        "status": "registered",
        "registered_at": datetime.now().isoformat()
    }

    save_metadata(metadata)

    return {
        "document_id": document_id,
        "filename": filename,
        "file_hash": file_hash,
        "version": version,
        "status": "registered"
    }
    # Step 4: Create version backup
    version_path = create_version_backup(
        file_path,
        document_id,
        document["version"]
    )

    return {
        "status": "processed",
        "filename": document["filename"],
        "version": document["version"],
        "document_id": document_id,
        "version_path": version_path
    }
def run_quality_test(
    previous_accuracy,
    new_accuracy,
    previous_grounding,
    new_grounding
):
    """
    Compare the existing knowledge-base quality
    with the proposed update.
    """

    accuracy_improved_or_equal = (
        new_accuracy >= previous_accuracy
    )

    grounding_improved_or_equal = (
        new_grounding >= previous_grounding
    )

    if (
        accuracy_improved_or_equal
        and grounding_improved_or_equal
    ):
        return {
            "approved": True,
            "reason": "Quality tests passed."
        }

    return {
        "approved": False,
        "reason": "Update rejected because accuracy or grounding decreased."
    }
def schedule_update(update_time):
    """
    Schedule a knowledge-base update at a configurable time.
    """

    return {
        "status": "scheduled",
        "update_time": update_time
    }


def get_retry_schedule():
    """
    Return the required retry intervals after a failed update.
    """

    return [15, 30, 60]


def record_update_failure(error_message, attempt=1):
    """
    Record a failed knowledge-base update.
    """

    retry_intervals = get_retry_schedule()

    if attempt <= len(retry_intervals):
        next_retry_minutes = retry_intervals[attempt - 1]
    else:
        next_retry_minutes = None

    return {
        "status": "failed",
        "attempt": attempt,
        "error": error_message,
        "next_retry_minutes": next_retry_minutes
    }
def is_within_maintenance_window(
    current_time,
    maintenance_start,
    maintenance_end
):
    """
    Check whether the current time is inside
    the configured maintenance window.
    """

    current = datetime.strptime(
        current_time,
        "%H:%M"
    ).time()

    start = datetime.strptime(
        maintenance_start,
        "%H:%M"
    ).time()

    end = datetime.strptime(
        maintenance_end,
        "%H:%M"
    ).time()

    if start <= end:
        return start <= current <= end

    # Supports a window crossing midnight.
    return current >= start or current <= end


def activate_update(
    update_status,
    current_time,
    maintenance_start,
    maintenance_end
):
    """
    Activate an approved update only during
    the configured maintenance window.
    """

    if not update_status.get("approved", False):
        return {
            "status": "rejected",
            "reason": "Update has not passed quality checks."
        }

    if not is_within_maintenance_window(
        current_time,
        maintenance_start,
        maintenance_end
    ):
        return {
            "status": "waiting",
            "reason": "Outside the maintenance window."
        }

    return {
        "status": "activated",
        "reason": "Approved update activated during the maintenance window."
    }
def run_health_check(
    latency_ms,
    service_available,
    confidence_score,
    escalation_count
):
    """
    Check the health of the knowledge-base service.
    """

    health_issues = []

    if not service_available:
        health_issues.append("Service unavailable.")

    if latency_ms > 5000:
        health_issues.append("Latency exceeded 5 seconds.")

    if confidence_score < 0.5:
        health_issues.append("Confidence score is too low.")

    if escalation_count > 10:
        health_issues.append("Escalation count is too high.")

    if health_issues:
        return {
            "healthy": False,
            "issues": health_issues
        }

    return {
        "healthy": True,
        "issues": []
    }


def automatic_rollback(
    health_check,
    document_id,
    previous_version
):
    """
    Roll back the knowledge-base update when
    the post-update health check fails.
    """

    if health_check["healthy"]:
        return {
            "status": "active",
            "reason": "Health check passed."
        }

    rollback_result = rollback_document(
        document_id,
        previous_version
    )

    if rollback_result["status"] == "rolled_back":
        return {
            "status": "rolled_back",
            "reason": "Health check failed. Previous version restored.",
            "rollback": rollback_result
        }

    return {
        "status": "rollback_failed",
        "reason": rollback_result["reason"]
    }
def check_access(user_role):
    """
    Check whether a user is authorized to modify the knowledge base.
    """

    allowed_roles = ["admin", "knowledge_manager"]

    if user_role in allowed_roles:
        return {
            "authorized": True,
            "role": user_role
        }

    return {
        "authorized": False,
        "role": user_role,
        "reason": "Unauthorized access."
    }
def detect_prompt_injection(text):
    """
    Detect common prompt-injection instructions
    before processing knowledge-base content.
    """

    injection_patterns = [
        "ignore previous instructions",
        "ignore all previous instructions",
        "forget previous instructions",
        "system prompt",
        "reveal your instructions",
        "reveal the system prompt",
        "bypass security",
        "jailbreak"
    ]

    text_lower = text.lower()

    detected_patterns = [
        pattern
        for pattern in injection_patterns
        if pattern in text_lower
    ]

    if detected_patterns:
        return {
            "safe": False,
            "reason": "Potential prompt injection detected.",
            "patterns": detected_patterns
        }

    return {
        "safe": True,
        "reason": "No prompt injection detected.",
        "patterns": []
    }
def mask_sensitive_data(text):
    """
    Mask common sensitive information before storing,
    logging, or sending customer data to other systems.
    """

    import re

    masked_text = text

    # Email addresses
    masked_text = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        "[EMAIL_MASKED]",
        masked_text
    )

    # Phone numbers
    masked_text = re.sub(
        r"\b(?:\+91[-\s]?)?[6-9]\d{9}\b",
        "[PHONE_MASKED]",
        masked_text
    )

    # Credit/debit card numbers
    masked_text = re.sub(
        r"\b(?:\d[ -]*?){13,16}\b",
        "[CARD_MASKED]",
        masked_text
    )

    return masked_text
def record_monitoring_metrics(
    latency_ms,
    failure_count,
    confidence_score,
    escalation_count
):
    """
    Record key chatbot monitoring metrics.
    """

    return {
        "latency_ms": latency_ms,
        "failure_count": failure_count,
        "confidence_score": confidence_score,
        "escalation_count": escalation_count,
        "recorded_at": datetime.now().isoformat()
    }