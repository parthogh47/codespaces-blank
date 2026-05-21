import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Card } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Avatar, AvatarFallback } from '../components/ui/avatar';
import { Button } from '../components/ui/button';
import { Sparkles, Users, MessageCircle } from 'lucide-react';
import axios from 'axios';

export const SharedMatch = () => {
  const { token } = useParams();
  const [share, setShare] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const API = '/api';

  useEffect(() => {
    loadShare();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const loadShare = async () => {
    try {
      const { data } = await axios.get(`${API}/share/${token}`);
      setShare(data);
    } catch {
      setNotFound(true);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#F3F4F6] to-[#EFF6FF]">
        <div className="w-12 h-12 border-4 border-[#4F46E5] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (notFound || !share) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#F3F4F6] to-[#EFF6FF] p-4">
        <Card className="bg-white rounded-3xl shadow-md border border-gray-100 p-8 text-center max-w-md">
          <h1 className="text-2xl font-bold text-[#111827] mb-2">Match Not Found</h1>
          <p className="text-[#4B5563] mb-6">This shared link may have expired.</p>
          <Button
            onClick={() => (window.location.href = '/')}
            className="bg-[#4F46E5] text-white hover:bg-[#4338CA] rounded-full"
          >
            Go to SkillPartner
          </Button>
        </Card>
      </div>
    );
  }

  const { match, user_name, user_skills } = share;

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#F3F4F6] to-[#EFF6FF] py-12 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-[#4F46E5] to-[#6366F1] rounded-full mb-4">
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-[#111827] mb-2">A Perfect Match!</h1>
          <p className="text-base text-[#4B5563]">{user_name} found their skill partner on SkillPartner</p>
        </div>

        <Card className="bg-white rounded-3xl shadow-md border border-gray-100 p-8 mb-6" data-testid="shared-match-card">
          <div className="flex items-center justify-center mb-6">
            <div className="flex items-center gap-4">
              <Avatar className="w-20 h-20">
                <AvatarFallback className="bg-[#4F46E5] text-white text-2xl font-bold">
                  {user_name?.charAt(0) || 'U'}
                </AvatarFallback>
              </Avatar>
              <div className="flex flex-col items-center">
                <Users className="w-8 h-8 text-[#10B981]" />
                <Badge className="mt-1 bg-[#10B981]/10 text-[#10B981] rounded-full px-3 py-1">
                  {match.compatibility} Match
                </Badge>
              </div>
              <Avatar className="w-20 h-20">
                <AvatarFallback className="bg-gradient-to-br from-[#4F46E5] to-[#6366F1] text-white text-2xl font-bold">
                  {match.partner_name?.charAt(0) || 'P'}
                </AvatarFallback>
              </Avatar>
            </div>
          </div>

          <div className="text-center mb-6">
            <p className="text-xl font-semibold text-[#111827]">{user_name} &times; {match.partner_name}</p>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-6">
            <div>
              <p className="text-xs font-semibold text-[#4B5563] uppercase mb-2">{user_name?.split(' ')[0]}'s Skills</p>
              <div className="flex flex-wrap gap-2">
                {user_skills?.slice(0, 5).map((skill, i) => (
                  <Badge key={i} className="px-3 py-1 bg-gray-100 text-[#4B5563] rounded-full text-xs">{skill}</Badge>
                ))}
              </div>
            </div>
            <div>
              <p className="text-xs font-semibold text-[#4B5563] uppercase mb-2">{match.partner_name?.split(' ')[0]}'s Skills</p>
              <div className="flex flex-wrap gap-2">
                {match.complementary_skills?.slice(0, 5).map((skill, i) => (
                  <Badge key={i} className="px-3 py-1 bg-[#4F46E5]/10 text-[#4F46E5] rounded-full text-xs">{skill}</Badge>
                ))}
              </div>
            </div>
          </div>

          <div className="bg-[#F3F4F6] rounded-2xl p-4">
            <p className="text-xs font-semibold text-[#4B5563] uppercase mb-2">Collaboration Idea</p>
            <p className="text-sm text-[#111827]">{match.collaboration_idea}</p>
          </div>
        </Card>

        <Card className="bg-white rounded-3xl shadow-sm border border-gray-100 p-6 text-center">
          <MessageCircle className="w-10 h-10 text-[#4F46E5] mx-auto mb-3" />
          <h2 className="text-xl font-semibold text-[#111827] mb-2">Find Your Own Skill Partner</h2>
          <p className="text-sm text-[#4B5563] mb-4">Join SkillPartner and let AI match you with the perfect collaborator</p>
          <Button
            onClick={() => (window.location.href = '/register')}
            className="bg-[#4F46E5] text-white hover:bg-[#4338CA] rounded-full px-8"
            data-testid="signup-cta-button"
          >
            Get Started Free
          </Button>
        </Card>
      </div>
    </div>
  );
};
