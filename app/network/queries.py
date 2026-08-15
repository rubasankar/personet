"""
All Cypher strings for the network module.

Every query is fully parameterised - no user input is ever concatenated into
query text. All parameters use the $paramName syntax required by the neo4j driver.
"""

# ---------------------------------------------------------------------------
# CREATE_KNOWS_PAIR
# ---------------------------------------------------------------------------
# Creates bidirectional KNOWS relationships between two users (MERGE so it's
# idempotent). The self-connect guard lives in the router.
#
# Parameters: $user_id, $target_id, $context, $since, $closeness
# ---------------------------------------------------------------------------

CREATE_KNOWS_PAIR = """
MATCH (a:User {id: $user_id}), (b:User {id: $target_id})
MERGE (a)-[:KNOWS {context: $context, since: $since, closeness: $closeness}]->(b)
MERGE (b)-[:KNOWS {context: $context, since: $since, closeness: $closeness}]->(a)
"""

# ---------------------------------------------------------------------------
# SEARCH_USERS
# ---------------------------------------------------------------------------
# Full-text people search. Name match is case-insensitive partial (CONTAINS).
# All extra filters are optional - pass null to skip each one:
#   $location     (string | null) - filters on u.location CONTAINS value
#   $company      (string | null) - must have a WORKED_AT edge to a Company
#                                   whose name CONTAINS value
#   $institution  (string | null) - must have a STUDIED_AT edge to an Institution
#                                   whose name CONTAINS value
# Excludes the requesting user. Returns up to $limit results ordered by name.
#
# Parameters: $my_id, $name, $location, $company, $institution, $limit
# Returns: id, name, location, companies (list), institutions (list)
# ---------------------------------------------------------------------------

SEARCH_USERS = """
MATCH (u:User)
WHERE u.id <> $my_id
  AND toLower(u.name) CONTAINS toLower($name)
  AND ($location IS NULL OR (u.location IS NOT NULL AND toLower(u.location) CONTAINS toLower($location)))
WITH u
OPTIONAL MATCH (u)-[:WORKED_AT]->(c:Company)
WITH u, collect(DISTINCT c.name) AS companies
WHERE $company IS NULL OR any(cn IN companies WHERE toLower(cn) CONTAINS toLower($company))
OPTIONAL MATCH (u)-[:STUDIED_AT]->(i:Institution)
WITH u, companies, collect(DISTINCT i.name) AS institutions
WHERE $institution IS NULL OR any(iname IN institutions WHERE toLower(iname) CONTAINS toLower($institution))
RETURN u.id AS id, u.name AS name, u.location AS location,
       companies, institutions
ORDER BY u.name ASC
LIMIT $limit
"""

# ---------------------------------------------------------------------------
# FIND_USER_BY_ID
# ---------------------------------------------------------------------------
# Simple existence check - used before connect / path to confirm the target
# exists and return their display name.
#
# Parameters: $id
# Returns: id, name
# ---------------------------------------------------------------------------

FIND_USER_BY_ID = """
MATCH (u:User {id: $id})
RETURN u.id AS id, u.name AS name
"""

# ---------------------------------------------------------------------------
# GET_SUGGESTIONS
# ---------------------------------------------------------------------------
# Returns up to 10 candidate Users who share at least one Institution or
# Company with the current user but are not yet connected via KNOWS.
# Ordered by overlap_score DESC, excluding the current user.
#
# Parameters: $my_id
# Returns: id, name, location, shared_context (list of names), overlap_score
# ---------------------------------------------------------------------------

GET_SUGGESTIONS = """
MATCH (me:User {id: $my_id})-[:STUDIED_AT|WORKED_AT]->(shared)<-[:STUDIED_AT|WORKED_AT]-(other:User)
WHERE other.id <> $my_id
WITH me, other,
     collect(DISTINCT shared.name) AS shared_context,
     count(DISTINCT shared)        AS overlap_score
WHERE COUNT { (me)-[:KNOWS]-(other) } = 0
RETURN other.id       AS id,
       other.name     AS name,
       other.location AS location,
       shared_context,
       overlap_score
ORDER BY overlap_score DESC
LIMIT 10
"""

