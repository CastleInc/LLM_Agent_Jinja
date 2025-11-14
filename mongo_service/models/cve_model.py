"""
CVE Data Model
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
try:
    # Pydantic v2 imports (preferred)
    from pydantic import AliasChoices, field_validator
    from pydantic.config import ConfigDict
except Exception:  # Fallback for older pydantic (not expected per requirements)
    AliasChoices = None  # type: ignore
    field_validator = None  # type: ignore
    ConfigDict = dict  # type: ignore


class CVEModel(BaseModel):
    """CVE vulnerability data model"""

    # Identifiers
    cve_number: str = Field(..., description="CVE identifier (e.g., CVE-2021-44228)")
    cve_no: Optional[str] = Field(None, description="Alternate CVE identifier if present")

    # Titles / names (accept either 'title' or 'cve_title' from input)
    title: Optional[str] = Field(
        None,
        description="Vulnerability title",
        validation_alias=AliasChoices("title", "cve_title") if 'AliasChoices' in globals() and AliasChoices else None,
    )
    cve_title: Optional[str] = Field(None, description="Title as stored in upstream datasets")

    # Descriptions and notes
    description: Optional[str] = Field(None, description="Detailed description")
    t_description: Optional[str] = Field(None, description="Technical description")
    manual_notes: Optional[str] = Field(None, description="Manual notes")
    additional_text: Optional[str] = Field(None, description="Additional text or metadata in free form")

    # Severity and scoring
    severity: Optional[str] = Field(None, description="Severity level (CRITICAL/HIGH/MEDIUM/LOW)")
    cvss_score: Optional[float] = Field(None, description="CVSS score")
    cvss_vector: Optional[str] = Field(
        None,
        description="CVSS vector string",
        validation_alias=AliasChoices("cvss_vector", "input_vector") if 'AliasChoices' in globals() and AliasChoices else None,
    )
    exploit_code_maturity: Optional[str] = Field(None, description="Exploit maturity level")
    remediation_level: Optional[str] = Field(None, description="Remediation level (e.g., Official Fix)")
    report_confidence: Optional[str] = Field(None, description="Report confidence level")

    # Dates
    published_date: Optional[str] = Field(None, description="Publication date")
    last_modified_date: Optional[str] = Field(None, description="Last modification date")
    source_last_modified_date: Optional[datetime] = Field(None, description="Source system last modified date")
    valid_from: Optional[datetime] = Field(None, description="Validity start date")

    # Categorization / classifications (accept legacy and pluralized keys)
    classification_location: Optional[str] = Field(
        None,
        description="Location classification",
        validation_alias=AliasChoices("classification_location", "classifications_location") if 'AliasChoices' in globals() and AliasChoices else None,
    )
    classification_attack_type: Optional[str] = Field(
        None,
        description="Attack type classification",
        validation_alias=AliasChoices("classification_attack_type", "classifications_attack_type") if 'AliasChoices' in globals() and AliasChoices else None,
    )
    classification_impact: Optional[str] = Field(
        None,
        description="Impact classification",
        validation_alias=AliasChoices("classification_impact", "classifications_impact") if 'AliasChoices' in globals() and AliasChoices else None,
    )
    classification_exploit: Optional[str] = Field(
        None,
        description="Exploit availability classification",
        validation_alias=AliasChoices("classification_exploit", "classifications_exploit") if 'AliasChoices' in globals() and AliasChoices else None,
    )
    classification_additional: Optional[str] = Field(
        None,
        description="Additional classification",
        validation_alias=AliasChoices("classification_additional", "classifications_additional") if 'AliasChoices' in globals() and AliasChoices else None,
    )

    # Solution / remediation
    solution: Optional[str] = Field(None, description="Solution/mitigation")

    # Keywords and references
    keywords: Optional[List[str]] = Field(default_factory=list, description="Related keywords")
    references: Optional[List[str]] = Field(default_factory=list, description="Reference URLs")

    # Affected products (normalize to list)
    affected_products: Optional[List[str]] = Field(default_factory=list, description="Affected products")

    # Flags and misc
    is_active: Optional[str] = Field(None, description="Active flag as provided by source")
    cisa_key: Optional[str] = Field(None, description="CISA Known Exploited Vulnerabilities flag")

    # Additional metadata and passthroughs
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    java_class: Optional[str] = Field(None, alias="_class", description="Source Java class identifier")
    mongo_id: Optional[Any] = Field(None, alias="_id", description="MongoDB document _id")

    # --- Normalizers / Validators ---
    if 'field_validator' in globals() and field_validator:
        @field_validator("keywords", mode="before")
        @classmethod
        def _normalize_keywords(cls, v):
            if v is None:
                return []
            if isinstance(v, list):
                return [str(x) for x in v if str(x).strip()]
            if isinstance(v, str):
                s = v.strip()
                if not s:
                    return []
                # Split on commas if present, else single token
                parts = [p.strip() for p in s.split(",")] if "," in s else [s]
                return [p for p in parts if p]
            return v

        @field_validator("affected_products", mode="before")
        @classmethod
        def _normalize_products(cls, v):
            if v is None:
                return []
            if isinstance(v, list):
                return [str(x) for x in v if str(x).strip()]
            if isinstance(v, str):
                s = v.strip()
                if not s:
                    return []
                # Prefer comma split if present; otherwise wrap as single
                parts = [p.strip() for p in s.split(",")] if "," in s else [s]
                return [p for p in parts if p]
            return v

    # Pydantic configuration
    model_config = ConfigDict(  # type: ignore[call-arg]
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "cve_number": "CVE-2020-000001",
                "cve_title": "Red Hat Operating System Directory Traversal",
                "description": "Red Hat Operating System contains a directory traversal vulnerability that allows an authenticated attacker to execute arbitrary code.",
                "severity": "CRITICAL",
                "cvss_score": 9.9,
                "cvss_vector": "CVSS:3.1/AV:N/AC:H/PR:L/UI:R/S:U/C:N/I:L/A:N",
                "exploit_code_maturity": "High",
                "classification_location": "Remote / Network Access",
                "classification_attack_type": "Memory Corruption",
                "classification_impact": "Information Disclosure",
                "classification_exploit": "Exploit Exists",
                "classification_additional": "Configuration",
                "solution": "Apply the vendor-provided hotfix immediately.",
                "affected_products": ["Red Hat Operating System versions 5.2 through 8.8"],
                "source_last_modified_date": "2023-02-11T00:00:00Z",
                "valid_from": "2022-03-24T00:00:00Z",
                "cisa_key": "No",
            }
        },
    )


class CVESearchFilter(BaseModel):
    """Filter model for CVE searches"""

    severity: Optional[str] = None
    exploit_maturity: Optional[str] = None
    keyword: Optional[str] = None
    min_cvss_score: Optional[float] = None
    max_cvss_score: Optional[float] = None
    limit: int = Field(default=10, ge=1, le=100)
    skip: int = Field(default=0, ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "severity": "CRITICAL",
                "limit": 10
            }
        }
