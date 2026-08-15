export interface Suggestion {
  id: string;
  name: string;
  location?: string | null;
  shared_context: string[];
  overlap_score: number;
}

export interface PathNode {
  id: string;
  name: string;
}

export interface UserSearchItem {
  id: string;
  name: string;
  location?: string | null;
  companies: string[];
  institutions: string[];
}

export interface ConnectionItem {
  id: string;
  name: string;
  location?: string | null;
  context: string;
  since: string | null;
  closeness: string;
}

export type IntroType =
  | "direct_context"
  | "knows_path"
  | "suggested_intro"
  | "unreachable";

export interface IntroSuggestion {
  id: string;
  name: string;
  location?: string | null;
  knows_distance: number;
  shared_node_name: string;
  shared_node_type: string;
  reach_type: "knows" | "context";
  chain_to_target: PathNode[];
}

export interface IntroResponse {
  type: IntroType;
  shared_context: string[];
  chain: PathNode[];
  hops: number;
  via_close_only: boolean;
  suggestions: IntroSuggestion[];
}

export type ConnectionContext = "classmate" | "colleague" | "family" | "friend";
export type Closeness = "close" | "acquaintance";

export interface ConnectRequest {
  context: ConnectionContext;
  since?: string | null;
  closeness: Closeness;
}
