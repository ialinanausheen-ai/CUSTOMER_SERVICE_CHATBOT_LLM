import os
import re
import time
import hashlib
import io
import threading
from datetime import datetime, timedelta

from PIL import Image
import pytesseract
from pypdf import PdfReader
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


MAX_FILE_SIZE_MB = 10
PROCESSING_TIMEOUT_SECONDS = 30
RETENTION_DAYS = 7
EVIDENCE_STORAGE_DIR = "evidence_storage"

os.makedirs(
    EVIDENCE_STORAGE_DIR,
    exist_ok=True
)
BACKGROUND_JOBS = {}


SUPPORTED_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".pdf"
}


def validate_uploaded_file(file_name, file_size_bytes):
    """
    Validate uploaded evidence before processing.
    """

    extension = os.path.splitext(
        file_name
    )[1].lower()

    if extension not in SUPPORTED_EXTENSIONS:
        return {
            "safe": False,
            "reason": "Unsupported or unsafe file type."
        }

    max_size = (
        MAX_FILE_SIZE_MB * 1024 * 1024
    )

    if file_size_bytes > max_size:
        return {
            "safe": False,
            "reason": "File exceeds the maximum allowed size."
        }

    return {
        "safe": True,
        "reason": "File passed initial validation."
    }


def detect_file_prompt_injection(text):
    """
    Detect instructions that attempt to manipulate
    the chatbot through uploaded evidence.
    """

    patterns = [
        r"ignore previous instructions",
        r"ignore all instructions",
        r"system prompt",
        r"developer message",
        r"reveal your instructions",
        r"disregard the rules",
        r"override the assistant",
        r"you must follow these instructions"
    ]

    detected = []

    lowered = text.lower()

    for pattern in patterns:
        if re.search(pattern, lowered):
            detected.append(pattern)

    return {
        "safe": len(detected) == 0,
        "patterns": detected
    }


def mask_sensitive_data(text):
    """
    Mask personal and payment information before logging.
    """

    if not text:
        return text

    masked = text

    masked = re.sub(
        r"\b\d{12,16}\b",
        "[MASKED_CARD]",
        masked
    )

    masked = re.sub(
        r"\b[A-Z]{2}\d{6,12}\b",
        "[MASKED_ACCOUNT]",
        masked
    )

    masked = re.sub(
        r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b",
        "[MASKED_EMAIL]",
        masked
    )

    masked = re.sub(
        r"\b(?:\+91[- ]?)?[6-9]\d{9}\b",
        "[MASKED_PHONE]",
        masked
    )

    return masked


def calculate_file_hash(file_bytes):
    """
    Generate a stable SHA-256 hash for the uploaded file.
    """

    return hashlib.sha256(
        file_bytes
    ).hexdigest()


