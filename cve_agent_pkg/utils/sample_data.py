"""
Sample data loader for testing CVE Agent
Inserts sample CVE data into MongoDB
"""
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()


def load_sample_data():
    """
    Load sample CVE data into MongoDB for testing
    Note: This will only insert if the CVE doesn't already exist
    """
    # Sample CVE data
    SAMPLE_CVE = {
        "cveId": "CVE-1999-0095",
        "published": "1988-10-01T04:00:00.000",
        "lastModified": "2025-04-03T01:03:51.193",
        "sourceIdentifier": "cve@mitre.org",
        "vulnStatus": "Deferred",
        "descriptions": [
            {
                "lang": "en",
                "value": "The debug command in Sendmail is enabled, allowing attackers to execute commands as root."
            },
            {
                "lang": "es",
                "value": "El comando de depuración de Sendmail está activado, permitiendo a atacantes ejecutar comandos como root."
            }
        ],
        "metrics": {
            "cvssMetricV2": [
                {
                    "source": "nvd@nist.gov",
                    "type": "Primary",
                    "cvssData": {
                        "version": "2.0",
                        "vectorString": "AV:N/AC:L/Au:N/C:C/I:C/A:C",
                        "baseScore": 10.0,
                        "accessVector": "NETWORK",
                        "accessComplexity": "LOW",
                        "authentication": "NONE",
                        "confidentialityImpact": "COMPLETE",
                        "integrityImpact": "COMPLETE",
                        "availabilityImpact": "COMPLETE"
                    },
                    "baseSeverity": "HIGH",
                    "exploitabilityScore": 10.0,
                    "impactScore": 10.0,
                    "acInsufInfo": False,
                    "obtainAllPrivilege": True,
                    "obtainUserPrivilege": False,
                    "obtainOtherPrivilege": False,
                    "userInteractionRequired": False
                }
            ]
        },
        "weaknesses": [
            {
                "source": "nvd@nist.gov",
                "type": "Primary",
                "description": [
                    {
                        "lang": "en",
                        "value": "NVD-CWE-Other"
                    }
                ]
            }
        ],
        "references": [
            {
                "url": "http://seclists.org/fulldisclosure/2019/Jun/16",
                "source": "cve@mitre.org",
                "tags": None
            },
            {
                "url": "http://www.securityfocus.com/bid/1",
                "source": "cve@mitre.org",
                "tags": None
            }
        ]
    }

    try:
        # Connect to MongoDB
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
        db_name = os.getenv('MONGO_DB', 'cve_database')
        collection_name = os.getenv('MONGO_COLLECTION', 'cves')

        client = MongoClient(mongo_uri)
        db = client[db_name]
        collection = db[collection_name]

        # Check if CVE already exists
        existing = collection.find_one({'cveId': SAMPLE_CVE['cveId']})

        if existing:
            print(f"ℹ️  Sample data already exists: {SAMPLE_CVE['cveId']}")
            print("No action taken.")
        else:
            # Insert sample data
            result = collection.insert_one(SAMPLE_CVE)
            print(f"✅ Sample CVE data loaded successfully!")
            print(f"   CVE ID: {SAMPLE_CVE['cveId']}")
            print(f"   Document ID: {result.inserted_id}")

        client.close()
        return True

    except Exception as e:
        print(f"❌ Error loading sample data: {e}")
        return False


if __name__ == '__main__':
    print("=" * 70)
    print("📦 CVE Agent - Sample Data Loader")
    print("=" * 70)
    print()
    load_sample_data()
    print()
    print("=" * 70)

