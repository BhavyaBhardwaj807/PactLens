import React, { useState } from 'react';
import { Send, Loader } from 'lucide-react';

export default function QuestionBox({ onSubmit, isLoading = false }) {
  const [question, setQuestion] = useState('');

  const suggestedQuestions = [
    'Do any clauses contradict each other?',
    'What could cause problems after termination?',
    'Which document overrides others?',
    'What are my confidentiality obligations?',
    'What happens to my work after I leave?',
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    if (question.trim()) {
      onSubmit(question);
      setQuestion('');
    }
  };

  const handleSuggestedClick = (q) => {
    setQuestion(q);
  };

  return (
    <div className="bg-dark-card border border-dark-border rounded-xl p-6 space-y-4">
      <div>
        <h3 className="font-semibold text-gray-100 mb-2">Ask About Your Contracts</h3>
        <p className="text-sm text-gray-400">
          Get insights, detect contradictions, or understand specific clauses
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="relative">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question about your contracts..."
            disabled={isLoading}
            className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-3 text-gray-100 placeholder-gray-500 focus:outline-none focus:border-accent-cyan disabled:opacity-50 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={isLoading || !question.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-gradient-accent rounded-lg text-white hover:shadow-accent disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {isLoading ? <Loader size={20} className="animate-spin" /> : <Send size={20} />}
          </button>
        </div>

        {/* Suggested Questions */}
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-wider text-gray-500 font-semibold">
            Suggested Questions
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {suggestedQuestions.map((q, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSuggestedClick(q)}
                className="text-left text-sm bg-dark-bg border border-dark-border rounded-lg px-3 py-2 text-gray-300 hover:border-accent-cyan hover:text-accent-cyan transition-all"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      </form>
    </div>
  );
}
