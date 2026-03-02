'use client';

import { ProfileCard } from '@/components/profile';
import { PersonalProfile } from '@/lib/api/profile';
import { toast } from '@/lib/toast';

const mockProfile: PersonalProfile = {
  first_name: 'John',
  last_name: 'Doe',
  age: 28,
  gender: 'male',
  occupation: 'Software Engineer',
  education_level: 'Bachelor\'s Degree',
  bio: 'Passionate about creating meaningful user experiences and exploring the depths of emotional intelligence. Always learning and growing through self-reflection and mindfulness practices.',
  avatar_path: 'john_doe_avatar.png',
  member_since: '2023-06-15T00:00:00Z',
  eq_stats: {
    last_score: 85,
    total_assessments: 12
  }
};

const mockUser = {
  username: 'johndoe',
  email: 'john.doe@example.com',
  created_at: '2023-06-15T00:00:00Z',
  name: 'John Doe'
};

export default function ProfileTestPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-6xl mx-auto space-y-12">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Profile Card Test</h1>
          <p className="text-gray-600">Testing both compact and full variants</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Full Variant */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-gray-800">Full Variant</h2>
            <ProfileCard
              profile={mockProfile}
              user={mockUser}
              variant="full"
              editable={true}
              onEdit={() => toast.info('Edit clicked!')}
            />
          </div>

          {/* Compact Variant */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-gray-800">Compact Variant</h2>
            <ProfileCard
              profile={mockProfile}
              user={mockUser}
              variant="compact"
              editable={false}
            />
          </div>
        </div>

        {/* Additional Test Cases */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-800">Edge Cases</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* No Avatar */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">No Avatar</h3>
              <ProfileCard
                profile={{ ...mockProfile, avatar_url: undefined }}
                user={mockUser}
                variant="compact"
              />
            </div>

            {/* No Bio */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">No Bio</h3>
              <ProfileCard
                profile={{ ...mockProfile, bio: undefined }}
                user={mockUser}
                variant="compact"
              />
            </div>

            {/* No EQ Stats */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">No EQ Stats</h3>
              <ProfileCard
                profile={{ ...mockProfile, eq_stats: undefined }}
                user={mockUser}
                variant="compact"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}