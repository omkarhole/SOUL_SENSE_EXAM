'use client';

import { PersonalProfile } from '@/lib/api/profile';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui';
import { Mail, Calendar, User as UserIcon, Briefcase, GraduationCap, Edit2, Moon, Activity, Apple, Heart, Target } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ProfileCardProps {
  profile: any | null;
  user: {
    username?: string;
    email?: string;
    created_at?: string;
    name?: string;
  } | null;
  className?: string;
  variant?: 'full' | 'compact';
  editable?: boolean;
  onEdit?: () => void;
}

export function ProfileCard({
  profile,
  user,
  className,
  variant = 'full',
  editable,
  onEdit,
}: ProfileCardProps) {
  const getInitials = () => {
    if (profile?.first_name || profile?.firstName) {
      const first = (profile.first_name || profile.firstName || '')[0] || '';
      const last = (profile.last_name || profile.lastName || '')[0] || '';
      if (first || last) return `${first}${last}`.toUpperCase();
    }
    return (user?.name || user?.username || 'U')
      .split(' ')
      .map((n) => n[0])
      .join('')
      .slice(0, 2)
      .toUpperCase();
  };

  return (
    <div className={cn('space-y-8', className)}>
      {/* Avatar and Name Section */}
      <div className="flex flex-col sm:flex-row items-center gap-8 border-b border-border/40 pb-8">
        <div className="relative group">
          <Avatar className="h-28 w-28 border-4 border-background shadow-xl group-hover:shadow-2xl transition-all duration-300">
            {profile?.avatar_path && (
              <AvatarImage
                src={`/api/v1/avatars/${profile.avatar_path}`}
                alt={`${user?.username || 'User'} avatar`}
                className="object-cover"
              />
            )}
            <AvatarFallback className="bg-gradient-to-br from-primary to-primary/60 text-white text-2xl font-black">
              {getInitials()}
            </AvatarFallback>
          </Avatar>
        </div>

        <div className="text-center sm:text-left flex-1 flex flex-col sm:flex-row justify-between items-center sm:items-start gap-4">
          <div className="space-y-1">
            <h2 className="text-3xl font-black tracking-tight text-foreground">
              {profile?.first_name || profile?.firstName
                ? `${profile.first_name || profile.firstName} ${profile.last_name || profile.lastName || ''}`
                : user?.name || user?.username || 'User'}
            </h2>
            <p className="text-lg text-muted-foreground font-medium opacity-70">
              @{user?.username}
            </p>
          </div>
          {editable && onEdit && (
            <button
              onClick={onEdit}
              className="flex items-center gap-2 px-4 py-2 rounded-full bg-primary/5 text-primary hover:bg-primary/10 transition-colors text-sm font-bold border border-primary/10"
            >
              <Edit2 className="h-3.5 w-3.5" />
              <span>Edit Details</span>
            </button>
          )}
        </div>
      </div>

      {/* Profile Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <div className="flex items-center gap-4 p-4 rounded-2xl bg-muted/20 border border-border/40 group hover:border-primary/20 transition-colors">
            <div className="p-2.5 rounded-xl bg-background border border-border/40 text-muted-foreground group-hover:text-primary transition-colors">
              <Mail className="h-4 w-4" />
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-widest font-black text-muted-foreground/60 mb-0.5">
                Email Address
              </p>
              <p className="font-semibold text-sm">{user?.email || 'Not provided'}</p>
            </div>
          </div>

          <div className="flex items-center gap-4 p-4 rounded-2xl bg-muted/20 border border-border/40 group hover:border-primary/20 transition-colors">
            <div className="p-2.5 rounded-xl bg-background border border-border/40 text-muted-foreground group-hover:text-primary transition-colors">
              <Calendar className="h-4 w-4" />
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-widest font-black text-muted-foreground/60 mb-0.5">
                Member Since
              </p>
              <p className="font-semibold text-sm">
                {user?.created_at
                  ? new Date(user.created_at).toLocaleDateString('en-US', {
                      month: 'long',
                      year: 'numeric',
                    })
                  : 'February 2026'}
              </p>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-4">
            {profile?.age && (
              <div className="flex items-center gap-4 p-4 rounded-2xl bg-muted/20 border border-border/40 group hover:border-primary/20 transition-colors">
                <div className="p-2.5 rounded-xl bg-background border border-border/40 text-muted-foreground group-hover:text-primary transition-colors">
                  <UserIcon className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-widest font-black text-muted-foreground/60 mb-0.5">
                    Age
                  </p>
                  <p className="font-semibold text-sm">{profile.age} years old</p>
                </div>
              </div>
            )}

            {profile?.occupation && (
              <div className="flex items-center gap-4 p-4 rounded-2xl bg-muted/20 border border-border/40 group hover:border-primary/20 transition-colors">
                <div className="p-2.5 rounded-xl bg-background border border-border/40 text-muted-foreground group-hover:text-primary transition-colors">
                  <Briefcase className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-widest font-black text-muted-foreground/60 mb-0.5">
                    Occupation
                  </p>
                  <p className="font-semibold text-sm">{profile.occupation}</p>
                </div>
              </div>
            )}

            {profile?.education_level && (
              <div className="flex items-center gap-4 p-4 rounded-2xl bg-muted/20 border border-border/40 group hover:border-primary/20 transition-colors">
                <div className="p-2.5 rounded-xl bg-background border border-border/40 text-muted-foreground group-hover:text-primary transition-colors">
                  <GraduationCap className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-widest font-black text-muted-foreground/60 mb-0.5">
                    Education
                  </p>
                  <p className="font-semibold text-sm">{profile.education_level}</p>
                </div>
              </div>
            )}

            {profile?.sleep_hours && (
              <div className="flex items-center gap-4 p-4 rounded-2xl bg-muted/20 border border-border/40 group hover:border-primary/20 transition-colors">
                <div className="p-2.5 rounded-xl bg-background border border-border/40 text-muted-foreground group-hover:text-primary transition-colors">
                  <Moon className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-widest font-black text-muted-foreground/60 mb-0.5">
                    Sleep Hours
                  </p>
                  <p className="font-semibold text-sm">{profile.sleep_hours} hours/night</p>
                </div>
              </div>
            )}

            {profile?.exercise_freq && (
              <div className="flex items-center gap-4 p-4 rounded-2xl bg-muted/20 border border-border/40 group hover:border-primary/20 transition-colors">
                <div className="p-2.5 rounded-xl bg-background border border-border/40 text-muted-foreground group-hover:text-primary transition-colors">
                  <Activity className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-widest font-black text-muted-foreground/60 mb-0.5">
                    Exercise Frequency
                  </p>
                  <p className="font-semibold text-sm capitalize">{profile.exercise_freq}</p>
                </div>
              </div>
            )}

            {profile?.dietary_patterns && (
              <div className="flex items-center gap-4 p-4 rounded-2xl bg-muted/20 border border-border/40 group hover:border-primary/20 transition-colors">
                <div className="p-2.5 rounded-xl bg-background border border-border/40 text-muted-foreground group-hover:text-primary transition-colors">
                  <Apple className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-widest font-black text-muted-foreground/60 mb-0.5">
                    Diet Type
                  </p>
                  <p className="font-semibold text-sm">{profile.dietary_patterns}</p>
                </div>
              </div>
            )}

            {profile?.has_therapist !== undefined && (
              <div className="flex items-center gap-4 p-4 rounded-2xl bg-muted/20 border border-border/40 group hover:border-primary/20 transition-colors">
                <div className="p-2.5 rounded-xl bg-background border border-border/40 text-muted-foreground group-hover:text-primary transition-colors">
                  <Heart className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-widest font-black text-muted-foreground/60 mb-0.5">
                    Therapist Access
                  </p>
                  <p className="font-semibold text-sm">{profile.has_therapist ? 'Yes' : 'No'}</p>
                </div>
              </div>
            )}

            {profile?.support_network_size !== undefined && (
              <div className="flex items-center gap-4 p-4 rounded-2xl bg-muted/20 border border-border/40 group hover:border-primary/20 transition-colors">
                <div className="p-2.5 rounded-xl bg-background border border-border/40 text-muted-foreground group-hover:text-primary transition-colors">
                  <UserIcon className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-widest font-black text-muted-foreground/60 mb-0.5">
                    Support Network
                  </p>
                  <p className="font-semibold text-sm">{profile.support_network_size} people</p>
                </div>
              </div>
            )}

            {profile?.primary_support_type && (
              <div className="flex items-center gap-4 p-4 rounded-2xl bg-muted/20 border border-border/40 group hover:border-primary/20 transition-colors">
                <div className="p-2.5 rounded-xl bg-background border border-border/40 text-muted-foreground group-hover:text-primary transition-colors">
                  <Briefcase className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-widest font-black text-muted-foreground/60 mb-0.5">
                    Primary Support
                  </p>
                  <p className="font-semibold text-sm capitalize">{profile.primary_support_type}</p>
                </div>
              </div>
            )}

            {profile?.primary_goal && (
              <div className="flex items-center gap-4 p-4 rounded-2xl bg-muted/20 border border-border/40 group hover:border-primary/20 transition-colors">
                <div className="p-2.5 rounded-xl bg-background border border-border/40 text-muted-foreground group-hover:text-primary transition-colors">
                  <Target className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-widest font-black text-muted-foreground/60 mb-0.5">
                    Primary Goal
                  </p>
                  <p className="font-semibold text-sm">{profile.primary_goal}</p>
                </div>
              </div>
            )}

            {profile?.focus_areas && profile.focus_areas.length > 0 && (
              <div className="flex items-center gap-4 p-4 rounded-2xl bg-muted/20 border border-border/40 group hover:border-primary/20 transition-colors">
                <div className="p-2.5 rounded-xl bg-background border border-border/40 text-muted-foreground group-hover:text-primary transition-colors">
                  <Activity className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-widest font-black text-muted-foreground/60 mb-0.5">
                    Focus Areas
                  </p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {profile.focus_areas?.map((area: string, index: number) => (
                      <span
                        key={index}
                        className="px-2 py-1 text-xs bg-primary/10 text-primary rounded-md"
                      >
                        {area}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
