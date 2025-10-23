"""
Audit Trail System
Comprehensive logging of all decisions and data access for compliance
"""

import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import logging
import hashlib
from collections import deque

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of auditable actions"""
    INCIDENT_CREATED = "incident_created"
    INCIDENT_PROCESSED = "incident_processed"
    RAG_QUERY = "rag_query"
    CAG_REFINEMENT = "cag_refinement"
    PREDICTION_MADE = "prediction_made"
    DECISION_MADE = "decision_made"
    DATA_ACCESSED = "data_accessed"
    CONFIGURATION_CHANGED = "configuration_changed"
    USER_FEEDBACK = "user_feedback"
    ALERT_GENERATED = "alert_generated"


@dataclass
class AuditEntry:
    """Single audit trail entry"""
    entry_id: str
    timestamp: datetime
    action_type: ActionType
    actor: str  # user, agent, system
    decision: Optional[str] = None
    rationale: Optional[str] = None
    data_accessed: List[str] = field(default_factory=list)
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    compliance_checks: Dict[str, bool] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    hash: Optional[str] = None  # For immutability verification


class AuditLogger:
    """
    Audit trail logging system for compliance and accountability
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}

        # Audit storage
        self.audit_trail: deque[AuditEntry] = deque(
            maxlen=self.config.get('max_entries', 100000)
        )

        # Entry counter for unique IDs
        self.entry_counter = 0

        # Compliance rules
        self.compliance_rules = self._initialize_compliance_rules()

        # Statistics
        self.stats = {
            "total_entries": 0,
            "entries_by_type": {},
            "compliance_violations": 0
        }

        logger.info("Audit Logger initialized")

    def _initialize_compliance_rules(self) -> Dict[str, Any]:
        """Initialize compliance checking rules"""
        return {
            "data_retention_days": self.config.get('data_retention_days', 365),
            "require_rationale": True,
            "pii_detection_enabled": True,
            "audit_all_data_access": True,
            "immutability_check": True
        }

    async def log_decision(
        self,
        action_type: ActionType,
        actor: str,
        decision: str,
        rationale: str,
        data_accessed: Optional[List[str]] = None,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log a decision with full audit trail

        Args:
            action_type: Type of action
            actor: Who made the decision
            decision: The decision made
            rationale: Reasoning behind the decision
            data_accessed: List of data sources accessed
            input_data: Input data used
            output_data: Output/result data
            metadata: Additional metadata

        Returns:
            Entry ID
        """
        self.entry_counter += 1
        entry_id = f"audit_{self.entry_counter}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Run compliance checks
        compliance_checks = await self._run_compliance_checks(
            action_type=action_type,
            decision=decision,
            rationale=rationale,
            data_accessed=data_accessed or [],
            input_data=input_data or {},
            output_data=output_data or {}
        )

        # Create audit entry
        entry = AuditEntry(
            entry_id=entry_id,
            timestamp=datetime.now(),
            action_type=action_type,
            actor=actor,
            decision=decision,
            rationale=rationale,
            data_accessed=data_accessed or [],
            input_data=input_data or {},
            output_data=output_data or {},
            compliance_checks=compliance_checks,
            metadata=metadata or {}
        )

        # Calculate hash for immutability
        entry.hash = self._calculate_entry_hash(entry)

        # Store entry
        self.audit_trail.append(entry)

        # Update statistics
        self.stats["total_entries"] += 1
        action_name = action_type.value
        if action_name not in self.stats["entries_by_type"]:
            self.stats["entries_by_type"][action_name] = 0
        self.stats["entries_by_type"][action_name] += 1

        # Check for compliance violations
        if not all(compliance_checks.values()):
            self.stats["compliance_violations"] += 1
            logger.warning(f"Compliance violation detected in entry {entry_id}")

        logger.debug(f"Audit entry created: {entry_id} ({action_type.value})")

        return entry_id

    async def _run_compliance_checks(
        self,
        action_type: ActionType,
        decision: str,
        rationale: str,
        data_accessed: List[str],
        input_data: Dict[str, Any],
        output_data: Dict[str, Any]
    ) -> Dict[str, bool]:
        """Run compliance checks on the audit entry"""
        checks = {}

        # Check 1: Rationale provided
        if self.compliance_rules["require_rationale"]:
            checks["has_rationale"] = bool(rationale and len(rationale) > 10)
        else:
            checks["has_rationale"] = True

        # Check 2: PII detection
        if self.compliance_rules["pii_detection_enabled"]:
            checks["no_pii_detected"] = not self._detect_pii(input_data, output_data)
        else:
            checks["no_pii_detected"] = True

        # Check 3: Data access logging
        if self.compliance_rules["audit_all_data_access"]:
            checks["data_access_logged"] = len(data_accessed) > 0 or action_type not in [
                ActionType.RAG_QUERY, ActionType.DATA_ACCESSED
            ]
        else:
            checks["data_access_logged"] = True

        # Check 4: Decision validity
        checks["valid_decision"] = bool(decision and len(decision) > 5)

        return checks

    def _detect_pii(
        self,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any]
    ) -> bool:
        """Detect potential PII in data (simplified)"""
        pii_patterns = [
            "ssn", "social_security",
            "credit_card", "card_number",
            "password", "secret",
            "email", "phone"
        ]

        data_str = json.dumps({**input_data, **output_data}).lower()

        for pattern in pii_patterns:
            if pattern in data_str:
                logger.warning(f"Potential PII detected: {pattern}")
                return True

        return False

    def _calculate_entry_hash(self, entry: AuditEntry) -> str:
        """Calculate hash for immutability verification"""
        # Serialize entry (excluding hash field)
        entry_data = {
            "entry_id": entry.entry_id,
            "timestamp": entry.timestamp.isoformat(),
            "action_type": entry.action_type.value,
            "actor": entry.actor,
            "decision": entry.decision,
            "rationale": entry.rationale,
            "data_accessed": entry.data_accessed
        }

        entry_str = json.dumps(entry_data, sort_keys=True)
        return hashlib.sha256(entry_str.encode()).hexdigest()

    async def verify_entry_integrity(self, entry_id: str) -> bool:
        """Verify integrity of an audit entry"""
        # Find entry
        entry = None
        for e in self.audit_trail:
            if e.entry_id == entry_id:
                entry = e
                break

        if not entry:
            logger.error(f"Entry {entry_id} not found")
            return False

        # Recalculate hash
        original_hash = entry.hash
        entry.hash = None
        calculated_hash = self._calculate_entry_hash(entry)
        entry.hash = original_hash

        is_valid = original_hash == calculated_hash

        if not is_valid:
            logger.error(f"Entry {entry_id} integrity check failed")

        return is_valid

    async def query_audit_trail(
        self,
        action_type: Optional[ActionType] = None,
        actor: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEntry]:
        """Query audit trail with filters"""
        results = []

        for entry in reversed(self.audit_trail):
            # Apply filters
            if action_type and entry.action_type != action_type:
                continue

            if actor and entry.actor != actor:
                continue

            if start_time and entry.timestamp < start_time:
                continue

            if end_time and entry.timestamp > end_time:
                continue

            results.append(entry)

            if len(results) >= limit:
                break

        logger.info(f"Audit trail query returned {len(results)} entries")
        return results

    async def get_decision_history(
        self,
        incident_id: str
    ) -> List[Dict[str, Any]]:
        """Get decision history for an incident"""
        history = []

        for entry in self.audit_trail:
            if entry.metadata.get('incident_id') == incident_id:
                history.append({
                    "entry_id": entry.entry_id,
                    "timestamp": entry.timestamp.isoformat(),
                    "action_type": entry.action_type.value,
                    "actor": entry.actor,
                    "decision": entry.decision,
                    "rationale": entry.rationale,
                    "compliance_passed": all(entry.compliance_checks.values())
                })

        history.sort(key=lambda x: x['timestamp'])
        return history

    async def generate_compliance_report(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Generate compliance report for a time period"""
        entries_in_period = [
            e for e in self.audit_trail
            if start_time <= e.timestamp <= end_time
        ]

        if not entries_in_period:
            return {
                "period": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                "total_entries": 0,
                "message": "No entries in this period"
            }

        # Analyze compliance
        total_entries = len(entries_in_period)
        compliant_entries = sum(
            1 for e in entries_in_period
            if all(e.compliance_checks.values())
        )

        violations_by_type = {}
        for entry in entries_in_period:
            for check, passed in entry.compliance_checks.items():
                if not passed:
                    if check not in violations_by_type:
                        violations_by_type[check] = 0
                    violations_by_type[check] += 1

        # Actions by type
        actions_by_type = {}
        for entry in entries_in_period:
            action_name = entry.action_type.value
            if action_name not in actions_by_type:
                actions_by_type[action_name] = 0
            actions_by_type[action_name] += 1

        report = {
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "summary": {
                "total_entries": total_entries,
                "compliant_entries": compliant_entries,
                "compliance_rate": compliant_entries / total_entries if total_entries > 0 else 0,
                "violations": total_entries - compliant_entries
            },
            "violations_by_type": violations_by_type,
            "actions_by_type": actions_by_type,
            "compliance_status": "PASS" if compliant_entries == total_entries else "FAIL"
        }

        logger.info(
            f"Compliance report generated: {compliant_entries}/{total_entries} compliant"
        )

        return report

    async def export_audit_trail(
        self,
        format: str = "json",
        include_hashes: bool = True
    ) -> str:
        """Export audit trail for archival or analysis"""
        if format == "json":
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "total_entries": len(self.audit_trail),
                "entries": [
                    {
                        "entry_id": e.entry_id,
                        "timestamp": e.timestamp.isoformat(),
                        "action_type": e.action_type.value,
                        "actor": e.actor,
                        "decision": e.decision,
                        "rationale": e.rationale,
                        "data_accessed": e.data_accessed,
                        "compliance_checks": e.compliance_checks,
                        "metadata": e.metadata,
                        "hash": e.hash if include_hashes else None
                    }
                    for e in self.audit_trail
                ]
            }

            return json.dumps(export_data, indent=2)

        else:
            raise ValueError(f"Unsupported export format: {format}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get audit trail statistics"""
        return {
            "total_entries": self.stats["total_entries"],
            "entries_by_type": dict(self.stats["entries_by_type"]),
            "compliance_violations": self.stats["compliance_violations"],
            "current_trail_size": len(self.audit_trail),
            "compliance_rate": (
                (self.stats["total_entries"] - self.stats["compliance_violations"]) /
                max(self.stats["total_entries"], 1)
            )
        }


# Global audit logger instance
_global_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create global audit logger"""
    global _global_audit_logger
    if _global_audit_logger is None:
        _global_audit_logger = AuditLogger()
    return _global_audit_logger
