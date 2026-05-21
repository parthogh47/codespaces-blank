import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { toast } from 'sonner';
import { Users, Trophy, Target, Sparkles, LogOut, RefreshCw } from 'lucide-react';
import axios from 'axios';

export const Dashboard = () => {
  const { user, logout } = useAuth();
  const [matches, setMatches] = useState([]);
  const [challenges, setChallenges] = useState([]);
  const [achievements, setAchievements] = useState([]);
  const [matchError, setMatchError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const navigate = useNavigate();
  const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [matchesRes, achievementsRes] = await Promise.all([
        axios.get(`${API}/matches`, { withCredentials: true }),
        axios.get(`${API}/achievements`, { withCredentials: true })
      ]);
      
      setMatches(matchesRes.data.matches || []);
      setChallenges(matchesRes.data.mini_challenges || []);
      setAchievements(achievementsRes.data.achievements || []);
      
      if (matchesRes.data.error) {
        setMatchError(matchesRes.data.error_message || 'Failed to generate matches');
      } else {
        setMatchError(null);
      }
    } catch (error) {
      toast.error('Failed to load data');
      setMatchError('Failed to load matches');
    } finally {
      setIsLoading(false);
    }
  };

  const generateNewMatches = async () => {
    setIsGenerating(true);
    try {
      const { data } = await axios.post(`${API}/matches/generate`, { force_refresh: true }, { withCredentials: true });
      setMatches(data.matches || []);
      setChallenges(data.mini_challenges || []);
      
      if (data.error) {
        setMatchError(data.error_message || 'Failed to generate matches');
        toast.error(data.error_message || 'Failed to generate matches');
      } else {
        setMatchError(null);
        toast.success('New matches generated!');
      }
    } catch (error) {
      toast.error('Failed to generate matches');
      setMatchError('Failed to generate matches');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F3F4F6]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-[#4F46E5] border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-[#4B5563] font-medium">Loading your matches...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F3F4F6]">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-[#4F46E5] to-[#6366F1] rounded-full flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <h1 className="text-2xl font-bold tracking-tight text-[#111827]">SkillPartner</h1>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right hidden sm:block">
                <p className="text-sm font-semibold text-[#111827]">{user?.name}</p>
                <p className="text-xs text-[#4B5563]">{user?.email}</p>
              </div>
              <Button
                onClick={handleLogout}
                variant="ghost"
                className="rounded-full"
                data-testid="logout-button"
              >
                <LogOut className="w-5 h-5" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h2 className="text-4xl sm:text-5xl font-bold tracking-tight text-[#111827] mb-2">Welcome back, {user?.name}!</h2>
          <p className="text-base text-[#4B5563]">Here are your personalized skill matches</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-8">
            {/* Your Skills */}
            <Card className="bg-white rounded-3xl shadow-sm border border-gray-100 p-6" data-testid="user-skills-card">
              <h3 className="text-xl sm:text-2xl font-semibold tracking-tight text-[#111827] mb-4">Your Skills</h3>
              <div className="flex flex-wrap gap-2">
                {user?.skills?.map((skill) => (
                  <Badge key={skill} className="px-3 py-1 bg-gray-100 text-[#4B5563] rounded-full text-sm font-medium">
                    {skill} · {user?.proficiency?.[skill] || 'beginner'}
                  </Badge>
                ))}
              </div>
            </Card>

            {/* Matches Section */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#111827] flex items-center gap-2">
                  <Users className="w-7 h-7 text-[#4F46E5]" />
                  Your Skill Matches
                </h3>
                <Button
                  onClick={generateNewMatches}
                  disabled={isGenerating}
                  className="bg-[#4F46E5] text-white hover:bg-[#4338CA] rounded-full transition-all"
                  data-testid="generate-matches-button"
                >
                  <RefreshCw className={`w-4 h-4 mr-2 ${isGenerating ? 'animate-spin' : ''}`} />
                  Refresh
                </Button>
              </div>
              
              <div className="space-y-6">
                {matchError ? (
                  <Card className="bg-white rounded-3xl shadow-sm border border-red-200 p-8 text-center">
                    <p className="text-red-600 font-medium mb-4">{matchError}</p>
                    <Button
                      onClick={generateNewMatches}
                      disabled={isGenerating}
                      className="bg-[#4F46E5] text-white hover:bg-[#4338CA] rounded-full"
                    >
                      {isGenerating ? 'Generating...' : 'Try Again'}
                    </Button>
                  </Card>
                ) : matches.length === 0 ? (
                  <Card className="bg-white rounded-3xl shadow-sm border border-gray-100 p-8 text-center">
                    <p className="text-[#4B5563]">No matches yet. Click refresh to generate!</p>
                  </Card>
                ) : (
                  matches.map((match, idx) => (
                    <Card
                      key={idx}
                      className="bg-white rounded-3xl shadow-sm border border-gray-100 p-6 hover:shadow-md hover:border-gray-200 hover:-translate-y-1 transition-all cursor-pointer border-l-4 border-l-[#4F46E5]"
                      onClick={() => navigate(`/match/${idx}`, { state: { match } })}
                      data-testid={`match-card-${idx}`}
                    >
                      <div className="flex items-start gap-4">
                        <Avatar className="w-12 h-12">
                          <AvatarFallback className="bg-[#4F46E5] text-white font-semibold">
                            {match.partner_name?.charAt(0) || 'P'}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="text-lg font-semibold text-[#111827]">{match.partner_name}</h4>
                            <Badge className={`px-3 py-1 rounded-full text-sm font-semibold ${
                              match.compatibility === 'High' ? 'bg-[#10B981]/10 text-[#10B981]' :
                              match.compatibility === 'Medium' ? 'bg-[#FBBF24]/10 text-[#D97706]' :
                              'bg-gray-100 text-[#4B5563]'
                            }`}>
                              {match.compatibility} Match
                            </Badge>
                          </div>
                          <p className="text-sm text-[#4B5563] mb-3">{match.collaboration_idea}</p>
                          <div className="flex flex-wrap gap-2">
                            {match.complementary_skills?.map((skill, i) => (
                              <Badge key={i} className="px-3 py-1 bg-gray-100 text-[#4B5563] rounded-full text-sm font-medium">
                                {skill}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      </div>
                    </Card>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-8">
            {/* Mini Challenges */}
            <Card className="bg-white rounded-3xl shadow-sm border border-gray-100 p-6" data-testid="challenges-card">
              <h3 className="text-xl sm:text-2xl font-semibold tracking-tight text-[#111827] mb-4 flex items-center gap-2">
                <Target className="w-6 h-6 text-[#FBBF24]" />
                Mini Challenges
              </h3>
              <div className="space-y-3">
                {challenges.map((challenge, idx) => (
                  <div key={idx} className="p-4 bg-white rounded-2xl border-l-4 border-[#FBBF24] shadow-sm" data-testid={`challenge-${idx}`}>
                    <p className="text-sm font-medium text-[#111827]">{challenge}</p>
                  </div>
                ))}
              </div>
            </Card>

            {/* Achievements */}
            <Card className="bg-white rounded-3xl shadow-sm border border-gray-100 p-6" data-testid="achievements-card">
              <h3 className="text-xl sm:text-2xl font-semibold tracking-tight text-[#111827] mb-4 flex items-center gap-2">
                <Trophy className="w-6 h-6 text-[#10B981]" />
                Achievements
              </h3>
              <div className="space-y-3">
                {achievements.map((achievement) => (
                  <div key={achievement.id} className="flex items-center gap-3 p-3 rounded-xl bg-gray-50" data-testid={`achievement-${achievement.id}`}>
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      achievement.earned ? 'bg-[#10B981]/10' : 'bg-gray-200'
                    }`}>
                      <Trophy className={`w-5 h-5 ${achievement.earned ? 'text-[#10B981]' : 'text-gray-400'}`} />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-semibold text-[#111827]">{achievement.title}</p>
                      <p className="text-xs text-[#4B5563]">{achievement.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};