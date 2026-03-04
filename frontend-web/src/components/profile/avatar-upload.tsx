'use client';

import { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui';
import { Camera, Upload, X, Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { toast } from 'sonner';

interface AvatarUploadResponse {
  avatar_path: string;
}

interface AvatarUploadProps {
  currentAvatarPath?: string;
  username?: string;
  onAvatarUpdate?: (avatarPath: string) => void;
  onUpload?: (file: File) => Promise<AvatarUploadResponse>;
  className?: string;
}

export function AvatarUpload({
  currentAvatarPath,
  username = 'User',
  onAvatarUpdate,
  onUpload,
  className
}: AvatarUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const queryClient = useQueryClient();

  const uploadMutation = useMutation<AvatarUploadResponse, Error, File>({
    mutationFn: async (file: File) => {
      if (onUpload) {
        return await onUpload(file);
      } else {
        const formData = new FormData();
        formData.append('file', file);

        const response = await apiClient.post<AvatarUploadResponse>('/users/me/avatar', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        return response;
      }
    },
    onSuccess: (data) => {
      toast.success('Avatar uploaded successfully!');
      setSelectedFile(null);
      setPreviewUrl(null);
      onAvatarUpdate?.(data.avatar_path);

      // Invalidate profile queries to refresh avatar
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      queryClient.invalidateQueries({ queryKey: ['user'] });
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to upload avatar');
    },
  });

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      toast.error('Please select an image file');
      return;
    }

    // Validate file size (5MB limit)
    if (file.size > 5 * 1024 * 1024) {
      toast.error('File size must be less than 5MB');
      return;
    }

    setSelectedFile(file);

    // Create preview URL
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    try {
      await uploadMutation.mutateAsync(selectedFile);
    } finally {
      setIsUploading(false);
    }
  };

  const handleCancel = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const getInitials = () => {
    return username
      .split(' ')
      .map((n: string) => n[0])
      .join('')
      .slice(0, 2)
      .toUpperCase();
  };

  return (
    <div className={cn('space-y-4', className)}>
      {/* Avatar Display */}
      <div className="flex flex-col items-center space-y-4">
        <div className="relative group">
          <Avatar className="h-32 w-32 border-4 border-background shadow-xl">
            {previewUrl ? (
              <AvatarImage
                src={previewUrl}
                alt="Avatar preview"
                className="object-cover"
              />
            ) : currentAvatarPath ? (
              <AvatarImage
                src={`/api/v1/avatars/${currentAvatarPath}`}
                alt={`${username} avatar`}
                className="object-cover"
              />
            ) : null}
            <AvatarFallback className="bg-gradient-to-br from-primary to-primary/60 text-white text-3xl font-black">
              {getInitials()}
            </AvatarFallback>
          </Avatar>

          {/* Upload overlay */}
          <div className="absolute inset-0 bg-black/50 rounded-full opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => fileInputRef.current?.click()}
              className="rounded-full"
            >
              <Camera className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* File input (hidden) */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileSelect}
          className="hidden"
        />

        {/* Upload button */}
        {!selectedFile && (
          <Button
            variant="outline"
            onClick={() => fileInputRef.current?.click()}
            className="flex items-center gap-2"
          >
            <Upload className="h-4 w-4" />
            Choose Avatar
          </Button>
        )}
      </div>

      {/* Preview and actions */}
      {selectedFile && (
        <div className="space-y-3 p-4 bg-muted/20 rounded-lg border">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Check className="h-4 w-4 text-green-500" />
              <span>{selectedFile.name}</span>
              <span className="text-xs">
                ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
              </span>
            </div>
          </div>

          <div className="flex gap-2">
            <Button
              onClick={handleUpload}
              disabled={isUploading}
              className="flex-1"
            >
              {isUploading ? 'Uploading...' : 'Upload Avatar'}
            </Button>
            <Button
              variant="outline"
              onClick={handleCancel}
              disabled={isUploading}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}