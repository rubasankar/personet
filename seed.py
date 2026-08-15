"""
seed.py - Database seeding utility for PerNet.

Usage examples
--------------
Full seed (append / idempotent):
    uv run python seed.py

Wipe everything first, then seed fresh:
    uv run python seed.py --fresh

Seed only users + constraints (no relationships):
    uv run python seed.py --only users constraints

Seed only KNOWS relationships (graph edges):
    uv run python seed.py --only knows

Wipe only the graph data, skip seeding:
    uv run python seed.py --fresh --only none

Available --only tokens:
    constraints   create/verify schema constraints & indexes
    institutions  Institution nodes
    companies     Company nodes
    users         User nodes
    studied_at    STUDIED_AT relationships
    worked_at     WORKED_AT relationships
    knows         KNOWS relationships
    all           everything (default)
    none          nothing - useful with --fresh to just wipe
"""

import argparse
import asyncio
import logging
import logging.config
import sys

import bcrypt

from app.config import get_settings
from app.database import close_driver
from app.database import init_driver
from app.database import run_query

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s %(levelname)-8s %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S",
            }
        },
        "handlers": {
            "console": {"class": "logging.StreamHandler", "formatter": "default"}
        },
        "root": {"handlers": ["console"], "level": "INFO"},
    }
)

log = logging.getLogger("seed")

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

