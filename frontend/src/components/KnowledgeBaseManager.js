/**
 * Knowledge Base Manager Component
 * Full CRUD operations for knowledge articles with search and filtering
 */

import React, { useState, useEffect } from 'react';
import { 
  FaBook, 
  FaPlus, 
  FaEdit, 
  FaTrash, 
  FaSearch,
  FaSync,
  FaDownload,
  FaUpload,
  FaFilter
} from 'react-icons/fa';
import { knowledgeService } from '../services/api';
import toast from 'react-hot-toast';
import './KnowledgeBaseManager.css';

const KnowledgeBaseManager = () => {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingArticle, setEditingArticle] = useState(null);
  const [stats, setStats] = useState(null);

  const [formData, setFormData] = useState({
    title: '',
    content: '',
    category: 'General',
    tags: '',
    solution_steps: '',
    related_incidents: ''
  });

  useEffect(() => {
    loadArticles();
    loadStats();
  }, [selectedCategory]);

  const loadArticles = async () => {
    try {
      setLoading(true);
      const filters = selectedCategory !== 'all' ? { category: selectedCategory } : {};
      const data = await knowledgeService.listArticles(filters);
      setArticles(data.articles || []);
    } catch (error) {
      console.error('Error loading articles:', error);
      // Set demo data on error
      setDemoArticles();
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const data = await knowledgeService.getStats();
      setStats(data);
    } catch (error) {
      console.error('Error loading stats:', error);
      setStats({
        total_articles: 45,
        by_category: { Database: 15, Network: 12, Application: 18 },
        most_accessed: 'Connection Pool Management'
      });
    }
  };

  const setDemoArticles = () => {
    setArticles([
      {
        id: 1,
        title: 'Database Connection Pool Management',
        category: 'Database',
        tags: ['connection', 'pool', 'performance'],
        created_at: '2025-10-20T10:00:00Z',
        updated_at: '2025-10-24T15:30:00Z',
        views: 342,
        helpful_count: 28
      },
      {
        id: 2,
        title: 'Resolving 502 Bad Gateway Errors',
        category: 'Network',
        tags: ['502', 'gateway', 'proxy'],
        created_at: '2025-10-18T14:00:00Z',
        updated_at: '2025-10-23T09:15:00Z',
        views: 256,
        helpful_count: 19
      },
      {
        id: 3,
        title: 'Memory Leak Detection and Prevention',
        category: 'Application',
        tags: ['memory', 'leak', 'debugging'],
        created_at: '2025-10-15T08:30:00Z',
        updated_at: '2025-10-22T16:45:00Z',
        views: 189,
        helpful_count: 15
      }
    ]);
  };

  const handleCreateArticle = async (e) => {
    e.preventDefault();
    try {
      const articleData = {
        ...formData,
        tags: formData.tags.split(',').map(t => t.trim()),
        solution_steps: formData.solution_steps.split('\n').filter(s => s.trim()),
        related_incidents: formData.related_incidents.split(',').map(i => i.trim())
      };

      await knowledgeService.createArticle(articleData);
      toast.success('Article created successfully!');
      setShowCreateModal(false);
      resetForm();
      loadArticles();
    } catch (error) {
      toast.error('Failed to create article: ' + error.message);
    }
  };

  const handleUpdateArticle = async (e) => {
    e.preventDefault();
    try {
      await knowledgeService.updateArticle(editingArticle.id, formData);
      toast.success('Article updated successfully!');
      setEditingArticle(null);
      resetForm();
      loadArticles();
    } catch (error) {
      toast.error('Failed to update article: ' + error.message);
    }
  };

  const handleDeleteArticle = async (articleId) => {
    if (!window.confirm('Are you sure you want to delete this article?')) return;
    
    try {
      await knowledgeService.deleteArticle(articleId);
      toast.success('Article deleted successfully!');
      loadArticles();
    } catch (error) {
      toast.error('Failed to delete article: ' + error.message);
    }
  };

  const handleSync = async () => {
    try {
      await knowledgeService.sync();
      toast.success('Knowledge base synced with vector store!');
      loadArticles();
    } catch (error) {
      toast.error('Sync failed: ' + error.message);
    }
  };

  const resetForm = () => {
    setFormData({
      title: '',
      content: '',
      category: 'General',
      tags: '',
      solution_steps: '',
      related_incidents: ''
    });
  };

  const openEditModal = (article) => {
    setEditingArticle(article);
    setFormData({
      title: article.title,
      content: article.content || '',
      category: article.category,
      tags: article.tags?.join(', ') || '',
      solution_steps: article.solution_steps?.join('\n') || '',
      related_incidents: article.related_incidents?.join(', ') || ''
    });
  };

  const filteredArticles = articles.filter(article =>
    article.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    article.category.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="knowledge-base-manager">
      {/* Header */}
      <div className="kb-header">
        <div>
          <h1><FaBook /> Knowledge Base Manager</h1>
          <p>Manage articles, solutions, and best practices</p>
        </div>
        <div className="kb-actions">
          <button onClick={() => setShowCreateModal(true)} className="btn-primary">
            <FaPlus /> New Article
          </button>
          <button onClick={handleSync} className="btn-secondary">
            <FaUpload /> Sync Vector Store
          </button>
          <button onClick={loadArticles} className="btn-secondary">
            <FaSync /> Refresh
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="kb-stats">
        <div className="stat-card">
          <h3>Total Articles</h3>
          <div className="stat-value">{stats?.total_articles || articles.length}</div>
        </div>
        <div className="stat-card">
          <h3>Categories</h3>
          <div className="stat-value">{Object.keys(stats?.by_category || {}).length || 3}</div>
        </div>
        <div className="stat-card">
          <h3>Most Accessed</h3>
          <div className="stat-value">{stats?.most_accessed || 'N/A'}</div>
        </div>
        <div className="stat-card">
          <h3>This Month</h3>
          <div className="stat-value">+12</div>
        </div>
      </div>

      {/* Search and Filter */}
      <div className="kb-controls">
        <div className="search-box">
          <FaSearch />
          <input
            type="text"
            placeholder="Search articles..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="filter-group">
          <FaFilter />
          <select value={selectedCategory} onChange={(e) => setSelectedCategory(e.target.value)}>
            <option value="all">All Categories</option>
            <option value="Database">Database</option>
            <option value="Network">Network</option>
            <option value="Application">Application</option>
            <option value="Security">Security</option>
            <option value="General">General</option>
          </select>
        </div>
      </div>

      {/* Articles List */}
      <div className="articles-grid">
        {loading ? (
          <div className="loading-state">Loading articles...</div>
        ) : filteredArticles.length === 0 ? (
          <div className="empty-state">
            <FaBook />
            <p>No articles found</p>
            <button onClick={() => setShowCreateModal(true)} className="btn-primary">
              Create First Article
            </button>
          </div>
        ) : (
          filteredArticles.map(article => (
            <div key={article.id} className="article-card">
              <div className="article-header">
                <h3>{article.title}</h3>
                <div className="article-actions">
                  <button onClick={() => openEditModal(article)} className="btn-icon">
                    <FaEdit />
                  </button>
                  <button onClick={() => handleDeleteArticle(article.id)} className="btn-icon danger">
                    <FaTrash />
                  </button>
                </div>
              </div>
              <div className="article-meta">
                <span className="category-badge">{article.category}</span>
                <span className="views">👁 {article.views || 0} views</span>
                <span className="helpful">👍 {article.helpful_count || 0} helpful</span>
              </div>
              {article.tags && (
                <div className="article-tags">
                  {article.tags.map((tag, idx) => (
                    <span key={idx} className="tag">{tag}</span>
                  ))}
                </div>
              )}
              <div className="article-footer">
                <span>Updated: {new Date(article.updated_at).toLocaleDateString()}</span>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Create/Edit Modal */}
      {(showCreateModal || editingArticle) && (
        <div className="modal-overlay" onClick={() => {
          setShowCreateModal(false);
          setEditingArticle(null);
          resetForm();
        }}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editingArticle ? 'Edit Article' : 'Create New Article'}</h2>
              <button onClick={() => {
                setShowCreateModal(false);
                setEditingArticle(null);
                resetForm();
              }}>×</button>
            </div>
            <form onSubmit={editingArticle ? handleUpdateArticle : handleCreateArticle}>
              <div className="form-group">
                <label>Title *</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({...formData, title: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Category *</label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({...formData, category: e.target.value})}
                  required
                >
                  <option value="General">General</option>
                  <option value="Database">Database</option>
                  <option value="Network">Network</option>
                  <option value="Application">Application</option>
                  <option value="Security">Security</option>
                </select>
              </div>
              <div className="form-group">
                <label>Content *</label>
                <textarea
                  value={formData.content}
                  onChange={(e) => setFormData({...formData, content: e.target.value})}
                  rows="8"
                  required
                />
              </div>
              <div className="form-group">
                <label>Solution Steps (one per line)</label>
                <textarea
                  value={formData.solution_steps}
                  onChange={(e) => setFormData({...formData, solution_steps: e.target.value})}
                  rows="4"
                  placeholder="Step 1: Check configuration&#10;Step 2: Restart service&#10;Step 3: Verify logs"
                />
              </div>
              <div className="form-group">
                <label>Tags (comma-separated)</label>
                <input
                  type="text"
                  value={formData.tags}
                  onChange={(e) => setFormData({...formData, tags: e.target.value})}
                  placeholder="database, connection, performance"
                />
              </div>
              <div className="form-group">
                <label>Related Incidents (comma-separated IDs)</label>
                <input
                  type="text"
                  value={formData.related_incidents}
                  onChange={(e) => setFormData({...formData, related_incidents: e.target.value})}
                  placeholder="INC001, INC002"
                />
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => {
                  setShowCreateModal(false);
                  setEditingArticle(null);
                  resetForm();
                }} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  {editingArticle ? 'Update' : 'Create'} Article
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default KnowledgeBaseManager;