# ---------------------------------------------------------------------------
# GET_CONNECTIONS
# ---------------------------------------------------------------------------
# Returns all users directly connected to the requesting user via KNOWS,
# along with the relationship attributes.
# Ordered by name ASC.
#
# Parameters: $my_id
# Returns: id, name, location, context, since, closeness
# ---------------------------------------------------------------------------

GET_CONNECTIONS = """
MATCH (me:User {id: $my_id})-[r:KNOWS]->(other:User)
RETURN other.id       AS id,
       other.name     AS name,
       other.location AS location,
       r.context      AS context,
       r.since        AS since,
       r.closeness    AS closeness
ORDER BY other.name ASC
"""

# ---------------------------------------------------------------------------
# REMOVE_KNOWS_PAIR
# ---------------------------------------------------------------------------
# Deletes both directions of the KNOWS relationship between two users.
#
# Parameters: $my_id, $target_id
# Returns: deleted (count of relationships removed)
# ---------------------------------------------------------------------------

REMOVE_KNOWS_PAIR = """
MATCH (a:User {id: $my_id})-[r:KNOWS]-(b:User {id: $target_id})
DELETE r
RETURN count(r) AS deleted
"""
# ---------------------------------------------------------------------------
# UPDATE_KNOWS_PAIR
# ---------------------------------------------------------------------------
# Updates attributes on both directions of an existing KNOWS relationship.
# Uses COALESCE so omitted fields (passed as null) keep their current value.
#
# Parameters: $my_id, $target_id, $context, $since, $closeness
# Returns: context, since, closeness (updated values), or empty if not found
# ---------------------------------------------------------------------------

UPDATE_KNOWS_PAIR = """
MATCH (a:User {id: $my_id})-[r:KNOWS]->(b:User {id: $target_id})
SET r.context   = COALESCE($context,   r.context),
    r.since     = COALESCE($since,     r.since),
    r.closeness = COALESCE($closeness, r.closeness)
WITH r
MATCH (b)-[r2:KNOWS]->(a)
SET r2.context   = r.context,
    r2.since     = r.since,
    r2.closeness = r.closeness
RETURN r.context AS context, r.since AS since, r.closeness AS closeness
"""

# ---------------------------------------------------------------------------
# FIND_SHORTEST_PATH
# ---------------------------------------------------------------------------
# Finds the shortest KNOWS path (≤ 7 hops, undirected) between two users.
# Used as fallback when no close-only path exists.
#
# Parameters: $my_id, $target_id
# Returns: chain (list of {id, name} maps), hops (int)
# ---------------------------------------------------------------------------

FIND_SHORTEST_PATH = """
MATCH path = shortestPath((me:User {id: $my_id})-[:KNOWS*..7]-(target:User {id: $target_id}))
RETURN [n IN nodes(path) | {id: n.id, name: n.name}] AS chain, length(path) AS hops
"""

# ---------------------------------------------------------------------------
# FIND_CLOSE_PATH
# ---------------------------------------------------------------------------
# Finds the shortest path where EVERY hop has closeness = 'close'.
# Returns empty if no such all-close path exists within 7 hops.
# The router falls back to FIND_SHORTEST_PATH when this returns nothing.
#
# Parameters: $my_id, $target_id
# Returns: chain (list of {id, name} maps), hops (int)
# ---------------------------------------------------------------------------

FIND_CLOSE_PATH = """
MATCH path = shortestPath((me:User {id: $my_id})-[:KNOWS*..7]-(target:User {id: $target_id}))
WHERE all(r IN relationships(path) WHERE r.closeness = 'close')
RETURN [n IN nodes(path) | {id: n.id, name: n.name}] AS chain, length(path) AS hops
"""

# ---------------------------------------------------------------------------
# FIND_SHARED_CONTEXT
# ---------------------------------------------------------------------------
# Returns all companies and institutions that BOTH the requesting user and
# the target user have in common (shared WORKED_AT or STUDIED_AT edges).
# Used as the first stage of the intro finder.
#
# Parameters: $my_id, $target_id
# Returns: name (of the shared node), type ("Company" or "Institution")
# ---------------------------------------------------------------------------

