# Project Overview

## Problem Statement
People save videos daily on various platforms like Instagram, TikTok, Facebook, and YouTube. However, finding a specific video later can be challenging since users often forget where they saved it or what it was called.

## Solution
This app enables users to save videos in two ways:
1. **Copy & Paste** – Manually add the link via the app's add page.
2. **Share Integration** – Directly share links from apps like Instagram, YouTube, TikTok, or Facebook. The app automatically captures and processes the link without extra steps.

AI then analyzes the video title, visual content, and audio transcription, generating a searchable summary. Users can later find videos simply by describing them, even without knowing the exact title or platform.

---

# User Workflow

## Step 1: Onboarding & Authentication
1. **Welcome Screen** – Clean UI with signup/login options.
2. **Sign-up with Email** – Users register using their email.
3. **Welcome Page** – Displays a "Let's Get Started" button.
4. **Highlighting App's Value** – Users answer three Yes/No questions:
   - ❓ *Do you struggle to find saved videos later?*
     - ✅ *Our AI makes them searchable so you never lose a video again!*
   - ❓ *Have you ever forgotten where a video was saved?*
     - ✅ *Find any video easily with our search AI!*
   - ❓ *Do you wish you could search for videos by description instead of title?*
     - ✅ *Our AI understands what's inside your videos!*

## Step 2: Home Page & Search
- **Home Page** – Displays saved videos categorized by platform (YouTube, Instagram, etc.).
- **Search Bar** – Allows searching by keywords or descriptions.
- **Search Workflow:**
  1. Clicking the search bar reveals category filters.
  2. After entering a query and pressing the search icon, results appear with:
     - Thumbnail (right)
     - Title (middle)
     - Quick link copy button (left)
     - 🗑 Delete button (right) for easy removal.
  3. Clicking a result opens the video in a browser.

## Step 3: Adding Videos
Users can add videos in two ways:
1. **Paste a link manually** on the add page.
2. **Share a link from another app** – The app auto-fills the link.

Users can assign categories before clicking the ➕ **Add** button to process and save the video.

## Step 4: Profile & Settings
Users access their profile via the bottom-right icon.
- **Profile Page Includes:**
  - Username & Profile Picture (optional).
  - Edit Profile – Change username, email, etc.
  - Manage Videos – Organize or delete multiple saved videos at once.
  - Privacy Policy & FAQs.
  - Logout Option.

---

# Step-by-Step Backend Workflow & Tech Stack

## Step 1: Adding a Video Link
Users can:
- **Manually paste a link** in the app.
- **Share a video link** from another app (Instagram, YouTube, TikTok, Facebook), and the app extracts and processes the link.
- **Tech Stack:** React Native (Frontend), Expo Intent Launcher (Handles Share Intent)

## Step 2: User Authentication
- Required for syncing videos across devices.
- **Tech Stack:** Supabase Auth

## Step 3: Extract Video Metadata
- The backend extracts metadata using yt-dlp.
- **Metadata Includes:**
  - Title
  - Description
  - Tags
  - Thumbnail
  - Video length
- **Tech Stack:** FastAPI (Backend), yt-dlp (Metadata Extraction), Supabase (Database)

## Step 4: Analyze Video Visual Content
- AI detects key visual elements:
  - Objects (e.g., "laptop", "car")
  - People (e.g., "man wearing yellow shirt")
  - Backgrounds (e.g., "indoor office")
  - On-screen text (captions, watermarks)
- **Tech Stack:** Hugging Face Image Models (Visual AI), FastAPI (Backend Processing)

## Step 5: Transcribe Audio (Speech-to-Text)
- AI extracts spoken words and generates a transcript.
- **Tech Stack:** OpenAI Whisper / Hugging Face Speech Models, Supabase (Database)

## Step 6: Generate Searchable Summary
AI combines metadata, visual analysis, and transcript into a structured summary:
```json
{
  "title": "AI Image Generator Tutorial",
  "platform": "YouTube",
  "visual_summary": "Man wearing yellow shirt using a laptop",
  "audio_transcription": "In this tutorial, I will show you how to use an AI image generator",
  "keywords": ["AI", "image generator", "yellow shirt", "tutorial", "laptop"]
}
```
- **Tech Stack:** FastAPI (Backend Processing), Supabase (Database)

## Step 7: Store Processed Data
- All extracted data is saved in a structured database for quick searches.
- **Tech Stack:** Supabase (Database Storage)

