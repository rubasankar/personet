# All Cypher strings for the profile module.
# No Cypher should appear in router.py or schemas.py.
# All queries use $paramName syntax - never string concatenation of user input.

# ---------------------------------------------------------------------------
# User profile node
# ---------------------------------------------------------------------------

GET_PROFILE_ME = """
MATCH (u:User {id: $id})
RETURN u, COUNT { (u)-[:KNOWS]->() } AS connection_count
"""

UPDATE_PROFILE = """
MATCH (u:User {id: $id})
SET u.name     = COALESCE($name, u.name),
    u.bio      = COALESCE($bio, u.bio),
    u.location = COALESCE($location, u.location)
RETURN u, COUNT { (u)-[:KNOWS]->() } AS connection_count
"""

DELETE_PROFILE = """
MATCH (u:User {id: $id})
DETACH DELETE u
"""

# ---------------------------------------------------------------------------
# Education (STUDIED_AT relationships)
# ---------------------------------------------------------------------------

MERGE_INSTITUTION = """
MERGE (i:Institution {name: $name})
ON CREATE SET i.id = randomUUID(), i.type = $type
RETURN i
"""

CREATE_STUDIED_AT = """
MATCH (u:User {id: $user_id}), (i:Institution {name: $institution_name})
CREATE (u)-[:STUDIED_AT {
    degree:     $degree,
    department: $department,
    start_year: $start_year,
    end_year:   $end_year
}]->(i)
RETURN u, i
"""

GET_EDUCATION = """
MATCH (u:User {id: $user_id})-[r:STUDIED_AT]->(i:Institution)
RETURN i.name AS institution_name, i.type AS institution_type,
       r.degree AS degree, r.department AS department,
       r.start_year AS start_year, r.end_year AS end_year
ORDER BY r.start_year DESC
"""

UPDATE_STUDIED_AT = """
MATCH (u:User {id: $user_id})-[r:STUDIED_AT]->(i:Institution {name: $institution_name})
WHERE r.start_year = $start_year
SET r.degree     = COALESCE($degree, r.degree),
    r.department = COALESCE($department, r.department),
    r.end_year   = COALESCE($end_year, r.end_year)
RETURN i.name AS institution_name, i.type AS institution_type,
       r.degree AS degree, r.department AS department,
       r.start_year AS start_year, r.end_year AS end_year
"""

DELETE_STUDIED_AT = """
MATCH (u:User {id: $user_id})-[r:STUDIED_AT]->(i:Institution {name: $institution_name})
WHERE r.start_year = $start_year
DELETE r
RETURN count(r) AS deleted
"""

# ---------------------------------------------------------------------------
# Employment (WORKED_AT relationships)
# ---------------------------------------------------------------------------

MERGE_COMPANY = """
MERGE (c:Company {name: $name})
ON CREATE SET c.id = randomUUID()
RETURN c
"""

CREATE_WORKED_AT = """
MATCH (u:User {id: $user_id}), (c:Company {name: $company_name})
CREATE (u)-[:WORKED_AT {
    role:       $role,
    start_year: $start_year,
    end_year:   $end_year,
    is_current: $is_current
}]->(c)
RETURN u, c
"""

GET_EMPLOYMENT = """
MATCH (u:User {id: $user_id})-[r:WORKED_AT]->(c:Company)
RETURN c.name AS company_name,
       r.role AS role, r.start_year AS start_year,
       r.end_year AS end_year, r.is_current AS is_current
ORDER BY r.start_year DESC
"""

UPDATE_WORKED_AT = """
MATCH (u:User {id: $user_id})-[r:WORKED_AT]->(c:Company {name: $company_name})
WHERE r.start_year = $start_year
SET r.role       = COALESCE($role, r.role),
    r.end_year   = COALESCE($end_year, r.end_year),
    r.is_current = COALESCE($is_current, r.is_current)
RETURN c.name AS company_name,
       r.role AS role, r.start_year AS start_year,
       r.end_year AS end_year, r.is_current AS is_current
"""

DELETE_WORKED_AT = """
MATCH (u:User {id: $user_id})-[r:WORKED_AT]->(c:Company {name: $company_name})
WHERE r.start_year = $start_year
DELETE r
RETURN count(r) AS deleted
"""