FIND_SHARED_CONTEXT = """
MATCH (me:User {id: $my_id})-[:WORKED_AT|STUDIED_AT]->(shared)<-[:WORKED_AT|STUDIED_AT]-(target:User {id: $target_id})
RETURN shared.name AS name, labels(shared)[0] AS type
"""

# ---------------------------------------------------------------------------
# FIND_INTRO_VIA_KNOWS
# ---------------------------------------------------------------------------
# Bridge path for users who already have KNOWS connections.
# Finds people you KNOW (within 3 hops) who share a company/institution
# with the target - they can make a warm introduction.
#
# Returns the full KNOWS chain from the bridge to the target so the frontend
# can render "Alice -> Charlie -> Bob" rather than just a hop count.
#
# Parameters: $my_id, $target_id
# Returns: intro_id, intro_name, intro_location, shared_node_name,
#          shared_node_type, knows_distance, reach_type, chain_to_target
# ---------------------------------------------------------------------------

FIND_INTRO_VIA_KNOWS = """
MATCH (target:User {id: $target_id})-[:WORKED_AT|STUDIED_AT]->(shared_node)
MATCH (shared_node)<-[:WORKED_AT|STUDIED_AT]-(bridge:User)
WHERE bridge.id <> $my_id AND bridge.id <> $target_id
MATCH my_path = shortestPath((me:User {id: $my_id})-[:KNOWS*..3]-(bridge))
WITH bridge, shared_node, length(my_path) AS knows_distance
MATCH target_path = shortestPath((bridge)-[:KNOWS*..5]-(target:User {id: $target_id}))
WITH bridge, shared_node, knows_distance,
     [n IN nodes(target_path) | {id: n.id, name: n.name}] AS chain_to_target,
     length(target_path) AS target_hops
ORDER BY knows_distance ASC, target_hops ASC
LIMIT 3
RETURN bridge.id              AS intro_id,
       bridge.name            AS intro_name,
       bridge.location        AS intro_location,
       shared_node.name       AS shared_node_name,
       labels(shared_node)[0] AS shared_node_type,
       knows_distance,
       'knows'                AS reach_type,
       chain_to_target
"""

# ---------------------------------------------------------------------------
# FIND_INTRO_VIA_MY_CONTEXT
# ---------------------------------------------------------------------------
# Bridge path for users with NO KNOWS connections (or when FIND_INTRO_VIA_KNOWS
# returns nothing). Finds people who share a company/institution with YOU
# who also have a KNOWS path to the target (within 5 hops).
#
# Scenario: You work at Acme -> Alice works at Acme -> Alice KNOWS Bob
# Returns the full KNOWS chain from the bridge to the target so the frontend
# can render "Connect with Alice -> Alice knows Charlie -> Charlie knows Bob".
#
# Parameters: $my_id, $target_id
# Returns: intro_id, intro_name, intro_location, shared_node_name,
#          shared_node_type, knows_distance, reach_type, chain_to_target
# ---------------------------------------------------------------------------

FIND_INTRO_VIA_MY_CONTEXT = """
MATCH (me:User {id: $my_id})-[:WORKED_AT|STUDIED_AT]->(my_node)
MATCH (my_node)<-[:WORKED_AT|STUDIED_AT]-(bridge:User)
WHERE bridge.id <> $my_id AND bridge.id <> $target_id
MATCH path = shortestPath((bridge)-[:KNOWS*..5]-(target:User {id: $target_id}))
WITH bridge, my_node, length(path) AS target_distance,
     [n IN nodes(path) | {id: n.id, name: n.name}] AS chain_to_target
ORDER BY target_distance ASC
LIMIT 3
RETURN bridge.id            AS intro_id,
       bridge.name          AS intro_name,
       bridge.location      AS intro_location,
       my_node.name         AS shared_node_name,
       labels(my_node)[0]   AS shared_node_type,
       target_distance      AS knows_distance,
       'context'            AS reach_type,
       chain_to_target
"""
