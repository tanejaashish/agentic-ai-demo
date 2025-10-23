"""
Knowledge Graph Service
Incident relationship modeling and pattern discovery
Note: This is a graph-based implementation without Neo4j dependency for ease of deployment
"""

import asyncio
import json
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict, deque
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class GraphNode:
    """Node in the knowledge graph"""
    node_id: str
    node_type: str  # incident, system, error, solution, team
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class GraphEdge:
    """Edge/relationship in the knowledge graph"""
    from_node: str
    to_node: str
    relationship_type: str  # affects, causes, solves, similar_to, assigned_to
    properties: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)


class KnowledgeGraphService:
    """
    In-memory knowledge graph for incident relationships
    Models relationships between incidents, systems, errors, and solutions
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}

        # Graph storage
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []

        # Adjacency lists for efficient traversal
        self.outgoing_edges: Dict[str, List[GraphEdge]] = defaultdict(list)
        self.incoming_edges: Dict[str, List[GraphEdge]] = defaultdict(list)

        # Indexes for fast lookups
        self.nodes_by_type: Dict[str, Set[str]] = defaultdict(set)

        # Statistics
        self.stats = {
            "total_nodes": 0,
            "total_edges": 0,
            "nodes_by_type": {},
            "edges_by_type": {}
        }

        logger.info("Knowledge Graph Service initialized")

    async def add_node(
        self,
        node_id: str,
        node_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> GraphNode:
        """Add a node to the graph"""
        if node_id in self.nodes:
            logger.debug(f"Node {node_id} already exists, updating properties")
            self.nodes[node_id].properties.update(properties or {})
            return self.nodes[node_id]

        node = GraphNode(
            node_id=node_id,
            node_type=node_type,
            properties=properties or {}
        )

        self.nodes[node_id] = node
        self.nodes_by_type[node_type].add(node_id)

        self.stats["total_nodes"] += 1
        self.stats["nodes_by_type"][node_type] = len(self.nodes_by_type[node_type])

        logger.debug(f"Node added: {node_id} (type: {node_type})")
        return node

    async def add_edge(
        self,
        from_node: str,
        to_node: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None,
        weight: float = 1.0
    ) -> GraphEdge:
        """Add an edge to the graph"""
        # Ensure nodes exist
        if from_node not in self.nodes or to_node not in self.nodes:
            logger.warning(
                f"Cannot add edge: node {from_node} or {to_node} does not exist"
            )
            return None

        edge = GraphEdge(
            from_node=from_node,
            to_node=to_node,
            relationship_type=relationship_type,
            properties=properties or {},
            weight=weight
        )

        self.edges.append(edge)
        self.outgoing_edges[from_node].append(edge)
        self.incoming_edges[to_node].append(edge)

        self.stats["total_edges"] += 1
        if relationship_type not in self.stats["edges_by_type"]:
            self.stats["edges_by_type"][relationship_type] = 0
        self.stats["edges_by_type"][relationship_type] += 1

        logger.debug(
            f"Edge added: {from_node} --[{relationship_type}]--> {to_node}"
        )
        return edge

    async def build_incident_graph(self, incident: Dict[str, Any]) -> str:
        """Build graph representation for an incident"""
        incident_id = incident.get('id', incident.get('incident_id', ''))

        # Add incident node
        await self.add_node(
            node_id=f"incident:{incident_id}",
            node_type="incident",
            properties={
                "title": incident.get('title', ''),
                "priority": incident.get('priority', ''),
                "category": incident.get('category', ''),
                "timestamp": incident.get('timestamp', datetime.now().isoformat())
            }
        )

        # Add affected systems as nodes
        affected_systems = incident.get('affected_systems', [])
        for system in affected_systems:
            system_id = f"system:{system}"
            await self.add_node(
                node_id=system_id,
                node_type="system",
                properties={"name": system}
            )

            # Create AFFECTS relationship
            await self.add_edge(
                from_node=f"incident:{incident_id}",
                to_node=system_id,
                relationship_type="affects"
            )

        # Add error pattern node if available
        error_message = incident.get('error_message', '')
        if error_message:
            # Extract error type
            error_type = self._extract_error_type(error_message)
            error_id = f"error:{error_type}"

            await self.add_node(
                node_id=error_id,
                node_type="error",
                properties={
                    "error_type": error_type,
                    "message": error_message[:200]
                }
            )

            # Create CAUSED_BY relationship
            await self.add_edge(
                from_node=f"incident:{incident_id}",
                to_node=error_id,
                relationship_type="caused_by"
            )

        logger.info(f"Incident graph built for {incident_id}")
        return f"incident:{incident_id}"

    async def add_solution_relationship(
        self,
        incident_id: str,
        solution_id: str,
        effectiveness: float
    ):
        """Add relationship between incident and solution"""
        incident_node = f"incident:{incident_id}"
        solution_node = f"solution:{solution_id}"

        # Add solution node if not exists
        if solution_node not in self.nodes:
            await self.add_node(
                node_id=solution_node,
                node_type="solution",
                properties={"solution_id": solution_id}
            )

        # Create SOLVED_BY relationship with effectiveness weight
        await self.add_edge(
            from_node=incident_node,
            to_node=solution_node,
            relationship_type="solved_by",
            weight=effectiveness,
            properties={"effectiveness": effectiveness}
        )

    async def find_related_incidents(
        self,
        incident_id: str,
        max_depth: int = 3,
        min_similarity: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Find related incidents using graph traversal

        Uses breadth-first search to find incidents connected through:
        - Same affected systems
        - Similar error patterns
        - Same solutions
        """
        incident_node = f"incident:{incident_id}"

        if incident_node not in self.nodes:
            return []

        # BFS to find related incidents
        related = []
        visited = {incident_node}
        queue = deque([(incident_node, 0, 1.0)])  # (node, depth, similarity)

        while queue:
            current_node, depth, similarity = queue.popleft()

            if depth >= max_depth:
                continue

            # Get outgoing edges
            for edge in self.outgoing_edges.get(current_node, []):
                next_node = edge.to_node

                if next_node not in visited:
                    visited.add(next_node)

                    # Calculate similarity decay
                    edge_similarity = similarity * edge.weight * 0.8  # 20% decay per hop

                    # If it's an incident node, add to results
                    if next_node.startswith("incident:") and next_node != incident_node:
                        if edge_similarity >= min_similarity:
                            related.append({
                                "incident_id": next_node.replace("incident:", ""),
                                "similarity": edge_similarity,
                                "path_length": depth + 1,
                                "relationship": edge.relationship_type,
                                "properties": self.nodes[next_node].properties
                            })

                    queue.append((next_node, depth + 1, edge_similarity))

                # Also check incoming edges
                for edge in self.incoming_edges.get(next_node, []):
                    prev_node = edge.from_node
                    if prev_node not in visited:
                        visited.add(prev_node)
                        edge_similarity = similarity * edge.weight * 0.8

                        if prev_node.startswith("incident:") and prev_node != incident_node:
                            if edge_similarity >= min_similarity:
                                related.append({
                                    "incident_id": prev_node.replace("incident:", ""),
                                    "similarity": edge_similarity,
                                    "path_length": depth + 1,
                                    "relationship": edge.relationship_type,
                                    "properties": self.nodes[prev_node].properties
                                })

                        queue.append((prev_node, depth + 1, edge_similarity))

        # Sort by similarity
        related.sort(key=lambda x: x['similarity'], reverse=True)

        logger.info(f"Found {len(related)} related incidents for {incident_id}")
        return related[:10]  # Return top 10

    async def find_common_solutions(
        self,
        incident_id: str,
        min_effectiveness: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Find solutions that worked for similar incidents"""
        # First find related incidents
        related_incidents = await self.find_related_incidents(incident_id)

        solution_scores = defaultdict(list)

        # Collect solutions from related incidents
        for related in related_incidents:
            related_node = f"incident:{related['incident_id']}"

            # Get solutions for this incident
            for edge in self.outgoing_edges.get(related_node, []):
                if edge.relationship_type == "solved_by":
                    effectiveness = edge.properties.get('effectiveness', 0.5)

                    if effectiveness >= min_effectiveness:
                        solution_id = edge.to_node.replace("solution:", "")
                        solution_scores[solution_id].append({
                            "effectiveness": effectiveness,
                            "similarity": related['similarity'],
                            "incident_id": related['incident_id']
                        })

        # Aggregate and rank solutions
        ranked_solutions = []
        for solution_id, scores in solution_scores.items():
            avg_effectiveness = sum(s['effectiveness'] for s in scores) / len(scores)
            weighted_score = sum(
                s['effectiveness'] * s['similarity']
                for s in scores
            ) / len(scores)

            ranked_solutions.append({
                "solution_id": solution_id,
                "score": weighted_score,
                "average_effectiveness": avg_effectiveness,
                "occurrences": len(scores),
                "source_incidents": [s['incident_id'] for s in scores]
            })

        ranked_solutions.sort(key=lambda x: x['score'], reverse=True)

        logger.info(f"Found {len(ranked_solutions)} common solutions")
        return ranked_solutions

    async def identify_system_patterns(self) -> List[Dict[str, Any]]:
        """Identify system-level patterns and dependencies"""
        patterns = []

        # Find systems with frequent incidents
        system_incident_counts = defaultdict(int)

        for node_id in self.nodes_by_type.get('system', set()):
            incident_count = len(self.incoming_edges.get(node_id, []))
            if incident_count > 0:
                system_name = self.nodes[node_id].properties.get('name', node_id)
                system_incident_counts[system_name] = incident_count

        # Rank systems by incident frequency
        for system, count in sorted(
            system_incident_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]:
            patterns.append({
                "pattern_type": "high_incident_system",
                "system": system,
                "incident_count": count,
                "severity": "high" if count > 10 else "medium"
            })

        # Find co-occurring system failures
        # (systems that appear together in incidents)
        system_pairs = defaultdict(int)

        for node_id in self.nodes_by_type.get('incident', set()):
            affected_systems = []
            for edge in self.outgoing_edges.get(node_id, []):
                if edge.relationship_type == "affects":
                    system_name = self.nodes[edge.to_node].properties.get('name', '')
                    if system_name:
                        affected_systems.append(system_name)

            # Count pairs
            for i, sys1 in enumerate(affected_systems):
                for sys2 in affected_systems[i+1:]:
                    pair = tuple(sorted([sys1, sys2]))
                    system_pairs[pair] += 1

        # Add co-occurrence patterns
        for (sys1, sys2), count in sorted(
            system_pairs.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]:
            if count >= 3:  # At least 3 co-occurrences
                patterns.append({
                    "pattern_type": "co_occurring_failures",
                    "systems": [sys1, sys2],
                    "co_occurrence_count": count,
                    "severity": "high"
                })

        logger.info(f"Identified {len(patterns)} system patterns")
        return patterns

    def _extract_error_type(self, error_message: str) -> str:
        """Extract error type from error message"""
        error_message = error_message.lower()

        # Common error patterns
        if "timeout" in error_message or "timed out" in error_message:
            return "timeout"
        elif "connection" in error_message:
            return "connection_error"
        elif "memory" in error_message or "oom" in error_message:
            return "memory_error"
        elif "null" in error_message or "nullptr" in error_message:
            return "null_pointer"
        elif "permission" in error_message or "access denied" in error_message:
            return "permission_error"
        elif "not found" in error_message or "404" in error_message:
            return "not_found"
        elif "500" in error_message or "internal" in error_message:
            return "internal_server_error"
        else:
            return "general_error"

    async def get_graph_stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics"""
        return {
            "total_nodes": self.stats["total_nodes"],
            "total_edges": self.stats["total_edges"],
            "nodes_by_type": dict(self.stats["nodes_by_type"]),
            "edges_by_type": dict(self.stats["edges_by_type"]),
            "graph_density": (
                self.stats["total_edges"] /
                max(self.stats["total_nodes"] * (self.stats["total_nodes"] - 1), 1)
            ),
            "average_degree": (
                self.stats["total_edges"] * 2 / max(self.stats["total_nodes"], 1)
            )
        }

    async def export_graph(self, format: str = "json") -> str:
        """Export graph in specified format"""
        if format == "json":
            export_data = {
                "nodes": [
                    {
                        "id": node.node_id,
                        "type": node.node_type,
                        "properties": node.properties,
                        "created_at": node.created_at.isoformat()
                    }
                    for node in self.nodes.values()
                ],
                "edges": [
                    {
                        "from": edge.from_node,
                        "to": edge.to_node,
                        "type": edge.relationship_type,
                        "weight": edge.weight,
                        "properties": edge.properties,
                        "created_at": edge.created_at.isoformat()
                    }
                    for edge in self.edges
                ],
                "stats": await self.get_graph_stats()
            }

            return json.dumps(export_data, indent=2)

        else:
            raise ValueError(f"Unsupported export format: {format}")


# Global knowledge graph instance
_global_graph: Optional[KnowledgeGraphService] = None


def get_knowledge_graph() -> KnowledgeGraphService:
    """Get or create global knowledge graph"""
    global _global_graph
    if _global_graph is None:
        _global_graph = KnowledgeGraphService()
    return _global_graph
