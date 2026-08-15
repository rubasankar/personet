# All Cypher strings for the auth module.
# No Cypher should appear in router.py or schemas.py.
# All queries use $paramName syntax - never string concatenation of user input.

CREATE_USER = """
CREATE (u:User {
    id:            $id,
    name:          $name,
    email:         toLower($email),
    password_hash: $password_hash,
    created_at:    datetime()
})
RETURN u
"""

GET_USER_BY_EMAIL = """
MATCH (u:User {email: toLower($email)})
RETURN u
"""

GET_USER_BY_ID = """
MATCH (u:User {id: $id})
RETURN u
"""