def extract_order_id(text):
    patterns = [
        r"(?:order\s*id|order)\s*(?:is|:|#|-)?\s*([A-Za-z0-9-]+)",
        r"\b(ORD[A-Za-z0-9-]+)\b"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            value = match.group(1).strip().upper()

            if not value.startswith("ORD"):
                value = "ORD" + value

        return value

        return None
def extract_amount(text):
    patterns = [
        r"(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d{1,2})?)",
        r"\$\s*([\d,]+(?:\.\d{1,2})?)",
        r"\bamount[:\s]+([\d,]+(?:\.\d{1,2})?)"
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            return match.group(1).replace(
                ",",
                ""
            )

    return None


def extract_date(text):
    patterns = [
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b"
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text
        )

        if match:
            return match.group(0)

    return None


def extract_product(text):
    patterns = [
        r"(?:product|item)[:\s]+(.+?)(?=\s+(?:error|error code|amount|date|order|order id)[:\s]|$)",
        r"(?:purchased|bought)[:\s]+(.+?)(?=\s+(?:error|error code|amount|date|order|order id)[:\s]|$)"
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            return match.group(1).strip()

    return None

def extract_error_code(text):
    patterns = [
        r"\bERR[-_ ]?\d{3,6}\b",
        r"\bERROR[-_ ]?\d{3,6}\b",
        r"\bE\d{3,6}\b"
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            return match.group(0)

    return None


def extract_evidence_fields(text):
    """
    Extract structured evidence from OCR text.
    """

    return {
        "order_id": extract_order_id(text),
        "date": extract_date(text),
        "amount": extract_amount(text),
        "product": extract_product(text),
        "error_code": extract_error_code(text)
    }


def compare_message_with_evidence(
    message_fields,
    evidence_fields
):
    conflicts = []

    comparable_fields = [
        "order_id",
        "date",
        "amount",
        "product",
        "error_code"
    ]

    evidence_found = False

    for field in comparable_fields:
        message_value = message_fields.get(field)
        evidence_value = evidence_fields.get(field)

        if evidence_value is not None:
            evidence_found = True

        if (
            message_value is not None
            and evidence_value is not None
            and str(message_value).lower()
            != str(evidence_value).lower()
        ):
            conflicts.append({
                "field": field,
                "message_value": message_value,
                "evidence_value": evidence_value
            })

    if not evidence_found:
        return {
            "match": False,
            "conflicts": [],
            "reason": "No supported evidence fields could be extracted."
        }

    return {
        "match": len(conflicts) == 0,
        "conflicts": conflicts
    }


def assess_ocr_quality(
    text,
    confidence=0.0
):
    """
    Detect poor-quality OCR or insufficient evidence.
    Confidence is expected as a percentage from 0 to 100.
    """

    if not text or len(text.strip()) < 5:
        return {
            "quality": "low",
            "reason": "Very little readable text was extracted."
        }

    if confidence < 70.0:
        return {
            "quality": "low",
            "reason": "OCR confidence is too low."
        }

    return {
        "quality": "acceptable",
        "reason": "OCR produced usable evidence."
    }

def ocr_image_bytes(file_bytes):
    """
    Extract text and OCR confidence from an image.
    """

    image = Image.open(
        io.BytesIO(file_bytes)
    )

    image = image.convert("RGB")

    data = pytesseract.image_to_data(
        image,
        output_type=pytesseract.Output.DICT
    )

    text_parts = []
    confidences = []

    for index, word in enumerate(data["text"]):
        word = word.strip()

        if not word:
            continue

        text_parts.append(word)

        try:
            confidence = float(
                data["conf"][index]
            )

            if confidence >= 0:
                confidences.append(confidence)

        except (ValueError, TypeError):
            continue

    extracted_text = " ".join(text_parts)

    average_confidence = (
        sum(confidences) / len(confidences)
        if confidences
        else 0.0
    )

    return {
        "text": extracted_text,
        "confidence": average_confidence
    }


def extract_pdf_text(file_bytes):
    """
    Extract text from a normal text-based PDF.
    """

    reader = PdfReader(
        io.BytesIO(file_bytes)
    )

    pages = []

    for page in reader.pages:
        text = page.extract_text() or ""

        if text.strip():
            pages.append(text)

    return {
    "text": "\n".join(pages),
    "confidence": 100.0
}

def run_with_timeout(
    processing_function,
    timeout_seconds=30,
    job_id=None
):
    """
    Run evidence processing with a timeout.

    If a job ID is supplied and processing exceeds the timeout,
    the same worker continues in the background.
    """

    result_holder = {}

    def worker():
        try:
            result_holder["result"] = processing_function()

            if job_id is not None:
                BACKGROUND_JOBS[job_id]["status"] = "completed"
                BACKGROUND_JOBS[job_id]["result"] = (
                    result_holder["result"]
                )

        except Exception as error:
            result_holder["error"] = error

            if job_id is not None:
                BACKGROUND_JOBS[job_id]["status"] = "failed"
                BACKGROUND_JOBS[job_id]["reason"] = str(error)

    thread = threading.Thread(
        target=worker,
        daemon=True
    )

    thread.start()
    thread.join(timeout_seconds)

    if thread.is_alive():
        return {
            "timed_out": True,
            "thread": thread
        }

    if "error" in result_holder:
        raise result_holder["error"]

    return {
        "timed_out": False,
        "result": result_holder.get("result")
    }

def process_uploaded_file(
    file_name,
    file_bytes,
    customer_message=""
):
    """
    Validate and process an uploaded image or PDF.
    Store the uploaded file with a retention expiry.
    """
    cleanup_expired_evidence_files()

    validation = validate_uploaded_file(
        file_name,
        len(file_bytes)
    )

    if not validation["safe"]:
        return {
            "status": "rejected",
            "reason": validation["reason"]
        }

    # Create a unique stored filename.
    file_hash = calculate_file_hash(
        file_bytes
    )

    stored_file_name = (
        f"{file_hash}_{os.path.basename(file_name)}"
    )

    stored_file_path = os.path.join(
        EVIDENCE_STORAGE_DIR,
        stored_file_name
    )

    # Store the uploaded evidence temporarily.
    with open(
        stored_file_path,
        "wb"
    ) as evidence_file:
        evidence_file.write(file_bytes)

    created_at = datetime.now()

    evidence_record = create_evidence_record(
        file_name,
        file_bytes
    )

    evidence_record["stored_file_path"] = (
        stored_file_path
    )

    evidence_record["created_at"] = (
        created_at.isoformat()
    )

    evidence_record["delete_after"] = (
        calculate_retention_expiry(
            created_at
        ).isoformat()
    )

    def process_file():
        start_time = time.time()

        extension = os.path.splitext(
            file_name
        )[1].lower()

        if extension in {
            ".png",
            ".jpg",
            ".jpeg",
            ".webp"
        }:
            extraction = ocr_image_bytes(
                file_bytes
            )

        elif extension == ".pdf":
            extraction = extract_pdf_text(
                file_bytes
            )

        else:
            return {
                "status": "rejected",
                "reason": "Unsupported file type."
            }

        result = process_evidence_text(
            extraction["text"],
            customer_message,
            extraction["confidence"]
        )

        result["file_name"] = file_name
        result["processing_time_seconds"] = (
            time.time() - start_time
        )
        result["ocr_confidence"] = (
            extraction["confidence"]
        )

        # Keep only masked evidence information
        # in the returned record.
        result["evidence_record"] = {
            "file_name": evidence_record[
                "file_name"
            ],
            "file_hash": evidence_record[
                "file_hash"
            ],
            "created_at": evidence_record[
                "created_at"
            ],
            "delete_after": evidence_record[
                "delete_after"
            ]
        }

        return result

    # Create the job first so the same worker can
    # continue in the background if processing exceeds 30 seconds.
    job_id = hashlib.sha256(
        f"{file_name}-{datetime.now().isoformat()}".encode()
    ).hexdigest()[:12]

    BACKGROUND_JOBS[job_id] = {
        "job_id": job_id,
        "status": "processing",
        "file_name": file_name,
        "created_at": created_at.isoformat(),
        "delete_after": evidence_record[
            "delete_after"
        ],
        "message": (
            "Evidence processing is in progress."
        )
    }

    timeout_result = run_with_timeout(
        process_file,
        PROCESSING_TIMEOUT_SECONDS,
        job_id=job_id
    )

    if timeout_result["timed_out"]:

        BACKGROUND_JOBS[job_id]["status"] = "queued"
        BACKGROUND_JOBS[job_id]["message"] = (
            "Evidence processing exceeded 30 seconds "
            "and is continuing in the background."
        )

        return {
            "status": "queued",
            "reason": (
                "Evidence processing exceeded 30 seconds "
                "and was moved to the background queue."
            ),
            "job": BACKGROUND_JOBS[job_id]
        }

    completed_result = (
        timeout_result["result"]
    )

    BACKGROUND_JOBS.pop(
        job_id,
        None
    )

    return completed_result
def process_evidence_text(
    text,
    customer_message="",
    confidence=100.0
):
    """
    Process already-extracted OCR text.
    """

    injection_check = detect_file_prompt_injection(
        text
    )

    if not injection_check["safe"]:
        return {
            "status": "rejected",
            "reason": (
                "Potential malicious instructions were "
                "detected inside the uploaded evidence."
            ),
            "detected_patterns": injection_check[
                "patterns"
            ]
        }

    quality = assess_ocr_quality(
    text,
    confidence
)

    if quality["quality"] == "low":
        return {
            "status": "clarification_required",
            "reason": quality["reason"]
        }

    evidence = extract_evidence_fields(
        text
    )

    message_fields = extract_evidence_fields(
    customer_message
)

    comparison = compare_message_with_evidence(
        message_fields,
        evidence
)
      
    return {
           "status": (
            "conflict_detected"
            if not comparison["match"]
            else "processed"
        ),
        "reason": (
            "Evidence conflicts with the customer's message."
            if not comparison["match"]
            else "Evidence processed successfully."
        ),
        "evidence": evidence,
        "comparison": comparison,
        "masked_text": mask_sensitive_data(text)
    }


def should_background_process(
    processing_time_seconds
):
    return (
        processing_time_seconds
        > PROCESSING_TIMEOUT_SECONDS
    )


def create_background_job(
    file_name,
    processing_function=None
):
    """
    Create and optionally start a background-processing job.
    """

    job_id = hashlib.sha256(
        f"{file_name}-{datetime.now().isoformat()}".encode()
    ).hexdigest()[:12]

    job = {
        "job_id": job_id,
        "status": "queued",
        "file_name": file_name,
        "created_at": datetime.now().isoformat(),
        "message": (
            "Evidence processing exceeded 30 seconds "
            "and was moved to the background queue."
        )
    }

    BACKGROUND_JOBS[job_id] = job

    if processing_function is not None:

        def worker():
            BACKGROUND_JOBS[job_id]["status"] = "processing"

            try:
                result = processing_function()

                BACKGROUND_JOBS[job_id]["status"] = "completed"
                BACKGROUND_JOBS[job_id]["result"] = result

            except Exception as error:
                BACKGROUND_JOBS[job_id]["status"] = "failed"
                BACKGROUND_JOBS[job_id]["reason"] = str(error)

        thread = threading.Thread(
            target=worker,
            daemon=True
        )

        thread.start()

    return job
def get_background_job_status(job_id):
    """
    Retrieve the current status of a background evidence job.
    """

    job = BACKGROUND_JOBS.get(job_id)

    if job is None:
        return {
            "status": "not_found",
            "reason": "Background job was not found."
        }

    return job


def calculate_retention_expiry(
    created_at=None
):
    if created_at is None:
        created_at = datetime.now()

    return (
        created_at
        + timedelta(days=RETENTION_DAYS)
    )


def should_delete_file(
    created_at,
    now=None
):
    if now is None:
        now = datetime.now()

    expiry = calculate_retention_expiry(
        created_at
    )

    return now >= expiry
def cleanup_expired_file(
    file_path,
    created_at,
    now=None
):
    """
    Delete an uploaded file when its retention period has expired.
    """

    if not should_delete_file(
        created_at,
        now
    ):
        return {
            "deleted": False,
            "reason": "File retention period has not expired."
        }

    if not os.path.exists(file_path):
        return {
            "deleted": False,
            "reason": "File does not exist."
        }

    try:
        os.remove(file_path)

        return {
            "deleted": True,
            "reason": "File deleted after retention period expired."
        }

    except OSError as error:
        return {
            "deleted": False,
            "reason": f"File deletion failed: {error}"
        }
def cleanup_expired_evidence_files():
    """
    Delete evidence files whose retention period has expired.
    """

    if not os.path.exists(EVIDENCE_STORAGE_DIR):
        return {
            "deleted_files": [],
            "deleted_count": 0
        }

    deleted_files = []

    for file_name in os.listdir(
        EVIDENCE_STORAGE_DIR
    ):
        file_path = os.path.join(
            EVIDENCE_STORAGE_DIR,
            file_name
        )

        if not os.path.isfile(file_path):
            continue

        created_at = datetime.fromtimestamp(
            os.path.getmtime(file_path)
        )

        result = cleanup_expired_file(
            file_path,
            created_at
        )

        if result["deleted"]:
            deleted_files.append(
                file_name
            )

    return {
        "deleted_files": deleted_files,
        "deleted_count": len(
            deleted_files
        )
    }
def create_evidence_record(
    file_name,
    file_bytes,
    ocr_text=""
):
    """
    Create a safe evidence record without storing
    unmasked sensitive text in logs.
    """

    created_at = datetime.now()

    return {
        "file_name": file_name,
        "file_hash": calculate_file_hash(
            file_bytes
        ),
        "created_at": created_at.isoformat(),
        "delete_after": calculate_retention_expiry(
            created_at
        ).isoformat(),
        "masked_ocr_text": mask_sensitive_data(
            ocr_text
        )
    }
