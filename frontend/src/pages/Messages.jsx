import React, { useEffect, useState, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card } from '../components/ui/card';
import { Avatar, AvatarFallback } from '../components/ui/avatar';
import { toast } from 'sonner';
import { ArrowLeft, Send, MessageCircle } from 'lucide-react';
import axios from 'axios';

export const Messages = () => {
  const { conversationId } = useParams();
  const { user } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [activeConv, setActiveConv] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const messagesEndRef = useRef(null);
  const navigate = useNavigate();
  const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    if (conversationId && conversations.length > 0) {
      const conv = conversations.find(c => c.id === conversationId);
      if (conv) {
        setActiveConv(conv);
        loadMessages(conversationId);
      }
    }
  }, [conversationId, conversations]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadConversations = async () => {
    try {
      const { data } = await axios.get(`${API}/conversations`, { withCredentials: true });
      setConversations(data.conversations || []);
    } catch (error) {
      toast.error('Failed to load conversations');
    } finally {
      setIsLoading(false);
    }
  };

  const loadMessages = async (convId) => {
    try {
      const { data } = await axios.get(`${API}/conversations/${convId}/messages`, { withCredentials: true });
      setMessages(data.messages || []);
    } catch (error) {
      toast.error('Failed to load messages');
    }
  };

  const openConversation = (conv) => {
    setActiveConv(conv);
    navigate(`/messages/${conv.id}`);
    loadMessages(conv.id);
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || !activeConv) return;
    
    try {
      const { data } = await axios.post(
        `${API}/conversations/${activeConv.id}/messages`,
        { content: newMessage },
        { withCredentials: true }
      );
      setMessages([...messages, data]);
      setNewMessage('');
      loadConversations();
    } catch (error) {
      toast.error('Failed to send message');
    }
  };

  return (
    <div className="min-h-screen bg-[#F3F4F6]">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center gap-4">
          <Button
            onClick={() => navigate('/dashboard')}
            variant="ghost"
            className="rounded-full"
            data-testid="back-button"
          >
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <h1 className="text-2xl font-bold tracking-tight text-[#111827]">Messages</h1>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-200px)]">
          {/* Conversation List */}
          <Card className="bg-white rounded-3xl shadow-sm border border-gray-100 p-4 overflow-y-auto lg:col-span-1" data-testid="conversations-list">
            <h2 className="text-lg font-semibold text-[#111827] mb-4 px-2">Conversations</h2>
            {isLoading ? (
              <p className="text-sm text-[#4B5563] px-2">Loading...</p>
            ) : conversations.length === 0 ? (
              <div className="text-center py-8">
                <MessageCircle className="w-12 h-12 text-gray-300 mx-auto mb-2" />
                <p className="text-sm text-[#4B5563]">No conversations yet</p>
                <p className="text-xs text-[#9CA3AF] mt-1">Start collaborating from a match!</p>
              </div>
            ) : (
              <div className="space-y-2">
                {conversations.map((conv) => (
                  <div
                    key={conv.id}
                    onClick={() => openConversation(conv)}
                    className={`p-3 rounded-2xl cursor-pointer transition-all ${
                      activeConv?.id === conv.id ? 'bg-[#4F46E5]/10' : 'hover:bg-gray-50'
                    }`}
                    data-testid={`conversation-${conv.id}`}
                  >
                    <div className="flex items-center gap-3">
                      <Avatar className="w-10 h-10">
                        <AvatarFallback className="bg-[#4F46E5] text-white">
                          {conv.partner.name?.charAt(0) || 'U'}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold text-[#111827] truncate">{conv.partner.name}</p>
                        <p className="text-xs text-[#4B5563] truncate">
                          {conv.last_message?.content || 'Start a conversation...'}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Chat Area */}
          <Card className="bg-white rounded-3xl shadow-sm border border-gray-100 lg:col-span-2 flex flex-col">
            {activeConv ? (
              <>
                <div className="p-4 border-b border-gray-100 flex items-center gap-3">
                  <Avatar className="w-10 h-10">
                    <AvatarFallback className="bg-[#4F46E5] text-white">
                      {activeConv.partner.name?.charAt(0) || 'U'}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <p className="text-sm font-semibold text-[#111827]">{activeConv.partner.name}</p>
                  </div>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-3" data-testid="messages-container">
                  {messages.length === 0 ? (
                    <p className="text-center text-sm text-[#4B5563] py-8">No messages yet. Say hi!</p>
                  ) : (
                    messages.map((msg) => {
                      const isMine = msg.sender_id === user.id;
                      return (
                        <div key={msg.id} className={`flex ${isMine ? 'justify-end' : 'justify-start'}`} data-testid={`message-${msg.id}`}>
                          <div className={`max-w-[70%] px-4 py-2 rounded-2xl ${
                            isMine ? 'bg-[#4F46E5] text-white' : 'bg-gray-100 text-[#111827]'
                          }`}>
                            <p className="text-sm">{msg.content}</p>
                          </div>
                        </div>
                      );
                    })
                  )}
                  <div ref={messagesEndRef} />
                </div>

                <form onSubmit={sendMessage} className="p-4 border-t border-gray-100 flex gap-2">
                  <Input
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    placeholder="Type a message..."
                    className="flex-1 rounded-full border-gray-200 px-4"
                    data-testid="message-input"
                  />
                  <Button
                    type="submit"
                    disabled={!newMessage.trim()}
                    className="bg-[#4F46E5] text-white hover:bg-[#4338CA] rounded-full px-6"
                    data-testid="send-message-button"
                  >
                    <Send className="w-4 h-4" />
                  </Button>
                </form>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <MessageCircle className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <p className="text-[#4B5563]">Select a conversation to start chatting</p>
                </div>
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};
