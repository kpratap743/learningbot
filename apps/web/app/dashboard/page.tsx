'use client';

import React, { useCallback, useEffect, useState, useMemo } from 'react';
import ReactFlow, {
  Background,
  Controls,
  Edge,
  Node,
  useNodesState,
  useEdgesState,
  MiniMap,
  Handle,
  Position,
} from 'reactflow';
import 'reactflow/dist/style.css';

const CustomNode = ({ data, id }: any) => {
  return (
    <div className="p-4 border-2 border-gray-200 rounded-lg bg-white shadow-md min-w-[200px] text-center">
      <Handle type="target" position={Position.Top} />
      <div className="font-bold text-lg mb-2 text-black">{data.label}</div>
      <div className="text-sm text-gray-500 mb-2">Mastery: {data.score}%</div>
      <button
        onClick={(e) => {
          e.stopPropagation();
          data.onQuiz(id);
        }}
        className="w-full bg-indigo-500 hover:bg-indigo-600 text-white text-sm py-1 px-3 rounded transition-colors"
      >
        Simulate Quiz
      </button>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};

export default function Dashboard() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newNodeLabel, setNewNodeLabel] = useState('');
  const [loading, setLoading] = useState(false);

  const nodeTypes = useMemo(() => ({ custom: CustomNode }), []);

  const handleSimulateQuiz = useCallback(async (nodeId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/nodes/${nodeId}/quiz`, {
        method: 'POST',
      });
      if (response.ok) {
        fetchNodes(); // Refresh to update score
      }
    } catch (error) {
      console.error('Failed to simulate quiz', error);
    }
  }, []);

  const fetchNodes = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/nodes');
      if (response.ok) {
        const data = await response.json();
        const flowNodes: Node[] = data.map((n: any, index: number) => ({
          id: n.id.toString(),
          type: 'custom',
          position: { x: index * 250 + 50, y: 100 },
          data: {
            label: n.label,
            score: n.mastery_score,
            onQuiz: handleSimulateQuiz
          },
        }));
        setNodes(flowNodes);
      }
    } catch (error) {
      console.error('Failed to fetch nodes', error);
    }
  }, [handleSimulateQuiz, setNodes]);

  useEffect(() => {
    fetchNodes();
  }, [fetchNodes]);

  const handleCreateNode = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/nodes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          label: newNodeLabel,
          summary: 'Created via dashboard',
          source_url: 'http://example.com',
          status: 'draft',
          mastery_score: 0.0,
        }),
      });

      if (response.ok) {
        setNewNodeLabel('');
        setIsModalOpen(false);
        fetchNodes();
      }
    } catch (error) {
      console.error('Failed to create node', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-screen w-screen flex flex-col bg-gray-50">
      <div className="bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center shadow-sm z-10">
        <h1 className="text-2xl font-bold text-gray-800">Knowledge Dashboard</h1>
        <button
          onClick={() => setIsModalOpen(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 font-medium transition-colors"
        >
          Create Node
        </button>
      </div>

      <div className="flex-1 w-full h-full">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          fitView
        >
          <Background color="#f1f5f9" gap={16} />
          <Controls />
          <MiniMap />
        </ReactFlow>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 backdrop-blur-sm">
          <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-md">
            <h2 className="text-2xl font-bold mb-6 text-gray-800">Create Knowledge Node</h2>
            <form onSubmit={handleCreateNode}>
              <div className="mb-6">
                <label className="block mb-2 text-sm font-medium text-gray-700">Label</label>
                <input
                  type="text"
                  value={newNodeLabel}
                  onChange={(e) => setNewNodeLabel(e.target.value)}
                  className="w-full border border-gray-300 p-3 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                  placeholder="Enter node label"
                  required
                />
              </div>
              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 font-medium transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium disabled:opacity-50 transition-colors"
                >
                  {loading ? 'Creating...' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
