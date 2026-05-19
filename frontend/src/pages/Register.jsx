import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card } from '../components/ui/card';
import { toast } from 'sonner';
import { Sparkles } from 'lucide-react';

export const Register = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    const result = await register(email, password, name);
    setIsLoading(false);
    
    if (result.success) {
      toast.success('Account created successfully!');
      navigate('/onboarding');
    } else {
      toast.error(result.error || 'Registration failed');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#F3F4F6] to-[#EFF6FF] flex items-center justify-center p-4">
      <Card className="w-full max-w-md bg-white rounded-3xl shadow-md border border-gray-100 p-8">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-[#4F46E5] to-[#6366F1] rounded-full mb-4">
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-[#111827] mb-2">Join SkillPartner</h1>
          <p className="text-base text-[#4B5563]">Start finding your perfect learning partners</p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <Label htmlFor="name" className="text-sm font-medium text-[#111827]">Full Name</Label>
            <Input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="John Doe"
              required
              className="mt-2 w-full rounded-xl border-gray-200 bg-white px-4 py-3 text-sm focus:border-[#4F46E5] focus:ring-2 focus:ring-[#4F46E5]/20 outline-none transition-all"
              data-testid="register-name-input"
            />
          </div>
          
          <div>
            <Label htmlFor="email" className="text-sm font-medium text-[#111827]">Email</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
              required
              className="mt-2 w-full rounded-xl border-gray-200 bg-white px-4 py-3 text-sm focus:border-[#4F46E5] focus:ring-2 focus:ring-[#4F46E5]/20 outline-none transition-all"
              data-testid="register-email-input"
            />
          </div>
          
          <div>
            <Label htmlFor="password" className="text-sm font-medium text-[#111827]">Password</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              minLength={6}
              className="mt-2 w-full rounded-xl border-gray-200 bg-white px-4 py-3 text-sm focus:border-[#4F46E5] focus:ring-2 focus:ring-[#4F46E5]/20 outline-none transition-all"
              data-testid="register-password-input"
            />
          </div>
          
          <Button
            type="submit"
            disabled={isLoading}
            className="w-full bg-[#4F46E5] text-white hover:bg-[#4338CA] rounded-full font-semibold py-6 transition-all shadow-sm shadow-[#4F46E5]/20"
            data-testid="register-submit-button"
          >
            {isLoading ? 'Creating account...' : 'Create Account'}
          </Button>
        </form>
        
        <p className="text-center mt-6 text-sm text-[#4B5563]">
          Already have an account?{' '}
          <Link to="/login" className="text-[#4F46E5] font-semibold hover:underline" data-testid="login-link">
            Sign in
          </Link>
        </p>
      </Card>
    </div>
  );
};