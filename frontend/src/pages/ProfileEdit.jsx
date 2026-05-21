import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import { Upload, X, Plus, ArrowLeft } from 'lucide-react';
import axios from 'axios';

export const ProfileEdit = () => {
  const { user, updateUser } = useAuth();
  const [name, setName] = useState('');
  const [bio, setBio] = useState('');
  const [profilePicture, setProfilePicture] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [skills, setSkills] = useState([]);
  const [currentSkill, setCurrentSkill] = useState('');
  const [proficiency, setProficiency] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();
  const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

  useEffect(() => {
    if (user) {
      setName(user.name || '');
      setBio(user.bio || '');
      setSkills(user.skills || []);
      setProficiency(user.proficiency || {});
    }
  }, [user]);

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
    setIsLoading(true);
    
    try {
      if (profilePicture) {
        const formData = new FormData();
        formData.append('file', profilePicture);
        await axios.post(`${API}/profile/upload-picture`, formData, {
          withCredentials: true,
          headers: { 'Content-Type': 'multipart/form-data' }
        });
      }
      
      const { data } = await axios.put(`${API}/profile`, { name, bio, skills, proficiency }, { withCredentials: true });
      updateUser(data);
      
      toast.success('Profile updated!');
      navigate('/dashboard');
    } catch (error) {
      toast.error('Failed to update profile');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F3F4F6]">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <Button
            onClick={() => navigate('/dashboard')}
            variant="ghost"
            className="rounded-full"
            data-testid="back-button"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            Back
          </Button>
        </div>
      </header>

      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card className="bg-white rounded-3xl shadow-md border border-gray-100 p-8">
          <h1 className="text-4xl font-bold tracking-tight text-[#111827] mb-2">Edit Profile</h1>
          <p className="text-base text-[#4B5563] mb-8">Update your information and skills</p>
          
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
                <p className="mt-3 text-sm text-[#4B5563]">Click to change photo</p>
              </div>
            </div>

            {/* Name */}
            <div>
              <Label htmlFor="name" className="text-sm font-medium text-[#111827]">Full Name</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="mt-2 w-full rounded-xl border-gray-200 bg-white px-4 py-3 text-sm focus:border-[#4F46E5] focus:ring-2 focus:ring-[#4F46E5]/20 outline-none"
                data-testid="profile-name-input"
              />
            </div>

            {/* Bio */}
            <div>
              <Label htmlFor="bio" className="text-sm font-medium text-[#111827]">Bio</Label>
              <Textarea
                id="bio"
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                placeholder="Tell others about yourself..."
                rows={4}
                className="mt-2 w-full rounded-xl border-gray-200 bg-white px-4 py-3 text-sm focus:border-[#4F46E5] focus:ring-2 focus:ring-[#4F46E5]/20 outline-none"
                data-testid="profile-bio-input"
              />
            </div>
            
            {/* Skills */}
            <div>
              <Label className="text-lg font-semibold text-[#111827] mb-4 block">Skills</Label>
              <div className="flex gap-2 mb-4">
                <Input
                  value={currentSkill}
                  onChange={(e) => setCurrentSkill(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addSkill())}
                  placeholder="e.g., Python, Design, Marketing"
                  className="flex-1 rounded-xl border-gray-200 bg-white px-4 py-3 text-sm focus:border-[#4F46E5] focus:ring-2 focus:ring-[#4F46E5]/20 outline-none"
                  data-testid="skill-input"
                />
                <Button
                  type="button"
                  onClick={addSkill}
                  className="bg-[#4F46E5] text-white hover:bg-[#4338CA] rounded-xl px-6"
                  data-testid="add-skill-button"
                >
                  <Plus className="w-5 h-5" />
                </Button>
              </div>
              
              <div className="space-y-3">
                {skills.map((skill) => (
                  <div key={skill} className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl" data-testid={`skill-item-${skill}`}>
                    <Badge className="px-3 py-1 bg-[#4F46E5]/10 text-[#4F46E5] rounded-full text-sm font-medium">{skill}</Badge>
                    <Select
                      value={proficiency[skill] || 'beginner'}
                      onValueChange={(value) => setProficiency({ ...proficiency, [skill]: value })}
                    >
                      <SelectTrigger className="w-40 rounded-xl border-gray-200">
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
                      className="ml-auto text-gray-400 hover:text-red-500"
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
              disabled={isLoading}
              className="w-full bg-[#4F46E5] text-white hover:bg-[#4338CA] rounded-full font-semibold py-6 transition-all shadow-sm shadow-[#4F46E5]/20"
              data-testid="save-profile-button"
            >
              {isLoading ? 'Saving...' : 'Save Changes'}
            </Button>
          </form>
        </Card>
      </div>
    </div>
  );
};
