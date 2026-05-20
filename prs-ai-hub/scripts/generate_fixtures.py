#!/usr/bin/env python3
"""Generate synthetic PRS fixtures from sample contracts."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "data" / "contracts"
FIXTURES = ROOT / "data" / "fixtures"

SCENARIOS = {
    "C-2024-001_apextech_supply.txt": {
        "id": "apextech-clean",
        "label": "ApexTech Supply — Clean Contract",
        "description": "All required fields present; expected HIGH confidence pass.",
        "expected_scenario": "pass",
        "requestor": {
            "requestor_name": "Sarah Mitchell",
            "requestor_business_unit": "Procurement",
            "business_owner": "David Chen",
            "business_unit": "Supply Chain",
            "business_priority": "High",
            "request_description": "Renew master supply agreement for enterprise IT hardware and peripherals per Exhibit A schedule.",
            "need_by_date": "2026-09-01",
        },
        "vendor": {
            "vendor_name": "ApexTech Distribution Inc.",
            "vendor_address_line1": "1200 Industrial Parkway",
            "vendor_address_line2": None,
            "vendor_address_county": "Denver County",
            "vendor_address_state": "CO",
            "vendor_address_country": "US",
            "vendor_contact_name": "Contracts Team",
            "vendor_contact_role": "Account Manager",
            "vendor_contact_phone_country_code": "+1",
            "vendor_contact_phone": "3035550192",
            "vendor_contact_email": "contracts@apextech.com",
            "vendor_master_id": "SUP-0014",
            "prior_contract_number": "C-2024-001",
        },
        "sku_items": [
            {
                "sku_number": "IT-SRV-001",
                "description": "Enterprise Server Rack Unit 2U",
                "unit_of_measure": "EA",
                "unit_price": 4200.0,
                "msrp": 4800.0,
                "min_order_qty": 5,
                "lead_time": "21 days",
                "status": "Active",
            },
            {
                "sku_number": "IT-NET-014",
                "description": "Core Switch 48-port managed",
                "unit_of_measure": "EA",
                "unit_price": 1850.0,
                "msrp": 2100.0,
                "min_order_qty": 2,
                "lead_time": "14 days",
                "status": "Active",
            },
            {
                "sku_number": "IT-WS-022",
                "description": "Clinical workstation bundle with monitor and dock",
                "unit_of_measure": "EA",
                "unit_price": 890.0,
                "msrp": 1050.0,
                "min_order_qty": 10,
                "lead_time": "14 days",
                "status": "Active",
            },
            {
                "sku_number": "IT-STO-008",
                "description": "SAN storage array 24TB usable capacity",
                "unit_of_measure": "EA",
                "unit_price": 12800.0,
                "msrp": 14500.0,
                "min_order_qty": 1,
                "lead_time": "28 days",
                "status": "Active",
            },
            {
                "sku_number": "IT-PER-031",
                "description": "Wireless keyboard and mouse kit hospital grade",
                "unit_of_measure": "BX",
                "unit_price": 42.5,
                "msrp": 55.0,
                "min_order_qty": 25,
                "lead_time": "7 days",
                "status": "Active",
            },
        ],
    },
    "C-2023-029_vertex_ambiguous.txt": {
        "id": "vertex-ambiguous",
        "label": "Vertex Services — Ambiguous Contract",
        "description": "Intentionally vague clauses; expect partial/fail with warnings.",
        "expected_scenario": "partial",
        "requestor": {
            "requestor_name": "James Porter",
            "requestor_business_unit": "Facilities",
            "business_owner": "Lisa Nguyen",
            "business_unit": "Operations",
            "business_priority": "Medium",
            "request_description": "Managed services agreement for cross-site facilities support with variable pricing terms.",
            "need_by_date": "2026-07-15",
        },
        "vendor": {
            "vendor_name": "Vertex Managed Services LLC",
            "vendor_address_line1": "215 Lakeshore Boulevard",
            "vendor_address_line2": None,
            "vendor_address_county": "Cuyahoga County",
            "vendor_address_state": "OH",
            "vendor_address_country": "US",
            "vendor_contact_name": "Vendor Relations",
            "vendor_contact_role": "Service Delivery Manager",
            "vendor_contact_phone_country_code": "+1",
            "vendor_contact_phone": "2165550142",
            "vendor_contact_email": "contracts@vertexms.com",
            "prior_contract_number": "C-2023-029",
        },
        "sku_items": [
            {
                "sku_number": "SVC-MS-100",
                "description": "Monthly managed services block (40 hrs)",
                "unit_of_measure": "EA",
                "unit_price": 12500.0,
                "msrp": 14000.0,
                "min_order_qty": 1,
                "lead_time": "5 days",
                "status": "Active",
            },
            {
                "sku_number": "SVC-EM-210",
                "description": "After-hours emergency facilities response per incident",
                "unit_of_measure": "EA",
                "unit_price": 950.0,
                "msrp": 1100.0,
                "min_order_qty": 1,
                "lead_time": "2 days",
                "status": "Active",
            },
            {
                "sku_number": "SVC-AUD-050",
                "description": "Quarterly compliance audit support day rate",
                "unit_of_measure": "EA",
                "unit_price": 3200.0,
                "msrp": 3600.0,
                "min_order_qty": 4,
                "lead_time": "10 days",
                "status": "Pending",
            },
        ],
    },
    "C-2023-015_stratagem_services.txt": {
        "id": "stratagem-milestone",
        "label": "Stratagem Consulting — Milestone Payments",
        "description": "Complex tiered payment structure; medium-high extraction confidence.",
        "expected_scenario": "partial",
        "requestor": {
            "requestor_name": "Emily Rodriguez",
            "requestor_business_unit": "Clinical Operations",
            "business_owner": "Michael Torres",
            "business_unit": "Professional Services",
            "business_priority": "High",
            "request_description": "Professional services engagement for healthcare process improvement with milestone-based billing.",
            "need_by_date": "2026-08-20",
        },
        "vendor": {
            "vendor_name": "Stratagem Consulting Partners LLC",
            "vendor_address_line1": "400 Park Avenue South",
            "vendor_address_line2": None,
            "vendor_address_county": "New York County",
            "vendor_address_state": "NY",
            "vendor_address_country": "US",
            "vendor_contact_name": "Billing Department",
            "vendor_contact_role": "Finance Contact",
            "vendor_contact_phone_country_code": "+1",
            "vendor_contact_phone": "2125550847",
            "vendor_contact_email": "billing@stratagemparters.com",
            "vendor_master_id": "SUP-0031",
            "prior_contract_number": "C-2023-015",
        },
        "sku_items": [
            {
                "sku_number": "PS-PHASE-1",
                "description": "Discovery and assessment phase",
                "unit_of_measure": "EA",
                "unit_price": 85000.0,
                "msrp": 95000.0,
                "min_order_qty": 1,
                "lead_time": "30 days",
                "status": "Active",
            },
            {
                "sku_number": "PS-PHASE-2",
                "description": "Implementation and workflow redesign phase",
                "unit_of_measure": "EA",
                "unit_price": 120000.0,
                "msrp": 135000.0,
                "min_order_qty": 1,
                "lead_time": "45 days",
                "status": "Active",
            },
            {
                "sku_number": "PS-PHASE-3",
                "description": "Training and go-live stabilization phase",
                "unit_of_measure": "EA",
                "unit_price": 45000.0,
                "msrp": 52000.0,
                "min_order_qty": 1,
                "lead_time": "21 days",
                "status": "Active",
            },
        ],
    },
    "C-2022-008_primeservice_facilities.txt": {
        "id": "primeservice-facilities",
        "label": "PrimeService — Facilities SLA",
        "description": "SLA-heavy facilities agreement with clear payment windows.",
        "expected_scenario": "pass",
        "requestor": {
            "requestor_name": "Robert Kim",
            "requestor_business_unit": "Facilities Management",
            "business_owner": "Angela Brooks",
            "business_unit": "Hospital Operations",
            "business_priority": "Critical",
            "request_description": "Multi-site facilities management services including preventive maintenance and emergency response per SLA.",
            "need_by_date": "2026-06-30",
        },
        "vendor": {
            "vendor_name": "PrimeService Facilities Group LLC",
            "vendor_address_line1": "800 Commerce Road",
            "vendor_address_line2": None,
            "vendor_address_county": "Davidson County",
            "vendor_address_state": "TN",
            "vendor_address_country": "US",
            "vendor_contact_name": "Facilities Account Lead",
            "vendor_contact_role": "Regional Manager",
            "vendor_contact_phone_country_code": "+1",
            "vendor_contact_phone": "6155550288",
            "vendor_contact_email": "contracts@primeservicefm.com",
            "vendor_master_id": "SUP-0019",
            "prior_contract_number": "C-2022-008",
        },
        "sku_items": [
            {
                "sku_number": "FM-PM-MONTHLY",
                "description": "Preventive maintenance monthly package per site",
                "unit_of_measure": "EA",
                "unit_price": 4500.0,
                "msrp": 5000.0,
                "min_order_qty": 12,
                "lead_time": "7 days",
                "status": "Active",
            },
            {
                "sku_number": "FM-ER-ONCALL",
                "description": "24x7 emergency HVAC and electrical response retainer",
                "unit_of_measure": "EA",
                "unit_price": 2200.0,
                "msrp": 2500.0,
                "min_order_qty": 12,
                "lead_time": "3 days",
                "status": "Active",
            },
            {
                "sku_number": "FM-FLT-HVAC",
                "description": "HEPA HVAC filter replacement kit per air handler",
                "unit_of_measure": "CS",
                "unit_price": 185.0,
                "msrp": 220.0,
                "min_order_qty": 6,
                "lead_time": "14 days",
                "status": "Active",
            },
        ],
    },
    "C-2019-003_vortex_expired.txt": {
        "id": "vortex-expired",
        "label": "Vortex Software — Expired Contract",
        "description": "Contract past expiry; expect fail flags on term dates.",
        "expected_scenario": "fail",
        "requestor": {
            "requestor_name": "Patricia Walsh",
            "requestor_business_unit": "IT Procurement",
            "business_owner": "Steven Hughes",
            "business_unit": "Information Technology",
            "business_priority": "Low",
            "request_description": "Software license renewal evaluation for legacy ERP support module — verify contract status before proceeding.",
            "need_by_date": "2026-10-01",
        },
        "vendor": {
            "vendor_name": "Vortex Software Solutions Inc.",
            "vendor_address_line1": "350 Technology Drive",
            "vendor_address_line2": None,
            "vendor_address_county": "Fairfax County",
            "vendor_address_state": "VA",
            "vendor_address_country": "US",
            "vendor_contact_name": "Accounts Payable",
            "vendor_contact_role": "Billing Contact",
            "vendor_contact_phone_country_code": "+1",
            "vendor_contact_phone": "7035550364",
            "vendor_contact_email": "accounts@vortexsoftware.com",
            "vendor_master_id": "SUP-0007",
            "prior_contract_number": "C-2019-003",
        },
        "sku_items": [
            {
                "sku_number": "SW-LIC-ENT",
                "description": "Enterprise license seat annual",
                "unit_of_measure": "EA",
                "unit_price": 1200.0,
                "msrp": 1500.0,
                "min_order_qty": 50,
                "lead_time": "3 days",
                "status": "Active",
            },
            {
                "sku_number": "SW-SUP-PREM",
                "description": "Premium support and patch entitlement per seat",
                "unit_of_measure": "EA",
                "unit_price": 280.0,
                "msrp": 350.0,
                "min_order_qty": 50,
                "lead_time": "5 days",
                "status": "Active",
            },
            {
                "sku_number": "SW-MOD-LEGACY",
                "description": "Legacy ERP connector module maintenance",
                "unit_of_measure": "EA",
                "unit_price": 4500.0,
                "msrp": 5200.0,
                "min_order_qty": 1,
                "lead_time": "120 days",
                "status": "Discontinued",
            },
        ],
    },
}


def main():
    FIXTURES.mkdir(parents=True, exist_ok=True)
    for filename, meta in SCENARIOS.items():
        contract_path = CONTRACTS / filename
        if not contract_path.exists():
            print(f"Skip missing: {filename}")
            continue
        contract_text = contract_path.read_text(encoding="utf-8")
        addendum = (
            contract_text[:6000]
            + "\n\n--- SKU ADDENDUM POLICIES ---\n"
            "Price changes require 30 days written notice. "
            "Product recall procedures: vendor shall notify buyer within 24 hours of recall initiation. "
            "Minimum annual purchase commitment applies per master agreement."
        )
        payload = {
            "requestor": meta["requestor"],
            "vendor": meta["vendor"],
            "contract_text": contract_text,
            "contract_filename": filename,
            "sku_items": meta["sku_items"],
            "addendum_text": addendum,
        }
        fid = meta["id"]
        (FIXTURES / f"{fid}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        (FIXTURES / f"{fid}.meta.json").write_text(
            json.dumps(
                {
                    "label": meta["label"],
                    "description": meta["description"],
                    "contract_file": filename,
                    "expected_scenario": meta["expected_scenario"],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"Generated {fid}")


if __name__ == "__main__":
    main()
