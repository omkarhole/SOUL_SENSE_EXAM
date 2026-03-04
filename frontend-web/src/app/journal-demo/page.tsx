'use client';

import React from 'react';
import { JournalEntryCard } from '@/components/journal';
import { JournalEntry } from '@/types/journal';
import { toast } from '@/lib/toast';

const MOCK_ENTRIES: JournalEntry[] = [
    {
        id: 1,
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:00:00Z',
        content: 'Today was a productive day. I managed to finish all my tasks and even had some time for a walk in the park. The weather was beautiful and I felt very peaceful.',
        mood_rating: 8,
        tags: ['Productive', 'Nature', 'Peaceful'],
        sentiment_score: 0.8
    },
    {
        id: 2,
        created_at: '2024-01-16T18:30:00Z',
        updated_at: '2024-01-16T18:30:00Z',
        content: 'Feeling a bit overwhelmed with work. There are so many deadlines approaching and I feel like I am falling behind. I need to take a break soon.',
        mood_rating: 3,
        tags: ['Work', 'Stress', 'Deadlines'],
        sentiment_score: -0.6
    },
    {
        id: 3,
        created_at: '2024-01-17T09:15:00Z',
        updated_at: '2024-01-17T09:15:00Z',
        content: 'Neutral day. Just regular routines. Nothing much happened, but that is okay sometimes.',
        mood_rating: 5,
        tags: ['Routine'],
        sentiment_score: 0.1
    }
];

export default function JournalDemoPage() {
    const handleClick = (entry: JournalEntry) => {
        toast.info(`Clicked entry: ${entry.id}`);
    };

    return (
        <div className="container mx-auto py-12 px-4 max-w-4xl">
            <h1 className="text-4xl font-bold mb-8 text-center bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Journal Entry Card Demo
            </h1>

            <section className="mb-12">
                <h2 className="text-2xl font-semibold mb-6 border-b pb-2">Compact Variant</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {MOCK_ENTRIES.map(entry => (
                        <JournalEntryCard
                            key={entry.id}
                            entry={entry}
                            variant="compact"
                            onClick={handleClick}
                        />
                    ))}
                </div>
            </section>

            <section>
                <h2 className="text-2xl font-semibold mb-6 border-b pb-2">Expanded Variant</h2>
                <div className="space-y-6">
                    {MOCK_ENTRIES.map(entry => (
                        <JournalEntryCard
                            key={entry.id}
                            entry={entry}
                            variant="expanded"
                            onClick={handleClick}
                        />
                    ))}
                </div>
            </section>
        </div>
    );
}
