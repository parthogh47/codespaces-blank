import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import { Upload, X, Plus } from 'lucide-react';
import axios from 'axios';

export const Onboarding = () => {
  const [profilePicture, setProfilePicture] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [skills, setSkills] = useState([]);
  const [currentSkill, setCurrentSkill] = useState('');
  const [proficiency, setProficiency] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const fileInputRef = useRef(null);
  const { user, updateUser } = useAuth();
  const navigate = useNavigate();
  const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setProfilePicture(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const addSkill = () => {
    if (currentSkill.trim() && !skills.includes(currentSkill.trim())) {
      const newSkill = currentSkill.trim();
      setSkills([...skills, newSkill]);
      setProficiency({ ...proficiency, [newSkill]: 'beginner' });
      setCurrentSkill('');
    }
  };

  const removeSkill = (skillToRemove) => {
    setSkills(skills.filter(s => s !== skillToRemove));
    const newProf = { ...proficiency };
    delete newProf[skillToRemove];
    setProficiency(newProf);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (skills.length === 0) {
      toast.error('Please add at least one skill');
      return;
    }
    
    setIsLoading(true);
    
    try {
      // Upload profile picture
      if (profilePicture) {
        const formData = new FormData();
        formData.append('file', profilePicture);
        await axios.post(`${API}/profile/upload-picture`, formData, {
          withCredentials: true,
          headers: { 'Content-Type': 'multipart/form-data' }
        });
      }
      
      // Update profile
      const { data } = await axios.put(`${API}/profile`, { skills, proficiency }, { withCredentials: true });
      updateUser(data);
      
      toast.success('Profile completed!');
      navigate('/dashboard');
    } catch (error) {
      toast.error('Failed to update profile');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#F3F4F6] to-[#EFF6FF] py-12 px-4">
      <div className="max-w-3xl mx-auto">
        <Card className="bg-white rounded-3xl shadow-md border border-gray-100 p-8">
          <div className="text-center mb-8">
            <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-[#111827] mb-2">Complete Your Profile</h1>
            <p className="text-base text-[#4B5563]">Let's set up your learning journey</p>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-8">
            {/* Profile Picture */}
            <div>
              <Label className="text-lg font-semibold text-[#111827] mb-4 block">Profile Picture</Label>
              <div className="flex flex-col items-center">
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="w-32 h-32 rounded-full border-4 border-[#4F46E5] border-dashed flex items-center justify-center cursor-pointer hover:border-[#4338CA] transition-all overflow-hidden bg-gray-50"
                  data-testid="profile-picture-upload"
                >
                  {previewUrl ? (
                    <img src={previewUrl} alt="Preview" className="w-full h-full object-cover" />
                  ) : (
                    <Upload className="w-8 h-8 text-[#4F46E5]" />
                  )}
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <p className="mt-3 text-sm text-[#4B5563]">Click to upload your photo</p>
              </div>
            </div>
            
            {/* Skills */}
            <div>
              <Label className="text-lg font-semibold text-[#111827] mb-4 block">Your Skills</Label>
              <div className="flex gap-2 mb-4">
                <Input
                  value={currentSkill}
                  onChange={(e) => setCurrentSkill(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addSkill())}
                  placeholder="e.g., Python, Design, Marketing"
                  className="flex-1 rounded-xl border-gray-200 bg-white px-4 py-3 text-sm focus:border-[#4F46E5] focus:ring-2 focus:ring-[#4F46E5]/20 outline-none transition-all"
                  data-testid="skill-input"
                />
                <Button
                  type="button"
                  onClick={addSkill}
                  className="bg-[#4F46E5] text-white hover:bg-[#4338CA] rounded-xl px-6 transition-all"
                  data-testid="add-skill-button"
                >
                  <Plus className="w-5 h-5" />
                </Button>
              </div>
              
              {/* Skill Tags */}
              <div className="space-y-3">
                {skills.map((skill) => (
                  <div key={skill} className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl" data-testid={`skill-item-${skill}`}>
                    <Badge className="px-3 py-1 bg-[#4F46E5]/10 text-[#4F46E5] rounded-full text-sm font-medium">
                      {skill}
                    </Badge>
                    <Select
                      value={proficiency[skill] || 'beginner'}
                      onValueChange={(value) => setProficiency({ ...proficiency, [skill]: value })}
                    >
                      <SelectTrigger className="w-40 rounded-xl border-gray-200" data-testid={`proficiency-select-${skill}`}>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="beginner">Beginner</SelectItem>
                        <SelectItem value="intermediate">Intermediate</SelectItem>
                        <SelectItem value="advanced">Advanced</SelectItem>
                      </SelectContent>
                    </Select>
                    <button
                      type="button"
                      onClick={() => removeSkill(skill)}
                      className="ml-auto text-gray-400 hover:text-red-500 transition-colors"
                      data-testid={`remove-skill-${skill}`}
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
            
            <Button
              type="submit"
              disabled={isLoading || skills.length === 0}
              className="w-full bg-[#4F46E5] text-white hover:bg-[#4338CA] rounded-full font-semibold py-6 transition-all shadow-sm shadow-[#4F46E5]/20"
              data-testid="complete-profile-button"
            >
              {isLoading ? 'Saving...' : 'Complete Profile'}
            </Button>
          </form>
        </Card>
      </div>
    </div>
  );
};