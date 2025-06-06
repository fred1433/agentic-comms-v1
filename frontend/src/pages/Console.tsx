import React, { useState, useEffect, useRef } from 'react';
import {
  PaperAirplaneIcon,
  PlusIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  AtSymbolIcon,
  ChatBubbleLeftRightIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { apiClient, chatUtils, formatUtils } from '../utils/api';
import { MessageResponse } from '../types';
import toast from 'react-hot-toast';
import classNames from 'classnames';

interface DemoMessage {
  id: string;
  content: string;
  timestamp: Date;
  sender: 'user' | 'agent';
  channel: 'chat' | 'email';
  agentId?: string;
  responseTime?: number;
  confidence?: number;
}

export default function Console() {
  const [messages, setMessages] = useState<DemoMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeChannel, setActiveChannel] = useState<'chat' | 'email'>('chat');
  const [emailSubject, setEmailSubject] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const demoQuestions = [
    "Comment puis-je réinitialiser mon mot de passe ?",
    "Je n'arrive pas à me connecter à mon compte",
    "Quels sont vos tarifs pour l'abonnement premium ?",
    "Comment puis-je annuler ma commande ?",
    "Mon paiement a été refusé, que faire ?",
    "Je souhaite modifier mes informations de profil",
    "Comment contacter le support technique ?",
    "Puis-je obtenir un remboursement ?",
    "Où puis-je télécharger votre application mobile ?",
    "Comment puis-je changer mon adresse email ?"
  ];

  const demoEmails = [
    {
      subject: "Problème de connexion urgent",
      content: "Bonjour, je n'arrive plus à me connecter à mon compte depuis ce matin. Pouvez-vous m'aider rapidement ?"
    },
    {
      subject: "Demande de remboursement",
      content: "Je souhaiterais annuler ma commande #12345 et obtenir un remboursement complet. La livraison était prévue hier mais je n'ai rien reçu."
    },
    {
      subject: "Question sur l'abonnement premium",
      content: "Quels sont les avantages de l'abonnement premium par rapport à la version gratuite ? Y a-t-il une période d'essai ?"
    }
  ];

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const sendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: DemoMessage = {
      id: `user-${Date.now()}`,
      content: inputValue,
      timestamp: new Date(),
      sender: 'user',
      channel: activeChannel
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setInputValue('');

    try {
      let response: MessageResponse;
      
      if (activeChannel === 'chat') {
        response = await chatUtils.sendMessage(inputValue);
      } else {
        response = await chatUtils.sendEmailDemo(
          emailSubject || 'Support Request',
          inputValue
        );
      }

      const agentMessage: DemoMessage = {
        id: response.id,
        content: response.content,
        timestamp: new Date(),
        sender: 'agent',
        channel: activeChannel,
        agentId: response.agent_id,
        responseTime: response.response_time_ms,
        confidence: response.confidence_score
      };

      setMessages(prev => [...prev, agentMessage]);
      
      if (response.escalated) {
        toast('Message escalated to human agent', { icon: '⚠️' });
      }
      
    } catch (error) {
      toast.error('Erreur lors de l\'envoi du message');
    } finally {
      setIsLoading(false);
      setEmailSubject('');
    }
  };

  const sendDemoQuestion = (question: string) => {
    setInputValue(question);
    setActiveChannel('chat');
  };

  const sendDemoEmail = (email: typeof demoEmails[0]) => {
    setActiveChannel('email');
    setEmailSubject(email.subject);
    setInputValue(email.content);
  };

  const clearChat = () => {
    setMessages([]);
    toast.success('Chat effacé');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="px-4 sm:px-6 lg:px-8 h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="mb-6 flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Console Unifiée</h1>
          <p className="text-gray-600">
            Inbox intelligente pour chat et email avec IA
          </p>
        </div>
        
        <div className="flex gap-2">
          <button
            onClick={clearChat}
            className="btn btn-secondary btn-sm"
          >
            Effacer
          </button>
          <div className="flex bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setActiveChannel('chat')}
              className={classNames(
                'px-3 py-1 rounded-md text-sm font-medium transition-colors',
                activeChannel === 'chat'
                  ? 'bg-white text-primary-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              )}
            >
              <ChatBubbleLeftRightIcon className="h-4 w-4 inline mr-1" />
              Chat
            </button>
            <button
              onClick={() => setActiveChannel('email')}
              className={classNames(
                'px-3 py-1 rounded-md text-sm font-medium transition-colors',
                activeChannel === 'email'
                  ? 'bg-white text-primary-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              )}
            >
              <AtSymbolIcon className="h-4 w-4 inline mr-1" />
              Email
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-full">
        {/* Demo Sidebar */}
        <div className="lg:col-span-1 card p-4 h-fit max-h-[600px] overflow-y-auto">
          <h3 className="font-semibold text-gray-900 mb-4">Questions Demo</h3>
          
          <div className="space-y-3 mb-6">
            <h4 className="text-sm font-medium text-gray-700">Chat rapide:</h4>
            {demoQuestions.slice(0, 5).map((question, index) => (
              <button
                key={index}
                onClick={() => sendDemoQuestion(question)}
                className="w-full text-left p-2 text-sm text-gray-600 hover:bg-gray-50 rounded-lg border border-gray-200 hover:border-primary-300 transition-colors"
              >
                {question}
              </button>
            ))}
          </div>

          <div className="space-y-3">
            <h4 className="text-sm font-medium text-gray-700">Emails type:</h4>
            {demoEmails.map((email, index) => (
              <button
                key={index}
                onClick={() => sendDemoEmail(email)}
                className="w-full text-left p-2 text-sm hover:bg-gray-50 rounded-lg border border-gray-200 hover:border-primary-300 transition-colors"
              >
                <div className="font-medium text-gray-900">{email.subject}</div>
                <div className="text-gray-600 text-xs mt-1 truncate">
                  {email.content.substring(0, 60)}...
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Main Chat Area */}
        <div className="lg:col-span-3 flex flex-col h-full">
          {/* Messages */}
          <div className="flex-1 card p-4 overflow-hidden flex flex-col">
            <div className="flex-1 overflow-y-auto space-y-4 mb-4">
              {messages.length === 0 ? (
                <div className="text-center py-12">
                  <ChatBubbleLeftRightIcon className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">
                    Aucune conversation
                  </h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Commencez une conversation ou utilisez les questions demo
                  </p>
                </div>
              ) : (
                messages.map((message) => (
                  <div
                    key={message.id}
                    className={classNames(
                      'flex',
                      message.sender === 'user' ? 'justify-end' : 'justify-start'
                    )}
                  >
                    <div
                      className={classNames(
                        'max-w-xs lg:max-w-md px-4 py-2 rounded-lg',
                        message.sender === 'user'
                          ? 'bg-primary-600 text-white'
                          : 'bg-gray-100 text-gray-900'
                      )}
                    >
                      <p className="text-sm">{message.content}</p>
                      <div className="mt-1 flex items-center justify-between text-xs opacity-70">
                        <span>
                          {message.timestamp.toLocaleTimeString()}
                        </span>
                        {message.sender === 'agent' && (
                          <div className="flex items-center space-x-2">
                            {message.responseTime && (
                              <span className="flex items-center">
                                <ClockIcon className="h-3 w-3 mr-1" />
                                {formatUtils.formatResponseTime(message.responseTime)}
                              </span>
                            )}
                            {message.confidence && (
                              <span className={classNames(
                                'px-1 py-0.5 rounded text-xs',
                                message.confidence > 0.8 
                                  ? 'bg-success-100 text-success-800'
                                  : message.confidence > 0.6
                                  ? 'bg-warning-100 text-warning-800'
                                  : 'bg-danger-100 text-danger-800'
                              )}>
                                {Math.round(message.confidence * 100)}%
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
              
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 px-4 py-2 rounded-lg">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="border-t border-gray-200 pt-4">
              {activeChannel === 'email' && (
                <input
                  type="text"
                  placeholder="Sujet de l'email..."
                  value={emailSubject}
                  onChange={(e) => setEmailSubject(e.target.value)}
                  className="w-full mb-3 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              )}
              
              <div className="flex space-x-2">
                <div className="flex-1 relative">
                  <textarea
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder={activeChannel === 'chat' ? 'Tapez votre message...' : 'Tapez votre email...'}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                    rows={activeChannel === 'email' ? 4 : 2}
                  />
                </div>
                <button
                  onClick={sendMessage}
                  disabled={!inputValue.trim() || isLoading}
                  className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                >
                  <PaperAirplaneIcon className="h-4 w-4" />
                </button>
              </div>
              
              <div className="mt-2 text-xs text-gray-500">
                {activeChannel === 'chat' ? 'Appuyez sur Entrée pour envoyer' : 'Mode email - réponse automatique'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Live Stats */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card p-4 text-center">
          <div className="text-2xl font-bold text-primary-600">
            {messages.filter(m => m.sender === 'agent').length}
          </div>
          <div className="text-sm text-gray-600">Réponses IA</div>
        </div>
        
        <div className="card p-4 text-center">
          <div className="text-2xl font-bold text-success-600">
            {messages.filter(m => m.sender === 'agent' && m.responseTime && m.responseTime < 5000).length}
          </div>
          <div className="text-sm text-gray-600">Réponses &lt; 5s</div>
        </div>
        
        <div className="card p-4 text-center">
          <div className="text-2xl font-bold text-warning-600">
            {messages.filter(m => m.sender === 'agent' && m.confidence && m.confidence > 0.8).length}
          </div>
          <div className="text-sm text-gray-600">Confiance &gt; 80%</div>
        </div>
      </div>
    </div>
  );
} 