_ALL_STEPS = [
    "constraints",
    "institutions",
    "companies",
    "users",
    "studied_at",
    "worked_at",
    "knows",
]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed the PerNet graph database.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="WIPE all nodes and relationships before seeding. "
        "Warning: this is destructive and irreversible.",
    )
    parser.add_argument(
        "--only",
        nargs="+",
        metavar="STEP",
        default=["all"],
        choices=[*_ALL_STEPS, "all", "none"],
        help="Space-separated list of steps to run. Defaults to 'all'.",
    )
    parser.add_argument(
        "--users",
        type=int,
        default=None,
        metavar="N",
        help="Seed only the first N users (and their relationships). "
        "Useful for a small local dataset.",
    )
    parser.add_argument(
        "--password",
        default="Password123!",
        metavar="PWD",
        help="Plain-text password to hash for all seed users. Default: Password123!",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity. Default: INFO.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


# ---------------------------------------------------------------------------
# Schema DDL
# ---------------------------------------------------------------------------

CONSTRAINTS = [
    (
        "unique_user_id",
        (
            "CREATE CONSTRAINT unique_user_id IF NOT EXISTS "
            "FOR (u:User) REQUIRE u.id IS UNIQUE"
        ),
    ),
    (
        "unique_user_email",
        (
            "CREATE CONSTRAINT unique_user_email IF NOT EXISTS "
            "FOR (u:User) REQUIRE u.email IS UNIQUE"
        ),
    ),
    (
        "unique_institution_id",
        (
            "CREATE CONSTRAINT unique_institution_id IF NOT EXISTS "
            "FOR (i:Institution) REQUIRE i.id IS UNIQUE"
        ),
    ),
    (
        "unique_company_id",
        (
            "CREATE CONSTRAINT unique_company_id IF NOT EXISTS "
            "FOR (c:Company) REQUIRE c.id IS UNIQUE"
        ),
    ),
]

INDEXES = [
    (
        "idx_institution_name",
        (
            "CREATE INDEX idx_institution_name IF NOT EXISTS "
            "FOR (i:Institution) ON (i.name)"
        ),
    ),
    (
        "idx_company_name",
        "CREATE INDEX idx_company_name IF NOT EXISTS FOR (c:Company) ON (c.name)",
    ),
    (
        "idx_user_name",
        "CREATE INDEX idx_user_name IF NOT EXISTS FOR (u:User) ON (u.name)",
    ),
]

# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

INSTITUTIONS = [
    {"name": "MIT", "type": "university"},
    {"name": "Stanford University", "type": "university"},
    {"name": "Harvard University", "type": "university"},
    {"name": "Carnegie Mellon University", "type": "university"},
    {"name": "University of California, Berkeley", "type": "university"},
    {"name": "Oxford University", "type": "university"},
    {"name": "Cambridge University", "type": "university"},
]

COMPANIES = [
    {"name": "Google"},
    {"name": "Microsoft"},
    {"name": "Amazon"},
    {"name": "Apple"},
    {"name": "Meta"},
    {"name": "Netflix"},
    {"name": "Stripe"},
]

USERS = [
    {
        "name": "Alice Chen",
        "email": "alice.chen@example.com",
        "bio": "ML researcher",
        "location": "San Francisco, CA",
    },
    {
        "name": "Bob Martinez",
        "email": "bob.martinez@example.com",
        "bio": "Backend engineer",
        "location": "Seattle, WA",
    },
    {
        "name": "Carol Johnson",
        "email": "carol.johnson@example.com",
        "bio": "Data scientist",
        "location": "New York, NY",
    },
    {
        "name": "David Lee",
        "email": "david.lee@example.com",
        "bio": "Product manager",
        "location": "Austin, TX",
    },
    {
        "name": "Eva Williams",
        "email": "eva.williams@example.com",
        "bio": "Frontend developer",
        "location": "Boston, MA",
    },
    {
        "name": "Frank Brown",
        "email": "frank.brown@example.com",
        "bio": "DevOps engineer",
        "location": "Chicago, IL",
    },
    {
        "name": "Grace Kim",
        "email": "grace.kim@example.com",
        "bio": "UX designer",
        "location": "Los Angeles, CA",
    },
    {
        "name": "Henry Davis",
        "email": "henry.davis@example.com",
        "bio": "Security researcher",
        "location": "Washington, DC",
    },
    {
        "name": "Iris Thompson",
        "email": "iris.thompson@example.com",
        "bio": "Cloud architect",
        "location": "Denver, CO",
    },
    {
        "name": "Jack Wilson",
        "email": "jack.wilson@example.com",
        "bio": "Full-stack developer",
        "location": "Portland, OR",
    },
    {
        "name": "Karen Moore",
        "email": "karen.moore@example.com",
        "bio": "AI engineer",
        "location": "San Jose, CA",
    },
    {
        "name": "Liam Taylor",
        "email": "liam.taylor@example.com",
        "bio": "Systems programmer",
        "location": "Austin, TX",
    },
    {
        "name": "Mia Anderson",
        "email": "mia.anderson@example.com",
        "bio": "Mobile developer",
        "location": "Miami, FL",
    },
    {
        "name": "Noah Jackson",
        "email": "noah.jackson@example.com",
        "bio": "Data engineer",
        "location": "Atlanta, GA",
    },
    {
        "name": "Olivia White",
        "email": "olivia.white@example.com",
        "bio": "Site reliability engineer",
        "location": "Seattle, WA",
    },
    {
        "name": "Paul Harris",
        "email": "paul.harris@example.com",
        "bio": "Research scientist",
        "location": "Cambridge, MA",
    },
    {
        "name": "Quinn Martin",
        "email": "quinn.martin@example.com",
        "bio": "Platform engineer",
        "location": "San Francisco, CA",
    },
    {
        "name": "Rachel Garcia",
        "email": "rachel.garcia@example.com",
        "bio": "Technical writer",
        "location": "Phoenix, AZ",
    },
    {
        "name": "Sam Clark",
        "email": "sam.clark@example.com",
        "bio": "Database administrator",
        "location": "Dallas, TX",
    },
    {
        "name": "Tina Lewis",
        "email": "tina.lewis@example.com",
        "bio": "Embedded systems engineer",
        "location": "San Diego, CA",
    },
    {
        "name": "Uma Robinson",
        "email": "uma.robinson@example.com",
        "bio": "Compiler engineer",
        "location": "Palo Alto, CA",
    },
    {
        "name": "Victor Walker",
        "email": "victor.walker@example.com",
        "bio": "Network engineer",
        "location": "Houston, TX",
    },
    {
        "name": "Wendy Hall",
        "email": "wendy.hall@example.com",
        "bio": "Quantum computing researcher",
        "location": "Boston, MA",
    },
    {
        "name": "Xander Allen",
        "email": "xander.allen@example.com",
        "bio": "Robotics engineer",
        "location": "Pittsburgh, PA",
    },
    {
        "name": "Yuki Young",
        "email": "yuki.young@example.com",
        "bio": "NLP researcher",
        "location": "New York, NY",
    },
    {
        "name": "Zoe Hernandez",
        "email": "zoe.hernandez@example.com",
        "bio": "Bioinformatics engineer",
        "location": "San Francisco, CA",
    },
    {
        "name": "Aaron King",
        "email": "aaron.king@example.com",
        "bio": "Infrastructure engineer",
        "location": "Chicago, IL",
    },
    {
        "name": "Bella Wright",
        "email": "bella.wright@example.com",
        "bio": "Accessibility specialist",
        "location": "Portland, OR",
    },
    {
        "name": "Carlos Lopez",
        "email": "carlos.lopez@example.com",
        "bio": "Fintech developer",
        "location": "Miami, FL",
    },
    {
        "name": "Diana Scott",
        "email": "diana.scott@example.com",
        "bio": "Computer vision engineer",
        "location": "Pittsburgh, PA",
    },
    {
        "name": "Ethan Green",
        "email": "ethan.green@example.com",
        "bio": "Game developer",
        "location": "Los Angeles, CA",
    },
    {
        "name": "Fiona Adams",
        "email": "fiona.adams@example.com",
        "bio": "Operating systems engineer",
        "location": "Seattle, WA",
    },
    {
        "name": "George Baker",
        "email": "george.baker@example.com",
        "bio": "Distributed systems researcher",
        "location": "San Jose, CA",
    },
    {
        "name": "Hannah Nelson",
        "email": "hannah.nelson@example.com",
        "bio": "Cryptography engineer",
        "location": "Washington, DC",
    },
    {
        "name": "Ivan Carter",
        "email": "ivan.carter@example.com",
        "bio": "Blockchain developer",
        "location": "Austin, TX",
    },
]

# Each entry: user_idx, institution_idx, degree, department, start_year, end_year
STUDIED_AT_RELS = [
    (0, 0, "PhD", "Computer Science", 2012, 2018),
    (1, 1, "BS", "Computer Science", 2010, 2014),
    (2, 2, "MS", "Data Science", 2015, 2017),
    (3, 1, "MBA", "Business", 2014, 2016),
    (4, 3, "BS", "Computer Science", 2013, 2017),
    (5, 4, "MS", "Electrical Engineering", 2011, 2013),
    (6, 2, "BA", "Design", 2016, 2020),
    (7, 0, "PhD", "Security", 2010, 2016),
    (8, 5, "MS", "Cloud Computing", 2013, 2015),
    (9, 3, "BS", "Software Engineering", 2015, 2019),
    (10, 0, "PhD", "Machine Learning", 2014, 2020),
    (11, 1, "BS", "Computer Science", 2012, 2016),
    (12, 6, "BS", "Computer Science", 2016, 2020),
    (13, 4, "MS", "Data Engineering", 2013, 2015),
    (14, 1, "MS", "Systems Engineering", 2015, 2017),
    (15, 2, "PhD", "Applied Mathematics", 2011, 2017),
    (16, 0, "MS", "Computer Science", 2016, 2018),
    (17, 3, "BA", "English", 2012, 2016),
    (18, 4, "MS", "Database Systems", 2014, 2016),
    (19, 5, "MS", "Embedded Systems", 2013, 2015),
    (20, 0, "PhD", "Programming Languages", 2010, 2016),
    (21, 4, "BS", "Networking", 2011, 2015),
    (22, 2, "PhD", "Quantum Computing", 2013, 2019),
    (23, 3, "MS", "Robotics", 2015, 2017),
    (24, 0, "PhD", "NLP", 2016, 2022),
    (25, 1, "MS", "Bioinformatics", 2014, 2016),
    (26, 4, "BS", "Computer Science", 2013, 2017),
    (27, 5, "BA", "Inclusive Design", 2015, 2019),
    (28, 6, "MS", "Finance", 2016, 2018),
    (29, 3, "PhD", "Computer Vision", 2013, 2019),
    (30, 1, "BS", "Game Design", 2017, 2021),
    (31, 2, "PhD", "Operating Systems", 2012, 2018),
    (32, 0, "PhD", "Distributed Systems", 2011, 2017),
    (33, 2, "PhD", "Cryptography", 2014, 2020),
    (34, 6, "MS", "Blockchain", 2018, 2020),
]

# Each entry: user_idx, company_idx, role, start_year, end_year, is_current
WORKED_AT_RELS = [
    (0, 0, "Research Scientist", 2018, None, True),
    (1, 1, "Senior Software Engineer", 2014, 2019, False),
    (1, 2, "Principal Engineer", 2019, None, True),
    (2, 0, "Data Scientist", 2017, 2020, False),
    (2, 6, "ML Engineer", 2020, None, True),
    (3, 4, "Product Manager", 2016, 2021, False),
    (3, 5, "Senior PM", 2021, None, True),
    (4, 0, "Frontend Engineer", 2017, None, True),
    (5, 2, "DevOps Engineer", 2013, 2018, False),
    (5, 1, "Cloud Engineer", 2018, None, True),
    (6, 3, "UX Designer", 2020, None, True),
    (7, 0, "Security Engineer", 2016, 2020, False),
    (7, 1, "Security Researcher", 2020, None, True),
    (8, 2, "Cloud Architect", 2015, None, True),
    (9, 0, "Full-Stack Engineer", 2019, None, True),
    (10, 4, "AI Engineer", 2020, None, True),
    (11, 1, "Systems Engineer", 2016, 2021, False),
    (11, 3, "Platform Engineer", 2021, None, True),
    (12, 5, "Mobile Developer", 2020, None, True),
    (13, 2, "Data Engineer", 2015, 2020, False),
    (13, 6, "Data Engineer", 2020, None, True),
    (14, 0, "SRE", 2017, None, True),
    (15, 1, "Research Scientist", 2017, None, True),
    (16, 3, "Platform Engineer", 2018, None, True),
    (17, 4, "Technical Writer", 2016, 2019, False),
    (17, 5, "Content Strategist", 2019, None, True),
    (18, 2, "Database Engineer", 2016, None, True),
    (19, 3, "Embedded Engineer", 2015, None, True),
    (20, 1, "Compiler Engineer", 2016, None, True),
    (21, 0, "Network Engineer", 2015, 2019, False),
    (21, 2, "Network Architect", 2019, None, True),
    (22, 1, "Quantum Researcher", 2019, None, True),
    (23, 4, "Robotics Engineer", 2017, None, True),
    (24, 0, "NLP Researcher", 2022, None, True),
    (25, 6, "Bioinformatics Engineer", 2016, None, True),
    (26, 2, "Infrastructure Engineer", 2017, None, True),
    (27, 3, "Accessibility Engineer", 2019, None, True),
    (28, 6, "Fintech Developer", 2018, None, True),
    (29, 0, "CV Engineer", 2019, None, True),
    (30, 4, "Game Developer", 2021, None, True),
    (31, 1, "OS Engineer", 2018, None, True),
    (32, 2, "Distributed Systems Eng", 2017, None, True),
    (33, 6, "Cryptography Engineer", 2020, None, True),
    (34, 6, "Blockchain Developer", 2020, None, True),
]

# Each entry: user_a_idx, user_b_idx, context, since, closeness
# Chain from Alice (index 0) through Bob and Ethan to Ivan (index 34) yields 3 hops.
KNOWS_RELS = [
    (0, 1, "colleague", "2018-06-01", "close"),
    (1, 2, "classmate", "2015-09-01", "close"),
    (2, 3, "colleague", "2017-03-15", "acquaintance"),
    (3, 4, "colleague", "2016-08-20", "close"),
    (4, 5, "classmate", "2013-09-01", "close"),
    (5, 6, "colleague", "2020-01-10", "acquaintance"),
    (6, 7, "friend", "2021-05-01", "close"),
    (7, 8, "colleague", "2016-11-15", "acquaintance"),
    (8, 9, "classmate", "2015-09-01", "close"),
    (9, 10, "colleague", "2019-07-20", "close"),
    (0, 10, "colleague", "2020-02-14", "close"),
    (1, 11, "classmate", "2012-09-01", "close"),
    (11, 12, "colleague", "2021-03-01", "acquaintance"),
    (12, 13, "classmate", "2016-09-01", "close"),
    (13, 14, "colleague", "2017-06-15", "close"),
    (14, 15, "classmate", "2015-09-01", "acquaintance"),
    (15, 16, "colleague", "2018-09-01", "close"),
    (16, 17, "colleague", "2018-11-01", "acquaintance"),
    (17, 18, "friend", "2019-01-20", "acquaintance"),
    (18, 19, "colleague", "2016-05-10", "close"),
    (19, 20, "classmate", "2013-09-01", "close"),
    (20, 21, "colleague", "2016-07-01", "acquaintance"),
    (21, 22, "friend", "2019-08-15", "close"),
    (22, 23, "classmate", "2015-09-01", "close"),
    (23, 24, "classmate", "2016-09-01", "acquaintance"),
    (24, 25, "colleague", "2022-01-10", "close"),
    (25, 26, "classmate", "2014-09-01", "acquaintance"),
    (26, 27, "colleague", "2019-04-05", "close"),
    (27, 28, "classmate", "2016-09-01", "acquaintance"),
    (28, 29, "colleague", "2020-02-01", "close"),
    (29, 30, "colleague", "2021-06-01", "acquaintance"),
    (1, 30, "colleague", "2021-08-01", "acquaintance"),  # Bob -> Ethan
    (30, 34, "colleague", "2021-10-01", "acquaintance"),  # Ethan -> Ivan
    (3, 10, "colleague", "2021-09-15", "acquaintance"),
    (5, 15, "classmate", "2011-09-01", "close"),
    (10, 20, "colleague", "2020-06-01", "close"),
    (15, 25, "colleague", "2017-01-15", "acquaintance"),
    (20, 30, "classmate", "2017-09-01", "acquaintance"),
    (25, 31, "classmate", "2014-09-01", "close"),
    (31, 32, "classmate", "2012-09-01", "close"),
    (32, 33, "colleague", "2017-09-01", "acquaintance"),
]


# ---------------------------------------------------------------------------
# Wipe
# ---------------------------------------------------------------------------


async def wipe_database() -> None:
    log.warning("Wiping all nodes and relationships from the database...")
    await run_query("MATCH (n) DETACH DELETE n")
    log.info("Database wiped.")


# ---------------------------------------------------------------------------
# Step functions
# ---------------------------------------------------------------------------


async def run_constraints() -> None:
    log.info("Applying %d constraints...", len(CONSTRAINTS))
    for name, cypher in CONSTRAINTS:
        await run_query(cypher)
        log.debug("  constraint ready: %s", name)
    log.info("Applying %d indexes...", len(INDEXES))
    for name, cypher in INDEXES:
        try:
            await run_query(cypher)
            log.debug("  index ready: %s", name)
        except Exception as exc:  # noqa: BLE001 - best-effort DDL, driver
            # raises varied/undocumented error types across backends.
            log.warning("  index skipped (%s): %s", name, exc)
    log.info("Schema DDL done.")


async def run_institutions() -> list[str]:
    log.info("Seeding %d institutions...", len(INSTITUTIONS))
    ids: list[str] = []
    for inst in INSTITUTIONS:
        rows = await run_query(
            """
            MERGE (i:Institution {name: $name})
            ON CREATE SET i.id = randomUUID(), i.type = $type
            ON MATCH  SET i.type = $type
            RETURN i.id AS id
            """,
            {"name": inst["name"], "type": inst["type"]},
        )
        ids.append(rows[0]["id"])
        log.debug("  institution: %s", inst["name"])
    log.info("%d institution nodes ready.", len(ids))
    return ids


async def run_companies() -> list[str]:
    log.info("Seeding %d companies...", len(COMPANIES))
    ids: list[str] = []
    for company in COMPANIES:
        rows = await run_query(
            """
            MERGE (c:Company {name: $name})
            ON CREATE SET c.id = randomUUID()
            RETURN c.id AS id
            """,
            {"name": company["name"]},
        )
        ids.append(rows[0]["id"])
        log.debug("  company: %s", company["name"])
    log.info("%d company nodes ready.", len(ids))
    return ids


async def run_users(user_limit: int | None, password_hash: str) -> list[str]:
    users = USERS[:user_limit] if user_limit is not None else USERS
    log.info("Seeding %d users (limit=%s)...", len(users), user_limit or "none")
    ids: list[str] = []
    for user in users:
        rows = await run_query(
            """
            MERGE (u:User {email: $email})
            ON CREATE SET
                u.id            = randomUUID(),
                u.name          = $name,
                u.password_hash = $password_hash,
                u.bio           = $bio,
                u.location      = $location,
                u.created_at    = $created_at
            ON MATCH SET
                u.name     = $name,
                u.bio      = $bio,
                u.location = $location
            RETURN u.id AS id
            """,
            {
                "email": user["email"],
                "name": user["name"],
                "password_hash": password_hash,
                "bio": user.get("bio", ""),
                "location": user.get("location", ""),
                "created_at": "2024-01-01T00:00:00Z",
            },
        )
        ids.append(rows[0]["id"])
        log.debug("  user: %s <%s>", user["name"], user["email"])
    log.info("%d user nodes ready.", len(ids))
    return ids


async def run_studied_at(user_ids: list[str], institution_ids: list[str]) -> None:
    # Only include relationships whose user index is within the seeded slice.
    rels = [r for r in STUDIED_AT_RELS if r[0] < len(user_ids)]
    log.info("Creating %d STUDIED_AT relationships...", len(rels))
    for u_idx, i_idx, degree, department, start_year, end_year in rels:
        await run_query(
            """
            MATCH (u:User {id: $user_id})
            MATCH (i:Institution {id: $inst_id})
            MERGE (u)-[r:STUDIED_AT {
                degree: $degree, department: $department, start_year: $start_year
            }]->(i)
            ON CREATE SET r.end_year = $end_year
            """,
            {
                "user_id": user_ids[u_idx],
                "inst_id": institution_ids[i_idx],
                "degree": degree,
                "department": department,
                "start_year": start_year,
                "end_year": end_year,
            },
        )
    log.info("%d STUDIED_AT relationships ready.", len(rels))


async def run_worked_at(user_ids: list[str], company_ids: list[str]) -> None:
    rels = [r for r in WORKED_AT_RELS if r[0] < len(user_ids)]
    log.info("Creating %d WORKED_AT relationships...", len(rels))
    for u_idx, c_idx, role, start_year, end_year, is_current in rels:
        await run_query(
            """
            MATCH (u:User {id: $user_id})
            MATCH (c:Company {id: $company_id})
            MERGE (u)-[r:WORKED_AT {role: $role, start_year: $start_year}]->(c)
            ON CREATE SET r.end_year = $end_year, r.is_current = $is_current
            """,
            {
                "user_id": user_ids[u_idx],
                "company_id": company_ids[c_idx],
                "role": role,
                "start_year": start_year,
                "end_year": end_year,
                "is_current": is_current,
            },
        )
    log.info("%d WORKED_AT relationships ready.", len(rels))


async def run_knows(user_ids: list[str]) -> None:
    rels = [r for r in KNOWS_RELS if r[0] < len(user_ids) and r[1] < len(user_ids)]
    log.info("Creating %d KNOWS pairs (bidirectional)...", len(rels))
    for a_idx, b_idx, context, since, closeness in rels:
        await run_query(
            """
            MATCH (a:User {id: $user_a}), (b:User {id: $user_b})
            MERGE (a)-[:KNOWS {
                context: $context, since: $since, closeness: $closeness
            }]->(b)
            MERGE (b)-[:KNOWS {
                context: $context, since: $since, closeness: $closeness
            }]->(a)
            """,
            {
                "user_a": user_ids[a_idx],
                "user_b": user_ids[b_idx],
                "context": context,
                "since": since,
                "closeness": closeness,
            },
        )
    log.info("%d directed KNOWS edges ready.", len(rels) * 2)


IVAN_USER_INDEX = 34
EXPECTED_MIN_HOPS = 3


async def verify_hop_distance(user_ids: list[str]) -> None:
    """Verify Alice(0) -> Ivan(34) is >= 3 hops when both are in the seeded slice."""
    if len(user_ids) <= IVAN_USER_INDEX:
        log.debug("Skipping hop verification - fewer than 35 users seeded.")
        return

    rows = await run_query(
        """
        MATCH path = shortestPath(
            (a:User {id: $user_a})-[:KNOWS*]-(b:User {id: $user_b})
        )
        RETURN length(path) AS hops
        """,
        {"user_a": user_ids[0], "user_b": user_ids[IVAN_USER_INDEX]},
    )
    if rows:
        hops = rows[0]["hops"]
        if hops >= EXPECTED_MIN_HOPS:
            log.info("Hop verification passed: Alice -> Ivan = %d hops.", hops)
        else:
            log.warning(
                "Hop verification: expected ≥ 3, got %d. Check KNOWS_RELS.", hops
            )
    else:
        log.warning("Hop verification: no path found between Alice and Ivan.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def _resolve_steps(only: list[str]) -> set[str]:
    if "none" in only:
        return set()
    if "all" in only:
        return set(_ALL_STEPS)
    return set(only)


async def _resolve_institution_ids(steps: set[str]) -> list[str]:
    if "institutions" in steps:
        return await run_institutions()
    if steps & {"studied_at"}:
        rows = await run_query(
            "MATCH (i:Institution) RETURN i.id AS id ORDER BY i.name"
        )
        ids = [r["id"] for r in rows]
        log.debug("Loaded %d existing institution IDs.", len(ids))
        return ids
    return []


async def _resolve_company_ids(steps: set[str]) -> list[str]:
    if "companies" in steps:
        return await run_companies()
    if steps & {"worked_at"}:
        rows = await run_query("MATCH (c:Company) RETURN c.id AS id ORDER BY c.name")
        ids = [r["id"] for r in rows]
        log.debug("Loaded %d existing company IDs.", len(ids))
        return ids
    return []


async def _resolve_user_ids(
    steps: set[str], args: argparse.Namespace, password_hash: str
) -> list[str]:
    if "users" in steps:
        return await run_users(args.users, password_hash)
    if steps & {"studied_at", "worked_at", "knows"}:
        rows = await run_query(
            "MATCH (u:User) RETURN u.id AS id, u.email AS email "
            "ORDER BY u.created_at, u.email"
        )
        ids = [r["id"] for r in rows]
        log.debug("Loaded %d existing user IDs.", len(ids))
        return ids
    return []


async def _run_relationship_steps(
    steps: set[str],
    user_ids: list[str],
    institution_ids: list[str],
    company_ids: list[str],
) -> None:
    if "studied_at" in steps:
        if institution_ids and user_ids:
            await run_studied_at(user_ids, institution_ids)
        else:
            log.warning("Skipping studied_at - institution or user IDs not available.")

    if "worked_at" in steps:
        if company_ids and user_ids:
            await run_worked_at(user_ids, company_ids)
        else:
            log.warning("Skipping worked_at - company or user IDs not available.")

    if "knows" in steps:
        if user_ids:
            await run_knows(user_ids)
        else:
            log.warning("Skipping knows - user IDs not available.")

    if "knows" in steps or "users" in steps:
        await verify_hop_distance(user_ids)


async def _run_seed(steps: set[str], args: argparse.Namespace) -> None:
    log.info("Steps to run: %s", ", ".join(sorted(steps)))

    # Pre-hash password once (bcrypt is slow by design).
    password_hash = hash_password(args.password)

    if "constraints" in steps:
        await run_constraints()

    # Node IDs are needed to wire up relationships; fetch from DB if we
    # skipped the seeding step so --only relationships still works.
    institution_ids = await _resolve_institution_ids(steps)
    company_ids = await _resolve_company_ids(steps)
    user_ids = await _resolve_user_ids(steps, args, password_hash)

    await _run_relationship_steps(steps, user_ids, institution_ids, company_ids)

    log.info("Seeding complete.")


async def main() -> None:
    args = _parse_args()

    # Apply requested log level.
    logging.getLogger().setLevel(args.log_level)

    steps = _resolve_steps(args.only)

    cfg = get_settings()
    log.info("Connecting to %s ...", cfg.COGNODB_URI)
    await init_driver(cfg.COGNODB_URI, cfg.COGNODB_USER, cfg.COGNODB_PASSWORD)

    try:
        if args.fresh:
            await wipe_database()

        if not steps:
            log.info("No steps selected - nothing to seed.")
            return

        await _run_seed(steps, args)

    except Exception as exc:
        log.critical("Seeding failed: %s", exc, exc_info=True)
        sys.exit(1)
    finally:
        await close_driver()


if __name__ == "__main__":
    asyncio.run(main())
