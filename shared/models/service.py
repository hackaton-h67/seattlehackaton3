"""
Service and department data models.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class Service(BaseModel):
    """Service type definition."""
    code: str
    name: str
    description: str
    department: str
    priority: int = 3  # 1-5 scale
    sla_days: Optional[int] = None
    requires_photo: bool = False
    requires_exact_location: bool = False


class Department(BaseModel):
    """City department information."""
    acronym: str
    full_name: str
    director: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None


class ServiceRequest(BaseModel):
    """Historical service request from Seattle Open Data."""
    number: str  # servicerequestnumber
    service_type: str  # webintakeservicerequests
    department: str  # departmentname
    created_date: datetime
    closed_date: Optional[datetime] = None
    resolution_days: Optional[int] = None
    status: str  # servicerequeststatusname
    method_received: str  # methodreceivedname
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    zipcode: Optional[str] = None
    council_district: Optional[str] = None
    neighborhood: Optional[str] = None
    police_precinct: Optional[str] = None
