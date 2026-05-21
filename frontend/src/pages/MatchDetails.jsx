import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Avatar, AvatarFallback } from '../components/ui/avatar';
import { toast } from 'sonner';
import { ArrowLeft, Copy, MessageCircle, Users } from 'lucide-react';

export const MatchDetails = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const match = location.state?.match;

  if (!match) {
    return (
      <div className="min-h-screen bg-[#F3F4F6] flex items-center justify-center">
        <Card className="bg-white rounded-3xl shadow-sm border border-gray-100 p-8">
          <p className="text-[#4B5563]">Match not found</p>
          <Button onClick={() => navigate('/dashboard')} className="mt-4 bg-[#4F46E5] text-white rounded-full">
            Back to Dashboard
          </Button>
        </Card>
      </div>
    );
  }

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
      .then(() => toast.success('Copied to clipboard!'))
      .catch(() => {
        // Fallback for browsers/contexts that block clipboard
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        try {
          document.execCommand('copy');
          toast.success('Copied to clipboard!');
        } catch {
          toast.error('Failed to copy');
        }
        document.body.removeChild(textArea);
      });
  };

  return (
    <div className="min-h-screen bg-[#F3F4F6]">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <Button
            onClick={() => navigate('/dashboard')}
            variant="ghost"
            className="rounded-full"
            data-testid="back-button"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            Back to Dashboard
          </Button>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Partner Profile */}
        <Card className="bg-white rounded-3xl shadow-md border border-gray-100 p-8 mb-8" data-testid="match-profile-card">
          <div className="flex flex-col sm:flex-row items-center gap-6 mb-6">
            <Avatar className="w-24 h-24">
              <AvatarFallback className="bg-gradient-to-br from-[#4F46E5] to-[#6366F1] text-white text-3xl font-bold">
                {match.partner_name?.charAt(0) || 'P'}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 text-center sm:text-left">
              <h1 className="text-4xl font-bold tracking-tight text-[#111827] mb-2">{match.partner_name}</h1>
              <Badge className={`px-4 py-2 rounded-full text-sm font-semibold ${
                match.compatibility === 'High' ? 'bg-[#10B981]/10 text-[#10B981]' :
                match.compatibility === 'Medium' ? 'bg-[#FBBF24]/10 text-[#D97706]' :
                'bg-gray-100 text-[#4B5563]'
              }`}>
                {match.compatibility} Compatibility
              </Badge>
            </div>
          </div>
        </Card>

        {/* Complementary Skills */}
        <Card className="bg-white rounded-3xl shadow-sm border border-gray-100 p-8 mb-8" data-testid="skills-card">
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#111827] mb-4 flex items-center gap-2">
            <Users className="w-7 h-7 text-[#4F46E5]" />
            Complementary Skills
          </h2>
          <div className="flex flex-wrap gap-3">
            {match.complementary_skills?.map((skill, i) => (
              <Badge key={i} className="px-4 py-2 bg-[#4F46E5]/10 text-[#4F46E5] rounded-full text-base font-medium">
                {skill}
              </Badge>
            ))}
          </div>
        </Card>

        {/* Collaboration Idea */}
        <Card className="bg-white rounded-3xl shadow-sm border border-gray-100 p-8 mb-8" data-testid="collaboration-card">
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#111827] mb-4">Collaboration Idea</h2>
          <p className="text-base leading-relaxed text-[#4B5563]">{match.collaboration_idea}</p>
        </Card>

        {/* Conversation Starters */}
        <Card className="bg-white rounded-3xl shadow-sm border border-gray-100 p-8 mb-8" data-testid="conversation-starters-card">
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#111827] mb-6 flex items-center gap-2">
            <MessageCircle className="w-7 h-7 text-[#4F46E5]" />
            Conversation Starters
          </h2>
          <div className="space-y-4">
            {match.conversation_starters?.map((starter, i) => (
              <div
                key={i}
                className="group p-4 bg-[#F3F4F6] rounded-2xl hover:bg-[#EFF6FF] transition-all cursor-pointer flex items-center justify-between"
                onClick={() => copyToClipboard(starter)}
                data-testid={`conversation-starter-${i}`}
              >
                <p className="text-sm font-medium text-[#111827] flex-1">{starter}</p>
                <Copy className="w-5 h-5 text-[#4F46E5] opacity-0 group-hover:opacity-100 transition-opacity ml-4" />
              </div>
            ))}
          </div>
          <p className="mt-4 text-sm text-[#4B5563] text-center">Click any starter to copy it</p>
        </Card>

        {/* CTA */}
        <div className="sticky bottom-0 bg-white border-t border-gray-200 p-4 rounded-t-3xl sm:relative sm:border-0 sm:bg-transparent sm:p-0">
          <Button
            className="w-full bg-[#4F46E5] text-white hover:bg-[#4338CA] rounded-full font-semibold py-6 text-lg transition-all shadow-sm shadow-[#4F46E5]/20"
            data-testid="start-collaboration-button"
          >
            Start Collaboration
          </Button>
        </div>
      </div>
    </div>
  );
};