## Step 8: Searching for a Video
- Users enter a description of the video they remember.
- **Tech Stack:** React Native (Frontend), FastAPI (Search API)

## Step 9: AI Matching Algorithm
- Search process:
  1. AI checks **search_summary** for an exact match.
  2. Looks at **keywords**.
  3. Searches **visual_summary** and **audio_transcription** if no match is found.
- **Tech Stack:** FAISS (Vector Search AI), FastAPI (Search API), Supabase (Database)

## Step 10: Displaying Search Results
- Top matching videos appear in order of relevance.
- **Tech Stack:** React Native (Frontend UI), FastAPI (Backend Search API)

## Step 11: Managing Saved Videos
- Users can delete or update video descriptions as needed.
- **Tech Stack:** Supabase (Database API)

---

# Search Results Prioritization
Videos are ranked based on a relevance score (0-100):

| Priority | Match Type         | Score Boost |
|----------|-------------------|-------------|
| 1️⃣      | **Perfect Match**  | +50 points  |
| 2️⃣      | **Strong Match**   | +30 points  |
| 3️⃣      | **Partial Match**  | +20 points  |
| 4️⃣      | **Weak Match**     | +10 points  |
| 5️⃣      | **Last Resort**    | +5 points   |

### Matching Criteria:
- **Perfect Match**: Matches `search_summary` or `title`
- **Strong Match**: Matches `keywords`
- **Partial Match**: Found in `visual_summary` (objects, colors, people)
- **Weak Match**: Found in `audio_transcription` (spoken words)
- **Last Resort**: Found in `metadata` (description, tags)

---

# Database Schema

## Tables

### users
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT UNIQUE NOT NULL,
  username TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  avatar_url TEXT
);
```

### videos
```sql
CREATE TABLE videos (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  url TEXT NOT NULL,
  platform TEXT NOT NULL,
  title TEXT,
  thumbnail_url TEXT,
  duration INTEGER,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### video_analysis
```sql
CREATE TABLE video_analysis (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
  search_summary TEXT,
  visual_summary TEXT,
  audio_transcription TEXT,
  keywords TEXT[],
  metadata JSONB,
  embedding vector(1536),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### categories
```sql
CREATE TABLE categories (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### video_categories
```sql
CREATE TABLE video_categories (
  video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
  category_id UUID REFERENCES categories(id) ON DELETE CASCADE,
  PRIMARY KEY (video_id, category_id)
);
```

## Indexes
```sql
CREATE INDEX idx_videos_user_id ON videos(user_id);
CREATE INDEX idx_video_analysis_video_id ON video_analysis(video_id);
CREATE INDEX idx_categories_user_id ON categories(user_id);
CREATE INDEX idx_embedding ON video_analysis USING ivfflat (embedding vector_cosine_ops);
```

---

# Project Folder Structure

```
📁 video-saver/
├── 📁 mobile/                  # React Native Mobile App
│   ├── 📁 src/
│   │   ├── 📁 components/     # Reusable UI components
│   │   ├── 📁 screens/        # Screen components
│   │   ├── 📁 navigation/     # Navigation configuration
│   │   ├── 📁 hooks/          # Custom React hooks
│   │   ├── 📁 services/       # API services
│   │   ├── 📁 utils/          # Helper functions
│   │   ├── 📁 constants/      # App constants
│   │   └── 📁 types/          # TypeScript types
│   ├── 📁 assets/             # Images, fonts, etc.
│   └── 📁 __tests__/          # Tests
│
├── 📁 backend/                 # FastAPI Backend
│   ├── 📁 app/
│   │   ├── 📁 api/            # API routes
│   │   ├── 📁 core/           # Core functionality
│   │   ├── 📁 models/         # Database models
│   │   ├── 📁 schemas/        # Pydantic schemas
│   │   ├── 📁 services/       # Business logic
│   │   └── 📁 utils/          # Helper functions
│   ├── 📁 tests/              # Backend tests
│   └── 📁 alembic/            # Database migrations
│
├── 📁 docs/                    # Documentation
│   ├── 📄 Contaxt.md
│   ├── 📄 API.md
│   └── 📄 Setup.md
│
├── 📁 infrastructure/          # Infrastructure as code
│   ├── 📁 terraform/
│   └── 📁 docker/
│
└── 📁 scripts/                 # Utility scripts
```

---

This Markdown version ensures readability, structure, and clarity for documentation purposes.

